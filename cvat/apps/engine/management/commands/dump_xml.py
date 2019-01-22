
# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from ... import annotation
from ... import models

class Command(BaseCommand):
    help = 'Dumps the XML File of a task id to the root of the share folder'

    def add_arguments(self, parser):
        parser.add_argument('tid', nargs='+', type=int)

    def handle(self, *args, **options):
        with transaction.atomic():
            for tid in options['tid']:
    
                db_task = models.Task.objects.select_for_update().get(id=tid)
                db_task.path = "/home/django/share"
                annotation1 = annotation._AnnotationForTask(db_task)
                annotation1.init_from_db()
                annotation1.dump(annotation.FORMAT_XML, db_task, 'http', 'localhost:8080')
