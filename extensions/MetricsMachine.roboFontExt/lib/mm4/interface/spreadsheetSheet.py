
import AppKit
import vanilla
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.glyphLineView import GlyphLineView
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
from mm4.interface.formatters import PairMemberFormatter, KerningValueFormatter
from mm4.interface.views.topographyView import TopographyView
from mm4.tools.patternMatching import isValidKerningExpression, searchKerningPairList, searchGlyphList, isValidExpression
from mm4.interface.glyphSortDescriptors import sortGlyphNames
from mm4.interface.glyphCellItem import MMGlyphCellItem
from mm4.interface.tempFontWrapper import FontWrapper
from mojo.events import addObserver, removeObserver
from mojo.UI import inDarkMode
from mojo.extensions import getExtensionDefault
from mojo.tools import CallbackWrapper


pairIndicatingCellName = "PairCountIndicatingGlyphCell"


class SpreadsheetSheet(BaseWindowController):

    def __init__(self, parentWindow, font, progress):
        self._inPairListReloadLoop = False

        self.tempFontWrapper = FontWrapper(font)
        self.tempFontWrapper.setGroups(font.groups)
        self.tempFontWrapper.setKerning(font.kerning)
        self.font = font

        self.subscribe()

        minWidth = 677
        self.w = vanilla.Sheet((minWidth, 500), parentWindow=parentWindow, minSize=(minWidth, 100))

        self.w.tabButtonsLine = vanilla.HorizontalLine((15, 50, -15, 1))
        self.w.tabButtons = vanilla.SegmentedButton((235, 15, 230, 24), [dict(title="Pair List"), dict(title="Topography"), dict(title="Glyphs")], callback=self.tabSelectionCallback, sizeStyle="regular")
        self.w.tabButtons.set(0)
        self.w.tabButtons.getNSSegmentedButton().setAutoresizingMask_(AppKit.NSViewMinYMargin | AppKit.NSViewMinXMargin | AppKit.NSViewMaxXMargin)

        pairMemberFormatter = PairMemberFormatter.alloc().init()
        numberFormatter = KerningValueFormatter()

        self.tabs = vanilla.Tabs((0, 0, -0, -0), ["Pair List", "Topography", "Spreadsheet"])
        self.tabs.getNSTabView().setTabViewType_(AppKit.NSNoTabsNoBorder)

        # pair list tab
        pairListTab = self.tabs[0]

        valueWidth = 50
        columnDescriptions = [
            dict(title="Side 1", key="side1", editable=False, formatter=pairMemberFormatter, width=100, maxWidth=1000),
            dict(title="Side 2", key="side2", editable=False, formatter=pairMemberFormatter, width=100, maxWidth=1000),
            dict(title="Value", key="value", width=valueWidth, editable=True, formatter=numberFormatter),
            dict(title="Side 1 Exception", key="side1Exception", editable=False, formatter=pairMemberFormatter, width=150, maxWidth=1000),
            dict(title="Side 2 Exception", key="side2Exception", editable=False, formatter=pairMemberFormatter, width=150, maxWidth=1000),
            dict(title="Value", key="exceptionValue", width=valueWidth, editable=False),
        ]
        self.pairList = pairList = pairListTab.pairList = vanilla.List((0, 0, -0, -0), [], columnDescriptions=columnDescriptions,
            editCallback=self.pairListEditCallback, selectionCallback=self.pairListSelectionCallback,
            enableDelete=True, drawFocusRing=False
        )
        tableView = pairList.getNSTableView()
        for columnIndex in (2, 5):
            column = tableView.tableColumns()[columnIndex]
            # column.setMinWidth_(valueWidth)
            # column.setMaxWidth_(valueWidth)
            cell = column.dataCell()
            cell.setAlignment_(AppKit.NSRightTextAlignment)

        self.w.pairListSearchField = vanilla.SearchBox((15, -36, 300, 22), callback=self.pairListFilterCallback)

        # topography tab
        self.tabs[1].topographyView = TopographyView((0, 0, -0, -0), self.tempFontWrapper, self.topographySelectionCallback)

        # line view
        self.lineView = GlyphLineView((0, 0, 0, 0), pointSize=None, autohideScrollers=False, applyKerning=True)

        # split view
        paneDescriptions = [
            dict(view=self.tabs, size=200, minSize=100, canCollapse=False, identifier="editPane"),
            dict(view=self.lineView, canCollapse=True, identifier="typingPane")
        ]
        self.w.splitView = vanilla.SplitView((15, 65, -15, -65), paneDescriptions=paneDescriptions, isVertical=False, dividerStyle="thick")

        # glyph collection view
        self._glyphListVisibleGlyphs = font.keys()
        columnDescriptions = [
            dict(title="Name"),
            dict(title="Side 1 Group Count", key="side1GroupPairCount", formatter=numberFormatter),
            dict(title="Side 2 Group Count", key="side2GroupPairCount", formatter=numberFormatter),
            dict(title="Side 1 Glyph Count", key="side1GlyphPairCount", formatter=numberFormatter),
            dict(title="Side 2 Glyph Count", key="side2GlyphPairCount", formatter=numberFormatter),
            dict(title="Side 1 Exception Count", key="side1ExceptionPairCount", formatter=numberFormatter),
            dict(title="Side 2 Exception Count", key="side2ExceptionPairCount", formatter=numberFormatter),
        ]
        self.w.glyphCellView = GlyphCollectionView((15, 65, -15, -65),
            listColumnDescriptions=columnDescriptions, listShowColumnTitles=True,
            cellRepresentationName=pairIndicatingCellName)
        self.w.glyphCellView.glyphCellItemClass = MMGlyphCellItem
        self.w.glyphCellView.setCellSize((70, 66))
        self.populateCollectionView()
        self.w.glyphCellView.show(False)

        self.w.glyphsSearchField = vanilla.SearchBox((15, -36, 300, 22), callback=self.glyphsFilterCallback)
        self.w.glyphsSearchField.show(False)

        sortOptions = [
            "Glyph Description",
            "Side 1 Group Count",
            "Side 1 Glyph Count",
            "Side 1 Exception Count",
            "Side 2 Group Count",
            "Side 2 Glyph Count",
            "Side 2 Exception Count",
        ]
        self.w.sortPopUp = vanilla.PopUpButton((325, -35, 178, 20), sortOptions)
        self.w.sortPopUp.show(False)

        # bottom
        self.w.bind("resize", self.windowResizeCallback)
        self.windowResizeCallback(None)

        self._loadPairList()

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))

        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        progress.close()

        self.appearanceChanged(None) 
        addObserver(self, "updateGlyphLineViewColors", "com.typesupply.MM4.invertPreviewsSettingDidChange")
        addObserver(self, "appearanceChanged", "appearanceChanged")

        self.setUpBaseWindowBehavior()
        self.w.open()

    def windowResizeCallback(self, sender):
        self.pairList.getNSTableView().sizeToFit()

    def appearanceChanged(self, notification):
        self._clearAllRepresentations()
        self.updateGlyphCollectionBGColor()
        self.updateGlyphLineViewColors(None)

    def updateGlyphLineViewColors(self, notification):
        if not hasattr(self.lineView, "_glyphLineView"):
            return
        invertPreviews = getExtensionDefault("com.typesupply.MM4.viewSettings.general.invertPreviews", False)
        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
            self.lineView.setBackgroundColor(AppKit.NSColor.blackColor())
            self.lineView.setGlyphColor(AppKit.NSColor.whiteColor())
        else:
            self.lineView.setBackgroundColor(AppKit.NSColor.whiteColor())
            self.lineView.setGlyphColor(AppKit.NSColor.blackColor())

    # -------------
    # Notifications
    # -------------

    def _invertPreviewsSettingDidChange(self, notification):
        self.appearanceChanged(None)

    def _contextStringsChanged(self, notification):
        self.pairListSelectionCallback(self.pairList)

    def _kerningChanged(self, notification):
        pass
        # self._destroyGlyphCells()

    # ------------
    # Apply/Cancel
    # ------------

    def applyCallback(self, sender):
        self.font.kerning.clear()
        self.font.kerning.update(self.tempFontWrapper.kerning)
        self.unsubscribe()
        self.w.close()

    def cancelCallback(self, sender):
        self.unsubscribe()
        self.w.close()

    def subscribe(self):
        self.font.metricsMachine.contextStrings.addObserver(self, "_contextStringsChanged", "MMContextStrings.Changed")
        self.tempFontWrapper.kerning.addObserver(self, "_kerningChanged", "Kerning.Changed")

    def unsubscribe(self):
        self.font.metricsMachine.contextStrings.removeObserver(self, "MMContextStrings.Changed")
        self.tempFontWrapper.kerning.removeObserver(self, "Kerning.Changed")
        removeObserver(self, "appearanceChanged")
        removeObserver(self, "com.typesupply.MM4.invertPreviewsSettingDidChange")
        del self.tempFontWrapper

    # -----------
    # Mode Switch
    # -----------

    def tabSelectionCallback(self, sender):
        index = sender.get()
        mode = ["pairs", "topography", "glyphs"][index]
        # turn things off
        if mode != "pairs":
            self.setModeNotPairs()
        if mode != "topography":
            self.setModeNotTopography()
        if mode != "glyphs":
            self.setModeNotGlyphs()
        # turn things on
        if mode == "pairs":
            self.setModePairs()
        elif mode == "topography":
            self.setModeTopography()
        else:
            self.setModeGlyphs()

    # ---------
    # Line View
    # ---------

    def _setLineView(self, side1, side2):
        if side1 is None or side2 is None:
            glyphs = []
        else:
            font = self.tempFontWrapper
            groups = font.groups
            if side1.startswith(side1Prefix):
                side1 = groups[side1]
                if not side1:
                    side1 = None
                else:
                    side1 = sorted(side1)[0]
            if side2.startswith(side2Prefix):
                side2 = groups[side2]
                if not side2:
                    side2 = None
                else:
                    side2 = sorted(side2)[0]
            glyphs, _ = font.contextStrings.getLongContext((side1, side2))
        glyphs = [glyph for glyph in glyphs if not glyph.template]
        self.lineView.set(glyphs)

    # ---------
    # Pair List
    # ---------

    def setModePairs(self):
        self.w.splitView.show(True)
        self.tabs.set(0)
        self._loadPairList()
        self.pairListFilterCallback(self.w.pairListSearchField)
        self.w.pairListSearchField.show(True)

    def setModeNotPairs(self):
        self.w.splitView.show(False)
        self.w.pairListSearchField.show(False)

    def _loadPairList(self):
        self._inPairListReloadLoop = True
        kerning = self.tempFontWrapper.kerning.metricsMachine
        self._pairListMutablePairs = {}
        self._paiListVisiblePairs = set(kerning.keys())
        pairs = [self._wrapPairForList(pair, kerning[pair]) for pair in kerning.sortedPairs()]
        self.pairList.set(pairs)
        self._inPairListReloadLoop = False

    def _wrapPairForList(self, pair, value):
        kerning = self.tempFontWrapper.kerning
        groups = self.tempFontWrapper.groups
        side1, side2 = pair
        side1Type, side2Type = kerning.metricsMachine.getPairType(pair)
        if side1Type == "exception":
            side1Exception = groups.metricsMachine.getSide1GroupForGlyph(side1)
        else:
            side1Exception = ""
        if side2Type == "exception":
            side2Exception = groups.metricsMachine.getSide2GroupForGlyph(side2)
        else:
            side2Exception = ""
        exceptionValue = ""
        if side1Exception or side2Exception:
            if side1Exception and side2Exception:
                exceptionValue = kerning.metricsMachine[side1Exception, side2Exception]
            elif side1Exception:
                exceptionValue = kerning.metricsMachine[side1Exception, side2]
            else:
                exceptionValue = kerning.metricsMachine[side1, side2Exception]
            # make a string
            if exceptionValue == int(exceptionValue):
                exceptionValue = str(int(exceptionValue))
            else:
                exceptionValue = str(round(exceptionValue, 2))
        if (side1, side2) in self._pairListMutablePairs:
            d = self._pairListMutablePairs[side1, side2]
        else:
            d = AppKit.NSMutableDictionary.dictionaryWithDictionary_({})
            self._pairListMutablePairs[side1, side2] = d
        d["side1"] = side1
        d["side2"] = side2
        d["value"] = value
        d["side1Exception"] = side1Exception
        d["side2Exception"] = side2Exception
        d["exceptionValue"] = exceptionValue
        return d

    def pairListEditCallback(self, sender):
        if self._inPairListReloadLoop:
            return
        # pair was deleted
        if len(sender) != len(self._paiListVisiblePairs):
            inList = set([(d["side1"], d["side2"]) for d in sender])
            deleted = self._paiListVisiblePairs - inList
            self.tempFontWrapper.kerning.metricsMachine.removePairs(deleted)
            for pair in deleted:
                del self._pairListMutablePairs[pair]
                self._paiListVisiblePairs.remove(pair)
        # edited a pair
        else:
            selectionIndexes = sender.getSelection()
            if not selectionIndexes:
                return
            selectionIndex = selectionIndexes[0]
            selection = sender[selectionIndex]
            side1 = selection["side1"]
            side2 = selection["side2"]
            value = selection["value"]
            self.tempFontWrapper.kerning.metricsMachine[side1, side2] = value
            # update the list to make sure proper
            # exception values are displayed.
            self._inPairListReloadLoop = True
            for pair, value in self.tempFontWrapper.kerning.items():
                self._wrapPairForList(pair, value)
            self._inPairListReloadLoop = False

    def pairListSelectionCallback(self, sender):
        selectionIndexes = sender.getSelection()
        if not len(selectionIndexes) == 1:
            self._setLineView(None, None)
        else:
            selectionIndex = selectionIndexes[0]
            selection = sender[selectionIndex]
            side1 = selection["side1"]
            side2 = selection["side2"]
            self._setLineView(side1, side2)

    def pairListFilterCallback(self, sender):
        kerning = self.tempFontWrapper.kerning.metricsMachine
        text = sender.get()
        if text and not isValidKerningExpression(text):
            sender.getNSSearchField().setTextColor_(AppKit.NSColor.redColor())
            return
        else:
            sender.getNSSearchField().setTextColor_(AppKit.NSColor.blackColor())
        if text:
            visiblePairs = searchKerningPairList(text, self._pairListMutablePairs.keys(), self.tempFontWrapper)
            self._paiListVisiblePairs = set(visiblePairs)
            visiblePairs = [self._pairListMutablePairs[pair] for pair in kerning.sortedPairs(visiblePairs)]
        else:
            visiblePairs = [self._pairListMutablePairs[pair] for pair in kerning.sortedPairs(self._pairListMutablePairs.keys())]
            self._paiListVisiblePairs = set(self._pairListMutablePairs.keys())
        self._inPairListReloadLoop = True
        self.pairList.set(visiblePairs)
        self._inPairListReloadLoop = False

    # ----------
    # Topography
    # ----------

    def setModeTopography(self):
        self.w.splitView.show(True)
        self.tabs.set(1)

    def setModeNotTopography(self):
        self.w.splitView.show(False)

    def topographySelectionCallback(self, sender):
        pair = sender.get()
        if not pair:
            glyphs = []
        else:
            font = self.tempFontWrapper
            glyphs, _ = font.contextStrings.getLongContext(pair)
        glyphs = [glyph for glyph in glyphs if not glyph.template]
        self.lineView.set(glyphs)

    # ---------
    # Cell View
    # ---------

    def setModeGlyphs(self):
        self.w.glyphCellView.show(True)
        self.w.sortPopUp.show(True)
        self.w.glyphsSearchField.show(True)

    def setModeNotGlyphs(self):
        self.w.glyphCellView.show(False)
        self.w.sortPopUp.show(False)
        self.w.glyphsSearchField.show(False)

    def populateCollectionView(self):
        glyphNames = self._glyphListVisibleGlyphs
        glyphNames = sortGlyphNames(self.font, glyphNames)
        glyphs = [self.tempFontWrapper[glyphName] for glyphName in glyphNames]
        self.w.glyphCellView.set(glyphs)

    def glyphsFilterCallback(self, sender):
        pattern = sender.get()
        if pattern.strip() and not isValidExpression(pattern, allowGroups=True, allowReferenceGroups=True):
            sender.getNSSearchField().setTextColor_(AppKit.NSColor.redColor())
            return
        else:
            sender.getNSSearchField().setTextColor_(AppKit.NSColor.blackColor())
        self._glyphListVisibleGlyphs = searchGlyphList(pattern, self.font.keys(), groups=self.font.groups, expandGroups=True)
        self.populateCollectionView()

    def updateGlyphCollectionBGColor(self): 
        if inDarkMode():
            backgroundColor = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .2, .2, 1.0)
        else:
            backgroundColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.6, 1.0)
        self.w.glyphCellView._glyphCellView.backgroundColor = backgroundColor
        self.w.glyphCellView._glyphCellView.gridColor = backgroundColor
        self.w.glyphCellView._glyphCellView.setNeedsDisplay_(True)

    def _clearAllRepresentations(self):
        font = self.font
        for glyphName in font.keys():
            font[glyphName].destroyRepresentation(pairIndicatingCellName)
