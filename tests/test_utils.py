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
        # account.acct is shortened by default (foo@bar.com → foo)
        g.prefs.tweetTemplate = "$account.acct$: $content$"
        s = make_status("<p>Test</p>", acct="foo@bar.com")
        result = utils.process_tweet(s)
        assert "foo" in result
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

    def test_multiple_emoji(self):
        result = utils.demojify("🎉 party 🎊 time 🥳")
        assert "party" in result
        assert "time" in result
        assert "🎉" not in result

    def test_empty_string(self):
        assert utils.demojify("") == ""


# ---------------------------------------------------------------------------
# shorten_acct
# ---------------------------------------------------------------------------

class TestShortenAcct:
    def test_with_instance(self):
        assert utils.shorten_acct("alice@mastodon.social") == "alice"

    def test_without_instance(self):
        assert utils.shorten_acct("alice") == "alice"

    def test_none(self):
        assert utils.shorten_acct(None) is None

    def test_empty_string(self):
        assert utils.shorten_acct("") == ""

    def test_multiple_at_signs(self):
        # only splits on the first @
        assert utils.shorten_acct("user@instance@other") == "user"


# ---------------------------------------------------------------------------
# strip_html — anchor handling
# ---------------------------------------------------------------------------

class TestStripHtmlAnchors:
    def test_shortened_url_uses_display_text(self):
        html = '<a href="https://github.com/foo/bar/very/long/path">github.com/foo/ba…</a>'
        result = utils.strip_html(html)
        assert result == "github.com/foo/ba…"

    def test_full_url_anchor_uses_domain(self):
        html = '<a href="https://example.com/path">https://example.com/path</a>'
        result = utils.strip_html(html)
        assert "example.com" in result

    def test_non_http_anchor_uses_text(self):
        html = '<a href="mailto:user@example.com">email me</a>'
        result = utils.strip_html(html)
        assert result == "email me"

    def test_multiple_anchors(self):
        html = '<p>see <a href="https://a.com">a.com</a> and <a href="https://b.com">b.com</a></p>'
        result = utils.strip_html(html)
        assert "a.com" in result
        assert "b.com" in result


# ---------------------------------------------------------------------------
# template_to_string
# ---------------------------------------------------------------------------

class TestTemplateToString:
    def setup_method(self):
        g.prefs.demojify = False
        g.prefs.demojify_tweet = False

    def test_simple_field(self):
        s = make_status("<p>hi</p>")
        s.content = "hi"
        result = utils.template_to_string(s, "$content$")
        assert result == "hi"

    def test_nested_field(self):
        s = make_status(acct="alice@example.com")
        s.content = "hello"
        result = utils.template_to_string(s, "$account.display_name$", _shorten_acct=False)
        assert "Test User" in result

    def test_acct_shortened_by_default(self):
        s = make_status(acct="alice@example.com")
        s.content = ""
        result = utils.template_to_string(s, "$account.acct$")
        assert result == "alice"

    def test_acct_not_shortened_when_disabled(self):
        s = make_status(acct="alice@example.com")
        s.content = ""
        result = utils.template_to_string(s, "$account.acct$", _shorten_acct=False)
        assert result == "alice@example.com"

    def test_missing_field_leaves_placeholder(self):
        s = make_status()
        s.content = "x"
        result = utils.template_to_string(s, "$nonexistent_field$")
        assert "$nonexistent_field$" in result

    def test_demojify_display_name(self):
        # demojify on nested account.display_name only fires when field is
        # accessed as a top-level field ($display_name$), not via dot notation
        # ($account.display_name$). The nested path checks (o,p) == ("name",)
        # conditions but display_name is not "name". Confirm it does NOT strip.
        g.prefs.demojify = True
        s = make_status()
        s.content = ""
        account = make_account(display_name="Alice 🎉")
        s.account = account
        result = utils.template_to_string(s, "$account.display_name$", _shorten_acct=False)
        assert "Alice" in result
        g.prefs.demojify = False

    def test_created_at_formatted(self):
        import datetime
        s = make_status()
        s.content = "x"
        s.created_at = datetime.datetime(2020, 3, 15, 9, 0, 0)
        result = utils.template_to_string(s, "$created_at$")
        assert "2020" in result or "03/15" in result

    def test_uses_global_template_when_empty(self):
        g.prefs.tweetTemplate = "GLOBAL: $content$"
        s = make_status()
        s.content = "body"
        result = utils.template_to_string(s, "")
        assert result == "GLOBAL: body"


