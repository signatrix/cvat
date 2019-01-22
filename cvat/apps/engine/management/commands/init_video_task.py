
# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

import os
import logging
import rq

import django_rq
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings

from ... import annotation
from ... import models
from ... import task
from ...logging import task_logger, job_logger

global_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates a task given a dataset id'

    def add_arguments(self, parser):
        parser.add_argument('dataset_id', type=str)

    def handle(self, *args, **options):
        with transaction.atomic():
            
            params = {  'data': options['dataset_id']+'/OUTFILE-2.mp4', 
                        'labels': 'cart ~radio=type:empty,full ~checkbox=difficult:false', 
                        'owner': User.objects.get(id=2), 
                        'z_order': 'false', 
                        'storage': 'share', 
                        'task_name': options['dataset_id'], 
                        'flip_flag': 'false', 
                        'bug_tracker_link': '' }
    
            db_task = task.create_empty(params)
            target_paths = []
            source_paths = []
            upload_dir = db_task.get_upload_dirname()
            share_root = settings.SHARE_ROOT

            if params['storage'] == 'share':
            
                relpath = os.path.normpath(params['data']).lstrip('/')
                if '..' in relpath.split(os.path.sep):
                    raise Exception('Permission denied')
                abspath = os.path.abspath(os.path.join(share_root, relpath))
                if os.path.commonprefix([share_root, abspath]) != share_root:
                    raise Exception('Bad file path on share: ' + abspath)
                source_paths.append(abspath)
                target_paths.append(os.path.join(upload_dir, relpath))

                params['SOURCE_PATHS'] = source_paths
                params['TARGET_PATHS'] = target_paths

                task.create(db_task.id, params)
                task._create_thread(db_task.id, params)