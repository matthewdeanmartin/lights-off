"""
Unit tests for MastodonAccount methods using mocked Mastodon API.

No network, no wx, no sound_lib required.
"""
import sys
import types
import unittest.mock as mock
import pytest
from mastodon.types_base import AttribAccessDict, PaginatableList
from mastodon.return_types import Account, Status


# ---------------------------------------------------------------------------
# Stub heavy dependencies so mastodon_account.py can be imported
# ---------------------------------------------------------------------------

def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules.setdefault(name, m)
    return m


_stub("wx")
_stub("sound_lib")
_stub("sound_lib.stream")
_stub("sound_lib.output")
_stub("accessible_output2")
_stub("accessible_output2.outputs")
_stub("accessible_output2.outputs.auto")
_stub("keyboard_handler")
_stub("keyboard_handler.wx_handler")

tweak_mod = _stub("tweak")


class _FakeConfig:
    def __init__(self, *a, **kw):
        self._d = {}
        self.user_config_dir = "/tmp/lights-off-test"

    def get(self, key, default=None):
        return self._d.get(key, default)

    def __setattr__(self, k, v):
        if k.startswith("_"):
            object.__setattr__(self, k, v)
        else:
            self._d[k] = v
            object.__setattr__(self, k, v)


tweak_mod.Config = _FakeConfig

gui_pkg = types.ModuleType("lights_off.GUI")
gui_pkg.__path__ = []
gui_pkg.__package__ = "lights_off.GUI"
sys.modules["lights_off.GUI"] = gui_pkg
_stub("lights_off.GUI.main", window=mock.MagicMock())
_stub("lights_off.GUI.misc")
_stub("lights_off.GUI.ask", ask=mock.MagicMock(return_value=""))
_stub("lights_off.timeline", add=mock.MagicMock(), timelineThread=mock.MagicMock())
_stub("lights_off.streaming", MastodonStreamListener=mock.MagicMock())
_stub("lights_off.speak", speak=mock.MagicMock())
_stub("lights_off.sound", play=mock.MagicMock())
_stub("lights_off.api_log", instrument=lambda api, **kw: api)
app_mod = _stub("lights_off.application")
app_mod.name = "lights-off"
app_mod.version = "0.1"
app_mod.shortname = "lights-off"

# Force the real mastodon_account module — test_utils.py stubs it as a bare
# module, so explicitly remove the stub and reimport the real one.
sys.modules.pop("lights_off.mastodon_account", None)
import importlib
import lights_off.mastodon_account as _ma_module
importlib.reload(_ma_module)

# Build a standalone fake globals object that mastodon_account.globals will
# point to — completely independent of lights_off.globals so test_utils.py
# cannot interfere.
class _FakeGlobals:
    pass

_fake_g = _FakeGlobals()


def _reset_globals():
    _fake_g.prefs = _FakeConfig()
    _fake_g.prefs.user_limit = 4
    _fake_g.prefs.count = 20
    _fake_g.prefs.streaming = False
    _fake_g.prefs.follow_prompt = True
    _fake_g.users = []
    _fake_g.unknown_users = []
    _fake_g.currentAccount = None
    _fake_g.accounts = []
    _fake_g.timeline_settings = []
    _fake_g.errors = []


_reset_globals()
# Patch mastodon_account's globals reference so it uses our fake
_ma_module.globals = _fake_g


@pytest.fixture(autouse=True)
def _fresh_globals():
    _reset_globals()
    _ma_module.globals = _fake_g
    yield


# ---------------------------------------------------------------------------
# Helpers to build Mastodon-typed objects
# ---------------------------------------------------------------------------

def _account(**kwargs) -> AttribAccessDict:
    base = dict(
        id="1", acct="user@mastodon.social", display_name="Test User",
        followers_count=10, following_count=5, statuses_count=100,
        note="<p>bio</p>", url="https://mastodon.social/@user",
        locked=False, following=False, last_status_at=None,
        created_at=None,
    )
    base.update(kwargs)
    a = AttribAccessDict(**base)
    return a


