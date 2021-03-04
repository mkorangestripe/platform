#!/usr/bin/env python
## Kill, start, bounce, and show status of Tomcat on app servers.
## Gavin Purcell

## Set these Bash functions for ease of use:
## kll(){ ~/scripts/apptool.py $1 kill; }
## str(){ ~/scripts/apptool.py $1 start; }
## bnc(){ ~/scripts/apptool.py $1 bounce; }
## stt(){ ~/scripts/apptool.py $1 status; }

import paramiko
import socket
import sys
import os

## Local command / remote command lookup.
action_lookup = {
'kill': "'bin/killdrh.sh'",
'start': "'bin/startdrh.sh'",
'bounce': "'bin/killdrh.sh; bin/startdrh.sh'",
'status': "'bin/showstatusdrh.sh'",
'actvck': "'ls -l /DRH/engine/active'"
}

port = 22
user = os.environ['USER']
jsuser = user + "_js"
pkey_file = "" ## FILENAME REMOVED
key = paramiko.DSSKey.from_private_key_file(pkey_file)

def connect_run(user, host, action):
    """Connect and run the command on the host."""
    sudo_cmd = '/opt/jumpstation/sudo/bin/sudo /bin/su - %s -c ' % user
    cmd = sudo_cmd + action_lookup[action]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port, jsuser, pkey=key)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        error_msg = stderr.read()
        print stdout.read()
        if error_msg: print error_msg
    except socket.error as e:
        print 'Cannot connect to %s: %s' % (host, e)
    finally:
        ssh.close()

if __name__ == '__main__':
    description = 'Description: Kill, start, bounce, and show status of Tomcat on app servers.'
    usage = 'Usage: %s HOST ACTION' % sys.argv[0]
    valid_actions = 'Actions: ' + ', '.join(action_lookup.keys())

    ## Check that script is given exactly 2 arguments.
    if len(sys.argv[1:]) != 2:
        print '%s\n%s' % (usage, valid_actions)
        sys.exit(1)

    ## Check if a username is included with the host.
    if '@' in sys.argv[1]:
        ruser = sys.argv[1].split('@')[0]
        host = sys.argv[1].split('@')[1]
    else:
        ruser = 'gcapp01'
        host = sys.argv[1]
    action = sys.argv[2]

    ## Check that action is a valid action.
    if action_lookup.has_key(action) == False:
        print '%s\n%s' % (usage, valid_actions)
        sys.exit(1)

    connect_run(ruser, host, action)