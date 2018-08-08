#!/usr/bin/env python3
import subprocess
import sys
import shelve
notifier = shelve.open("notifier")

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

    def __init__(self, notification_key, message):
        """__init__ Takes an argument which lets us to decide what message to show.

        Arguments:
             notification_key {int} --- unique identifier for notification
             message {boolean} -- Text to be popped-up
        """
        self.notification_key = notification_key
        self.message = message
        self.fallback = fallback
        self.notification = None
        self.tbird_notification_count = 0
        self.max_notification = 3
        if not fallback:
            self.notification = Notify.Notification.new(
                "ThunderPopper", "Welcome", None)
            self.notification.add_action('1', 'Open ThunderBird', self.notification_callback, None)
            self.notification.add_action('2', 'Dismiss', self.notification_callback, None)
            self.notification.connect("closed", self.closed)

        self.send_notification()

    def send_notification(self):
        """send_notification

        Send pop-up notification to users.
        """
        print(self.max_notification, self.tbird_notification_count)
        should_notify = False
        # Check if thunderbird is open
        thunderbird = len(subprocess.check_output(
            "ps aux | grep /usr/lib/thunderbird", shell=True).decode().split("\n")) > 3

        if thunderbird:
            if self.tbird_notification_count == 0:
                self.tbird_notification_count = 1
        else:
            self.tbird_notification_count = 0

        self.max_notification -= 1
        if self.fallback:
            subprocess.call(["notify-send", self.message])

        else:
            self.notification.update("ThunderPopper", self.message, None)
            self.notification.show()
            if self.max_notification < 0 or (thunderbird and self.tbird_notification_count == 1):
                loop.quit()
            GLib.timeout_add_seconds(10, self.send_notification)

    def notification_callback(self, callback, action, data):
        if action == "1":
            print("Opened ThunderBird")
            subprocess.Popen(["thunderbird"])
        elif action == "2":
            print("Dismissed")
        if action:
            notifier[self.notification_key] = action
        self.closed()

    def closed(self, *args):
        if len(args):
            notifier[self.notification_key] = '3'
            print('Clicked')
        notifier.sync()
        notifier.close()
        loop.quit()


if __name__ == "__main__":
    msg = ''
    if len(sys.argv) == 2:
        key = ""
        msg = sys.argv[1]
    elif len(sys.argv) == 3:
        key = sys.argv[1]
        msg = sys.argv[2]
    else:
        key = ""
        msg = "You have a new message!"

    if not (notifier.get(key, None) and key != ''):
        app = Notifier(key, msg)
        if not fallback:
            loop.run()
