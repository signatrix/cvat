from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.task import delete
from cvat.apps.engine.models import Task


class Command(BaseCommand):
    help = 'Deletes completed tasks'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, default="bot")

    def handle(self, *args, **options):
        answer = input("All tasks for user " + options['user'] + " will be deleted. Continue? (yes/no)    ")
        if answer in ['yes', 'Yes']:
            self.delete_tasks(options['user'])
        else:
            print("\nAborting.")

    def delete_tasks(self, user='bot'):
        for task in Task.objects.filter(status='completed', assignee=User.objects.get(username=user)):
            delete(task.id)
