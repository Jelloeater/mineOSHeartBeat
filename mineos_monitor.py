#!/usr/bin/env python2.7
"""A python project for managing Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""

import logging
from time import sleep
import sys
import argparse

sys.path.append("/usr/games/minecraft")  # So we can run the script from other locations
from mineos import mc

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.6b"
__email__ = "jelloeater@gmail.com"





class Settings():
	BASE_DIRECTORY = ""


def main():
	parser = argparse.ArgumentParser(description="A MineOS Server Monitor"
	                                             " (http://github.com/jelloeater/MineOSheartbeat)",
	                                 version=__version__, epilog="Please specify mode (-s, -i or -m) to start monitoring")

	server_group = parser.add_argument_group('Single Server Mode')
	server_group.add_argument("-s", "--single", action="store", help="Single server watch mode")

	interactive_group = parser.add_argument_group('Interactive Mode')
	interactive_group.add_argument("-i", "--interactive", help="Interactive menu mode", action="store_true")

	multi_server_group = parser.add_argument_group('Multi Server Mode')
	multi_server_group.add_argument("-m", "--multi", help="Multi server watch mode", action="store_true")

	parser.add_argument("-t", "--timeout", action="store", type=int, default=60,
	                    help="Wait x second between checks (ex. 60)")

	parser.add_argument('-b', dest='base_directory', help='MineOS Server Base Location (ex. /var/games/minecraft)',
	                    default='/var/games/minecraft')
	parser.add_argument("-l", "--list", action="store_true", help="List MineOS Servers")
	parser.add_argument("-d", "--debug", action="store_true", help="Debug Logging Flag")
	args = parser.parse_args()

	if len(sys.argv) == 1:  # Displays help and lists servers
		parser.print_help()
		sys.exit(1)

	Settings.BASE_DIRECTORY = args.base_directory

	if args.list:
		print("Servers @ " + Settings.BASE_DIRECTORY)
		for i in mc.list_servers(Settings.BASE_DIRECTORY):
			print(i)

	if args.debug:
		logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
		                    level=logging.DEBUG)
	else:
		logging.basicConfig(filename="heartbeat.log",
		                    format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
		                    level=logging.WARNING)

	logging.debug(sys.path)

	# TODO I hope there is a better way to do this
	if args.interactive and not args.single and not args.multi:
		interactive_mode.HEART_BEAT_WAIT = args.timeout
		interactive_mode.start()

	if args.single and not args.interactive and not args.multi:
		single_server_mode.TIME_OUT = args.timeout
		single_server_mode.start(args.server)

	if args.multi and not args.interactive and not args.single:
		multi_server_mode.TIME_OUT = args.timeout
		multi_server_mode.start()


class interactive_mode():
	MONITOR_LIST = []
	HEART_BEAT_WAIT = 5

	@classmethod
	def start(cls):
		print("Interactive Mode")

		# FIXME loop logic is messy
		mcServers = interactive_mode.get_server_status_list()

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
				sleep(.5)
			sleep(cls.HEART_BEAT_WAIT)


	@classmethod
	def get_server_status_list(cls):
		mcServers = mc.list_servers(Settings.BASE_DIRECTORY)
		status = []
		for i in mcServers:
			x = server(i)
			if x.is_server_up():
				status.append("UP")
			else:
				status.append("DOWN")
		return list(zip(mcServers, status))


class multi_server_mode:
	TIME_OUT = 60

	@classmethod
	def start(cls):
		print("Multi Server mode")
		print("Press Ctrl-C to quit")

		while True:
			for i in mc.list_servers(Settings.BASE_DIRECTORY):
				server(i).check_server()
			sleep(cls.TIME_OUT)


class single_server_mode:
	TIME_OUT = 60

	@classmethod
	def start(cls, server_name):
		print("Single Server Mode: " + server_name)
		print("Press Ctrl-C to quit")

		while True:
			try:
				server(server_name).check_server()
			except RuntimeWarning:
				print("Please enter a valid server name")
				break
			sleep(cls.TIME_OUT)


class server():
	def __init__(self, serverName, owner="mc", serverBootWait=120):
		self.serverName = serverName
		self.owner = owner
		self.bootWait = serverBootWait

	def check_server(self):
		logging.info("Checking server {0}".format(self.serverName))

		if self.is_server_up():
			logging.debug("Server {0} is Up".format(self.serverName))
		else:
			logging.error("Server {0} is Down".format(self.serverName))
			self.start_server()
			sleep(self.bootWait)

	def is_server_up(self):
		return mc(server_name=self.serverName, base_directory=Settings.BASE_DIRECTORY).up

	def start_server(self):
		logging.info("Starting Server: " + self.serverName)
		x = mc(self.serverName, self.owner, Settings.BASE_DIRECTORY)
		x.start()
		logging.info("Server Started")


if __name__ == "__main__":
	main()
