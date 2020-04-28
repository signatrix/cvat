import logging
import os.path
import time
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from cvat.apps.engine import task
global_logger = logging.getLogger(__name__)


# ./exec_manage init_video_task --video_path "aero/aero_office/dataset_000002/aero_office_000002.mp4" --task_name "aero_office_000002" --labels hand juice cacao pasta chips;\
# ./exec_manage init_video_task --video_path "aero/aero_office/dataset_000003/aero_office_000003.mp4" --task_name "aero_office_000003" --labels hand juice cacao pasta chips;\
# ./exec_manage init_video_task --video_path "tesco/tesco02/cam0/2019-01-28_11:44:05.mp4" --task_name "tesco/tesco02/cam0/2019-01-28_11:44:05" --xml_path "/home/django/share/out_bak/tesco/tesco02_cam0_2019-01-28_11_44_05.xml" --wait


# for i in {60..69}
# do
# . / exec_manage init_video_task - -video_path "red_exports/edeka_entrance/dataset_0000$i/edeka_entrance_0000$i.mp4" - -task_name "edeka_entrance_0000$i" - -labels cart
# done

# ./exec_manage init_video_task --video_path "red_exports/globus_se/dataset_000549/globus_se_000549_test.mp4" --labels cart person

base_url = "http://localhost:8080/"
user, password = "cvat", "cvat1234"


