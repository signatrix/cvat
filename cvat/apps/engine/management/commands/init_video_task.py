import os.path
import time
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

import cvat.apps.engine.task
from cvat.apps.engine.annotation import save_task
from .update_task_data import Command as UpdateTaskData
global_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates a task given a dataset'

    def add_arguments(self, parser):
        parser.add_argument('--video_path', type=str, required=True)
        parser.add_argument('--xml_path', type=str, required=False)
        parser.add_argument('--task_name', type=str, required=True)
        parser.add_argument('--wait', type=bool, default=False)

    def handle(self, *args, **options):

        # pardir_and_vid_file = os.path.join(os.path.split(os.path.split(options['video_path'])[0])[1],os.path.basename(options['video_path']))

        tom = User.objects.get(id=2)
        params = {'data': "/" + options['video_path'],
                  'labels': 'cart ~radio=type:empty,full ~checkbox=difficult:false person ~checkbox=difficult:false',
                  'owner': tom,
                  'z_order': 'false',
                  'storage': 'share',
                  'task_name': options['task_name'],
                  'flip_flag': 'false',
                  'bug_tracker_link': ''}

        db_task = task.create_empty(params)
        target_paths = []
        source_paths = []
        upload_dir = db_task.get_upload_dirname()
        share_root = settings.SHARE_ROOT

        # share_path = params['data']           
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
        print("Enqueued new Task with id: " + str(db_task.id))

        xml_path = options.get('xml_path')
        if xml_path:
            UpdateTaskData.handle(None, {'xml_path': xml_path, 'task_name': options['task_name']})
        log_path = db_task.get_log_path()
        status = task.check(db_task.id)

        while options['wait'] and status['state'] not in ["error", "created"]:
            print("waiting...")
            status = task.check(db_task.id)
            time.sleep(10)
            print(status)
            if os.path.isfile(log_path):
                with open(log_path, "r") as log:
                    print(log.readlines())
