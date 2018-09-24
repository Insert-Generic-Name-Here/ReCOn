import os, sys
import subprocess
import paramiko
import threading
import configparser

def interactive_ssh(servers, server_name):

	usrn = servers[server_name]['uname']
	host = servers[server_name]['host']
	key = servers[server_name]['pkey']
	port = servers[server_name]['port']

	try:
		retcode = subprocess.call(f'ssh -i {key} -p {port} {usrn}@{host}', shell=True)
		if retcode < 0:
			print (sys.stderr, "\nSSH Shell was terminated by signal", -retcode)
		else:
			print (sys.stderr, "\nSSH Shell returned", retcode)
	except OSError as e:
		print (sys.stderr, "\nSSH Interactive Shell creation failed:", e)


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


def sftp_upload(data, dest, server):
	print (f'\tSource Data Path: {data}')
	print (f'\tDestination Data Path: {dest}')
	print (f'Server \'{server["uname"]}@{server["host"]}\'')
	ssh = server['connection']
	sftp = ssh.open_sftp()
	sftp.put(data, dest, confirm=True)
	file_name = dest[dest.rfind('/')+1:]
	files_in_dir = sftp.listdir(dest[:dest.rfind('/')+1])
	if file_name in files_in_dir:
		print (f'[+] SFTP for file \'{file_name}\' on \'{server["uname"]}@{server["host"]}\' successful')
	else:
		print('[-] SFTP transfer failed')
	sftp.close()
	

def get_servers(ini_path, host_name=''):
	server_objs = {}
	servers = configparser.ConfigParser()
	servers.read(ini_path)
	if host_name == '':
		for server_name in servers.sections():
			server_objs.update({server_name : get_server_object(server_name, servers)})
		return server_objs
	else:
		return get_server_object(host_name, servers)
	

def get_server_object(server_name, servers_ini):
	print (f'\tConnecting with Host: {server_name}')
	host = servers_ini[server_name]['host']
	uname = servers_ini[server_name]['uname']
	port = servers_ini[server_name]['port']
	pkey = servers_ini[server_name]['pkey']
	recon_path = servers_ini[server_name]['recon_path']

	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh_pkey = paramiko.RSAKey.from_private_key_file(pkey)

	try:
		ssh.connect(host, port=port, pkey=ssh_pkey, username=uname)
		print (f'[+] Success for host: {server_name}')
		curr_server = {}
		curr_server = {'connection':ssh, 'host':host, 'uname':uname, 'port':port, 
					   'pkey':pkey, 'recon_path': recon_path}
		return curr_server
	except:
		print(f"[-] Host {server_name} is Unavailable.")
		return 0		


def close_connection(servers, host_name=''):
	if (host_name):
		print (f'\t[+] Closing the SSH Connection for {host_name} ...')
		servers[host_name]['connection'].close()
		print (f'[+] Connection to {host_name} Closed.')
	else:
		print (f'\t[+] Closing the SSH Connection for All Servers ...')
		for serv in servers:
			servers[serv]['connection'].close()
		print ('[+] All Connections Closed.')
