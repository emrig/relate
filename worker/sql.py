import psycopg2
from psycopg2 import sql
from utils.str_encode import Encoder
from resolution import Clustering
from datetime import datetime


BATCH_SIZE = 10000

"""
    This script stores and retrieves entities from SQL.
    TODO:   Resolve entities (updated DB)
            Find some sort of count relationship
            FUZZY MATCHING - How do we rank the most important matches?
            Different entity types could have the same name
            Word cloud for entity relationships? - DO this in SQL
            
            Create function/trigger to get counts for clusters
            Figure out a way to cleanup clusters table after resolution
            Use MD5 (or similar) encoding for guids
            
            GUI - 'Profile Page' Docs, similar entities, etc...
            TF-IDF...? I think that's only import on a per-doc basis
            user should be able to search clusters
"""

class Sql:
    def __init__(self, name):
        self.conn = psycopg2.connect(f"host=database dbname=postgres user=postgres password=pass")
        self.cur = self.conn.cursor()
        self.name = name

        hashed = Encoder(self.name)
        self.hash = hashed.hash_clean
        self.entities = f'Entities_{self.hash}'.lower()
        self.documents = f'Documents_{self.hash}'.lower()
        self.found_in = f'FoundIn_{self.hash}'.lower()
        self.filtered = f'Filtered_{self.hash}'.lower()
        self.clusters = f'Clusters_{self.hash}'.lower()

    def create_tables(self):
        queries = []
        queries.append(f"CREATE TABLE {self.entities} (name varchar NOT NULL, type varchar(20) NOT NULL, \
                            alias varchar NOT NULL, PRIMARY KEY (name, alias))")
        queries.append(f"CREATE TABLE {self.documents} (doc_id varchar PRIMARY KEY, tokens text, \
                            status int NOT NULL, path varchar NOT NULL, last_update timestamp default current_timestamp)")
        #queries.append("""
        #    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        #    ON Documents FOR EACH ROW EXECUTE PROCEDURE
        #    tsvector_update_trigger(tsv, 'pg_catalog.english', doc_id, tokens)""")
        queries.append(f"CREATE TABLE {self.found_in} (id serial PRIMARY KEY, name varchar NOT NULL, alias varchar NOT NULL, doc_id varchar NOT NULL, count integer,\
                            FOREIGN KEY (name, alias) REFERENCES {self.entities}(name, alias) ON DELETE CASCADE ON UPDATE CASCADE, \
                            FOREIGN KEY (doc_id) REFERENCES {self.documents}(doc_id) ON DELETE CASCADE)")


        queries.append(f"CREATE TABLE {self.filtered} (name varchar PRIMARY KEY, type varchar(20) NOT NULL)")
        queries.append(f"""CREATE TABLE {self.clusters} (id serial, names varchar[] PRIMARY KEY, alias varchar, type varchar(20) NOT NULL, \
                            count int, status VARCHAR(10), algorithm varchar(20))""")
        for query in queries:
            try:
                self.cur.execute(query)
                self.conn.commit()
            except Exception as err:
                print(err)
                self.cur.execute('rollback;')

    def clear_tables(self):
        tables = [self.found_in, self.entities, self.documents, self.clusters, self.filtered]
        for table in tables:
            try:
                self.cur.execute(f"DELETE FROM ONLY {table}")
                self.conn.commit()
            except Exception as err:
                print(err)
                self.cur.execute('rollback;')

    def drop_tables(self):
        tables = [self.found_in, self.entities, self.documents, self.clusters, self.filtered]
        for table in tables:
            try:
                self.cur.execute(f"DROP TABLE {table}")
                self.conn.commit()
            except Exception as err:
                print(err)
                self.cur.execute('rollback;')

    def drop_everything(self):
        try:
            self.cur.execute(f"DROP TRIGGER get_cluster_count ON {self.clusters}")
            self.cur.execute(f"DROP FUNCTION get_file_count()")
            self.conn.commit()
        except Exception as err:
            print(err)
            self.cur.execute('rollback;')
        self.drop_tables()

    def insert_entity(self, name, type):
        try:
            # set alias as name during initial insert
            self.cur.execute(f"INSERT INTO {self.entities} (name, type, alias) VALUES (%s, %s, %s)", (name, type, name))
            self.conn.commit()
        except Exception as err:
            if 'already exists' not in str(err.args):
                print(err.args)
            self.cur.execute('rollback;')

    def insert_docs(self, docs):
        try:
            arg_str = ','.join([self.cur.mogrify('(%s, %s, %s, %s)', (x[0], [], x[1], 0)).decode('UTF-8') for x in docs])
            self.cur.execute(f"INSERT INTO {self.documents} (doc_id, tokens, path, status) VALUES " + arg_str + ' ON CONFLICT DO NOTHING')
            self.conn.commit()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')