def _paginatable(items, next_max_id=None):
    """Build a PaginatableList with optional _pagination_next."""
    pl = PaginatableList(items)
    if next_max_id is not None:
        pl._pagination_next = {"max_id": next_max_id, "limit": 80,
                               "_pagination_method": "GET",
                               "_pagination_endpoint": "/fake"}
    else:
        pl._pagination_next = None
    return pl


# ---------------------------------------------------------------------------
# Build a MastodonAccount with a mocked api
# ---------------------------------------------------------------------------

def _make_account_obj():
    """Return a MastodonAccount instance with api fully mocked, skipping __init__."""
    obj = object.__new__(_ma_module.MastodonAccount)
    obj.api = mock.MagicMock()
    obj.me = _account(id="42", acct="me@mastodon.social")
    obj.prefs = _FakeConfig()
    obj.prefs.soundpack = "default"
    obj.prefs.soundpan = 0
    obj.prefs.footer = ""
    obj.prefs.user_timelines = []
    obj.prefs.list_timelines = []
    obj.prefs.search_timelines = []
    obj.prefs.follow_prompt = True
    obj.timelines = []
    obj.currentTimeline = None
    obj.currentIndex = 0
    obj.ready = False
    return obj


# ---------------------------------------------------------------------------
# _paginate
# ---------------------------------------------------------------------------

class TestPaginate:
    def test_single_page_no_next(self):
        acc = _make_account_obj()
        users = [_account(id=str(i)) for i in range(5)]
        acc.api.account_followers.return_value = _paginatable(users, next_max_id=None)
        result = acc._paginate(acc.api.account_followers, "42")
        assert len(result) == 5
        acc.api.account_followers.assert_called_once_with("42", limit=80)

    def test_two_pages(self):
        acc = _make_account_obj()
        page1 = _paginatable([_account(id="1"), _account(id="2")], next_max_id="111")
        page2 = _paginatable([_account(id="3")], next_max_id=None)
        acc.api.account_followers.side_effect = [page1, page2]
        result = acc._paginate(acc.api.account_followers, "42")
        assert len(result) == 3
        assert acc.api.account_followers.call_count == 2
        # Second call must pass max_id
        _, kwargs = acc.api.account_followers.call_args
        assert kwargs.get("max_id") == "111"

    def test_respects_user_limit(self):
        acc = _make_account_obj()
        _fake_g.prefs.user_limit = 2
        pages = [_paginatable([_account(id=str(i))], next_max_id=str(i + 1)) for i in range(10)]
        acc.api.account_followers.side_effect = pages
        result = acc._paginate(acc.api.account_followers, "42")
        assert acc.api.account_followers.call_count <= 3

    def test_promotes_plain_dicts(self):
        acc = _make_account_obj()
        # Plain dict (not AttribAccessDict) — _promote should wrap it
        plain = {"id": "99", "acct": "plain@example.com", "display_name": "Plain"}
        pl = PaginatableList([plain])
        pl._pagination_next = None
        acc.api.account_followers.return_value = pl
        result = acc._paginate(acc.api.account_followers, "42")
        assert len(result) == 1
        assert hasattr(result[0], "acct")
        assert result[0].acct == "plain@example.com"

    def test_empty_first_page(self):
        acc = _make_account_obj()
        acc.api.account_followers.return_value = _paginatable([], next_max_id=None)
        result = acc._paginate(acc.api.account_followers, "42")
        assert result == []

    def test_returns_typed_account_objects(self):
        acc = _make_account_obj()
        users = [_account(id=str(i), acct=f"u{i}@x.com") for i in range(3)]
        acc.api.account_followers.return_value = _paginatable(users)
        result = acc._paginate(acc.api.account_followers, "42")
        for u in result:
            assert hasattr(u, "display_name")
            assert hasattr(u, "acct")


# ---------------------------------------------------------------------------
# followers / friends
# ---------------------------------------------------------------------------

