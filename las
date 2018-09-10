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

workspaces = configparser.ConfigParser()
workspaces.read('workspaces.ini')

server_parser = argparse.ArgumentParser(add_help=False)
server_parser.add_argument('--server','-s',dest='server_name',nargs='?',choices=servers.sections(), help='Pick a server from the available ones',metavar='SERVER_NAME')

workspace_parser = argparse.ArgumentParser(add_help=False)
workspace_parser.add_argument('--workspace','-w',dest='workspace_name' ,nargs='?', help='Pick a workspace from the available ones',metavar='WORKSPACE_NAME')

all_parser = argparse.ArgumentParser(add_help=False)
all_parser.add_argument('--all', '-a',default=False, action="store_true", help= 'Run command on all servers')

parser = argparse.ArgumentParser(description='Process some integers.')
subparser = parser.add_subparsers(metavar='command')
run = subparser.add_parser('exec', help = 'Execute a command on server',description='Process some integers.', parents=[server_parser])
run.add_argument('command',nargs='?',type=str )
add = subparser.add_parser('add', help = 'Add server or workspace', parents=[server_parser,workspace_parser])
info = subparser.add_parser('info', help='Show info', parents=[server_parser, all_parser,workspace_parser])
sync = subparser.add_parser('sync', help='Sync files on server', parents=[server_parser, all_parser,workspace_parser])
portf = subparser.add_parser('port-forward', help='Setup port forwarding', parents=[server_parser])
connect = subparser.add_parser('connect', help='Open an interactive ssh connection with server', parents=[server_parser])
args = parser.parse_args()
print ('known',vars(args))

# try:
#     args, ukargs = parser.parse_known_args()
#     print ('known',vars(args))
#     print ('unknown',ukargs)
# except SystemExit:
#     args = parser.parse_args(['exec',cmd])
#     print('yea')



#print (args.step)
# server_dict = connections.get_servers('servers.ini', args.server)

# cmd = ' '.join(sys.argv[1:])
# if cmd == '': print('Shoooot yooo foookin mout and type foookin smthing m8')

# server_dict['connection'].exec_command(cmd.split())