class Command(BaseCommand):
    help = 'Creates a task given a video\nExample use: \n./exec_manage init_video_task --video_path "aero/aero_office/dataset_000002/aero_office_000002.mp4" --task_name "aero_office_000002" --labels hand juice cacao pasta chips'

    def add_arguments(self, parser):
        parser.add_argument('--video_path', type=str, required=True)
        parser.add_argument('--labels', type=str, required=False, nargs='+', default=['cart'])
        parser.add_argument('--xml_path', type=str, required=False)

    def build_labels(self, labels):
        label_dict = {'cart': {"name": "cart",
                               "attributes": [
                                   {
                                       "name": "type",
                                       "mutable": True,
                                       "input_type": "radio",
                                       "default_value": "empty",
                                       "values": ["empty", "full", "unclear"],
                                   },
                                   {
                                       "name": "difficult",
                                       "mutable": False,
                                       "input_type": "checkbox",
                                       "default_value": "false",
                                       "values": ["false"]
                                   },
                               ]},  # 'cart ~radio=type:empty,full,unclear ~checkbox=difficult:false',
                      'basket': {"name": "basket",
                                 "attributes": [
                                     {
                                         "name": "type",
                                         "mutable": True,
                                         "input_type": "radio",
                                         "default_value": "empty",
                                         "values": ["empty", "full", "unclear"],
                                     },
                                 ]},  # 'basket ~radio=type:empty,full,unclear
                      'person': {"name": "person",
                                 "attributes": [
                                     {
                                         "name": "difficult",
                                         "mutable": False,
                                         "input_type": "checkbox",
                                         "default_value": "false",
                                         "values": ["false"]
                                     },
                                 ]},  # 'person ~checkbox=difficult:false',
                      'head': {"name": "head",
                                 "attributes": [
                                     {
                                         "name": "facemask",
                                         "mutable": True,
                                         "input_type": "checkbox",
                                         "default_value": "false",
                                         "values": ["false"]
                                     },
                                     {
                                         "name": "back_head",
                                         "mutable": True,
                                         "input_type": "checkbox",
                                         "default_value": "false",
                                         "values": ["false"]
                                     },
                                 ]},  # 'head ~checkbox=facemask:false' ~back_head=facemask:false'
                      'hand': {"name": "hand",
                               "attributes": [
                                   {
                                       "name": "type",
                                       "mutable": False,
                                       "input_type": "radio",
                                       "default_value": "",
                                       "values": ["none", "empty", "juice", "cacao", "pasta", "chips"],
                                   },
                                   {
                                       "name": "difficult",
                                       "mutable": False,
                                       "input_type": "checkbox",
                                       "default_value": "false",
                                       "values": ["false"]
                                   },
                               ]},  # 'hand ~radio=type:none,empty,juice,cacao,pasta,chips',
                      'juice': {"name": "juice",
                                "attributes": [
                                    {
                                        "name": "type",
                                        "mutable": False,
                                        "input_type": "radio",
                                        "default_value": "",
                                        "values": ["none", "in", "out"],
                                    }
                                ]},  # 'juice ~radio=type:none,in,out',
                      'cacao': {"name": "cacao",
                                "attributes": [
                                    {
                                        "name": "type",
                                        "mutable": False,
                                        "input_type": "radio",
                                        "default_value": "",
                                        "values": ["none", "in", "out"],
                                    }
                                ]},  # 'cacao ~radio=type:none,in,out',
                      'pasta': {"name": "pasta",
                                "attributes": [
                                    {
                                        "name": "type",
                                        "mutable": False,
                                        "input_type": "radio",
                                        "default_value": "",
                                        "values": ["none", "in", "out"],
                                    }
                                ]},  # 'pasta ~radio=type:none,in,out',
                      'chips': {"name": "chips",
                                "attributes": [
                                    {
                                        "name": "type",
                                        "mutable": False,
                                        "input_type": "radio",
                                        "default_value": "",
                                        "values": ["none", "in", "out"],
                                    }
                                ]},  # 'chips ~radio=type:none,in,out',
                      }
        print(label_dict)
        wanted_labels = []
        for label in labels:
            if label not in label_dict.keys():
                print(label_dict.keys())
                raise ValueError("Did not recognize label " + label)
            wanted_labels.append(label_dict[label])
        return wanted_labels

    def handle(self, *args, **options):

        resp = requests.get(base_url + 'api/v1/users/self', verify=False, auth=(user, password))
        cur_user_info = resp.json()

        if resp.status_code != 200:
            print("Wrong username/password")
            return False

        # if Task.objects.filter(name=options['task_name']).first():
        #     raise ValueError("A Task with the name " + options['task_name'] + " already exists.")
        # user = User.objects.get(username='bot')
        labels = self.build_labels(options['labels'])
        share_root = settings.SHARE_ROOT
        relpath = os.path.normpath("/" + options['video_path']).lstrip('/')
        abspath = os.path.abspath(os.path.join(share_root, relpath))
        task_name = os.path.splitext(os.path.basename(relpath))[0]
        if os.path.commonprefix([share_root, abspath]) != share_root:
            raise Exception('Bad file path on share: ' + abspath)
        if not os.path.isfile(abspath):
            raise ValueError("\nFile at " + abspath + " does not exist.\n")
        xml_path = options.get('xml_path')
        if xml_path:
            if not os.path.isfile(xml_path):
                xml_path = os.path.abspath(os.path.join(share_root, xml_path))
            if not os.path.isfile(xml_path):
                raise ValueError("File at " + xml_path + " does not exist.")

        res = self.create_task(task_name, relpath, cur_user_info, user, password, labels=labels)
        print(res)

        if xml_path:
            try:
                print("Adding annotations from {}".format(xml_path))
                call_command('import_annotation', xml_path=xml_path, task_name=task_name)
            except:
                pass
        if res:
            try:
                os.remove(abspath)
            except OSError as e:
                print(f"Could not delete file at {abspath}.\n{e}")

    def create_task(self, task_name, full_relative_path, cur_user_info, user, password, labels=[], bug_tracker=""):
        res = {"status": False, "full_relative_path": full_relative_path}
        # cart ~radio=type:empty,full,unclear ~checkbox=difficult:false
        data_task_create = {
            "name": task_name,
            "owner": cur_user_info["id"],
            "image_quality": 75,
            "bug_tracker": bug_tracker,
            "labels": labels
        }

        task_creation_resp = requests.post(base_url + 'api/v1/tasks', verify=False, auth=(user, password), json=data_task_create)

        if task_creation_resp.status_code != 201:
            print("task_creation_resp.status_code =", task_creation_resp.status_code)
            print("task_creation_resp.json =")
            print(task_creation_resp.json())
            print("CANNOT CREATE TASK {}".format(task_name))
            return res
        task_id = task_creation_resp.json()["id"]
        res["task_id"] = task_id

        data_server_files = {
            #            'client_files': [],
            #            'remote_files': [],
            "server_files[0]": [full_relative_path]
        }

        server_files_resp = requests.post(base_url + 'api/v1/tasks/{}/data'.format(task_id), verify=False, auth=(user, password), data=data_server_files)

        # print("server_files_resp.status_code =", server_files_resp.status_code)
        # print("server_files_resp.json =")
        # print(server_files_resp.json())
        if int(server_files_resp.status_code) not in (201, 202):
            print("CANNOT SET SERVER FILES")
            return res

        print("Task for '{}' is added".format(os.path.basename(full_relative_path)))

        status_resp_json = {}
        message = ""
        while True:
            status_files_resp = requests.get(base_url + 'api/v1/tasks/{}/status'.format(task_id), verify=False, auth=(user, password))
            if status_files_resp.status_code != 200:
                print("CANNOT GET STATUS")
                return res
            status_resp_json = status_files_resp.json()
            if not message == status_resp_json["message"]:
                message = status_resp_json["message"]
                print(message)
            if status_resp_json.get('state', "") in ("Finished", "Failed"):
                break

            time.sleep(3)

        if status_resp_json.get('state', "") == "Finished":
            print("Task is created and video '{}' was decoded".format(os.path.basename(full_relative_path)))
        else:
            print("ERROR DURING CREATION OF THE TASK '{}'".format(task_name))
            return res

        job_id_resp = requests.get(base_url + 'api/v1/tasks/{}'.format(task_id), verify=False, auth=(user, password))
        if job_id_resp.status_code != 200:
            print("CANNOT GET JOB ID, status code =", job_id_resp.status_code)
            print(job_id_resp.json())
            return res
        job_id_json = job_id_resp.json()
        # print(job_id_json)
        assert "segments" in job_id_json
        segments = list(job_id_json["segments"])
        assert segments
        assert len(segments) == 1
        assert "jobs" in segments[0]
        jobs = segments[0]["jobs"]
        assert len(jobs) == 1
        job_id = jobs[0]["id"]
        url_for_job = base_url + "?id={}".format(job_id)
        # print("url_for_job =", url_for_job)
        res["url_for_job"] = url_for_job
        res["status"] = True
        return res
