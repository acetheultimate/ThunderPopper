#!/usr/bin/env python3
import sys
import time
import shelve
import getpass
import imaplib
import traceback
import subprocess
import threading
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(threadName)-15s:  %(message)s",
)

notifier = None

popper_data = shelve.open("thunderpopper", writeback=True)


class Account:
    """ Handles all account related functionality.

    Contains functions related to accounts like list, add, remove, edit.
    """

    def __init__(self, database):
        self.popper_data = database

    def list_accounts(self):
        """list_accounts
        Lists users from db

        Returns:
            int -- User ID of selected user from the list.
        """

        if self.popper_data.get("accounts", None):
            print("Please choose an account: ")
            print("\tID\tUsername")
            for acid in self.popper_data["accounts"]:
                print(
                    f"\t{acid}\t{self.popper_data['accounts'][acid]['uname']}")

            return int(input("Choose an account: ") or -1)
        else:
            ask_create = input(
                "You do not have any account. Do you want to add one?(y/n): ")
            if ask_create == "y":
                return self.create_account()
            elif ask_create == "n":
                print("Bye!")
                exit()
            else:
                print("Not a valid input. Bye! :)")
                exit()

    def login(self, acid=None):
        """login

        Give back login credentials needed to log in for given Account ID. If
        account ID is not given it lists accounts and ask user to choose one.

        Arguments:
            acid {int} -- Account ID

        Returns:
            tuple{int} -- returns login credentials needed for login
        """

        if acid:
            for login in self.popper_data["accounts"]:
                if acid == login:
                    server_port = self.popper_data["accounts"][acid]["server_port"]
                    username = self.popper_data["accounts"][acid]['uname']
                    password = self.popper_data["accounts"][acid]['password']
                    logging.debug("Got creds, returning to pass to the server.")
                    return server_port, username, password
            else:
                logging.debug("Error while handling acid %s" % acid)
                return False
        else:
            acid = self.list_accounts()
            payload = self.popper_data["accounts"][acid]
            server_port = payload["server_port"]
            username = payload['uname']
            password = payload['password']
            if self.popper_data.get('last_logins', None):
                if acid not in self.popper_data['last_logins']:
                    self.popper_data["last_logins"].append(acid)
            else:
                self.popper_data["last_logins"] = [acid]
            self.popper_data.sync()
            return server_port, username, password

    def create_account(self):
        """create_account

        Creates an account and store creds in db
        """

        new_id = self.popper_data.get("accounts", None)
        if new_id:
            c = 2
            while c in list(new_id.keys()):
                c += 1
            new_id = c
        else:
            self.popper_data["accounts"] = {}
            new_id = 1

        try:
            server, port = [i.strip() for i in input("Enter comma-separated server and port:  ").split(",")]
        except ValueError as e:
            print("Error: ", e)
            sys.exit()
        uname = input("Enter User name: ").strip()
        password = getpass.getpass("Enter you password: ").strip()
        if not (uname and password):
            print("You username and password should not be empty.")
            sys.exit()

        self.popper_data.sync()
        self.popper_data["accounts"][new_id] = {
            "server_port": (server, int(port)),
            "uname": uname,
            "password": password
        }
        self.popper_data.sync()
        return new_id

    def edit_account(self, acid=None):
        """edit_account

        Used for changing creds of given Account ID. If Account id is not given,
        lists all Accounts and asks user to pick one.

        Arguments:
            acid {int} -- Account ID of the user.
        """
        new_value = None
        if not acid:
            acid = self.list_accounts()

        if acid in self.popper_data['accounts'].keys():
            what = input('Enter\n\t1. To edit server and port.\n\t' +
                         '2. To edit username.\n\t' +
                         '3. To edit password. : ')
            if what == "1":
                new_value = input(
                    "Enter comma-separated new server and port: ")
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

    def delete_account(self, acid=None):
        """delete_account

        Given the Account ID, Deletes an account from db. If Account ID is not
        given, It lists all the accounts to pick from.

        Arguments:
            acid {int} -- Account ID of the User.
        """
        if not acid:
            acid = self.list_accounts()

        del self.popper_data["accounts"][acid]
        if acid in self.popper_data.get("last_logins", []):
            self.popper_data["last_logins"].remove(acid)

    def print_db(self):
        """print_db For testing purpose

        To get what's there in db.
        """

        print(self.popper_data.items())


