import AppKit


def getIconMenuImage(size=(15, 16)):
    w, h = size
    sizeMultiplierX = w / 15.
    sizeMultiplierY = h / 16.
    menuIconImage = AppKit.NSImage.alloc().initWithSize_((15 * sizeMultiplierX, 16 * sizeMultiplierY))
    menuIconImage.lockFocus()
    c = 0.126
    AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(c, c, c, 1.0).set()
    arrowPath = AppKit.NSBezierPath.bezierPath()
    arrowPath.moveToPoint_((0 * sizeMultiplierX, 9 * sizeMultiplierY))
    arrowPath.lineToPoint_((0 * sizeMultiplierX, 13 * sizeMultiplierY))
    arrowPath.lineToPoint_((3 * sizeMultiplierX, 13 * sizeMultiplierY))
    arrowPath.lineToPoint_((3 * sizeMultiplierX, 16 * sizeMultiplierY))
    arrowPath.lineToPoint_((10 * sizeMultiplierX, 11 * sizeMultiplierY))
    arrowPath.lineToPoint_((3 * sizeMultiplierX, 6 * sizeMultiplierY))
    arrowPath.lineToPoint_((3 * sizeMultiplierX, 9 * sizeMultiplierY))
    arrowPath.closePath()
    arrowPath.moveToPoint_((15 * sizeMultiplierX, 3 * sizeMultiplierY))
    arrowPath.lineToPoint_((15 * sizeMultiplierX, 7 * sizeMultiplierY))
    arrowPath.lineToPoint_((12 * sizeMultiplierX, 7 * sizeMultiplierY))
    arrowPath.lineToPoint_((12 * sizeMultiplierX, 10 * sizeMultiplierY))
    arrowPath.lineToPoint_((5 * sizeMultiplierX, 5 * sizeMultiplierY))
    arrowPath.lineToPoint_((12 * sizeMultiplierX, 0 * sizeMultiplierY))
    arrowPath.lineToPoint_((12 * sizeMultiplierX, 3 * sizeMultiplierY))
    arrowPath.closePath()
    arrowPath.fill()
    AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(c, c, c, 0.25).set()
    linePath = AppKit.NSBezierPath.bezierPath()
    linePath.moveToPoint_((7.5 * sizeMultiplierX, 0 * sizeMultiplierY))
    linePath.lineToPoint_((7.5 * sizeMultiplierX, 2 * sizeMultiplierY))
    linePath.moveToPoint_((7.5 * sizeMultiplierX, 14 * sizeMultiplierY))
    linePath.lineToPoint_((7.5 * sizeMultiplierX, 16 * sizeMultiplierY))
    linePath.setLineWidth_(1.0)
    linePath.stroke()
    menuIconImage.unlockFocus()
    menuIconImage.setTemplate_(True)
    return menuIconImage