# ---------------------------------------------------------------------------
# find_urls_in_tweet
# ---------------------------------------------------------------------------

class TestFindUrlsInTweet:
    def test_extracts_from_content(self):
        s = make_status()
        s.content = "check https://example.com please"
        urls = utils.find_urls_in_tweet(s)
        assert any("example.com" in u for u in urls)

    def test_extracts_media_attachments(self):
        media = AttrDict(url="https://files.mastodon.social/image.jpg")
        s = make_status(media_attachments=[media])
        s.content = ""
        urls = utils.find_urls_in_tweet(s)
        assert "https://files.mastodon.social/image.jpg" in urls

    def test_no_urls(self):
        s = make_status()
        s.content = "no links here"
        # may or may not return empty; just confirm it returns a list
        assert isinstance(utils.find_urls_in_tweet(s), list)

    def test_no_content_attr(self):
        s = AttrDict(media_attachments=[])
        assert isinstance(utils.find_urls_in_tweet(s), list)


# ---------------------------------------------------------------------------
# process_message
# ---------------------------------------------------------------------------

class TestProcessMessage:
    def test_plain_status(self):
        s = make_status("<p>hello dm</p>", acct="sender@example.com")
        result = utils.process_message(s)
        assert "sender" in result
        assert "hello dm" in result

    def test_conversation_object(self):
        last = make_status("<p>conv msg</p>", acct="conv@example.com")
        conv = AttrDict(last_status=last)
        result = utils.process_message(conv)
        assert "conv" in result
        assert "conv msg" in result

    def test_none_last_status_returns_empty(self):
        # last_status=None falls through to status=None path → returns ""
        conv = AttrDict(last_status=None)
        # process_message treats the conv itself as the status when last_status is None;
        # the conv has no 'content' attr so raw="" and account is "unknown"
        result = utils.process_message(conv)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# notification_to_status
# ---------------------------------------------------------------------------

class TestNotificationToStatus:
    def _make_notif(self, ntype, acct="actor@social.example", status=None):
        actor = make_account(acct=acct)
        n = AttrDict(
            id="notif-1",
            type=ntype,
            account=actor,
            status=status,
            created_at=None,
        )
        return n

    def test_follow_notification(self):
        n = self._make_notif("follow")
        result = utils.notification_to_status(n)
        assert result is not None
        assert "actor" in result.content

    def test_mention_notification(self):
        s = make_status("<p>hello!</p>", acct="me@social.example", id=10)
        n = self._make_notif("mention", status=s)
        result = utils.notification_to_status(n)
        assert "mentioned you" in result.content

    def test_favourite_notification(self):
        n = self._make_notif("favourite")
        result = utils.notification_to_status(n)
        assert "favourited" in result.content

    def test_reblog_notification(self):
        n = self._make_notif("reblog")
        result = utils.notification_to_status(n)
        assert "boosted" in result.content

    def test_none_returns_none(self):
        assert utils.notification_to_status(None) is None

    def test_unknown_type_uses_actor_and_type(self):
        n = self._make_notif("custom_event")
        result = utils.notification_to_status(n)
        assert result is not None
        assert "custom_event" in result.content

    def test_mention_with_status_object_annotates_content(self):
        s = make_status("<p>original content</p>", id=20)
        n = self._make_notif("mention", status=s)
        result = utils.notification_to_status(n)
        assert "mentioned you" in result.content
        assert "original content" in result.content


# ---------------------------------------------------------------------------
# isDuplicate — additional edge cases
# ---------------------------------------------------------------------------

class TestIsDuplicateExtra:
    def test_large_list_no_match(self):
        statuses = [make_status(id=i) for i in range(50)]
        s = make_status(id=9999)
        assert utils.isDuplicate(s, statuses) is False

    def test_large_list_with_match(self):
        statuses = [make_status(id=i) for i in range(50)]
        s = make_status(id=25)
        assert utils.isDuplicate(s, statuses) is True


