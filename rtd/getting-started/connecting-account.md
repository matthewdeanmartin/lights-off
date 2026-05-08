# Connecting your Mastodon account

## Finding your instance URL

Your instance URL is the base URL of the Mastodon server your account is on. You can find
it in the address bar when you log in via a web browser. Examples:

| Server | Instance URL |
|---|---|
| Mastodon (flagship) | `https://mastodon.social` |
| Fosstodon | `https://fosstodon.org` |
| Mastodon Online | `https://mastodon.online` |
| Your own server | `https://yourserver.example.com` |

## First-time setup

1. **Launch Lights Off.** The accounts dialog opens automatically if no account is saved.

2. **Enter your instance URL** when prompted. Include the `https://` prefix; omit any
   trailing slash.

3. **Authorise in the browser.** A browser window opens to your instance's OAuth consent
   page. Log in if needed, then click **Authorise**.

4. **Copy the code.** After authorisation the browser shows a short code. Copy it.

5. **Paste the code** into the dialog in Lights Off and press **Enter**.

Lights Off stores the access token in your user config directory. On Windows this is
`%APPDATA%\lights-off\`; on macOS it is `~/Library/Application Support/lights-off/`.

## Adding a second account

You can add accounts on additional instances via **Application menu → Accounts**
(shortcut: **Ctrl+A**). Each instance gets its own OAuth registration stored separately.

## Removing an account

Delete the account's config folder from the platform config directory listed above, then
restart Lights Off.

## OAuth scopes requested

Lights Off requests the following Mastodon OAuth scopes:

| Scope | Used for |
|---|---|
| `read` | Reading timelines, notifications, DMs, profile |
| `write` | Posting, boosting, favouriting, following, blocking |
| `follow` | Managing follow/block/mute lists |

The app does not request admin scopes and cannot perform moderation actions.
