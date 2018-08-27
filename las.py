#!/usr/bin/env python

## Lick (the timestamp) And Send it --> LAS

import sys
import configparser
import paramiko 
import argparse
from setuptools import find_packages
from lib import connections


servers = configparser.ConfigParser()
servers.read('servers.ini')


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--server',dest='servers_name',nargs='?',choices=servers.sections(), help='Pick a server from the available ones')
parser.add_argument('--sync', default=False, action="store_true", help='Sync')
#parser.add_argument('--workspace' ,nargs='?',choices=servers.sections(), help='Pick a workspace from the available ones')
args = parser.parse_args()

print (vars(args))
# server_dict = connections.get_servers('servers.ini', args.server)

# cmd = ' '.join(sys.argv[1:])
# if cmd == '': print('Shoooot yooo foookin mout and type foookin smthing m8')

# server_dict['connection'].exec_command(cmd.split())
