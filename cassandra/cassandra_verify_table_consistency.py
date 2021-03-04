#!/usr/bin/env python
# Verify synchronous table creation in Cassandra on all nodes in the cluster.
# This queries Cassandra until either finding the table in question or being terminated.
# Yes, the queries could be run with the parallel module, but they usually return quickly.
# Gavin Purcell

# This script is run in conjunction with cassandra_create_table_rand_consistency.py
# 1) Run cassandra_create_table_rand_consistency.py to get the random consistency level.
# 2) Run cassandra_verify_table_consistency.py <CONSISTENCY_LEVEL>
# 3) Return to cassandra_create_table_rand_consistency.py to continue with table creation.
# 4) View log file cassandra_verify_table_consistency.log

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
import logging
import json
import time
import signal
import sys
from creds import *
# Put username and password in creds.py

# Because we're querying multiple endpoints, this script should be run...
# from a machine with access to all nodes in the Cassandra cluster.
# cassandra_endpoints=['10.141.18.229', '10.141.18.214', '10.141.18.219'] # stable staging
cassandra_endpoints=['10.141.18.229', '10.141.18.214'] # testing with one node marked down
keyspace = 'Metrics'

# tablename = "storage_account_operations_" + time.strftime('%Y%m')
# tablename = "storage_account_delta_usage_" + time.strftime('%Y%m')

if len(sys.argv) == 1:
  print "Valid arguments are: all, local_quorum, one"
  sys.exit(1)
if str.lower(sys.argv[1]) == 'all':
    tablename = "pbprb_1802_consistency_all_" + time.strftime('%Y%m')
elif str.lower(sys.argv[1]) == 'local_quorum':
    tablename = "pbprb_1802_consistency_local_quorum_" + time.strftime('%Y%m')
elif str.lower(sys.argv[1]) == 'one':
    tablename = "pbprb_1802_consistency_one_" + time.strftime('%Y%m')
else:
    print "Not a valid option"
    sys.exit(1)

query = (
    "SELECT count(*) FROM system_schema.tables "
    "WHERE table_name='" + tablename + "' "
    "ALLOW FILTERING;")

auth_provider = PlainTextAuthProvider(username=username,
                                      password=password)

logging.basicConfig(filename='cassandra_verify_table_consistency.log', level=logging.INFO)

sessions = {'all_rowcount': 0, 'table_consistency': 0, 'first_count_1': ''}

for endpoint in cassandra_endpoints:
    cluster = Cluster([endpoint], auth_provider=auth_provider)
    sessions[endpoint] = {'connection':cluster.connect(),
                          'time':'',
                          'rowcount':0}
    print("Connected to " + endpoint)
    log_line = {'timestamp': time.time(),
    'file': 'cassandra_verify_table_consistency.py',
    'message': "Connected to " + endpoint}
    logging.info(json.dumps(log_line))
    sessions[endpoint]['connection'].set_keyspace(keyspace.lower())

def query_table_creation():
    for endpoint in cassandra_endpoints:
        rows = sessions[endpoint]['connection'].execute(query)
        timestamp = time.time()
        for row in rows:
            if 'Row(count=0)' in str(row):
                sessions[endpoint]['rowcount'] = 0
            elif 'Row(count=1)' in str(row):
                sessions[endpoint]['rowcount'] = 1
                if type(sessions['first_count_1']) != float:
                    sessions['first_count_1'] = timestamp
            sessions[endpoint]['time'] = timestamp
            log_line = {'timestamp': timestamp,
            'file': 'cassandra_verify_table_consistency.py',
            'message': endpoint + ' ' + tablename + ' ' + str(row)} 
            logging.info(json.dumps(log_line))
        sessions['all_rowcount'] += sessions[endpoint]['rowcount']
        if sessions['table_consistency'] == 0:
            if sessions['all_rowcount'] == len(cassandra_endpoints):
                sessions['table_consistency'] = 1
                delta = timestamp - sessions['first_count_1']
                log_line = {'timestamp': timestamp,
                'file': 'cassandra_verify_table_consistency.py',
                'message': 'seconds between last count=0 and table_consistency: ' + str(delta)}
                logging.info(json.dumps(log_line))
                exit_gracefully(None, None)

def exit_gracefully(signal, frame):
    print "\nClosing sessions"
    for endpoint in cassandra_endpoints:
        sessions[endpoint]['connection'].shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
print("Querying for " + tablename)
print("Press Ctrl+C to exit")
while True:
    query_table_creation()
    # time.sleep(1)
    time.sleep(0.1)
