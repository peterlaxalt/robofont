import weakref
import AppKit
from objc import super, python_method
import vanilla
from defconAppKit.controls.placardScrollView import PlacardPopUpButton
from defconAppKit.windows.popUpWindow import InformationPopUpWindow, HUDTextBox
from mm4.objects.mmGroups import userFriendlyGroupName
from mm4.interface.colors import *
from mm4.interface.views.scrollView import MMScrollView, MMBaseView
from mm4.interface.glyphSortDescriptors import sortGlyphNames
from mm4.interface.views.contextPrefsView import unicodeCategoryValues
from mojo.UI import inDarkMode
from mojo.events import addObserver, removeObserver


# ------------------
# topography NSViews
# ------------------

class MMTopographyView(MMBaseView):

    def initWithFont_(self, font):
        self = super(MMTopographyView, self).init()
        self._font = font
        self._side1Glyphs = []
        self._side2Glyphs = []

        self._columnWidth = None
        self._rowHeight = None
        self._yOffset = 0
        self._xOffset = 0

        self._side1DivisionIndexes = set()
        self._side2DivisionIndexes = set()

        self._selectedPair = None

        self._flatPairs = {}

        self._rowHeight = self._columnWidth = 3
        self._makeGlyphGridImage()
        self._detailPopUp = None

        self._side1GlyphToIndex = {}
        self._side2GlyphToIndex = {}

        self._cachedImage = None
        self._cachedImageLeftRange = None
        self._cachedImageRightRange = None

        self._windowIsClosed = False
        self._haveSubscribedToWindow = False

        return self

    def dealloc(self):
        self._font = None
        del self.vanillaWrapper
        super(MMTopographyView, self).dealloc()

    def isFlipped(self):
        return True

    def acceptsFirstResponder(self):
        return True

    # ------------
    # external API
    # ------------

    def positionSubviews(self):
        pass

    def setFlatPairs_(self, pairs):
        font = self._font

        self._flatPairs = pairs

        self._side1ToPairs = {}
        self._side2ToPairs = {}
        self._alphaToPairs = {}

        self._zeroPairs = set()
        self._negativePairs = set()
        self._positivePairs = set()
        self._exceptionPairs = set()

        self._highlightExceptions = True

        for (side1, side2), value in self._flatPairs.items():
            if side1 not in self._side1ToPairs:
                self._side1ToPairs[side1] = []
            self._side1ToPairs[side1].append((side1, side2))
            if side2 not in self._side2ToPairs:
                self._side2ToPairs[side2] = []
            self._side2ToPairs[side2].append((side1, side2))
            # pair type
            if "exception" in font.kerning.metricsMachine.getPairType((side1, side2)):
                self._exceptionPairs.add((side1, side2))
            # value storage
            pair = (side1, side2)
            if value == 0:
                self._zeroPairs.add(pair)
                continue
            if value < 0:
                self._negativePairs.add(pair)
            else:
                self._positivePairs.add(pair)
            alpha = abs(value)
            alpha = int(round(alpha * .01, 3) * 100)
            if alpha > 100:
                alpha = 100
            elif alpha < 10:
                alpha = 10
            alpha = alpha * .01
            if alpha not in self._alphaToPairs:
                self._alphaToPairs[alpha] = set()
            self._alphaToPairs[alpha].add(pair)

        self.setNeedsDisplay_(True)

    def setGlyphsSide1_side2_(self, side1, side2):
        self._side1Glyphs = side1
        self._side2Glyphs = side2
        self._side1DivisionIndexes = self._getDivisionIndexes(side1)
        self._side2DivisionIndexes = self._getDivisionIndexes(side2)
        self._side1GlyphToIndex = {}
        self._side2GlyphToIndex = {}
        for index, glyphName in enumerate(side1):
            self._side1GlyphToIndex[glyphName] = index
        for index, glyphName in enumerate(side2):
            self._side2GlyphToIndex[glyphName] = index
        self._updateFrame()

    @python_method
    def _getDivisionIndexes(self, glyphs):
        font = self._font
        scriptDivisions = set()
        categoryDivisions = set()
        suffixDivisions = set()
        currentScript = None
        currentCategory = None
        currentSuffix = None
        for index, glyphName in enumerate(glyphs):
            category = font.unicodeData.categoryForGlyphName(glyphName)
            script = font.unicodeData.scriptForGlyphName(glyphName)
            suffix = None
            if len(glyphName.split(".", 1)) > 1:
                suffix = glyphName.split(".", 1)[1]
            if category != currentCategory and index != 0:
                categoryDivisions.add(index)
            if script != currentScript and index != 0:
                scriptDivisions.add(index)
            if suffix != currentSuffix and index != 0:
                suffixDivisions.add(index)
            currentSuffix = suffix
            currentCategory = category
            currentScript = script
        categoryDivisions = categoryDivisions - (scriptDivisions | suffixDivisions)
        suffixDivisions = suffixDivisions - (scriptDivisions | categoryDivisions)
        return scriptDivisions, categoryDivisions, suffixDivisions

    def get(self):
        return self._selectedPair

    def setHighlightExceptions_(self, value):
        self._highlightExceptions = value
        self.setNeedsDisplayInRect_(self.visibleRect())

    def setBlockSize_(self, size):
        self._rowHeight = self._columnWidth = size
        self._makeGlyphGridImage()
        self._updateFrame()

    # ------------------
    # internal utilities
    # ------------------

    def _updateFrame(self):
        side1 = self._side1Glyphs
        side2 = self._side2Glyphs
        w = (len(side2) * self._columnWidth) + self._xOffset
        h = (len(side1) * self._rowHeight) + self._yOffset
        r = ((0, 0), (w, h))
        self.setFrame_(r)
        self.setNeedsDisplay_(True)

    @python_method
    def _gridFitRect(self, rect):
        rowHeight = self._rowHeight
        columnWidth = self._columnWidth
        xOffset = self._xOffset
        yOffset = self._yOffset
        (x, y), (w, h) = rect
        # xPlusOffset = x + xOffset
        # yPlusOffset = y + yOffset
        wPlusOffset = w - xOffset
        hPlusOffset = h - yOffset
        # count the number of visible cells
        side2Count = int(wPlusOffset / columnWidth)
        side1Count = int(hPlusOffset / rowHeight)
        # work out the visible ranges
        minSide2Index = int(x / columnWidth)
        if minSide2Index * columnWidth > x:
            minSide2Index -= 1
            side2Count += 1
        minSide1Index = int(y / rowHeight)
        if minSide1Index * rowHeight > y:
            minSide1Index -= 1
            side1Count += 1
        # tweak the counts
        if yOffset + (minSide1Index * rowHeight) + (side1Count * rowHeight) < (y + h):
            diff = (y + h) - (yOffset + (minSide1Index * rowHeight) + (side1Count * rowHeight))
            count = int(diff / rowHeight)
            if diff % rowHeight:
                count += 1
            side1Count += count
        if xOffset + (minSide2Index * columnWidth) + (side2Count * columnWidth) < (x + w):
            diff = (x + w) - (xOffset + (minSide2Index * columnWidth) + (side2Count * columnWidth))
            count = int(diff / columnWidth)
            if diff % columnWidth:
                count += 1
            side2Count += count
        # work out the max edge of the ranges
        maxSide2Index = minSide2Index + side2Count
        maxSide1Index = minSide1Index + side1Count

        minSide1Index = int(minSide1Index)
        maxSide1Index = int(maxSide1Index)
        side1Count = int(side1Count)
        minSide2Index = int(minSide2Index)
        maxSide2Index = int(maxSide2Index)
        side2Count = int(side2Count)

        origin = (minSide2Index * columnWidth, minSide1Index * rowHeight)
        size = (side2Count * columnWidth, side1Count * rowHeight)
        drawRect = (origin, size)
        return drawRect, minSide1Index, maxSide1Index, side1Count, minSide2Index, maxSide2Index, side2Count

    @python_method
    def _getHitResult(self, xy):
        x, y = xy
        (visibleX, visibleY), (visibleW, visibleH) = self.visibleRect()
        rowHeight = self._rowHeight
        columnWidth = self._columnWidth
        xOffset = self._xOffset
        yOffset = self._yOffset
        rowHeaderMax = visibleX + xOffset
        columnHeaderMax = visibleY + yOffset
        # side 1
        side1Index = (y - yOffset) / rowHeight
        if int(side1Index) > side1Index:
            side1Index = int(side1Index) - 1
        side1Index = int(side1Index)
        # side 2
        side2Index = (x - xOffset) / columnWidth
        if int(side2Index) > side2Index:
            side2Index = int(side2Index) - 1
        side2Index = int(side2Index)
        # hit corner
        if x < rowHeaderMax and y < columnHeaderMax:
            return None
        # hit header
        elif x < rowHeaderMax or y < columnHeaderMax:
            if x < rowHeaderMax:
                position = "row"
            else:
                position = "column"
            return "%s header" % position, (side1Index, side2Index)
        # pair
        else:
            return "pair", (side1Index, side2Index)

    # ------------------------
    # notifications for pop up
    # ------------------------

    def viewDidMoveToWindow(self):
        # if window() returns an object, open the detail window
        window = self.window()
        if window is not None and not self._haveSubscribedToWindow:
            window.setAcceptsMouseMovedEvents_(True)
            notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
            notificationCenter.addObserver_selector_name_object_(
                self, "windowResignMainNotification:", AppKit.NSWindowDidResignKeyNotification, window
            )
            notificationCenter.addObserver_selector_name_object_(
                self, "windowCloseNotification:", AppKit.NSWindowWillCloseNotification, window
            )
            self._haveSubscribedToWindow = True

    def detailPopUp(self):
        if self._detailPopUp is None:
            self._detailPopUp = MMTopographyDetailPopUp()
            # try to add it to the document so that
            # it can be released when the document is closed.
            window = self.window()
            if window is not None:
                windowController = window.windowController()
                if windowController is not None:
                    document = windowController.document()
                    if document is not None:
                        document.addWindowController_(self._detailPopUp.getNSWindowController())
        return self._detailPopUp

    def windowResignMainNotification_(self, notification):
        self._mouseAction()

    def windowCloseNotification_(self, notification):
        self._windowIsClosed = True
        if self._detailPopUp is not None:
            if self._detailPopUp.getNSWindow() is not None:
                self._detailPopUp.hide()
                self._detailPopUp.getNSWindow().orderOut_(None)
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)
        self._haveSubscribedToWindow = False

    # ---------------
    # cursor handling
    # ---------------

    def resetCursorRects(self):
        cursorImage = makeCursorImage()
        cursor = AppKit.NSCursor.alloc().initWithImage_hotSpot_(cursorImage, (16, 16))
        self.addCursorRect_cursor_(self.visibleRect(), cursor)

    # -------
    # drawing
    # -------

    def _makeGlyphGridImage(self):
        blockSize = self._rowHeight
        imageSize = blockSize * 100
        pattern = AppKit.NSImage.alloc().initWithSize_((blockSize, blockSize))
        pattern.lockFocus()
        topographyViewLineColor.set()
        path = AppKit.NSBezierPath.bezierPath()
        path.moveToPoint_((0, .5))
        path.lineToPoint_((blockSize, .5))
        path.moveToPoint_((.5, 0))
        path.lineToPoint_((.5, blockSize))
        path.setLineWidth_(1.0)
        path.stroke()
        pattern.unlockFocus()
        oneBlockColor = AppKit.NSColor.colorWithPatternImage_(pattern)
        pattern = AppKit.NSImage.alloc().initWithSize_((imageSize, imageSize))
        pattern.lockFocus()
        oneBlockColor.set()
        AppKit.NSRectFillUsingOperation(((0, 0), (imageSize, imageSize)), AppKit.NSCompositeSourceOver)
        pattern.unlockFocus()
        self._glyphGridPatternImage = pattern

    def drawRect_(self, rect):
        blockSize = self._rowHeight
        # normalize the rect to draw
        drawRect, minSide1Index, maxSide1Index, side1Count, minSide2Index, maxSide2Index, side2Count = self._gridFitRect(rect)
        (originX, originY), (width, height) = drawRect
        # draw the background
        AppKit.NSColor.blackColor().set()
        AppKit.NSRectFill(self.bounds())
        # draw the pairs
        # group the rects
        negativeRects = {}
        positiveRects = {}
        zeroRects = []
        possibleSide1 = []
        possibleSide2 = []
        for side1Index in range(minSide1Index, maxSide1Index):
            side1 = self._side1Glyphs[side1Index]
            if side1 not in self._side1ToPairs:
                continue
            possibleSide1.extend(self._side1ToPairs[side1])
        for side2Index in range(minSide2Index, maxSide2Index):
            side2 = self._side2Glyphs[side2Index]
            if side2 not in self._side2ToPairs:
                continue
            possibleSide2.extend(self._side2ToPairs[side2])
        inView = set(possibleSide1) & set(possibleSide2)
        zero = self._zeroPairs & inView
        negative = self._negativePairs & inView
        positive = self._positivePairs & inView
        exceptions = self._exceptionPairs & inView
        pairRects = {}
        for side1, side2 in zero:
            side1Index = self._side1GlyphToIndex[side1]
            side2Index = self._side2GlyphToIndex[side2]
            x = blockSize * side2Index
            y = blockSize * side1Index
            r = ((x, y), (blockSize, blockSize))
            zeroRects.append(r)
            pairRects[side1, side2] = r
        for alpha, pairs in self._alphaToPairs.items():
            negativeRects[alpha] = []
            for side1, side2 in negative & pairs:
                side1Index = self._side1GlyphToIndex[side1]
                side2Index = self._side2GlyphToIndex[side2]
                x = blockSize * side2Index
                y = blockSize * side1Index
                r = ((x, y), (blockSize, blockSize))
                negativeRects[alpha].append(r)
                pairRects[side1, side2] = r
            if not negativeRects[alpha]:
                del negativeRects[alpha]
            positiveRects[alpha] = []
            for side1, side2 in positive & pairs:
                side1Index = self._side1GlyphToIndex[side1]
                side2Index = self._side2GlyphToIndex[side2]
                x = blockSize * side2Index
                y = blockSize * side1Index
                r = ((x, y), (blockSize, blockSize))
                positiveRects[alpha].append(r)
                pairRects[side1, side2] = r
            if not positiveRects[alpha]:
                del positiveRects[alpha]
        # fill the rects
        for alpha, rectList in negativeRects.items():
            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 0, 0, alpha).set()
            AppKit.NSRectFillListUsingOperation(rectList, len(rectList), AppKit.NSCompositeSourceOver)
        for alpha, rectList in positiveRects.items():
            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 1, 0, alpha).set()
            AppKit.NSRectFillListUsingOperation(rectList, len(rectList), AppKit.NSCompositeSourceOver)
        if zeroRects:
            AppKit.NSColor.yellowColor().set()
            AppKit.NSRectFillListUsingOperation(zeroRects, len(zeroRects), AppKit.NSCompositeSourceOver)
        if exceptions:
            sizes = {
                1: 0,
                2: 0,
                3: 1,
                4: 2,
                5: 3,
                6: 4,
                7: 3,
                8: 4,
                9: 3,
                10: 4
            }
            exceptionRectSize = sizes[self._columnWidth]
            if exceptionRectSize:
                exceptionRectOffset = (self._columnWidth - exceptionRectSize) / 2
                exceptionRects = [((pairRects[pair][0][0] + exceptionRectOffset, pairRects[pair][0][1] + exceptionRectOffset), (exceptionRectSize, exceptionRectSize)) for pair in exceptions]
                topographyViewExceptionColor.set()
                AppKit.NSRectFillListUsingOperation(exceptionRects, len(exceptionRects), AppKit.NSCompositeSourceOver)
        # draw the glyph grid lines
        size = self._glyphGridPatternImage.size()
        xCount = int(width / size[0]) + 1
        yCount = int(height / size[1]) + 1
        x = originX
        for i in range(xCount):
            y = originY
            for j in range(yCount):
                self._glyphGridPatternImage.drawInRect_fromRect_operation_fraction_(
                    ((x, y), size), ((0, 0), size), AppKit.NSCompositeSourceOver, 1.0
                )
                y += size[1]
            x += size[0]
        # draw the division lines
        colors = [topographyViewLineColor1, topographyViewLineColor2, topographyViewLineColor3]
        for groupNumber, indexes in enumerate(self._side1DivisionIndexes):
            divisionPath = AppKit.NSBezierPath.bezierPath()
            for index in indexes:
                if index < minSide1Index or index > maxSide1Index:
                    continue
                x = originX
                w = width
                y = (self._rowHeight * index) + .5
                divisionPath.moveToPoint_((x, y))
                divisionPath.lineToPoint_((x + w, y))
            colors[groupNumber].set()
            divisionPath.setLineWidth_(1)
            divisionPath.stroke()
        for groupNumber, indexes in enumerate(self._side2DivisionIndexes):
            divisionPath = AppKit.NSBezierPath.bezierPath()
            for index in indexes:
                if index < minSide2Index or index > maxSide2Index:
                    continue
                x = (self._columnWidth * index) + .5
                y = originY
                h = height
                divisionPath.moveToPoint_((x, y))
                divisionPath.lineToPoint_((x, y + h))
            colors[groupNumber].set()
            divisionPath.setLineWidth_(1)
            divisionPath.stroke()

    # --------------
    # event handling
    # --------------

    def mouseDown_(self, event):
        self._mouseAction(event, mouseDown=True)

    def mouseDragged_(self, event):
        self._mouseAction(event, mouseDragged=True)

    def mouseMoved_(self, event):
        self._mouseAction(event)

    def _mouseAction(self, event=None, mouseDown=False, mouseDragged=False):
        if self._windowIsClosed:
            return
        detailPopUp = self.detailPopUp()
        if detailPopUp is None:
            return
        showPopUp = False
        if event is not None:
            eventLocation = event.locationInWindow()
            point = self.convertPoint_fromView_(eventLocation, None)
            if AppKit.NSPointInRect(point, self.visibleRect()):
                result = self._getHitResult(point)
                if result:
                    hitType, (side1Index, side2Index) = result
                    if hitType == "pair":
                        showPopUp = True
                        side1 = self._side1Glyphs[side1Index]
                        side2 = self._side2Glyphs[side2Index]
                        detailX, detailY = self.window().convertBaseToScreen_(eventLocation)
                        pair = (side1, side2)
                        side1Group = self._font.groups.metricsMachine.getSide1GroupForGlyph(pair[0])
                        side2Group = self._font.groups.metricsMachine.getSide2GroupForGlyph(pair[1])
                        category = (self._font.unicodeData.categoryForGlyphName(pair[0]), self._font.unicodeData.categoryForGlyphName(pair[1]))
                        script = (self._font.unicodeData.scriptForGlyphName(pair[0]), self._font.unicodeData.scriptForGlyphName(pair[1]))
                        _side1Suffix = ""
                        _side2Suffix = ""
                        if "." in side1:
                            _side1Suffix = side1.split(".", 1)[1]
                        if "." in side2:
                            _side2Suffix = side2.split(".", 1)[1]
                        suffix = (_side1Suffix, _side2Suffix)
                        value = self._flatPairs.get(pair, 0)
                        detailPopUp.set(category, script, suffix, pair, (side1Group, side2Group), value)
                        detailPopUp.setPosition((detailX, detailY))
                        self._selectedPair = pair
                        if mouseDown or mouseDragged:
                            self.vanillaWrapper()._selection()
        if AppKit.NSApp().keyWindow() != self.window():
                showPopUp = False
        if showPopUp:
            detailPopUp.show()
        else:
            detailPopUp.hide()


