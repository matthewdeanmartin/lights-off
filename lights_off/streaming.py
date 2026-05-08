from mastodon import StreamListener
from lights_off import speak
from lights_off import utils


class MastodonStreamListener(StreamListener):

    def __init__(self, account):
        super().__init__()
        self.account = account

    def on_update(self, status):
        """New post arrived on the home timeline."""
        utils.add_users(status)
        home_tl = self.account.timelines[0] if self.account.timelines else None
        if home_tl:
            home_tl.load(items=[status])

        # Route to user/list timelines that match
        for tl in self.account.timelines:
            if tl.type == "user":
                if status.account.acct == tl.data or status.account.id == tl.data:
                    tl.load(items=[status])
            elif tl.type == "list" and status.account.id in tl.members:
                tl.load(items=[status])

    def on_notification(self, notification):
        """Notification (mention, boost, favourite, follow, etc.) arrived."""
        stub = utils.notification_to_status(notification)
        if stub is None:
            return
        if getattr(stub, "account", None) is not None:
            try:
                utils.add_users(stub)
            except Exception:
                pass
        notif_tl = next(
            (t for t in self.account.timelines if t.type == "notifications"),
            None,
        )
        if notif_tl:
            notif_tl.load(items=[stub])

    def on_abort(self, err):
        speak.speak("Streaming disconnected for " + self.account.me.acct)

    def on_error(self, err):
        speak.speak("Streaming error for " + self.account.me.acct + ": " + str(err))