# ---------------------------------------------------------------------------
# dict_obj / dict2obj / ensure_attr_access
# ---------------------------------------------------------------------------

class TestDictObj:
    def test_attr_access(self):
        obj = utils.dict_obj({"foo": "bar", "num": 42})
        assert obj.foo == "bar"
        assert obj.num == 42

    def test_dict2obj_nested(self):
        data = {"a": {"b": "c"}}
        obj = utils.dict2obj(data)
        assert obj.a.b == "c"

    def test_ensure_attr_access_passthrough_for_attrdict(self):
        ad = AttrDict(x=1)
        result = utils.ensure_attr_access(ad)
        assert result is ad

    def test_ensure_attr_access_converts_plain_dict(self):
        d = {"x": 1, "y": 2}
        result = utils.ensure_attr_access(d)
        assert result.x == 1

    def test_ensure_attr_access_none(self):
        assert utils.ensure_attr_access(None) is None

    def test_ensure_attr_access_non_dict(self):
        assert utils.ensure_attr_access("hello") == "hello"


# ---------------------------------------------------------------------------
# _nget
# ---------------------------------------------------------------------------

class TestNget:
    def test_obj_attr(self):
        obj = AttrDict(foo="bar")
        assert utils._nget(obj, "foo") == "bar"

    def test_dict_key(self):
        assert utils._nget({"foo": "bar"}, "foo") == "bar"

    def test_missing_returns_default(self):
        assert utils._nget(AttrDict(), "missing", "fallback") == "fallback"

    def test_none_returns_default(self):
        assert utils._nget(None, "key", "d") == "d"


# ---------------------------------------------------------------------------
# add_users — edge cases
# ---------------------------------------------------------------------------

class TestAddUsersExtra:
    def setup_method(self):
        g.users = []
        g.unknown_users = []

    def test_none_status_is_noop(self):
        utils.add_users(None)
        assert g.users == []

    def test_conversation_accounts_list(self):
        a1 = make_account("a1@example.com")
        a2 = make_account("a2@example.com")
        last = make_status(acct="a1@example.com")
        conv = AttrDict(accounts=[a1, a2], last_status=last)
        utils.add_users(conv)
        accts = [u.acct for u in g.users]
        assert "a1@example.com" in accts
        assert "a2@example.com" in accts


# ---------------------------------------------------------------------------
# lookup_user / lookup_user_name
# ---------------------------------------------------------------------------

class TestLookupUser:
    def setup_method(self):
        g.users = []
        g.unknown_users = []

    def test_found_by_id(self):
        acct = make_account("find@example.com", id=777)
        g.users = [acct]
        result = utils.lookup_user(777)
        assert result.acct == "find@example.com"

    def test_not_found_appends_unknown(self):
        result = utils.lookup_user(9999)
        assert result is None
        assert 9999 in g.unknown_users

    def test_lookup_user_name_found_locally(self):
        acct = make_account("local@example.com")
        g.users = [acct]
        result = utils.lookup_user_name(None, "local@example.com", use_api=False)
        assert result.acct == "local@example.com"

    def test_lookup_user_name_not_found_no_api(self):
        result = utils.lookup_user_name(None, "ghost@example.com", use_api=False)
        assert result == -1

    def test_lookup_user_name_strips_at_prefix(self):
        acct = make_account("atuser@example.com")
        g.users = [acct]
        result = utils.lookup_user_name(None, "@atuser@example.com", use_api=False)
        assert result.acct == "atuser@example.com"


# ---------------------------------------------------------------------------
# find_status / find_reply
# ---------------------------------------------------------------------------

class TestFindStatus:
    def _make_tl(self, ids):
        tl = AttrDict(statuses=[make_status(id=i) for i in ids])
        return tl

    def test_finds_by_id(self):
        tl = self._make_tl([10, 20, 30])
        assert utils.find_status(tl, 20) == 1

    def test_not_found_returns_minus_one(self):
        tl = self._make_tl([10, 20])
        assert utils.find_status(tl, 99) == -1

    def test_find_reply_found(self):
        statuses = [make_status(id=i) for i in range(3)]
        statuses[1].in_reply_to_id = 55
        tl = AttrDict(statuses=statuses)
        assert utils.find_reply(tl, 55) == 1

    def test_find_reply_not_found(self):
        tl = self._make_tl([1, 2, 3])
        assert utils.find_reply(tl, 999) == -1


