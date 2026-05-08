# lights-off: Mastodon Client Conversion Spec

Conversion of Quinter (Twitter client) to lights-off (Mastodon client).

## License Note

No license file exists in the repository. The only license reference is `Tolk.py` (LGPLv3, by Davy Kager). Before publishing, choose a license. Dependencies `accessible_output2` and `sound_lib` (accessibleapps) impose their own terms.

## Twitter → Mastodon Mapping

| Area | Twitter/Quinter | Mastodon equivalent |
|---|---|---|
| API library | `tweepy` | `Mastodon.py` |
| Auth | OAuth 1.0a PIN flow | OAuth 2.0 + instance URL |
| "Tweet" concept | `status` with `.text`, `.user`, `.id` | toot/status with `.content` (HTML), `.account`, `.id` |
| Direct messages | `get_direct_messages()` | Not supported in public API — drop |
| Retweet | `retweet()` | boost / `status_reblog()` |
| Quote tweet | `create_tweet(quote_tweet_id=)` | Not native — append URL manually |
| Like | `like()` | `status_favourite()` |
| Lists | Twitter lists (`list_id`) | Mastodon lists (`list_id`, similar API) |
| Search | `search_tweets(q=)` | `search_v2()` |
| Streaming | Tweepy `StreamListener` | `stream_user()` with `CallbackStreamListener` |
| User model | `.screen_name`, `.friends_count` | `.acct`, `.following_count`, `.followers_count` |
| Content | Plain text | HTML (strip with `html.parser`) |
| Character limit | 280 | Configurable per-instance (typically 500) |
| Instance | Fixed (api.twitter.com) | User-specified (e.g. mastodon.social) |
| URL in status | `t.co` shortlinks in entities | Inline in HTML content |
| Config name | `Quinter` | `lights-off` |

---

## Phase 1 — Project skeleton & rename

**Goal:** Create a clean `lights-off` repo with all Twitter branding removed and groundwork laid.

- [x] Rename `application.py`: `name="lights-off"`, `shortname="lights-off"`, bump version to `0.1`
- [x] Replace `requirements.txt`: swap `tweepy` → `Mastodon.py`, remove `twitter-text-parser`, keep `wxpython`, `accessible_output2`, `sound_lib`, `keyboard_handler`, `pyperclip`, `tweak`
- [x] Rename `twitter.py` → `mastodon_account.py`, class `twitter` → `MastodonAccount`
- [x] Update `globals.py` imports and all config names (`Quinter` → `lights-off`)
- [x] Rename `quinter.pyw` → `lights-off.pyw`
- [x] Remove `twishort.py` (Twitter-only URL expansion service)
- [x] Remove `streaming.py` (rewrite from scratch in Phase 6)
- [x] Rename sound references: `send_tweet` → `send_post`, `send_retweet` → `send_boost`

---

## Phase 2 — Authentication & account bootstrap

**Goal:** Replace the Twitter OAuth PIN flow with Mastodon OAuth 2.0 + instance selection.

Files: `mastodon_account.py` (`__init__`), `GUI/accounts.py`, `GUI/account_options.py`

- [x] Add "Instance URL" prompt stored in `account.prefs.instance`
- [x] Use `Mastodon.create_app()` once per instance to register the app (store `client_id`/`client_secret` per instance)
- [x] Use OAuth browser flow to obtain `access_token`
- [x] Store `access_token` + `instance` in `tweak.Config` per account (replacing `key`/`secret`)
- [x] Instantiate `Mastodon(access_token=..., api_base_url=...)` as `self.api`
- [x] Replace `self.me = self.api.verify_credentials()` → `self.me = self.api.me()`
- [x] Update window title to use `self.me.acct`

---

## Phase 3 — Core timeline data layer

**Goal:** Make timelines fetch and display Mastodon statuses correctly.

Files: `timeline.py`, `utils.py`

- [x] Replace timeline `func` assignments in `timeline.__init__`:
  - `home` → `self.api.timeline_home()`
  - `mentions` → `self.api.notifications(types=['mention'])`
  - `messages` → drop (no DM API); replace with "Notifications" timeline
  - `likes` → `self.api.favourites()`
  - `user` → `self.api.account_statuses(id)`
  - `list` → `self.api.timeline_list(list_id)`
  - `search` → `self.api.search_v2(q, result_type='statuses')`
- [x] Replace `count`/`tweet_mode` kwargs → `limit` kwarg
- [x] Replace `since_id`/`max_id` pagination (same kwarg names — minimal change)
- [x] Rewrite `utils.process_tweet()` → `utils.process_status()`:
  - Strip HTML from `.content` using `html.parser`
  - `.user.screen_name` → `.account.acct`
  - Handle `reblog` (boosted post) in place of `retweeted_status`
  - `.favorited` → `.favourited`
