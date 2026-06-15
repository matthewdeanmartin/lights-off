"""Integration fixtures: drive MastodonAccount against a real HTTP mock.

These tests do **not** touch a live Mastodon and need no API keys. They boot the
``mastodon_mock`` package (published on PyPI) as a uvicorn server on a free port
and point a ``MastodonAccount`` at it. ``mastodon_mock`` is a *stateful*
simulation — a status you POST shows up in the next GET of that account's
timeline — so MastodonAccount's thin Mastodon.py wrappers (``tweet``, ``like``,
``retweet``, ``follow``, ``_paginate``, the follower/friend analysis, …) can be
exercised end to end over HTTP, exactly as they would be against a real instance.

MastodonAccount.__init__ is heavily GUI-coupled (wx, sound, threads, OAuth), so
these tests **skip __init__** and build the object via ``object.__new__``, wiring
just the attributes the wrapper methods need: a real ``api`` (Mastodon.py client
pointed at the mock), ``me``, and a fake ``globals`` for ``prefs.user_limit``.
That mirrors the unit suite in ``tests/test_mastodon_account.py``; the difference
is that ``api`` here is a real client talking to a real server, not a MagicMock.

The whole package self-skips when it cannot run:

* on Python < 3.13 (the mock's ``requires-python``), or
* if ``mastodon_mock`` is not installed (install ``mastodon_mock[test]``).

Run just this suite::

    uv run pytest test_integration
"""

from __future__ import annotations

import sys
import types
import unittest.mock as mock
from collections.abc import Iterator

import pytest

# --- Hard preconditions: skip the entire package rather than error on collect ---

if sys.version_info < (3, 13):
    pytest.skip(
        "mastodon_mock requires Python >= 3.13; skipping mock integration suite",
        allow_module_level=True,
    )

pytest.importorskip(
    "mastodon_mock",
    reason="install mastodon_mock[test] to run these tests",
)

from mastodon import Mastodon  # noqa: E402

from mastodon_mock.config import (  # noqa: E402
    SeedAccount,
    SeedConfig,
    SeedFollow,
    SeedStatus,
)
from mastodon_mock.testing import MockServer  # noqa: E402


# ---------------------------------------------------------------------------
# Stub the heavy GUI/sound deps so lights_off.mastodon_account imports without a
# display, audio device, or screen reader — same approach as the unit suite.
# ---------------------------------------------------------------------------

def _stub(name: str, **attrs: object) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules.setdefault(name, module)
    return module


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
    """A stand-in for tweak.Config that never touches disk."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._d: dict[str, object] = {}
        self.user_config_dir = "/tmp/lights-off-test"

    def get(self, key: str, default: object = None) -> object:
        return self._d.get(key, default)

    def __setattr__(self, key: str, value: object) -> None:
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self._d[key] = value
            object.__setattr__(self, key, value)


tweak_mod.Config = _FakeConfig

gui_pkg = types.ModuleType("lights_off.GUI")
gui_pkg.__path__ = []  # mark as a package
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

# test_utils.py (unit suite) stubs mastodon_account as a bare module; force the
# real module so the wrapper methods under test are the genuine article.
sys.modules.pop("lights_off.mastodon_account", None)
import importlib  # noqa: E402

import lights_off.mastodon_account as mastodon_account_module  # noqa: E402

importlib.reload(mastodon_account_module)


class _FakeGlobals:
    """A minimal stand-in for lights_off.globals used by the wrapper methods."""


def _fresh_fake_globals() -> _FakeGlobals:
    fake = _FakeGlobals()
    prefs = _FakeConfig()
    prefs.user_limit = 4
    prefs.count = 20
    prefs.streaming = False
    fake.prefs = prefs
    fake.currentAccount = None
    return fake


# ---------------------------------------------------------------------------
# Seed: "me" follows "friend", who has a couple of statuses, so home is
# non-empty and the follower/friend analysis has rows to chew on.
# ---------------------------------------------------------------------------

ME_TOKEN = "me_token"
FRIEND_TOKEN = "friend_token"

INTEGRATION_SEED = SeedConfig(
    accounts=[
        SeedAccount(username="me", display_name="Lights Off User", access_token=ME_TOKEN),
        SeedAccount(username="friend", display_name="A Friend", access_token=FRIEND_TOKEN),
        # A third account "me" does not follow yet — a target for follow/block/mute.
        SeedAccount(username="stranger", display_name="A Stranger", access_token="stranger_token"),
    ],
    follows=[SeedFollow(follower="me", following="friend")],
    statuses=[
        SeedStatus(account="friend", text="hello from the timeline"),
        SeedStatus(account="friend", text="a second friendly post"),
    ],
)


@pytest.fixture(scope="session")
def _mock_server_session() -> Iterator[MockServer]:
    """One started server for the whole session (fast: no per-test boot)."""
    with MockServer(seed=INTEGRATION_SEED) as server:
        yield server


@pytest.fixture
def mock_server(_mock_server_session: MockServer) -> MockServer:
    """The session server, ``reset()``-ed to seed state before each test.

    Resetting per test keeps tests independent despite the shared server: a test
    that unfollows "friend" or follows "stranger" must not bleed into the next.
    ``POST /api/v1/_mock/reset`` drops every table and re-applies the seed.
    """
    _mock_server_session.reset()
    return _mock_server_session


@pytest.fixture(autouse=True)
def patched_globals(monkeypatch: pytest.MonkeyPatch) -> Iterator[_FakeGlobals]:
    """Point mastodon_account.globals at a fresh fake for each test."""
    fake = _fresh_fake_globals()
    monkeypatch.setattr(mastodon_account_module, "globals", fake)
    yield fake


def _build_account(api: Mastodon) -> object:
    """A MastodonAccount with a real ``api`` but no GUI __init__ run."""
    account = object.__new__(mastodon_account_module.MastodonAccount)
    account.api = api
    account.me = api.me()
    account.prefs = _FakeConfig()
    account.timelines = []
    account.currentTimeline = None
    account.currentIndex = 0
    account.currentStatus = None
    account.ready = False
    return account


@pytest.fixture
def me_account(mock_server: MockServer):
    """A MastodonAccount logged in as "me", pointed at the mock."""
    return _build_account(mock_server.client("me"))


@pytest.fixture
def friend_account(mock_server: MockServer):
    """A second MastodonAccount (as "friend") to set up state "me" reads back."""
    return _build_account(mock_server.client("friend"))


@pytest.fixture
def friend_client(mock_server: MockServer) -> Mastodon:
    """A raw Mastodon.py client as "friend" — to author inbound state."""
    return mock_server.client("friend")