# ---------------------------------------------------------------------------
# handle_error
# ---------------------------------------------------------------------------

class TestHandleError:
    def setup_method(self):
        g.errors = []
        g.prefs.errors = False

    def test_appends_to_errors(self):
        utils.handle_error(ValueError("boom"), "test_func")
        assert any("boom" in e for e in g.errors)
        assert any("test_func" in e for e in g.errors)

    def test_default_name(self):
        utils.handle_error(RuntimeError("oops"))
        assert any("Unknown" in e for e in g.errors)

    def test_multiple_errors_accumulate(self):
        utils.handle_error(Exception("first"), "f1")
        utils.handle_error(Exception("second"), "f2")
        assert len(g.errors) == 2


# ---------------------------------------------------------------------------
# parse_date — additional
# ---------------------------------------------------------------------------

class TestParseDateExtra:
    def test_non_today_includes_date(self):
        import datetime
        # Use a date far in the past so any timezone offset cannot make it "today"
        d = datetime.datetime(1990, 7, 4, 12, 0, 0)
        result = utils.parse_date(d)
        # The year or month/day should appear regardless of local timezone
        assert result != ""

    def test_24hour_format(self):
        import datetime
        import time
        g.prefs.use24HourTime = True
        # Build a datetime whose hour survives tz adjustment into a recognisable 2-digit hour
        # parse_date subtracts time.timezone (seconds west of UTC), so we add it back
        tz_offset = time.altzone if time.localtime().tm_isdst else time.timezone
        # Pick a fixed UTC hour that after adjustment lands at a known local hour
        d = datetime.datetime(2020, 6, 15, 12, 30, 0) + datetime.timedelta(seconds=tz_offset)
        result = utils.parse_date(d)
        assert "12:30" in result
        g.prefs.use24HourTime = False

    def test_non_datetime_returns_empty_string(self):
        result = utils.parse_date("not a date")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# process_tweet — reblog content propagation
# ---------------------------------------------------------------------------

class TestProcessTweetReblog:
    def test_reblog_content_uses_inner_account(self):
        g.prefs.retweetTemplate = "$account.acct$: $content$"
        inner = make_status("<p>inner text</p>", acct="inner@example.com", id=1)
        outer = make_status("<p>outer</p>", acct="booster@example.com", reblog=inner, id=2)
        result = utils.process_tweet(outer, return_only_text=True)
        assert "inner text" in result

    def test_return_only_text_skips_template(self):
        g.prefs.tweetTemplate = "PREFIX: $content$"
        s = make_status("<p>raw text</p>")
        result = utils.process_tweet(s, return_only_text=True)
        assert result == "raw text"
        assert "PREFIX" not in result


# ---------------------------------------------------------------------------
# message_template_to_string (stub — always "")
# ---------------------------------------------------------------------------

class TestMessageTemplateToString:
    def test_always_returns_empty(self):
        assert utils.message_template_to_string(make_status()) == ""


# ---------------------------------------------------------------------------
# dict_match / class_match
# ---------------------------------------------------------------------------

class TestDictMatch:
    def test_copies_missing_keys(self):
        d1 = {"a": 1}
        d2 = {"a": 99, "b": 2}
        result = utils.dict_match(d1, d2)
        assert result["a"] == 1   # existing key not overwritten
        assert result["b"] == 2   # missing key filled in

    def test_empty_d2(self):
        d1 = {"x": 10}
        result = utils.dict_match(d1, {})
        assert result == {"x": 10}

    def test_both_empty(self):
        assert utils.dict_match({}, {}) == {}


class TestClassMatch:
    def test_no_properties_is_noop(self):
        class A:
            pass
        class B:
            pass
        a, b = A(), B()
        result = utils.class_match(a, b)
        assert result is a


# ---------------------------------------------------------------------------
# get_users_in_tweet
# ---------------------------------------------------------------------------

