import os
import stat
import hashlib
from itertools import filterfalse


_cache = {}
BUFSIZE = 8*1024


def cmp(local_file, remote_file, sftp_client, shallow=True):
    """
    Compare two files.
    Arguments:
    local_file -- First file name
    remote_file -- Second file name
    sftp_client -- The Paramiko Object of the SFTP Connection to the Server
    shallow -- Just check stat signature (do not read the files).
               defaults to True.
    Return value:
    True if the files are the same, False otherwise.
    This function uses a cache for past comparisons and the results,
    with cache entries invalidated if their stat information
    changes.  The cache may be cleared by calling clear_cache().
    """

    s1 = _sig(os.stat(local_file))
    s2 = _sig(sftp_client.stat(remote_file))
    if s1[0] != stat.S_IFREG or s2[0] != stat.S_IFREG:
        return False
    if shallow and s1 == s2:
        return True
    if s1[1] != s2[1]:
        return False

    outcome = _cache.get((local_file, remote_file, s1, s2))
    if outcome is None:
        outcome = _do_cmp(local_file, remote_file, sftp_client)
        if len(_cache) > 100:      # limit the maximum size of the cache
            clear_cache()
        _cache[local_file, remote_file, s1, s2] = outcome
    return outcome


def _sig(st):
    return (stat.S_IFMT(st.st_mode),
            st.st_size,
            st.st_mtime)


def _do_cmp(f1, f2, sftp_client):
    bufsize = BUFSIZE
    with open(f1, 'rb') as fp1, sftp_client.open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True


def clear_cache():
    """Clear the filecmp cache."""
    _cache.clear()


def cmpolder(local_file, remote_file, sftp_client):
    '''
    Compare two Files to see which is the oldest.

    Arguments:
    local_file -- First file name
    remote_file -- Second file name
    sftp_client -- The Paramiko Object of the SFTP Connection to the Server
    
    Return value:
    True if local_file is the newest, False otherwise.
    '''
    st_local_mtime  = os.stat(local_file).st_mtime
    st_remote_mtime = sftp_client.stat(remote_file).st_mtime
    
    return True if (st_local_mtime > st_remote_mtime) else False


def cmphash(local_file, remote_file, sftp_client):
    '''
    Compare two Files using the MD5 Hash Algorithm
    
    Arguments:
    local_file -- First file name
    remote_file -- Second file name
    sftp_client -- The Paramiko Object of the SFTP Connection to the Server
    
    Return value:
    True if the files are the same, False otherwise.
    '''
    bufsize = BUFSIZE
    
    local_file_hash = hashlib.md5()
    remote_file_hash = hashlib.md5()
    
    # we use the read passing the size of the block to avoid heavy ram usage
    with open(local_file, 'rb') as fp1:
        while True:
            b1 = fp1.read(bufsize)
            # partially calculate the hash                
            local_file_hash.update(b1)
            if not b1: break
    with sftp_client.open(remote_file, 'rb') as fp2:
        while True:
            b2 = fp2.read(bufsize)
            # partially calculate the hash
            remote_file_hash.update(b2)
            if not b2: break
                
    return (local_file_hash.digest() == remote_file_hash.digest())
