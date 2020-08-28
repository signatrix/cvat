// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import { ExtendedKeyMapOptions } from 'react-hotkeys';
import { connect } from 'react-redux';

import { Canvas } from 'cvat-canvas-wrapper';
import {
    mergeObjects,
    groupObjects,
    splitTrack,
    redrawShapeAsync,
    rotateCurrentFrame,
    repeatDrawShapeAsync,
    pasteShapeAsync,
    resetAnnotationsGroup,

    groupAnnotationsAsync,
    createAnnotationsAsync,
    saveAnnotationsAsync,
    createAnnotationsAndGroupAsync,
    trackAnnotationsAsync,
} from 'actions/annotation-actions';
import ControlsSideBarComponent from 'components/annotation-page/standard-workspace/controls-side-bar/controls-side-bar';
import { ActiveControl, CombinedState, Rotation } from 'reducers/interfaces';
import { AnyAction } from 'redux';
import { ThunkDispatch } from 'redux-thunk';

interface StateToProps {
    canvasInstance: Canvas;
    rotateAll: boolean;
    activeControl: ActiveControl;
    keyMap: Record<string, ExtendedKeyMapOptions>;
    normalizedKeyMap: Record<string, string>;
    labels: any[];

    jobInstance: any,
    frame: number,
}

interface DispatchToProps {
    mergeObjects(enabled: boolean): void;
    groupObjects(enabled: boolean): void;
    splitTrack(enabled: boolean): void;
    rotateFrame(angle: Rotation): void;
    resetGroup(): void;
    repeatDrawShape(): void;
    pasteShape(): void;
    redrawShape(): void;

    onCreateAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onGroupAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onCreateAnnotationsAndGrouping(sessionInstance: any, frame: number, states: any[]): Promise<void>;
    onTrackAnnotation(sessionInstance: any, frame: number): Promise<void>;
}

function mapStateToProps(state: CombinedState): StateToProps {
    const {
        annotation: {
            canvas: {
                instance: canvasInstance,
                activeControl,
            },
            job: {
                instance: jobInstance,
                labels,
            },
            player: {
                frame: {
                    number: frame,
                },
            },
        },
        settings: {
            player: {
                rotateAll,
            },
        },
        shortcuts: {
            keyMap,
            normalizedKeyMap,
        },
    } = state;

    return {
        rotateAll,
        canvasInstance,
        activeControl,
        normalizedKeyMap,
        keyMap,
        labels,

        jobInstance,
        frame,
    };
}

function dispatchToProps(dispatch: ThunkDispatch<{}, {}, AnyAction>): DispatchToProps {
    return {
        mergeObjects(enabled: boolean): void {
            dispatch(mergeObjects(enabled));
        },
        groupObjects(enabled: boolean): void {
            dispatch(groupObjects(enabled));
        },
        splitTrack(enabled: boolean): void {
            dispatch(splitTrack(enabled));
        },
        rotateFrame(rotation: Rotation): void {
            dispatch(rotateCurrentFrame(rotation));
        },
        repeatDrawShape(): void {
            dispatch(repeatDrawShapeAsync());
        },
        pasteShape(): void {
            dispatch(pasteShapeAsync());
        },
        resetGroup(): void {
            dispatch(resetAnnotationsGroup());
        },
        redrawShape(): void {
            dispatch(redrawShapeAsync());
        },
        onCreateAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void> {
            return dispatch(createAnnotationsAsync(sessionInstance, frame, states));
        },
        onGroupAnnotations(sessionInstance: any, frame: number, states: any[]): Promise<void> {
            return dispatch(groupAnnotationsAsync(sessionInstance, frame, states));
        },
        onCreateAnnotationsAndGrouping(sessionInstance: any, frame: number, states: any[]): Promise<void> {
            return dispatch(createAnnotationsAndGroupAsync(sessionInstance, frame, states));
        },
        onTrackAnnotation(sessionInstance: any, frame: number): Promise<void> {
            return dispatch(trackAnnotationsAsync(sessionInstance, frame));
        },
    };
}

export default connect(
    mapStateToProps,
    dispatchToProps,
)(ControlsSideBarComponent);