# ----------
# info popup
# ----------

unicodeCategoryTranslation = {}
for k, v in unicodeCategoryValues:
    unicodeCategoryTranslation[k] = v


def makeCursorImage():
    image = AppKit.NSImage.alloc().initWithSize_((32, 32))
    image.lockFocus()
    path = AppKit.NSBezierPath.bezierPath()
    path.appendBezierPathWithOvalInRect_(((12, 12), (8, 8)))
    path.setLineWidth_(4)
    if inDarkMode():
        AppKit.NSColor.colorWithCalibratedWhite_alpha_(1, .5).set()
    else:
        AppKit.NSColor.colorWithCalibratedWhite_alpha_(0, .5).set()
    path.stroke()

    path = AppKit.NSBezierPath.bezierPath()
    path.appendBezierPathWithOvalInRect_(((9.5, 9.5), (13, 13)))
    path.moveToPoint_((5, 16.5))
    path.lineToPoint_((13, 16.5))
    path.moveToPoint_((19, 16.5))
    path.lineToPoint_((27, 16.5))
    path.moveToPoint_((16.5, 5))
    path.lineToPoint_((16.5, 13))
    path.moveToPoint_((16.5, 19))
    path.lineToPoint_((16.5, 27))
    path.setLineWidth_(1.0)
    if inDarkMode():
        AppKit.NSColor.blackColor().set()
    else:
        AppKit.NSColor.whiteColor().set()
    path.stroke()
    image.unlockFocus()
    return image


