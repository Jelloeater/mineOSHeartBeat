#!/usr/bin/env python2.7
"""A python project for managing Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""
import getpass
import json
import os
import smtplib
import logging
import sys
import argparse
import base64
from time import sleep
from conf_reader import config_file

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.9"
__email__ = "jelloeater@gmail.com"

sys.path.append("/usr/games/minecraft")  # So we can run the script from other locations
from mineos import mc

BOOT_WAIT = 120
LOG_FILENAME = "heartbeat.log"
USE_GMAIL = True

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
    else:
        logging.basicConfig(filename=LOG_FILENAME,
                            format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.WARNING)

    logging.debug(sys.path)
    logging.debug(args)

    mode = modes(args.base_directory, args.delay)

    if args.list:
        mode.list_servers()
    if args.configure_email_alerts:
        gmail.configure()

    # Magic starts here
    if args.interactive:
        mode.interactive()
    elif args.single:
        mode.single_server()
    elif args.multi:
        mode.multi_server()

class modes(object):
    def __init__(self, base_directory, sleep_delay=10):
        self.base_directory = base_directory
        self.sleep_delay = sleep_delay

    def sleep(self):
        try:
            sleep(self.sleep_delay)
        except KeyboardInterrupt:
            print("Bye Bye.")
            sys.exit(0)

    def list_servers(self):
        print("Servers:")
        print("{0}{1}".format("Name".ljust(20), 'State'))
        for i in mc.list_servers(self.base_directory):
            print "{0}{1}".format(i.ljust(20), ['down','up'][mc(i).up])
        
    def interactive(self):
        servers_to_monitor = []
        print("Interactive Mode")

        while True:
            self.list_servers()
            print("\n\nCurrently Monitoring: {0}\n".format(', '.join(servers_to_monitor)))
            print("Type name of server to monitor")
            server_name = raw_input(">")

            if server_name:
                servers_to_monitor.append(server_name)

            if server_name.lower() in ['done', 'd', ''] and servers_to_monitor:
                break  # Only exits if we have work to do

        logging.info("Starting monitor")

        while True:
            for i in servers_to_monitor:
                server_logger(i).check_server()
            self.sleep()

    def multi_server(self):
        print("Multi Server mode")
        print("Press Ctrl-C to quit")

        while True:
            server_list = mc.list_servers(args.base_directory)
            logging.debug(server_list)

            for i in server_list:
                server_logger(i).check_server()
            self.sleep()

    def single_server(self, server_name):
        print("Single Server Mode: " + server_name)
        print("Press Ctrl-C to quit")

        while True:
            server_logger(server_name).check_server()
            try:
                pass
            except RuntimeWarning:
                print("Please enter a valid server name")
                break
            self.sleep()

class gmail(object):
    """
    Lets users send email messages

    # TODO Maybe implement other mail providers
    """
    SETTINGS_FILE_PATH = "alerts-settings.dat"
    SEND_ALERT_TO = []  # Must be a list
    
    def __init__(self):
        self.settings = config_file(self.SETTINGS_FILE_PATH)

    def send(cls, subject, text):
        logging.debug("Sending email")

        message = "\From: {0}\nTo: {1}\nSubject: {2}\n\n{3}".format(self.settings['EMAIL_USERNAME'],
                                                                    ", ".join(self.settings['EMAIL_SEND_ALERT_TO']),
                                                                    subject,
                                                                    text)

        server = smtplib.SMTP("smtp.gmail.com", 587)  # or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(self.settings['EMAIL_USERNAME'], self.settings['EMAIL_PASSWORD'])
        server.sendmail(self.settings['EMAIL_USERNAME'], self.settings['EMAIL_SEND_ALERT_TO'], message)
        server.close()

    def configure(self):
        print("Enter user email (user@domain.com) or press enter to skip")

        username = raw_input('({0})>'.format(self.settings['EMAIL_USERNAME']))
        
        print("Enter email password or press enter to skip")
        password = getpass.getpass(prompt='>')  # To stop shoulder surfing
        if username and password:
            self.settings['EMAIL_USERNAME'] = username
            self.settings['EMAIL_PASSWORD'] = password
            self.settings.commit()

        print("Clear alerts list? (yes/no)?")
        import distutils.util
        if distutils.util.strtobool(raw_input(">")):
            self.SEND_ALERT_TO = []  # Clear the list
            print("Alerts list cleared")

        print("Send alerts to (press enter when done):")
        while True:
            user_input = raw_input('({0})>'.format(','.join(self.SEND_ALERT_TO)))
            if not user_input:
                break
            else:
                self.SEND_ALERT_TO.append(user_input)

class server_logger(mc):
    """
    A re-implemented instance of the mc class

    not providing __init__ means we can use the superclass' __init__ by default.
    this class can use all functions within server_logger and mc as if they were
    coded together in the first place
    """
    
    def check_server(self):
        logging.info("Checking server {0}".format(self.server_name))
        logging.debug("Server {0} is {1}".format(self.server_name,
                                                 ['Down', 'Up'][self.up]))

        if not self.up:
            self.start_server()
            sleep(BOOT_WAIT)

    def start_server(self):
        logging.info("Starting Server: " + self.server_name)
        self.start()
        logging.info("Server Started")
        '''if USE_GMAIL:
            try:
                logging.debug("Debug logging should be off, so we write issues to the file, NOT the console")
                with open(LOG_FILENAME) as f:
                    log = f.read()
                    gmail.send(subject="Server " + self.server_name + " is down", text=log)  # Sends alert
            except IOError:
                logging.error("Can't find the log file to send, aborting sending mail")
        '''

if __name__ == "__main__":
    main()

