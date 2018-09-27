import os
import signal
from sys import argv
import paramiko
import configparser
from lib.connections import select_server, get_servers
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
    properties = configparser.ConfigParser()
    properties.read(os.path.join('config','props.ini'))
    properties = properties['properties']

    workspaces_config = configparser.ConfigParser()
    workspaces_config.read(os.path.join('config','workspaces.ini'))

    default_server = get_servers(os.path.join('config','servers.ini'), properties['default-server'])
    server_workspaces = workspaces_config[properties['default_server']]

    try:
        # Initiating the Client and Server paths 
        # Get The HOME Directory of the SSH Server
        stdin, stdout, stderr = default_server['connection'].exec_command("echo $HOME")
        ssh_server_home_dir = stdout.readlines()[0].split('\n')[0]

        for workspace_name in server_workspaces:
            ## Get the Workspace Directory of SSH Client 
            workspace_path = server_workspaces[workspace_name]

            ## Instantiate a ServerWorkSync WatchDog (handler) as well as a Recursive Observer Object for the given handler
            handler = sync.ServerWorkSync(default_server, localpath = workspace_path, remotepath = ssh_server_home_dir, verbose=True)  
            observer = Observer()
            observer.schedule(handler, path = workspace_path, recursive = True)
            observer.start()

    except (paramiko.SSHException, IOError):
        print (f'Can\'t connect to Server {properties["default-server"]}')

#TODO: Handle System Shutdown Gracefully
    try:
        while True:
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), end='\r', flush=True)
            signal.signal(signal.SIGTERM, {raise KeyboardInterrupt})
            sleep(1)
    except KeyboardInterrupt:
        print ('\nStopping the Observer...')
        observer.stop()
    finally:
        print ('Closing the SSH Connection...')
        observer.join()
        ssh_client.close()