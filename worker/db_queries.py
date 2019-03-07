from utils.sql import Sql


class queries(Sql):
    def get_docs(self, aliases):
        num_entities = len(aliases)
        try:
            self.cur.execute(f"""SELECT a.doc_id, b.path FROM 
                    (SELECT doc_id, count(*) FROM  
                            (SELECT DISTINCT doc_id, alias from {self.found_in} WHERE alias = any (%s)) z\
                            GROUP BY doc_id) a, {self.documents} b
                    WHERE a.doc_id = b.doc_id AND a.count >= (%s)""", (aliases, num_entities))
            return self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
    def get_related_clusters(self, entity, type):
        try:
            self.cur.execute(f"""SELECT id, names, count 
                    FROM {self.clusters}
                    WHERE (%s) = any(names) AND type = (%s) AND status = (%s)""", (entity, type, 'PENDING'))
            return self.cur.fetchall()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
    def update_cluster_status(self, id, alias, status):
        try:
            self.cur.execute(f"""
                UPDATE ONLY {self.clusters}
                SET status = (%s), alias = (%s)
                WHERE id = (%s)
            """, (status, alias, id))
            self.conn.commit()
        except Exception as err:
            print(err.args)
            self.cur.execute('rollback;')
            return False
if __name__ == "__main__":
    db = queries('a')
    #result2 = db.get_related_entities(['Sand Hill Capital'], 'PERSON')
    #result3 = db.get_related_entities(['Elizabeth Sager', 'Genia Fitzgerald', "David Portz", 'Leslie Hansen'], 'LOCATION')
    #file_results = db.get_docs(['Elizabeth Sager', 'Genia Fitzgerald', "David Portz", 'Leslie Hansen', 'Cayman Islands'])

    names = ['Houston', 'California', 'Washington', 'San Francisco', 'Europe', 'Canada', 'Portland', 'Smith Street', 'United States',
             'El Paso', 'Sacramento', 'San Diego', 'Australia', 'Virginia', 'Louisiana', 'Atlanta', 'Las Vegas', 'Singapore',
             'Tennessee', 'Miami', 'Sydney', 'New Orleans', 'Georgia', 'Kansas City', 'Berkeley', 'Seattle', 'North America', 'New Dehli',
             'Albuquerque', 'Arkansas', 'Netherlands', 'Minneapolis', 'Salt Lake City', 'Pasadena', 'Pennsylvania Avenue', 'Philippines'
             'Washington Dc', 'San Antonio', 'Cayman Islands', 'Pennsylvania', 'Cincinnati', 'Yucca Mountain', 'Pittsburgh', 'Abu Dhabi']
    #names = ['Jeff Dasovich', 'Steven J Kean', 'Vince J Kaminski', 'Sara Shackleton', 'Tana Jones', 'Mark Taylor', 'Sally Beck', 'Susan J Mara',
    #         'Daren J Farmer', 'David W Delainey', 'Elizabeth A Sager', 'Carol St Claire', 'Benjamin Rogers', 'Jeffrey Skilling', 'Steven J Keanna',
    #         'Steven J Keanna', 'Linda Robertson', 'Mark Haediecke', 'Harry J Kingerski', 'Gerald Ray Nemec', 'Sandra Mccubbin', 'John J Lavorato',
    #         'Greg Whalley', 'Mike Mcconell', 'Louise Kitchens', 'Kenneth Lay','Travis Mccullough', ('Steve Kean', 'Steven J Kean'), 'Louis Soldano',
    #         ('William S Bradfordhouect', 'William S Bradford'), 'Rebecca Mcdonald', 'Curtis L Hebert Jr', 'Georganne M Hodges', 'Jeff Garcia',
    #         'Tammy Depaolis', 'Joseph Stepenovitch']
    #names = ['Enron North America Corp', 'Enron Corp', 'Enron Wholesale Services Group', 'California Public Utilities Commission', 'Federal Energy Regulatory Commission',
    #         'Pacific Gas And Electric Company', ('San Diego Gas And Electric Co', 'San Diego Gas and Electric Company'), 'Dabhol Power Company', 'Jp Morgan Chase',
    #         'Silicon Valley Manufacturing Group']

    type  = 'LOCATION'

    for name in names:
        if len(name) == 2:
            results = db.get_related_clusters(name[0], type)
            name = name[1]
        else:
            results = db.get_related_clusters(name, type)
        name_results = [(x[0], x[1]) for x in results]
        if len(name_results) > 0:
            print(name_results)
            for cluster in name_results:
                id = cluster[0]
                group = cluster[1]
                db.merge_entities(name, group, type)
                db.update_cluster_status(id, name, 'ADDED')
    pass
