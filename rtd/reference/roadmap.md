# Roadmap

## Completed

- [x] Project rename and packaging (Quinter → lights-off)
- [x] Mastodon authentication (OAuth 2.0, multi-instance)
- [x] Core timeline data layer (home, notifications, messages, likes, sent)
- [x] Posting actions (new post, reply, boost, quote, favourite, delete)
- [x] Social actions (follow, unfollow, block, unblock, mute, unmute)
- [x] List management
- [x] User timeline, search, user search
- [x] Streaming (real-time updates via Mastodon streaming API)
- [x] Screen reader integration (Windows: Tolk/SAPI; macOS: accessible_output2)
- [x] Sound effects (earcons via sound_lib)
- [x] PyPI packaging with hatchling

## Planned

- [ ] Speech Dispatcher integration for Linux
- [ ] Settings UI for screen reader preference (SAPI vs NVDA vs JAWS)
- [ ] Content-warning / spoiler text display and composition
- [ ] Poll display and voting
- [ ] Proper DM conversation threading
- [ ] Sound on Linux (when a suitable cross-platform backend is available)
- [ ] Custom keybinding file support (keymap.keymap)
- [ ] Accessibility audit against NVDA and JAWS
