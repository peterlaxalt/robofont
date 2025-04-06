import AppKit
import vanilla

from mm4.tools.patternMatching import isValidKerningExpression, searchKerningPairList
from mm4.interface.formatters import KerningValueFormatter


class PairList(vanilla.Group):

    def __init__(self, posSize, font, selectionCallback):
        super(PairList, self).__init__(posSize)
        self.font = font
        self.font.kerning.addObserver(self, "_kerningPairSetChanged", "Kerning.PairSet")
        self.font.kerning.addObserver(self, "_kerningPairDeletedChanged", "Kerning.PairDeleted")
        self.font.kerning.addObserver(self, "_kerningClearedChanged", "Kerning.Cleared")
        self.font.kerning.addObserver(self, "_kerningUpdatedChanged", "Kerning.Updated")
        self._selectionCallback = selectionCallback

        self._originalList = []
        self._indexMap = {}

        formatter = KerningValueFormatter()

        columnDescriptions = [
            dict(title="side1"),
            dict(title="side2"),
            dict(title="value", formatter=formatter),
        ]
        self.list = vanilla.List(posSize, [], columnDescriptions=columnDescriptions,
            showColumnTitles=False, allowsEmptySelection=False, allowsMultipleSelection=False,
            selectionCallback=self._pairListSelectionCallback, drawFocusRing=False)

        for i, column in enumerate(self.list.getNSTableView().tableColumns()):
            if column.title() == "value":
                cell = column.dataCell()
                cell.setAlignment_(AppKit.NSRightTextAlignment)
                column.setResizingMask_(AppKit.NSTableColumnNoResizing)
                column.setWidth_(50)
            else:
                column.setResizingMask_(AppKit.NSTableColumnAutoresizingMask)
        self.list.getNSTableView().sizeToFit()

        # filter
        self.filterBoxHeight = 32
        filterGroup = vanilla.Group((0, -self.filterBoxHeight, -0, self.filterBoxHeight))
        filterGroup.frameAdjustments = (-1, 0, 1, 1)
        filterGroup.searchBox = vanilla.SearchBox((10, 10, -10, 22), callback=self._filterCallback)
        filterGroup.searchBox.getNSSearchField().setFocusRingType_(AppKit.NSFocusRingTypeNone)
        filterGroup.line = vanilla.VerticalLine((-1, 0, 1, -1))
        self.filterGroup = filterGroup
        self.filterGroup.show(False)

    def set(self, items):
        self._originalList = items
        self._setList(items)
        self.filterGroup.searchBox.set("")

    def _setList(self, items):
        self._indexMap = {}
        wrapped = []
        for index, ((side1, side2), context) in enumerate(items):
            value = self.font.kerning.metricsMachine[side1, side2]
            d = dict(side1=side1, side2=side2, value=value, context=context)
            wrapped.append(d)
            if (side1, side2) not in self._indexMap:
                self._indexMap[side1, side2] = []
            self._indexMap[side1, side2].append(index)
        self.list.set(wrapped)

    def getSelection(self):
        selection = self.list.getSelection()
        if not selection:
            return None
        index = selection[0]
        d = self.list[index]
        side1 = d["side1"]
        side2 = d["side2"]
        context = d["context"]
        return (side1, side2), context, index

    def setSelection(self, pair):
        if pair not in self._indexMap:
            return
        indexes = self._indexMap[pair]
        if len(indexes) == 1:
            index = indexes[0]
        else:
            # pair is in the list more than once.
            # locate the instance of the pair closest
            # to the current selection. it also attempts
            # to go up the list rather than down.
            distances = []
            currentIndex = self.list.getSelection()[0]
            for index in indexes:
                dist = abs(index - currentIndex)
                if index < currentIndex:
                    direction = 0
                else:
                    direction = 1
                distances.append((dist, direction, index))
            index = min(distances)[2]
        self.list.setSelection([index])

    def isFilterVisible(self):
        return self.filterGroup.isVisible()

    def toggleFilter(self):
        if self.filterGroup.isVisible():
            x, y, w, h = self.list.getPosSize()
            h = -0
            self.list.setPosSize((x, y, w, h))
            self.filterGroup.show(False)
        else:
            x, y, w, h = self.list.getPosSize()
            h = -self.filterBoxHeight
            self.list.setPosSize((x, y, w, h))
            self.filterGroup.show(True)

    def selectNextPair(self):
        if not len(self.list):
            return
        index = self.list.getSelection()[0]
        if index < len(self.list) - 1:
            self.list.setSelection([index + 1])

    def selectPreviousPair(self):
        if not len(self.list):
            return
        index = self.list.getSelection()[0]
        if index > 0:
            self.list.setSelection([index - 1])

    def _breakCycles(self):
        if self.font is not None:
            self.font.kerning.removeObserver(self, "Kerning.PairSet")
            self.font.kerning.removeObserver(self, "Kerning.PairDeleted")
            self.font.kerning.removeObserver(self, "Kerning.Cleared")
            self.font.kerning.removeObserver(self, "Kerning.Updated")
        self.font = None
        self._selectionCallback = None
        super(PairList, self)._breakCycles()

    def _pairListSelectionCallback(self, sender):
        if self._selectionCallback is not None:
            self._selectionCallback(self)

    def _findChangedPair(self, changedPair):
        mmgroups = self.font.groups.metricsMachine
        getSide1GroupForGlyph = mmgroups.getSide1GroupForGlyph
        getSide2GroupForGlyph = mmgroups.getSide2GroupForGlyph
        needUpdating = set()
        for pair in self._indexMap.keys():
            side1, side2 = pair
            if pair == changedPair:
                needUpdating.add(pair)
                continue
            side1Group = getSide1GroupForGlyph(side1)
            side2Group = getSide2GroupForGlyph(side2)
            if (side1Group, side2) == changedPair:
                needUpdating.add(pair)
            elif (side1, side2Group) == changedPair:
                needUpdating.add(pair)
            elif (side1Group, side2Group) == changedPair:
                needUpdating.add(pair)
        return needUpdating

    # filter

    def _filterCallback(self, sender):
        text = sender.get()
        if text and not isValidKerningExpression(text, allowGroups=False, allowVariables=False):
            sender.getNSSearchField().setTextColor_(AppKit.NSColor.redColor())
            return
        else:
            sender.getNSSearchField().setTextColor_(AppKit.NSColor.blackColor())
        if text:
            line = [pair for pair, context in self._originalList]
            result = searchKerningPairList(text, line, self.font, allowVariables=False)
            result = set(result)
            result = [(pair, context) for (pair, context) in self._originalList if pair in result]
        else:
            result = self._originalList
        self._setList(result)

    # notifications

    def _kerningPairSetChanged(self, notification):
        changedData = notification.data
        needUpdating = self._findChangedPair(changedData["key"])
        for pair in needUpdating:
            value = changedData["newValue"]
            for index in self._indexMap.get(pair, []):
                item = self.list[index]
                item["value"] = value
        # if not needUpdating:
        #     # add pair
        #     newPairs = self.font.kerning.metricsMachine.pairsSortedByUnicode(keys=[changedData["key"]])
        #     self._originalList.extend(newPairs)
        #     for index, ((side1, side2), context) in enumerate(newPairs):
        #         value = self.font.kerning.metricsMachine[side1, side2]
        #         d = dict(side1=side1, side2=side2, value=value, context=context)
        #         if (side1, side2) not in self._indexMap:
        #             self._indexMap[side1, side2] = []
        #         self._indexMap[side1, side2].append(index + len(self.list))
        #         self.list.append(d)

    def _kerningPairDeletedChanged(self, notification):
        changedData = notification.data
        needUpdating = self._findChangedPair(changedData["key"])
        for pair in needUpdating:
            for index in self._indexMap.get(pair, []):
                item = self.list[index]
                item["value"] = 0

    def _kerningClearedChanged(self, notification):
        for item in self.list:
            item["value"] = 0

    def _kerningUpdatedChanged(self, notification):
        self.set(self._originalList)