class TestFollowersFriends:
    def test_followers_delegates_to_paginate(self):
        acc = _make_account_obj()
        users = [_account(id="1")]
        acc.api.account_followers.return_value = _paginatable(users)
        result = acc.followers("42")
        assert len(result) == 1
        acc.api.account_followers.assert_called_once_with("42", limit=80)

    def test_friends_delegates_to_paginate(self):
        acc = _make_account_obj()
        users = [_account(id="1")]
        acc.api.account_following.return_value = _paginatable(users)
        result = acc.friends("42")
        assert len(result) == 1
        acc.api.account_following.assert_called_once_with("42", limit=80)


# ---------------------------------------------------------------------------
# mutual_following / not_following / not_following_me
# ---------------------------------------------------------------------------

class TestUserAnalysis:
    def _acc_with_followers_friends(self, follower_ids, friend_ids):
        acc = _make_account_obj()
        followers = [_account(id=str(i)) for i in follower_ids]
        friends = [_account(id=str(i)) for i in friend_ids]
        acc.api.account_followers.return_value = _paginatable(followers)
        acc.api.account_following.return_value = _paginatable(friends)
        return acc

    def test_mutual_following_intersection(self):
        acc = self._acc_with_followers_friends(
            follower_ids=[1, 2, 3],
            friend_ids=[2, 3, 4],
        )
        mutuals = acc.mutual_following()
        ids = {int(u.id) for u in mutuals}
        assert ids == {2, 3}

    def test_mutual_following_empty_when_no_overlap(self):
        acc = self._acc_with_followers_friends(
            follower_ids=[1, 2],
            friend_ids=[3, 4],
        )
        assert acc.mutual_following() == []

    def test_not_following_me_finds_friends_not_in_followers(self):
        acc = self._acc_with_followers_friends(
            follower_ids=[1, 2],
            friend_ids=[2, 3],
        )
        result = acc.not_following_me()
        ids = {int(u.id) for u in result}
        assert ids == {3}

    def test_not_following_returns_followers_not_followed_back(self):
        acc = _make_account_obj()
        followers = [_account(id="1"), _account(id="2")]
        acc.api.account_followers.return_value = _paginatable(followers)
        # relationship: we follow id=2 but not id=1
        rel1 = AttribAccessDict(id="1", following=False)
        rel2 = AttribAccessDict(id="2", following=True)
        acc.api.account_relationships.return_value = [rel1, rel2]
        result = acc.not_following()
        assert len(result) == 1
        assert result[0].id == "1"

    def test_not_following_empty_followers(self):
        acc = _make_account_obj()
        acc.api.account_followers.return_value = _paginatable([])
        result = acc.not_following()
        assert result == []
        acc.api.account_relationships.assert_not_called()


# ---------------------------------------------------------------------------
# tweet / retweet / like / unlike
# ---------------------------------------------------------------------------

class TestPostActions:
    def test_tweet_posts_status(self):
        acc = _make_account_obj()
        fake_status = mock.MagicMock()
        acc.api.status_post.return_value = fake_status
        result = acc.tweet("Hello world")
        acc.api.status_post.assert_called_once_with("Hello world", visibility="public")
        assert result is fake_status

    def test_tweet_with_reply(self):
        acc = _make_account_obj()
        acc.api.status_post.return_value = mock.MagicMock()
        acc.tweet("reply text", id="99")
        call_kwargs = acc.api.status_post.call_args[1]
        assert call_kwargs.get("in_reply_to_id") == "99"

    def test_tweet_with_spoiler(self):
        acc = _make_account_obj()
        acc.api.status_post.return_value = mock.MagicMock()
        acc.tweet("text", spoiler_text="CW here")
        call_kwargs = acc.api.status_post.call_args[1]
        assert call_kwargs.get("spoiler_text") == "CW here"

    def test_tweet_with_visibility(self):
        acc = _make_account_obj()
        acc.api.status_post.return_value = mock.MagicMock()
        acc.tweet("private", visibility="private")
        call_kwargs = acc.api.status_post.call_args[1]
        assert call_kwargs.get("visibility") == "private"

    def test_tweet_returns_false_on_error(self):
        from mastodon import MastodonError
        acc = _make_account_obj()
        acc.api.status_post.side_effect = MastodonError("rate limited")
        result = acc.tweet("bad")
        assert result is False

    def test_retweet_calls_reblog(self):
        acc = _make_account_obj()
        acc.retweet("123")
        acc.api.status_reblog.assert_called_once_with("123")

    def test_like_calls_favourite(self):
        acc = _make_account_obj()
        acc.like("55")
        acc.api.status_favourite.assert_called_once_with("55")

    def test_unlike_calls_unfavourite(self):
        acc = _make_account_obj()
        acc.unlike("55")
        acc.api.status_unfavourite.assert_called_once_with("55")


