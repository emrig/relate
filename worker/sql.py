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

    def get_docs_to_parse(self, batch_size):
        try:
            # set status flag
            self.cur.execute(f"UPDATE {self.documents} SET status = -1, last_update = current_timestamp WHERE doc_id in \
                                (select doc_id from {self.documents}  WHERE status = 0 \
                                OR (current_timestamp - last_update >= INTERVAL '10 minutes' AND status = -1) \
                                ORDER BY random() limit {batch_size}) RETURNING doc_id, path")
            return self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')

    def get_unprocessed_doc_count(self):
        try:
            # set status flag
            self.cur.execute(f"SELECT count(*) from {self.documents} WHERE status <> {1} AND status <> {-2}")
            return self.cur.fetchall()[0][0]
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')

    def insert_mappings(self, doc_updates, entity_inserts):
        dedup_entities = set([(x['name'], x['type']) for x in entity_inserts])
        arg1 = ','.join([self.cur.mogrify('(%s, %s, %s)', (x[0], x[1], x[0])).decode('UTF-8') for x in dedup_entities])
        arg2 = ','.join([self.cur.mogrify('(%s, %s, %s, %s)', (x['name'], x['doc_id'], x['name'], x['count'])).decode('UTF-8') for x in entity_inserts])
        #TODO: figure out tokens
        arg3 = [x['doc_id'] for x in doc_updates]
        try:
            if arg1:
                self.cur.execute(f"INSERT INTO {self.entities} (name, type, alias) VALUES " + arg1 + ' ON CONFLICT DO NOTHING')
            if arg2:
                self.cur.execute(f"INSERT INTO {self.found_in} (name, doc_id, alias, count) VALUES " + arg2 + ' ON CONFLICT DO NOTHING')
            if arg3:
                self.cur.execute(f"UPDATE {self.documents} SET STATUS = 1, last_update = current_timestamp WHERE doc_id = any (%s)", [arg3])
            self.conn.commit()
            return True

        except Exception as err:
            self.cur.execute('rollback;')
            if 'already exists' not in str(err.args):
                print(err.args)
                raise err.args
            return True

    def update_files_with_errors(self, doc_updates):
        try:
            self.cur.execute(
                f"UPDATE {self.documents} SET STATUS = -2, last_update = current_timestamp WHERE doc_id = any (%s)", [doc_updates])
            return True
        except Exception as err:
            self.cur.execute('rollback;')
            print(err.args)
            return False

    def insert_foundin(self, name, doc_id, count):
        try:
            self.cur.execute(f"INSERT INTO {self.found_in} (name, alias, doc_id, count) VALUES (%s, %s, %s, %s)", (name, name, doc_id, count))
            self.conn.commit()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')

    """
        Retrieve all entities that are found in the same documents as a given entity
    """
    def get_related_entities(self, alias, type=None):
        try:
            self.cur.execute(f"""select c.type, c.alias, count(c.alias)
                from (SELECT aa.doc_id FROM 
                    (SELECT doc_id, count(*) FROM  
                        (SELECT DISTINCT doc_id, alias from {self.found_in} WHERE alias = any (%s)) z\
                        GROUP BY doc_id) aa, {self.documents} bb
                    WHERE aa.doc_id = bb.doc_id AND aa.count >= (%s)) as a, 
                    {self.found_in} as b, {self.entities} as c
                where a.doc_id = b.doc_id and b.alias = c.alias and b.alias != any (%s) and c.type = %s
                group by c.alias, c.type 
                order by count desc
                """, (alias, len(alias), alias, type))
            result = self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return
        if type:
            return [x for x in result if x[0] == type]
        else:
            return result

    """
        Merges entities when user presented with potential matches and proves a resolution
    """
    def merge_entities(self, alias, group, type):
        try:
            self.cur.execute(f"""
            UPDATE {self.entities}
            SET    alias = %s 
            WHERE  alias = any (%s) and type = (%s) 
            """, [alias, group, type])
            self.conn.commit()
            return True
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False

    def delete_entity(self, name):
        try:
            self.cur.execute(f"""
            DELETE FROM {self.entities} CASCADE
            WHERE name = %s
            """, [name])
            self.conn.commit()
            return True
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False

    def get_entities(self):
        try:
            self.cur.execute(f"""
            SELECT distinct alias FROM {self.entities}
            """)
            return self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False

    """
        Gets the total document frequency for a group of entities. Used to rank potential matches.
    """
    def get_group_counts(self, names):
        try:
            self.cur.execute(f"""
                SELECT count(*) FROM {self.found_in}
                WHERE name = any (%s)
                """, [names])
            return self.cur.fetchall()[0][0]
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False

    """
        Gets all of the words in the documents that a group of entities share.
    """
    def get_common_words(self, names):
        try:
            self.cur.execute(sql.SQL("""select b.tokens
            from (select doc_id from {0} 
            where name = any (%s)) as a, {1} as b
            where a.doc_id = b.doc_id""").format(sql.Identifier(self.found_in), sql.Identifier(self.documents)), [names])
            return self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False

    def infer_clusters(self, algorithm, ent_type):
        #q = f"""SELECT DISTINCT alias FROM {self.entities} WHERE type like '{type}'"""
        # dont forget about type
        q = f"""SELECT a.alias, a.doc_id FROM {self.found_in} a, {self.entities} b\
                WHERE a.alias = b.alias AND type = (%s) ORDER BY a.alias"""
        try:
            self.cur.execute(q, [ent_type])
            entities = self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False

        name_match = Clustering(algorithm)
        matches = name_match.get_clusters(entities)

        try:
            arg_str = ','.join([self.cur.mogrify('(%s, %s, %s, %s, %s)', (x[0], x[1], ent_type, 'PENDING', algorithm)).decode('UTF-8') for x in matches])
            self.cur.execute(f"INSERT INTO {self.clusters} (names, count, type, status, algorithm) VALUES " + arg_str + " ON CONFLICT DO NOTHING")
            self.conn.commit()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
