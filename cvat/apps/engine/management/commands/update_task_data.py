import json
import functools
import re
from xml.dom import minidom
from django.core.management.base import BaseCommand
from ...models import Task
from ...annotation import save_task


class Command(BaseCommand):
    help = 'Updates a given tasks annotation data'

    def add_arguments(self, parser):
        parser.add_argument('--xml_path', type=str, required=True)
        parser.add_argument('--task_name', type=str, required=True)

    def handle(self, *args, **options):
        task = Task.objects.filter(task_name=options['task_name'])

        _, interpolationData = self.parseFile(options.get('xml_path'), task.data)

        save_task(task.id, json.loads(interpolationData))

    def parseFile(self, xml_path, task_data):

        annotationParser = AnnotationParser({'start': 0,
                                             'stop': task_data.size,
                                             'image_meta_data': task_data.image_meta_data,
                                             'flipped': task_data.flipped},
                                            LabelsInfo(task_data.spec),
                                            ConstIdGenerator(-1))

        parsed = annotationParser.parse(xml_path)

        exportData = createExportContainer()
        exportData['create'] = parsed

        return exportData


def createExportContainer():
    exportType = {'create': 0,
                  'update': 1,
                  'delete': 2}
    container = {}
    for key in exportType.keys():
        container[key] = {"boxes": [],
                          "box_paths": [],
                          "points": [],
                          "points_paths": [],
                          "polygons": [],
                          "polygon_paths": [],
                          "polylines": [],
                          "polyline_paths": []}
    return container


class ConstIdGenerator:
    def __init__(self, startId=-1):
        self.startId = startId

    def next(self):
        return self.startId


class IncrementIdGenerator:
    def __init__(self, startId=0):
        self.startId = startId

    def next(self):
        self.startId += 1
        return self.startId

    def reset(self, startId=0):
        self.startId = startId


