import AppKit
from objc import super, pyobjc_unicode, python_method
import vanilla
from mm4.interface.colors import *
from mojo.UI import inDarkMode


class MMGroupStackView(AppKit.NSView):

    def init(self):
        self = super(MMGroupStackView, self).init()
        self._visibleSide = "side1"
        self._glyphs = []

        self._verticalBuffer = 20
        if inDarkMode():
            self._backgroundColor = AppKit.NSColor.blackColor()
            self._oneGlyphColor = AppKit.NSColor.whiteColor()
            self._multipleGlyphsColor = groupStackViewGlyphColorDarkMode
            self._maskColor = groupStackViewMaskColorDarkMode
        else:
            self._backgroundColor = AppKit.NSColor.whiteColor()
            self._oneGlyphColor = AppKit.NSColor.blackColor()
            self._multipleGlyphsColor = groupStackViewGlyphColor
            self._maskColor = groupStackViewMaskColor

        return self

    def dealloc(self):
        self._glyphs = []
        super(MMGroupStackView, self).dealloc()

    def setVerticalBuffer_(self, value):
        self._verticalBuffer = value

    def setBackgroundColor_(self, color):
        self._backgroundColor = color

    def setOneGlyphColor_(self, color):
        self._oneGlyphColor = color

    def setMultipleGlyphsColor_(self, color):
        self._multipleGlyphsColor = color

    def setMaskColor_(self, color):
        self._maskColor = color

    def setGlyphs_(self, glyphs):
        self._glyphs = list(glyphs)
        self.setNeedsDisplay_(True)

    def getGlyphs(self):
        return self._glyphs

    def setVisibleSide_(self, side):
        self._visibleSide = side
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        if self._backgroundColor is not None:
            self._backgroundColor.set()
            AppKit.NSRectFill(self.bounds())

        w, h = self.frame().size
        half = w / 2
        if self._visibleSide == "side1":
            x = half
        else:
            x = 0

        # draw the glyphs
        if self._glyphs:
            context = AppKit.NSGraphicsContext.currentContext()
            context.saveGraphicsState()

            glyphs = self._glyphs
            font = glyphs[0].getParent()

            verticalBuffer = self._verticalBuffer
            scale = (h - (verticalBuffer * 2)) / font.info.unitsPerEm

            # set the glyph color
            if len(glyphs) < 2:
                self._oneGlyphColor.set()
            else:
                self._multipleGlyphsColor.set()

            # shift into position
            averageWidth = sum([glyph.width for glyph in glyphs]) / len(glyphs)
            xOffset = ((w * (1.0 / scale)) - averageWidth) / 2
            left = xOffset
            right = xOffset + averageWidth

            transform = AppKit.NSAffineTransform.transform()
            transform.translateXBy_yBy_(0, verticalBuffer)
            transform.scaleBy_(scale)
            transform.translateXBy_yBy_(xOffset, -font.info.descender)
            transform.concat()

            # draw each glyph
            for glyph in glyphs:
                if self._visibleSide == "side1":
                    shift = 0
                else:
                    shift = averageWidth - glyph.width
                if shift:
                    transform = AppKit.NSAffineTransform.transform()
                    transform.translateXBy_yBy_(shift, 0)
                    transform.concat()
                path = glyph.getRepresentation("defconAppKit.NSBezierPath")
                path.fill()
                if shift:
                    transform.invert()
                    transform.concat()

            context.restoreGraphicsState()

        # draw the mask
        self._maskColor.set()
        AppKit.NSRectFillUsingOperation(((x, 0), (half, h)), AppKit.NSCompositeSourceOver)

    # ----
    # drop
    # ----

    def draggingEntered_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return AppKit.NSDragOperationNone
        return AppKit.NSDragOperationCopy

    def draggingUpdated_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return AppKit.NSDragOperationNone
        return AppKit.NSDragOperationCopy

    def draggingExited_(self, sender):
        return None

    def prepareForDragOperation_(self, sender):
        return self._handleDrop(sender, True)

    def performDragOperation_(self, sender):
        return self._handleDrop(sender, False)

    @python_method
    def _handleDrop(self, draggingInfo, isProposal):
        draggingSource = draggingInfo.draggingSource()
        sourceForCallback = draggingSource
        if hasattr(draggingSource, "vanillaWrapper") and getattr(draggingSource, "vanillaWrapper") is not None:
            sourceForCallback = getattr(draggingSource, "vanillaWrapper")()
        # drag from self
        if draggingSource == self:
            return AppKit.NSDragOperationNone
        # drag from same window
        if draggingSource.window() != self.window():
            return AppKit.NSDragOperationNone
        # unpack indexes and convert to glyphs
        pboard = draggingInfo.draggingPasteboard()
        data = pboard.propertyListForType_("DefconAppKitSelectedGlyphIndexesPboardType")
        if isinstance(data, (AppKit.NSString, pyobjc_unicode)):
            data = data.propertyList()
        indexes = [int(i) for i in data]
        if hasattr(draggingSource, "vanillaWrapper") and getattr(draggingSource, "vanillaWrapper") is not None:
            v = draggingSource.vanillaWrapper()
            glyphs = [v[i] for i in indexes]
        elif isinstance(draggingSource, vanilla.VanillaBaseObject):
            glyphs = [draggingSource[i] for i in indexes]
        else:
            glyphs = draggingSource.getGlyphsAtIndexes_(indexes)
        # call the callback
        dropInformation = dict(isProposal=isProposal, data=glyphs, source=sourceForCallback)
        return self.vanillaWrapper()._proposeDrop(dropInformation)


class GroupStackView(vanilla.VanillaBaseObject):

    def __init__(self, posSize, visibleSide="side1", dropCallback=None):
        self._setupView(MMGroupStackView, posSize)
        self._nsObject.setVisibleSide_(visibleSide)
        self._dropCallback = dropCallback
        if dropCallback is not None:
            self._nsObject.registerForDraggedTypes_(["DefconAppKitSelectedGlyphIndexesPboardType"])

    def _breakCycles(self):
        if self._nsObject is not None:
            self._unsubscribeFromGlyphs()
        self._nsObject = None
        super(GroupStackView, self)._breakCycles()

    def getNSView(self):
        return self._nsObject

    def _proposeDrop(self, dropInfo):
        if self._dropCallback is not None:
            return self._dropCallback(self, dropInfo)
        return False

    def set(self, glyphs):
        self._unsubscribeFromGlyphs()
        self._subscribeToGlyphs(glyphs)
        self._nsObject.setGlyphs_(glyphs)

    def setVisibleSide(self, side):
        self._nsObject.setVisibleSide_(side)

    # ---------------------------------
    # glyph change notification support
    # ---------------------------------

    def _subscribeToGlyphs(self, glyphs):
        for glyph in glyphs:
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")

    def _unsubscribeFromGlyphs(self):
        done = set()
        for glyph in self._nsObject.getGlyphs():
            if glyph in done:
                continue
            glyph.removeObserver(self, "Glyph.Changed")
            done.add(glyph)

    def _glyphChanged(self, notification):
        self._nsObject.setNeedsDisplay_(True)
