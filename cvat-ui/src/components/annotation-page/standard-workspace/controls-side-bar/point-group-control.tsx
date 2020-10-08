// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import Tooltip from 'antd/lib/tooltip';
import Icon from 'antd/lib/icon';

import { GroupIcon } from 'icons';
import { Canvas } from 'cvat-canvas-wrapper';
import { ActiveControl } from 'reducers/interfaces';

interface Props {
    canvasInstance: Canvas;
    activeControl: ActiveControl;
    switchGroupShortcut: string;
    resetGroupShortcut: string;
    pointGroupObjects(enabled: boolean): void;
}

function PointGroupControl(props: Props): JSX.Element {
    const {
        switchGroupShortcut,
        resetGroupShortcut,
        activeControl,
        canvasInstance,
        pointGroupObjects,
    } = props;

    const dynamicIconProps = activeControl === ActiveControl.POINT_GROUP
        ? {
            className: 'cvat-active-canvas-control',
            onClick: (): void => {
                canvasInstance.pointGroup({ enabled: false });
                pointGroupObjects(false);
            },
        } : {
            onClick: (): void => {
                canvasInstance.cancel();
                canvasInstance.pointGroup({ enabled: true });
                pointGroupObjects(true);
            },
        };

    const title = `Move points as a group ${switchGroupShortcut}.`
        + ` Select and press ${resetGroupShortcut} to reset a group`;
    return (
        <Tooltip title={title} placement='right'>
            <Icon {...dynamicIconProps} component={GroupIcon} />
        </Tooltip>
    );
}

export default React.memo(PointGroupControl);
