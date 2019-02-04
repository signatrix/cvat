
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
        parser.add_argument('--tid', nargs='+', type=int)
        parser.add_argument('--dump_folder', type=str, default="/home/django/share")

    def handle(self, *args, **options):
        for tid in options['tid']:

            db_task = models.Task.objects.get(id=tid)
            db_task.path = options['dump_folder']
            annotation1 = annotation._AnnotationForTask(db_task)
            annotation1.init_from_db()
            annotation1.dump(annotation.FORMAT_XML, 'http', 'localhost:8080', {})
