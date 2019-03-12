#!/usr/bin/env python
from django.utils import timezone
from worker.stanford_ner import stan_parse
from worker.queries import num_docs_to_proc, get_docs_to_proc
from relate.settings import NER_BATCH_SIZE
from time import sleep
from discover.models import Entity, Document, Cluster

MAX_ENT_LENGTH = 10

def process_batch():
    t1 = timezone.now()
    print('Files left: ', num_docs_to_proc())

    docs = get_docs_to_proc(NER_BATCH_SIZE)

    if docs:
        stan_parse(docs)
        t2 = timezone.now()
        print('Batch size ', NER_BATCH_SIZE, 'Time: ', str(t2 - t1))

def parse():
    print('Parsing Docs')
    t3 = timezone.now()

    while num_docs_to_proc() > 0:
        print('Total time: ', (timezone.now() - t3))
        process_batch()

    print('Total parse time: ', (timezone.now() - t3))
