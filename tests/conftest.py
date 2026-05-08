"""
Shared fixtures for lights-off tests.

Loads credentials from .env (bash export format) and builds a live
Mastodon API client.  Tests that hit the network are marked `live` and
skipped automatically when credentials are absent.
"""
import os
import re
import sys
import pathlib
import pytest
from mastodon import Mastodon

# Ensure project root is on sys.path so `import globals`, `import utils` etc. work
_root = str(pathlib.Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)


def _load_env(path=".env"):
    """Parse `export KEY=VALUE` lines from a bash-style .env file."""
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                m = re.match(r'^export\s+([A-Z_][A-Z0-9_]*)=(.*)$', line)
                if m:
                    env[m.group(1)] = m.group(2).strip()
    except FileNotFoundError:
        pass
    return env


_env = _load_env()

# Inject into os.environ so sub-modules that read os.environ also see them
for k, v in _env.items():
    os.environ.setdefault(k, v)

_has_creds = all(
    _env.get(k)
    for k in ("MASTODON_BASE_URL", "MASTODON_CLIENT_ID",
              "MASTODON_CLIENT_SECRET", "MASTODON_ACCESS_TOKEN")
)


@pytest.fixture(scope="session")
def api():
    """Return a live Mastodon client using primary credentials from .env."""
    if not _has_creds:
        pytest.skip("No Mastodon credentials in .env")
    return Mastodon(
        client_id=_env["MASTODON_CLIENT_ID"],
        client_secret=_env["MASTODON_CLIENT_SECRET"],
        access_token=_env["MASTODON_ACCESS_TOKEN"],
        api_base_url=_env["MASTODON_BASE_URL"],
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live: test requires live Mastodon API credentials")
    config.addinivalue_line("markers", "live_write: live test that creates or mutates data")
