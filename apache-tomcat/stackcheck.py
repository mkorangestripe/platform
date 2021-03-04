#!/usr/bin/env python
## Get the HTTP response status codes of the dr-status and db_xs pages.
## Gavin Purcell

import sys
import socket
import httplib
from multiprocessing import Process

description = 'Get the HTTP status codes of the dr-status and db_xs pages.'
usage1 = 'Usage 1: %s HOST' % sys.argv[0]
usage2 = 'Usage 2: HOSTLIST | %s' % sys.argv[0]
usage_host = 'HOST can be hostname or IP addr of app or che server.'

stack = ['Tomcat', 'Apache', 'Varnish'] ## This will set the order of checking.
resource_drstatus = '/dr-status'
resource_dbxs = '/DRHM/dajsp/util/test/db_xs.jsp'

def get_hostnames(host):
    """Check that the given hostname or IP address is valid and determine the app and cache hostnames"""
    try:
        fqdn = socket.gethostbyaddr(host)[0]
    except socket.error, e:
        print 'Not a valid IP or hostname: %s' % host
        return 'invalid'
    app_hostname = 'app'.join(fqdn.split('che')) ## Set app address if che address is given to script.
    che_hostname = 'che'.join(fqdn.split('app')) ## Set che address if app address is given to script.
    return [fqdn,app_hostname,che_hostname]

def get_stack(hostnames):
    """Return a dictionary mapping applications to hostnames and ports."""
    hostname, app_hostname, che_hostname = hostnames[0],hostnames[1],hostnames[2]
    stack_lookup = {'Varnish': (che_hostname, 1025), 'Apache': (app_hostname, 7775), 'Tomcat': (app_hostname, 57425)}
    return stack_lookup

def get_http(stack_lookup, app, resource):
    """Conect and get the HTTP response status codes."""
    hostname, port = stack_lookup[app][0], stack_lookup[app][1]
    try:
        conn = httplib.HTTPConnection(hostname, port, timeout=8)
        conn.request('HEAD', resource)
        response = conn.getresponse()
        print '%s  %s status code: %s %s' % ('.'.join(hostname.split('.')[:2]), app, response.status, response.reason)
    except socket.error, e:
        print '%s  %s: %s' % ('.'.join(hostname.split('.')[:2]), app, e)
    finally:
        conn.close()

## If input is from command line arguments, do the following.
if sys.stdin.isatty():

    ## Run script with 0 arguments to get useful info.
    if len(sys.argv) == 1:
        print '%s\n%s\n%s\n%s' % (description, usage1, usage2, usage_host)
        sys.exit(1)

    ## Check all health pages of one host.
    hostnames = get_hostnames(sys.argv[1])
    if hostnames != 'invalid':
        stack_lookup = get_stack(hostnames)
        if 'gcadm' in hostnames[0] or 'gcutl' in hostnames[0] or 'gcwse' in hostnames[0]:  ##These have no Varnish hosts.
            print '  Checking dr-status pages...'
            get_http(stack_lookup, stack[1], resource_drstatus)
            print '  Checking db_xs pages...'
            for app in stack[:2]:
                get_http(stack_lookup, app, resource_dbxs)
            sys.exit(0)
        print '  Checking dr-status pages...'
        for app in stack[1:]:
            get_http(stack_lookup, app, resource_drstatus)
        print '  Checking db_xs pages...'
        for app in stack:
            get_http(stack_lookup, app, resource_dbxs)
    sys.exit(0)

## If input is from stdin, do the following.
hosts = []
for line in sys.stdin.readlines():
    if '#' not in line:
        hosts.append(line.strip())

## Check the Varnish or Apache health pages of multiple hosts in parallel.
for host in hosts:
    hostnames = get_hostnames(host)
    if hostnames != 'invalid':
        stack_lookup = get_stack(hostnames)
        if 'gcadm' in hostnames[0] or 'gcutl' in hostnames[0] or 'gcwse' in hostnames[0]:
            status = Process(target=get_http, args=(stack_lookup, 'Apache', resource_dbxs))
            status.start()
        ##status.join()  ## For testing execution time.
        else:
            status = Process(target=get_http, args=(stack_lookup, 'Varnish', resource_dbxs))
            status.start()
        ##status.join()  ## For testing execution time.