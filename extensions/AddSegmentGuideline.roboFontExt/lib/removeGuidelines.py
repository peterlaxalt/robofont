from typing import Tuple
from lib.fontObjects.fontPartsWrappers import RGlyph
from addGuideline import getColor


def removeGuidelines(glyph: RGlyph):
    colorsToRemove: Tuple[tuple, ...] = ((0.999, 0.001, 0.0, 0.499), getColor())
    for guideline in glyph.guidelines:
        if guideline.color in colorsToRemove:
            glyph.removeGuideline(guideline)


if __name__ == "__main__":
    try:
        glyph: RGlyph = CurrentGlyph()
        with glyph.undo(f"removed segment guideliens in {glyph.name}"):
            removeGuidelines(glyph)
    except:
        pass
