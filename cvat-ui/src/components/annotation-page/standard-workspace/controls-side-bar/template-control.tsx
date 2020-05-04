import Button from "antd/lib/button";
import Popover from "antd/lib/popover";
import { Canvas } from "cvat-canvas-wrapper";
import getCore from "cvat-core-wrapper";
import React, { FC } from "react";

const cvat = getCore();

export interface TemplateControlProps {
    canvasInstance: Canvas;
    isDrawing: boolean;
    jobInstance: any;
    frame: number;

    onCreateAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onGroupAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onCreateAnnotationsAndGrouping(sessionInstance: any, frame: number, states: any[]): Promise<void>;
}


export const TemplateControl: FC<TemplateControlProps> = ({
    canvasInstance,
    isDrawing,
    jobInstance,
    frame,
    onCreateAnnotations,
    onGroupAnnotations,
    onCreateAnnotationsAndGrouping,
}) => {

    const template: PointData[] = [
        {
            frame,
            label: { id: 1 },
            points: [302.470703125, 280.466796875],
            zOrder: 0,
        },
        {
            frame,
            label: { id: 2 },
            points: [200.470703125, 280.466796875],
            zOrder: 0,
        },
        {
            frame,
            label: { id: 3 },
            points: [400.470703125, 280.466796875],
            zOrder: 0,
        },
    ]


    const drawTemplate = () => {
        const states = template.map(createPoint);
        onCreateAnnotationsAndGrouping(jobInstance, frame, states);
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

    return (
        <Popover
            {...dynamicPopoverPros}
            overlayClassName="cvat-draw-shape-popover"
            placement="right"
            content={<Button onClick={drawTemplate}>Insert</Button>}
        >
            <p {...dynamicIconProps}>Template</p>
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
}

const createLabel = (args: LabelData) => new cvat.classes.Label(args);

const createPoint = ({
    label,
    ...other
}: PointData) =>
    new cvat.classes.ObjectState({
        label: createLabel(label),
        occluded: false,
        objectType: "track",
        shapeType: "points",
        ...other
    });

export default TemplateControl;
