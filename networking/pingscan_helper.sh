#!/usr/bin/env bash
# Helper script for pingscan.py
# Evaluate the third octet with each execution.

# Required symlinks:
# cd ~/.local/bin
# ln -s ~/src/mkorangestripe/devops/networking/pingscan.py pingscan
# ln -s ~/src/mkorangestripe/devops/networking/pingscan_helper.sh pingscan_helper

# Useful aliases:
# zsh also allows pingscan/27 and pingscan/24
# alias pingscan-27="pingscan_helper 27"
# alias pingscan-24="pingscan_helper 24"

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
