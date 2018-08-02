import paramiko

hostname = '35.198.95.94' 
myuser   = 'giorgostheo'
mySSHK   = '/Users/giorgostheo/.ssh/google_compute_engine'
sshcon   = paramiko.SSHClient()  # will create the object
sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())# no known_hosts error
sshcon.connect(hostname, username=myuser, key_filename=mySSHK)

stdin, stdout, stderr = sshcon.exec_command('conda list --explicit > spec-file.txt'.)
print (stdout.readlines())
sshcon.close()

smth = 'dnksajndk{}'