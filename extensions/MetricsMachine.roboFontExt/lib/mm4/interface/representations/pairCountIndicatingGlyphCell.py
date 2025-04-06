import AppKit
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactoryDrawingController
from mm4.interface.colors import *
from mojo.UI import inDarkMode


groupGlow = AppKit.NSShadow.alloc().init()
groupGlow.setShadowColor_(glyphCountCellGroupGlowColor)
groupGlow.setShadowBlurRadius_(2.0)
groupGlow.setShadowOffset_((0, 0))

glyphGlow = AppKit.NSShadow.alloc().init()
glyphGlow.setShadowColor_(glyphCountCellGlyphGlowColor)
glyphGlow.setShadowBlurRadius_(2.0)
glyphGlow.setShadowOffset_((0, 0))

exceptionGlow = AppKit.NSShadow.alloc().init()
exceptionGlow.setShadowColor_(glyphCountCellExceptionGlowColor)
exceptionGlow.setShadowBlurRadius_(2.0)
exceptionGlow.setShadowOffset_((0, 0))


class PairCountIndicatingGlyphCellFactoryDrawingController(GlyphCellFactoryDrawingController):

    def drawCellGlyph(self):
        if inDarkMode():
            AppKit.NSColor.whiteColor().set()
        else:
            AppKit.NSColor.blackColor().set()
        path = self.glyph.getRepresentation("defconAppKit.NSBezierPath")
        path.fill()

    def drawCellBackground(self, rect):
        if inDarkMode():
            AppKit.NSColor.blackColor().set()
            AppKit.NSRectFill(rect)

    def drawCellHeaderBackground(self, rect):
        (xMin, yMin), (width, height) = rect
        if inDarkMode():
            cellHeaderBaseColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(0, 1.0)
            cellHeaderHighlightColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.02, 1.0)
            cellHeaderLineColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(1, .2)
        else:
            cellHeaderBaseColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.968, 1.0)
            cellHeaderHighlightColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.98, 1.0)
            cellHeaderLineColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(0, .2)
        # background
        try:
            gradient = AppKit.NSGradient.alloc().initWithColors_([cellHeaderHighlightColor, cellHeaderBaseColor])
            gradient.drawInRect_angle_(rect, 90)
        except NameError:
            cellHeaderBaseColor.set()
            AppKit.NSRectFill(rect)
        # bottom line
        cellHeaderLineColor.set()
        bottomPath = AppKit.NSBezierPath.bezierPath()
        bottomPath.moveToPoint_((xMin, yMin + height - .5))
        bottomPath.lineToPoint_((xMin + width, yMin + height - .5))
        bottomPath.setLineWidth_(1.0)
        bottomPath.stroke()

    def drawCellHeaderText(self, rect):
        paragraph = AppKit.NSMutableParagraphStyle.alloc().init()
        paragraph.setAlignment_(AppKit.NSCenterTextAlignment)
        paragraph.setLineBreakMode_(AppKit.NSLineBreakByTruncatingMiddle)
        if inDarkMode():
            color = AppKit.NSColor.whiteColor()
        else:
            color = AppKit.NSColor.blackColor()
        attributes = {
            AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(10.0),
            AppKit.NSForegroundColorAttributeName: color,
            AppKit.NSParagraphStyleAttributeName: paragraph,
        }
        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(self.glyph.name, attributes)
        text.drawInRect_(rect)

    def drawCellForeground(self, rect):
        glyph = self.glyph.metricsMachine.tempGlyphWrapper
        width = rect[1][0] - 5
        width = (width / 2.0) - 1
        height = 14
        left1 = 2
        left2 = left1 + 2 + width
        top1 = 2
        top2 = 18
        top3 = 34

        # group pairs
        rect = ((left1, top1), (width, height))
        drawPill(rect, glyph.side2GroupPairCount, glyphCountCellGroupBackgroundColor, groupGlow, "left")
        rect = ((left2, top1), (width, height))
        drawPill(rect, glyph.side1GroupPairCount, glyphCountCellGroupBackgroundColor, groupGlow, "right")
        # glyph pairs
        rect = ((left1, top2), (width, height))
        drawPill(rect, glyph.side2GlyphPairCount, glyphCountCellGlyphBackgroundColor, glyphGlow, "left")
        rect = ((left2, top2), (width, height))
        drawPill(rect, glyph.side1GlyphPairCount, glyphCountCellGlyphBackgroundColor, glyphGlow, "right")
        # exceptions
        rect = ((left1, top3), (width, height))
        drawPill(rect, glyph.side2ExceptionPairCount, glyphCountCellExceptionBackgroundColor, exceptionGlow, "left")
        rect = ((left2, top3), (width, height))
        drawPill(rect, glyph.side1ExceptionPairCount, glyphCountCellExceptionBackgroundColor, exceptionGlow, "right")



textAttributes = {
    AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(9.0),
    AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
}


def drawPill(rect, count, backgroundColor, glow, align):
    ((x, y), (w, h)) = rect
    radius = h / 2.0


    attrs = dict(textAttributes)
    attrs[AppKit.NSShadowAttributeName] = glow

    text = str(count)
    text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, attrs)
    textRect = text.boundingRectWithSize_options_((w, h), 0)
    (textX, textY), (textW, textH) = textRect

    if align == "right":
        textRect = ((x + w - textW - radius, y), (textW, h))
    else:
        textRect = ((x + radius, y), (textW, textH))

    backgroundColor.set()
    path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
    path.fill()

    # draw with glow
    text.drawInRect_(textRect)

    # draw without glow
    text = str(count)
    text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, textAttributes)
    text.drawInRect_(textRect)


def PairCountIndicatingGlyphCellFactory(glyph, width, height):
    obj = PairCountIndicatingGlyphCellFactoryDrawingController(
        glyph=glyph, font=glyph.font, width=width, height=height, drawHeader=True, drawMetrics=False)
    return obj.getImage()
