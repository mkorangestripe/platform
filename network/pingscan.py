#!/usr/bin/env python3
# Gavin Purcell

# Useful alias examples:
# Create a symlink in ~/.bin from pingscan to pingscan.py
# alias pingscan24='pingscan -w 2 -c 192.168.0.0/24'
# alias pingscan27='pingscan -w 2 -c 192.168.0.0/27'

"""
Scan a network by pinging a CIDR range in parallel.
CIDR notation examples:
192.168.0.0/28
10.0.0.0/28
"""

import sys
import subprocess
import ipaddress
from argparse import ArgumentParser


class Color:
    green = '\033[92m'
    red = '\033[91m'
    end = '\033[0m'


class PingScan(object):

    def __init__(self, net_address):
        self.net_address = net_address

    def generate_ip_addrs(self):
        """Generate the list of IP addresses to ping."""
        try:
            ip_net = ipaddress.ip_network(self.net_address)
        except ValueError as e:
            print(e)
            sys.exit(1)
        self.ip_list = list(ip_net.hosts())

    def run_ping_cmd(self, ip):
        """Run the ping command."""
        ping_cmd = 'ping -w %s %s' % (args.deadline, ip)
        return subprocess.Popen(ping_cmd,
                                shell=True,
                                stdout=subprocess.PIPE)

    def create_ping_processes(self):
        """Create a ping subprocesses per IP address."""
        self.jobs = []
        self.response_by_ip = {}
        print('Starting ping of', self.net_address)
        for ip in self.ip_list:
            ip = str(ip)
            self.response_by_ip[ip] = ''
            ping_process = self.run_ping_cmd(ip)
            self.jobs.append((ping_process, ip))

    def get_return_code_response(self):
        """Wait for the ping subprocesses to finish and get the return code and response."""
        for job in self.jobs:
            process, ip = job[0], job[1]
            process.wait()
            return_code = process.returncode
            response = process.stdout.readlines()
            self.response_by_ip[ip] = (return_code, response)

    def print_ip_group(self, requested_return_code):
        """Print group of IPs, either up or down."""
        for ip in self.ip_list:
            ip = str(ip)
            ret_code = self.response_by_ip[ip][0]
            if ret_code == requested_return_code:
                print(ip)
        print()

    def print_ips_state(self):
        """Print all IPs in CIDR range with up/down state."""
        for ip in self.ip_list:
            ip = str(ip)
            ret_code = self.response_by_ip[ip][0]
            if ret_code == 0:
                print('%s is %sup%s' % (ip, Color.green, Color.end))
            else:
                print('%s is %sdown%s' % (ip, Color.red, Color.end))
        print()

    def print_stdout(self):
        """Print stdout if verbose argument is given."""
        for ip in self.ip_list:
            ip = str(ip)
            print(ip)
            stdout = self.response_by_ip[ip][1]
            for line in stdout:
                print(line.strip().decode('utf-8'))
            print()


def _get_argparser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-i', '--infile',
                        help="Input file. Expects subnets in CIDR notation.")
    parser.add_argument('-c', '--cidr',
                        help="Scan a CIDR range i.e. 10.0.0.0/24 which would scan address range 10.0.0.0 - 10.0.0.255")
    parser.add_argument('-w', '--deadline', type=int, default=5,
                        help='Specify a timeout, in seconds, before ping exits.')
    parser.add_argument('-u', '--up', action='store_true', help='Only output hosts that are up.')
    parser.add_argument('-d', '--down', action='store_true', help='Only output hosts that are down.')
    args = parser.parse_args()
    if args.up is True and args.down is True:
        print("Arguments 'up' and 'down' should not be used together.")
        sys.exit(1)
    if args.infile is not None and args.cidr is not None:
        print("Arguments 'infile' and 'cidr' should not be used together.")
        sys.exit(1)
    if args.infile is None and args.cidr is None:
        print("Either 'infile' or 'cidr' is required.")
        sys.exit(1)
    return args


if __name__ == '__main__':

    args = _get_argparser()

    if args.infile is not None:
        with open(args.infile) as infile:
            cidr_list = infile.read().split()
    elif args.cidr is not None:
        cidr_list = [args.cidr]

    for net_addr in cidr_list:
        ping_scan = PingScan(net_addr)
        ping_scan.generate_ip_addrs()
        ping_scan.create_ping_processes()
        ping_scan.get_return_code_response()

        if args.up is True:
            print('The following hosts are up.\n')
            ping_scan.print_ip_group(0)
        elif args.down is True:
            print('The following hosts are down.\n')
            ping_scan.print_ip_group(1)
        else:
            print()
            ping_scan.print_ips_state()

        if args.verbose is True:
            print()
            ping_scan.print_stdout()
