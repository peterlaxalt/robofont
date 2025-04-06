from defconAppKit.controls.glyphCollectionView import GlyphCellItem


class MMGlyphCellItem(GlyphCellItem):

    # only available for glyph wrappers
    def side1GroupPairCount(self):
        return self.glyph().side1GroupPairCount

    # only available for glyph wrappers
    def side2GroupPairCount(self):
        return self.glyph().side2GroupPairCount

    # only available for glyph wrappers
    def side1GlyphPairCount(self):
        return self.glyph().side1GlyphPairCount

    # only available for glyph wrappers
    def side2GlyphPairCount(self):
        return self.glyph().side2GlyphPairCount

    # only available for glyph wrappers
    def side1ExceptionPairCount(self):
        return self.glyph().side1ExceptionPairCount

    # only available for glyph wrappers
    def side2ExceptionPairCount(self):
        return self.glyph().side2ExceptionPairCount

    def side1GroupName(self):
        return self.glyph().metricsMachine.side1GroupName

    def side2GroupName(self):
        return self.glyph().metricsMachine.side2GroupName
