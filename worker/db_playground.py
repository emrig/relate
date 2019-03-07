from utils.sql import Sql
from utils.str_encode import Encoder
from db_queries import queries
from datetime import datetime
import os
import re

db = Sql('ENRON-2')

#db.drop_everything()
#db.create_tables()

t1 = datetime.now()
#db.infer_clusters('fingerprint', 'PERSON')
#db.infer_clusters('fingerprint', 'ORGANIZATION')

#q = queries('Enron')

#files = q.get_docs(['George W. Bush', 'Osama Bin Laden'])
db.infer_clusters('lev_slide', 'PERSON')
db.infer_clusters('lev_slide', 'ORGANIZATION')
db.infer_clusters('lev_slide', 'LOCATION')
#db.infer_clusters('levenshtein', 'PERSON')

t2 = datetime.now()

print(t2 - t1)




#db.create_tables()
#db.infer_clusters('PERSON')

#db.merge_entities('Matthew B.', ['Mathew', 'Matthew B'], 'PERSON')

pass
