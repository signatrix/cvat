from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task


# python3 manage.py cleanup_tasks --user=bot
class Command(BaseCommand):
    help = 'Deletes completed tasks'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, default='bot')

    def handle(self, *args, **options):
        tasks = Task.objects.filter(status='completed', assignee=User.objects.get(username=options['user']))
        answer = input(str(len(tasks)) + ' task(s) assigned to ' + options['user'] + ' will be deleted. Continue? (yes/no): ')
        if answer in ['yes', 'Yes']:
            for task in tasks:
                task.delete()
        else:
            print('\nAborting.')
