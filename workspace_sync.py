import os
import paramiko
import configparser
import utilities.ServerWorkSync as sync
from watchdog.observers import Observer
from time import gmtime, strftime, sleep


if __name__ == '__main__':
    # Getting Remote Server Information (host, name, port)
    ssh_config = configparser.ConfigParser()
    ssh_config.read(os.path.join('.', 'utilities', 'ssh_config.ini'))

    ssh_hostname = ssh_config['CONNECTION']['HOST']
    ssh_username = ssh_config['CONNECTION']['USER']
    ssh_port     = ssh_config['CONNECTION']['PORT']

    # Getting RSA Private Key
    ssh_pkey = paramiko.RSAKey.from_private_key_file(config['CONNECTION']['PKEY'])
    
    # Initiating the Connection and Opening an SFTP Session
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ssh_hostname, username=ssh_username, port=ssh_port, pkey=ssh_pkey)
    sftp_client = ssh_client.open_sftp()

    # Initiating the Client and Server paths 
    ## Get The HOME Directory of the SSH Server
    stdin, stdout, stderr = ssh_client.exec_command("echo $HOME")
    ssh_server_home_dir = stdout.readlines()[0].split('\n')[0]
    ssh_server_home_dir

    ## Get the Workspace Directory of SSH Client 
    ssh_client_localpath = os.path.abspath(".")
    ssh_client_localpath

    ## Instantiate a ServerWorkSync WatchDog (handler) as well as a Recursive Observer Object for the given handler
    handler = sync.ServerWorkSync(sftp_client, localpath = ssh_client_localpath, remotepath = ssh_server_home_dir)  
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