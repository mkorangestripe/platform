#!/usr/bin/env bash

if [ $# -ne 1 ]; then
    echo "This script compares the A record and PTR record of a host."
    echo "Usage 1: ./chkdns.sh lin2dev242"
    echo "Usage 2: ./chkdns.sh hostlist.txt"
    exit 1
fi

get_ptr() {
    ARECORD_HOSTNAME=$(echo "$DNS_RETURN_LINE1" | awk '{print $1}')
    ARECORD_IPADDR=$(echo "$DNS_RETURN_LINE1" | awk '{print $4}')
    PTR=$(host "$ARECORD_IPADDR") || { echo "$PTR"; exit 1; }
    PTR_HOSTNAME=$(echo "$PTR" | awk '{print $5}')

    echo "$PTR"

    PTR_HOSTNAME_PERIOD_STRIPPED=${PTR_HOSTNAME%?}
    if [[ "${ARECORD_HOSTNAME,,}" != "${PTR_HOSTNAME_PERIOD_STRIPPED,,}" ]]; then
        echo "Hostname in A record and PTR record do not match."
        echo "A:   $ARECORD_HOSTNAME"
        echo "PTR: $PTR_HOSTNAME"
    else
        echo "Records match."
    fi
}

get_arecord() {
    PTR_HOSTNAME=$(echo "$DNS_RETURN_LINE1" | awk '{print $5}')
    ARECORD=$(host "$PTR_HOSTNAME") || { echo "$ARECORD"; exit 1; }
    ARECORD_IPADDR=$(echo "$ARECORD" | awk '{print $4}')

    echo "$ARECORD"

    if [[ "$IPADDR" != "$ARECORD_IPADDR" ]]; then
        echo "IP address in PTR and A record do not match."
	echo "PTR:  $IPADDR"
	echo "A:    $ARECORD_IPADDR"
    else
	echo "Records match."
    fi
}

check_dns_records() {
    DNS_RETURN=$(host "$1") || { echo "$DNS_RETURN"; exit 1; }
    DNS_RETURN_LINE1=$(echo "$DNS_RETURN" | head -1)
    RECORD_TYPE=$(echo "$DNS_RETURN_LINE1" | egrep -wo 'address|pointer')

    echo "$DNS_RETURN"

    if [[ "$RECORD_TYPE" == "address" ]]; then
        get_ptr $DNS_RETURN_LINE1
    elif [[ "$RECORD_TYPE" == "pointer" ]]; then
        IPADDR=$1
        get_arecord $DNS_RETURN_LINE1
    fi
}

if [ ! -f "$1" ]; then
    check_dns_records $1
else
    HOSTS=$(cat $1)
    for HOST in $HOSTS; do
        check_dns_records $HOST
        echo
    done
fi