- [x] Drop `utils.process_message()` or convert to notification processing
- [x] Update `utils.add_users()` → `add_accounts()`, use `.account` not `.user`
- [x] Update `utils.lookup_user()` / `lookup_user_name()` → `self.api.account_search()`
- [x] Update `utils.lookup_status()` → `self.api.status(id)`
- [x] Rewrite `template_to_string()` for Mastodon field names
- [x] Update default templates in `globals.py`

---

## Phase 4 — Actions layer

**Goal:** Map all user actions to Mastodon API calls.

Files: `mastodon_account.py` methods, `GUI/misc.py`, `GUI/tweet.py`

- [x] `post(text, id=None)` → `self.api.status_post(text, in_reply_to_id=id)`
- [x] `boost(id)` → `self.api.status_reblog(id)`
- [x] `quote(status, text)` → `self.api.status_post(text + " " + status_url)`
- [x] `favourite(id)` → `self.api.status_favourite(id)`
- [x] `unfavourite(id)` → `self.api.status_unfavourite(id)`
- [x] `follow(username)` → resolve acct to ID, then `self.api.account_follow(id)`
- [x] `unfollow` / `block` / `unblock` → same pattern
- [x] `mute` / `unmute` → `self.api.account_mute(id)` / `account_unmute(id)`
- [x] `followers(id)` → `self.api.account_followers(id)`
- [x] `friends(id)` → `self.api.account_following(id)`
- [x] `update_profile` → `self.api.account_update_credentials(...)`
- [x] `delete` → `self.api.status_delete(id)`
- [x] Lists: `self.api.lists()`, add/remove: `self.api.list_accounts_add()` / `list_accounts_delete()`

---

## Phase 5 — GUI layer updates

**Goal:** Rename all Twitter-specific labels, menu items, and dialogs.

Files: `GUI/main.py`, `GUI/tweet.py`, `GUI/view.py`, `GUI/options.py`, `GUI/account_options.py`, `GUI/profile.py`, `GUI/search.py`, `GUI/lists.py`

- [x] Menu: "New tweet" → "New post", "Retweet" → "Boost", "Quote" → "Quote post", "Like" → "Favourite", "Messages" → remove
- [x] `GUI/tweet.py`: update char counter to use `instance.max_toot_chars`
- [x] `GUI/view.py`: update field rendering for Mastodon status fields
- [x] `GUI/options.py`: update templates/defaults
- [x] `GUI/account_options.py`: add instance URL display
- [x] `GUI/profile.py`: map fields (`display_name`, `note` for bio, `fields` array)
- [x] `OnTweetUrl` → construct `https://<instance>/@<acct>/<id>` URL
- [x] Stats dialog: "tweets sent" → "posts sent"
- [x] Remove QPlay download menu item (or keep as generic media player)
- [x] Add `spoiler_text` (content warning) field to `GUI/tweet.py`
- [x] Handle `sensitive` media flag

---

## Phase 6 — Streaming

**Goal:** Replace Tweepy streaming with Mastodon.py streaming.

File: new `streaming.py`

- [x] `Mastodon.stream_user(listener)` with a `CallbackStreamListener` subclass
- [x] Handle `on_update` (new post), `on_notification` (mention/boost/favourite/follow)
- [x] Wire back into `timeline.load(items=[...])` the same way current streaming does
- [x] Add streaming toggle in `GUI/options.py`

---

## Phase 7 — Polish & accessibility QA

**Goal:** Ensure the app works correctly with screen readers and matches accessible design.

- [x] Test all keyboard shortcuts with NVDA and JAWS on Windows
- [x] Verify `Tolk.py` (LGPLv3) still works
- [x] Verify `accessible_output2` speaks HTML-stripped content correctly
- [x] Test multi-account flow (multiple Mastodon instances)
- [x] Handle instance-specific differences (character limits, custom emoji, content warnings)
- [x] Handle `sensitive` media flag
- [x] Rename sound files: `send_tweet.ogg` → `send_post.ogg`, `send_retweet.ogg` → `send_boost.ogg`
- [x] Update `README.md` and `docs/changelog.txt`

---

## Key Risks

1. **DMs have no Mastodon equivalent** — needs design decision (drop the tab, or repurpose as Notifications)
2. **Mastodon status content is HTML** — must strip before passing to speech/display
3. **Multi-instance auth** — more complex than single-endpoint Twitter auth; each account needs its own `client_id`/`client_secret` per instance
