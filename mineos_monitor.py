#!/usr/bin/env python2.7
"""A python project for managing Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""

import sys
from keyring.errors import PasswordDeleteError

sys.path.append("/usr/games/minecraft")  # So we can run the script from other locations

import json
import os
import keyring
import getpass
import smtplib
import logging
import argparse
from time import sleep
from mineos import mc

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.9"
__email__ = "jelloeater@gmail.com"


BOOT_WAIT = 120
LOG_FILENAME = "heartbeat.log"


def main():
    """ Take arguments and direct program """
    parser = argparse.ArgumentParser(description="A MineOS Server Monitor"
                                                 " (http://github.com/jelloeater/MineOSheartbeat)",
                                     version=__version__,
                                     epilog="Please specify mode (-s, -i or -m) to start monitoring")
    server_group = parser.add_argument_group('Single Server Mode')
    server_group.add_argument("-s",
                              "--single",
                              action="store",
                              help="Single server watch mode")
    interactive_group = parser.add_argument_group('Interactive Mode')
    interactive_group.add_argument("-i",
                                   "--interactive",
                                   help="Interactive menu mode",
                                   action="store_true")
    multi_server_group = parser.add_argument_group('Multi Server Mode')
    multi_server_group.add_argument("-m",
                                    "--multi",
                                    help="Multi server watch mode",
                                    action="store_true")

    email_group = parser.add_argument_group('E-mail Alert Mode')
    email_group.add_argument("-e",
                             "--email_mode",
                             help="Enables email notification",
                             action="store_true")
    email_group.add_argument("-c",
                             "--configure_email_alerts",
                             help="Configure email alerts",
                             action="store_true")
    email_group.add_argument("-r",
                             "--remove_password_store",
                             help="Removes password stored in system keyring",
                             action="store_true")

    parser.add_argument("-d",
                        "--delay",
                        action="store",
                        type=int,
                        default=60,
                        help="Wait x second between checks (ex. 60)")
    parser.add_argument('-b',
                        dest='base_directory',
                        default='/var/games/minecraft',
                        help='Change MineOS Server Base Location (ex. /var/games/minecraft)')
    parser.add_argument("-l",
                        "--list",
                        action="store_true",
                        help="List MineOS Servers")
    parser.add_argument("--debug",
                        action="store_true",
                        help="Debug Mode Logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.DEBUG)
        logging.debug(sys.path)
        logging.debug(args)
        print("")
    else:
        logging.basicConfig(filename=LOG_FILENAME,
                            format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.WARNING)

    mode = modes(args.base_directory, args.delay)  # Create new mode object for flow, I'll buy that :)

    if args.list:
        mode.list_servers()

    if args.remove_password_store:
        gmail().clear_password_store()
    if args.configure_email_alerts:
        gmail().configure()
    if args.email_mode:
        server_logger.USE_GMAIL = True
        print("E-mail notifications enabled")

    if args.email_mode and args.debug:
        logging.critical("Debug mode and e-mail notifications are mutually exclusive")
        sys.exit(1)

    # Magic starts here
    if args.interactive:
        mode.interactive()
    elif args.single:
        mode.single_server(args.single)  # Needs server name to start
    elif args.multi:
        mode.multi_server()


class modes(object):  # Uses new style classes
    def __init__(self, base_directory, owner="mc", sleep_delay=60):
        self.base_directory_m = base_directory
        self.sleep_delay = sleep_delay
        self.owner = owner

    def sleep(self):
        try:
            sleep(self.sleep_delay)
        except KeyboardInterrupt:
            print("Bye Bye.")
            sys.exit(0)

    def list_servers(self):
        print("Servers:")
        print("{0}{1}".format("Name".ljust(20), 'State'))
        for i in mc.list_servers(self.base_directory_m):
            print "{0}{1}".format(i.ljust(20), ['down','up'][mc(i).up])
        
    def interactive(self):
        servers_to_monitor = []
        print("Interactive Mode")

        while True:
            self.list_servers()
            print("\n\nCurrently Monitoring: {0}\n".format(', '.join(servers_to_monitor)))
            print("Type name of server to monitor. Enter (d/done) when finished.")
            server_name = raw_input(">")

            if server_name.lower() in ['done', 'd', ''] and servers_to_monitor:
                break  # Only exits if we have work to do
            elif server_name in mc.list_servers(self.base_directory_m):  # Checks if name is valid
                servers_to_monitor.append(server_name)

        logging.info("Starting monitor")

        while True:
            for i in servers_to_monitor:
                server_logger(server_name=i, owner=self.owner, base_directory=self.base_directory_m).check_server()
            self.sleep()

    def multi_server(self):
        print("Multi Server mode")
        print("Press Ctrl-C to quit")

        while True:
            server_list = mc.list_servers(self.base_directory_m)
            logging.debug(server_list)

            for i in server_list:
                server_logger(server_name=i, owner=self.owner, base_directory=self.base_directory_m).check_server()
            self.sleep()

    def single_server(self, server_name):
        print("Single Server Mode: " + server_name)
        print("Press Ctrl-C to quit")

        while True:
            server_logger(server_name=server_name, owner=self.owner, base_directory=self.base_directory_m).check_server()
            try:
                pass
            except RuntimeWarning:
                print("Please enter a valid server name")
                break
            self.sleep()


class gmailSettings():
    """ Container class for load/save """
    USERNAME = ""
    # Password should be stored with keyring
    SEND_ALERT_TO = []  # Must be a list


class SettingsHelper(gmailSettings):
    SETTINGS_FILE_PATH = "settings.json"
    KEYRING_APP_ID = 'mineOSHeartBeat'

    @classmethod
    def loadSettings(cls):
        if os.path.isfile(cls.SETTINGS_FILE_PATH):
            try:
                with open(cls.SETTINGS_FILE_PATH) as fh:
                    gmailSettings.__dict__ = json.loads(fh.read())
            except ValueError:
                logging.error("Settings file has been corrupted, reverting to defaults")
                os.remove(cls.SETTINGS_FILE_PATH)
        logging.debug("Settings Loaded")

    @classmethod
    def saveSettings(cls):
        with open(cls.SETTINGS_FILE_PATH, "w") as fh:
            fh.write(json.dumps(gmailSettings.__dict__, sort_keys=True, indent=0))
        logging.debug("Settings Saved")


class gmail(object, SettingsHelper):
    """ Lets users send email messages """
    # TODO Maybe implement other mail providers
    def __init__(self):
        self.loadSettings()
        self.PASSWORD = keyring.get_password(self.KEYRING_APP_ID,self.USERNAME)  # Loads password from secure storage

    def send(self, subject, text):
        logging.debug("Sending email")

        message = "\From: {0}\nTo: {1}\nSubject: {2}\n\n{3}".format(self.USERNAME,
                                                                    ", ".join(self.SEND_ALERT_TO),
                                                                    subject,
                                                                    text)

        server = smtplib.SMTP("smtp.gmail.com", 587)  # or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(self.USERNAME, self.PASSWORD)
        server.sendmail(self.USERNAME, self.SEND_ALERT_TO, message)
        server.close()
        print("Message Sent")

    def configure(self):
        print("Enter user email (user@domain.com) or press enter to skip")

        username = raw_input('({0})>'.format(self.USERNAME))
        
        print("Enter email password or press enter to skip")
        password = getpass.getpass(
            prompt='>')  # To stop shoulder surfing
        if username:
            gmailSettings.USERNAME = username
        if password:
            keyring.set_password(self.KEYRING_APP_ID, self.USERNAME, password)

        print("Clear alerts list? (yes/no)?")
        import distutils.util
        try:
            if distutils.util.strtobool(raw_input(">")):
                gmailSettings.SEND_ALERT_TO = []  # Clear the list
                print("Alerts list cleared")
        except ValueError:
            pass

        print("Send alerts to (press enter when done):")
        while True:
            user_input = raw_input('({0})>'.format(','.join(self.SEND_ALERT_TO)))
            if not user_input:
                break
            else:
                gmailSettings.SEND_ALERT_TO.append(user_input)
        self.saveSettings()

    def clear_password_store(self):
        try:
            keyring.delete_password(self.KEYRING_APP_ID, self.USERNAME)
            print("Password removed from Keyring")
        except PasswordDeleteError:
            logging.error("Password cannot be deleted or already has been removed")


class server_logger(mc):
    USE_GMAIL = False  # Static variable for e-mail mode

    def check_server(self):
        logging.info("Checking server {0}".format(self.server_name))
        logging.debug("Server {0} is {1}".format(self.server_name,
                                                 ['Down', 'Up'][self.up]))

        if not self.up:
            self.start_server()
            sleep(BOOT_WAIT)

    def start_server(self):
        logging.warning(str(self.server_name) + 'has gone DOWN, restarting.')
        logging.info("Starting Server: " + self.server_name)

        # FIXME Server start error RuntimeWarning
        print(self._base_directory)
        mc(self.server_name, self._base_directory).start()
        logging.info("Server Started")
        if server_logger.USE_GMAIL:
            try:
                with open(LOG_FILENAME) as f:
                    log = f.read()
                    gmail().send(subject="Server " + self.server_name + " is down", text=log)  # Sends alert
            except IOError:
                logging.error("Can't find the log file to send, aborting sending mail")


if __name__ == "__main__":
    main()

