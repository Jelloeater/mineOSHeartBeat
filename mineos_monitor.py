#!/usr/bin/env python2.7
"""A python project for managing Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""
import getpass
import json
import os
import smtplib
import logging
from time import sleep
import sys
import argparse
import base64

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.9"
__email__ = "jelloeater@gmail.com"


sys.path.append("/usr/games/minecraft")  # So we can run the script from other locations
from mineos import mc


class GlobalVars():
	""" Exists to solve outer scope access issues, and maybe save/load down the road"""
	BOOT_WAIT = 120
	DELAY = 60
	EMAIL_SETTINGS_FILE_PATH = "alerts-settings.dat"
	BASE_DIRECTORY = "/var/games/minecraft"
	LOG_FILENAME = "heartbeat.log"
	MINEOS_USERNAME = "mc"


def main():
	""" Take arguments and direct program """
	parser = argparse.ArgumentParser(description="A MineOS Server Monitor"
	                                             " (http://github.com/jelloeater/MineOSheartbeat)",
	                                 version=__version__,
	                                 epilog="Please specify mode (-s, -i or -m) to start monitoring")

	server_group = parser.add_argument_group('Single Server Mode')
	server_group.add_argument("-s", "--single", action="store", help="Single server watch mode")

	interactive_group = parser.add_argument_group('Interactive Mode')
	interactive_group.add_argument("-i", "--interactive", help="Interactive menu mode", action="store_true")

	multi_server_group = parser.add_argument_group('Multi Server Mode')
	multi_server_group.add_argument("-m", "--multi", help="Multi server watch mode", action="store_true")

	email_group = parser.add_argument_group('E-mail Alert Mode')
	email_group.add_argument("-e", "--emailMode", help="Enables email notification", action="store_true")
	email_group.add_argument("-c", "--configureEmailAlerts", help="Configure email alerts", action="store_true")

	parser.add_argument("-d", "--delay", action="store", type=int,
	                    help="Wait x second between checks (ex. 60)")

	parser.add_argument('-b', dest='base_directory', help='Change MineOS Server Base Location (ex. /var/games/minecraft)')
	parser.add_argument("-l", "--list", action="store_true", help="List MineOS Servers")
	parser.add_argument("--debug", action="store_true", help="Debug Mode Logging")
	args = parser.parse_args()

	if args.base_directory is not None:  # Because we now are relying on globalVars for defaults vs argparse
		GlobalVars.BASE_DIRECTORY = args.base_directory

	if args.debug:
		logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
		                    level=logging.DEBUG)
	else:
		logging.basicConfig(filename=GlobalVars.LOG_FILENAME,
		                    format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
		                    level=logging.WARNING)

	logging.debug(sys.path)
	logging.debug(args)

	if len(sys.argv) == 1:  # Displays help and lists servers
		parser.print_help()
		sys.exit(1)

	if args.list:
		print("Servers @ " + GlobalVars.BASE_DIRECTORY)
		for i in mc.list_servers(GlobalVars.BASE_DIRECTORY):
			print(i)

	if args.configureEmailAlerts:
		gmail.email_configure()

	if args.emailMode:
		gmail.loadSettings()
		logging.debug(emailSettings.__dict__)
		try:
			if all([emailSettings.EMAIL_USERNAME is not None,
			        emailSettings.EMAIL_PASSWORD is not None,
			        emailSettings.EMAIL_SEND_ALERT_TO is not None]):
				gmail.ENABLE = args.emailMode
			else:
				print("Please configure email alerts first (run with just -c)")
				sys.exit(0)
		except AttributeError:
			print("Email config corrupted, please delete it and try again")
			sys.exit(1)

	if args.delay is not None:
		GlobalVars.DELAY = args.delay

	logging.debug(args)

	# Magic starts here
	if all([args.interactive, args.single is None, not args.multi]):
		interactive_mode.start()

	if all([args.single, not args.interactive, not args.multi]):
		single_server_mode.start(args.single)

	if all([args.multi, not args.interactive, args.single is None]):
		multi_server_mode.start()


class GlobalServer(GlobalVars):
	@classmethod
	def get_server_status_list(cls):
		mcServers = mc.list_servers(GlobalVars.BASE_DIRECTORY)
		status = []
		for i in mcServers:
			x = server(i)
			if x.is_server_up():
				status.append("UP")
			else:
				status.append("DOWN")
		return list(zip(mcServers, status))

	@classmethod
	def server_sleep(cls):
		try:
			sleep(cls.DELAY)
		except KeyboardInterrupt:
			print("Bye Bye.")
			sys.exit(0)


class interactive_mode(GlobalServer):
	MONITOR_LIST = []

	@classmethod
	def start(cls):
		print("Interactive Mode")

		# FIXME loop logic is messy
		mcServers = cls.get_server_status_list()

		checkServer = []
		for i in mcServers:  # Generate matching t/f list
			checkServer.append(False)

		serverList = list(zip(mcServers, checkServer))

		while True:
			print("")
			print("Servers:")
			print("# \t Name \t\t UP/DOWN \t Check")
			for i in serverList:
				print(str(serverList.index(i)) + "\t" + str(i[0][0]) + "\t" + str(i[0][1]) + "\t" + str(i[1]))

			print("Select servers to Monitor(#) / (Done)")
			user_input = raw_input(">")

			if user_input.isdigit():
				checkServer[int(user_input)] = True
				serverList = list(zip(mcServers, checkServer))
			# Rewrites list when values are changed (I don't feel like packing and unpacking tuples)
			cls.MONITOR_LIST = [x[0][0] for x in serverList if x[1] is True]

			if user_input == "Done" or user_input == "d" and len(cls.MONITOR_LIST) >= 1:
				break  # Only exits if we have work to do

		logging.info("Starting monitor")

		while True:
			for i in cls.MONITOR_LIST:
				server(i).check_server()
			cls.server_sleep()


class multi_server_mode(GlobalServer):
	@classmethod
	def start(cls):
		print("Multi Server mode")
		print("Press Ctrl-C to quit")

		while True:
			server_list = mc.list_servers(GlobalVars.BASE_DIRECTORY)
			logging.debug(server_list)

			for i in server_list:
				server(i).check_server()
			cls.server_sleep()


class single_server_mode(GlobalServer):
	@classmethod
	def start(cls, server_name):
		print("Single Server Mode: " + server_name)
		print("Press Ctrl-C to quit")

		while True:
			server(server_name).check_server()
			try:
				pass
			except RuntimeWarning:
				print("Please enter a valid server name")
				break
			cls.server_sleep()


class emailSettings():
	""" Container class for load/save """
	EMAIL_USERNAME = None  # Should be in form (username@domain.com)
	EMAIL_PASSWORD = None
	EMAIL_SEND_ALERT_TO = []  # Must be a list


class gmail(emailSettings):
	""" Lets users send email messages """
	# TODO Maybe implement other mail providers

	ENABLE = False

	@classmethod
	def send(cls, subject, text):
		logging.debug("Sending email")

		SUBJECT = subject
		TEXT = text

		# Prepare actual message
		message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (cls.EMAIL_USERNAME, ", ".join(cls.EMAIL_SEND_ALERT_TO), SUBJECT, TEXT)

		emailServer = smtplib.SMTP("smtp.gmail.com", 587)  # or port 465 doesn't seem to work!
		emailServer.ehlo()
		emailServer.starttls()
		emailServer.login(cls.EMAIL_USERNAME, cls.EMAIL_PASSWORD)
		emailServer.sendmail(cls.EMAIL_USERNAME, cls.EMAIL_SEND_ALERT_TO, message)
		emailServer.close()

	@staticmethod
	def loadSettings():
		if os.path.isfile(GlobalVars.EMAIL_SETTINGS_FILE_PATH):
			with open(GlobalVars.EMAIL_SETTINGS_FILE_PATH) as fh:
				rawJSON = gmail.decodeSettings(fh.read())
				emailSettings.__dict__ = json.loads(rawJSON)
				logging.debug(emailSettings.__dict__)

	@staticmethod
	def saveSettings():
		with open(GlobalVars.EMAIL_SETTINGS_FILE_PATH, "w") as fh:
			rawJSON = json.dumps(emailSettings.__dict__, sort_keys=True, indent=0)
			fh.write(gmail.encodeSettings(rawJSON))

	@staticmethod
	def decodeSettings(RawData):  # TODO Implement encryption
		rawJSON = base64.b64decode(RawData).decode('rot13').decode('rot13').decode('hex')
		return rawJSON

	@staticmethod
	def encodeSettings(JSONin):
		rawData = JSONin.encode('hex').encode('rot13').encode('rot13')
		return base64.b64encode(rawData)

	@classmethod
	def email_configure(cls):
		cls.loadSettings()
		print("Enter user email (user@domain.com) or press enter to skip")
		user_input = raw_input('(' + str(cls.EMAIL_USERNAME) + ')>')
		if user_input != "":
			emailSettings.EMAIL_USERNAME = user_input

		print("Enter email password or press enter to skip")
		user_input = getpass.getpass(prompt='>')  # To stop shoulder surfing
		if user_input != "":
			emailSettings.EMAIL_PASSWORD = user_input

		print("Clear alerts list? (yes/no)?")
		user_input = raw_input(">")
		if user_input == "yes":
			emailSettings.EMAIL_SEND_ALERT_TO[:] = []  # Clear the list
			print("Alerts list cleared")

		print("Send alerts to (press enter when done):")
		while True:
			user_input = raw_input('(' + str(cls.EMAIL_SEND_ALERT_TO) + ')>')
			if user_input == "":
				break
			emailSettings.EMAIL_SEND_ALERT_TO.append(user_input)
		logging.debug(emailSettings.__dict__)
		cls.saveSettings()


class server():
	""" A re-implemented instance of the mc class"""
	# Yes, I want to use inheritance, but for some odd reason when I do, everything breaks :(
	def __init__(self, server_name):
		self.server_name = server_name

	def check_server(self):
		logging.info("Checking server {0}".format(self.server_name))

		if self.is_server_up():
			logging.debug("Server {0} is Up".format(self.server_name))
		else:
			logging.error("Server {0} is Down".format(self.server_name))
			self.start_server()
			sleep(GlobalVars.BOOT_WAIT)

	def is_server_up(self):
		return mc(server_name=self.server_name, owner=GlobalVars.MINEOS_USERNAME, base_directory=GlobalVars.BASE_DIRECTORY).up

	def start_server(self):
		logging.info("Starting Server: " + self.server_name)
		mc(self.server_name, owner=GlobalVars.MINEOS_USERNAME, base_directory=GlobalVars.BASE_DIRECTORY).start()
		# self.start()  # Re implementing it causes "[error]" to display on the Web GUI when it runs
		logging.info("Server Started")
		if gmail.ENABLE:
			try:
				logging.debug("Debug logging should be off, so we write issues to the file, NOT the console")
				with open(GlobalVars.LOG_FILENAME) as f:
					log = f.read()
					gmail.send(subject="Server " + self.server_name + " is down", text=log)  # Sends alert
			except IOError:
				logging.error("Can't find the log file to send, aborting sending mail")


if __name__ == "__main__":
	gmail.loadSettings()
	main()