class MMTopographyDetailPopUp(InformationPopUpWindow):

    def __init__(self):
        posSize = (300, 280)
        super(MMTopographyDetailPopUp, self).__init__(posSize)

        titleWidth = 110
        entryLeft = 122

        self.side1GlyphTitle = HUDTextBox((10, 10, titleWidth, 17), "Side 1 Glyph:", alignment="right")
        self.side1Glyph = HUDTextBox((entryLeft, 10, -10, 17), "")
        self.side2GlyphTitle = HUDTextBox((10, 30, titleWidth, 17), "Side 2 Glyph:", alignment="right")
        self.side2Glyph = HUDTextBox((entryLeft, 30, -10, 17), "")
        self.valueTitle = HUDTextBox((10, 50, titleWidth, 17), "Value:", alignment="right")
        self.value = HUDTextBox((entryLeft, 50, -10, 17), "")

        self.side1GroupTitle = HUDTextBox((10, 80, titleWidth, 17), "Side 1 Group:", alignment="right")
        self.side1Group = HUDTextBox((entryLeft, 80, -10, 17), "")
        self.side2GroupTitle = HUDTextBox((10, 100, titleWidth, 17), "Side 2 Group:", alignment="right")
        self.side2Group = HUDTextBox((entryLeft, 100, -10, 17), "")

        self.side1ScriptTitle = HUDTextBox((10, 130, titleWidth, 17), "Side 1 Script:", alignment="right")
        self.side1Script = HUDTextBox((entryLeft, 130, -10, 17), "")
        self.side2ScriptTitle = HUDTextBox((10, 150, titleWidth, 17), "Side 2 Script:", alignment="right")
        self.side2Script = HUDTextBox((entryLeft, 150, -10, 17), "")

        self.side1CategoryTitle = HUDTextBox((10, 180, titleWidth, 17), "Side 1 Category:", alignment="right")
        self.side1Category = HUDTextBox((entryLeft, 180, -10, 17), "")
        self.side2CategoryTitle = HUDTextBox((10, 200, titleWidth, 17), "Side 2 Category:", alignment="right")
        self.side2Category = HUDTextBox((entryLeft, 200, -10, 17), "")

        self.side1SuffixTitle = HUDTextBox((10, 230, titleWidth, 17), "Side 1 Suffix:", alignment="right")
        self.side1Suffix = HUDTextBox((entryLeft, 230, -10, 17), "")
        self.side2SuffixTitle = HUDTextBox((10, 250, titleWidth, 17), "Side 2 Suffix:", alignment="right")
        self.side2Suffix = HUDTextBox((entryLeft, 250, -10, 17), "")

    @python_method
    def set(self, category, script, suffix, pair, groups, value):
        # category
        if category is not None:
            side1Category, side2Category = category
        else:
            side1Category = side2Category = ""
        side1Category = unicodeCategoryTranslation.get(side1Category, side1Category)
        side2Category = unicodeCategoryTranslation.get(side2Category, side2Category)
        if side1Category is None:
            side1Category = ""
        if side2Category is None:
            side2Category = ""
        # script
        if script is not None:
            side1Script, side2Script = script
        else:
            side1Script = side2Script = ""
        # suffix
        if suffix is not None:
            _side1Suffix, _side2Suffix = suffix
        else:
            _side1Suffix = _side2Suffix = ""
        # pair
        if pair is not None:
            side1Glyph, side2Glyph = pair
            value = str(int(round(value)))
        else:
            side1Glyph = side2Glyph = value = ""
        if side1Glyph is None or side2Glyph is None:
            value = ""
        if side1Glyph is None:
            side1Glyph = ""
        if side2Glyph is None:
            side2Glyph = ""
        # groups
        if groups is not None:
            side1Group, side2Group = groups
        else:
            side1Group = side2Group = ""
        if side1Group is None:
            side1Group = ""
        if side2Group is None:
            side2Group = ""
        side1Group = userFriendlyGroupName(side1Group)
        side2Group = userFriendlyGroupName(side2Group)
        # set
        self.side1Category.set(side1Category)
        self.side2Category.set(side2Category)
        self.side1Script.set(side1Script)
        self.side2Script.set(side2Script)
        self.side1Suffix.set(_side1Suffix)
        self.side2Suffix.set(_side2Suffix)
        self.side1Glyph.set(side1Glyph)
        self.side2Glyph.set(side2Glyph)
        self.value.set(value)
        self.side1Group.set(side1Group)
        self.side2Group.set(side2Group)

    @python_method
    def setPosition(self, xy):
        x, y = xy
        screen = self._window.screen()
        if screen is None:
            return
        screenFrame = screen.visibleFrame()
        (screenMinX, screenMinY), (screenW, screenH) = screenFrame
        screenMaxX = screenMinX + screenW
        screenMaxY = screenMinY + screenH

        cursorOffset = 16

        x += cursorOffset
        y -= cursorOffset

        windowW, windowH = self._window.frame().size
        if x + windowW > screenMaxX:
            x = x - windowW - (cursorOffset * 2)
        elif x < screenMinX:
            x = screenMinX + cursorOffset
        if y > screenMaxY:
            y = screenMaxY
        elif y - windowH < screenMinY:
            y = screenMinY + windowH

        self._window.setFrameTopLeftPoint_((x, y))


