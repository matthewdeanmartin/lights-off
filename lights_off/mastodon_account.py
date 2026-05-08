import datetime
import os
import platform
import sys
import threading
import webbrowser

from mastodon import Mastodon, MastodonError

from lights_off import application
from lights_off import globals
from lights_off import speak
from lights_off import streaming
from lights_off import timeline
import tweak
from lights_off.GUI import main, misc
from lights_off.GUI.ask import ask
from lights_off import api_log

APP_NAME = "lights-off"
APP_SCOPES = ["read", "write", "follow"]


def _get_or_register_app(instance_url, confpath):
    """Return (client_id, client_secret) for this instance, registering if needed."""
    secrets_file = os.path.join(confpath, "client_secrets.secret")
    if os.path.exists(secrets_file):
        with open(secrets_file) as f:
            lines = f.read().splitlines()
        if len(lines) == 2:
            return lines[0], lines[1]

    client_id, client_secret = Mastodon.create_app(
        APP_NAME,
        api_base_url=instance_url,
        scopes=APP_SCOPES,
    )
    with open(secrets_file, "w") as f:
        f.write(client_id + "\n" + client_secret)
    return client_id, client_secret


class MastodonAccount(object):
    def __init__(self, index):
        self.ready = False
        self.timelines = []
        self.currentTimeline = None
        self.currentIndex = 0
        self.currentStatus = None
        self.confpath = ""

        self.prefs = tweak.Config(name="lights-off/account" + str(index), autosave=True)
        self.confpath = self.prefs.user_config_dir

        self.prefs.access_token = self.prefs.get("access_token", "")
        self.prefs.instance = self.prefs.get("instance", "")
        self.prefs.user_timelines = self.prefs.get("user_timelines", [])
        self.prefs.list_timelines = self.prefs.get("list_timelines", [])
        self.prefs.search_timelines = self.prefs.get("search_timelines", [])
        self.prefs.follow_prompt = self.prefs.get("follow_prompt", False)
        self.prefs.footer = self.prefs.get("footer", "")
        self.prefs.soundpack = self.prefs.get("soundpack", "default")
        self.prefs.soundpan = self.prefs.get("soundpan", 0)

        needs_auth = (
            not self.prefs.access_token
            or not self.prefs.instance
        )

        if needs_auth:
            instance_url = ask(
                caption="Instance",
                message="Enter your Mastodon instance URL (e.g. https://mastodon.social):",
            )
            if not instance_url:
                sys.exit()
            instance_url = instance_url.strip().rstrip("/")
            if not instance_url.startswith("http"):
                instance_url = "https://" + instance_url
            self.prefs.instance = instance_url

        instance_confpath = os.path.join(
            self.confpath, self.prefs.instance.replace("://", "_").replace("/", "_")
        )
        os.makedirs(instance_confpath, exist_ok=True)

        client_id, client_secret = _get_or_register_app(self.prefs.instance, instance_confpath)

        if needs_auth:
            # Browser OAuth flow
            mastodon_temp = Mastodon(
                client_id=client_id,
                client_secret=client_secret,
                api_base_url=self.prefs.instance,
            )
            api_log.instrument(mastodon_temp, label="auth" + str(index))
            auth_url = mastodon_temp.auth_request_url(scopes=APP_SCOPES)
            if platform.system() != "Darwin":
                webbrowser.open(auth_url)
            else:
                os.system("open " + auth_url)
            code = ask(caption="Authorization code", message="Enter the authorization code from your browser:")
            if not code:
                sys.exit()
            access_token = mastodon_temp.log_in(
                code=code,
                scopes=APP_SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
            self.prefs.access_token = access_token

        self.api = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=self.prefs.access_token,
            api_base_url=self.prefs.instance,
        )
        api_log.instrument(self.api, label="acct" + str(index))

        self.me = self.api.me()
        self.instance_info = self.api.instance()
        # max_toot_chars varies by instance; default 500 if not advertised
        self.max_chars = getattr(self.instance_info, "max_toot_chars", None) or 500

        if globals.currentAccount is None:
            globals.currentAccount = self
            main.window.SetLabel(
                self.me.acct + " - " + application.name + " " + application.version
            )

        timeline.add(self, "Home", "home")
        timeline.add(self, "Notifications", "notifications")
        timeline.add(self, "Messages", "messages")
        timeline.add(self, "Likes", "likes")
        timeline.add(self, "Sent", "user", self.me.id, self.me)

        for i in self.prefs.user_timelines:
            tl = misc.user_timeline_user(self, i, False)
            if not tl:
                self.prefs.user_timelines.remove(i)
        for i in self.prefs.list_timelines:
            try:
                lst = self.api.list(i)
                misc.list_timeline(self, lst.title, i, False)
            except MastodonError:
                self.prefs.list_timelines.remove(i)
        for i in self.prefs.search_timelines:
            misc.search(self, i, False)

        if globals.currentAccount == self:
            main.window.list.SetSelection(0)
            main.window.on_list_change(None)

        threading.Thread(target=timeline.timelineThread, args=[self], daemon=True).start()

        if globals.prefs.streaming:
            self.start_stream()

    # ------------------------------------------------------------------ posting

    def tweet(self, text, id=None, spoiler_text=None, visibility="public", poll=None, **kwargs):
        """Post a status (toot). `id` is in_reply_to_id when replying."""
        try:
            post_kwargs = dict(visibility=visibility)
            if id is not None:
                post_kwargs["in_reply_to_id"] = id
            if spoiler_text:
                post_kwargs["spoiler_text"] = spoiler_text
            if poll is not None:
                post_kwargs["poll"] = poll
            return self.api.status_post(text, **post_kwargs)
        except MastodonError as e:
            speak.speak(str(e))
            return False

    def retweet(self, id):
        self.api.status_reblog(id)

    def quote(self, status, text, spoiler_text=None, visibility="public"):
        status_url = status.url
        post_kwargs = dict(visibility=visibility)
        if spoiler_text:
            post_kwargs["spoiler_text"] = spoiler_text
        return self.api.status_post(text + " " + status_url, **post_kwargs)

    def like(self, id):
        self.api.status_favourite(id)

    def unlike(self, id):
        self.api.status_unfavourite(id)

    # ------------------------------------------------------------------ social

    def _resolve_account_id(self, acct):
        """Resolve an @acct string or display name to an account ID."""
        results = self.api.account_search(acct, limit=1)
        if results:
            return results[0].id
        return None

    def follow(self, acct):
        aid = self._resolve_account_id(acct.lstrip("@"))
        if aid:
            self.api.account_follow(aid)

    def unfollow(self, acct):
        aid = self._resolve_account_id(acct.lstrip("@"))
        if aid:
            self.api.account_unfollow(aid)

    def block(self, acct):
        aid = self._resolve_account_id(acct.lstrip("@"))
        if aid:
            self.api.account_block(aid)

    def unblock(self, acct):
        aid = self._resolve_account_id(acct.lstrip("@"))
        if aid:
            self.api.account_unblock(aid)

    def mute(self, acct):
        aid = self._resolve_account_id(acct.lstrip("@"))
        if aid:
            self.api.account_mute(aid)

    def unmute(self, acct):
        aid = self._resolve_account_id(acct.lstrip("@"))
        if aid:
            self.api.account_unmute(aid)

    # ------------------------------------------------------------------ users

    def _paginate(self, func, id, limit=80):
        from mastodon.types_base import AttribAccessDict
        def _promote(item):
            if isinstance(item, dict) and not isinstance(item, AttribAccessDict):
                return AttribAccessDict(**item)
            return item
        results = []
        page = func(id, limit=limit)
        count = 0
        while page and count < globals.prefs.user_limit:
            results.extend(_promote(u) for u in page)
            next_params = getattr(page, "_pagination_next", None)
            if not next_params:
                break
            max_id = next_params.get("max_id")
            if not max_id:
                break
            page = func(id, limit=limit, max_id=max_id)
            count += 1
        return results

    def followers(self, id):
        return self._paginate(self.api.account_followers, id)

    def friends(self, id):
        return self._paginate(self.api.account_following, id)

    def mutual_following(self):
        followers = self.followers(self.me.id)
        friends = self.friends(self.me.id)
        follower_ids = {u.id for u in followers}
        return [u for u in friends if u.id in follower_ids]

    def not_following(self):
        followers = self.followers(self.me.id)
        if not followers:
            return []
        # Check relationships in batches of 40 (API limit)
        following_ids = set()
        for i in range(0, len(followers), 40):
            batch = followers[i:i+40]
            rels = self.api.account_relationships([u.id for u in batch])
            for rel in rels:
                if rel.following:
                    following_ids.add(str(rel.id))
        return [u for u in followers if str(u.id) not in following_ids]

    def not_following_me(self):
        followers = self.followers(self.me.id)
        friends = self.friends(self.me.id)
        follower_ids = {u.id for u in followers}
        return [u for u in friends if u.id not in follower_ids]

    def havent_posted(self):
        friends = self.friends(self.me.id)
        cutoff = datetime.datetime.now().year - 1
        result = []
        for u in friends:
            if u.last_status_at and u.last_status_at.year < cutoff:
                result.append(u)
        return result

    # ------------------------------------------------------------------ profile

    def UpdateProfile(self, display_name, url, note):
        self.api.account_update_credentials(
            display_name=display_name,
            note=note,
        )

    # ------------------------------------------------------------------ streaming

    def start_stream(self):
        listener = streaming.MastodonStreamListener(self)
        self._stream_thread = threading.Thread(
            target=self.api.stream_user,
            kwargs={"listener": listener, "run_async": False},
            daemon=True,
        )
        self._stream_thread.start()

    # ------------------------------------------------------------------ lists

    def list_timelines(self, hidden=False):
        tl = []
        for i in self.timelines:
            if i.hide == hidden:
                tl.append(i)
        return tl
