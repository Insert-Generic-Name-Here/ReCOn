import os
from sys import argv
import paramiko
import configparser
from lib.connections import select_server
import lib.ServerWorkSync as sync
from watchdog.observers import Observer
from time import gmtime, strftime, sleep


'''
    las sync --all: Implicit Folder Sync (GOTO: workspace.ini > SYNC ALL PATHS)
    las sync --path WORKSPACE_PATH : Explicit Folder Sync

    las <PROCESS>: Sync all paths on workspace.ini and Execute <PROCESS> on Default Server.
    las --server SERVER_NAME --workspace WORKSPACE_NAME <PROCESS>: Sync selected workspace on workspace.ini and Execute <PROCESS> on Selected Server (SERVER_NAME must be on servers.ini).
'''


if __name__ == '__main__':
    ssh_config = configparser.ConfigParser()
    ssh_config.read(os.path.join(os.environ['RECON_LOCAL_PATH'],'servers.ini'))
    # ssh_config.read(os.path.join('lib', 'utilities','ssh_config.ini'))
    ssh_config = select_server(ssh_config)

    curr_server = {'host':ssh_config['HOST'], 'uname':ssh_config['UNAME'], 'port':ssh_config['PORT'], 
                   'pkey':ssh_config['PKEY'], 'recon_path':os.path.join('/home',ssh_config['UNAME'],'.recon')}
    
    # Initiating the Connection
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_pkey = paramiko.RSAKey.from_private_key_file(curr_server['pkey'])    
    
    ssh_client.connect(hostname=curr_server['host'], username=curr_server['uname'], port=curr_server['port'], pkey=ssh_pkey)
    curr_server['connection'] = ssh_client

    # Initiating the Client and Server paths 
    ## Get The HOME Directory of the SSH Server
    stdin, stdout, stderr = curr_server['connection'].exec_command("echo $HOME")
    ssh_server_home_dir = stdout.readlines()[0].split('\n')[0]
    # ssh_server_home_dir

    ## Get the Workspace Directory of SSH Client 
    ssh_client_localpath = os.path.abspath(".")
    # ssh_client_localpath

    ## Instantiate a ServerWorkSync WatchDog (handler) as well as a Recursive Observer Object for the given handler
    handler = sync.ServerWorkSync(curr_server['connection'], localpath = ssh_client_localpath, remotepath = ssh_server_home_dir)  
    observer = Observer()
    observer.schedule(handler, path = ssh_client_localpath, recursive = True)
    observer.start()

    try:
        while True:
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), end='\r', flush=True)
            sleep(1)
    except KeyboardInterrupt:
        print ('\nStopping the Observer...')
        observer.stop()
    finally:
        print ('Closing the SSH Connection...')
        observer.join()
        ssh_client.close()