# ---------------
# external object
# ---------------


class TopographyView(MMScrollView):

    topographyViewClass = MMTopographyView
    showPlacard = True

    def __init__(self, posSize, font, selectionCallback=None):
        self._selectionCallback = selectionCallback
        self._topographyView = None

        font.kerning.addObserver(self, "_kerningChanged", "Kerning.PairSet")
        font.kerning.addObserver(self, "_kerningChanged", "Kerning.PairDeleted")
        addObserver(self, "updateBackgroundColor", "appearanceChanged")

        glyphNames = sortGlyphNames(font)
        glyphs = [font[glyphName] for glyphName in glyphNames]
        self._font = font
        self._allGlyphNames = [glyph.name for glyph in glyphs]

        super(TopographyView, self).__init__(posSize, MMBaseView.alloc().init(),
            autohidesScrollers=False, backgroundColor=AppKit.NSColor.grayColor())
        self._loadView()

        if self.showPlacard:
            placardW = 55
            placardH = 16
            self._placardOptions = [str(i) for i in range(1, 11)]
            self._placard = vanilla.Group((0, 0, placardW, placardH))
            self._placard.button = PlacardPopUpButton((0, 0, placardW, placardH),
                self._placardOptions, callback=self._placardSelection, sizeStyle="mini")
            self._placard.button.set(2)
            self.setPlacard(self._placard)
            self.updateBackgroundColor(None)


    def updateBackgroundColor(self, info):
        # Unwrap from try/except once RoboFont 4.5p is released.
        try:
            if inDarkMode():
                self._placard.button.setBackgroundColor(AppKit.NSColor.blackColor())
            else:
                self._placard.button.setBackgroundColor(AppKit.NSColor.whiteColor())
        except:
            pass

    def _breakCycles(self):
        super(TopographyView, self)._breakCycles()
        if self._font is not None:
            self._font.kerning.removeObserver(self, "Kerning.PairSet")
            self._font.kerning.removeObserver(self, "Kerning.PairDeleted")
        removeObserver(self, "appearanceChanged")
        self._selectionCallback = None
        self._font = None
        self._topographyView = None
        self._placard = None

    def _loadView(self):
        self._flatPairs = self._font.kerning.metricsMachine.getFlatKerning()
        self._topographyView = self.topographyViewClass.alloc().initWithFont_(self._font)
        self._topographyView.setGlyphsSide1_side2_(self._allGlyphNames, self._allGlyphNames)
        self._topographyView.vanillaWrapper = weakref.ref(self)
        self._topographyView.setFlatPairs_(self._flatPairs)
        self._nsObject.setDocumentView_(self._topographyView)

    def _placardSelection(self, sender):
        index = sender.get()
        size = self._placardOptions[index]
        size = int(size)
        self._topographyView.setBlockSize_(size)

    def _selection(self):
        if self._selectionCallback is not None:
            self._selectionCallback(self)

    def _kerningChanged(self, notification):
        pairs = {}
        pair = notification.data["key"]
        pairs[pair] = self._font.kerning.metricsMachine[pair]
        newFlatPairs = self._font.kerning.metricsMachine.getFlatKerning(pairs)
        self._flatPairs.update(newFlatPairs)
        self._topographyView.setFlatPairs_(self._flatPairs)

    # ------------
    # external API
    # ------------

    def get(self):
        if self._topographyView is not None:
            return self._topographyView.get()
