#!/usr/bin/env python3
import subprocess
import sys

fallback = False
loop = None

try:
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify, GLib
    loop = GLib.MainLoop()
    Notify.init(app_name="ThunderPopper")
except ModuleNotFoundError:
    fallback = True


class Notifier:
    """A notifier to give pop ups when new information is available."""

    def __init__(self, message):
        """__init__ Takes an argument which lets us to decide what message to show.

        Arguments:
             message {boolean} -- Text to be popped-up
        """
        self.message = message
        self.fallback = fallback
        self.notification = None
        self.tbird_notification_count = 0
        self.max_notification = 5
        if not fallback:
            self.notification = Notify.Notification.new(
                "ThunderPopper", "Welcome", None)
            self.notification.add_action('1', 'Open ThunderBird', self.notification_callback, None)
            self.notification.add_action('2', 'Dismiss', self.notification_callback, {"Hello": "world"})
            self.notification.connect("closed", self.closed)

        self.send_notification()

    def send_notification(self):
        """send_notificatioin

        Send pop-up notification to users.
        """

        should_notify = False
        # Check if thunderbird is open
        thunderbird = subprocess.check_output(
            "ps aux | grep /usr/lib/thunderbird", shell=True).decode()
        if len(thunderbird.split("\n")) > 3:
            if self.tbird_notification_count == 0:
                self.tbird_notification_count = 1
                should_notify = True
        else:
            should_notify = True
            self.tbird_notification_count = 0

        if should_notify:
            self.max_notification -= 1
            if self.fallback:
                subprocess.call("notify-send", self.message)

            else:
                self.notification.update("ThunderPopper", self.message, None)
                self.notification.show()

        if not fallback:
            if self.max_notification < 0:
                loop.quit()
            GLib.timeout_add_seconds(10, self.send_notification)

    def notification_callback(self, callback, action, data):
        if action == "1":
            print("Open ThunderBird")
            subprocess.Popen(["thunderbird"])
        elif action == "2":
            print("Dismiss")
        self.closed()

    @staticmethod
    def closed():
        loop.quit()


if __name__ == "__main__":
    msg = ''
    if len(sys.argv) > 1:
        msg = sys.argv[1]
    else:
        msg = "You have a new message!"
    app = Notifier(msg)
    loop.run()
