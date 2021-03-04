#!/usr/bin/env python
## Gavin Purcell
## Gather lists of ESXi hosts by vSphere cluster and output to file.

import urllib2
import base64
import sys
import os
import re
import getpass
import pickle

username = raw_input("Username: ")
username = username.split('@')[0] + '@mpls'
obscure = getpass.getpass()
if len(username) == 0 or len(obscure) == 0:
  print "Either username or password not provided."
  sys.exit(1)

dir_path = os.path.dirname(os.path.abspath(__file__))
hosts_by_cluster_pickle = dir_path + '/hosts_by_cluster.pkl'
hosts_by_cluster_pickle_old = dir_path + '/hosts_by_cluster.pkl.old'

mob_resource = '/mob' ## Managed Object Reference
mob_clusters_resource = "/mob/?moid=group-h23"

vcenters = {
'vc020':'', ## HOSTNAME REMOVED
'vc030':'', ## HOSTNAME REMOVED
'vc090':'' ## HOSTNAME REMOVED
}

class color:
  red = '\033[91m'
  end = '\033[0m'

def establish_vcenter_connection(vcenter):
  """Establish connections to the vcenters and set a cookie."""
  vcenter_mob_url = 'https://' + vcenters[vcenter] + mob_resource
  request = urllib2.Request(vcenter_mob_url)
  base64string = base64.encodestring('%s:%s' % (username, obscure)).replace('\n', '')
  request.add_header("Authorization", "Basic %s" % base64string)
  try:
    result = urllib2.urlopen(request)
  except urllib2.URLError as e:
      print e, vcenter_mob_url
      sys.exit(1)
  except urllib2.HTTPError as e:
      print e, vcenter_mob_url
      sys.exit(1)
  cookie = result.headers.get('Set-Cookie')
  cookies[vcenter] = cookie

def get_html(url, cookie):
  """Get html content."""
  try:
    request = urllib2.Request(url)
    request.add_header('cookie', cookie)
    result = urllib2.urlopen(request)
    html = result.read()
    return html
  except ValueError as e:
    print color.red, e, color.end
    sys.exit(1)
  except (urllib2.URLError, urllib2.HTTPError) as e:
    print color.red, e, url, color.end
    sys.exit(1)

## Establish connections to vcenters.
cookies = {}
for vcenter in vcenters.keys():
  establish_vcenter_connection(vcenter)
  print "Connected to", vcenter

## Get cluster to cluster-domains.
clusters_to_c_domains = []
for vcenter in vcenters.keys():
  vcenter_url = 'https://' + vcenters[vcenter]
  clusters_url = vcenter_url + mob_clusters_resource
  html = get_html(clusters_url, cookies[vcenter])
  match = re.findall('domain-c.+?</a> \(C[0-9][0-9][0-9]-CL[0-9][0-9][0-9]', html)
  for item in match:
    c_domain, cluster = item.split()[0].rstrip('</a>'), item.split()[1].lstrip('(')
    clusters_to_c_domains.append((vcenter, c_domain, cluster))

## For datacenter d010
vcenter = 'vc020'
clusters_url = 'https://' + vcenters[vcenter] + '/mob/?moid=group-h11451'
html = get_html(clusters_url, cookies[vcenter])
match = re.findall('domain-c.+?</a> \(D[0-9][0-9][0-9]-CL[0-9][0-9][0-9]', html)
for item in match:
  c_domain, cluster = item.split()[0].rstrip('</a>'), item.split()[1].lstrip('(')
  clusters_to_c_domains.append((vcenter, c_domain, cluster))

## For datacenter c035
vcenter = 'vc030'
clusters_url = 'https://' + vcenters[vcenter] + '/mob/?moid=group-h9465'
html = get_html(clusters_url, cookies[vcenter])
match = re.findall('domain-c.+?</a> \(C[0-9][0-9][0-9]-CL[0-9][0-9][0-9]', html)
for item in match:
  c_domain, cluster = item.split()[0].rstrip('</a>'), item.split()[1].lstrip('(')
  clusters_to_c_domains.append((vcenter, c_domain, cluster))

## Get hosts by cluster:
hosts_by_cluster = {}
for cluster in clusters_to_c_domains:
  vcenter, c_domain, cluster = cluster[0], cluster[1], cluster[2]
  hosts_url = 'https://' + vcenters[vcenter] + '/mob/?moid=' + c_domain
  html = get_html(hosts_url, cookies[vcenter])
  hosts = re.findall('n...\.....\.digitalriverws.net', html)
  hosts_by_cluster[cluster] = hosts

## Backup the hosts_by_cluster file.
if os.path.exists(hosts_by_cluster_pickle):
  os.rename(hosts_by_cluster_pickle, hosts_by_cluster_pickle_old)

## Write out hosts_by_cluster.
with open(hosts_by_cluster_pickle, 'w') as pickle_file:
  pickle.dump(hosts_by_cluster, pickle_file)