import codecs
import AppKit
import vanilla
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
from mm4.tools.patternMatching import searchGlyphList, isValidExpression
from mm4.interface.formatters import GroupNameFormatter
from mm4.interface.glyphSortDescriptors import sortGlyphNames
from mm4.interface.glyphCellItem import MMGlyphCellItem
from mm4.tools.pairListBuilder import createPairs


class PairListBuilderSheet(BaseWindowController):

    def __init__(self, parentWindow, font, progressSheet=None, setCallback=None):
        self.font = font
        self.setCallback = setCallback

        sortedGlyphNames = sortGlyphNames(font)
        self._allGlyphs = [font[glyphName] for glyphName in sortedGlyphNames]

        size = (780, 600)
        self.w = vanilla.Sheet(size, parentWindow=parentWindow, minSize=size)

        formatter = GroupNameFormatter.alloc().init()
        collectionListColumnDescriptions = [
            dict(title="Name"),
            dict(title="Side 1 Group", key="side1GroupName", formatter=formatter),
            dict(title="Side 2 Group", key="side2GroupName", formatter=formatter),
        ]

        # source
        sourceGroupView = vanilla.Group((0, 0, 0, 0))
        sourceGroupView.sourceSearchBox = self.sourceSearchBox = vanilla.SearchBox((0, 0, -160, 22), callback=self.filterSourceCallback)
        sourceGroupView.sourceHideTitle = vanilla.TextBox((-150, 5, 35, 17), "Hide:", sizeStyle="small")
        sourceGroupView.sourceHideSide1CheckBox = self.sourceHideSide1CheckBox = vanilla.CheckBox((-115, 3, 50, 18), "Side 1", callback=self.filterSourceCallback, sizeStyle="small")
        sourceGroupView.sourceHideSide2CheckBox = self.sourceHideSide2CheckBox = vanilla.CheckBox((-55, 3, 50, 18), "Side 2", callback=self.filterSourceCallback, sizeStyle="small")
        sourceGroupView.sourceCollectionView = self.sourceCollectionView = GlyphCollectionView((0, 35, 0, 0), initialMode="cell",
            listColumnDescriptions=collectionListColumnDescriptions, allowDrag=True, listShowColumnTitles=True,
            cellRepresentationName="NoLayerGlyphCell")
        sourceGroupView.sourceCollectionView.glyphCellItemClass = MMGlyphCellItem
        sourceGroupView.sourceCollectionView.setCellSize((42, 56))
        sourceGroupView.sourceCollectionView.setCellRepresentationArguments(drawHeader=True)
        sourceGroupView.sourceCollectionView.set(self._allGlyphs)

        # side1 and side2
        dropSettings = dict(
            callback=self.sideDropCallback,
            allowsDropOnRows=False,
            allowsDropBetweenRows=False
        )
        self.side1CellView = GlyphCollectionView((0, 0, 0, 0),
            deleteCallback=self.sideDeleteCallback, selfWindowDropSettings=dropSettings,
            enableDelete=True, allowDrag=True, glyphDetailWindowClass=None,
            cellRepresentationName="NoLayerGlyphCell")
        self.side1CellView.setCellSize((42, 56))
        self.side1CellView.setCellRepresentationArguments(drawHeader=True)

        self.side2CellView = GlyphCollectionView((0, 0, 0, 0),
            deleteCallback=self.sideDeleteCallback, selfWindowDropSettings=dropSettings,
            enableDelete=True, allowDrag=True, glyphDetailWindowClass=None,
            cellRepresentationName="NoLayerGlyphCell")
        self.side2CellView.setCellSize((42, 56))
        self.side2CellView.setCellRepresentationArguments(drawHeader=True)

        paneDescriptions = [
            dict(view=self.side1CellView, identifier="side1CellView", minSize=50, canCollapse=False),
            dict(view=self.side2CellView, identifier="side2CellView", minSize=50, canCollapse=False)
        ]
        pairSplitView = vanilla.SplitView((0, 0, 0, 0), paneDescriptions=paneDescriptions, isVertical=True, dividerStyle="thick")

        # split view
        paneDescriptions = [
            dict(view=sourceGroupView, size=350, minSize=100, maxSize=10000, canCollapse=False, identifier="sourceCollectionView"),
            dict(view=pairSplitView, canCollapse=False, minSize=100, identifier="pairSplitView")
        ]
        self.w.splitView = vanilla.SplitView((15, 15, -285, -65), paneDescriptions=paneDescriptions, isVertical=False, dividerStyle="thick")

        # results
        self.w.resultsLine = vanilla.VerticalLine((-270, 15, 1, -65))

        self.w.titleTextField = vanilla.EditText((-255, 15, -15, 22), "My Pair List")

        self.w.complieButton = vanilla.Button((-255, 50, 85, 20), "Compile", self.compileCallback)
        self.w.importButton = vanilla.Button((-255, 80, 85, 20), "Import", callback=self.importPairListCallback)

        self.w.compileLine = vanilla.VerticalLine((-155, 50, 1, 84))

        self.w.compileFlipCheckBox = vanilla.CheckBox((-140, 50, -15, 18), "Create Flipped", sizeStyle="small")
        self.w.compileAvoidDuplicatesCheckBox = vanilla.CheckBox((-140, 67, -15, 18), "Avoid Duplicates", sizeStyle="small")
        self.w.compileCompressGroupsCheckBox = vanilla.CheckBox((-140, 84, -15, 18), "Compress Groups", sizeStyle="small")
        self.w.createOpenCloseCheckBox = vanilla.CheckBox((-140, 101, -15, 18), "Create Open+Close", sizeStyle="small")
        self.w.createCloseOpenCheckBox = vanilla.CheckBox((-140, 118, -15, 18), "Create Close+Open", sizeStyle="small")

        columnDescriptions = [
            dict(title="side1", width=120),
            dict(title="side2", width=120),
        ]
        self.w.resultList = vanilla.List((-255, 144, -15, -65), [], columnDescriptions=columnDescriptions,
            showColumnTitles=False, enableDelete=True)

        # bottom
        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))

        self.w.sortDropCheckBox = vanilla.CheckBox((15, -32, 150, 18), "Sort Dropped Glyphs", value=True, callback=self.sortDropCallback, sizeStyle="small")

        self.w.saveButton = vanilla.Button((-256, -35, 75, 20), "Save", callback=self.savePairListCallback)
        self.w.useButton = vanilla.Button((-173, -35, 75, 20), "Use", callback=self.usePairListCallback)
        self.w.closeButton = vanilla.Button((-90, -35, 75, 20), "Close", callback=self.closeCallback)

        self._lastSave = self._getPairListText()
        self._pairUniqueID = 0

        self.setUpBaseWindowBehavior()
        if progressSheet:
            self.sourceCollectionView.preloadGlyphCellImages()
            progressSheet.close()
        self.w.open()

    # --------------
    # exit callbacks
    # --------------

    def _needSave(self):
        current = self._getPairListText()
        return current != self._lastSave

    def savePairListCallback(self, sender):
        if not self.w.resultList.get():
            AppKit.NSBeep()
            return
        title = self.w.titleTextField.get()
        if not title:
            title = "Untitled Pair List"
        fileName = title + ".txt"
        self.showPutFile(["txt"], callback=self._savePairListCallback, fileName=fileName)

    def _savePairListCallback(self, path):
        if not path:
            return
        text = self._getPairListText()
        f = codecs.open(path, "wb", encoding="utf8")
        f.write(text)
        f.close()
        self._lastSave = text

    def usePairListCallback(self, sender):
        if not self.w.resultList.get():
            AppKit.NSBeep()
            return
        text = self._getPairListText()
        self.setCallback(text)
        self._closeCallback(1)

    def closeCallback(self, sender):
        if not self._needSave():
            self._closeCallback(1)
        else:
            messageText = "You have unsaved changes. Do you really want to close this window?"
            informativeText = "Your changes will be lost if you don't save them."
            self.showAskYesNo(informativeText=informativeText, messageText=messageText, callback=self._closeCallback)

    def _closeCallback(self, result):
        if result:
            self.w.close()
            self.setCallback = None

    # ------------------
    # member compilation
    # ------------------

    def filterSourceCallback(self, sender=None):
        pattern = self.sourceSearchBox.get()
        if pattern and not isValidExpression(pattern, allowGroups=True, allowReferenceGroups=True):
            self.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.redColor())
            return
        else:
            self.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.blackColor())
        glyphs = self._allGlyphs
        glyphNames = [glyph.name for glyph in glyphs]
        ignoreSide1 = self.sourceHideSide1CheckBox.get()
        ignoreSide2 = self.sourceHideSide2CheckBox.get()
        if ignoreSide1:
            side1 = set(self.side1CellView.getGlyphNames())
            glyphNames = [glyphName for glyphName in glyphNames if glyphName not in side1]
        if ignoreSide2:
            side2 = set(self.side2CellView.getGlyphNames())
            glyphNames = [glyphName for glyphName in glyphNames if glyphName not in side2]
        if pattern:
            font = self.font
            result = searchGlyphList(pattern, glyphNames, groups=font.groups, expandGroups=True)
            filtered = []
            for i in result:
                if i.startswith(side1Prefix) or i.startswith(side2Prefix):
                    if i not in font.groups:
                        continue
                    filtered += font.groups[i]
                else:
                    filtered.append(i)
            glyphNames = [glyphName for glyphName in glyphNames if glyphName in filtered]

        if glyphNames != self.sourceCollectionView.getGlyphNames():
            self.sourceCollectionView.setGlyphNames(glyphNames)

    def sideDropCallback(self, sender, dropInfo):
        glyphs = dropInfo["data"]
        isProposal = dropInfo["isProposal"]
        if not isProposal:
            existing = sender.get()
            added = [glyph for glyph in glyphs if glyph not in existing]
            if not added:
                return False
            glyphs = existing + added
            sender.set(glyphs)
            if self.w.sortDropCheckBox.get():
                self._sortDroppedGlyphs(sender)
            self.filterSourceCallback()
        return True

    def _sortDroppedGlyphs(self, sender):
        glyphs = sender.get()
        glyphNames = [glyph.name for glyph in glyphs]
        sortedNames = sortGlyphNames(self.font, glyphNames)
        glyphs = [self.font[glyphName] for glyphName in sortedNames]
        sender.set(glyphs)

    def sortDropCallback(self, sender):
        if sender.get():
            self._sortDroppedGlyphs(self.side1CellView)
            self._sortDroppedGlyphs(self.side2CellView)

    def sideDeleteCallback(self, sender):
        self.filterSourceCallback()

    # -----------
    # result list
    # -----------

    def _wrapPairs(self, pairs):
        wrapList = []
        for side1, side2 in pairs:
            wrapList.append(dict(side1=side1, side2=side2, id=self._pairUniqueID))
            self._pairUniqueID += 1
        return wrapList

    def _unpackList(self):
        pairs = []
        for d in self.w.resultList.get():
            pairs.append((d["side1"], d["side2"]))
        return pairs

    def _getPairListText(self):
        title = self.w.titleTextField.get()
        if not title:
            title = "Untitled Pair List"
        lines = ["#KPL:P: %s" % title]
        pairs = self._unpackList()
        for side1, side2 in pairs:
            lines.append("%s %s" % (side1, side2))
        text = "\n".join(lines)
        return text

    def importPairListCallback(self, sender):
        self.showGetFile(["txt"], self._importPairListCallbackResult, allowsMultipleSelection=False)

    def _importPairListCallbackResult(self, path):
        from mm4.tools.pairListParser import parsePairList
        if not path:
            return
        path = path[0]
        text = ""
        with open(path, "r") as f:
            text = f.read()
        result = parsePairList(text, self.font)
        if isinstance(result, str):
            self.showMessage("The file could not be loaded.", result)
        else:
            pairs, mode, title = result
            pairs = [pair for pair, word in pairs]
            pairs = self._wrapPairs(pairs)
            self.w.resultList.set(pairs)

    # -------
    # compile
    # -------

    def compileCallback(self, sender):
        side1Glyphs = self.side1CellView.get()
        side1Glyphs = [glyph.name for glyph in side1Glyphs]
        side2Glyphs = self.side2CellView.get()
        side2Glyphs = [glyph.name for glyph in side2Glyphs]

        result = createPairs(
            side1Glyphs, side2Glyphs,
            font=self.font,
            createFlipped=self.w.compileFlipCheckBox.get(),
            createOpenClose=self.w.createOpenCloseCheckBox.get(),
            createCloseOpen=self.w.createCloseOpenCheckBox.get(),
            compressGroups=self.w.compileCompressGroupsCheckBox.get(),
            avoidDuplicates=self.w.compileAvoidDuplicatesCheckBox.get(),
            existingPairs=self._unpackList()
        )
        result = self._wrapPairs(result)
        self.w.resultList.extend(result)
