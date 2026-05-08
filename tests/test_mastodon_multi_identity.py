"""
Tests that verify each identity in .env can authenticate independently.
"""
import os
import re
import pytest
from mastodon import Mastodon


pytestmark = pytest.mark.live


def _load_env(path=".env"):
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


def _identities_from_env(env):
    """Return list of (name, base_url, client_id, client_secret, access_token)."""
    names = set()
    for k in env:
        m = re.match(r'^MASTODON_ID_([A-Z0-9]+)_BASE_URL$', k)
        if m:
            names.add(m.group(1))
    identities = []
    for name in sorted(names):
        prefix = f"MASTODON_ID_{name}_"
        base_url = env.get(prefix + "BASE_URL", "")
        client_id = env.get(prefix + "CLIENT_ID", "")
        client_secret = env.get(prefix + "CLIENT_SECRET", "")
        access_token = env.get(prefix + "ACCESS_TOKEN", "")
        if base_url and client_id and client_secret and access_token:
            identities.append((name, base_url, client_id, client_secret, access_token))
    return identities


_env = _load_env()
_identities = _identities_from_env(_env)


@pytest.mark.parametrize("name,base_url,client_id,client_secret,access_token", _identities)
def test_identity_can_authenticate(name, base_url, client_id, client_secret, access_token):
    """Each named identity should be able to call me() successfully."""
    api = Mastodon(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        api_base_url=base_url,
    )
    me = api.me()
    assert me.acct, f"Identity {name} at {base_url}: me() returned empty acct"
    print(f"  {name}: {me.acct} @ {base_url}")


@pytest.mark.parametrize("name,base_url,client_id,client_secret,access_token", _identities)
def test_identity_home_timeline(name, base_url, client_id, client_secret, access_token):
    """Each identity should be able to fetch a home timeline."""
    api = Mastodon(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        api_base_url=base_url,
    )
    tl = api.timeline_home(limit=3)
    assert isinstance(tl, list), f"Identity {name}: timeline_home did not return a list"
