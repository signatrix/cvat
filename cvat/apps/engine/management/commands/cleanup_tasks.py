from django.contrib.auth.models import Task, User
from django.core.management.base import BaseCommand

from ... import task


class Command(BaseCommand):
    help = 'Prints some database information'

    def handle(self, *args, **options):

        for db_task in Task.objects.filter(status='completed', assignee=User.objects.get(username='bot')):
            task.delete(db_task.id)
