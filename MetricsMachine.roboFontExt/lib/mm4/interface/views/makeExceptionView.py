import weakref
import AppKit
from objc import super
import vanilla
from defconAppKit.windows.popUpWindow import InteractivePopUpWindow, DefconAppKitInteractivePopUpNSWindow
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix
from mm4.interface.formatters import PairMemberFormatter, KerningValueFormatter
from mojo.events import addObserver, removeObserver
from mojo.UI import inDarkMode


class MMMakeExceptionNSPanel(DefconAppKitInteractivePopUpNSWindow):

    def keyDown_(self, event):
        characters = event.charactersIgnoringModifiers()
        if characters == AppKit.NSDownArrowFunctionKey:
            self.vanillaWrapper().selectNextException()
        elif characters == AppKit.NSUpArrowFunctionKey:
            self.vanillaWrapper().selectPreviousException()
        else:
            super(MMMakeExceptionNSPanel, self).keyDown_(event)


class MakeExceptionPopUpWindow(InteractivePopUpWindow):

    nsWindowClass = MMMakeExceptionNSPanel


class MakeExceptionView(object):

    def __init__(self, pairs, font, viewToCenterOver, closeCallback):
        self.font = font
        self._closeCallback = closeCallback

        pairs = sorted(pairs)
        self.pairs = pairs
        stringPairs = []
        for side1, side2 in pairs:
            if side1.startswith(side1Prefix):
                side1 = "[%s]" % side1[7:]
            if side2.startswith(side2Prefix):
                side2 = "[%s]" % side2[7:]
            s = "%s, %s" % (side1, side2)
            stringPairs.append(s)

        radioHeight = 22 * len(pairs)
        radioHeight = 22 * len(pairs)
        self.heightWithoutRemove = 127 + radioHeight
        self.heightWithRemove = self.heightWithoutRemove + 190

        removePairs = font.kerning.metricsMachine.getConflictingExceptions(pairs[0])
        haveRemovePairs = bool(removePairs)
        removePairs = self._wrapRemovePairs(removePairs)

        w = 340
        if haveRemovePairs:
            h = self.heightWithRemove
        else:
            h = self.heightWithoutRemove

        # work out the pos size relative to the other view
        viewFrame = viewToCenterOver.visibleRect()
        previous = viewToCenterOver
        while 1:
            s = previous.superview()
            if s is None:
                break
            else:
                viewFrame = s.convertRect_fromView_(viewFrame, previous)
                previous = s
        viewFramePosition, viewFrameSize = viewFrame
        viewWindow = viewToCenterOver.window()
        viewFramePosition = viewWindow.convertBaseToScreen_(viewFramePosition)
        viewFrame = (viewFramePosition, viewFrameSize)
        (sL, sB), (sW, sH) = viewWindow.screen().frame()
        (vL, vB), (vW, vH) = viewFrame
        vT = sH - vB - vH - 40
        # find the window position
        x = vL + ((vW - w) / 2)
        y = vT + ((vH - h) / 2)
        posSize = (x, y, w, h)

        self.w = MakeExceptionPopUpWindow(posSize, screen=viewToCenterOver.window().screen())
        self.w.getNSWindow().vanillaWrapper = weakref.ref(self)

        self.w.exceptionTitle = vanilla.TextBox((15, 15, -15, 34), "More than one exception is possible.\nChoose the exception you would like to create.")
        self.w.line1 = vanilla.HorizontalLine((15, 60, -15, 1))
        self.w.exceptionGroup = vanilla.RadioGroup((15, 70, -15, radioHeight), stringPairs, callback=self.exceptionChoiceCallback)
        self.w.exceptionGroup.set(0)

        top = 55 + radioHeight + 20
        self.w.removeTitle = vanilla.TextBox((15, top, -15, 51), "The selected exception will create conflicting data. The following pairs will be removed to resolve the problem.")
        top += 65

        formatter = KerningValueFormatter()
        columnDescriptions = [
            dict(title="side 1", key="side1", width=120, formatter=PairMemberFormatter.alloc().init()),
            dict(title="side 2", key="side2", width=120, formatter=PairMemberFormatter.alloc().init()),
            dict(title="value", formatter=formatter),
        ]
        self.w.removeList = vanilla.List((15, top, -15, 112), removePairs, columnDescriptions=columnDescriptions,
            showColumnTitles=False, drawVerticalLines=True, drawFocusRing=False)
        cell = self.w.removeList.getNSTableView().tableColumns()[2].dataCell()
        cell.setAlignment_(AppKit.NSRightTextAlignment)

        self.w.removeTitle.show(haveRemovePairs)
        self.w.removeList.show(haveRemovePairs)

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)
        self.w.setDefaultButton(self.w.applyButton)
        self.w.bind("close", self.windowCloseCallback)

        self.updateBackgroundColor(None)
        addObserver(self, "updateBackgroundColor", "appearanceChanged")

        self.w.open()

    def _wrapRemovePairs(self, pairs):
        return [dict(side1=l, side2=r, value=v) for (l, r), v in pairs.items()]

    # ----------------
    # button callbacks
    # ----------------

    def windowCloseCallback(self, sender):
        if self._closeCallback is not None:
            self._closeCallback()
            self._closeCallback = None

    def _finalize(self):
        self.w.getNSWindow().vanillaWrapper = None
        removeObserver(self, "appearanceChanged")
        self.w.close()

    def cancelCallback(self, sender):
        self._finalize()

    def applyCallback(self, sender):
        kerning = self.font.kerning
        pairIndex = self.w.exceptionGroup.get()
        pair = self.pairs[pairIndex]
        for removePair in kerning.metricsMachine.getConflictingExceptions(pair).keys():
            del kerning[removePair]
        kerning.metricsMachine.makeException(pair)
        self._finalize()

    def exceptionChoiceCallback(self, sender):
        kerning = self.font.kerning
        pairIndex = sender.get()
        pair = self.pairs[pairIndex]
        l, t, w, h = self.w.getPosSize()
        removePairs = kerning.metricsMachine.getConflictingExceptions(pair)
        self._showRemove = bool(removePairs)
        if removePairs:
            nH = self.heightWithRemove
            t += (h - nH) / 2
            self.w.setPosSize((l, t, w, nH), animate=True)
            removePairs = self._wrapRemovePairs(removePairs)
            self.w.removeList.set(removePairs)
            self.w.removeTitle.show(True)
            self.w.removeList.show(True)
        else:
            self.w.removeTitle.show(False)
            self.w.removeList.show(False)
            nH = self.heightWithoutRemove
            t += (h - nH) / 2
            self.w.setPosSize((l, t, w, nH), animate=True)

    # ---------------
    # key interaction
    # ---------------

    def selectPreviousException(self):
        count = len(self.pairs)
        current = self.w.exceptionGroup.get()
        prev = current - 1
        if prev == -1:
            prev = count - 1
        self.w.exceptionGroup.set(prev)
        self.exceptionChoiceCallback(self.w.exceptionGroup)

    def selectNextException(self):
        count = len(self.pairs)
        current = self.w.exceptionGroup.get()
        next = current + 1
        if next == count:
            next = 0
        self.w.exceptionGroup.set(next)
        self.exceptionChoiceCallback(self.w.exceptionGroup)


    def updateBackgroundColor(self, notification):
        # Unwrap from try/except on the next RF release
        if inDarkMode():
            try:
                self.w.setContentBackgroundColor(AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .2, .2, .95))
            except:
                pass
        else:
            try:
                self.w.setContentBackgroundColor(AppKit.NSColor.colorWithCalibratedWhite_alpha_(.9, .95))
            except:
                pass
