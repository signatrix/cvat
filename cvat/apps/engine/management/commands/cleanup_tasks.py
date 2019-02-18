from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from ... import models
from ... import task

class Command(BaseCommand):
    help = 'Prints some database information'

    def handle(self, *args, **options):

        for db_task in models.Task.objects.filter(status='completed', assignee=User.objects.get(username='bot')):
            task.delete(db_task.id)