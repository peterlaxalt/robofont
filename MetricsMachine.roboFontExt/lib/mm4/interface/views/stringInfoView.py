import AppKit
from objc import super

from mm4.interface.colors import *

from mojo.UI import inDarkMode

columnWidth = 60
rowHeight = 15
iconColumnWidth = 14



# -----
# icons
# -----

iconWidthImage = None
iconLeftImage = None
iconRightImage = None
iconKernImage = None


def _makeIconImages():
    global iconWidthImage
    global iconLeftImage
    global iconRightImage
    global iconKernImage

    h = rowHeight - 1
    y3 = h / 2.0
    y2 = y3 - 1
    y4 = y3 + 1
    y1 = y3 - 4
    y5 = y3 + 4

    w = iconColumnWidth
    x3 = w / 2.0
    x2 = x3 - 1
    x4 = x3 + 1
    x1 = x3 - 5
    x5 = x3 + 5

    iconWidthImage = AppKit.NSImage.alloc().initWithSize_((iconColumnWidth, rowHeight - 1))
    iconWidthImage.lockFocus()
    if inDarkMode():
        glyphInfoIconColorDarkMode.set()
    else:
        glyphInfoIconColor.set()
    path = AppKit.NSBezierPath.bezierPath()
    path.moveToPoint_((x1, y3))
    path.lineToPoint_((x2, y5))
    path.lineToPoint_((x2, y4))
    path.lineToPoint_((x4, y4))
    path.lineToPoint_((x4, y5))
    path.lineToPoint_((x5, y3))
    path.lineToPoint_((x4, y1))
    path.lineToPoint_((x4, y2))
    path.lineToPoint_((x2, y2))
    path.lineToPoint_((x2, y1))
    path.lineToPoint_((x1, y3))
    path.fill()
    iconWidthImage.unlockFocus()

    iconLeftImage = AppKit.NSImage.alloc().initWithSize_((iconColumnWidth, rowHeight - 1))
    iconLeftImage.lockFocus()
    if inDarkMode():
        glyphInfoIconColorDarkMode.set()
    else:
        glyphInfoIconColor.set()
    path = AppKit.NSBezierPath.bezierPath()
    path.moveToPoint_((x1, y3))
    path.lineToPoint_((x2, y5))
    path.lineToPoint_((x2, y4))
    path.lineToPoint_((x5, y4))
    path.lineToPoint_((x5, y2))
    path.lineToPoint_((x2, y2))
    path.lineToPoint_((x2, y1))
    path.lineToPoint_((x1, y3))
    path.fill()
    iconLeftImage.unlockFocus()

    iconRightImage = AppKit.NSImage.alloc().initWithSize_((iconColumnWidth, rowHeight - 1))
    iconRightImage.lockFocus()
    if inDarkMode():
        glyphInfoIconColorDarkMode.set()
    else:
        glyphInfoIconColor.set()
    path = AppKit.NSBezierPath.bezierPath()
    path.moveToPoint_((x1, y4))
    path.lineToPoint_((x2, y4))
    path.lineToPoint_((x4, y4))
    path.lineToPoint_((x4, y5))
    path.lineToPoint_((x5, y3))
    path.lineToPoint_((x4, y1))
    path.lineToPoint_((x4, y2))
    path.lineToPoint_((x1, y2))
    path.lineToPoint_((x1, y4))
    path.fill()
    iconRightImage.unlockFocus()

    iconKernImage = AppKit.NSImage.alloc().initWithSize_((iconColumnWidth, rowHeight - 1))
    iconKernImage.lockFocus()
    if inDarkMode():
        glyphInfoIconColorDarkMode.set()
    else:
        glyphInfoIconColor.set()
    path = AppKit.NSBezierPath.bezierPath()
    path.moveToPoint_((x1 + 1, y5))
    path.lineToPoint_((x2 + 1, y3))
    path.lineToPoint_((x1 + 1, y1))
    path.lineToPoint_((x1 + 1, y5))
    path.moveToPoint_((x4 - 1, y3))
    path.lineToPoint_((x5 - 1, y5))
    path.lineToPoint_((x5 - 1, y1))
    path.lineToPoint_((x4 - 1, y3))
    path.fill()
    iconKernImage.unlockFocus()


