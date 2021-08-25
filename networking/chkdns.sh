#!/usr/bin/env bash

if [ $# -ne 1 ]; then
    echo "This script compares the A record and PTR record."
    echo "Usage: ./chkdns.sh lin2dev242"
    exit 1
fi

get_ptr() {
    ARECORD_HOSTNAME=$(echo "$DNS_RETURN_LINE1" | awk '{print $1}')
    ARECORD_IPADDR=$(echo "$DNS_RETURN_LINE1" | awk '{print $4}')
    PTR=$(host "$ARECORD_IPADDR") || { echo "$PTR"; exit 1; }
    PTR_HOSTNAME=$(echo "$PTR" | awk '{print $5}')

    echo "$PTR"

    if [[ "$ARECORD_HOSTNAME" != "${PTR_HOSTNAME%?}" ]]; then
        echo "Hostname in A record and PTR record do not match."
        echo "$ARECORD_HOSTNAME"
        echo "$PTR_HOSTNAME"
    else
        echo "Records match."
    fi
}

get_arecord() {
    PTR_HOSTNAME=$(echo "$DNS_RETURN_LINE1" | awk '{printf $5}')
    ARECORD=$(host "$PTR_HOSTNAME") || { echo "$ARECORD"; exit 1; }
    ARECORD_IPADDR=$(echo "$ARECORD" | awk '{print $4}')

    echo "$ARECORD"

    if [[ "$IPADDR" != "$ARECORD_IPADDR" ]]; then
        echo "IP address in PTR and A record do not match."
	echo "$IPADDR"
	echo "$ARECORD_IPADDR"
    else
	echo "Records match."
    fi
}

DNS_RETURN=$(host "$1") || { echo "$DNS_RETURN"; exit 1; }
DNS_RETURN_LINE1=$(echo "$DNS_RETURN" | head -1)
RECORD_TYPE=$(echo "$DNS_RETURN_LINE1" | egrep -wo 'address|pointer')

echo "$DNS_RETURN"

if [[ "$RECORD_TYPE" == "address" ]]; then
    get_ptr
elif [[ "$RECORD_TYPE" == "pointer" ]]; then
    IPADDR=$1
    get_arecord
fi
