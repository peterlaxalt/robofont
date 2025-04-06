import AppKit
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactoryDrawingController
from mojo.UI import inDarkMode


class NoLayerGlyphCellFactoryDrawingController(GlyphCellFactoryDrawingController):

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
        


def NoLayerGlyphCellFactory(glyph, width, height, drawHeader=True, drawMetrics=False):
    obj = NoLayerGlyphCellFactoryDrawingController(
        glyph=glyph, font=glyph.font, width=width, height=height, drawHeader=drawHeader, drawMetrics=False)
    return obj.getImage()