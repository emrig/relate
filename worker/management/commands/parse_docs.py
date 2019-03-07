from django.core.management.base import BaseCommand
from datetime import datetime
from worker.worker import parse

class Command(BaseCommand):
    help = 'works'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        t1 = datetime.now()

        parse()

        print(datetime.now() - t1)