# ---------------------------------------------------------------------------
# follow / unfollow / block / unblock / mute / unmute
# ---------------------------------------------------------------------------

class TestSocialActions:
    def _acc_with_search(self, found_id="99"):
        acc = _make_account_obj()
        acc.api.account_search.return_value = [_account(id=found_id)]
        return acc

    def test_follow_resolves_and_calls_api(self):
        acc = self._acc_with_search("10")
        acc.follow("@someone")
        acc.api.account_follow.assert_called_once_with("10")

    def test_unfollow_resolves_and_calls_api(self):
        acc = self._acc_with_search("10")
        acc.unfollow("someone")
        acc.api.account_unfollow.assert_called_once_with("10")

    def test_block_resolves_and_calls_api(self):
        acc = self._acc_with_search("10")
        acc.block("someone")
        acc.api.account_block.assert_called_once_with("10")

    def test_unblock_resolves_and_calls_api(self):
        acc = self._acc_with_search("10")
        acc.unblock("someone")
        acc.api.account_unblock.assert_called_once_with("10")

    def test_mute_resolves_and_calls_api(self):
        acc = self._acc_with_search("10")
        acc.mute("someone")
        acc.api.account_mute.assert_called_once_with("10")

    def test_unmute_resolves_and_calls_api(self):
        acc = self._acc_with_search("10")
        acc.unmute("someone")
        acc.api.account_unmute.assert_called_once_with("10")

    def test_follow_noop_when_not_found(self):
        acc = _make_account_obj()
        acc.api.account_search.return_value = []
        acc.follow("ghost")
        acc.api.account_follow.assert_not_called()

    def test_follow_strips_leading_at(self):
        acc = _make_account_obj()
        acc.api.account_search.return_value = [_account(id="5")]
        acc.follow("@stripped")
        acc.api.account_search.assert_called_once_with("stripped", limit=1)


# ---------------------------------------------------------------------------
# quote
# ---------------------------------------------------------------------------

class TestQuote:
    def test_quote_appends_url(self):
        acc = _make_account_obj()
        acc.api.status_post.return_value = mock.MagicMock()
        status = mock.MagicMock()
        status.url = "https://mastodon.social/@orig/1"
        acc.quote(status, "My comment")
        call_args = acc.api.status_post.call_args
        posted_text = call_args[0][0]
        assert "My comment" in posted_text
        assert status.url in posted_text

    def test_quote_passes_visibility(self):
        acc = _make_account_obj()
        acc.api.status_post.return_value = mock.MagicMock()
        status = mock.MagicMock()
        status.url = "https://example.com/post/1"
        acc.quote(status, "comment", visibility="unlisted")
        kwargs = acc.api.status_post.call_args[1]
        assert kwargs.get("visibility") == "unlisted"


# ---------------------------------------------------------------------------
# havent_posted
# ---------------------------------------------------------------------------

class TestHaventPosted:
    def test_filters_old_posters(self):
        import datetime
        acc = _make_account_obj()
        old = _account(id="1", last_status_at=datetime.datetime(2020, 1, 1))
        recent = _account(id="2", last_status_at=datetime.datetime.now())
        acc.api.account_following.return_value = _paginatable([old, recent])
        result = acc.havent_posted()
        ids = [u.id for u in result]
        assert "1" in ids
        assert "2" not in ids

    def test_excludes_never_posted(self):
        acc = _make_account_obj()
        never = _account(id="3", last_status_at=None)
        acc.api.account_following.return_value = _paginatable([never])
        result = acc.havent_posted()
        assert "3" not in [u.id for u in result]
