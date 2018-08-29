import os
import configparser
from lib.connections import *


def workspace_ini_creator(servers_path):
    Config = configparser.ConfigParser()
    servers = configparser.ConfigParser()
    servers.read(servers_path)
    srv = select_server(servers)

    print (f'Configuring workspaces for {srv.name}')
    while(1):
        info = str(input('Add Workspace:Name (Default name -> dir name)\n ex. /home/ReCon : ReCon workspace\n '))

        workspace = [arg.strip() for arg in info.split(':') ]
        if len(workspace)==1:
            w_name = os.path.split(workspace[0])[-1]
            w_path = workspace[0]
        else:
            w_path = workspace[0]
            w_name = workspace[1]
        if os.path.exists(w_path):
            break
        else:
            print('Path not available')


    Config[server_name] = {w_name: w_path}
    with open(os.path.join('workspaces.ini'), 'w+') as configfile:
        Config.write(configfile)