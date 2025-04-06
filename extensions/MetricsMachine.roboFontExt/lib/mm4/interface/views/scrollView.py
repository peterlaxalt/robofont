import AppKit
from defconAppKit.controls.placardScrollView import DefconAppKitPlacardNSScrollView, PlacardScrollView
from objc import super


class MMNSScrollView(DefconAppKitPlacardNSScrollView):

    def reflectScrolledClipView_(self, clipView):
        view = self.documentView()
        if view:
            view.positionSubviews()
        super(MMNSScrollView, self).reflectScrolledClipView_(clipView)

    def setFrame_(self, frame):
        super(MMNSScrollView, self).setFrame_(frame)
        view = self.documentView()
        if view:
            view.flushFrame()


class MMBaseView(AppKit.NSView):

    def positionSubviews(self):
        pass

    def flushFrame(self):
        pass


class MMScrollView(PlacardScrollView):

    nsScrollViewClass = MMNSScrollView
