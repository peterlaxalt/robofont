import AppKit
from objc import super
from ufo2fdk.kernFeatureWriter import side1FeaPrefix, side2FeaPrefix
from mm4.interface.colors import *
from mm4.objects.mmGroups import userFriendlyGroupName
from mojo.extensions import getExtensionDefault
from mojo.UI import inDarkMode


iconColumnWidth = 14
titleHeight = 15


class MMGroupPreviewView(AppKit.NSView):

    def initWithFont_(self, font):
        self = super(MMGroupPreviewView, self).init()
        self._font = font
        self._leftGlyphs = None
        self._leftGroup = None
        self._rightGlyphs = None
        self._rightGroup = None
        return self

    def dealloc(self):
        self._font = None
        self._leftGlyphs = None
        self._leftGroup = None
        self._rightGlyphs = None
        self._rightGroup = None
        super(MMGroupPreviewView, self).dealloc()

    def setLeftGlyphs_leftGroup_rightGlyphs_rightGroup_(self, leftGlyphs, leftGroup, rightGlyphs, rightGroup):
        self._leftGlyphs = leftGlyphs
        if leftGroup == "None":
            leftGroup = None
        self._leftGroup = leftGroup
        self._rightGlyphs = rightGlyphs
        if rightGroup == "None":
            rightGroup = None
        self._rightGroup = rightGroup
        self.flushFrame()

    def flushFrame(self):
        font = self._font
        leftWidth = 0
        if self._leftGlyphs:
            previous = None
            for glyph in self._leftGlyphs:
                glyphName = glyph.name
                kern = 0
                if previous is not None:
                    kern = font.kerning.metricsMachine[previous, glyphName]
                leftWidth += kern + glyph.width
                previous = glyphName
        rightWidth = 0
        if self._rightGlyphs:
            previous = None
            for glyph in self._rightGlyphs:
                glyphName = glyph.name
                kern = 0
                if previous is not None:
                    kern = font.kerning.metricsMachine[previous, glyphName]
                rightWidth += kern + glyph.width
                previous = glyphName

        scale = self._getScale()
        glyphBuffer = (font.info.unitsPerEm * scale) * .4

        width = iconColumnWidth + (max((leftWidth, rightWidth)) * scale) + (glyphBuffer * 2)
        height = (titleHeight * 2) + ((font.info.unitsPerEm * scale) * 2) + (glyphBuffer * 4)

        self.setFrame_(((0, 0), (width, height)))

    def _getScale(self):
        pointSize = getExtensionDefault("com.typesupply.MM4.viewSettings.general.groupPreviewPointSize")
        scale = pointSize / float(self._font.info.unitsPerEm)
        return scale

    def drawRect_(self, rect):
        invertPreviews = getExtensionDefault("com.typesupply.MM4.viewSettings.general.invertPreviews", False)
        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
            AppKit.NSColor.blackColor().set()
        else:
            AppKit.NSColor.whiteColor().set()
        AppKit.NSRectFill(self.bounds())
        width, height = self.frame().size

        font = self._font
        scale = self._getScale()
        glyphBuffer = (font.info.unitsPerEm * scale) * .4
        rowHeight = (font.info.unitsPerEm * scale) + (glyphBuffer * 2)

        # blocks
        if inDarkMode():
            glyphInfoBackgroundColorDarkMode.set()
        else:
            glyphInfoBackgroundColor.set()
        r = (((0, 0), (iconColumnWidth, height)))
        AppKit.NSRectFill(r)
        if inDarkMode():
            glyphInfoHeaderColorDarkMode.set()
        else:
            glyphInfoHeaderColor.set()
        r = (((iconColumnWidth, height - titleHeight), (width - iconColumnWidth, titleHeight)))
        AppKit.NSRectFill(r)
        r = (((iconColumnWidth, height - titleHeight - rowHeight - titleHeight), (width - iconColumnWidth, titleHeight)))
        AppKit.NSRectFill(r)

        # grid
        if inDarkMode():
            glyphInfoLineColorDarkMode.set()
        else:
            glyphInfoLineColor.set()
        path = AppKit.NSBezierPath.bezierPath()
        path.moveToPoint_((iconColumnWidth + .5, 0))
        path.lineToPoint_((iconColumnWidth + .5, height))

        path.moveToPoint_((0, height - .5))
        path.lineToPoint_((width, height - .5))
        path.moveToPoint_((0, height - titleHeight - .5))
        path.lineToPoint_((width, height - titleHeight - .5))
        path.moveToPoint_((0, height - titleHeight - rowHeight - .5))
        path.lineToPoint_((width, height - titleHeight - rowHeight - .5))
        path.moveToPoint_((0, height - titleHeight - rowHeight - titleHeight - .5))
        path.lineToPoint_((width, height - titleHeight - rowHeight - titleHeight - .5))

        path.setLineWidth_(1.0)
        path.stroke()

        # icons
        if inDarkMode():
            glyphInfoIconColorDarkMode.set()
        else:
            glyphInfoIconColor.set()
        r = (((2, height - titleHeight + 2), ((iconColumnWidth / 2) - 2, titleHeight - 5)))
        AppKit.NSRectFillUsingOperation(r, AppKit.NSCompositeSourceOver)
        r = ((((iconColumnWidth / 2), height - titleHeight - rowHeight - titleHeight + 2), ((iconColumnWidth / 2) - 2, titleHeight - 5)))
        AppKit.NSRectFillUsingOperation(r, AppKit.NSCompositeSourceOver)

        # titles
        x = iconColumnWidth + 3
        y = height - titleHeight - 1
        w = width - iconColumnWidth - 3
        h = titleHeight
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        textAttributes = {
            AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(9.0),
            AppKit.NSForegroundColorAttributeName: textColor,
        }

        if self._leftGroup is not None:
            text = "%s%s" % (side1FeaPrefix, userFriendlyGroupName(self._leftGroup))
            text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, textAttributes)
            text.drawInRect_(((x, y), (w, h)))
        y = height - titleHeight - rowHeight - titleHeight - 1
        if self._rightGroup is not None:
            text = "%s%s" % (side2FeaPrefix, userFriendlyGroupName(self._rightGroup))
            text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, textAttributes)
            text.drawInRect_(((x, y), (w, h)))

        context = AppKit.NSGraphicsContext.currentContext()
        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
            AppKit.NSColor.whiteColor().set()
        else:
            AppKit.NSColor.blackColor().set()

        # right group
        if self._rightGlyphs:
            context.saveGraphicsState()
            transform = AppKit.NSAffineTransform.transform()
            transform.translateXBy_yBy_(iconColumnWidth + glyphBuffer, glyphBuffer)
            transform.scaleBy_(scale)
            transform.translateXBy_yBy_(0, -font.info.descender)
            transform.concat()

            previous = None
            for glyph in self._rightGlyphs:
                kern = 0
                if previous is not None:
                    kern = font.kerning.metricsMachine[previous, glyph.name]
                if kern:
                    transform = AppKit.NSAffineTransform.transform()
                    transform.translateXBy_yBy_(kern, 0)
                    transform.concat()
                path = glyph.getRepresentation("defconAppKit.NSBezierPath")
                path.fill()
                transform = AppKit.NSAffineTransform.transform()
                transform.translateXBy_yBy_(glyph.width, 0)
                transform.concat()
                previous = glyph.name
            context.restoreGraphicsState()
        # left group
        if self._leftGlyphs:
            context.saveGraphicsState()
            transform = AppKit.NSAffineTransform.transform()
            transform.translateXBy_yBy_(iconColumnWidth + glyphBuffer, glyphBuffer + rowHeight + titleHeight)
            transform.scaleBy_(scale)
            transform.translateXBy_yBy_(0, -font.info.descender)
            transform.concat()

            previous = None
            for glyph in self._leftGlyphs:
                kern = 0
                if previous is not None:
                    kern = font.kerning.metricsMachine[previous, glyph.name]
                if kern:
                    transform = AppKit.NSAffineTransform.transform()
                    transform.translateXBy_yBy_(kern, 0)
                    transform.concat()
                path = glyph.getRepresentation("defconAppKit.NSBezierPath")
                path.fill()
                transform = AppKit.NSAffineTransform.transform()
                transform.translateXBy_yBy_(glyph.width, 0)
                transform.concat()
                previous = glyph.name
            context.restoreGraphicsState()
