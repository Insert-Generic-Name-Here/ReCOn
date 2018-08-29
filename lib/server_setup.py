import os
import configparser
from pathlib import Path


### UPDATED ###
def server_ini_creator(path):
    home = str(Path.home())
    config = configparser.ConfigParser()
    
    info = str(input('Add servers -> Nickname, Host, Username, Port, Enable-Jupyter-Forwarding(y/n) / next server...\n ex. pi, 192.168.1.1, Josh, 22, y \n'))
    servers = info.split('/')

    for server in servers:
        pkey_path = input(f'RSA (Private) Key Path for Server {server[1].strip()} (Default: {os.path.join(home, ".ssh", "id_rsa")}): ')

        if (pkey_path == ''):
            pkey_path = os.path.join(home, '.ssh', 'id_rsa')

        server = server.split(',')
        config[server[0]] = {'HOST'    : server[1].strip(),
                             'UNAME'   : server[2].strip(),
                             'PORT'    : server[3].strip(),
                             'PKEY'    : pkey_path,
                             'JUPYTER' : server[4].strip()}

    with open(os.path.join(path,'servers.ini'), 'w+') as configfile:
        config.write(configfile)
##############
	
    	
def get_path():
    home = str(Path.home())
    def_path = os.path.join(home,'.recon')
    while True:
        path = str(input(f"Select path -> (Default: '{def_path}')\n"))  
        if path == '' : 
            return def_path
        if os.path.exists(path):
            return path
        else:
            print ('invalid')


def create_dir_tree(path,dirs):
    cmd = f"mkdir {path} "
    for folder in dirs:
        cmd += os.path.join(path,str(folder))+ ' '
    return cmd

