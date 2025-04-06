import AppKit
from objc import super
import vanilla
from defconAppKit.controls.glyphSequenceEditText import GlyphSequenceEditText
from defconAppKit.controls.placardScrollView import PlacardPopUpButton
from mm4.interface.views.scrollView import MMScrollView
from mm4.interface.views.lineView import MMLineView
from mm4.interface.views.stringInfoView import MMStringInfoView
from mojo.UI import inDarkMode
from mojo.events import addObserver, removeObserver


# ---------------
# NSView subclass
# ---------------

class MMTypingView(AppKit.NSView):

    def initWithFont_(self, font):
        self = super(MMTypingView, self).init()
        self._font = font

        self._lineView = MMLineView.alloc().initWithFont_(font)
        self.addSubview_(self._lineView)

        self._infoView = None

        return self

    def setNeedsDisplay_(self, value):
        self._lineView.setNeedsDisplay_(value)
        if self._infoView is not None:
            self._infoView.setNeedsDisplay_(value)
        super(MMTypingView, self).setNeedsDisplay_(value)

    def dealloc(self):
        self._font = None
        super(MMTypingView, self).dealloc()

    def acceptsFirstResponder(self):
        return False

    def drawRect_(self, rect):
        super(MMTypingView, self).drawRect_(rect)

    # ---------------------
    # frame setting support
    # ---------------------

    def vanillaWrapper(self):
        scrollView = self.enclosingScrollView()
        superview = scrollView.superview()
        return superview.vanillaWrapper()

    def positionSubviews(self):
        scrollView = self.enclosingScrollView()
        if scrollView is None:
            return
        clipView = scrollView.contentView()
        fY = scrollView.documentView().frame().size[1]
        (vX, vY), (vW, vH) = clipView.visibleRect()

        w, h = self._lineView.frame().size
        self._lineView.setFrame_(((0, fY - h), (w, h)))
        if self._infoView is not None:
            w, h = self._infoView.frame().size
            self._infoView.setFrame_(((0, vY), (w, h)))

        self.setNeedsDisplay_(True)

    def flushFrame(self):
        # calculate the maximum width and height
        maxWidth, maxHeight = self.enclosingScrollView().contentView().visibleRect().size
        necessaryHeight = 0
        if self._infoView is not None:
            self._infoView.flushFrame()
            w, h = self._infoView.frame().size
            if w > maxWidth:
                maxWidth = w
            necessaryHeight += h
        self._lineView.flushFrame()
        w, h = self._lineView.frame().size
        if w > maxWidth:
            maxWidth = w
        if h > maxHeight:
            maxHeight = h
        # force all views to the max width
        w, h = self._lineView.frame().size
        if w < maxWidth:
            self._lineView.setFrame_(((0, 0), (w, h)))
        if self._infoView is not None:
            w, h = self._infoView.frame().size
            if w < maxWidth:
                self._infoView.setFrame_(((0, 0), (maxWidth, h)))
        if maxHeight < necessaryHeight:
            maxHeight = necessaryHeight
        # set the width of this view to the max width
        self.setFrame_(((0, 0), (maxWidth, maxHeight)))
        self.positionSubviews()

    def availableHeightForLineView(self):
        usedSpace = 0
        if self._infoView is not None:
            usedSpace += self._infoView.frame().size[1]
        totalSpace = self.enclosingScrollView().contentView().visibleRect().size[1]
        if totalSpace <= usedSpace:
            return 0
        return totalSpace - usedSpace

    def refreshFrame(self):
        self.setGlyphs_(self._lineView.getGlyphs())

    # ------------
    # external API
    # ------------

    def getFont(self):
        return self._font

    def setGlyphs_(self, glyphs):
        self._lineView.setGlyphs_selectionIndexes_(glyphs, [])
        if self._infoView is not None:
            self._infoView.setGlyphs_selectionIndexes_(glyphs, [])
        self.flushFrame()

    def getGlyphs(self):
        return self._lineView.getGlyphs()

    def getPointSize(self):
        return self._lineView.getPointSize()

    def setPointSize_(self, value):
        if self._lineView is not None:
            self._lineView.setPointSize_(value)
        self.flushFrame()

    def isInfoVisible(self):
        return self._infoView is not None

    def setShowInfo_(self, value):
        if (value and self._infoView is not None) or (not value and self._infoView is None):
            return
        if not value:
            self._infoView.removeFromSuperview()
            self._infoView = None
        else:
            self._infoView = MMStringInfoView.alloc().initWithFont_(self._font)
            self.addSubview_(self._infoView)
        self.refreshFrame()


