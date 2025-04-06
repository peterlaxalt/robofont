import AppKit
from objc import super
import vanilla
from defconAppKit.controls.glyphNameComboBox import GlyphNameComboBox
from defconAppKit.controls.placardScrollView import PlacardPopUpButton

from mm4.interface.views.scrollView import MMScrollView
from mm4.interface.views.pairListProgressIndicator import PairListProgressIndicator
from mm4.interface.views.typingGroup import MMTypingView
from mm4.interface.views.groupPreviewView import MMGroupPreviewView
from mm4.interface.views.makeExceptionView import MakeExceptionView
from mm4.interface.formatters import NumberEditText

from mojo import events
from mojo.extensions import getExtensionDefault
from mojo.UI import inDarkMode
from lib.tools.debugTools import ClassNameIncrementer


# ---------------
# NSView subclass
# ---------------

class MMPairView(MMTypingView):

    __metaclass__ = ClassNameIncrementer

    def initWithFont_(self, font):
        self = super(MMPairView, self).initWithFont_(font)

        self._pairAndContext = (None, None, None)
        self._groupPreviewView = None
        self._makeExceptionViewIsOpen = False

        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.addObserver_selector_name_object_(self, "groupPreviewPointSizeChanged:", "MM4.GroupPreviewPointSizeChanged", None)

        self.increments = getExtensionDefault("com.typesupply.MM4.viewSettings.general.kernIncrements", (1, 5, 10))

        return self

    def dealloc(self):
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)
        super(MMPairView, self).dealloc()

    def setNeedsDisplay_(self, value):
        if self._groupPreviewView is not None:
            self._groupPreviewView.setNeedsDisplay_(value)
        super(MMPairView, self).setNeedsDisplay_(value)

    def acceptsFirstResponder(self):
        return True

    def acceptsFirstMouse_(self, event):
        return True

    def becomeFirstResponder(self):
        self.increments = getExtensionDefault("com.typesupply.MM4.viewSettings.general.kernIncrements", (1, 5, 10))
        self._lineView.setShowFirstResponderIndicator_(True)
        return True

    def resignFirstResponder(self):
        self._lineView.setShowFirstResponderIndicator_(False)
        return True

    # -------------
    # notifications
    # -------------

    def fontChanged(self):
        self.refreshFrame()

    def contextStringsChanged(self):
        self.setPair_context_contextName_(self._pairAndContext[0], self._pairAndContext[1], self._pairAndContext[2])

    def groupPreviewPointSizeChanged_(self, notification):
        if self._groupPreviewView is not None:
            self.flushFrame()
            self.positionSubviews()

    # ----------
    # menu items
    # ----------

    def validateMenuItem_(self, item):
        if self.isMakeExceptionVisible() and item.action():
            if hasattr(self, item.action().replace(":", "_")):
                return False
        return True

    def keyDown_(self, event):
        if self.isMakeExceptionVisible():
            return
        characters = event.charactersIgnoringModifiers()
        modifiers = event.modifierFlags()
        # pseudo menu items
        if characters == AppKit.NSDownArrowFunctionKey:
            if modifiers & AppKit.NSShiftKeyMask:
                self.selectNextInLeftGroup_(None)
            elif modifiers & AppKit.NSAlternateKeyMask:
                self.selectNextInRightGroup_(None)
            else:
                self.selectNextPair_(None)
        elif characters == AppKit.NSUpArrowFunctionKey:
            if modifiers & AppKit.NSShiftKeyMask:
                self.selectPreviousInLeftGroup_(None)
            elif modifiers & AppKit.NSAlternateKeyMask:
                self.selectPreviousInRightGroup_(None)
            else:
                self.selectPreviousPair_(None)
        elif characters == AppKit.NSLeftArrowFunctionKey:
            if modifiers & AppKit.NSShiftKeyMask:
                self.kernSubtract5_(None)
            elif modifiers & AppKit.NSAlternateKeyMask:
                self.kernSubtract1_(None)
            else:
                self.kernSubtract10_(None)
        elif characters == AppKit.NSRightArrowFunctionKey:
            if modifiers & AppKit.NSShiftKeyMask:
                self.kernAdd5_(None)
            elif modifiers & AppKit.NSAlternateKeyMask:
                self.kernAdd1_(None)
            else:
                self.kernAdd10_(None)
        else:
            super(MMPairView, self).keyDown_(event)

    # actions

    def mouseDown_(self, event):
        self.window().makeFirstResponder_(self)

    def kernAdd10_(self, sender):
        self.vanillaWrapper().adjustPairBy(self.increments[2])

    def kernAdd5_(self, sender):
        self.vanillaWrapper().adjustPairBy(self.increments[1])

    def kernAdd1_(self, sender):
        self.vanillaWrapper().adjustPairBy(self.increments[0])

    def kernSubtract10_(self, sender):
        self.vanillaWrapper().adjustPairBy(-self.increments[2])

    def kernSubtract5_(self, sender):
        self.vanillaWrapper().adjustPairBy(-self.increments[1])

    def kernSubtract1_(self, sender):
        self.vanillaWrapper().adjustPairBy(-self.increments[0])

    def selectNextPair_(self, sender):
        self.vanillaWrapper().selectNextPair()

    def selectPreviousPair_(self, sender):
        self.vanillaWrapper().selectPreviousPair()

    def flipCurrentPair_(self, sender):
        if self.isMakeExceptionVisible():
            return
        self.vanillaWrapper().flipCurrentPair()

    def selectNextInLeftGroup_(self, sender):
        self.vanillaWrapper().selectNextInLeftGroup()

    def selectPreviousInLeftGroup_(self, sender):
        self.vanillaWrapper().selectPreviousInLeftGroup()

    def selectNextInRightGroup_(self, sender):
        self.vanillaWrapper().selectNextInRightGroup()

    def selectPreviousInRightGroup_(self, sender):
        self.vanillaWrapper().selectPreviousInRightGroup()

    def makeException_(self, sender):
        self.vanillaWrapper().makeException()

    def breakException_(self, sender):
        self.vanillaWrapper().breakException()

    # ---------------------
    # frame setting support
    # ---------------------

    def positionSubviews(self):
        scrollView = self.enclosingScrollView()
        if scrollView is None:
            return
        clipView = scrollView.contentView()
        fY = scrollView.documentView().frame().size[1]
        (vX, vY), (vW, vH) = clipView.visibleRect()

        if self._lineView is not None:
            w, h = self._lineView.frame().size
            y = fY - h
            # try to center the line view in the available space
            availableHeight = fY
            if self._infoView is not None:
                availableHeight -= self._infoView.frame().size[1]
            if self._groupPreviewView is not None:
                availableHeight -= self._groupPreviewView.frame().size[1]
            if h < availableHeight:
                y -= (availableHeight - h) / 2
            self._lineView.setFrame_(((0, y), (w, h)))
        if self._infoView is not None:
            w, h = self._infoView.frame().size
            self._infoView.setFrame_(((0, vY), (w, h)))
        if self._groupPreviewView is not None:
            y = 0
            if self._infoView is not None:
                (x, y), (w, h) = self._infoView.frame()
                y += h
            w, h = self._groupPreviewView.frame().size
            self._groupPreviewView.setFrame_(((0, y), (w, h)))

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
        if self._groupPreviewView is not None:
            self._groupPreviewView.flushFrame()
            w, h = self._groupPreviewView.frame().size
            if w > maxWidth:
                maxWidth = w
            necessaryHeight += h
        if self._lineView is not None:
            self._lineView.flushFrame()
            w, h = self._lineView.frame().size
            if w > maxWidth:
                maxWidth = w
            if h > maxHeight:
                maxHeight = h
        # force all views to the max width
        if self._lineView is not None:
            w, h = self._lineView.frame().size
            if w < maxWidth:
                self._lineView.setFrame_(((0, 0), (w, h)))
        if self._infoView is not None:
            w, h = self._infoView.frame().size
            if w < maxWidth:
                self._infoView.setFrame_(((0, 0), (maxWidth, h)))
        if self._groupPreviewView is not None:
            w, h = self._groupPreviewView.frame().size
            if w < maxWidth:
                self._groupPreviewView.setFrame_(((0, 0), (maxWidth, h)))
        if maxHeight < necessaryHeight:
            maxHeight = necessaryHeight
        # set the width of this view to the max width
        self.setFrame_(((0, 0), (maxWidth, maxHeight)))
        self.positionSubviews()

    def availableHeightForLineView(self):
        usedSpace = 0
        if self._infoView is not None:
            usedSpace += self._infoView.frame().size[1]
        if self._groupPreviewView is not None:
            usedSpace += self._groupPreviewView.frame().size[1]
        totalSpace = self.enclosingScrollView().contentView().visibleRect().size[1]
        if totalSpace <= usedSpace:
            return 0
        return totalSpace - usedSpace

    def refreshFrame(self):
        self.setPair_context_contextName_(self._pairAndContext[0], self._pairAndContext[1], self._pairAndContext[2])

    # ------------
    # external API
    # ------------

    def setPair_context_contextName_(self, pair, context, contextName):
        if pair is None:
            return
        self._pairAndContext = (pair, context, contextName)
        if contextName:
            string, selectionIndexes = self._font.metricsMachine.contextStrings.getLongContext(pair, name=contextName)
        elif context:
            leftContext, rightContext = context
            leftContext = [glyphName for glyphName in leftContext if glyphName in self._font]
            rightContext = [glyphName for glyphName in rightContext if glyphName in self._font]
            # if the left or right aren't in the font, don't do much
            left, right = pair
            if left not in self._font or right not in self._font:
                selectionIndexes = []
            else:
                selectionIndexes = [(len(leftContext) - 1, len(leftContext))]
            string = [self._font[glyphName] for glyphName in leftContext + rightContext]
        else:
            string, selectionIndexes = self._font.metricsMachine.contextStrings.getLongContext(pair)
        if self._lineView is not None:
            self._lineView.setGlyphs_selectionIndexes_(string, selectionIndexes)
        if self._infoView is not None:
            self._infoView.setGlyphs_selectionIndexes_(string, selectionIndexes)
        if self._groupPreviewView is not None:
            # XXX here?
            # XXX assumes that all glyphs in group are in the font!
            left, right = pair
            leftGroup = self._font.groups.metricsMachine.getSide1GroupForGlyph(left)
            if leftGroup is not None:
                leftGlyphs = []
                for glyphName in sorted(self._font.groups[leftGroup]):
                    leftGlyphs += self._font.metricsMachine.contextStrings.getShortContext((glyphName, right), name=contextName)[0]
            else:
                leftGroup = "None"
                leftGlyphs = []
            rightGroup = self._font.groups.metricsMachine.getSide2GroupForGlyph(right)
            if rightGroup is not None:
                rightGlyphs = []
                for glyphName in sorted(self._font.groups[rightGroup]):
                    rightGlyphs += self._font.metricsMachine.contextStrings.getShortContext((left, glyphName), name=contextName)[0]
            else:
                rightGroup = "None"
                rightGlyphs = []
            self._groupPreviewView.setLeftGlyphs_leftGroup_rightGlyphs_rightGroup_(leftGlyphs, leftGroup, rightGlyphs, rightGroup)
        self.flushFrame()
        events.publishEvent("MetricsMachine.currentPairChanged", font=self._font, pair=pair)

    def getPair(self):
        if self._pairAndContext is None:
            return None
        return self._pairAndContext[0]

    def setShowInfo_(self, value):
        if self.isMakeExceptionVisible():
            return
        super(MMPairView, self).setShowInfo_(value)

    def isGroupPreviewVisible(self):
        return self._groupPreviewView is not None

    def setShowGroupPreview_(self, value):
        if self.isMakeExceptionVisible():
            return
        if (value and self._groupPreviewView is not None) or (not value and self._groupPreviewView is None):
            return
        if not value:
            self._groupPreviewView.removeFromSuperview()
            self._groupPreviewView = None
        else:
            self._groupPreviewView = MMGroupPreviewView.alloc().initWithFont_(self._font)
            self.addSubview_(self._groupPreviewView)
        self.setPair_context_contextName_(self._pairAndContext[0], self._pairAndContext[1], self._pairAndContext[2])
        self.positionSubviews()

    def isGroupStackVisible(self):
        return self._lineView.isGroupStackVisible()

    def setShowGroupStack_(self, value):
        if self.isMakeExceptionVisible():
            return
        self._lineView.setShowGroupStack_(value)

    def showMakeException_(self, pairs):
        if self.isMakeExceptionVisible():
            return
        self._makeExceptionViewIsOpen = True
        MakeExceptionView(pairs, self._font, self, self.finishedMakeException)

    def finishedMakeException(self):
        self._makeExceptionViewIsOpen = False

    def isMakeExceptionVisible(self):
        return self._makeExceptionViewIsOpen


