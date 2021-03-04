#!/usr/bin/env python
# Create a Cassandra table with the consistency level chosen at random.
# Gavin Purcell

# This script is run in conjunction with cassandra_verify_table_consistency.py
# 1) Run cassandra_create_table_rand_consistency.py to get the random consistency level.
# 2) Run cassandra_verify_table_consistency.py <CONSISTENCY_LEVEL>
# 3) Return to cassandra_create_table_rand_consistency.py to continue with table creation.
# 4) View log file cassandra_verify_table_consistency.log

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement
import time
import random
from creds import *
# Put username and password in creds.py

# If Cassandra is running remotely, use an ssh tunnel similar to the following.
# ssh -L 9042:10.141.18.229:9042 USER@HOSTNAME -o ServerAliveInterval=60

endpoints = ['127.0.0.1']
keyspace = 'Metrics'

consistencylevels = [ConsistencyLevel.ALL,
                     ConsistencyLevel.LOCAL_QUORUM,
                     ConsistencyLevel.ONE]

consistencylevel = random.choice(consistencylevels)

if consistencylevel == ConsistencyLevel.ALL:
    tablename = "pbprb_1802_consistency_all_" + time.strftime('%Y%m')
if consistencylevel == ConsistencyLevel.LOCAL_QUORUM:
    tablename = "pbprb_1802_consistency_local_quorum_" + time.strftime('%Y%m')
if consistencylevel == ConsistencyLevel.ONE:
    tablename = "pbprb_1802_consistency_one_" + time.strftime('%Y%m')

auth_provider = PlainTextAuthProvider(username=username,
                                      password=password)
cluster = Cluster(endpoints, auth_provider=auth_provider)
session = cluster.connect()
print("Connected to Cassandra")
session.set_keyspace(keyspace.lower())


def create_table(table_name):
    """Create the Cassandra table if it doesn't already exist.

    Complete without errors if the table does already exist.
    """

    delta_usage_table_query = (
        "CREATE TABLE IF NOT EXISTS " + table_name + "("
        "storage_entity_id text,"
        "storage_loc_id text,"
        "storage_class_id text,"
        "timestamp bigint,"
        "bytes_used_active counter,"
        "bytes_used_temp_active counter,"
        "PRIMARY KEY ("
        "storage_entity_id, storage_loc_id, storage_class_id, timestamp)"
        ") WITH CLUSTERING ORDER BY ("
        "storage_loc_id ASC, storage_class_id ASC, timestamp DESC);")

    operations_table_query = SimpleStatement(
        "CREATE TABLE IF NOT EXISTS " + table_name + "("
        "storage_entity_id text,"
        "storage_loc_id text,"
        "storage_class_id text,"
        "timestamp bigint,"
        "copy_count counter,"
        "delete_count counter,"
        "get_count counter,"
        "head_count counter,"
        "list_count counter,"
        "min_filesize_penalty counter,"
        "other_count counter,"
        "post_count counter,"
        "private_bytes_in counter,"
        "private_bytes_out counter,"
        "public_bytes_in counter,"
        "public_bytes_out counter,"
        "put_count counter,"
        "restore_charge_bytes counter,"
        "retention_penalty counter,"
        "retrieval counter,"
        "PRIMARY KEY ("
        "storage_entity_id, storage_loc_id, storage_class_id, timestamp)"
        ") WITH CLUSTERING ORDER BY ("
        "storage_loc_id ASC, storage_class_id ASC, timestamp DESC)",
        consistency_level=consistencylevel)

    if 'storage_account_delta_usage' in table_name:
        query = delta_usage_table_query
    elif 'storage_account_operations' in table_name:
        query = operations_table_query
    else:
         # query = delta_usage_table_query # for testing table creation
         query = operations_table_query # for testing table creation

    session.execute(query)


def drop_table(table_name):
    drop_query = SimpleStatement(
        "DROP TABLE IF EXISTS " + table_name)
    session.execute(drop_query)


if __name__ == '__main__':
    print "Will create table: " + tablename
    raw_input("Press any key to continue: ")
    create_table(tablename)
    print("Table created")
    # raw_input("Press any key to drop table: ")
    time.sleep(2)
    print "Dropping table: " + tablename
    drop_table(tablename)
    print "Closing sessions"
    session.shutdown()