class AnnotationParser:
    def __init__(self, job, labelsInfo, idGenerator):
        self.startFrame = job.start
        self.stopFrame = job.stop
        self.flipped = job.flipped
        self.im_meta = job.image_meta_data
        self.labelsInfo = labelsInfo
        self.idGen = idGenerator

    def parse_interpolation_data(self, xml):
        data = {'box_paths': [],
                'polygon_paths': [],
                'polyline_paths': [],
                'points_paths': []}

        tracks = xml.getElementsByTagName('track')
        for track in tracks:
            labelId = self.labelsInfo.labelIdOf(track.getAttribute('label'))
            groupId = track.getAttribute('group_id') or '0'
            if not labelId:
                raise ValueError('An unknown label found in the annotation file: ' + xml)

            parsed = {'boxes': track.getElementsByTagName('box'),
                      'polygons': track.getElementsByTagName('polygon'),
                      'polylines': track.getElementsByTagName('polyline'),
                      'points': track.getElementsByTagName('points')}

            for shapetype_ in parsed:
                shapes = sorted(parsed[shapetype_], key=functools.cmp_to_key(lambda x, y: int(x.getAttribute('frame')) - int(y.getAttribute('frame'))))

                while shapes and shapes[0].get('outside'):
                    shapes.pop(0)

                if len(shapes) == 2:
                    if int(shapes[1].getAttribute('frame')) - int(shapes[0].getAttribute('frame')) == 1 and not shapes[0].getAttribute('outside') and shapes[1].getAttribute('outside'):
                        parsed[shapetype_] = []  # pseudo interpolation track (actually is annotation)

            type_ = None
            target = None
            if parsed['boxes']:
                type_ = 'boxes'
                target = 'box_paths'
            elif parsed['polygons']:
                type_ = 'polygons'
                target = 'polygon_paths'
            elif parsed['polylines']:
                type_ = 'polylines'
                target = 'polyline_paths'
            elif parsed['points']:
                type_ = 'points'
                target = 'points_paths'
            else:
                continue

            path = {'label_id': labelId,
                    'group_id': int(groupId),
                    'frame': int(parsed[type_][0].getAttribute('frame')),
                    'attributes': [],
                    'shapes': [],
                    'id': self.idGen_.next()}

            for shape in parsed[type_]:
                keyFrame = int(shape.getAttribute('keyframe'))
                outside = int(shape.getAttribute('outside'))
                frame = int(shape.getAttribute('frame'))

                # All keyframes are significant.
                # All shapes on first segment frame also significant.
                # Ignore all frames less then start.
                # Ignore all frames more then stop.

                significant = keyFrame or frame == self.startFrame

                if significant:
                    attributeList = self.getAttributeList(shape, labelId)
                    shapeAttributes = []
                    pathAttributes = []

                    for attr in attributeList:
                        attrInfo = self.labelsInfo.attrInfo(attr['id'])
                        if attrInfo['mutable']:
                            shapeAttributes.append({'id': attr['id'],
                                                    'value': attr['value']})
                        else:
                            pathAttributes.append({'id': attr['id'],
                                                   'value': attr['value']})

                    path['attributes'] = pathAttributes

                    if type_ == 'boxes':
                        boxPosition = self.getBoxPosition(shape, max(min(frame, self.stopFrame), self.startFrame))
                        path['shapes'].append({'frame': frame,
                                               'occluded': boxPosition['occluded'],
                                               'outside': outside,
                                               'xtl': boxPosition['xtl'],
                                               'ytl': boxPosition['ytl'],
                                               'xbr': boxPosition['xbr'],
                                               'ybr': boxPosition['ybr'],
                                               'z_order': boxPosition['z_order'],
                                               'attributes': shapeAttributes})
                    else:
                        continue
                        # [points, occluded, z_order] = self.getPolyPosition(shape, max(min(frame, self.stopFrame), self.startFrame))
                        # path['shapes'].append({'frame': frame,
                        #                        'occluded': occluded,
                        #                        'outside': outside,
                        #                        'points': points,
                        #                        'z_order': z_order,
                        #                        'attributes': shapeAttributes})

            if path['shapes']:
                data[target].append(path)

        return data

    def parseAnnotationData(self, xml):
        data = {
            'boxes': [],
            'polygons': [],
            'polylines': [],
            'points': []
        }

        tracks = xml.getElementsByTagName('track')
        parsed = {
            'boxes': self.getShapeFromPath('box', tracks),
            'polygons': self.getShapeFromPath('polygon', tracks),
            'polylines': self.getShapeFromPath('polyline', tracks),
            'points': self.getShapeFromPath('points', tracks),
        }

        images = xml.getElementsByTagName('image')
        for image in images:
            frame = image.getAttribute('id')

            for box in image.getElementsByTagName('box'):
                box['frame'] = frame
                parsed['boxes'].append(box)

            for polygon in image.getElementsByTagName('polygon'):
                polygon['frame'] = frame
                parsed['polygons'].append(polygon)

            for polyline in image.getElementsByTagName('polyline'):
                polyline['frame'] = frame
                parsed['polylines'].append(polyline)

            for points in image.getElementsByTagName('points'):
                points['frame'] = frame
                parsed['points'].append(points)

        for shape_type in parsed:
            for shape in parsed[shape_type]:
                frame = int(shape.getAttribute('frame'))
                if frame < self.startFrame or frame > self.stopFrame:
                    continue

                labelId = self.labelsInfo.labelIdOf(shape.getAttribute('label'))
                groupId = shape.getAttribute('group_id') or "0"
                if not labelId:
                    raise ValueError('An unknown label found in the annotation file: ' + shape.getAttribute('label'))

                attributeList = self.getAttributeList(shape, labelId)

                if (shape_type == 'boxes'):
                    boxPosition = self.getBoxPosition(shape, frame)
                    data.boxes.append({
                        'label_id': labelId,
                        'group_id': +groupId,
                        'frame': frame,
                        'occluded': boxPosition['occluded'],
                        'xtl': boxPosition['xtl'],
                        'ytl': boxPosition['ytl'],
                        'xbr': boxPosition['xbr'],
                        'ybr': boxPosition['ybr'],
                        'z_order': boxPosition['z_order'],
                        'attributes': attributeList,
                        'id': self.idGen.next(),
                    })
                else:
                    continue
                    # polyPosition = self.getPolyPosition(shape, frame)
                    # data[shape_type].append({
                    #     'label_id': labelId,
                    #     'group_id': int(groupId),
                    #     'frame': frame,
                    #     'points': polyPosition['points'],
                    #     'occluded': polyPosition['occluded'],
                    #     'z_order': polyPosition['z_order'],
                    #     'attributes': attributeList,
                    #     'id': self.idGen.next(),
                    # })

        return data

    def getBoxPosition(self, box, frame):
        frame = min(frame - self.startFrame, len(self.im_meta['original_size']) - 1)
        im_w = self.im_meta['original_size'][frame].width
        im_h = self.im_meta['original_size'][frame].height

        xtl = int(box.getAttribute('xtl'))
        ytl = int(box.getAttribute('ytl'))
        xbr = int(box.getAttribute('xbr'))
        ybr = int(box.getAttribute('ybr'))

        if xtl < 0 or ytl < 0 or xbr < 0 or ybr < 0 or xtl > im_w or ytl > im_h or xbr > im_w or ybr > im_h:
            raise ValueError('Incorrect bb found in annotation file: xtl=' + xtl + ' ytl=' + ytl + ' xbr=' + xbr + ' ybr=' + ybr + '.\n Box out of range: ' + im_w + 'x' + im_h)

        if self.flipped:
            _xtl = im_w - xbr
            _xbr = im_w - xtl
            _ytl = im_h - ybr
            _ybr = im_h - ytl
            xtl = _xtl
            ytl = _ytl
            xbr = _xbr
            ybr = _ybr

        occluded = int(box.getAttribute('occluded'))
        z_order = box.getAttribute('z_order') or '0'
        return {'xtl': xtl, 'ytl': ytl, 'xbr': xbr, 'ybr': ybr, 'occluded': occluded, 'z_order': int(z_order)}

    def getPolyPosition(self, shape, frame):
        frame = min(frame - self.startFrame, self.im_meta['original_size'].length - 1)
        im_w = self.im_meta['original_size'][frame].width
        im_h = self.im_meta['original_size'][frame].height
        points = shape.getAttribute('points').split('').join(' ')
        # points = PolyShapeModel.convertStringToNumberArray(points)

        for point in points:
            if (point.x < 0 or point.y < 0 or point.x > im_w or point.y > im_h):
                raise ValueError('Incorrect point found in annotation file x=' + point.x + ' y=' + point.y + '. \nPoint out of range ' + im_w + 'x' + im_h)

            if self.flipped:
                point.x = im_w - point.x
                point.y = im_h - point.y
        # points = PolyShapeModel.convertNumberArrayToString(points)

        occluded = int(shape.getAttribute('occluded'))
        z_order = shape.getAttribute('z_order') or '0'
        return {'points': points, 'occluded': occluded, 'z_order': int(z_order)}

    def getAttribute(self, labelId, attrTag):
        name = attrTag.getAttribute('name')
        attrId = self.labelsInfo.attrIdOf(labelId, name)
        if not attrId:
            raise ValueError('An unknown attribute found in the annotation file: ' + name)

        attrInfo = self.labelsInfo.attrInfo(attrId)
        value = self.labelsInfo.strToValues(attrInfo['type'], attrTag.innerHTML)[0]

        if attrInfo['type'] in ['select', 'radio'] and value not in attrInfo['values']:
            raise ValueError('Incorrect attribute value found for "' + name + '" attribute: ' + value)

        elif attrInfo['type'] == 'number':
            if not int(value):
                raise ValueError('Incorrect attribute value found for {name} attribute: {value}. Value must be a number.')
            else:
                minval = int(attrInfo['values'][0])
                maxval = int(attrInfo['values'][1])
                if (int(value) < minval or int(value) > maxval):
                    raise ValueError('Number attribute value out of range for ' + name + ' attribute: ' + value)
        return (attrId, value)

    def getAttributeList(self, shape, labelId):
        attributeDict = {}
        attributes = shape.getElementsByTagName('attribute')
        for attribute in attributes:
            (attrId, value) = self.getAttribute(labelId, attribute)
            attributeDict[attrId] = value

        attributeList = []
        for attrId in attributeDict:
            attributeList.append({'id': attrId,
                                  'value': attributeDict[attrId]})

        return attributeList

    def parse(self, xml_path):
        xml = minidom.parse(xml_path)
        interpolationData = self.parseInterpolationData(xml)
        annotationData = {}  # self.parseAnnotationData(xml)
        return annotationData, interpolationData