# --------------------------------------
# vanilla ScrollView holding typing view
# --------------------------------------

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]


class TypingView(MMScrollView):

    def __init__(self, posSize, font):
        self._typingView = MMTypingView.alloc().initWithFont_(font)
        super(TypingView, self).__init__(posSize, self._typingView, autohidesScrollers=False)
        self.pointSizes = ["Auto"] + [str(i) for i in pointSizes]
        self.buildPlacard()
        self.setPlacard(self.placard)
        font.kerning.addObserver(self, "_fontChanged", "Kerning.Changed")
        font.addObserver(self, "_fontChanged", "Font.ReloadedGlyphs")
        addObserver(self, "updatePointSizeBackgroundColor", "appearanceChanged")
        addObserver(self, "updateTypingViewColors", "com.typesupply.MM4.invertPreviewsSettingDidChange")

    def _breakCycles(self):
        font = self._typingView.getFont()
        if font is not None:
            font.kerning.removeObserver(self, "Kerning.Changed")
            font.removeObserver(self, "Font.ReloadedGlyphs")
        self.unsubscribeGlyphs()
        removeObserver(self, "appearanceChanged")
        removeObserver(self, "com.typesupply.MM4.invertPreviewsSettingDidChange")
        super(TypingView, self)._breakCycles()

    def updateTypingViewColors(self, notification):
        self.update()

    def subscribeGlyphs(self):
        done = set()
        for glyph in self._typingView.getGlyphs():
            if glyph in done:
                continue
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            done.add(glyph)

    def unsubscribeGlyphs(self):
        done = set()
        for glyph in self._typingView.getGlyphs():
            if glyph in done:
                continue
            glyph.removeObserver(self, "Glyph.Changed")
            done.add(glyph)

    def buildPlacard(self):
        placardW = 55
        placardH = 16
        self.placard = vanilla.Group((0, 0, placardW, placardH))
        self.placard.pointSizeButton = PlacardPopUpButton((0, 0, placardW, placardH),
            self.pointSizes, callback=self.placardPointSizeSelection, sizeStyle="mini")
        self.updatePointSizeBackgroundColor(None)

    def updatePointSizeBackgroundColor(self, info):
        # Unwrap from try/except once RoboFont 4.5p is released.
        try:
            if inDarkMode():
                self.placard.pointSizeButton.setBackgroundColor(AppKit.NSColor.blackColor())
            else:
                self.placard.pointSizeButton.setBackgroundColor(AppKit.NSColor.whiteColor())
        except:
            pass

    def placardPointSizeSelection(self, sender):
        value = self.pointSizes[sender.get()]
        if value == "Auto":
            value = None
        else:
            value = int(value)
        self.setPointSize(value)

    def update(self):
        self._typingView.setNeedsDisplay_(True)

    def set(self, glyphs):
        self.unsubscribeGlyphs()
        self._typingView.setGlyphs_(glyphs)
        self.subscribeGlyphs()

    def getPointSize(self):
        return self._typingView.getPointSize()

    def setPointSize(self, value):
        self._typingView.setPointSize_(value)

    def isInfoVisible(self):
        return self._typingView.isInfoVisible()

    def showInfo(self, value):
        self._typingView.setShowInfo_(value)

    # --------------------
    # Notification Support
    # --------------------

    def _fontChanged(self, notification):
        self._typingView.flushFrame()
        self._typingView.setNeedsDisplay_(True)

    def _glyphChanged(self, notification):
        self._typingView.flushFrame()
        self._typingView.setNeedsDisplay_(True)


