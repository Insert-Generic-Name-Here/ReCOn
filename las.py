#!/usr/bin/env python

## Lick (the timestamp) And Send it --> LAS

import sys, os
import configparser
import paramiko 
import argparse
from setuptools import find_packages
from lib import connections

config_path = './configs'

servers = configparser.ConfigParser()
servers.read(os.path.join(config_path,'servers.ini'))

workspaces = configparser.ConfigParser()
workspaces.read(os.path.join(config_path,'workspace.ini'))

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--sync', default=False, action="store_true", help='Sync')
parser.add_argument('--server',dest='server_name',nargs='?',choices=servers.sections(), help='Pick a server from the available ones')
parser.add_argument('--workspace',dest='workspace_name' ,nargs='?', help='Pick a workspace from the available ones')


args, ukargs = parser.parse_known_args()

# print ('known',vars(args))
# print ('unknown',ukargs)

server_dict = connections.get_servers('servers.ini', args.server_name)

cmd = ' '.join(ukargs)
if cmd == '': print('Shoooot yooo foookin mout and type foookin smthing m8')

server_dict['connection'].exec_command(cmd.split())
print (cmd)
