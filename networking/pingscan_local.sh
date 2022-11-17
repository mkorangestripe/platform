#!/usr/bin/env bash

# Useful symlinks and aliases:
# cd ~/.local/bin
# ln -s ~/src/mkorangestripe/devops/networking/pingscan.py pingscan
# ln -s ~/src/mkorangestripe/devops/networking/pingscan_local.sh pingscan_local
# alias pingscan-27="pingscan_local 27"
# alias pingscan-24="pingscan_local 24"

if [ $# -ne 1 ]; then
    echo "Pingscan the local Class C network with pingscan.py"
    echo "This determines the third octet every time, useful when moving locations."
    echo "Example using local files: ./pingscan_local.py 27"
    echo "Example using symlinks in path: pingscan_local 27"
    exit 1
fi

# Assuming only one Class C address:
if command -v ip > /dev/null; then
    THIRD_OCTET=$(ip addr | grep "inet 192" | awk -F. '{print $3}')
else
    THIRD_OCTET=$(ifconfig | grep "inet 192" | awk -F. '{print $3}')
fi

LOCAL='false'
test -x pingscan.py && LOCAL='true'

if [ $1 == 27 ]; then
    if [ $LOCAL == 'true' ]; then
        ./pingscan.py -w 2 -c 192.168.$THIRD_OCTET.0/27
    else
        pingscan -w 2 -c 192.168.$THIRD_OCTET.0/27
    fi
elif [ $1 == 24 ]; then
    if [ $LOCAL == 'true' ]; then
        ./pingscan.py -w 2 -c 192.168.$THIRD_OCTET.0/24
    else
        pingscan -w 2 -c 192.168.$THIRD_OCTET.0/24
    fi
fi
