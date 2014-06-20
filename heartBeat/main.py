#!/usr/bin/env python2.7
"""A python project to manage Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""
import logging
import multiprocessing
from threading import Thread
from time import sleep
import sys
import argparse

from mineos import mc


__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.1b"
__email__ = "jelloeater@gmail.com"

logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                    level=logging.DEBUG)

baseDirectory = "/var/games/minecraft"


def main():
	logging.debug(sys.path)

	parser = argparse.ArgumentParser(usage="Please specify either -i or -s",
	                                 description="A MineOS Server Monitor"
	                                             " (http://github.com/jelloeater/MineOSheartbeat)",
	                                 version=__version__, )
	parser.add_argument("-i", "--interactive", help="Interactive menu mode",
	                    action="store_true")
	parser.add_argument("-s", "--server", action="store", help="Single server watch mode"
	)
	args = parser.parse_args()

	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(1)

	if args.interactive and not args.server:
		interactive_mode.start()
	if args.server and not args.interactive:
		server_mode(args.server)


class interactive_mode():
	monitor_list = []
	heartBeatWait = 5

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
			cls.monitor_list = [x[0][0] for x in serverList if x[1] is True]

			print(user_input)
			if user_input == "Done" or user_input == "d" and len(
					cls.monitor_list) >= 1:  # Only exits if we have work to do
				break

		logging.info("Starting monitor")

		# FIXME Multi processing isn't working due to a pickle error.
		# server(cls.monitor_list[0]).monitor_server()

		while True:
			for i in cls.monitor_list:
				server(i).check_server()
				sleep(.5)
			sleep(cls.heartBeatWait)


	@classmethod
	def get_server_status_list(cls):
		mcServers = mc.list_servers(baseDirectory)
		status = []
		for i in mcServers:
			x = server(i)
			if x.is_server_up():
				status.append("UP")
			else:
				status.append("DOWN")
		return list(zip(mcServers, status))


def monitorServerWorker(serverName):
	server(serverName).check_server()


def server_mode(server_name):
	print("Single Server Mode")
	print(server_name)


def get_server_list(self):
	return mc.list_servers(baseDirectory)


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
		return mc(server_name=self.serverName, base_directory=baseDirectory).up

	def start_server(self):
		logging.info("Starting Server: " + self.serverName)
		x = mc(self.serverName, self.owner, baseDirectory)
		x.start()
		logging.info("Server Started")


if __name__ == "__main__":
	main()