# ------------------------------------
# vanilla ScrollView holding pair view
# ------------------------------------

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]


class PairView(MMScrollView):

    def __init__(self, posSize, font):
        self.font = font
        self._pairView = MMPairView.alloc().initWithFont_(font)
        super(PairView, self).__init__(posSize, self._pairView, autohidesScrollers=False)

        self.pointSizes = ["Auto"] + [str(i) for i in pointSizes]
        placardW = 55
        placardH = 16
        self._placard = vanilla.Group((0, 0, placardW, placardH))
        self._placard.button = PlacardPopUpButton((0, 0, placardW, placardH),
            self.pointSizes, callback=self._placardSelection, sizeStyle="mini")
        self.setPlacard(self._placard)
        self.updateBackgroundColor(None)

        events.addObserver(self, "updateBackgroundColor", "appearanceChanged")
        self.font.metricsMachine.contextStrings.addObserver(self, "_contextStringsChanged", "MMContextStrings.Changed")
        self.font.addObserver(self, "_fontChanged", "Font.Changed")
        self.font.kerning.addObserver(self, "_kerningChanged", "Kerning.Changed")

    def _breakCycles(self):
        if self.font is not None:
            self.font.metricsMachine.contextStrings.removeObserver(self, "MMContextStrings.Changed")
            self.font.removeObserver(self, "Font.Changed")
            self.font.kerning.removeObserver(self, "Kerning.Changed")
        self.font = None
        events.removeObserver(self, "appearanceChanged")
        super(PairView, self)._breakCycles()

    def getPairView(self):
        return self._pairView

    def updateBackgroundColor(self, info):
        # Unwrap from try/except once RoboFont 4.5p is released.
        try:
            if inDarkMode():
                self._placard.button.setBackgroundColor(AppKit.NSColor.blackColor())
            else:
                self._placard.button.setBackgroundColor(AppKit.NSColor.whiteColor())
        except:
            pass

    def _placardSelection(self, sender):
        value = self.pointSizes[sender.get()]
        if value == "Auto":
            value = None
        else:
            value = int(value)
        self.setPointSize(value)

    def _contextStringsChanged(self, notification):
        self._pairView.contextStringsChanged()

    def _fontChanged(self, notification):
        self._pairView.fontChanged()

    def _kerningChanged(self, notification):
        self._pairView.fontChanged()

    def update(self):
        self._pairView.setNeedsDisplay_(True)

    def setPair(self, pair, context=None, contextName=None):
        self._pairView.setPair_context_contextName_(pair, context=context, contextName=contextName)

    def getPair(self):
        return self._pairView.getPair()

    def increasePointSize(self):
        pointSize = self._pairView.getPointSize()
        if pointSize not in pointSizes:
            closest = None
            for value in pointSizes:
                if closest is None:
                    closest = value
                    continue
                if value > pointSize:
                    break
                else:
                    closest = value
            pointSize = closest
        index = pointSizes.index(pointSize)
        next = index + 1
        if next == len(pointSizes):
            return
        pointSize = pointSizes[next]
        self.setPointSize(pointSize)

    def decreasePointSize(self):
        pointSize = self._pairView.getPointSize()
        if pointSize not in pointSizes:
            closest = None
            for value in pointSizes:
                if closest is None:
                    closest = value
                    continue
                if value > pointSize:
                    break
                else:
                    closest = value
            pointSize = closest
        else:
            index = pointSizes.index(pointSize)
            previous = index - 1
            if previous == -1:
                return
            pointSize = pointSizes[previous]
        self.setPointSize(pointSize)

    def getPointSize(self):
        return self._pairView.getPointSize()

    def setPointSize(self, value):
        self._pairView.setPointSize_(value)
        if value is None:
            value = "Auto"
        value = str(value)
        self._placard.button.set(self.pointSizes.index(value))

    def isInfoVisible(self):
        return self._pairView.isInfoVisible()

    def showInfo(self, value):
        self._pairView.setShowInfo_(value)

    def isGroupPreviewVisible(self):
        return self._pairView.isGroupPreviewVisible()

    def showGroupPreview(self, value):
        self._pairView.setShowGroupPreview_(value)

    def isGroupStackVisible(self):
        return self._pairView.isGroupStackVisible()

    def showGroupStack(self, value):
        self._pairView.setShowGroupStack_(value)

    def showMakeException(self, pairs):
        self._pairView.showMakeException_(pairs)


