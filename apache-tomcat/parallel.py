#!/usr/bin/env python
## Gavin Purcell
## With multiple databases, start/restart appservers in parallel, but only one appserver per database at a time.
## Basically, the appservers pool lists are gathered from a cmdb, the lists are transposed, and the start/restart commands are run.

from optparse import OptionParser
import sys
import os
import urllib2
import re
import subprocess
import time
import string

gccmdb = '' ## URL REMOVED
gccmdb_showall = gccmdb + '/ccon/objects/showall'
script_path = os.path.dirname(os.path.abspath(__file__))
cmd = "%s/apptool.py" % (script_path)
actvck_hostlist = [] ## HOSTNAMES REMOVED

class color:
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    end = '\033[0m'

def query_gccmdb(query):
    """Queries the gccmdb and returns the results."""
    try:
        query_results = urllib2.urlopen(query)
        return query_results
    except urllib2.URLError as e:
        print e, query
        sys.exit(1)
    except urllib2.HTTPError as e:
        print e, query
        sys.exit(1)

def get_pools():
    """Returns a dictionary of pools with empty lists."""
    query = '%s/ccon/%s/%s/%s/%s/%s' % (gccmdb, 'pools', options.stage, options.group, options.datacenter, options.tier)
    query_results = query_gccmdb(query)
    pools = {}
    for line in query_results.readlines():
        match = re.search('c[0-9][0-9][0-9]', line)
        if match:
            pools[line.strip().split(',')[0]] = []
    return pools

def get_pool_members(pool):
    """Takes a pool name and returns the list of members."""
    query = '%s/ccon/%s/%s/%s/%s/%s/%s' % (gccmdb, 'instances', options.stage, options.group, options.datacenter, options.tier, pool)
    query_results = query_gccmdb(query)
    pool_members = []
    for line in query_results.readlines():
        match = re.search('c[0-9][0-9][0-9]', line)
        if match:
            pool_members.append('@'.join(line.strip().split(',')))
    return pool_members

def transpose_pools(pools):
    """
    Takes a dictionary of lists and returns a tuple with
    a transposed list of lists of hosts, and
    a list of lists of corresponding pools names.
    """
    ## Find which pool is the longest.
    longest_pool_len = 0
    for pool in pools:
        if len(pools[pool]) > longest_pool_len:
            longest_pool_len = len(pools[pool])

    transposed_pools = [[] for x in range(longest_pool_len)]
    remaining_pools = [[] for x in range(longest_pool_len)]

    ## Transpose and append the members to the transposed_pools lists.
    for pool in pools:
        for member_i in range(len(pools[pool])):
            #print member_i, pools[pool][member_i] #testing
            transposed_pools[member_i].append(pools[pool][member_i])
            remaining_pools[member_i].append(pool)

    return (transposed_pools, remaining_pools)

def run_cmd(host):
    """Takes a hostname, runs a command and captures the stdout."""
    print time.asctime(), "Working on", host
    rcmd = '%s %s %s' % (cmd, host, options.action)
    return subprocess.Popen(rcmd, shell=True, stdout=subprocess.PIPE)

def run_groups(transposed):
    """Takes a tuple of two lists, the transposed pools and remaining pools.
       Calls run_cmd() with groups of transposed pools,
       waits for the stdout and prints it.
    """
    transposed_pools = transposed[0]
    remaining_pools = transposed[1]
    z = [[] for x in transposed_pools]
    last_group_i = len(remaining_pools) - 1
    for group_i in range(len(transposed_pools)):
        for host in transposed_pools[group_i]:
            p = run_cmd(host)
            z[group_i].append((p, host))
        print
        for p, host in z[group_i]:
            print time.asctime(), "Waiting for", host
            p.wait()
            print time.asctime(), host, "Returned:"
            for line in p.stdout.readlines():
                print line.strip('\n')
        if group_i != last_group_i:
            print 'Remaining pools:\n%s\n' % str(remaining_pools[group_i + 1])
            print '%sSleeping for %s seconds...\n%s' % (color.green, options.sleep, color.end)
            time.sleep(options.sleep)

if __name__ == "__main__":

    ## This parses the command line options/arguments.
    parser = OptionParser(description='Kill, start, bounce, and show status of Tomcat on app servers in parallel.  One appserver per pool at a time.', prog=sys.argv[0], usage='%prog [OPTIONS]')
    parser.add_option('-s', '--stage', default='any')
    parser.add_option('-g', '--group', default='any')
    parser.add_option('-d', '--datacenter', default='any')
    parser.add_option('-t', '--tier', default='any')
    parser.add_option('-a', '--action', default=None, help='kill, start, bounce, status')
    parser.add_option('-S', '--sleep', default=300, type='float', help='the sleep time between actions')
    (options, arguments) = parser.parse_args()

    ## If run without arguments, print help and 'gccmdb showall' text.
    if not sys.argv[1:]:
        parser.print_help()
        print '\n############################################################\n'
        print query_gccmdb(gccmdb_showall).read()
        sys.exit()

    ## If any additional arguments are given, exit with the message below.
    if arguments:
        print 'Invalid argument(s): ' + ' '.join([x for x in arguments])
        sys.exit(1)

    ## Check which prd environment is active, exit if active prd will be killed, warn if active prd will be bounced.
    if options.stage == 'prd' or options.stage == 'any':
        if options.action == 'kill' or options.action == 'bounce':
            actvck_host = actvck_hostlist[3]
            print "Connecting to %s to check which environment is active..." % actvck_host
            ls_list = []
            rcmd = '%s %s %s' % (cmd, actvck_host, 'actvck')
            p = subprocess.Popen(rcmd, shell=True, stdout=subprocess.PIPE)
            p.wait()
            for line in p.stdout.readlines():
                for item in line.split():
                    ls_list.append(item)
            if ls_list[-1] != 'E1' and ls_list[-1] != 'E2':
                print "Cannot determine which environment is active.  Exiting now."
                sys.exit(0)
            active_prd_env = ls_list[-1]
            print "The active production environment is %s\n" % active_prd_env
            if string.upper(options.group) == active_prd_env or options.group == 'any':
                if options.action == 'kill':
                    print "You are trying to kill the ACTIVE PRODUCTION ENVIRONMENT.\nYou don't want to do this.  Exiting now."
                    sys.exit(0)
                if options.action == 'bounce':
                    print "You are trying to bounce the ACTIVE PRODUCTION ENVIRONMENT.\nSleeping for 5 seconds...\nTo exit press Ctrl + c"
                    time.sleep(5)

    ## This runs everything as requested.
    print color.green + 'Getting pools...' + color.end
    pools = get_pools()
    print '%s\n' % pools
    print color.green + 'Getting pool members...' + color.end
    for pool in pools:
        pools[pool] = get_pool_members(pool)
    print '%s\n' % pools
    print color.green + 'Transposing pools...' + color.end
    transposed = transpose_pools(pools)
    print '%s\n' % transposed[0]
    print '%s\n' % transposed[1]
    if options.action == None:
        sys.exit()
    print color.green + 'Running groups in parallel...\n' + color.end
    run_groups(transposed)