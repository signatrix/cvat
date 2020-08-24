import { Button, Col, List, Row, Select } from 'antd';
import Popover from 'antd/lib/popover';
import Text from 'antd/lib/typography/Text';
import { Canvas } from 'cvat-canvas-wrapper';
import getCore from 'cvat-core-wrapper';
import React, { FC, useCallback, useEffect, useState } from 'react';
import { ShapeType } from 'reducers/interfaces';

const cvat = getCore();

export interface TemplateControlProps {
    canvasInstance: Canvas;
    isDrawing: boolean;
    jobInstance: any;
    frame: number;
    labels: any[];

    onCreateAnnotationsAndGrouping(
        sessionInstance: any,
        frame: number,
        states: any[]
    ): Promise<void>;
}

export const TemplateControl: FC<TemplateControlProps> = ({
    canvasInstance,
    isDrawing,
    frame,
    labels,
}) => {
    const template: VertexTemplate[] = [
        {
            location: [0.5, 0],
            nameHint: 'Head',
        },
        {
            location: [0.5, 0.1],
            nameHint: 'Neck',
        },

        {
            location: [0.28, 0.12],
            nameHint: 'RShoulder',
        },
        {
            location: [0.26, 0.3],
            nameHint: 'RElbow',
        },
        {
            location: [0.24, 0.5],
            nameHint: 'RWrist',
        },

        {
            location: [0.72, 0.12],
            nameHint: 'LShoulder',
        },
        {
            location: [0.75, 0.3],
            nameHint: 'LElbow',
        },
        {
            location: [0.76, 0.5],
            nameHint: 'LWrist',
        },

        {
            location: [0.30, 0.45],
            nameHint: 'RHip',
        },
        {
            location: [0.27, 0.75],
            nameHint: 'RKnee',
        },
        {
            location: [0.25, 1.0],
            nameHint: 'RAnkle',
        },

        {
            location: [0.70, 0.45],
            nameHint: 'LHip',
        },
        {
            location: [0.73, 0.75],
            nameHint: 'LKnee',
        },
        {
            location: [0.75, 1.0],
            nameHint: 'LAnkle',
        },

        // {
        //     location: [0, 0],
        //     nameHint: 'tl',
        // },
        // {
        //     location: [1, 0],
        //     nameHint: 'tr',
        // },
        // {
        //     location: [0, 1],
        //     nameHint: 'bl',
        // },
        // {
        //     location: [1, 1],
        //     nameHint: 'br',
        // }
    ];

    const [points, setPoints] = useState<(PointData & { id: number })[]>([]);

    const getLabel = (nameHint: string | undefined) => {
        const defaultLabel = labels[0] || { id: 1 };

        if (nameHint === undefined) return defaultLabel;

        const nameHintLowerCase = nameHint.toLowerCase();
        const alternatives = labels.filter(({ name }) => name.includes(nameHintLowerCase));

        return alternatives[0] || defaultLabel;
    };

    useEffect(() => {
        setPoints(
            template.map(({ location, nameHint }, idx) => ({
                points: location,
                frame,
                zOrder: 0,
                label: getLabel(nameHint),
                nameHint,
                id: idx,
            })),
        );
    }, []);

    const handleChangeLabel = useCallback(
        (pointId: number) => (labelId: number) => setPoints(points.map((point) => {
            return point.id === pointId
                ? {
                    ...point,
                    label: { id: labelId },
                }
                : point;
        })),
        [points],
    );

    const drawTemplate = () => {
        canvasInstance.cancel();
        canvasInstance.draw({
            enabled: true,
            shapeType: ShapeType.TEMPLATE,
            template: {
                vertices: points.map((x) => x.points),
                labels: points.map((x) => x.label.id),
                edges: [],
            },
        });

        // const states = points.map(createPoint);
        // onCreateAnnotationsAndGrouping(jobInstance, frame, states);
    };

    const dynamicPopoverPros = isDrawing
        ? {
              overlayStyle: {
                  display: 'none',
              },
          }
        : {};

    const dynamicIconProps = isDrawing
        ? {
              className: 'cvat-active-canvas-control',
              onClick: (): void => {
                  canvasInstance.draw({ enabled: false });
              },
          }
        : {};

    const popoverContent = (
        <div
            style={{
                padding: '10px',
            }}
        >
            <Row>
                <Col span={24}>
                    <Text strong>Draw template</Text>
                </Col>
            </Row>
            <Row>
                <Col span={24}>
                    <List
                        dataSource={points}
                        renderItem={item => (
                            <List.Item
                                key={item.id}
                                actions={[
                                    <Select
                                        value={item.label.id}
                                        onChange={handleChangeLabel(item.id)}
                                    >
                                        {labels.map((label: any) => (
                                            <Select.Option
                                                key={label.id}
                                                value={label.id}
                                            >
                                                {label.name}
                                            </Select.Option>
                                        ))}
                                    </Select>,
                                ]}
                            >
                                <List.Item.Meta
                                    title={item.nameHint}
                                />
                            </List.Item>
                        )}
                    />
                </Col>
            </Row>
            <Row>
                <Col offset={12} span={12}>
                    <Button onClick={drawTemplate}>Insert</Button>
                </Col>
            </Row>
        </div>
    );

    return (
        <Popover
            {...dynamicPopoverPros}
            overlayClassName='cvat-draw-shape-popover'
            placement='right'
            content={popoverContent}
        >
            <p
                style={{
                    textAlign: 'center',
                    fontWeight: 'bold',
                }}
                {...dynamicIconProps}
            >
                T
            </p>
        </Popover>
    );
};

interface LabelData {
    id: number;
    name?: string;
    color?: string;
    attributes?: unknown[];
}

interface PointData {
    points: [number, number];
    label: LabelData;
    zOrder: number;
    frame: number;
    nameHint: string | undefined;
}

interface VertexTemplate {
    location: [number, number];
    nameHint: string | undefined;
}

interface EdgeTemplate {
    from: number;
    to: number;
}

const createLabel = (args: LabelData) => new cvat.classes.Label(args);

const createPoint = ({ label, ...other }: PointData) =>
    new cvat.classes.ObjectState({
        label: createLabel(label),
        occluded: false,
        objectType: 'track',
        shapeType: 'points',
        ...other,
    });

export default TemplateControl;
