# Quickstart

## 1. Install

```
pipx install lights-off
```

See [Installation](../installation/overview.md) for platform-specific details.

## 2. Launch

```
lights-off
```

## 3. Connect your Mastodon account

On the first run a dialog asks for your **instance URL**. Type the full URL of your
Mastodon server, e.g.:

```
https://mastodon.social
```

The application registers itself with your instance (no credentials stored yet) and then
opens a browser window where you log in and authorise Lights Off. Copy the code from the
browser back into the dialog that appears.

Your access token is saved locally. You will not be asked again unless you remove the
account or the token is revoked.

See [Connecting your account](connecting-account.md) for a step-by-step walkthrough.

## 4. Navigate

The window has two list boxes:

- **Timelines** (top) — lists the feeds available for the active account (Home,
  Notifications, Messages, Likes, Sent, plus any user/search timelines you have opened).
- **Contents** (bottom) — lists the posts in the selected timeline.

Use **Tab** to move between the two boxes and **arrow keys** to move within each list.
Each post is spoken as you select it.

Press **F5** to refresh the current timeline.

## 5. Common actions

| Action | Shortcut |
|---|---|
| New post | Ctrl+N |
| Reply | Ctrl+R |
| Boost | Ctrl+Shift+R |
| Favourite | Ctrl+L |
| Open URL in post | Ctrl+O |
| View full post | Enter |
| Refresh timeline | F5 |
| Quit | Alt+F4 |

See the full [Keyboard reference](keyboard-reference.md) for all shortcuts.
