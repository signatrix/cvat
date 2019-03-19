import logging
import os.path
import time
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from cvat.apps.engine import task
global_logger = logging.getLogger(__name__)


#./exec_manage init_video_task --video_path="tesco/tesco02/cam0/2019-01-28_11:44:05.mp4" --task_name="tesco/tesco02/cam0/2019-01-28_11:44:05" --xml_path="/home/django/share/out_bak/tesco/tesco02_cam0_2019-01-28_11_44_05.xml" --wait
class Command(BaseCommand):
    help = 'Creates a task given a dataset'

    def add_arguments(self, parser):
        parser.add_argument('--video_path', type=str, required=True)
        parser.add_argument('--task_name', type=str, required=True)
        parser.add_argument('--wait', '-w', action='store_true',
                            help='Wait for task in queue to finish and print logs ')
        parser.add_argument('--xml_path', type=str, required=False)   #requires the flag --wait, because the video import needs to be done

    def handle(self, *args, **options):
        if Task.objects.filter(name=options['task_name']).first():
            raise ValueError("A Task with the name " + options['task_name'] + " already exists.")
        user = User.objects.get(username='bot')
        
        params = {'data': "/" + options['video_path'],
                  'labels': 'cart ~radio=type:empty,full,unclear ~checkbox=difficult:false person ~checkbox=difficult:false',
                  'owner': user,
                  'z_order': 'false',
                  'storage': 'share',
                  'task_name': options['task_name'],
                  'flip_flag': 'false',
                  'bug_tracker_link': ''}

        db_task = task.create_empty(params)

        upload_dir = db_task.get_upload_dirname()
        share_root = settings.SHARE_ROOT

        relpath = os.path.normpath(params['data']).lstrip('/')

        if '..' in relpath.split(os.path.sep):
            raise Exception('Permission denied')

        abspath = os.path.abspath(os.path.join(share_root, relpath))
        
        if os.path.commonprefix([share_root, abspath]) != share_root:
            raise Exception('Bad file path on share: ' + abspath)
        if not os.path.isfile(abspath):
            raise ValueError("\nFile at " + abspath + " does not exist.\n")
        xml_path = options.get('xml_path')
        if xml_path:
            if not os.path.isfile(options['xml_path']):
                raise ValueError("File at " + options['xml_path'] + " does not exist.")

        params['SOURCE_PATHS'] = [abspath]
        params['TARGET_PATHS'] = [os.path.join(upload_dir, relpath)]

        task.create(db_task.id, params)
        print("Enqueued new Task with id: " + str(db_task.id))

        log_path = db_task.get_log_path()
        status = task.check(db_task.id)

        while options['wait'] and status['state'] not in ["error", "created"]:
            print("Waiting...")
            status = task.check(db_task.id)
            time.sleep(10)
            print(status)
            if os.path.isfile(log_path):
                with open(log_path, "r") as log:
                    print(log.readlines())

        # can only 
        if xml_path and options['wait']:
            call_command('import_annotation', xml_path=xml_path, task_name=options['task_name'])