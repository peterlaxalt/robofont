from mojo.UI import getDefault
from math import atan2, degrees
from lib.fontObjects.fontPartsWrappers import RGuideline, RGlyph, RPoint
from typing import Tuple, Union


def getColor():
    curColor = getDefault("glyphViewLocalGuidesColor")
    curColor = map(lambda x: x - 0.001 if x > 0.5 else x + 0.001, curColor)
    return tuple(curColor)


def angleBetweenTwoPoints(pt1: RPoint, pt2: RPoint) -> float:
    x: int
    y: int
    x, y = tuple(i - j for i, j in zip(pt1.position, pt2.position))
    return degrees(atan2(y, x)) % 180


def middleBetweenTwoPoints(pt1: RPoint, pt2: RPoint) -> Tuple[int, int]:
    sums: Tuple[int, int] = tuple(map(sum, zip(pt1.position, pt2.position)))
    return tuple(map(lambda x: x // 2, sums))


def appendGuideline(ptFrom: RPoint, ptTo: RPoint, glyph: RGlyph) -> None:
    angle: float = angleBetweenTwoPoints(ptFrom, ptTo)
    position: Tuple[int, int] = middleBetweenTwoPoints(ptFrom, ptTo)
    glyph.appendGuideline(position, angle, color=getColor())


def addGuideline(glyph: RGlyph) -> None:
    if len(glyph.selection) == 1:
        ptTo, *_ = glyph.selection
        if ptTo.type == "offcurve":
            index = ptTo.index
            contour = ptTo.contour.points
            ptFrom = contour[index + 1]
            if ptFrom.type == "offcurve":
                ptFrom = contour[index - 1]
            appendGuideline(ptFrom, ptTo, glyph)
    if len(glyph.selection) == 2:
        appendGuideline(*glyph.selection, glyph)
    else:
        for contour in glyph:
            for i, segment in enumerate(contour):
                if segment.selected:
                    if segment.type == "line":
                        ptTo = segment.points[-1]
                        ptFrom = contour[i - 1].points[-1]
                        appendGuideline(ptFrom, ptTo, glyph)

    glyph.update()


if __name__ == "__main__":
    glyph: RGlyph = CurrentGlyph()
    with glyph.undo(f"Added segment guideline in {glyph.name}"):
        addGuideline(glyph)
