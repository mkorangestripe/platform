#!/usr/bin/env python
## Gavin Purcell
## Determine which ordertakers (databases) are using which vSphere clusters
## based on the numbers of appservers (VMs) residing on each cluster.

import paramiko
import socket
import sys
import os
import base64
from multiprocessing import Process, Queue
import resource
import urllib2
from collections import Counter
from datetime import date
import pickle
from shutil import copyfile

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'
hosts_by_cluster_pickle = dir_path + 'hosts_by_cluster.pkl'
html_head_file = dir_path + 'html_head.txt'

gccmdb_url = '' ## HOSTNAME REMOVED
gccmdb_databases_url = gccmdb_url + '/ccon/database/showall'
gccmdb_database_info_url = gccmdb_url + '/ccon/database/info/'
gccmdb_database_hosts_url = gccmdb_url + '/ccon/database/hosts/'

port = 22
user = 'root'
password = base64.b64decode('') ## PASSWORD REMOVED
get_vms = 'esxcli vm process list | grep "Display Name" | awk \'{print $3}\''

html_title_placeholder = 'title not set'
html_title = 'Ordertaker Landscape'
html_colors = ['#cce6ff', '#ffddcc', '#e6ccff', '#ffffcc']
webpage_dir = '/var/www/html/'
favicon_file_name = 'cloudopsvcli_icon.png'
favicon_file = webpage_dir + favicon_file_name
html_file_name = 'otlandscape'
html_file = webpage_dir + html_file_name
csv_file_name = 'ot_landscape.csv'
csv_file = webpage_dir + csv_file_name

class color:
  red = '\033[91m'
  end = '\033[0m'

## Check that the hosts_by_cluster_pickle file exists.
if os.path.exists(hosts_by_cluster_pickle) == False:
  print hosts_by_cluster_pickle,  "does not exist."
  sys.exit(1)

## Output files to local directory if webpage_dir doesn't exist.
if os.path.exists(webpage_dir) == False:
  print webpage_dir, 'does not exist. Outputting to local directory.'
  csv_file = dir_path + csv_file_name
  html_file = dir_path + html_file_name

## Set the ulimit to 2048
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (2048, hard))

def get_html(url):
  """Get html."""
  try:
    result = urllib2.urlopen(url)
    return result.read()
  except ValueError as e:
    print color.red, e, color.end
    sys.exit(1)
  except (urllib2.URLError, urllib2.HTTPError) as e:
    print color.red, e, url, color.end
    sys.exit(1)

def clean_html(html):
  """Remove comments and trailing newline characters."""
  html_split = html.rstrip().split('\n')
  for i,v in enumerate(html_split):
    if v.startswith('#'): del html_split[i]
  return html_split

