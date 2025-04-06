import AppKit
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactoryDrawingController
from mojo.UI import inDarkMode


class GroupIndicatingGlyphCellFactoryDrawingController(GlyphCellFactoryDrawingController):

    def drawCellGlyph(self):
        if inDarkMode():
            AppKit.NSColor.whiteColor().set()
        else:
            AppKit.NSColor.blackColor().set()
        path = self.glyph.getRepresentation("defconAppKit.NSBezierPath")
        path.fill()

    def drawCellBackground(self, rect):
        font = self.font
        glyph = self.glyph
        (xMin, yMin), (width, height) = rect
        half = width / 2.0
        # Draw background color
        if inDarkMode():
            AppKit.NSColor.blackColor().set()
            AppKit.NSRectFillUsingOperation(((0, 0), (width, height)), AppKit.NSCompositeSourceOver)
        if hasattr(font.metricsMachine, "mutableGroups"):
            groups = font.metricsMachine.mutableGroups
            side1Group = groups.metricsMachine.getSide1GroupForGlyph(glyph.name)
            side2Group = groups.metricsMachine.getSide2GroupForGlyph(glyph.name)
            if side1Group or side2Group:
                # Draw group color
                if side1Group:
                    r, g, b, a = groups.metricsMachine.getColorForGroup(side1Group)
                    AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a).set()
                    AppKit.NSRectFillUsingOperation(((half, 4), (half - 4, height - 7)), AppKit.NSCompositeSourceOver)
                if side2Group:
                    r, g, b, a = groups.metricsMachine.getColorForGroup(side2Group)
                    AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a).set()
                    AppKit.NSRectFillUsingOperation(((3, 4), (half - 3, height - 7)), AppKit.NSCompositeSourceOver)

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


def GroupIndicatingGlyphCellFactory(glyph, width, height):
    obj = GroupIndicatingGlyphCellFactoryDrawingController(
        glyph=glyph, font=glyph.font, width=width, height=height, drawHeader=True, drawMetrics=False)
    return obj.getImage()