class Mailer:
    """Handles queries related to e-mail."""

    def __init__(self, host, port):
        try:
            self.mailClient = imaplib.IMAP4_SSL(host, port)
            logging.debug("Connection to the server made!")
        except Exception as e:
            logging.error('Error %s occured!' % e)
            exit()

    def login(self, uname, pwd):
        """login Login the User.

        Log in the user to the email account with given username and password.

        Arguments:
            uname {str} -- Username
            pwd {str} -- Password
        """
        logging.debug("Logging in...")
        self.mailClient.login(uname, pwd)
        logging.debug("Logged in successfully!")
        self.mailClient.select(readonly=True)
        logging.debug("Inbox Selected!")

    def check(self):
        """check Check for incoming mails

        Check if there's any unread email in Inbox.

        Returns:
            tuple -- Returns a tuple containing status and number of unread
                     emails, if any.
        """
        logging.debug("Searching for unseens...")
        res, messages = self.mailClient.search(None, '(UNSEEN)')
        if res == "OK":
            n = 0
            for num in messages[0].split():
                n += 1
                typ, data = self.mailClient.fetch(num, '(RFC822)')
                for response_part in data:
                    if isinstance(response_part, tuple):
                        typ, data = self.mailClient.store(num, '+FLAGS', '\\Seen')
            return res, [n]
        return None


def main(login_creds):
    server, port = login_creds[0]
    uname, password = login_creds[1:]
    mailer_object = Mailer(server, port)
    mailer_object.login(uname, password)
    pre_n_new = 0
    pre_time = time.clock()
    status, n_new = mailer_object.check()
    try:
        while status == "OK":
            status, n_new = mailer_object.check()
            n_new = int(n_new[0]) if n_new[0] else None
            if ((n_new and n_new > 0) and ((time.clock() - pre_time) > 5 or
                                           (pre_n_new != n_new))):
                subprocess.call(["./Notifier.py", f'You have {n_new} unread email(s)!'])
                pre_time = time.clock()

            time.sleep(1)
    except KeyboardInterrupt:
        # Let's exit gracefully
        sys.exit()


if __name__ == "__main__":
    try:
        account_object = Account(popper_data)
        action = None
        login_creds_list = False
        last_user_list = None

        if len(sys.argv) == 1:
            last_user_list = popper_data.get("last_logins", None)
            if last_user_list and len(last_user_list):
                login_creds_list = []
                logging.debug(
                    "Logging in with " + ", ".join(str(popper_data["accounts"][i]['uname']) for i in last_user_list))
                for acid in last_user_list:
                    login_creds_list.append(account_object.login(acid))

        elif len(sys.argv) == 2:
            if sys.argv[1] == "-i":
                # Interactive mode
                action = input("Choose an option to proceed with:\n" +
                               "\t1. Login\n" +
                               "\t2. Logout\n" +
                               "\t3. Create an account\n" +
                               "\t4. Edit an account\n" +
                               "\t5. Delete an account: ")
                if action == '1':
                    login_creds_list = [account_object.login()]
                elif action == '2':
                    account_object.popper_data['last_logins'] = None
                    print("Logged Out!")
                elif action == '3':
                    account_object.create_account()
                elif action == '4':
                    account_object.edit_account()
                elif action == '5':
                    account_object.delete_account()

            elif sys.argv[1] == "-x":
                # Logout from All
                account_object.popper_data['last_logins'] = None
                print("Logged out from all accounts!")
                sys.exit()
        else:
            logging.warn("Weird >" + "<>".join(sys.argv) + "<")
            sys.exit()

        if login_creds_list:
            for login_creds in login_creds_list:
                t = threading.Thread(target=main, name=login_creds[1], args=(login_creds,))
                t.start()

    except Exception as e:
        print("An error occured.")
        print("-----------------")
        print(traceback.print_exc())
        print("-----------------")
    finally:
        popper_data.close()