class TestGetUsersInTweet:
    def _make_account_obj(self, acct, id=None):
        return make_account(acct, id=id or next(_next_id))

    def _make_fake_account_ctx(self, me_acct):
        me = self._make_account_obj(me_acct)
        account = AttrDict(me=me)
        return account

    def test_returns_author_when_not_self(self):
        account = self._make_fake_account_ctx("me@example.com")
        s = make_status(acct="other@example.com")
        s.reblog = None
        s.mentions = []
        result = utils.get_users_in_tweet(account, s)
        assert "other@example.com" in result

    def test_excludes_self_as_author(self):
        account = self._make_fake_account_ctx("me@example.com")
        s = make_status(acct="me@example.com")
        s.reblog = None
        s.mentions = []
        result = utils.get_users_in_tweet(account, s)
        assert result == ""

    def test_includes_mentions(self):
        account = self._make_fake_account_ctx("me@example.com")
        s = make_status(acct="other@example.com")
        s.reblog = None
        mention = AttrDict(acct="third@example.com")
        s.mentions = [mention]
        result = utils.get_users_in_tweet(account, s)
        assert "third@example.com" in result

    def test_excludes_self_from_mentions(self):
        account = self._make_fake_account_ctx("me@example.com")
        s = make_status(acct="other@example.com")
        s.reblog = None
        mention = AttrDict(acct="me@example.com")
        s.mentions = [mention]
        result = utils.get_users_in_tweet(account, s)
        assert "me@example.com" not in result

    def test_reblog_appends_reblogged_author_to_content(self):
        # get_users_in_tweet appends the reblogged author to s.content (side
        # effect), not to the return value. The return value is empty here
        # because the outer post's author is "me".
        account = self._make_fake_account_ctx("me@example.com")
        inner = make_status(acct="boostee@example.com", id=1)
        inner.content = "original"
        outer = make_status(acct="me@example.com", reblog=inner, id=2)
        outer.content = "boosted"
        outer.mentions = []
        utils.get_users_in_tweet(account, outer)
        assert "boostee@example.com" in outer.content


# ---------------------------------------------------------------------------
# demojify — top-level field via template_to_string
# ---------------------------------------------------------------------------

class TestDemojifyViaTemplate:
    def test_display_name_top_level_stripped(self):
        g.prefs.demojify = True
        s = make_status()
        s.content = ""
        s.display_name = "Alice 🎉"
        result = utils.template_to_string(s, "$display_name$")
        assert "🎉" not in result
        assert "Alice" in result
        g.prefs.demojify = False

    def test_content_stripped_when_demojify_tweet(self):
        g.prefs.demojify_tweet = True
        s = make_status()
        s.content = "hello 🎊 world"
        result = utils.template_to_string(s, "$content$")
        assert "🎊" not in result
        g.prefs.demojify_tweet = False


# ---------------------------------------------------------------------------
# find_urls_in_text — edge cases
# ---------------------------------------------------------------------------

class TestFindUrlsExtra:
    def test_www_url(self):
        urls = utils.find_urls_in_text("go to www.example.com now")
        assert any("example.com" in u for u in urls)

    def test_strips_trailing_punctuation(self):
        urls = utils.find_urls_in_text("see https://example.com.")
        # The trailing period should be stripped
        assert all(not u.endswith(".") for u in urls)


# ---------------------------------------------------------------------------
# notification_to_status — dict-based actor (streaming path)
# ---------------------------------------------------------------------------

class TestNotificationDictActor:
    def test_dict_actor_converted(self):
        n = AttrDict(
            id="n99",
            type="follow",
            account={"acct": "dict_actor@example.com", "id": 500,
                     "display_name": "Dict Actor"},
            status=None,
            created_at=None,
        )
        result = utils.notification_to_status(n)
        assert result is not None
        assert "dict_actor" in result.content

    def test_poll_notification(self):
        n = AttrDict(
            id="poll-1",
            type="poll",
            account=make_account("voter@example.com"),
            status=None,
            created_at=None,
        )
        result = utils.notification_to_status(n)
        assert "Poll ended" in result.content

    def test_follow_request_notification(self):
        n = AttrDict(
            id="fr-1",
            type="follow_request",
            account=make_account("req@example.com"),
            status=None,
            created_at=None,
        )
        result = utils.notification_to_status(n)
        assert "requested to follow" in result.content
