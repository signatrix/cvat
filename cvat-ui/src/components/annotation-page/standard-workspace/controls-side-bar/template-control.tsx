import { Button, Col, List, Row, Select } from 'antd';
import Popover from 'antd/lib/popover';
import Text from 'antd/lib/typography/Text';
import { Canvas } from 'cvat-canvas-wrapper';
import getCore from 'cvat-core-wrapper';
import React, { FC, useCallback, useEffect, useState } from 'react';

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
    jobInstance,
    frame,
    labels,
    onCreateAnnotationsAndGrouping
}) => {
    const template: VertexTemplate[] = [
        {
            location: [302.470703125, 280.466796875],
            nameHint: "Head"
        },
        {
            location: [200.470703125, 280.466796875],
            nameHint: "LHand"
        },
        {
            location: [400.470703125, 280.466796875],
            nameHint: "RHand"
        }
    ];

    const [points, setPoints] = useState<(PointData & { id: number })[]>([]);

    useEffect(() => {
        setPoints(
            template.map(({ location, nameHint }, idx) => ({
                points: location,
                frame,
                zOrder: 0,
                label: labels[0] || { id: 1 },
                nameHint,
                id: idx
            }))
        );
    }, []);

    const handleChangeLabel = useCallback(
        (pointId: number) => (labelId: number) =>
            setPoints(
                points.map(point =>
                    point.id === pointId
                        ? {
                              ...point,
                              label: { id: labelId }
                          }
                        : point
                )
            ),
        [points]
    );

    const drawTemplate = () => {
        canvasInstance.cancel();
        canvasInstance.draw({
            enabled: true,
            shapeType: ShapeType.TEMPLATE,
            template: {
                vertices: points.map(x => x.points),
                labels: points.map(x => x.label.id),
                edges: [],
            }
        });

        // const states = points.map(createPoint);
        // onCreateAnnotationsAndGrouping(jobInstance, frame, states);
    };

    const dynamicPopoverPros = isDrawing
        ? {
              overlayStyle: {
                  display: "none"
              }
          }
        : {};

    const dynamicIconProps = isDrawing
        ? {
              className: "cvat-active-canvas-control",
              onClick: (): void => {
                  canvasInstance.draw({ enabled: false });
              }
          }
        : {};

    const popoverContent = (
        <div
            style={{
                padding: "10px"
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
                                    </Select>
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
            overlayClassName="cvat-draw-shape-popover"
            placement="right"
            content={popoverContent}
        >
            <p
                style={{
                    textAlign: "center",
                    fontWeight: "bold"
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
        objectType: "track",
        shapeType: "points",
        ...other
    });

export default TemplateControl;
