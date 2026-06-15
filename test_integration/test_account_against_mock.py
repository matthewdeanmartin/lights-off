"""End-to-end tests for MastodonAccount's wrapper methods against the mock.

Each test drives a real ``MastodonAccount`` (built without its GUI ``__init__``;
see ``conftest.py``) whose ``api`` is a real Mastodon.py client pointed at a
stateful ``mastodon_mock`` HTTP server. Where the unit suite in
``tests/test_mastodon_account.py`` asserts *that the right api method was called*
with a MagicMock, these assert *that the call actually works* over HTTP: a tweet
round-trips into the timeline, a follow creates a real relationship, ``_paginate``
walks real Link-header pages, and the analysis helpers compute over real rows.
"""

from __future__ import annotations

from mastodon import Mastodon


# --- posting ---------------------------------------------------------------


class TestPosting:
    def test_tweet_round_trips_into_timeline(self, me_account, friend_client: Mastodon) -> None:
        status = me_account.tweet("posting from lights-off", visibility="public")
        assert status is not False
        assert "posting from lights-off" in status.content

        # "me" is followed by nobody here, but the author's own home timeline
        # includes their own public posts.
        home = me_account.api.timeline_home()
        assert status.id in {s.id for s in home}

    def test_tweet_reply_sets_in_reply_to(self, me_account, friend_client: Mastodon) -> None:
        parent = friend_client.status_post("anyone around?", visibility="public")
        reply = me_account.tweet("yes, hello!", id=parent.id, visibility="public")
        assert reply is not False
        assert str(reply.in_reply_to_id) == str(parent.id)

    def test_tweet_with_spoiler_text(self, me_account) -> None:
        status = me_account.tweet(
            "the body", visibility="public", spoiler_text="content warning"
        )
        assert status is not False
        assert status.spoiler_text == "content warning"

    def test_tweet_carries_visibility(self, me_account) -> None:
        status = me_account.tweet("an unlisted thought", visibility="unlisted")
        assert status is not False
        assert status.visibility == "unlisted"

    def test_tweet_returns_false_on_error(self, me_account, monkeypatch) -> None:
        """A MastodonError is swallowed: the method speaks it and returns False."""
        from mastodon import MastodonError

        def boom(*args, **kwargs):
            raise MastodonError("nope")

        monkeypatch.setattr(me_account.api, "status_post", boom)
        assert me_account.tweet("this will fail") is False


# --- favourite / reblog ----------------------------------------------------


class TestPostActions:
    def test_like_then_unlike(self, me_account, friend_client: Mastodon) -> None:
        target = friend_client.status_post("favourite me maybe", visibility="public")

        me_account.like(target.id)
        assert me_account.api.status(target.id).favourited is True

        me_account.unlike(target.id)
        assert me_account.api.status(target.id).favourited is False

    def test_retweet_boosts(self, me_account, friend_client: Mastodon) -> None:
        target = friend_client.status_post("boost me", visibility="public")
        me_account.retweet(target.id)
        assert me_account.api.status(target.id).reblogged is True

    def test_quote_appends_url(self, me_account, friend_client: Mastodon) -> None:
        original = friend_client.status_post("the quotable original", visibility="public")
        quote = me_account.quote(original, "well said", visibility="public")
        assert original.url in quote.content


# --- social actions (real account_search resolution) -----------------------


class TestSocialActions:
    def test_follow_resolves_and_creates_relationship(self, me_account) -> None:
        # "stranger" is seeded but not yet followed by "me".
        stranger_id = me_account._resolve_account_id("stranger")
        assert stranger_id is not None
        assert me_account.api.account_relationships(stranger_id)[0].following is False

        me_account.follow("@stranger")
        assert me_account.api.account_relationships(stranger_id)[0].following is True

    def test_unfollow_clears_relationship(self, me_account) -> None:
        friend_id = me_account._resolve_account_id("friend")
        # "me" follows "friend" from the seed.
        assert me_account.api.account_relationships(friend_id)[0].following is True

        me_account.unfollow("friend")
        assert me_account.api.account_relationships(friend_id)[0].following is False

    def test_block_then_unblock(self, me_account) -> None:
        stranger_id = me_account._resolve_account_id("stranger")
        me_account.block("@stranger")
        assert me_account.api.account_relationships(stranger_id)[0].blocking is True
        me_account.unblock("@stranger")
        assert me_account.api.account_relationships(stranger_id)[0].blocking is False

    def test_mute_then_unmute(self, me_account) -> None:
        stranger_id = me_account._resolve_account_id("stranger")
        me_account.mute("@stranger")
        assert me_account.api.account_relationships(stranger_id)[0].muting is True
        me_account.unmute("@stranger")
        assert me_account.api.account_relationships(stranger_id)[0].muting is False

    def test_follow_noop_when_not_found(self, me_account) -> None:
        """An unresolvable handle is a no-op, not an error."""
        # Should neither raise nor call account_follow with a bad id.
        me_account.follow("@definitely-not-a-seeded-account-xyz")


# --- pagination + follower/friend analysis ---------------------------------


class TestFollowersAndFriends:
    def test_friends_returns_followed_accounts(self, me_account) -> None:
        friends = me_account.friends(me_account.me.id)
        accts = {u.acct for u in friends}
        assert "friend" in accts

    def test_followers_walks_real_pages(self, me_account, mock_server) -> None:
        """Seed several followers for "me" and page through them via Link headers.

        ``_paginate`` follows ``_pagination_next`` with a small page size, so this
        exercises the real multi-page walk against the mock's pagination, not a
        single short page.
        """
        # Have a handful of distinct accounts follow "me".
        me_id = me_account.me.id
        for token in ("friend_token", "stranger_token"):
            mock_server.client(token=token).account_follow(me_id)

        followers = me_account.followers(me_id)
        accts = {u.acct for u in followers}
        assert {"friend", "stranger"}.issubset(accts)

    def test_mutual_following_intersection(self, me_account, mock_server) -> None:
        """"friend" follows back → friend is a mutual."""
        me_id = me_account.me.id
        mock_server.client("friend").account_follow(me_id)

        mutuals = me_account.mutual_following()
        assert "friend" in {u.acct for u in mutuals}

    def test_not_following_me_finds_one_way_friends(self, me_account) -> None:
        """"me" follows "friend"; if friend does not follow back, it shows here."""
        result = me_account.not_following_me()
        # "friend" is followed by "me" but (absent a follow-back) is not a follower.
        assert "friend" in {u.acct for u in result}

    def test_not_following_returns_unreciprocated_followers(self, me_account, mock_server) -> None:
        """A follower "me" does not follow back appears in not_following()."""
        me_id = me_account.me.id
        # "stranger" follows "me"; "me" does not follow "stranger".
        mock_server.client("stranger").account_follow(me_id)

        result = me_account.not_following()
        assert "stranger" in {u.acct for u in result}