class PseudoFeatureTypingView(TypingView):

    def __init__(self, posSize, font, suffixes):
        self.font = font
        self.suffixes = suffixes
        self.currentSuffix = suffixes[0]
        self._rawGlyphNames = []
        super(PseudoFeatureTypingView, self).__init__(posSize, font)
        addObserver(self, "updateSuffixBackgroundColor", "appearanceChanged")

    def _breakCycles(self):
        self.font = None
        removeObserver(self, "appearanceChanged")
        super(PseudoFeatureTypingView, self)._breakCycles()

    def buildPlacard(self):
        super(PseudoFeatureTypingView, self).buildPlacard()
        placardX, placardY, placardW, placardH = self.placard.getPosSize()
        buttonW = 90
        self.placard.suffixButton = PlacardPopUpButton((placardW, 0, buttonW, placardH),
            self.suffixes, callback=self.placardSuffixSelection, sizeStyle="mini")
        self.placard.setPosSize((placardX, placardY, placardW + buttonW, placardH))
        self.updateSuffixBackgroundColor(None)

    def updateSuffixBackgroundColor(self, info):
        # Unwrap from try/except once RoboFont 4.5p is released.
        try:
            if inDarkMode():
                self.placard.suffixButton.setBackgroundColor(AppKit.NSColor.blackColor())
            else:
                self.placard.suffixButton.setBackgroundColor(AppKit.NSColor.whiteColor())
        except:
            pass

    def placardSuffixSelection(self, sender):
        index = sender.get()
        self.currentSuffix = self.suffixes[index]
        self._internalSet()

    def set(self, glyphs):
        self._rawGlyphNames = [glyph.name for glyph in glyphs]
        self._internalSet()

    def _internalSet(self):
        glyphNames = self._rawGlyphNames
        # apply the suffix where possible
        suffix = self.currentSuffix
        if suffix == ApplyNoSuffixMenuItemTitle:
            suffix = None
        if suffix:
            _glyphNames = glyphNames
            glyphNames = []
            for glyphName in _glyphNames:
                applied = glyphName + "." + suffix
                if applied in self.font:
                    glyphName = applied
                glyphNames.append(glyphName)
        # convert to glyphs
        glyphs = [self.font[glyphName] for glyphName in glyphNames if glyphName in self.font]
        # set the glyphs
        super(PseudoFeatureTypingView, self).set(glyphs)


# ---------------------
# complete typing group
# ---------------------

ApplyNoSuffixMenuItemTitle = "No Feature"


class TypingGroup(vanilla.Group):

    def __init__(self, posSize, font, pseudoFeatures=False):
        self.font = font
        super(TypingGroup, self).__init__(posSize)

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # todo:
        # update features on glyphset change
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        posSize = (0, 32, -0, -0)
        suffixes = None
        if pseudoFeatures:
            suffixes = set([glyphName.split(".", 1)[1] for glyphName in self.font.keys() if "." in glyphName and glyphName.split(".", 1)[1] and glyphName.split(".")[0]])
            suffixes = list(sorted(suffixes))
        if suffixes:
            suffixes = [ApplyNoSuffixMenuItemTitle, AppKit.NSMenuItem.separatorItem()] + suffixes
            typingView = PseudoFeatureTypingView(posSize, self.font, suffixes)
        else:
            typingView = TypingView((0, 37, -0, -0), self.font)

        typingView.frameAdjustments = (-1, 0, 0, 1)
        typingView.showInfo(True)
        self.typingView = typingView

        self.textEntry = GlyphSequenceEditText((10, 5, -10, 19), font=font, sizeStyle="small", callback=self.textEntryCallback)

    def _breakCycles(self):
        self.font = None
        super(TypingGroup, self)._breakCycles()

    def textEntryCallback(self, sender):
        glyphs = sender.get()
        self.typingView.set(glyphs)

    def isInfoVisible(self):
        return self.typingView.isInfoVisible()

    def showInfo(self, value):
        self.typingView.showInfo(value)

    def toggleGlyphInfo(self):
        if self.isInfoVisible():
            self.showInfo(False)
        else:
            self.showInfo(True)
