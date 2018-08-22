import os 
import subprocess
import paramiko
import threading
import configparser

### USE THESE FOR CONNECTING TO THE SERVERS ###

def ssh_connect(host, uname, cmd, *args):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		ssh.connect(host, username=uname)
		stdin, stdout, stderr = ssh.exec_command(cmd(*args))
		print (f'Success for server {host}')
		ssh.close()
	except: 
		print(f"Server {host} is unavailable.")

def exec_all_servers(cmd, *args):
	
	servers = configparser.ConfigParser()
	servers.read('/Users/giorgostheo/Code/RemoteCompProject/servers.ini')
	for host in servers.sections():
		ssh_connect(servers[host]['host'],servers[host]['uname'],cmd, *args)

def connect_to_server(cmd, host='', uname='', *args):
	''' Connect with one or more servers.

			IMP: If host or uname variables are empty, exec command on every available server

			Keyword arguments:
			cmd -- command to be executed
			host -- host to connect to
			uname --  username
			*args -- more args if needed
			"""
		'''
	if host=='' or uname=='':
		exec_all_servers(cmd, *args)
	else:
		ssh_connect(host, uname, cmd, *args)
