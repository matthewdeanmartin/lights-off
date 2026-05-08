"""
Live integration tests against the real Mastodon API.

All tests in this file require valid credentials in .env and are marked `live`.
They are safe to run: any posts created are immediately deleted or posted as
`private` visibility so they don't appear on public timelines.
"""
import pytest
from mastodon import MastodonError


pytestmark = pytest.mark.live


class TestCredentials:
    def test_me_returns_account(self, api):
        me = api.me()
        assert me.acct
        assert me.id

    def test_instance_info(self, api):
        inst = api.instance()
        assert inst.title
        # Mastodon v2 API returns `domain`, v1 returns `uri`
        assert getattr(inst, "domain", None) or getattr(inst, "uri", None)


class TestTimelines:
    def test_home_timeline_returns_list(self, api):
        tl = api.timeline_home(limit=5)
        assert isinstance(tl, list)

    def test_home_timeline_status_shape(self, api):
        tl = api.timeline_home(limit=3)
        if not tl:
            pytest.skip("home timeline is empty")
        s = tl[0]
        assert hasattr(s, "id")
        assert hasattr(s, "content")
        assert hasattr(s, "account")
        assert hasattr(s.account, "acct")
        assert hasattr(s, "reblog")
        assert hasattr(s, "spoiler_text")
        assert hasattr(s, "media_attachments")
        assert hasattr(s, "url")
        assert isinstance(s.content, str)

    def test_notifications_returns_list(self, api):
        notifs = api.notifications(limit=5)
        assert isinstance(notifs, list)

    def test_favourites_returns_list(self, api):
        favs = api.favourites(limit=5)
        assert isinstance(favs, list)

    def test_account_statuses_returns_list(self, api):
        me = api.me()
        posts = api.account_statuses(me.id, limit=5)
        assert isinstance(posts, list)


class TestSearch:
    def test_search_v2_returns_statuses(self, api):
        result = api.search_v2("python")
        assert "statuses" in result
        assert isinstance(result["statuses"], list)

    def test_search_v2_no_limit_kwarg(self, api):
        """Confirm search_v2 does NOT accept a limit param (API difference)."""
        import inspect
        sig = inspect.signature(api.search_v2)
        assert "limit" not in sig.parameters


class TestPostRoundTrip:
    pytestmark = pytest.mark.live_write

    def test_post_and_delete(self, api):
        """Post a private status and immediately delete it."""
        s = api.status_post(
            "lights-off automated test [safe to ignore]",
            visibility="private",
        )
        assert s.id
        assert s.visibility == "private"
        api.status_delete(s.id)

    def test_post_with_content_warning(self, api):
        s = api.status_post(
            "test content",
            spoiler_text="test CW",
            visibility="private",
        )
        assert s.spoiler_text == "test CW"
        api.status_delete(s.id)

    def test_reply(self, api):
        parent = api.status_post("parent post [test]", visibility="private")
        reply = api.status_post(
            "reply post [test]",
            in_reply_to_id=parent.id,
            visibility="private",
        )
        assert reply.in_reply_to_id == parent.id
        api.status_delete(reply.id)
        api.status_delete(parent.id)

    def test_favourite_and_unfavourite(self, api):
        s = api.status_post("favourite test [automated]", visibility="private")
        fav = api.status_favourite(s.id)
        assert fav.favourited is True
        unfav = api.status_unfavourite(s.id)
        assert unfav.favourited is False
        api.status_delete(s.id)

    def test_boost_and_unboost(self, api):
        s = api.status_post("boost test [automated]", visibility="private")
        boosted = api.status_reblog(s.id)
        assert boosted.reblogged is True
        api.status_unreblog(s.id)
        api.status_delete(s.id)


class TestAccounts:
    def test_account_followers_returns_list(self, api):
        me = api.me()
        followers = api.account_followers(me.id, limit=5)
        assert isinstance(followers, list)

    def test_account_following_returns_list(self, api):
        me = api.me()
        following = api.account_following(me.id, limit=5)
        assert isinstance(following, list)

    def test_account_search_returns_list(self, api):
        results = api.account_search("mastodon", limit=3)
        assert isinstance(results, list)
        if results:
            assert hasattr(results[0], "acct")

    def test_account_search_self(self, api):
        me = api.me()
        results = api.account_search(me.acct, limit=1)
        assert results


class TestLists:
    def test_lists_returns_list(self, api):
        lists = api.lists()
        assert isinstance(lists, list)

    @pytest.mark.live_write
    def test_list_create_update_delete(self, api):
        lst = api.list_create("test-lights-off")
        assert lst.title == "test-lights-off"
        updated = api.list_update(lst.id, "test-lights-off-updated")
        assert updated.title == "test-lights-off-updated"
        api.list_delete(lst.id)


class TestHtmlContent:
    """Verify that live status content is HTML and our stripper handles it."""

    def test_content_is_html(self, api):
        tl = api.timeline_home(limit=5)
        if not tl:
            pytest.skip("timeline empty")
        s = tl[0]
        # Mastodon wraps all content in at least <p> tags
        assert "<" in s.content or s.content == ""

    def test_strip_html_produces_clean_text(self, api):
        from html.parser import HTMLParser
        import html

        class Stripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts = []
            def handle_data(self, d):
                self.parts.append(d)

        tl = api.timeline_home(limit=5)
        if not tl:
            pytest.skip("timeline empty")
        s = tl[0]
        stripper = Stripper()
        stripper.feed(html.unescape(s.content))
        text = "".join(stripper.parts)
        assert "<" not in text
