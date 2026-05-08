# Security

## Credential storage

Lights Off stores your Mastodon **access token** on disk in your platform config directory:

| Platform | Location |
|---|---|
| Windows | `%APPDATA%\lights-off\<instance>\` |
| macOS | `~/Library/Application Support/lights-off/<instance>/` |
| Linux | `~/.config/lights-off/<instance>/` |

The access token allows the app to read and post on your behalf. It is stored as a plain
text file with standard user-only file permissions. **Do not share this directory.**

OAuth client credentials (`client_id` and `client_secret`) are stored in
`client_secrets.secret` in the same directory. These are public-ish (they identify the
app registration, not your account) but there is no reason to share them either.

## No password storage

Your Mastodon password is never seen or stored by Lights Off. Authentication is handled
entirely through the Mastodon OAuth 2.0 browser flow; Lights Off only ever receives the
resulting access token.

## Network access

Lights Off makes HTTPS calls only to:

- Your configured Mastodon instance (API calls and streaming)
- `pypi.org` on startup (version check — can be skipped)
- URLs you explicitly open via Ctrl+O (in your default browser)

It does not phone home, send analytics, or contact any Anthropic or third-party service.

## Reporting vulnerabilities

Open an issue at <https://github.com/matthewdeanmartin/lights-off/issues> with the label
**security**. For sensitive issues, email matthewdeanmartin@gmail.com directly.
