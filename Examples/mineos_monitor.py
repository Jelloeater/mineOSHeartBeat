#!/usr/bin/env python2.7
"""A python script to manage minecraft servers
Designed for use with MineOS: http://minecraft.codeemo.com
Will start servers based on the [onreboot][start] value in server.config
"""

__author__ = "William Dizon"
__license__ = "GNU GPL v3.0"
__version__ = "0.6.0"
__email__ = "wdchromium@gmail.com"

import logging
from mineos import mc
from time import sleep
from argparse import ArgumentParser

STATES = {True: 'UP', False: 'DOWN'}
logging.basicConfig(filename="heartbeat.log",
                    format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                    level=logging.INFO)

if __name__ == "__main__":
	parser = ArgumentParser(description='MineOS command line server starter',
	                        version=__version__)

parser.add_argument('-d',
                    dest='base_directory',
                    help='the base of the mc file structure',
                    default='/var/games/minecraft')
parser.add_argument('-i',
                    dest='interval',
                    help='how often to check state',
                    default=60)

args = parser.parse_args()

while 1:
	for i in mc.list_servers(args.base_directory):
		throwaway = mc(i, base_directory=args.base_directory)

if throwaway.server_config['onreboot':'start']:
	logging.info('Checking server "%s" - %s:%s' % (i,
	                                               throwaway.ip_address,
	                                               throwaway.port))
logging.info('Server %s: %s' % (i, STATES[throwaway.up]))
try:
	if not throwaway.up:
		throwaway.start()  # try/catch + if to catch decorator exception spam
except RuntimeError as e:
	logging.error(e.message)
else:
	sleep(30)

retest = 'Server %s: %s' % (i, STATES[throwaway.up])
if throwaway.up:
	logging.info(retest)
else:
	logging.error(retest)
sleep(args.interval)