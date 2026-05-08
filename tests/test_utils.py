"""
Unit tests for utils.py — no GUI, no network, no Mastodon API.
"""
import sys
import types
import unittest.mock as mock
import pytest


# ---------------------------------------------------------------------------
# Minimal stubs so utils.py can be imported without wx / sound_lib / speak
# ---------------------------------------------------------------------------

def _stub_module(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


_stub_module("wx")
_stub_module("lights_off.speak", speak=lambda *a, **kw: None)
_stub_module("lights_off.sound", play=lambda *a, **kw: None)
_stub_module("sound_lib")
_stub_module("sound_lib.stream")
_stub_module("sound_lib.output")
_stub_module("accessible_output2")
_stub_module("accessible_output2.outputs")
_stub_module("accessible_output2.outputs.auto")
_stub_module("keyboard_handler")
_stub_module("keyboard_handler.wx_handler")

# Stub tweak so globals.py can be imported
tweak_mod = _stub_module("tweak")
class _FakeConfig:
    def __init__(self, *a, **kw):
        self._d = {}
        self.user_config_dir = "/tmp/lights-off-test"
    def get(self, key, default=None):
        return self._d.get(key, default)
    def __setattr__(self, k, v):
        if k.startswith('_'):
            object.__setattr__(self, k, v)
        else:
            self._d[k] = v
            object.__setattr__(self, k, v)
tweak_mod.Config = _FakeConfig

# Stub GUI modules. `lights_off` itself is the real package on disk; we only
# stub specific submodules so the heavy imports (wx, sound, timeline, etc.)
# don't fire when test_utils imports utils.
_stub_module("lights_off.GUI")
_stub_module("lights_off.GUI.main", window=mock.MagicMock())
_stub_module("lights_off.GUI.misc")

# Stub timeline / mastodon_account so globals import chain works
_stub_module("lights_off.timeline")
_stub_module("lights_off.mastodon_account")
app_mod = _stub_module("lights_off.application")
app_mod.name = "lights-off"
app_mod.version = "0.1"
app_mod.shortname = "lights-off"

from lights_off import globals as g
g.prefs = _FakeConfig()
g.prefs.tweetTemplate = "$account.acct$: $content$ $created_at$"
g.prefs.retweetTemplate = "Boosting $account.display_name$ ($account.acct$): $content$"
g.prefs.quoteTemplate = "Quoting $account.display_name$ ($account.acct$): $content$"
g.prefs.userTemplate = "$display_name$ ($acct$)"
g.prefs.demojify = False
g.prefs.demojify_tweet = False
g.prefs.errors = False
g.prefs.use24HourTime = False
g.users = []
g.unknown_users = []
g.currentAccount = None
g.accounts = []

from lights_off import utils


# ---------------------------------------------------------------------------
# Helpers to build minimal Mastodon-like status objects
# ---------------------------------------------------------------------------

class AttrDict(dict):
    """dict that allows attribute access — mimics Mastodon.py AttribAccessDict."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value


_next_id = iter(range(1, 10000))

def make_account(acct="user@mastodon.social", display_name="Test User", id=None):
    if id is None:
        id = next(_next_id)
    return AttrDict(acct=acct, display_name=display_name, id=id, note="bio")


def make_status(content="<p>Hello world</p>", acct="user@mastodon.social",
                reblog=None, spoiler_text="", in_reply_to_id=None,
                media_attachments=None, id=42, url="https://mastodon.social/@user/42",
                mentions=None):
    import datetime
    return AttrDict(
        id=id,
        content=content,
        account=make_account(acct),
        reblog=reblog,
        spoiler_text=spoiler_text,
        in_reply_to_id=in_reply_to_id,
        media_attachments=media_attachments or [],
        url=url,
        created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
        favourited=False,
        favourites_count=0,
        reblogs_count=0,
        mentions=mentions or [],
        sensitive=False,
    )


# ---------------------------------------------------------------------------
# strip_html
# ---------------------------------------------------------------------------

class TestStripHtml:
    def test_plain_paragraph(self):
        assert utils.strip_html("<p>Hello</p>") == "Hello"

    def test_nested_tags(self):
        assert utils.strip_html("<p><strong>bold</strong> text</p>") == "bold text"

    def test_empty_string(self):
        assert utils.strip_html("") == ""

    def test_entities_decoded(self):
        import html
        raw = html.unescape("<p>AT&amp;T</p>")
        assert utils.strip_html(raw) == "AT&T"

    def test_no_tags(self):
        assert utils.strip_html("plain text") == "plain text"

    def test_br_tag(self):
        result = utils.strip_html("<p>line1<br/>line2</p>")
        assert "line1" in result and "line2" in result


# ---------------------------------------------------------------------------
# process_tweet
# ---------------------------------------------------------------------------

class TestProcessTweet:
    def test_strips_html(self):
        s = make_status("<p>Hello <strong>world</strong></p>")
        text = utils.process_tweet(s, return_only_text=True)
        assert text == "Hello world"
        assert "<" not in text

    def test_reblog_uses_boost_template(self):
        g.prefs.retweetTemplate = "Boosting $account.acct$: $content$"
        inner = make_status("<p>Original post</p>", acct="original@mastodon.social", id=1)
        outer = make_status("<p>ignored</p>", acct="booster@mastodon.social", reblog=inner, id=2)
        text = utils.process_tweet(outer, return_only_text=True)
        assert "Original post" in text

    def test_none_returns_empty(self):
        assert utils.process_tweet(None) == ""

    def test_returns_template_string_by_default(self):
        g.prefs.tweetTemplate = "$account.acct$: $content$"
        s = make_status("<p>Test</p>", acct="foo@bar.com")
        result = utils.process_tweet(s)
        assert "foo@bar.com" in result
        assert "Test" in result

    def test_cw_preserved_on_status_object(self):
        s = make_status("<p>Hidden</p>", spoiler_text="CW: politics")
        utils.process_tweet(s, return_only_text=True)
        assert s.spoiler_text == "CW: politics"


# ---------------------------------------------------------------------------
# find_urls_in_text
# ---------------------------------------------------------------------------

class TestFindUrls:
    def test_http_url(self):
        urls = utils.find_urls_in_text("check https://example.com out")
        assert "https://example.com" in urls

    def test_multiple_urls(self):
        text = "see https://a.com and https://b.org"
        urls = utils.find_urls_in_text(text)
        assert len(urls) == 2

    def test_no_urls(self):
        assert utils.find_urls_in_text("no urls here") == []


# ---------------------------------------------------------------------------
# isDuplicate
# ---------------------------------------------------------------------------

class TestIsDuplicate:
    def test_found(self):
        s = make_status(id=99)
        assert utils.isDuplicate(s, [make_status(id=99)]) is True

    def test_not_found(self):
        s = make_status(id=99)
        assert utils.isDuplicate(s, [make_status(id=1), make_status(id=2)]) is False

    def test_empty_list(self):
        assert utils.isDuplicate(make_status(id=1), []) is False

    def test_string_vs_int_id(self):
        s = make_status(id="99")
        assert utils.isDuplicate(s, [make_status(id=99)]) is True


# ---------------------------------------------------------------------------
# add_users
# ---------------------------------------------------------------------------

class TestAddUsers:
    def setup_method(self):
        g.users = []

    def test_adds_account(self):
        s = make_status(acct="foo@bar.com")
        utils.add_users(s)
        assert any(u.acct == "foo@bar.com" for u in g.users)

    def test_adds_reblog_account(self):
        inner = make_status(acct="orig@mastodon.social", id=1)
        outer = make_status(acct="booster@mastodon.social", reblog=inner, id=2)
        utils.add_users(outer)
        accts = [u.acct for u in g.users]
        assert "orig@mastodon.social" in accts
        assert "booster@mastodon.social" in accts

    def test_deduplicates(self):
        account = make_account("dup@mastodon.social")
        g.users = [account]
        s = make_status(acct="dup@mastodon.social")
        s.account = account
        utils.add_users(s)
        assert len([u for u in g.users if u.acct == "dup@mastodon.social"]) == 1


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_returns_string(self):
        import datetime
        d = datetime.datetime(2024, 6, 15, 14, 30, 0)
        result = utils.parse_date(d)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_today_omits_date(self):
        import datetime
        now = datetime.datetime.now()
        result = utils.parse_date(now)
        # today's date should not be in the string (only time shown)
        today_str = now.strftime("%m/%d/%Y")
        assert today_str not in result


# ---------------------------------------------------------------------------
# demojify
# ---------------------------------------------------------------------------

class TestDemojify:
    def test_strips_emoji(self):
        result = utils.demojify("hello 🌍 world")
        assert "🌍" not in result
        assert "hello" in result

    def test_plain_text_unchanged(self):
        assert utils.demojify("plain text") == "plain text"