class MMStringInfoView(AppKit.NSView):

    def initWithFont_(self, font):
        self = super(MMStringInfoView, self).init()
        self.font = font
        self._glyphs = []
        self._selectionIndexes = []
        if iconWidthImage is None:
            _makeIconImages()
        return self

    def dealloc(self):
        self._font = None
        self._glyphs = None
        super(MMStringInfoView, self).dealloc()

    # ---------------------
    # frame setting support
    # ---------------------

    def flushFrame(self):
        neededWidth = len(self._glyphs) * columnWidth
        neededHeight = rowHeight * 5
        self.setFrame_(((0, 0), (neededWidth, neededHeight)))

    # ------------
    # data setting
    # ------------

    def setGlyphs_selectionIndexes_(self, glyphs, selectionIndexes):
        # XXX subscribe to glyph changes!
        self._glyphs = glyphs
        self._selectionIndexes = selectionIndexes
        if glyphs:
            self._font = glyphs[0].getParent()
        else:
            self._font = None

    # -------
    # drawing
    # -------

    def drawRect_(self, rect):
        if inDarkMode():
            glyphInfoBackgroundColorDarkMode.set()
        else:
            glyphInfoBackgroundColor.set()
        AppKit.NSRectFill(self.bounds())

        if self._glyphs:
            drawKerning = len(self._glyphs) > 1
            kerning = self._font.kerning

            # blocks
            if inDarkMode():
                glyphInfoHeaderColorDarkMode.set()
            else:
                glyphInfoHeaderColor.set()
            x = iconColumnWidth
            y = rowHeight * 4
            w = len(self._glyphs) * columnWidth
            h = rowHeight
            AppKit.NSRectFill(((x, y), (w, h)))
            if inDarkMode():
                AppKit.NSColor.blackColor().set()
            else:
                AppKit.NSColor.whiteColor().set()
            x = iconColumnWidth
            y = rowHeight
            w = len(self._glyphs) * columnWidth
            h = rowHeight * 3
            AppKit.NSRectFill(((x, y), (w, h)))
            if drawKerning:
                x = iconColumnWidth + (columnWidth / 2)
                y = 0
                w = (len(self._glyphs) - 1) * columnWidth
                h = rowHeight
                AppKit.NSRectFill(((x, y), (w, h)))

            # selection
            if self._selectionIndexes:
                for leftIndex, rightIndex in self._selectionIndexes:
                    left = self._glyphs[leftIndex].name
                    right = self._glyphs[rightIndex].name
                    # column
                    x = iconColumnWidth + (leftIndex * columnWidth)
                    y = rowHeight
                    w = columnWidth * 2
                    h = rowHeight * 3
                    if inDarkMode():
                        glyphInfoSelectionColorDarkMode.set()
                    else:
                        glyphInfoSelectionColor.set()
                    AppKit.NSRectFill(((x, y), (w, h)))
                    # kern
                    x = iconColumnWidth + (leftIndex * columnWidth) + (columnWidth / 2)
                    y = 0
                    w = columnWidth
                    h = rowHeight
                    value = kerning.metricsMachine[left, right]
                    if value > 0:
                        if inDarkMode():
                            glyphInfoKernPositiveColorDarkMode.set()
                        else:
                            glyphInfoKernPositiveColor.set()
                    elif value < 0:
                        if inDarkMode():
                            glyphInfoKernNegativeColorDarkMode.set()
                        else:
                            glyphInfoKernNegativeColor.set()
                    elif value == 0 and "exception" in kerning.metricsMachine.getPairType((left, right)):
                        if inDarkMode():
                            glyphInfoKernZeroColorDarkMode.set()
                        else:
                            glyphInfoKernZeroColor.set()
                    AppKit.NSRectFill(((x, y), (w, h)))
                    # header
                    leftType, rightType = kerning.metricsMachine.getPairType((left, right))
                    x = iconColumnWidth + (leftIndex * columnWidth)
                    y = rowHeight * 4
                    w = columnWidth
                    h = rowHeight
                    if leftType == "glyph":
                        if inDarkMode():
                            glyphInfoKernGlyphColorDarkMode.set()
                        else:
                            glyphInfoKernGlyphColor.set()
                    elif leftType == "group":
                        if inDarkMode():
                            glyphInfoKernGroupColorDarkMode.set()
                        else:
                            glyphInfoKernGroupColor.set()
                    else:
                        if inDarkMode():
                            glyphInfoKernExceptionColorDarkMode.set()
                        else:
                            glyphInfoKernExceptionColor.set()
                    AppKit.NSRectFill(((x, y), (w, h)))
                    x = iconColumnWidth + (rightIndex * columnWidth)
                    if rightType == "glyph":
                        if inDarkMode():
                            glyphInfoKernGlyphColorDarkMode.set()
                        else:
                            glyphInfoKernGlyphColor.set()
                    elif rightType == "group":
                        if inDarkMode():
                            glyphInfoKernGroupColorDarkMode.set()
                        else:
                            glyphInfoKernGroupColor.set()
                    else:
                        if inDarkMode():
                            glyphInfoKernExceptionColorDarkMode.set()
                        else:
                            glyphInfoKernExceptionColor.set()
                    AppKit.NSRectFill(((x, y), (w, h)))

            # grid
            if inDarkMode():
                glyphInfoLineColorDarkMode.set()
            else:
                glyphInfoLineColor.set()
            path = AppKit.NSBezierPath.bezierPath()
            # vertical
            x = iconColumnWidth + .5
            y1 = rowHeight
            y2 = rowHeight * 5
            for index in range(len(self._glyphs)):
                x += columnWidth
                path.moveToPoint_((x, y1))
                path.lineToPoint_((x, y2))
            # kerning
            if drawKerning:
                x = iconColumnWidth - (columnWidth / 2) + .5
                y1 = 0
                y2 = rowHeight
                for index in range(len(self._glyphs)):
                    x += columnWidth
                    path.moveToPoint_((x, y1))
                    path.lineToPoint_((x, y2))
            path.setLineWidth_(1.0)
            path.stroke()

            # glyph data
            x = iconColumnWidth
            y = rowHeight * 4
            w = columnWidth
            h = rowHeight
            paragraph = AppKit.NSMutableParagraphStyle.alloc().init()
            paragraph.setAlignment_(AppKit.NSCenterTextAlignment)
            paragraph.setLineBreakMode_(AppKit.NSLineBreakByTruncatingMiddle)
            if inDarkMode():
                textColor = AppKit.NSColor.whiteColor()
            else:
                textColor = AppKit.NSColor.blackColor()
            textAttributes = {
                AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(9.0),
                AppKit.NSForegroundColorAttributeName: textColor,
                AppKit.NSParagraphStyleAttributeName: paragraph
            }
            for glyph in self._glyphs:
                for attr in ["name", "width", "leftMargin", "rightMargin"]:
                    r = ((x, y-1), (w, h))
                    text = getattr(glyph, attr)
                    if isinstance(text, (int, float)):
                        text = str(int(round(text)))
                    if text:
                        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, textAttributes)
                        text.drawInRect_(r)
                    y -= rowHeight
                x += columnWidth
                y = rowHeight * 4

            # kerning
            if drawKerning:
                previousGlyph = None
                x = iconColumnWidth - (columnWidth / 2)
                for glyph in self._glyphs:
                    y = -1
                    w = columnWidth
                    h = rowHeight
                    glyph = glyph.name
                    if previousGlyph is not None:
                        kern = str(int(round(kerning.metricsMachine[previousGlyph, glyph])))
                        r = ((x, y), (w, h))
                        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(kern, textAttributes)
                        text.drawInRect_(r)
                    previousGlyph = glyph
                    x += columnWidth

        self._drawRequired()

    def _drawRequired(self):
        # icons
        iconWidthImage.drawAtPoint_fromRect_operation_fraction_(
            (0, rowHeight * 3), ((0, 0), (14, 14)), AppKit.NSCompositeSourceOver, 1.0)
        iconLeftImage.drawAtPoint_fromRect_operation_fraction_(
            (0, rowHeight * 2), ((0, 0), iconLeftImage.size()), AppKit.NSCompositeSourceOver, 1.0)
        iconRightImage.drawAtPoint_fromRect_operation_fraction_(
            (0, rowHeight), ((0, 0), iconRightImage.size()), AppKit.NSCompositeSourceOver, 1.0)
        iconKernImage.drawAtPoint_fromRect_operation_fraction_(
            (0, 0), ((0, 0), iconKernImage.size()), AppKit.NSCompositeSourceOver, 1.0)
        # grid
        if inDarkMode():
            glyphInfoLineColorDarkMode.set()
        else:
            glyphInfoLineColor.set()
        path = AppKit.NSBezierPath.bezierPath()
        # vertical
        x = iconColumnWidth + .5
        y1 = rowHeight
        y2 = rowHeight * 5
        path.moveToPoint_((iconColumnWidth + .5, 0))
        path.lineToPoint_((iconColumnWidth + .5, y2))
        # horizontal
        x1 = 0
        x2 = self.frame().size[0]
        y = -.5
        for index in range(5):
            y += rowHeight
            path.moveToPoint_((x1, y))
            path.lineToPoint_((x2, y))
        path.setLineWidth_(1.0)
        path.stroke()

