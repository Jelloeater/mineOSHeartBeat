__author__ = 'Jesse'

#!/usr/bin/env python2.7
from minecraft_query import MinecraftQuery


def main():
	print("Hi")
	query = MinecraftQuery("192.168.1.151", 25565)

	basic_status = query.get_status()
	print "The server has %d players" % (basic_status['numplayers'])

	full_info = query.get_rules()
	print "The server is on the map '%s'" % (full_info['map'])


if __name__ == "__main__":
	main()
