import os, sys
import subprocess
import bash_commands
import time
import paramiko
import configparser

def create_env(selected_env):
	return f'conda env create -f ~/.recon/envs/{selected_env}_envfile.yml'

def set_default_env(envname):
	return f"echo 'source activate {envname}' >> ~/.bashrc && . ~/.bashrc"

def export_env(selected_env):
	return f'conda env export --no-builds -n {selected_env}> {selected_env}_envfile.yml'

def yes_no(msg, default_yes=True):
	if default_yes:
		return input(f"{msg} (Y/n) ").lower() != 'n'
	else:
		return input(f"{msg} (y/N) ").lower() == 'y'


# def get_conda_envs():
# 	process = subprocess.Popen('which conda'.split(), stdout=subprocess.PIPE)
# 	conda_dir = process.communicate()[0].decode('utf8').replace('\n', '').split('/bin')[0]
# 	process = subprocess.Popen(f'ls {conda_dir}/envs'.split(), stdout=subprocess.PIPE)
# 	envs = process.communicate()[0].decode('utf8').replace('\n', ',')[:-1].split(',') # if empty -> no envs
# 	if envs[0] == '': return ''
# 	envs.insert(0, 'base')
# 	return envs


def select_env():

	process = subprocess.Popen('which conda'.split(), stdout=subprocess.PIPE)
	conda_dir = process.communicate()[0].decode('utf8').replace('\n', '').split('/bin')[0]
	process = subprocess.Popen(f'ls {conda_dir}/envs'.split(), stdout=subprocess.PIPE)
	envs = process.communicate()[0].decode('utf8').replace('\n', ',')[:-1].split(',') # if empty -> no envs
	if envs[0] == '':
		return 'base'
	
	envs.insert(0, 'base')
	
	while True:
		try: 
			[print (f'[{ind}]{env} ',end='') for ind, env in enumerate(envs)]
			inpt = input ('(Default [0]): ')
			if inpt == '': 
				selected_env = envs[0]
				break
			index_of_env = int(inpt)
			if index_of_env < len(envs):
				selected_env = envs[index_of_env]
				break
			else:
				raise ValueError()
		except ValueError:
			print('Invalid option')
		except KeyboardInterrupt:
			sys.exit()

	return selected_env
		
	
def upload_env(selected_env, hostname='ELMA', config='config.ini'):

	servers = configparser.ConfigParser()
	servers.read('/Users/giorgostheo/Code/RemoteCompProject/servers.ini')
	for host in servers.sections():
		target_file = f'/home/{servers[host]['uname']}/.recon/envs/{selected_env}_envfile.yml'
		s = paramiko.SSHClient()
		s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		try:
			s.connect(servers[host]['host'],22,username=servers[host]['uname'],timeout=4)

			sftp = s.open_sftp()
			sftp.put(f'{selected_env}_envfile.yml', target_file)
			s.close()
		except: 
			print(f"Server {host} is unavailable.")


		




	

