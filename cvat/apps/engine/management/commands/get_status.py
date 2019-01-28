
# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from ... import annotation
from ... import models

class Command(BaseCommand):
    help = 'Prints some database information'

    # def add_arguments(self, parser):
    #     parser.add_argument('tid', nargs='+', type=int)

    def handle(self, *args, **options):

        print("{:<10} {:<20} {:<40} {:<40}".format('task id', 'task name', 'created date', 'last save/updated at'))

        for task in models.Task.objects.all():
            print("{:<10} {:<20} {:<40} {:<40}".format(task.id, task.name, str(task.created_date), str(task.updated_date)))

