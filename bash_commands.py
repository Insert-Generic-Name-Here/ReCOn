def scp_upload(path_to_file, path_to_sshkey, uname, host):
	return f'scp -i {path_to_sshkey} {path_to_file} {uname}@{host}:~'

def export_conda_specs(specfile_name='spec-file.txt'):
	return f"conda list --explicit > {specfile_name}"

def create_conda_from_specfile(envname, specfile='spec-file.txt'):
	return f'conda create --{envname}  --file {specfile}'