// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { GlobalHotKeys, ExtendedKeyMapOptions } from 'react-hotkeys';
import Layout from 'antd/lib/layout';

import { ActiveControl, Rotation } from 'reducers/interfaces';
import { Canvas } from 'cvat-canvas-wrapper';

import RotateControl from './rotate-control';
import CursorControl from './cursor-control';
import MoveControl from './move-control';
import FitControl from './fit-control';
import ResizeControl from './resize-control';
import DrawRectangleControl from './draw-rectangle-control';
import DrawPolygonControl from './draw-polygon-control';
import DrawPolylineControl from './draw-polyline-control';
import DrawPointsControl from './draw-points-control';
import DrawCuboidControl from './draw-cuboid-control';
import SetupTagControl from './setup-tag-control';
import MergeControl from './merge-control';
import GroupControl from './group-control';
import SplitControl from './split-control';
import TemplateControl from './template-control';
import { Button } from 'antd';

interface Props {
    canvasInstance: Canvas;
    activeControl: ActiveControl;
    keyMap: Record<string, ExtendedKeyMapOptions>;
    normalizedKeyMap: Record<string, string>;
    jobInstance: any,
    frame: number,
    labels: any[],

    mergeObjects(enabled: boolean): void;
    groupObjects(enabled: boolean): void;
    splitTrack(enabled: boolean): void;
    rotateFrame(rotation: Rotation): void;
    repeatDrawShape(): void;
    pasteShape(): void;
    resetGroup(): void;
    onCreateAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onGroupAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onCreateAnnotationsAndGrouping(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onTrackAnnotation(sessionInstance: any, frame: number): Promise<void>;
    redrawShape(): void;
}

export default function ControlsSideBarComponent(props: Props): JSX.Element {
    const {
        canvasInstance,
        activeControl,
        normalizedKeyMap,
        keyMap,
        mergeObjects,
        groupObjects,
        splitTrack,
        rotateFrame,
        repeatDrawShape,
        pasteShape,
        resetGroup,
        normalizedKeyMap,
        keyMap,

        jobInstance,
        labels,
        frame,
        onCreateAnnotations,
        onGroupAnnotations,
        onCreateAnnotationsAndGrouping,
        onTrackAnnotation,
        redrawShape,
    } = props;

    const preventDefault = (event: KeyboardEvent | undefined): void => {
        if (event) {
            event.preventDefault();
        }
    };

    const subKeyMap = {
        PASTE_SHAPE: keyMap.PASTE_SHAPE,
        SWITCH_DRAW_MODE: keyMap.SWITCH_DRAW_MODE,
        SWITCH_MERGE_MODE: keyMap.SWITCH_MERGE_MODE,
        SWITCH_SPLIT_MODE: keyMap.SWITCH_SPLIT_MODE,
        SWITCH_GROUP_MODE: keyMap.SWITCH_GROUP_MODE,
        RESET_GROUP: keyMap.RESET_GROUP,
        CANCEL: keyMap.CANCEL,
        CLOCKWISE_ROTATION: keyMap.CLOCKWISE_ROTATION,
        ANTICLOCKWISE_ROTATION: keyMap.ANTICLOCKWISE_ROTATION,
    };

    const handlers = {
        PASTE_SHAPE: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            canvasInstance.cancel();
            pasteShape();
        },
        SWITCH_DRAW_MODE: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            const drawing = [ActiveControl.DRAW_POINTS, ActiveControl.DRAW_POLYGON,
                ActiveControl.DRAW_POLYLINE, ActiveControl.DRAW_RECTANGLE,
                ActiveControl.DRAW_CUBOID].includes(activeControl);

            if (!drawing) {
                canvasInstance.cancel();
                // repeateDrawShapes gets all the latest parameters
                // and calls canvasInstance.draw() with them

                if (event && event.shiftKey) {
                    redrawShape();
                } else {
                    repeatDrawShape();
                }
            } else {
                canvasInstance.draw({ enabled: false });
            }
        },
        SWITCH_MERGE_MODE: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            const merging = activeControl === ActiveControl.MERGE;
            if (!merging) {
                canvasInstance.cancel();
            }
            canvasInstance.merge({ enabled: !merging });
            mergeObjects(!merging);
        },
        SWITCH_SPLIT_MODE: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            const splitting = activeControl === ActiveControl.SPLIT;
            if (!splitting) {
                canvasInstance.cancel();
            }
            canvasInstance.split({ enabled: !splitting });
            splitTrack(!splitting);
        },
        SWITCH_GROUP_MODE: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            const grouping = activeControl === ActiveControl.GROUP;
            if (!grouping) {
                canvasInstance.cancel();
            }
            canvasInstance.group({ enabled: !grouping });
            groupObjects(!grouping);
        },
        RESET_GROUP: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            const grouping = activeControl === ActiveControl.GROUP;
            if (!grouping) {
                return;
            }
            resetGroup();
            canvasInstance.group({ enabled: false });
            groupObjects(false);
        },
        CANCEL: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            if (activeControl !== ActiveControl.CURSOR) {
                canvasInstance.cancel();
            }
        },
        CLOCKWISE_ROTATION: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            rotateFrame(Rotation.CLOCKWISE90);
        },
        ANTICLOCKWISE_ROTATION: (event: KeyboardEvent | undefined) => {
            preventDefault(event);
            rotateFrame(Rotation.ANTICLOCKWISE90);
        },
    };

    return (
        <Layout.Sider
            className='cvat-canvas-controls-sidebar'
            theme='light'
            width={44}
        >
            <GlobalHotKeys keyMap={subKeyMap} handlers={handlers} allowChanges />
            <CursorControl
                cursorShortkey={normalizedKeyMap.CANCEL}
                canvasInstance={canvasInstance}
                activeControl={activeControl}
            />
            <MoveControl canvasInstance={canvasInstance} activeControl={activeControl} />
            <RotateControl
                anticlockwiseShortcut={normalizedKeyMap.ANTICLOCKWISE_ROTATION}
                clockwiseShortcut={normalizedKeyMap.CLOCKWISE_ROTATION}
                rotateFrame={rotateFrame}
            />

            <hr />

            <Button onClick={() => onTrackAnnotation(jobInstance, frame)}>Track</Button>

            <hr />

            <FitControl canvasInstance={canvasInstance} />
            <ResizeControl canvasInstance={canvasInstance} activeControl={activeControl} />

            <hr />

            <DrawRectangleControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_RECTANGLE}
            />
            <DrawPolygonControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_POLYGON}
            />
            <DrawPolylineControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_POLYLINE}
            />
            <DrawPointsControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_POINTS}
            />
            <DrawCuboidControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_CUBOID}
            />
            <TemplateControl
                canvasInstance={canvasInstance}
                isDrawing={activeControl === ActiveControl.DRAW_TEMPLATE}
                jobInstance={jobInstance}
                frame={frame}
                labels={labels}
                onCreateAnnotationsAndGrouping={onCreateAnnotationsAndGrouping}
            />

            <SetupTagControl
                canvasInstance={canvasInstance}
                isDrawing={false}
            />

            <hr />

            <MergeControl
                switchMergeShortcut={normalizedKeyMap.SWITCH_MERGE_MODE}
                canvasInstance={canvasInstance}
                activeControl={activeControl}
                mergeObjects={mergeObjects}
            />
            <GroupControl
                switchGroupShortcut={normalizedKeyMap.SWITCH_GROUP_MODE}
                resetGroupShortcut={normalizedKeyMap.RESET_GROUP}
                canvasInstance={canvasInstance}
                activeControl={activeControl}
                groupObjects={groupObjects}
            />
            <SplitControl
                canvasInstance={canvasInstance}
                switchSplitShortcut={normalizedKeyMap.SWITCH_SPLIT_MODE}
                activeControl={activeControl}
                splitTrack={splitTrack}
            />
        </Layout.Sider>
    );
}
