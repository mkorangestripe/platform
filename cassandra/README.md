# Cassandra Scripts

1. Run cassandra_create_table_rand_consistency.py to get the random consistency level.
2. Run cassandra_verify_table_consistency.py <CONSISTENCY_LEVEL>
3. Return to cassandra_create_table_rand_consistency.py to continue with table creation.
4. View log file cassandra_verify_table_consistency.log
---
### cassandra_create_table_rand_consistency.py
###### Create a Cassandra table with the consistency level chosen at random.
![Output from cassandra_create_table_rand_consistency.py](sample-output/cassandra_create_table_rand_consistency.png)

### cassandra_verify_table_consistency.py
###### Verify synchronous table creation in Cassandra on all nodes in the cluster.  This queries Cassandra until either finding the table in question or being terminated.
![Output from cassandra_verify_table_consistency.py](sample-output/cassandra_verify_table_consistency.png)
