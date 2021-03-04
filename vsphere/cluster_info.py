#!/usr/bin/env python
## Gavin Purcell
## Gather system resource info from VMware ESXi hosts and create totals by vSphere cluster.

import paramiko
import socket
import sys
import os
import base64
from multiprocessing import Process, Queue
import resource
from datetime import date
import pickle
from shutil import copyfile

dir_path = os.path.dirname(os.path.abspath(__file__)) + '/'
hosts_by_cluster_pickle = dir_path + 'hosts_by_cluster.pkl'
html_head_file = dir_path + 'html_head.txt'

port = 22
user = 'root'
password = base64.b64decode('') ## PASSWORD REMOVED
get_sysinfo = 'timeout -t 3 esxcli hardware cpu global get | grep CPU | awk \'{print $3}\'; timeout -t 3 esxcli hardware memory get | grep "Physical Memory" | awk \'{print $3}\''
expected_itmes_returned = 4

html_title_placeholder = 'title not set'
html_title = 'Vsphere Cluster Info'
html_colors = ['#ffddcc', '#e6ccff', '#ffffcc', '#cce6ff']
webpage_dir = '/var/www/html/'
favicon_file_name = 'cloudopsvcli_icon.png'
favicon_file = webpage_dir + favicon_file_name
html_file_name = 'cluster_info'
html_file = webpage_dir + html_file_name
csv_file_name = 'cluster_info.csv'
csv_file = webpage_dir + csv_file_name

class color:
  red = '\033[91m'
  end = '\033[0m'

## For converting from bytes to gigabytes.
gigabyte_divisor = 1073741824

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

## Get hosts by cluster:
hosts_by_cluster = {}
with open(hosts_by_cluster_pickle, 'r') as pickle_file:
  hosts_by_cluster = pickle.load(pickle_file)

## Create and start processes for getting sysinfo by cluster in parallel.
jobs = []
sysinfo_by_host = {}
for cluster in hosts_by_cluster.keys():
    for host in hosts_by_cluster[cluster]:
      sysinfo_by_host[host] = []
      q = Queue()
      process = Process(target=ssh_run_cmd, args=(q,user,host,get_sysinfo))
      jobs.append((process,q,cluster,host))
      process.start()

## Wait for the processes to finish and append to the lists of vm's.
for job in jobs:
  process,q,cluster,host = job[0],job[1],job[2],job[3]
  print "Waiting for:", cluster, host
  sysinfo = q.get()
  process.join()
  sysinfo_by_host[host].extend(sysinfo)

## Create a table of clusters.
table_header = ['Cluster','Hosts(up)','Sockets','Cores','Threads','Memory(gigibytes)', 'Hosts(down)']
table = []

for cluster in hosts_by_cluster.keys():
  host_cnt,socket_cnt,core_cnt,thread_cnt,memory_cnt,host_down_cnt = [0,0,0,0,0,0]
  for host in hosts_by_cluster[cluster]:
    if len(sysinfo_by_host[host]) >= expected_itmes_returned: ## Some hosts are down and don't return anyting.
      sockets,cores,threads,memory = sysinfo_by_host[host]
      host_cnt += 1
      socket_cnt += int(sockets)
      core_cnt += int(cores)
      thread_cnt += int(threads)
      memory_cnt += int(round(float(memory) / gigabyte_divisor))
    else:
      host_down_cnt += 1
  table.append([cluster,host_cnt,socket_cnt,core_cnt,thread_cnt,memory_cnt,host_down_cnt])

table.sort()

## Map html colors to clusters.
cluster_colors = {}
for row in table:
  cluster = row[0]
  cluster_colors[cluster] = html_colors[0]
  if 'C02' in cluster:
    cluster_colors[cluster] = html_colors[1]
  if 'C03' in cluster:
    cluster_colors[cluster] = html_colors[2]
  if 'C09' in cluster:
    cluster_colors[cluster] = html_colors[3]

## Write out csv file.
with open(csv_file, 'w') as out_file:
  table_csv = [table_header] + table
  for row in table_csv:
    cluster,host_cnt,socket_cnt,core_cnt,thread_cnt,memory_cnt,host_down_cnt = row
    line = '%s,%s,%s,%s,%s,%s,%s\n' % (cluster,host_cnt,socket_cnt,core_cnt,thread_cnt,memory_cnt,host_down_cnt)
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
cluster,host_cnt,socket_cnt,core_cnt,thread_cnt,memory_cnt,host_down_cnt = table_header
html = html + '<tr>\n'
html = html + '<th>' + cluster + '</th>\n'
html = html + '<th>' + host_cnt + '</th>\n'
html = html + '<th>' + socket_cnt + '</th>\n'
html = html + '<th>' + core_cnt + '</th>\n'
html = html + '<th>' + thread_cnt + '</th>\n'
html = html + '<th>' + memory_cnt + '</th>\n'
html = html + '<th>' + host_down_cnt + '</th>\n'
html = html + '</tr>\n'
for row in table:
  cluster,host_cnt,socket_cnt,core_cnt,thread_cnt,memory_cnt,host_down_cnt = row
  html = html + '<tr bgcolor="' + cluster_colors[cluster] + '">\n'
  html = html + '<td>' + cluster + '</td>\n'
  html = html + '<td>' + str(host_cnt) + '</td>\n'
  html = html + '<td>' + str(socket_cnt) + '</td>\n'
  html = html + '<td>' + str(core_cnt) + '</td>\n'
  html = html + '<td>' + str(thread_cnt) + '</td>\n'
  html = html + '<td>' + str(memory_cnt) + '</td>\n'
  html = html + '<td>' + str(host_down_cnt) + '</td>\n'
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