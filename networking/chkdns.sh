#!/usr/bin/env bash

if [ $# -ne 1 ]; then
  echo "This script compares the A record and PTR record."
  echo "Usage: ./chkdns.sh lin2dev242"
  exit 1
fi

ARECORD=$(host "$1") || { echo $ARECORD; exit 1; }
ARECORD_HOSTNAME=$(echo $ARECORD | awk '{print $1}')
ARECORD_IPADDR=$(echo $ARECORD | awk '{printf $4}')
PTR=$(host $ARECORD_IPADDR)
PTR_HOSTNAME=$(echo $PTR | awk '{printf $5}')

echo $ARECORD
echo $PTR

if [ $ARECORD_HOSTNAME != ${PTR_HOSTNAME%?} ]; then
  echo "Hostname in A record and PTR record do not match."
  echo $ARECORD_HOSTNAME
  echo $PTR_HOSTNAME
else
  echo "Records match."
fi
