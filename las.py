#!/usr/bin/env python

## Lick (the timestamp) And Send it --> LAS

import sys
import configparser
import paramiko 
import argparse
from setuptools import find_packages
import lib.connections


servers = configparser.ConfigParser()
servers.read('servers.ini')

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('select_server', choices=servers.sections(), help='Pick a server from the available ones')
args = parser.parse_args()
print (args.select_server)

host = servers[args.select_server]['host']
uname = servers[args.select_server]['uname']

cmd = ' '.join(sys.argv[1:])
if cmd == '': print('Shoooot yooo foookin mout and type foookin smthing m8')

lib.connections.connect_to_server(host, uname, cmd)