class LabelsInfo:
    def __init__(self, job):
        self.self_labels = {}
        self.self_attributes = {}
        self.self_colorIdxs = {}

        for labelKey in job.labels:
            label = {'name': job.labels[labelKey],
                     'attributes': {}}

            for attrKey in job.attributes[labelKey]:
                label['attributes'][attrKey] = self.parseAttributeRow.call(self, job.attributes[labelKey][attrKey])
                self.self_attributes[attrKey] = label['attributes'][attrKey]

            self.self_labels[labelKey] = label
            self.self_colorIdxs[labelKey] = int(labelKey)

    def parseAttributeRow(self, attrRow):
        regex = r"/([~@]{1})(.+)=(.+):(.*)/"
        match = re.findall(regex, attrRow)
        if not match:
            raise ValueError('Can not parse attribute string: ' + attrRow)

        return {
            'mutable': match[1] == "~",
            'type': match[2],
            'name': match[3],
            'values': self.strToValues(match[2], match[4])}

    def labelColorIdx(self, labelId):
        return self.self_colorIdxs[labelId]

    def updateLabelColorIdx(self, labelId):
        if labelId in self.self_colorIdxs:
            self.self_colorIdxs[labelId] += 1

    def normalize(self):
        labels = ""
        for labelId in self.self_labels:
            labels += " " + self.self_labels[labelId].name
            for attrId in self.self_labels[labelId]['attributes']:
                attr = self.self_labels[labelId]['attributes'][attrId]
                labels += ' ' + ("~" if attr['mutable'] else "@")
                labels += attr.type + '=' + attr.name + ':'
                labels += ','.join(map((lambda x: "'" + x + "'" if ' ' in x else x), attr['values']))
        return labels.strip()

    def labels(self):
        tempLabels = {}
        for labelId in self.self_labels:
            tempLabels[labelId] = self.self_labels[labelId]['name']
        return tempLabels

    def labelAttributes(self, labelId):
        attributes = {}
        if labelId in self.self_labels:
            for attrId in self.self_labels[labelId].attributes:
                attributes[attrId] = self.self_labels[labelId].attributes[attrId]['name']
        return attributes

    def attributes(self):
        attributes = {}
        for attrId in self.self_attributes:
            attributes[attrId] = self.self_attributes[attrId]['name']
        return attributes

    def attrInfo(self, attrId):
        info = {}
        if attrId in self.self_attributes:
            obj = self.self_attributes[attrId]
            info['name'] = obj['name']
            info['type'] = obj['type']
            info['mutable'] = obj['mutable']
            info['values'] = obj['values'].slice()
        return info

    def labelIdOf(self, name):
        for labelId in self.self_labels:
            if self.self_labels[labelId]['name'] == name:
                return int(labelId)

    def attrIdOf(self, labelId, name):
        attributes = self.selflabelAttributes(labelId)
        for attrId in attributes:
            if self.self_attributes[attrId]['name'] == name:
                return int(attrId)

    def strToValues(self, type_, string):
        switcher = {'checkbox': [string != '0' and string and string != 'false'],
                    'text': [string]}
        return switcher.get(type_, str(string).split(','))
