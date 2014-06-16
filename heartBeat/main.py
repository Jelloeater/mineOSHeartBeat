import logging
from socket import timeout
import os
from time import sleep
from minecraft_query import MinecraftQuery

__author__ = 'Jesse S'

logging.basicConfig(filename="/heartBeat.log", format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)", level=logging.INFO)


def main():
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
