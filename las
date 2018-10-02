#!/usr/bin/env python

## Lick (the timestamp) And Send it --> LAS pf, add

import sys, os
import configparser
import paramiko 
import argparse
from setuptools import find_packages
from lib import connections,ini_lib
from lib.JournalSyncing import JournalSyncing


def get_srvname(props, server_name):
	if server_name == None:
		return props['properties']['default-server']
	else:
		return server_name


def sync_data(server_name, workspaces_config):
	server_workspaces = workspaces_config[server_name]
	jrnsync = JournalSyncing(server_name, server_workspaces, verbose=True, shallow_filecmp=True)
	jrnsync.journal_syncing()


recon_path 			= os.path.dirname(os.path.abspath(__file__))
servers_path 		= os.path.join(recon_path,'config/servers.ini')
props_path  		= os.path.join(recon_path,'config/props.ini')
workspaces_path = os.path.join('.','config','workspaces.ini')

servers = configparser.ConfigParser()
servers.read(servers_path)

props = configparser.ConfigParser()
props.read(props_path)

workspaces_config = configparser.ConfigParser()
workspaces_config.read(workspaces_path)

#PARENTS
server_parser = argparse.ArgumentParser(add_help=False)
server_parser.add_argument('--server','-s',dest='server_name',nargs='?',choices=servers.sections(), help='Pick a server from the available ones',metavar='SERVER_NAME')
all_parser = argparse.ArgumentParser(add_help=False)
all_parser.add_argument('--all', '-a',default=False, action="store_true", help= 'Run command on all servers')


parser = argparse.ArgumentParser(description='Process some integers.')
subparser = parser.add_subparsers(metavar='command', dest= 'func')
#EXEC
run = subparser.add_parser('exec', help = 'Execute a command on server',description='Process some integers.', parents=[server_parser])
run.add_argument('command',nargs='?',type=str )

#ADD
add_srv = subparser.add_parser('add-server', help = 'Add server')
add_ws = subparser.add_parser('add-workspace', help = 'Add directory to workspace')

#REMOVE
remove = subparser.add_parser('remove-server', help = 'Add server or directory to workspace')
remove.add_argument('server', choices = [x for x in servers.sections() if x not in props['properties']['default-server']],type=str)
remove = subparser.add_parser('remove-workspace', help = 'Add server or directory to workspace')
remove.add_argument('server', choices = servers.sections(),type=str)
remove.add_argument('workspace',type=str)

#DEFAULT-SERVER
def_srv = subparser.add_parser('default-server')
def_srv.add_argument('server',nargs='?',choices=servers.sections(), help='Pick a server from the available ones',metavar='SERVER_NAME')

#AUTOSYNC
auto_sync = subparser.add_parser('auto-sync')
auto_sync.add_argument('val',nargs='?',choices = ['on','off'],type=str)

#SYNC
sync = subparser.add_parser('sync', help='Sync files on server', parents=[server_parser, all_parser])

#PORT-FORWARD
portf = subparser.add_parser('port-forward', help='Setup port forwarding', parents=[server_parser])

#INTERACTIVE SSH
connect = subparser.add_parser('connect', help='Open an interactive ssh connection with server', parents=[server_parser])

args = parser.parse_args()
print (vars(args))


if args.func == 'sync':
	server_name = get_srvname(props,args.server_name)
	sync_data(server_name, workspaces_config)
	

if args.func == 'exec':

	server_name = get_srvname(props,args.server_name)
	sync_data(server_name, workspaces_config)
	# TODO sync only the workspace that is used

	server_dict = connections.get_servers(servers_path,server_name)  

	stdin, stdout, stderr = server_dict['connection'].exec_command(args.command)

	for line in iter(stdout.readline, ""):
			print(line, end="")
	stdout.channel.recv_exit_status()

if args.func == 'auto-sync':
	if args.val == 'on':
		props['properties']['auto-sync'] = 'T'
		print('AUTOSYNC ON')
	else:
		props['properties']['auto-sync'] = 'F'
		print('AUTOSYNC OFF')

	ini_lib.save_ini(props, props_path)

if args.func == 'add-server':
	servers = ini_lib.server_ini_creator(servers_path,append=True)
	print(servers.sections())
	ini_lib.save_ini(servers, servers_path)

if args.func == 'add-workspace':
	workspaces_config = ini_lib.workspace_ini_creator(os.path.join(recon_path,'config'),True,workspaces_path)
	ini_lib.save_ini(workspaces_config, workspaces_path)


if args.func == 'remove-workspace':
	if args.workspace not in workspaces_config[args.server]:
		raise parser.error(f'Workspace {args.workspace} not in server {args.server}')
	else:
		workspaces_config = ini_lib.delete_workspace(args.workspace, args.server, workspaces_config)
		ini_lib.save_ini(workspaces_config, workspaces_path)




if args.func == 'remove-server':
	servers, workspaces_config = ini_lib.remove_server(servers, workspaces_config, args.server)
	ini_lib.save_ini(servers, servers_path)
	ini_lib.save_ini(workspaces_config, workspaces_path)


if args.func == 'connect':
	server_name = get_srvname(props, args.server_name)
	connections.interactive_ssh(servers, server_name)

if args.func == 'default-server':
	props['properties']['default-server'] = str(args.server)
	print(f'DEFAULT-SERVER = {str(args.server)}')
	with open(props_path, 'w+') as configfile:
		props.write(configfile)




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