def ssh_run_cmd(q, user, host, cmd):
    """Connect and run the command on the host."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port, user, password, timeout=3)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        error_msg = stderr.read()
        vms_on_host = stdout.read().split()
        q.put(vms_on_host)
        if error_msg: print error_msg
    except (socket.error, paramiko.ssh_exception.BadAuthenticationType, paramiko.ssh_exception.SSHException) as e:
        print '%sCannot connect to %s: %s%s' % (color.red, host, e, color.end)
        q.put('')
    finally:
        ssh.close()

## Get ordertakers from the gccmdb:
databases_html = get_html(gccmdb_databases_url)
ordertakers = clean_html(databases_html)
if len(ordertakers) == 0:
  print "No ordertakers returned from the gccmdb."
  sys.exit(1)

## Get ordertaker hostnames from the gccmdb:
ordertakers_to_hostnames = {}
for ordertaker in ordertakers:
  database_info_url = gccmdb_database_info_url + ordertaker
  database_info_html = get_html(database_info_url)
  html_split = clean_html(database_info_html)
  hostname = '.'.join(html_split[0].split(',')[3].split('.')[0:2])
  ordertakers_to_hostnames[ordertaker] = hostname

## Get appservers by ordertaker:
appservers_by_ordertaker = {}
for ordertaker in ordertakers:
  database_hosts_url = gccmdb_database_hosts_url + ordertaker
  database_hosts_html = get_html(database_hosts_url)
  html_split = clean_html(database_hosts_html)
  appservers_by_ordertaker[ordertaker] = [line.split(',')[0] for line in html_split]

## Get hosts by cluster:
hosts_by_cluster = {}
with open(hosts_by_cluster_pickle, 'r') as pickle_file:
  hosts_by_cluster = pickle.load(pickle_file)

## Create and start processes for getting vms by cluster in parallel.
jobs = []
vms_by_cluster = {}
for cluster in hosts_by_cluster.keys():
    vms_by_cluster[cluster] = []
    for host in hosts_by_cluster[cluster]:
      q = Queue()
      process = Process(target=ssh_run_cmd, args=(q,user,host,get_vms))
      jobs.append((process,q,cluster,host))
      process.start()

## Wait for the processes to finish and append to the lists of vm's.
for job in jobs:
  process,q,cluster,host = job[0],job[1],job[2],job[3]
  print "Waiting for:", cluster, host
  vms_on_host = q.get()
  process.join()
  vms_by_cluster[cluster].extend(vms_on_host)

## Get clusters by ordertaker
clusters_by_ordertakers = {}
for ordertaker in ordertakers:
  clusters_by_ordertakers[ordertaker] = []
  for appserver in appservers_by_ordertaker[ordertaker]:
    for cluster in vms_by_cluster.keys():
      if appserver.split('.')[0] in vms_by_cluster[cluster]:
        clusters_by_ordertakers[ordertaker].append(cluster)

## Get the count of appservers in each cluster by ordertaker.
cluster_counts_by_ordertaker = {}
for ordertaker in ordertakers:
  counted_clusters = Counter(clusters_by_ordertakers[ordertaker])
  cluster_counts_by_ordertaker[ordertaker] = counted_clusters.items()

## Create a table. Note - this throughs out ordertakers with no appservers:
table_header = ['Host','Ordertaker','Cluster','AppserverCount']
table = []
for ordertaker in ordertakers:
  for cluster_count in cluster_counts_by_ordertaker[ordertaker]:
    hostname, cluster, appserver_count = ordertakers_to_hostnames[ordertaker], cluster_count[0], cluster_count[1]
    table.append([hostname, ordertaker, cluster, appserver_count])

## Map html colors to ordertaker.
ordertaker_colors = {}
cnt_max = len(html_colors)
cnt = 0
for row in table:
  ordertaker = row[1]
  if ordertaker not in ordertaker_colors:
    ordertaker_colors[ordertaker] = html_colors[cnt]
    cnt += 1
    if cnt == cnt_max: cnt = 0

## Write out csv file.
with open(csv_file, 'w') as out_file:
  table_csv = [table_header] + table
  for row in table_csv:
    hostname, ordertaker, cluster, appserver_count = row
    line = '%s,%s,%s,%s\n' % (hostname, ordertaker, cluster, appserver_count)
    out_file.write(line)

## Check that the html_head file exists:
if os.path.exists(html_head_file) == False:
  print html_head_file, "does not exist."
  sys.exit(2)

## Read in the html head file and set the title.
with open(html_head_file, 'r') as in_file:
  html = in_file.read()
html = html.replace(html_title_placeholder, html_title, 1)

## Create the html for output.
date = str(date.today())
html = html + '<body>\n\n'
html = html + '<table>\n'
hostname, ordertaker, cluster, appserver_count = table_header
html = html + '<tr>\n'
html = html + '<th>' + hostname + '</th>\n'
html = html + '<th>' + ordertaker + '</th>\n'
html = html + '<th>' + cluster + '</th>\n'
html = html + '<th>' + appserver_count + '</th>\n'
html = html + '</tr>\n'
for row in table:
  hostname, ordertaker, cluster, appserver_count = row
  html = html + '<tr bgcolor="' + ordertaker_colors[ordertaker] + '">\n'
  html = html + '<td>' + hostname + '</td>\n'
  html = html + '<td>' + ordertaker + '</td>\n'
  html = html + '<td>' + cluster + '</td>\n'
  html = html + '<td>' + str(appserver_count) + '</td>\n'
  html = html + '</tr>\n'
html = html + '</table>\n\n'
html = html + '<br>\n'
html = html + '<a href="' + csv_file_name + '">' + csv_file_name + '</a>\n'
html = html + '<br>\n'
html = html + '<p>' + 'Last updated ' + date + '</p>\n'
html = html + '</body>\n'
html = html + '</html>'

## Check that the favicon file exists and copy it to the web page directory:
if os.path.exists(favicon_file_name) == False:
  print favicon_file_name, "does not exist."
else:
  copyfile(favicon_file_name, favicon_file)

## Write out html file.
with open(html_file, 'w') as out_file:
  out_file.write(html)