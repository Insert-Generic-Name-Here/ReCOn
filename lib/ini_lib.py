import os
import readline
from lib.connections import *
from lib.autocomplete import *
import configparser
from pathlib import Path

def workspace_ini_creator(config_path):
    Config = configparser.ConfigParser()
    servers = configparser.ConfigParser()
    servers.read(os.path.join(config_path,'servers.ini'))
    srv = select_server(servers)

    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(pathCompleter)

    print (f'[+] Configuring workspace for {srv.name}')
    while(1):
        info = str(input('Add dir to Workspace (Default name = dir name)\n ex. /home/ReCon : ReConWs\n '))

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
            print('[-] Path not available')


    Config[srv.name] = {w_name: w_path}
    with open(os.path.join(config_path,'workspaces.ini'), 'w+') as configfile:
        Config.write(configfile)
    return os.path.join(config_path,'workspaces.ini')

def props_ini_creator(config_path):
    Config = configparser.ConfigParser()
    servers = configparser.ConfigParser()
    servers.read(os.path.join(config_path,'servers.ini'))
    srv = select_server(servers)

    Config['properties'] = {'default-server': srv.name}
    Config['properties'] = {'auto-sync': False}

    with open(os.path.join(config_path,'props.ini'), 'w+') as configfile:
        Config.write(configfile)
    return os.path.join(config_path,'props.ini')

def server_ini_creator(path):
    home = str(Path.home())
    config = configparser.ConfigParser()
    
    info = str(input('Add servers -> Nickname, Host, Username, Port, Enable-Jupyter-Forwarding(y/n) / next server...\n ex. pi, 192.168.1.1, Josh, 22, y \n'))
    servers = info.split('/')

    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(pathCompleter)

    for server in servers:
        server = server.split(',')
        pkey_path = input(f'RSA (Private) Key Path for Server {server[1].strip()} (Default: {os.path.join(home, ".ssh", "id_rsa")}): ')

        if (pkey_path == ''):
            pkey_path = os.path.join(home, '.ssh', 'id_rsa')

        
        config[server[0]] = {'HOST'    : server[1].strip(),
                             'UNAME'   : server[2].strip(),
                             'PORT'    : server[3].strip(),
                             'PKEY'    : pkey_path,
                             'JUPYTER' : server[4].strip()}

    with open(os.path.join(path,'config','servers.ini'), 'w+') as configfile:
        config.write(configfile)