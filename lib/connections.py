import os, sys
import subprocess
import paramiko
import threading
import configparser

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
	print ('server' , server)
	ssh = server['connection']
	sftp = ssh.open_sftp()
	sftp.put(data, dest, confirm=True)
	file_name = dest[dest.rfind('/')+1:]
	files_in_dir = sftp.listdir(dest[:dest.rfind('/')+1])
	if file_name in files_in_dir:
		print (f'[+] SFTP for file "{file_name}" on server "{server}" successful')
	else:
		print('[-] SFTP transfer failed')
	sftp.close()
	

def get_servers(ini_path):
	server_objs = {}
	servers = configparser.ConfigParser()
	servers.read(ini_path)
	for server_name in servers.sections():
		print (f'\tConnecting with Host: {server_name}')

		host = servers[server_name]['host']
		uname = servers[server_name]['uname']
		port = servers[server_name]['port']
		pkey = servers[server_name]['pkey']

		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh_pkey = paramiko.RSAKey.from_private_key_file(pkey)

		try:
			ssh.connect(host, port=port, pkey=ssh_pkey, username=uname)
			print (f'[+] Success for host: {server_name}')
			curr_server = {}
			curr_server = {'connection':ssh, 'host':host, 'uname':uname, 'port':port, 
						   'pkey':pkey, 'recon_path': os.path.join('/home',uname,'.recon')}
			server_objs.update({server_name : curr_server})
		except: 
			print(f"[-] Host {server_name} is Unavailable.")

	return server_objs

def close_all(servers):
	for serv in servers:
		servers[serv]['connection'].close()