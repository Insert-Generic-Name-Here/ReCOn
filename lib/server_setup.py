import configparser
import os
from pathlib import Path

def server_ini_creator(path):
    Config = configparser.ConfigParser()

    info = str(input('Add servers -> Nickname, Host, Username, Port, RSA ID (Private) Key Path, Enable-Jupyter-Forwarding(y/n) / next server...\n ex. pi 192.168.1.1 Josh 22 y \n'))
    servers = info.split('/')
      
    for server in servers:
        server = server.split(',')
        Config[server[0]] = {'HOST': server[1].strip(),'UNAME': server[2].strip(),'PORT': server[3].strip(), 'PKEY':server[4].strip(), 'JUPYTER': server[5].strip()}

    with open(os.path.join(path,'servers.ini'), 'w+') as configfile:
        Config.write(configfile)

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