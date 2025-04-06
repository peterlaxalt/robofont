import AppKit
from objc import super
from mm4.interface.colors import *
from mojo.UI import inDarkMode
from mojo.extensions import getExtensionDefault


class MMLineView(AppKit.NSView):

    def initWithFont_(self, font):
        self = super(MMLineView, self).init()
        self._font = font
        self._glyphs = []
        self._selectionIndexes = []

        self._pointSize = None
        self._scale = 1.0
        self._glyphBuffer = 0
        self._showGroupStack = True
        self._showPairSelectionIndicators = True
        self._showFirstResponderIndicator = False

        return self

    def dealloc(self):
        self._font = None
        self._glyphs = []
        super(MMLineView, self).dealloc()

    def isFlipped(self):
        return True

    # ---------------------
    # frame setting support
    # ---------------------

    def flushFrame(self):
        font = self._font
        availableHeight = self.superview().availableHeightForLineView()
        if font is None or availableHeight <= 0:
            self.setFrame_(((0, 0), (0, 0)))
            return
        if self._pointSize is None:
            scale = self._scale = (availableHeight * .7) / font.info.unitsPerEm
            glyphBuffer = self._glyphBuffer = (availableHeight * .3) / 2
            height = availableHeight
        else:
            scale = self._scale = self._pointSize / float(font.info.unitsPerEm)
            glyphBuffer = self._glyphBuffer = self._pointSize * .2
            height = (font.info.unitsPerEm * scale) + (glyphBuffer * 2)
        width = 0
        previous = None
        for glyph in self._glyphs:
            if previous is not None:
                width += font.kerning.metricsMachine[previous, glyph.name]
            previous = glyph.name
            width += glyph.width
        width = (width * scale) + (glyphBuffer * 2)
        self.setFrame_(((0, 0), (width, height)))

    # ------------
    # external API
    # ------------

    def setShowFirstResponderIndicator_(self, value):
        self._showFirstResponderIndicator = value
        self.setNeedsDisplay_(True)

    def getGlyphs(self):
        return self._glyphs

    def setGlyphs_selectionIndexes_(self, glyphs, selectionIndexes):
        self._glyphs = glyphs
        self._selectionIndexes = selectionIndexes

    def getPointSize(self):
        value = self._pointSize
        if value is None:
            value = self._font.info.unitsPerEm * self._scale
        return value

    def setPointSize_(self, value):
        self._pointSize = value

    def isGroupStackVisible(self):
        return self._showGroupStack

    def setShowGroupStack_(self, value):
        self._showGroupStack = value
        self.setNeedsDisplay_(True)

    # -------
    # drawing
    # -------

    def drawRect_(self, rect):
        invertPreviews = getExtensionDefault("com.typesupply.MM4.viewSettings.general.invertPreviews", False)
        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
            AppKit.NSColor.blackColor().set()
        else:
            AppKit.NSColor.whiteColor().set()
        AppKit.NSRectFill(self.bounds())

        font = self._font
        groups = self._font.groups

        scale = self._scale
        inverseScale = 1.0 / scale

        transform = AppKit.NSAffineTransform.transform()
        transform.translateXBy_yBy_(self._glyphBuffer, self._glyphBuffer)
        transform.scaleBy_(scale)
        transform.concat()

        flipTransform = AppKit.NSAffineTransform.transform()
        flipTransform.translateXBy_yBy_(0, font.info.unitsPerEm)
        flipTransform.scaleXBy_yBy_(1.0, -1.0)
        flipTransform.translateXBy_yBy_(0, -font.info.descender)
        flipTransform.concat()
        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
            black = AppKit.NSColor.whiteColor()
        else:
            black = AppKit.NSColor.blackColor()
        black.set()
        previous = None
        for index, glyph in enumerate(self._glyphs):
            # handle kern
            kern = 0
            if previous is not None:
                kern = font.kerning.metricsMachine[previous, glyph.name]
            previous = glyph.name
            if kern:
                transform = AppKit.NSAffineTransform.transform()
                transform.translateXBy_yBy_(kern, 0)
                transform.concat()
            # draw group stack
            if self._showGroupStack:
                # left
                if (index, index + 1) in self._selectionIndexes:
                    groupName = groups.metricsMachine.getSide1GroupForGlyph(glyph.name)
                    if groupName is not None:
                        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                            editViewGlyphStackColorDarkMode.set()
                        else:
                            editViewGlyphStackColor.set()
                        group = groups[groupName]
                        for glyphName in group:
                            if glyphName == glyph.name:
                                continue
                            otherGlyph = font[glyphName]
                            if otherGlyph.width != glyph.width:
                                diff = glyph.width - otherGlyph.width
                                transform = AppKit.NSAffineTransform.transform()
                                transform.translateXBy_yBy_(diff, 0)
                                transform.concat()
                            path = otherGlyph.getRepresentation("defconAppKit.NSBezierPath")
                            path.fill()
                            if otherGlyph.width != glyph.width:
                                transform.invert()
                                transform.concat()
                        black.set()
                # right
                if (index - 1, index) in self._selectionIndexes:
                    groupName = groups.metricsMachine.getSide2GroupForGlyph(glyph.name)
                    if groupName is not None:
                        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                            editViewGlyphStackColorDarkMode.set()
                        else:
                            editViewGlyphStackColor.set()
                        group = groups[groupName]
                        for glyphName in group:
                            if glyphName == glyph.name:
                                continue
                            otherGlyph = font[glyphName]
                            path = otherGlyph.getRepresentation("defconAppKit.NSBezierPath")
                            path.fill()
                        black.set()
            # selection indicators
            if self._showPairSelectionIndicators and self._showFirstResponderIndicator:
                left = (index, index + 1)
                right = (index - 1, index)
                if left in self._selectionIndexes or right in self._selectionIndexes:
                    glyphWidth = glyph.width
                    halfWidth = glyph.width / 2
                    lineWidth = 4 * inverseScale
                    y = font.info.descender - lineWidth - (font.info.unitsPerEm * .05)
                    if left in self._selectionIndexes:
                        l = self._glyphs[index].name
                        r = self._glyphs[index + 1].name
                        pairType = font.kerning.metricsMachine.getPairType((l, r))[0]
                        kern = font.kerning.metricsMachine[l, r]
                        if pairType == "exception":
                            if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                                editViewSelectionExceptionColorDarkMode.set()
                            else:
                                editViewSelectionExceptionColor.set()
                        elif pairType == "group":
                            if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                                editViewSelectionGroupColorDarkMode.set()
                            else:
                                editViewSelectionGroupColor.set()
                        else:
                            if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                                editViewSelectionGlyphColorDarkMode.set()
                            else:
                                editViewSelectionGlyphColor.set()
                        x1 = halfWidth
                        x2 = glyphWidth + kern
                        path = AppKit.NSBezierPath.bezierPath()
                        path.moveToPoint_((x1, y))
                        path.lineToPoint_((x2, y))
                        path.setLineWidth_(lineWidth)
                        path.stroke()
                    if right in self._selectionIndexes:
                        l = self._glyphs[index - 1].name
                        r = self._glyphs[index].name
                        pairType = font.kerning.metricsMachine.getPairType((l, r))[1]
                        kern = font.kerning.metricsMachine[l, r]
                        if pairType == "exception":
                            if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                                editViewSelectionExceptionColorDarkMode.set()
                            else:
                                editViewSelectionExceptionColor.set()
                        elif pairType == "group":
                            if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                                editViewSelectionGroupColorDarkMode.set()
                            else:
                                editViewSelectionGroupColor.set()
                        else:
                            if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
                                editViewSelectionGlyphColorDarkMode.set()
                            else:
                                editViewSelectionGlyphColor.set()
                        x1 = 0
                        x2 = halfWidth
                        path = AppKit.NSBezierPath.bezierPath()
                        path.moveToPoint_((x1, y))
                        path.lineToPoint_((x2, y))
                        path.setLineWidth_(lineWidth)
                        path.stroke()
                    black.set()
            # regular drawing
            path = glyph.getRepresentation("defconAppKit.NSBezierPath")
            path.fill()
            transform = AppKit.NSAffineTransform.transform()
            transform.translateXBy_yBy_(glyph.width, 0)
            transform.concat()

