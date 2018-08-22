import configparser
import os

def server_ini_creator(path='.'):
    Config = configparser.ConfigParser()

    info = str(input('Add servers -> Nickname Host Username Enable-Jupyter-Forwarding(y/n) / next server...)\n ex. pi 192.168.1.1 Josh y \n'))

    servers = info.split('/')
    for server in servers:
        server = server.split()
        Config[server[0]] = {'HOST': server[1],'UNAME': server[2],'JUPYTER': server[3]}

    with open(os.path.join(path,'servers.ini'), 'w') as configfile:
        Config.write(configfile)

def dsad(env):
    process = subprocess.Popen(bash_commands.create_env(env).split(), stdout=subprocess.PIPE)
    print(process.communicate())
    process = subprocess.Popen(bash_commands.set_default_env(env).split(), stdout=subprocess.PIPE)
    print(process.communicate())

def sftp_upload(file, )