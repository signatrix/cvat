import SVG from 'svg.js';
import 'svg.select.js';

import { GroupData, Geometry } from './canvasModel';
import { GroupHandlerImpl } from './groupHandler';
import { translateToSVG, translateFromSVG } from './shared';

export interface PointGroupHandler {
    group(groupData: GroupData): void;
    select(state: any): void;
    cancel(): void;
    transform(geometry: Geometry): void;
    resetSelectedObjects(): void;
}

interface BBox {
    x: number;
    y: number;
    width: number;
    height: number;
}

function isShapeInBox(box: BBox): (shape: any) => boolean {
    return (shape: any): boolean => {
        const bbox: SVG.BBox = shape.bbox();

        return bbox.x > box.x
            && bbox.y > box.y
            && bbox.x2 < box.x + box.width
            && bbox.y2 < box.y + box.height;
    };
}

function toObjectState(states: any[]): (shape: any) => any {
    return (shape: any): any => {
        const clientID = shape.attr('clientID');

        return states
            .filter((state: any): boolean => state.clientID === clientID)[0];
    };
}

function transform(prevBBox: BBox, bbox: BBox): (shape: any) => any {
    const transX = bbox.x - prevBBox.x;
    const transY = bbox.y - prevBBox.y;
    const scaleWidth = bbox.width / prevBBox.width;
    const scaleHeight = bbox.height / prevBBox.height;

    return (shape: any): any => {
        const points = [];

        for (let i = 0; i < shape.points.length - 1; i += 2) {
            const [x, y] = [shape.points[i], shape.points[i + 1]];

            const xOffset = x - prevBBox.x;
            const yOffset = y - prevBBox.y;

            const newX = prevBBox.x + transX + xOffset * scaleWidth;
            const newY = prevBBox.y + transY + yOffset * scaleHeight;

            points.push(newX, newY);
        }

        shape.points = points;

        return shape;
    };
}

export class PointGroupHandlerImpl
    extends GroupHandlerImpl
    implements PointGroupHandlerImpl {
    protected onMultipleEditsDone: (objects?: any[]) => void;
    protected isDrawing: boolean;
    protected prevBBox: SVG.BBox;
    protected geometry: Geometry;

    public constructor(
        onMultipleEditsDone: (objects?: any[]) => void,
        getStates: () => any[],
        onFindObject: (event: MouseEvent) => void,
        canvas: SVG.Container,
    ) {
        super((): void => { }, getStates, onFindObject, canvas);

        this.isDrawing = false;
        this.onMultipleEditsDone = onMultipleEditsDone;
    }

    public resetSelectedObjects(): void { }

    public select(): void { }

    public transform(geometry: Geometry): void {
        this.geometry = geometry;
    }

    protected closeGrouping(): void {
        if (this.selectionRect) {
            (this.selectionRect as any)
                .off('dragend')
                .off('resizedone')
                .draggable('stop')
                .resize('stop')
                .selectize(false)
                .remove();

            this.selectionRect = null;
        }

        this.release();
    }

    private bboxFromSVGCoordinates(bbox: SVG.BBox): BBox {
        const frameWidth = this.geometry.image.width;
        const frameHeight = this.geometry.image.height;
        const { offset } = this.geometry;

        let [xtl, ytl, xbr, ybr] = [bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height]
            .map((coord: number): number => coord - offset);

        xtl = Math.min(Math.max(xtl, 0), frameWidth);
        xbr = Math.min(Math.max(xbr, 0), frameWidth);
        ytl = Math.min(Math.max(ytl, 0), frameHeight);
        ybr = Math.min(Math.max(ybr, 0), frameHeight);

        return {
            x: xtl,
            y: ytl,
            width: xbr - xtl,
            height: ybr - ytl,
        };
    }

    private onResizeOrMove(): void {
        const bbox = this.selectionRect.bbox();

        const newStates = this.statesToBeGroupped
            .map(
                transform(
                    this.bboxFromSVGCoordinates(this.prevBBox),
                    this.bboxFromSVGCoordinates(bbox),
                ),
            );

        this.onMultipleEditsDone(newStates);

        this.prevBBox = bbox;
    }

    private getSelectedPoints(bbox: SVG.BBox): any[] {
        const shapes = (this.canvas as any)
            .select('.cvat_canvas_shape')
            .members;

        return shapes
            .filter(isShapeInBox(bbox))
            .map(toObjectState(this.getStates()));
    }

    protected onSelectStart(event: MouseEvent): void {
        if (this.selectionRect) {
            this.closeGrouping();

            this.statesToBeGroupped = [];
            this.highlightedShapes = {};
        }

        const point = translateToSVG(
            this.canvas.node as any as SVGSVGElement,
            [event.clientX, event.clientY],
        );
        this.startSelectionPoint = {
            x: point[0],
            y: point[1],
        };

        this.selectionRect = this.canvas
            .rect()
            .addClass('cvat_canvas_shape_drawing');
        this.selectionRect.attr({ ...this.startSelectionPoint });

        this.isDrawing = true;
    }

    protected onSelectUpdate(event: MouseEvent): void {
        if (this.selectionRect && this.isDrawing) {
            const box = this.getSelectionBox(event);

            this.selectionRect.attr({
                x: box.xtl,
                y: box.ytl,
                width: box.xbr - box.xtl,
                height: box.ybr - box.ytl,
            });
        }
    }

    protected onSelectStop(): void {
        // called on mouseup, mouseleave
        if (this.selectionRect && this.isDrawing) {
            this.prevBBox = this.selectionRect.bbox();

            this.statesToBeGroupped = this.getSelectedPoints(this.prevBBox);

            (this.selectionRect as any)
                .selectize(true, {
                    rotationPoint: false,
                    pointType(x: number, y: number): SVG.Circle {
                        return this.nested
                            .circle(this.options.pointSize)
                            .stroke('black')
                            .fill('#aaa')
                            .center(x, y)
                            .attr({
                                'stroke-width': 1.5,
                            });
                    },
                })
                .resize()
                .resize()
                .draggable()
                .on('resizedone', this.onResizeOrMove.bind(this))
                .on('dragend', this.onResizeOrMove.bind(this));

            this.isDrawing = false;
        }
    }
}
