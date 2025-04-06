import AppKit
import vanilla
from mojo.UI import inDarkMode


if inDarkMode():
    controlColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.65, 1)
    controlShadow = AppKit.NSShadow.alloc().init()
    controlShadow.setShadowColor_(AppKit.NSColor.colorWithCalibratedWhite_alpha_(0, .25))
else:
    controlColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.35, 1)
    controlShadow = AppKit.NSShadow.alloc().init()
    controlShadow.setShadowColor_(AppKit.NSColor.colorWithCalibratedWhite_alpha_(1, .25))
controlShadow.setShadowBlurRadius_(1.0)
controlShadow.setShadowOffset_((0, -1.0))


class MMPairListProgressIndicatorView(AppKit.NSView):

    def setValue_(self, value):
        self._value = value
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        if hasattr(self, "_value"):
            value = self._value
        else:
            value = 0

        (boundsX, boundsY), (boundsW, boundsH) = self.bounds()

        lineY = 3.5
        lineW = boundsW - 6
        lineX1 = boundsX + 3
        lineX2 = boundsX + boundsW - 3
        lineCenterX = boundsX + int(round(lineW / 2.0))

        # lines
        linePath = AppKit.NSBezierPath.bezierPath()
        linePath.setLineWidth_(1.0)
        linePath.moveToPoint_((lineX1, lineY))
        linePath.lineToPoint_((lineX2, lineY))
        linePath.moveToPoint_((lineX1 - .5, lineY + 2))
        linePath.lineToPoint_((lineX1 - .5, lineY - 2))
        linePath.moveToPoint_((lineX2 - .5, lineY + 2))
        linePath.lineToPoint_((lineX2 - .5, lineY - 2))
        linePath.moveToPoint_((lineCenterX - .5, lineY + 2))
        linePath.lineToPoint_((lineCenterX - .5, lineY - 2))

        # knob
        knobCenterX = lineX1 + int(round(lineW * value))
        knobX1 = knobCenterX - 3.5
        knobX2 = knobCenterX + 3.5
        knobY1 = lineY + 4
        knobY2 = lineY + 8.5

        knobPath = AppKit.NSBezierPath.bezierPath()
        knobPath.moveToPoint_((knobCenterX, knobY1))
        knobPath.lineToPoint_((knobX1, knobY2))
        knobPath.lineToPoint_((knobX2, knobY2))
        knobPath.lineToPoint_((knobCenterX, knobY1))

        # paint
        controlColor.set()
        controlShadow.set()
        linePath.stroke()
        knobPath.fill()


class PairListProgressIndicator(vanilla.VanillaBaseObject):

    frameAdjustments = (-3, -1, 6, 1)

    def __init__(self, posSize):
        self._setupView(MMPairListProgressIndicatorView, posSize)
        self._count = 0

    def setCount(self, value):
        self._count = value
        self._nsObject.setValue_(0)

    def set(self, value):
        if self._count == 0:
            percent = 0
        else:
            percent = value / float(self._count)
        self._nsObject.setValue_(percent)
