#!/usr/bin/python3
import sys
import time
import shelve
import getpass
import imaplib
import traceback

fallback = False
try:
    from gi.repository import Notify
    Notify.init(app_name="ThunderPopper")
except ModuleNotFoundError:
    import os
    fallback = True

popper_data = shelve.open("thunderpopper", writeback=True)


class Notifier:
    def __init__(self, fallback):
        self.fallback = fallback
        self.notification = None
        try:
            self.notification = Notify.Notification.new("ThunderPopper", "Welcome", None)
        except ModuleNotFoundError:
            import os
            self.fallback = True

    def send_notification(self, message):
        if self.fallback:
            os.system(f"notify-send \"{message}\"")
        else:
            self.notification.update("ThunderPopper", message, None)
            self.notification.show()

notifier_obj = Notifier(fallback)


class Account:
    def __init__(self, database):
        self.popper_data = database
        self.username = self.password = None

    def list_accounts(self):
        if self.popper_data.get("accounts", None):
            print("Please choose an account: ")
            print("\tID\tUsername")
            for acid in self.popper_data["accounts"]:
                print(f"\t{acid}\t{self.popper_data['accounts'][acid]['uname']}")

            return int(input("Choose an account: ") or -1)
        else:
            ask_create = input("You do not have any account. Do you want to add one?(y/n): ")
            if ask_create == "y":
                return self.create_account()
            elif ask_create == "n":
                print("Bye!")
                exit()
            else:
                print("Not a valid input. Bye! :)")
                exit()

    def login(self):
        # If not logged out ie. have last_login
        last_login = self.popper_data.get("last_login", None)
        if last_login:
            for acid in self.popper_data["accounts"]:
                if acid == last_login:
                    self.server_port = self.popper_data["accounts"][acid]["server_port"]
                    self.username = self.popper_data["accounts"][acid]['uname']
                    self.password = self.popper_data["accounts"][acid]['password']
                    return self.server_port, self.username, self.password
            else:
                return False

        else:
            acid = self.list_accounts()
            if acid in self.popper_data["accounts"]:    
                self.server_port = self.popper_data["accounts"][acid]["server_port"]
                self.username = self.popper_data["accounts"][acid]['uname']
                self.password = self.popper_data["accounts"][acid]['password']
                return self.server_port, self.username, self.password
            else:
                print("Invalid Account ID.")
                return False

    def create_account(self):
        new_id = self.popper_data.get("accounts", None)
        if new_id:
            new_id = list(new_id.keys())[-1] + 1
        else:
            new_id = 0
        server, port = [i.strip() for i in input("Enter comma-separated server and port:  ").split(",")]
        uname = input("Enter User name: ")
        password = getpass.getpass("Enter you password: ")
        if not self.popper_data.get("accounts", None):
            self.popper_data["accounts"] = {}
        self.popper_data.sync()
        self.popper_data["accounts"][new_id] = {
            "server_port": (server, int(port)),
            "uname": uname,
            "password": password
            }
        self.popper_data.sync()

    def edit_account(self):
        acid = self.list_accounts()
        if acid in self.popper_data['accounts'].keys():
            what = input('Enter\n\t1. To edit server and port.\n\t' +
                         '2. To edit username.\n\t' +
                         '3. To edit password. : ')
            if what == "1":
                new_value = input("Enter comma-separated new server and port: ")
                new_value = [i.strip() for i in new_value.split(", ")]
                new_value = new_value[0], int(new_value[1])
                what = "server_port"
            elif what == "2":
                new_value = input("Enter new username: ")
                what = "uname"
            elif what == "3":
                what = "password"
                new_value = getpass.getpass("Enter new password: ")
            else:
                print("Invalid choice.")
                exit()
            self.popper_data["accounts"][acid][what] = new_value
            self.popper_data.sync()
        else:
            print("ID does not exist.", acid)

    def delete_account(self):
        acid = self.list_accounts()
        del self.popper_data["accounts"][acid]

    def print_accounts(self):
        print(self.popper_data.items())


class Mailer:
    def __init__(self, host, port):
        try:
            self.mailClient = imaplib.IMAP4_SSL(host, port)
        except Exception as e:
            notifier_obj.send_notification(f"Error {e} occured!")
            exit()

    def login(self, uname, pwd):
        self.mailClient.login(uname, pwd)
        self.mailClient.select()

    def check(self):
        return self.mailClient.search(None, "UnSeen")


if __name__ == "__main__":
    if not len(sys.argv) > 1:
        last_user = popper_data.get("last_login", None)
        last_user_str = ""
        if last_user:
            last_user_str = " as " + popper_data.get("accounts").get(last_user)
        action = input("Choose an option to proceed with:\n" +
                       f"\t1. Login {last_user_str}\n" +
                       "\t2. Logout\n" +
                       "\t3. Create an account\n" +
                       "\t4. Edit an account\n" +
                       "\t5. Delete an account: ")

    try:
        account_object = Account(popper_data)
        login_creds = False
        if action == '1':
            login_creds = account_object.login()
        elif action == '2':
            account_object.popper_data['last_login'] = None
            print("Logged Out!")
        elif action == '3':
            account_object.create_account()
        elif action == '4':
            account_object.edit_account()
        elif action == '5':
            account_object.delete_account()

    except Exception as e:
        print("An error occured.")
        print("-----------------")
        print(traceback.print_exc())
        print("-----------------")
    finally:
        popper_data.close()

    if login_creds:
        server, port = login_creds[0]
        uname, password = login_creds[1:]
        mailer_object = Mailer(server, port)
        mailer_object.login(uname, password)

        status, n_new = mailer_object.check()
        try:
            while status == "OK":
                status, n_new = mailer_object.check()
                n_new = int(n_new[0]) if n_new[0] else None
                if n_new and n_new > 0:
                    notifier_obj.send_notification(f"You have {n_new} unread email(s)!")
                time.sleep(300)
        except KeyboardInterrupt:
            # Let's exit gracefully
            sys.exit()
