#!/usr/bin/env python2.7
"""A python project to manage Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""
import argparse
import sys

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "0.1b"
__email__ = "jelloeater@gmail.com"


import logging
from socket import timeout
import os
from time import sleep
from minecraft_query import MinecraftQuery

logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)", level=logging.DEBUG)

logging.debug(sys.path)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--server", action="store", help="Single server watch mode")
	args = parser.parse_args()

	if args.server:
		monitor_server(args.server)
	else:
		print("Please specify -s")

def monitor_server():
	address = "localhost"
	port = 25565
	logging.info("Starting monitor")
	sleep(120)
	while True:
		logging.debug("Checking Server @ " + address + ":" + str(port))
		try:
			query = MinecraftQuery(address, port)
			query.get_status()
			logging.debug("Server is UP!")
		except timeout:
			logging.error("Server is Down @ " + address + ":" + str(port))
			startServer("MagicFarm")
			sleep(120)
		sleep(60)


def startServer(serverName):
	logging.info("Starting Server: " + serverName)
	os.chdir("/usr/games/minecraft")
	os.system("python ./mineos_console.py -d /var/games/minecraft -s "+serverName+" start")
	logging.info("Server Started")

if __name__ == "__main__":
	main()
