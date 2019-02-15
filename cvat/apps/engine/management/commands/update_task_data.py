import json
from xml.dom import minidom
from django.core.management.base import BaseCommand
from ...models import Task
from ...annotation import save_task
from auto_annotation import create_anno_container


class Command(BaseCommand):
    help = 'Updates a given tasks data'

    def add_arguments(self, parser):
        parser.add_argument('--xml_path', type=str, required=True)
        parser.add_argument('--task_name', type=str, required=True)

    def handle(self, *args, **options):
        task = Task.objects.filter(task_name=options['task_name'])
        result = {"create": create_anno_container()}
        interpolation_data = parse_interpolation_data(options.get('xml_path'))
        
        itemlist = xmldoc.getElementsByTagName('item')
        print(len(itemlist))
        print(itemlist[0].attributes['name'].value)
        for s in itemlist:
            print(s.attributes['name'].value)
        result['create']['box_paths'] = box_paths

        save_task(task.id, json.loads(result))


def parse_interpolation_data(xml):
    data = {
        'box_paths': [],
        'polygon_paths': [],
        'polyline_paths': [],
        'points_paths': []
    }
    xmldoc = minidom.parse(xml)
    labelsInfo = ""  # WRONG
    tracks = xmldoc.getElementsByTagName('track')
    for track in tracks:
        labelId = labelsInfo.labelIdOf(track.getAttribute('label'))
        groupId = track.getAttribute('group_id') or '0'
        if not labelId:
            raise ValueError('An unknown label found in the annotation file: ' + xml)

        parsed = {
            'boxes': track.getElementsByTagName('box'),
            'polygons': track.getElementsByTagName('polygon'),
            'polylines': track.getElementsByTagName('polyline'),
            'points': track.getElementsByTagName('points'),
        }

        for shape_type in parsed:
            shapes = parsed[shape_type]
            shapes.sort((a,b) => int(a.getAttribute('frame')) - + b.getAttribute('frame'))

            while shapes and shapes[0].get('outside'):
                shapes.shift()

            if len(shapes) == 2:
                if shapes[1].getAttribute('frame') - shapes[0].getAttribute('frame') == 1 and not shapes[0].getAttribute('outside') and shapes[1].getAttribute('outside'):
                    parsed[shape_type] = []  # pseudo interpolation track (actually is annotation)

        type_ = None
        target = None
        if parsed['boxes']:
            type = 'boxes'
            target = 'box_paths'
        elif parsed['polygons']:
            type = 'polygons'
            target = 'polygon_paths'
        elif parsed['polylines']:
            type = 'polylines'
            target = 'polyline_paths'
        elif parsed['points']:
            type = 'points'
            target = 'points_paths'
        else:
            continue

        path = {
            'label_id': labelId,
            'group_id': +groupId,
            'frame': +parsed[type][0].getAttribute('frame'),
            'attributes': [],
            'shapes': [],
            'id': this._idGen.next(),
        }

        for shape in parsed[_type]:
            keyFrame = +shape.getAttribute('keyframe')
            outside = +shape.getAttribute('outside')
            frame = +shape.getAttribute('frame')

            # All keyframes are significant.
            # All shapes on first segment frame also significant.
            # Ignore all frames less then start.
            # Ignore all frames more then stop.

            significant = keyFrame or frame == this._startFrame

            if significant:
                attributeList = this._getAttributeList(shape, labelId)
                shapeAttributes = []
                pathAttributes = []

                for attr in attributeList:
                    attrInfo = this._labelsInfo.attrInfo(attr.id)
                    if attrInfo.mutable:
                        shapeAttributes.append({'id': attr.id,
                                                'value': attr.value})
                    else:
                        pathAttributes.append({'id': attr.id,
                                               'value': attr.value})

                path.attributes = pathAttributes

                if type == 'boxes':
                    xtl, ytl, xbr, ybr, occluded, z_order = _getBoxPosition(shape, Math.clamp(frame, this._startFrame, this._stopFrame))
                    path.shapes.append({'frame': frame,
                                        'occluded': occluded,
                                        'outside': outside,
                                        'xtl': xtl,
                                        'ytl': ytl,
                                        'xbr': xbr,
                                        'ybr': ybr,
                                        'z_order': z_order,
                                        'attributes': shapeAttributes})
                else:
                    [points, occluded, z_order] = this._getPolyPosition(shape, Math.clamp(frame, this._startFrame, this._stopFrame))
                    path.shapes.append({'frame': frame,
                                        'occluded': occluded,
                                        'outside': outside,
                                        'points': points,
                                        'z_order': z_order,
                                        'attributes': shapeAttributes})

        if path['shapes']:
            data[target].append(path)

    return data
