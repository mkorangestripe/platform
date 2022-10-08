#!/usr/bin/env bash

# Required symlinks:
# cd ~/.local/bin
# ln -s ~/src/mkorangestripe/devops/networking/pingscan.py pingscan
# ln -s ~/src/mkorangestripe/devops/networking/pingscan_helper.sh pingscan_helper

if [ $# -ne 1 ]; then
    echo "Helper script for pingscan.py"
    echo "Evaluate the third octet with each execution."
    echo "Example: pingscan_helper 27"
    exit 1
fi

# Assuming only one Class C address:
if command -v ip > /dev/null; then
    THIRD_OCTET=$(ip addr | grep "inet 192" | awk -F. '{print $3}')
else
    THIRD_OCTET=$(ifconfig | grep "inet 192" | awk -F. '{print $3}')
fi

if [ $1 == 27 ]; then
    pingscan -w 2 -c 192.168.$THIRD_OCTET.0/27
fi

if [ $1 == 24 ]; then
    pingscan -w 2 -c 192.168.$THIRD_OCTET.0/24
fi