# -------------------
# complete pair group
# -------------------

class PairGroup(vanilla.Group):

    def __init__(self, posSize, font, selectionCallback):
        self.font = font
        self.font.kerning.addObserver(self, "_kerningChanged", "Kerning.Changed")
        self.font.metricsMachine.contextStrings.addObserver(self, "_contextStringsChanged", "MMContextStrings.Changed")

        self.glyphs = []
        self._selectionCallback = selectionCallback
        super(PairGroup, self).__init__(posSize)

        # -----------
        # scroll view
        # -----------

        pairView = PairView((0, 37, -0, -0), font)
        pairView.frameAdjustments = (-1, 0, 1, 1)
        pairView.showInfo(True)
        pairView.showGroupPreview(True)
        self.pairView = pairView

        # -------
        # toolbar
        # -------

        toolGroup = vanilla.Group((0, 0, -0, 36))

        toolGroup.leftComboBox = GlyphNameComboBox((10, 10, 120, 19), font, callback=self._leftRightEntryCallback, sizeStyle="small")
        toolGroup.rightComboBox = GlyphNameComboBox((140, 10, 120, 19), font, callback=self._leftRightEntryCallback, sizeStyle="small")
        toolGroup.valueEntry = NumberEditText((270, 10, 40, 19), sizeStyle="small", callback=self._valueEntryCallback)

        toolGroup.line1 = vanilla.VerticalLine((320, 5, 1, -5))

        toolGroup.controlStringPopUp = vanilla.PopUpButton((330, 10, 150, 17), ["Automatic"], sizeStyle="small", callback=self._contextNameCallback)

        toolGroup.line2 = vanilla.VerticalLine((490, 5, 1, -5))

        toolGroup.progressIndicator = PairListProgressIndicator((500, 11, 130, 11))
        toolGroup.progressIndicator.show(False)

        self.toolGroup = toolGroup
        self._loadContextStrings()

    def _breakCycles(self):
        if self.font is not None:
            self.font.kerning.removeObserver(self, "Kerning.Changed")
            self.font.metricsMachine.contextStrings.removeObserver(self, "MMContextStrings.Changed")
        self.font = None
        self.glyphs = None
        self._selectionCallback = None
        super(PairGroup, self)._breakCycles()

    def setupKeyLoop(self, window):
        loop = [
            self.toolGroup.leftComboBox.getNSTextField(),
            self.toolGroup.rightComboBox.getNSTextField(),
            self.toolGroup.valueEntry.getNSTextField(),
            self.pairView.getPairView()
        ]
        window.getNSWindow().setInitialFirstResponder_(loop[0])
        for index, view in enumerate(loop):
            next = index + 1
            if next == len(loop):
                next = 0
            next = loop[next]
            view.setNextKeyView_(next)

    def _leftRightEntryCallback(self, sender):
        left = self.toolGroup.leftComboBox.get()
        right = self.toolGroup.rightComboBox.get()
        if left not in self.font or right not in self.font:
            return
        self.set((left, right))
        if self._selectionCallback is not None:
            self._selectionCallback(self)

    def _valueEntryCallback(self, sender):
        value = sender.get()
        if value is None:
            return
        left = self.toolGroup.leftComboBox.get()
        right = self.toolGroup.rightComboBox.get()
        if left not in self.font or right not in self.font:
            return
        self.font.kerning.metricsMachine[left, right] = value

    def _contextNameCallback(self, sender):
        left = self.toolGroup.leftComboBox.get()
        right = self.toolGroup.rightComboBox.get()
        self.set((left, right))

    def _kerningChanged(self, notification):
        left = self.toolGroup.leftComboBox.get()
        right = self.toolGroup.rightComboBox.get()
        value = self.font.kerning.metricsMachine[left, right]
        self.toolGroup.valueEntry.set(value)

    def _contextStringsChanged(self, notification):
        self._loadContextStrings()

    def _loadContextStrings(self):
        strings = getExtensionDefault("com.typesupply.MM4.contextStrings")
        available = ["Automatic"]
        for string in strings:
            if not string["enabled"]:
                continue
            name = string["name"]
            if name in available:
                continue
            available.append(name)
        self._contextStrings = available
        self.toolGroup.controlStringPopUp.setItems(available)

    # ----------
    # menu items
    # ----------

    def _getVanillaWindowController(self):
        window = self.getNSView().window()
        if window is not None:
            delegate = window.delegate()
            if delegate is not None:
                if hasattr(delegate, "vanillaWrapper"):
                    return delegate.vanillaWrapper()
        return None

    def selectNextPair(self):
        controller = self._getVanillaWindowController()
        controller.selectNextPair()
        # app = NSApp()
        # doc = app.orderedDocuments()[0]
        # doc.vanillaWindowController.selectNextPair()

    def selectPreviousPair(self):
        controller = self._getVanillaWindowController()
        controller.selectPreviousPair()
        # app = AppKit.NSApp()
        # doc = app.orderedDocuments()[0]
        # doc.vanillaWindowController.selectPreviousPair()

    def selectNextInLeftGroup(self):
        left, right = self.get()
        groups = self.font.groups
        leftGroup = groups.metricsMachine.getSide1GroupForGlyph(left)
        if leftGroup is None:
            return
        group = list(sorted(groups[leftGroup]))
        index = group.index(left)
        if index + 1 == len(group):
            index = 0
        else:
            index += 1
        self.set((group[index], right))

    def selectPreviousInLeftGroup(self):
        left, right = self.get()
        groups = self.font.groups
        leftGroup = groups.metricsMachine.getSide1GroupForGlyph(left)
        if leftGroup is None:
            return
        group = list(sorted(groups[leftGroup]))
        index = group.index(left)
        if index == 0:
            index = len(group) - 1
        else:
            index -= 1
        self.set((group[index], right))

    def selectNextInRightGroup(self):
        left, right = self.get()
        groups = self.font.groups
        rightGroup = groups.metricsMachine.getSide2GroupForGlyph(right)
        if rightGroup is None:
            return
        group = list(sorted(groups[rightGroup]))
        index = group.index(right)
        if index + 1 == len(group):
            index = 0
        else:
            index += 1
        self.set((left, group[index]))

    def selectPreviousInRightGroup(self):
        left, right = self.get()
        groups = self.font.groups
        rightGroup = groups.metricsMachine.getSide2GroupForGlyph(right)
        if rightGroup is None:
            return
        group = list(sorted(groups[rightGroup]))
        index = group.index(right)
        if index == 0:
            index = len(group) - 1
        else:
            index -= 1
        self.set((left, group[index]))

    def adjustPairBy(self, value):
        left, right = self.get()
        old = self.font.kerning.metricsMachine[left, right]
        self.font.kerning.metricsMachine[left, right] = old + value

    def flipCurrentPair(self):
        left, right = self.get()
        self.set((right, left))

    def isInfoVisible(self):
        return self.pairView.isInfoVisible()

    def showInfo(self, value):
        self.pairView.showInfo(value)

    def toggleGlyphInfo(self):
        if self.isInfoVisible():
            self.showInfo(False)
        else:
            self.showInfo(True)

    def isGroupPreviewVisible(self):
        return self.pairView.isGroupPreviewVisible()

    def showGroupPreview(self, value):
        self.pairView.showGroupPreview(value)

    def toggleGroupPreview(self):
        if self.isGroupPreviewVisible():
            self.pairView.showGroupPreview(False)
        else:
            self.pairView.showGroupPreview(True)

    def isGroupStackVisible(self):
        return self.pairView.isGroupStackVisible()

    def showGroupStack(self, value):
        self.pairView.showGroupStack(value)

    def toggleGroupStack(self):
        if self.isGroupStackVisible():
            self.showGroupStack(False)
        else:
            self.showGroupStack(True)

    def increasePointSize(self):
        self.pairView.increasePointSize()

    def decreasePointSize(self):
        self.pairView.decreasePointSize()

    def makeException(self):
        pair = self.get()
        possiblePairs = self.font.kerning.metricsMachine.getPossibleExceptions(pair)
        if len(possiblePairs) == 0 or pair not in possiblePairs:
            return
        elif possiblePairs == [pair]:
            self.font.kerning.metricsMachine.makeException(pair)
        else:
            self.pairView.showMakeException(possiblePairs)

    def breakException(self):
        pair = self.get()
        pairType = self.font.kerning.metricsMachine.getPairType(pair)
        if "exception" not in pairType:
            AppKit.NSBeep()
            return
        self.font.kerning.metricsMachine.breakException(pair)

    # ------------
    # external API
    # ------------

    def set(self, pair, context=None, index=None):
        left, right = pair
        self.toolGroup.leftComboBox.set(left)
        self.toolGroup.rightComboBox.set(right)
        self.toolGroup.valueEntry.set(self.font.kerning.metricsMachine[pair])
        contextNameIndex = self.toolGroup.controlStringPopUp.get()
        if contextNameIndex == 0:
            contextName = None
        else:
            contextName = self._contextStrings[contextNameIndex]
        self.pairView.setPair(pair, context=context, contextName=contextName)
        if index is not None:
            self.toolGroup.progressIndicator.set(index)

    def get(self):
        left = self.toolGroup.leftComboBox.get()
        right = self.toolGroup.rightComboBox.get()
        return (left, right)

    def setPairListCount(self, value):
        self.toolGroup.progressIndicator.show(True)
        self.toolGroup.progressIndicator.setCount(value)
