#!/usr/bin/env python2.7
"""A python project to manage Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""
import multiprocessing
import logging
from time import sleep
import sys
from mineos import mc
import argparse


__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.1b"
__email__ = "jelloeater@gmail.com"

logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                    level=logging.WARNING)

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
		interactive_mode()
	if args.server and not args.interactive:
		server_mode(args.server)


def interactive_mode():
	print("Interactive Mode")
	serverList = mc.list_servers(baseDirectory)
	print(serverList)

	# exServer = server(serverList[0])
	# exServer.monitor_server()

	logging.info("Starting monitor")
	sleep(120)
	serversToCheck = []

	pool = multiprocessing.Pool(serverList, server.monitor_server)

	pool.map()
	pool.close()
	pool.join()


# TODO Implement TUI menu?
# TODO Create command line arg parse for reuse

def server_mode(server_name):
	print("Single Server Mode")
	print(server_name)


def get_server_list(self):
	return mc.list_servers(baseDirectory)


class server():
	def __init__(self, serverName, owner="mc", serverBootWait=120, heartBeatWait=60):
		self.serverName = serverName
		self.owner = owner
		self.bootWait = serverBootWait
		self.heartBeatWait = heartBeatWait

	def monitor_server(self):
		while True:
			logging.info("Checking server {0}".format(self.serverName))

			if self.is_server_up():
				logging.debug("Server {0} is Up".format(self.serverName))
			else:
				logging.error("Server {0} is Down".format(self.serverName))
				self.start_server()
				sleep(self.bootWait)

			sleep(self.heartBeatWait)

	def is_server_up(self):
		return mc(server_name=self.serverName, base_directory=baseDirectory).up

	def start_server(self):
		logging.info("Starting Server: " + self.serverName)
		x = mc(self.serverName, self.owner, baseDirectory)
		x.start()
		logging.info("Server Started")


if __name__ == "__main__":
	main()
