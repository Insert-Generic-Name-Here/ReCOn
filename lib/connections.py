import os, sys
import subprocess
import paramiko
import threading
import configparser


global LOCAL_HOME_FOLDER
global LOCAL_RECON_PATH


def init():
    LOCAL_HOME_FOLDER = None
    LOCAL_RECON_PATH = None


def select_server(servers):
	opts = [host for host in servers.sections()]

	if len(opts) == 0:
		raise ValueError('No Servers Found in servers.ini.')
	if len(opts) == 1:
		return servers[opts[0]]

	while True:
		try: 
			[print (f'[{ind}]{env}',end=' ') for ind, env in enumerate(opts)]
			inpt = input ('(Default [0]): ')
			if inpt == '': 
				selected_server = opts[0]
				break
			index_of_srv = int(inpt)
			if index_of_srv < len(opts):
				selected_server = opts[index_of_srv]
				break
			else:
				raise ValueError()
		except ValueError:
			print('Invalid option')
		except KeyboardInterrupt:
			sys.exit()
		
	return servers[selected_server]


### USE THESE FOR CONNECTING TO THE SERVERS ###
def ssh_connect(cmd, config_path, server_name, *args):
	servers = configparser.ConfigParser()
	servers.read(config_path)

	host = servers[server_name]['host']
	uname = servers[server_name]['uname']
	port = servers[server_name]['port']
	pkey = servers[server_name]['pkey']

	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh_pkey = paramiko.RSAKey.from_private_key_file(pkey)
	
	try:
		ssh.connect(host, port=port, pkey=ssh_pkey, username=uname)
		stdin, stdout, stderr = ssh.exec_command(cmd(os.path.join('/home',uname,'.recon'), *args))
		#### addition if something fails check ####
		stdout.channel.recv_exit_status()
		###########################################
		# print (f'stdout:\n{stdout.readlines()}')
		# print (f'stderr:\n{stderr.readlines()}')
		print (f'[+] Success for {cmd} on host: {host}')
		output = stdout.readlines()
		ssh.close()
		return output
	except: 
		print(f"[-] Host {host} is Unavailable.")


def exec_all_servers(cmd,config_path,*args):
	outputs = []
	servers = configparser.ConfigParser()
	servers.read(config_path)
	for host in servers.sections():
		print (f'\tConnecting with Host: {host}')
		outputs.append(ssh_connect(cmd, config_path, host, *args))
	return outputs


def connect_to_server(cmd, config_path, server_name= '', cmd_args=''):
	''' Connect with one or more servers.

			IMP: If host or uname variables are empty, exec command on every available server

			Keyword arguments:
			cmd -- command to be executed
			host -- host to connect to
			uname --  username
			*args -- more args if needed
			"""
		'''
	print (f'[+] Configuration Path is: {config_path}')

	if server_name == '':
		print ('\n[+] EXECUTING COMMANDS ON ALL SERVERS\n')
		output = exec_all_servers(cmd, config_path, *cmd_args)
	else:
		print (f'\n[+] EXECUTING COMMANDS ON SERVER {server_name}\n')
		output = ssh_connect(cmd, config_path, server_name, *cmd_args)
	return output


def sftp_upload(data, dest, config_path, server_name):
	print (f'\tSource Data Path: {data}')
	print (f'\tDestination Data Path: {dest}')

	servers = configparser.ConfigParser()
	servers.read(config_path)
	host = servers[server_name]['host']
	uname = servers[server_name]['uname']
	port = servers[server_name]['port']
	pkey = servers[server_name]['pkey']

	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	ssh_pkey = paramiko.RSAKey.from_private_key_file(pkey)
	
	ssh.connect(host, port=port, pkey=ssh_pkey, username=uname)
	sftp = ssh.open_sftp()
	sftp.put(data, dest, confirm=True)
	print (f'\tUpload Successful for Server {host}')
	ssh.close()
