import AppKit
import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.glyphLineView import GlyphLineView
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix
from mm4.objects.mmKerning import getKerningValue
from mm4.interface.formatters import PairMemberFormatter, KerningValueFormatter
from mm4.interface.colors import *
from mm4.interface.tempFontWrapper import FontWrapper
from mm4.interface.views.popUpButtonListCell import PopUpButtonListCell
from mm4.interface.views.countListCell import CountListCell
from mojo.events import addObserver, removeObserver
from mojo.extensions import getExtensionDefault
from mojo.UI import inDarkMode


class ConflictResolutionSheet(BaseWindowController):

    def __init__(self, parentWindow, font):
        self.parentWindow = parentWindow
        self.font = font
        self.fontWrapperForLineView = FontWrapper(font)
        self.groups = font.metricsMachine.mutableGroups
        self.savedKerning = font.kerning

        pairs = self.groups.metricsMachine.getAllPairsNeedingResolution().items()
        allPairs = []
        for (side1, side2), value in sorted(pairs):
            groupValueCount = 0
            followGroupCount = 0
            exceptionCount = 0
            for (l, r), data in self.groups.metricsMachine.getConflictsForPair((side1, side2)).items():
                resolution = data["resolution"]
                if resolution == "group value":
                    groupValueCount += 1
                elif resolution == "follow group":
                    followGroupCount += 1
                else:
                    exceptionCount += 1
            d = dict(side1=side1, side2=side2, value=value, groupValueCount=groupValueCount, followGroupCount=followGroupCount, exceptionCount=exceptionCount)
            allPairs.append(d)
        # Sort by exception count
        allPairs = sorted(allPairs, key=lambda d: d['exceptionCount'], reverse=True)

        width = 900
        self.w = vanilla.Sheet((width, 500), minSize=(width, 200), maxSize=(width, 10000), parentWindow=parentWindow)

        # formatters

        valueFormatter = KerningValueFormatter()
        pairMemberFormatter = PairMemberFormatter.alloc().init()

        # class pair list

        listGroup = vanilla.Group((0, 0, -0, -0))

        columnDescriptions = [
            dict(title="Side 1", key="side1", width=98, formatter=PairMemberFormatter.alloc().init()),
            dict(title="Side 2", key="side2", width=98, formatter=PairMemberFormatter.alloc().init()),
            dict(title="value", width=40, formatter=valueFormatter),
            dict(title="groupValueCount", width=35, cell=CountListCell.alloc().initWithColor_(conflictResolutionListGroupValuePillColor)),
            dict(title="followGroupCount", width=35, cell=CountListCell.alloc().initWithColor_(conflictResolutionListFollowGroupPillColor)),
            dict(title="exceptionCount", width=35, cell=CountListCell.alloc().initWithColor_(conflictResolutionListExceptionPillColor)),
        ]
        topLevelPairListWidth = 440
        listGroup.topLevelPairList = self.topLevelPairList = vanilla.List((0, 0, topLevelPairListWidth, -0), allPairs, columnDescriptions=columnDescriptions,
            autohidesScrollers=False, showColumnTitles=False, drawVerticalLines=True, drawFocusRing=False,
            allowsEmptySelection=False, allowsMultipleSelection=False,
            selectionCallback=self.topLevelPairListSelectionCallback)
        self.topLevelPairList.getNSScrollView().setHasHorizontalScroller_(False)
        cell = self.topLevelPairList.getNSTableView().tableColumns()[2].dataCell()
        cell.setAlignment_(AppKit.NSRightTextAlignment)

        # conflicts

        options = [
            AppKit.NSAttributedString.alloc().initWithString_attributes_("exception", {AppKit.NSForegroundColorAttributeName: conflictResolutionListExceptionColor}),
            AppKit.NSAttributedString.alloc().initWithString_attributes_("follow group", {AppKit.NSForegroundColorAttributeName: conflictResolutionListFollowGroupColor}),
            AppKit.NSAttributedString.alloc().initWithString_attributes_("group value", {AppKit.NSForegroundColorAttributeName: conflictResolutionListGroupValueColor}),
        ]

        columnDescriptions = [
            dict(title="Side 1", key="side1", width=98, formatter=pairMemberFormatter, editable=False),
            dict(title="Side 2", key="side2", width=98, formatter=pairMemberFormatter, editable=False),
            dict(title="Value", key="value", width=40, formatter=valueFormatter, editable=False),
            dict(title="Resolution", key="resolution", editable=True, binding="selectedValue", cell=PopUpButtonListCell(options))
        ]

        listGroup.conflictsList = self.conflictsList = vanilla.List((topLevelPairListWidth + 10, 0, -0, -0), [], columnDescriptions=columnDescriptions,
            autohidesScrollers=False, showColumnTitles=False, drawVerticalLines=True, drawFocusRing=False,
            allowsEmptySelection=False, allowsMultipleSelection=False,
            editCallback=self.conflictEditCallback, selectionCallback=self.conflictSelectionCallback)
        self.conflictsList.getNSScrollView().setHasHorizontalScroller_(False)
        cell = self.conflictsList.getNSTableView().tableColumns()[2].dataCell()
        cell.setAlignment_(AppKit.NSRightTextAlignment)

        # line view

        self.lineView = GlyphLineView((0, 0, 0, 0), pointSize=None, autohideScrollers=False, applyKerning=True)

        # split view

        paneDescriptions = [
            dict(view=listGroup, size=300, minSize=100, canCollapse=False, identifier="listPane"),
            dict(view=self.lineView, minsize=100, canCollapse=False, identifier="typingPane")
        ]
        self.w.splitView = vanilla.SplitView((15, 15, -15, -65), paneDescriptions=paneDescriptions, isVertical=False, dividerStyle="thick")

        # bottom

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))

        self.w.returnToGroupEditorButton = vanilla.Button((15, -35, 170, 20), "Return to Group Editor", callback=self.returnToGroupEditorCallback)
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self.setUpBaseWindowBehavior()

        self.topLevelPairListSelectionCallback(self.topLevelPairList)

        self.updateGlyphLineViewColors(None)
        addObserver(self, "updateGlyphLineViewColors", "com.typesupply.MM4.invertPreviewsSettingDidChange")
        addObserver(self, "updateGlyphLineViewColors", "appearanceChanged")

        self.w.open()

    # ----------------
    # button callbacks
    # ----------------

    def returnToGroupEditorCallback(self, sender):
        messageText = "Are you sure you want to return to the group editor?"
        informativeText = "All kerning changes from this session will be lost."
        self.showAskYesNo(messageText, informativeText, self._returnToGroupEditor)

    def _returnToGroupEditor(self, result):
        if result:
            from mm4.interface.groupEditSheet import GroupEditSheet
            self.unsubscribe()
            self.w.close()
            GroupEditSheet(self.parentWindow, self.font, groupsHaveChanged=True)

    def cancelCallback(self, sender):
        messageText = "Are you sure you want to cancel?"
        informativeText = "All group editing and kerning changes from this session will be lost."
        self.showAskYesNo(messageText, informativeText, self._cancel)

    def _cancel(self, result):
        if result:
            self.groups.metricsMachine.cancelEverything()
            self.unsubscribe()
            self.w.close()

    def applyCallback(self, sender):
        self.groups.metricsMachine.applyKerning()
        self.unsubscribe()
        self.w.close()

    def unsubscribe(self):
        removeObserver(self, "appearanceChanged")
        removeObserver(self, "com.typesupply.MM4.invertPreviewsSettingDidChange")

    # ------------------------------
    # kerning manipulation callbacks
    # ------------------------------

    def topLevelPairListSelectionCallback(self, sender):
        index = sender.getSelection()[0]
        item = sender[index]
        pair = (item["side1"], item["side2"])

        pairs = sorted(self.groups.metricsMachine.getConflictsForPair(pair).items())
        conflicts = []
        for (side1, side2), data in pairs:
            d = dict(side1=side1, side2=side2, value=data["value"], resolution=data["resolution"])
            conflicts.append(d)
        self.conflictsList.set(conflicts)

    def conflictEditCallback(self, sender):
        selection = sender.getSelection()
        if not selection:
            return
        index = self.topLevelPairList.getSelection()[0]
        topItem = self.topLevelPairList[index]
        topPair = (topItem["side1"], topItem["side2"])

        index = selection[0]
        item = sender[index]
        pair = (item["side1"], item["side2"])
        resolution = item["resolution"]

        needReload = self.groups.metricsMachine.setResolutionForPair(topPair, pair, resolution)
        if needReload:
            topItem["value"] = self.groups.metricsMachine.getValueForPair(topPair)
            self.topLevelPairListSelectionCallback(self.topLevelPairList)
            sender.setSelection(selection)

        groupValueCount = 0
        followGroupCount = 0
        exceptionCount = 0
        for (l, r), data in self.groups.metricsMachine.getConflictsForPair(topPair).items():
            resolution = data["resolution"]
            if resolution == "group value":
                groupValueCount += 1
            elif resolution == "follow group":
                followGroupCount += 1
            else:
                exceptionCount += 1
        topItem["groupValueCount"] = groupValueCount
        topItem["followGroupCount"] = followGroupCount
        topItem["exceptionCount"] = exceptionCount

    def conflictSelectionCallback(self, sender):
        font = self.font
        mutableGroups = font.metricsMachine.mutableGroups
        selection = sender.getSelection()
        if not selection:
            self.lineView.set([])
            return
        pairData = sender[selection[0]]
        side1 = pairData["side1"]
        if side1.startswith(side1Prefix):
            side1Group = mutableGroups[side1]
            if side1Group:
                side1 = sorted(side1Group)[0]
            else:
                side1 = None
        side2 = pairData["side2"]
        if side2.startswith(side2Prefix):
            side2Group = mutableGroups[side2]
            if side2Group:
                side2 = sorted(side2Group)[0]
            else:
                side2 = None
        if side1 is not None and side2 is not None:
            glyphs = font.metricsMachine.contextStrings.getLongContext((side1, side2))[0]
        else:
            glyphs = []
        # make a basic kerning dict
        pairs = set()
        previous = None
        for glyph in glyphs:
            glyphName = glyph.name
            if previous is not None:
                pairs.add((previous, glyphName))
            previous = glyphName
        groupKerning = mutableGroups.metricsMachine.getBasicKerningDictForPairs(pairs)
        kerning = {}
        for pair in pairs:
            kerning[pair] = getKerningValue(pair, groupKerning, mutableGroups.metricsMachine)
        self.fontWrapperForLineView.setKerning(kerning)
        # force all the glyphs to load. this handles components.
        neededGlyphs = set()
        for glyph in glyphs:
            self._getNeededGlyphs(glyph, neededGlyphs)
        # get the wrapped glyphs
        glyphs = [self.fontWrapperForLineView[glyph.name] for glyph in glyphs if not glyph.template]
        self.lineView.set(glyphs)

    def _getNeededGlyphs(self, glyph, glyphs):
        if glyph not in glyphs:
            glyphs.add(glyph)
        if glyph.components:
            font = glyph.getParent()
            for componentName in glyph.components:
                if componentName not in font:
                    continue
                component = font[componentName]
                self._getNeededGlyphs(component, glyphs)

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
