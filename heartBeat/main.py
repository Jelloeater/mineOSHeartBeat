#!/usr/bin/env python2.7
"""A python project to manage Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""
import multiprocessing

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.1b"
__email__ = "jelloeater@gmail.com"

import logging
from time import sleep
import sys
from mineos import mc


logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                    level=logging.DEBUG)

logging.debug(sys.path)

baseDirectory = "/var/games/minecraft"


def main():
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
