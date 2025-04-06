import AppKit
from objc import super
from mm4.interface.colors import conflictResolutionListFollowGroupPillColor
from mojo.UI import inDarkMode


textAttributes = {
    AppKit.NSFontAttributeName: AppKit.NSFont.fontWithName_size_("Helvetica Bold", 12.0),
    AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
}


class CountListCell(AppKit.NSActionCell):

    def initWithColor_(self, color):
        self = super(CountListCell, self).init()
        self._color = color
        self._cellTextAttributes = dict(textAttributes)
        return self

    def drawWithFrame_inView_(self, frame, view):
        row = view.selectedRow()
        columnCount = len(view.tableColumns())
        frames = [view.frameOfCellAtColumn_row_(i, row) for i in range(columnCount)]
        selected = frame in frames

        (x, y), (w, h) = frame
        y += 1
        h -= 2

        text = self.title()
        if text == '0':
            mainColor = conflictResolutionListFollowGroupPillColor
        else:
            mainColor = self._color

        if selected:
            self._cellTextAttributes[AppKit.NSForegroundColorAttributeName] = mainColor
            if inDarkMode():
                pillColor = AppKit.NSColor.blackColor()
            else:
                pillColor = AppKit.NSColor.whiteColor()
        else:
            if inDarkMode():
                self._cellTextAttributes[AppKit.NSForegroundColorAttributeName] = AppKit.NSColor.blackColor()
            else:
                self._cellTextAttributes[AppKit.NSForegroundColorAttributeName] = AppKit.NSColor.whiteColor()
            pillColor = mainColor

        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, self._cellTextAttributes)
        textRect = text.boundingRectWithSize_options_((w, h), 0)
        (textX, textY), (textW, textH) = textRect

        pillColor.set()
        path = AppKit.NSBezierPath.bezierPath()
        radius = h / 2.0
        path.appendBezierPathWithOvalInRect_(((x, y), (h, h)))
        path.appendBezierPathWithOvalInRect_(((x + textW - 1, y), (h, h)))
        path.appendBezierPathWithRect_(((x + radius, y), (textW - 1, h)))
        path.fill()
        text.drawInRect_(((x + radius, y), (textW, textH)))
