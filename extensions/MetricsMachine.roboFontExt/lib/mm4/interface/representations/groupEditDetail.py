import AppKit
from mm4.objects.mmGroups import userFriendlyGroupName


def GroupEditDetailFactory(glyph):
    from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath
    font = glyph.font

    imageWidth = 200
    imageHeight = 220

    scale = 120.0 / font.info.unitsPerEm
    glyphLeftOffset = (imageWidth - (glyph.width * scale)) / 2

    basePath = roundedRectBezierPath(((.5, .5), (imageWidth - 1, imageHeight - 1)), 7)
    basePath.setLineWidth_(1.0)

    glyphPath = glyph.getRepresentation("defconAppKit.NSBezierPath")

    line1Path = AppKit.NSBezierPath.bezierPath()
    line1Path.moveToPoint_((1, 60.5))
    line1Path.lineToPoint_((imageWidth - 1, 60.5))
    line1Path.setLineWidth_(1.0)

    line2Path = AppKit.NSBezierPath.bezierPath()
    line2Path.moveToPoint_((1, 61.5))
    line2Path.lineToPoint_((imageWidth - 1, 61.5))
    line2Path.setLineWidth_(1.0)

    lineColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.5, 1.0)

    paragraph = AppKit.NSMutableParagraphStyle.alloc().init()
    paragraph.setAlignment_(AppKit.NSRightTextAlignment)
    paragraph.setLineBreakMode_(AppKit.NSLineBreakByCharWrapping)
    leftAttributes = {
        AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(12.0),
        AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor(),
        AppKit.NSParagraphStyleAttributeName: paragraph
    }

    paragraph = AppKit.NSMutableParagraphStyle.alloc().init()
    paragraph.setAlignment_(AppKit.NSLeftTextAlignment)
    paragraph.setLineBreakMode_(AppKit.NSLineBreakByTruncatingMiddle)
    rightAttributes = {
        AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(12.0),
        AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor(),
        AppKit.NSParagraphStyleAttributeName: paragraph
    }

    leftTitle = AppKit.NSAttributedString.alloc().initWithString_attributes_("Side 1:", leftAttributes)
    groupName = font.metricsMachine.mutableGroups.getSide2GroupForGlyph(glyph.name)
    if groupName is None:
        groupName = "None"
    leftText = AppKit.NSAttributedString.alloc().initWithString_attributes_(userFriendlyGroupName(groupName), rightAttributes)

    rightTitle = AppKit.NSAttributedString.alloc().initWithString_attributes_("Side 2:", leftAttributes)
    groupName = font.mutableGroups.getSide1GroupForGlyph(glyph.name)
    if groupName is None:
        groupName = "None"
    rightText = AppKit.NSAttributedString.alloc().initWithString_attributes_(userFriendlyGroupName(groupName), rightAttributes)

    image = AppKit.NSImage.alloc().initWithSize_((imageWidth, imageHeight))
    image.setFlipped_(True)
    image.lockFocus()

    AppKit.NSColor.colorWithCalibratedWhite_alpha_(0, .65).set()
    basePath.fill()
    lineColor.set()
    basePath.stroke()

    context = AppKit.NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    transform = AppKit.NSAffineTransform.transform()
    transform.translateXBy_yBy_(glyphLeftOffset, 85)
    transform.scaleBy_(scale)
    transform.translateXBy_yBy_(0, -font.info.descender)
    transform.concat()

    AppKit.NSColor.whiteColor().set()
    glyphPath.fill()
    context.restoreGraphicsState()

    lineColor.set()
    line1Path.stroke()
    AppKit.NSColor.colorWithCalibratedWhite_alpha_(0, .5).set()
    line2Path.stroke()

    transform = AppKit.NSAffineTransform.transform()
    transform.translateXBy_yBy_(0, 80)
    transform.scaleXBy_yBy_(1.0, -1.0)
    transform.concat()

    leftTitle.drawInRect_(((0, 30), (90, 17)))
    leftText.drawInRect_(((95, 30), (85, 17)))

    rightTitle.drawInRect_(((0, 50), (90, 17)))
    rightText.drawInRect_(((95, 50), (85, 17)))

    image.unlockFocus()
    return image
