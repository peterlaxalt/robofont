
import os
import re
from copy import deepcopy
import AppKit
import vanilla
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.glyphLineView import GlyphLineView
from mm4 import MetricsMachineError
from mm4.interface.views.popUpButtonListCell import PopUpButtonListCell
from mm4.interface.formatters import PairMemberFormatter, KerningValueFormatter, NumberEditText
from mm4.tools.patternMatching import isValidExpression, isValidKerningExpression, searchKerningPairList, searchGlyphList, createGlyphListFromPairList
from mm4.tools.transformationsReadWrite import readTransformations, writeTransformations
from mm4.interface.tempFontWrapper import FontWrapper
from mm4.objects.mmKerning import getKerningValue
from mm4.objects.mmGroups import bracketedUserFriendlyGroupName
from mm4.interface.colors import *
from mojo.events import addObserver, removeObserver
from mojo.extensions import getExtensionDefault
from mojo.UI import inDarkMode


defaultTransformations = {
    "Copy": dict(
        type="Copy",
        storedType="Copy",
        settings=dict(pattern="", side1Replacement="", side2Replacement="", report={}),
        kerning=None,
        changedPairs={},
        padding=""
    ),
    "Remove": dict(
        type="Remove",
        storedType="Remove",
        settings=dict(pattern=""),
        kerning=None,
        changedPairs={},
        padding=""
    ),
    "Scale": dict(
        type="Scale",
        storedType="Scale",
        settings=dict(pattern="", value=1),
        kerning=None,
        changedPairs={},
        padding=""
    ),
    "Shift": dict(
        type="Shift",
        storedType="Shift",
        settings=dict(pattern="", value=0),
        kerning=None,
        changedPairs={},
        padding=""
    ),
    "Round": dict(
        type="Round",
        storedType="Round",
        settings=dict(pattern="", value=1, removeRedundantExceptions=True),
        kerning=None,
        changedPairs={},
        padding=""
    ),
    "Threshold": dict(
        type="Threshold",
        storedType="Threshold",
        settings=dict(pattern="", value=1, removeRedundantExceptions=True),
        kerning=None,
        changedPairs={},
        padding=""
    )
}


class TransformationSheet(BaseWindowController):

    def __init__(self, parentWindow, font):
        self.font = font
        self.fontWrapperForLineView = FontWrapper(font)
        self.fontWrapperForLineView.setGroups(font.groups)

        size = (550, 600)
        minSize = (550, 600)
        maxSize = (550, 1000)
        # self.w = vanilla.Window(size, minSize=minSize, maxSize=maxSize)
        self.w = vanilla.Sheet(size, parentWindow, minSize=minSize, maxSize=maxSize)

        # transformation list
        transformationTypes = ["Copy", "Remove", "Scale", "Shift", "Round", "Threshold"]
        columnDescriptions = [
            dict(title="padding", width=3, editable=False),
            dict(title="type", cell=PopUpButtonListCell(transformationTypes), binding="selectedValue", editable=True),
        ]
        self.w.transformationList = self.transformationList = vanilla.List((15, 15, 100, -245), [], columnDescriptions=columnDescriptions,
            showColumnTitles=False, drawFocusRing=False, allowsMultipleSelection=True,
            selectionCallback=self.transformationListSelectionCallback, editCallback=self.transformationListEditCallback)

        self.w.addButton = vanilla.Button((15, -235, 10, 10), "+", sizeStyle="small",
            callback=self.addTransformationCallback)
        self.w.addButton.getNSButton().setBezelStyle_(AppKit.NSSmallSquareBezelStyle)
        self.w.removeButton = vanilla.Button((34, -235, 10, 10), "-", sizeStyle="small",
            callback=self.deleteTransformationCallback)
        self.w.removeButton.getNSButton().setBezelStyle_(AppKit.NSSmallSquareBezelStyle)

        self.w.upButton = vanilla.Button((76, -235, 10, 11), chr(0x2191), sizeStyle="small",
            callback=self.upTransformationCallback)
        self.w.upButton.getNSButton().setBezelStyle_(AppKit.NSSmallSquareBezelStyle)
        self.w.downButton = vanilla.Button((95, -235, 10, 11), chr(0x2193), sizeStyle="small",
            callback=self.downTransformationCallback)
        self.w.downButton.getNSButton().setBezelStyle_(AppKit.NSSmallSquareBezelStyle)

        # transformation settings
        self.transformationsSettingsBox = vanilla.Box((0, 0, 0, 0))
        self.transformationsSettingsBox.copyControls = CopyControls(self.controlsChangeCallback)
        self.transformationsSettingsBox.removeControls = RemoveControls(self.controlsChangeCallback)
        self.transformationsSettingsBox.scaleControls = ScaleControls(self.controlsChangeCallback)
        self.transformationsSettingsBox.shiftControls = ShiftControls(self.controlsChangeCallback)
        self.transformationsSettingsBox.roundControls = RoundControls(self.controlsChangeCallback)
        self.transformationsSettingsBox.thresholdControls = ThresholdControls(self.controlsChangeCallback)

        # transformation results list
        pairMemberFormatter = PairMemberFormatter.alloc().init()
        formatter = KerningValueFormatter()
        columnDescriptions = [
            dict(title="Side 1", key="side1", width=170, formatter=pairMemberFormatter),
            dict(title="Side 2", key="side2", width=170, formatter=pairMemberFormatter),
            dict(title="value", formatter=formatter),
        ]
        self.transformationResultsList = vanilla.List((0, 0, 0, 0), [], columnDescriptions=columnDescriptions,
            showColumnTitles=False, drawFocusRing=False, selectionCallback=self.resultsListSelectionCallback,
            allowsMultipleSelection=False)
        cell = self.transformationResultsList.getNSTableView().tableColumns()[2].dataCell()
        cell.setAlignment_(AppKit.NSRightTextAlignment)

        # controls split view
        paneDescriptions = [
            dict(view=self.transformationsSettingsBox, minSize=225, maxSize=1000, canCollapse=False, identifier="transformationControls"),
            dict(view=self.transformationResultsList, minSize=50, canCollapse=False, identifier="transformationResults")
        ]
        self.w.splitView = vanilla.SplitView((125, 15, -15, -215), paneDescriptions=paneDescriptions, isVertical=False, dividerStyle="thick")

        # preview
        self.w.lineView = GlyphLineView((15, -205, -15, -65), pointSize=None, autohideScrollers=False, applyKerning=True)

        # bottom
        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))

        self.w.loadButton = vanilla.Button((15, -35, 70, 20), "Import", callback=self.loadTransformationsCallback)
        self.w.saveButton = vanilla.Button((95, -35, 70, 20), "Export", callback=self.saveTransformationsCallback)

        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self._inDelete = False
        self.addTransformationCallback(None)

        self.appearanceChanged(None)
        addObserver(self, "updateGlyphLineViewColors", "com.typesupply.MM4.invertPreviewsSettingDidChange")
        addObserver(self, "appearanceChanged", "appearanceChanged")

        self.setUpBaseWindowBehavior()
        self.w.open()

    def appearanceChanged(self, notification):
        self.updateGlyphLineViewColors(None)
        allControls = [
                self.transformationsSettingsBox.copyControls,
                self.transformationsSettingsBox.removeControls,
                self.transformationsSettingsBox.scaleControls,
                self.transformationsSettingsBox.shiftControls,
                self.transformationsSettingsBox.roundControls,
                self.transformationsSettingsBox.thresholdControls
                ]
        for controls in allControls:
            if hasattr(controls, 'setEditTextColors'):
                controls.setEditTextColors()

    def cancelCallback(self, sender):
        removeObserver(self, "com.typesupply.MM4.invertPreviewsSettingDidChange")
        removeObserver(self, "appearanceChanged")
        self.w.close()

    def applyCallback(self, sender):
        if len(self.transformationList):
            item = self.transformationList[-1]
            if item["kerning"] is None:
                self._performTransformation(item)
            kerning = item["kerning"]
            self.font.kerning.metricsMachine.clear()
            self.font.kerning.metricsMachine.update(kerning)
        removeObserver(self, "com.typesupply.MM4.invertPreviewsSettingDidChange")
        removeObserver(self, "appearanceChanged")
        self.w.close()

    # --------------
    # internal tools
    # --------------

    def _invalidateKerningObjects(self):
        currentItem = self.currentItem
        index = self.transformationList.index(currentItem)
        for item in self.transformationList[index:]:
            item["kerning"] = None

    def _performTransformation(self, item):
        index = self.transformationList.index(item)
        # get a kerning object
        if index == 0:
            kerning = self.font.kerning.metricsMachine.makeCopyWithoutSubscribers()
        else:
            previousItem = self.transformationList[index - 1]
            if previousItem["kerning"] is None:
                self._performTransformation(previousItem)
            kerning = previousItem["kerning"].metricsMachine.makeCopyWithoutSubscribers()
        # skip flagged items
        font = self.font
        if item.get("inputError"):
            kerning.clear()
            item["kerning"] = kerning
            item["changedPairs"] = {}
            return
        # perform the transformation
        itemType = item["type"]
        settings = item["settings"]
        pattern = settings["pattern"]
        pairs = searchKerningPairList(pattern, kerning.keys(), self.font)
        value = settings.get("value")
        removeRedundantExceptions = settings.get("removeRedundantExceptions")
        if itemType == "Copy":
            # gather side1
            if pattern:
                side1Source = createGlyphListFromPairList(pattern, kerning.keys(), font, "side1")
            else:
                side1Source = []
            side1Replacement = settings["side1Replacement"]
            if side1Replacement:
                side1Replacement = searchGlyphList(side1Replacement, font.keys(), groups=font.groups, expandGroups=False)
            else:
                side1Replacement = []
            side1Source = [i for i in side1Source if not i.startswith(side2Prefix)]
            side1Replacement = [i for i in side1Replacement if not i.startswith(side2Prefix)]
            # gather side2
            if pattern:
                side2Source = createGlyphListFromPairList(pattern, kerning.keys(), font, "side2")
            else:
                side2Source = []
            side2Replacement = settings["side2Replacement"]
            if side2Replacement:
                side2Replacement = searchGlyphList(side2Replacement, font.keys(), groups=font.groups, expandGroups=False)
            else:
                side2Replacement = []
            side2Source = [i for i in side2Source if not i.startswith(side1Prefix)]
            side2Replacement = [i for i in side2Replacement if not i.startswith(side1Prefix)]
            # perform transformation
            if (side1Source or side2Source) and (side1Replacement or side2Replacement):
                result, report = kerning.metricsMachine.transformationCopy(pairs, side1Source=side1Source, side2Source=side2Source, side1Replacement=side1Replacement, side2Replacement=side2Replacement)
            else:
                result = {}
                report = {}
            item["changedPairs"] = result
            item["settings"]["report"] = report
        elif itemType == "Remove":
            kerning.metricsMachine.transformationRemove(pairs)
            p = {}
            for pair in pairs:
                p[pair] = 0
            pairs = p
            item["changedPairs"] = pairs
        elif itemType == "Scale":
            result = kerning.metricsMachine.transformationScale(pairs, value)
            item["changedPairs"] = result
        elif itemType == "Shift":
            result = kerning.metricsMachine.transformationShift(pairs, value)
            item["changedPairs"] = result
        elif itemType == "Round":
            result = kerning.metricsMachine.transformationRound(pairs, value, removeRedundantExceptions)
            item["changedPairs"] = result
        elif itemType == "Threshold":
            result = kerning.metricsMachine.transformationThreshold(pairs, value)
            item["changedPairs"] = result
        item["kerning"] = kerning

    # ----------
    # read/write
    # ----------

    def loadTransformationsCallback(self, sender):
        self.showGetFile(["mmt"], self._loadTransformations)

    def _loadTransformations(self, paths):
        if not paths:
            return
        try:
            transformations = readTransformations(paths[0])
        except MetricsMachineError as msg:
            msg = unicode(msg)
            self.showMessage(messageText="The transformations cound not be loaded.", informativeText=msg)
            return
        for transformation in transformations:
            transType = transformation["type"]
            default = defaultTransformations[transType]
            for k, v in default.items():
                if k not in transformation:
                    transformation[k] = deepcopy(v)
            for k, v in default["settings"].items():
                if k not in transformation["settings"]:
                    transformation["settings"][k] = deepcopy(v)
        self.transformationList.set(transformations)
        if transformations:
            self._performTransformation(self.transformationList[-1])
            self.transformationList.setSelection([0])
            self.transformationList.scrollToSelection()
            self._updateResultsList()
            self.appearanceChanged(None)

    def saveTransformationsCallback(self, sender):
        fileName = os.path.splitext(os.path.basename(self.font.path))[0]
        fileName = [fileName]
        for transformation in self.transformationList:
            fileName.append(transformation["type"])
        fileName = " ".join(fileName)
        if len(fileName) >= 241:
            fileName = fileName[:241]
        fileName += ".mmt"
        self.showPutFile(["mmt"], callback=self._saveTransformations, fileName=fileName)

    def _saveTransformations(self, path):
        if not path:
            return
        writeTransformations(path, list(self.transformationList))

    # -------------------
    # transformation list
    # -------------------

    def _get_currentItem(self):
        selection = sorted(self.transformationList.getSelection())
        if len(selection) != 1 or self._inDelete:
            return None
        return self.transformationList[selection[0]]

    currentItem = property(_get_currentItem)

    def addTransformationCallback(self, sender):
        self.transformationList.append(deepcopy(defaultTransformations["Copy"]))
        self.transformationList.setSelection([len(self.transformationList) - 1])
        self.transformationList.scrollToSelection()

    def deleteTransformationCallback(self, sender):
        self._inDelete = True
        selection = sorted(self.transformationList.getSelection())
        for index in reversed(selection):
            del self.transformationList[index]
        self._inDelete = False

    def transformationListEditCallback(self, sender):
        currentItem = self.currentItem
        if currentItem is not None:
            currentType = currentItem["type"]
            if currentType != currentItem["storedType"]:
                currentItem["settings"] = deepcopy(defaultTransformations[currentType]["settings"])
                currentItem["storedType"] = currentType
                self._invalidateKerningObjects()
                self._performTransformation(currentItem)
        self._updateControls()
        self._updateResultsList()
        self.appearanceChanged(None)

    def upTransformationCallback(self, sender):
        selection = self.transformationList.getSelection()
        if len(selection) != 1:
            return
        selection = selection[0]
        if selection == 0:
            return
        item = self.transformationList[selection]
        del self.transformationList[selection]
        newIndex = selection - 1
        self.transformationList.insert(newIndex, item)
        self.transformationList.setSelection([newIndex])

    def downTransformationCallback(self, sender):
        selection = self.transformationList.getSelection()
        if len(selection) != 1:
            return
        selection = selection[0]
        if selection == len(self.transformationList) - 1:
            return
        item = self.transformationList[selection]
        del self.transformationList[selection]
        newIndex = selection + 1
        self.transformationList.insert(newIndex, item)
        self.transformationList.setSelection([newIndex])

    def transformationListSelectionCallback(self, sender):
        self._updateControls()
        self._updateResultsList()

    # --------
    # controls
    # --------

    def _updateControls(self):
        views = {
            "Copy": self.transformationsSettingsBox.copyControls,
            "Remove": self.transformationsSettingsBox.removeControls,
            "Scale": self.transformationsSettingsBox.scaleControls,
            "Shift": self.transformationsSettingsBox.shiftControls,
            "Round": self.transformationsSettingsBox.roundControls,
            "Threshold": self.transformationsSettingsBox.thresholdControls
        }
        currentItem = self.currentItem
        if currentItem is None:
            for view in views.values():
                view.show(False)
            return
        currentType = currentItem["type"]
        for viewType, view in views.items():
            if viewType == currentType:
                view.set(currentItem["settings"])
            else:
                view.set(None)
            view.show(viewType == currentType)
        self.appearanceChanged(None)

    def controlsChangeCallback(self, sender):
        self._invalidateKerningObjects()
        self._performTransformation(self.currentItem)
        self._updateResultsList()
        self.appearanceChanged(None)


    # -------
    # preview
    # -------

    def resultsListSelectionCallback(self, sender):
        selectionIndexes = sender.getSelection()
        if not len(selectionIndexes) == 1:
            glyphs = []
        else:
            font = self.font
            groups = font.groups
            selectionIndex = selectionIndexes[0]
            selection = sender[selectionIndex]
            side1 = selection["side1"]
            side2 = selection["side2"]
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
            glyphs, _ = font.metricsMachine.contextStrings.getLongContext((side1, side2))
            # make a basic kerning dict
            pairs = set()
            previous = None
            for glyph in glyphs:
                glyphName = glyph.name
                if previous is not None:
                    pairs.add((previous, glyphName))
                previous = glyphName
            kerning = {}
            tempKerning = self._unwrapPairs(sender)
            for pair in pairs:
                kerning[pair] = getKerningValue(pair, tempKerning, font.groups)
            self.fontWrapperForLineView.setKerning(kerning)
            # force all the glyphs to load. this handles components.
            neededGlyphs = set()
            for glyph in glyphs:
                self._getNeededGlyphs(glyph, neededGlyphs)
            self.fontWrapperForLineView.setGlyphs(glyphs)
            # get the wrapped glyphs
            glyphs = [self.fontWrapperForLineView[glyph.name] for glyph in glyphs]
        self.w.lineView.set(glyphs)

    def _updateResultsList(self):
        selection = self.transformationResultsList.getSelection()
        item = self.currentItem
        if item is None:
            pairs = {}
        else:
            pairs = item["changedPairs"]
        pairs = self._wrapPairs(pairs)
        self.transformationResultsList.set(pairs)
        if selection:
            selection = selection[0]
            if selection < len(self.transformationResultsList):
                self.transformationResultsList.setSelection([selection])

    def _getNeededGlyphs(self, glyph, glyphs):
        if glyph not in glyphs:
            glyphs.add(glyph)
        if glyph.components:
            font = glyph.font
            for componentName in glyph.components:
                if componentName not in font:
                    continue
                component = font[componentName]
                self._getNeededGlyphs(component, glyphs)

    def _wrapPairs(self, pairs):
        wrapped = []
        for (side1, side2), value in sorted(pairs.items()):
            d = dict(side1=side1, side2=side2, value=value)
            wrapped.append(d)
        return wrapped

    def _unwrapPairs(self, sender):
        kerning = {}
        for data in sender.get():
            side1 = data["side1"]
            side2 = data["side2"]
            value = data["value"]
            kerning[side1, side2] = value
        return kerning


    def updateGlyphLineViewColors(self, notification):
        if not hasattr(self.w.lineView, "_glyphLineView"):
            return
        invertPreviews = getExtensionDefault("com.typesupply.MM4.viewSettings.general.invertPreviews", False)
        if (inDarkMode() and not invertPreviews) or (not inDarkMode() and invertPreviews):
            self.w.lineView.setBackgroundColor(AppKit.NSColor.blackColor())
            self.w.lineView.setGlyphColor(AppKit.NSColor.whiteColor())
        else:
            self.w.lineView.setBackgroundColor(AppKit.NSColor.whiteColor())
            self.w.lineView.setGlyphColor(AppKit.NSColor.blackColor())


# --------
# Controls
# --------

controlTitleWidth = 97
controlInputLeft = 102
controlInputWidth = 280
controlInputHalfWidth = controlInputWidth / 2


class BaseControls(vanilla.Group):

    def __init__(self, callback):
        super(BaseControls, self).__init__((10, 10, -10, -10))
        self._callback = callback
        self.titleBox = vanilla.TextBox((0, 0, -0, 17), self.title)
        self.line = vanilla.HorizontalLine((0, 25, -0, 1))

    def _breakCycles(self):
        self._callback = None
        super(BaseControls, self)._breakCycles()

    def settingsEditCallback(self, sender):
        self._callback(self)

    def _validatePattern(self, sender, pairMode=True, allowGroups=False):
        text = sender.get()
        if not text:
            return False
        if pairMode:
            isValid = isValidKerningExpression(text)
        else:
            isValid = isValidExpression(text, allowGroups=allowGroups, allowReferenceGroups=allowGroups)
        if not isValid:
            sender.getNSTextField().setTextColor_(AppKit.NSColor.redColor())
        else:
            sender.getNSTextField().setTextColor_(AppKit.NSColor.blackColor())
        return isValid


class CopyControls(BaseControls):

    title = "Copy"

    def __init__(self, callback):
        super(CopyControls, self).__init__(callback)
        self.sourceTitle = vanilla.TextBox((0, 47, controlTitleWidth, 17), "Pattern:", alignment="right")
        self.sourceField = vanilla.EditText((controlInputLeft, 45, controlInputWidth, 22), callback=self.settingsEditCallback)
        self.replacementTitle = vanilla.TextBox((0, 77, controlTitleWidth, 17), "Replacements:", alignment="right")
        self.side1ReplacementField = vanilla.EditText((controlInputLeft, 75, controlInputHalfWidth - 5, 22), callback=self.settingsEditCallback)
        self.side2ReplacementField = vanilla.EditText((controlInputLeft + controlInputHalfWidth + 5, 75, controlInputHalfWidth - 5, 22), callback=self.settingsEditCallback)
        self.detailsTitle = vanilla.TextBox((0, 107, controlTitleWidth, 17), "Details:", alignment="right")
        self.details = vanilla.TextEditor((controlInputLeft, 105, controlInputWidth, -0), readOnly=True)
        self.setEditTextColors()

    def adjust(self):
        self.details.setPosSize(self.details.getPosSize())

    def set(self, item):
        self._item = item
        if item is None:
            self.details.set("")
            return
        self.sourceField.set(item["pattern"])
        self.side1ReplacementField.set(item["side1Replacement"])
        self.side2ReplacementField.set(item["side2Replacement"])
        self._updateDetails()

    def setEditTextColors(self):
        allEditText = [
            self.sourceField,
            self.side1ReplacementField,
            self.side2ReplacementField
            ]
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        for editText in allEditText:
            editText.getNSTextField().setTextColor_(textColor)

    def settingsEditCallback(self, sender):
        self._item["inputError"] = False
        # source
        isValidPattern = self._validatePattern(self.sourceField)
        if isValidPattern or not self.sourceField.get():
            self._item["pattern"] = self.sourceField.get()
        else:
            self._item["inputError"] = True
        # left
        isValidPattern = self._validatePattern(self.side1ReplacementField, pairMode=False, allowGroups=True)
        if isValidPattern or not self.side1ReplacementField.get():
            self._item["side1Replacement"] = self.side1ReplacementField.get()
        else:
            self._item["inputError"] = True
        # right
        isValidPattern = self._validatePattern(self.side2ReplacementField, pairMode=False, allowGroups=True)
        if isValidPattern or not self.side2ReplacementField.get():
            self._item["side2Replacement"] = self.side2ReplacementField.get()
        else:
            self._item["inputError"] = True
        super(CopyControls, self).settingsEditCallback(sender)
        self._updateDetails()

    def _updateDetails(self):
        if self._item.get("inputError"):
            self.details.set("")
            return
        report = self._item["report"]
        text = []
        arrow = u"\u2192"
        for side in ("Side 1", "Side 2"):
            # copy type
            copyType = report.get("type %s" % side)
            if copyType is not None:
                text.append("%s Copy Type: %s" % (side, copyType.replace(side, "")))
                text.append("")
            # write the partners
            partners = report.get("partners %s" % side)
            if partners:
                text.append("%s Source and Replacement Pairs:" % side)
                for s, r in sorted(partners):
                    if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                        s = bracketedUserFriendlyGroupName(s)
                    if r.startswith(side2Prefix) or r.startswith(side2Prefix):
                        r = bracketedUserFriendlyGroupName(r)
                    text.append(u"\t%s %s %s" % (s, arrow, r))
                text.append("")
            # group warnings
            groupNotInSource = report.get("warning.groupNotInSource %s" % side)
            if groupNotInSource:
                text.append("%s Warning: Source glyph is in a group, but the group is not a source." % side)
                for glyph, group in sorted(groupNotInSource):
                    if group.startswith(side1Prefix) or group.startswith(side2Prefix):
                        group = bracketedUserFriendlyGroupName(group)
                    text.append(u"\t%s %s %s" % (glyph, arrow, group))
                text.append("")
            groupNotInReplacement = report.get("warning.groupNotInReplacement %s" % side)
            if groupNotInReplacement:
                text.append("%s Warning: Replacement glyph is in a group, but the group is not a replacement." % side)
                for glyph, group in sorted(groupNotInReplacement):
                    if group.startswith(side1Prefix) or group.startswith(side2Prefix):
                        group = bracketedUserFriendlyGroupName(group)
                    text.append(u"\t%s %s %s" % (glyph, arrow, group))
                text.append("")
            # source is replacement
            sourceIsReplacement = report.get("error.sourceIsReplacement %s" % side)
            if sourceIsReplacement:
                text.append("%s Error: The source is the same as the replacement." % side)
                for s, r in sorted(sourceIsReplacement):
                    if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                        s = bracketedUserFriendlyGroupName(s)
                    if r.startswith(side2Prefix) or r.startswith(side2Prefix):
                        r = bracketedUserFriendlyGroupName(r)
                    text.append(u"\t%s %s %s" % (s, arrow, r))
                text.append("")
            # in source not replacement
            inSourceNotReplacement = report.get("error.inSourceNotReplacement %s" % side)
            if inSourceNotReplacement:
                text.append("%s Error: Could not match source to replacement." % side)
                for s in sorted(inSourceNotReplacement):
                    if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                        s = bracketedUserFriendlyGroupName(s)
                    text.append("\t" + s)
                text.append("")
            # in replacement not source
            inReplacementNotSource = report.get("error.inReplacementNotSource %s" % side)
            if inReplacementNotSource:
                text.append("%s Error: Could not match replacement to source." % side)
                for s in sorted(inReplacementNotSource):
                    if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                        s = bracketedUserFriendlyGroupName(s)
                    text.append("\t" + s)
                text.append("")
            # too many sources
            tooManySources = report.get("error.tooManySources %s" % side)
            if tooManySources:
                text.append("%s Error: Too many sources with the same base." % side)
                for s in sorted(tooManySources):
                    text.append("\t" + ", ".join(s))
                text.append("")
            # too many possible source groups
            tooManySourceGroups = report.get("error.tooManySourceGroups %s" % side)
            if tooManySourceGroups:
                text.append("%s Error: Found too many possible sources for a replacement group." % side)
                for groupName, groupList in sorted(tooManySourceGroups.items()):
                    groupName = bracketedUserFriendlyGroupName(groupName)
                    groupList = ", ".join([bracketedUserFriendlyGroupName(g) for g in groupList])
                    text.append("\t%s %s %s" % (groupName, arrow, groupList))
                text.append("")
            # too many replacements
            tooManyReplacements = report.get("error.tooManyReplacements %s" % side)
            if tooManyReplacements:
                text.append("%s Error: Too many replacements with the same base." % side)
                for s in sorted(tooManyReplacements):
                    text.append("\t" + ", ".join(s))
                text.append("")
            # too many possible replacement groups
            tooManyReplacementGroups = report.get("error.tooManyReplacementGroups %s" % side)
            if tooManyReplacementGroups:
                text.append("%s Error: Found too many possible replacements for a source group." % side)
                for groupName, groupList in sorted(tooManyReplacementGroups.items()):
                    groupName = bracketedUserFriendlyGroupName(groupName)
                    groupList = ", ".join([bracketedUserFriendlyGroupName(g) for g in groupList])
                    text.append("\t%s %s %s" % (groupName, arrow, groupList))
                text.append("")
            # conflicting sources
            conflictingSources = report.get("error.conflictingSources %s" % side)
            if conflictingSources:
                text.append("%s Error: Sources are mapped to more than one replacement." % side)
                for s in sorted(conflictingSources):
                    if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                        s = bracketedUserFriendlyGroupName(s)
                    text.append("\t" + s)
                text.append("")
            # conflicting replacements
            conflictingReplacements = report.get("error.conflictingReplacements %s" % side)
            if conflictingReplacements:
                text.append("%s Error: Replacements are mapped to more than one source." % side)
                for s in sorted(conflictingReplacements):
                    if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                        s = bracketedUserFriendlyGroupName(s)
                    text.append("\t" + s)
                text.append("")
        # display the report
        self.details.set(u"\n".join(text))
        textView = self.details.getNSTextView()
        # make titles bold
        font = AppKit.NSFont.fontWithName_size_("Helvetica", 12)
        boldFont = AppKit.NSFont.fontWithName_size_("Helvetica Bold", 12)
        errorColor = AppKit.NSColor.redColor()
        count = 0
        for line in text:
            if not line.startswith("\t") and line.strip():
                textView.setFont_range_(boldFont, (count, len(line)))
                if "Error" in line or "Warning" in line:
                    textView.setTextColor_range_(errorColor, (count, len(line)))
            else:
                textView.setFont_range_(font, (count, len(line)))
            count += len(line) + 1
        # color groups
        count = 0
        groupColor = listViewGroupColor
        for line in text:
            # headline
            if not line.startswith("\t"):
                count += len(line) + 1
                continue
            # no groups
            if "[" not in line and "]" not in line:
                count += len(line) + 1
                continue
            # work through parts
            parts = line.split(" ")
            for part in parts:
                if "[" in part or "]" in part:
                    textView.setTextColor_range_(groupColor, (count, len(part)))
                count += len(part) + 1
        # color arrows
        count = 0
        arrowColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.7, 1)
        arrowRE = re.compile(arrow)
        for line in text:
            if line.startswith("\t"):
                search = arrowRE.search(line)
                if search is not None:
                    start, end = search.span()
                    start += count
                    textView.setTextColor_range_(arrowColor, (start, 1))
            count += len(line) + 1


class RemoveControls(BaseControls):

    title = "Remove"

    def __init__(self, callback):
        super(RemoveControls, self).__init__(callback)
        self.sourceTitle = vanilla.TextBox((0, 47, controlTitleWidth, 17), "Pattern:", alignment="right")
        self.sourceField = vanilla.EditText((controlInputLeft, 45, controlInputWidth, 22), callback=self.settingsEditCallback)

    def set(self, item):
        self._item = item
        if item is None:
            return
        self.sourceField.set(item["pattern"])

    def setEditTextColors(self):
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        self.sourceField.getNSTextField().setTextColor_(textColor)

    def settingsEditCallback(self, sender):
        self._item["inputError"] = False
        isValidPattern = self._validatePattern(self.sourceField)
        if isValidPattern:
            self._item["pattern"] = self.sourceField.get()
        else:
            self._item["inputError"] = True
        super(RemoveControls, self).settingsEditCallback(sender)


class ScaleControls(BaseControls):

    title = "Scale"

    def __init__(self, callback):
        super(ScaleControls, self).__init__(callback)
        self.sourceTitle = vanilla.TextBox((0, 47, controlTitleWidth, 17), "Pattern:", alignment="right")
        self.sourceField = vanilla.EditText((controlInputLeft, 45, controlInputWidth, 22), callback=self.settingsEditCallback)
        self.valueTitle = vanilla.TextBox((0, 77, controlTitleWidth, 17), "Value:", alignment="right")
        self.valueField = NumberEditText((controlInputLeft, 75, 45, 22), "100", callback=self.settingsEditCallback)
        self.valueNote = vanilla.TextBox((153, 77, 50, 17), "%")
        self.setEditTextColors()

    def set(self, item):
        self._item = item
        if item is None:
            return
        self.sourceField.set(item["pattern"])
        self.valueField.set(item["value"] * 100)

    def setEditTextColors(self):
        allEditText = [
            self.sourceField,
            self.valueField
            ]
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        for editText in allEditText:
            editText.getNSTextField().setTextColor_(textColor)

    def settingsEditCallback(self, sender):
        self._item["inputError"] = False
        isValidPattern = self._validatePattern(self.sourceField)
        if isValidPattern:
            self._item["pattern"] = self.sourceField.get()
        else:
            self._item["inputError"] = True
        self._item["value"] = self.valueField.get() * .01
        super(ScaleControls, self).settingsEditCallback(sender)


class ShiftControls(BaseControls):

    title = "Shift"

    def __init__(self, callback):
        super(ShiftControls, self).__init__(callback)
        self.sourceTitle = vanilla.TextBox((0, 47, controlTitleWidth, 17), "Pattern:", alignment="right")
        self.sourceField = vanilla.EditText((controlInputLeft, 45, controlInputWidth, 22), callback=self.settingsEditCallback)
        self.valueTitle = vanilla.TextBox((0, 77, controlTitleWidth, 17), "Value:", alignment="right")
        self.valueField = NumberEditText((controlInputLeft, 75, 45, 22), "0", callback=self.settingsEditCallback)
        self.valueNote = vanilla.TextBox((153, 77, 50, 17), "units")
        self.setEditTextColors()

    def set(self, item):
        self._item = item
        if item is None:
            return
        self.sourceField.set(item["pattern"])
        self.valueField.set(item["value"])

    def setEditTextColors(self):
        allEditText = [
            self.sourceField,
            self.valueField
            ]
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        for editText in allEditText:
            editText.getNSTextField().setTextColor_(textColor)

    def settingsEditCallback(self, sender):
        self._item["inputError"] = False
        isValidPattern = self._validatePattern(self.sourceField)
        if isValidPattern:
            self._item["pattern"] = self.sourceField.get()
        else:
            self._item["inputError"] = True
        self._item["value"] = self.valueField.get()
        super(ShiftControls, self).settingsEditCallback(sender)


class RoundControls(BaseControls):

    title = "Round"

    def __init__(self, callback):
        super(RoundControls, self).__init__(callback)
        self.sourceTitle = vanilla.TextBox((0, 47, controlTitleWidth, 17), "Pattern:", alignment="right")
        self.sourceField = vanilla.EditText((controlInputLeft, 45, controlInputWidth, 22), callback=self.settingsEditCallback)
        self.valueTitle = vanilla.TextBox((0, 77, controlTitleWidth, 17), "Value:", alignment="right")
        self.valueField = NumberEditText((controlInputLeft, 75, 45, 22), "1", callback=self.settingsEditCallback)
        self.valueNote = vanilla.TextBox((153, 77, 50, 17), "units")
        self.exceptionOption = vanilla.CheckBox((controlInputLeft, 110, 220, 20), "Remove redundant exceptions", value=True, callback=self.settingsEditCallback)
        self.setEditTextColors()

    def set(self, item):
        self._item = item
        if item is None:
            return
        self.sourceField.set(item["pattern"])
        self.valueField.set(item["value"])
        self.exceptionOption.set(item["removeRedundantExceptions"])

    def setEditTextColors(self):
        allEditText = [
            self.sourceField,
            self.valueField
            ]
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        for editText in allEditText:
            editText.getNSTextField().setTextColor_(textColor)

    def settingsEditCallback(self, sender):
        self._item["inputError"] = False
        isValidPattern = self._validatePattern(self.sourceField)
        if isValidPattern:
            self._item["pattern"] = self.sourceField.get()
        else:
            self._item["inputError"] = True
        self._item["value"] = self.valueField.get()
        self._item["removeRedundantExceptions"] = self.exceptionOption.get()
        super(RoundControls, self).settingsEditCallback(sender)


class ThresholdControls(BaseControls):

    title = "Threshold"

    def __init__(self, callback):
        super(ThresholdControls, self).__init__(callback)
        self.sourceTitle = vanilla.TextBox((0, 47, controlTitleWidth, 17), "Pattern:", alignment="right")
        self.sourceField = vanilla.EditText((controlInputLeft, 45, controlInputWidth, 22), callback=self.settingsEditCallback)
        self.valueTitle = vanilla.TextBox((0, 77, controlTitleWidth, 17), "Value:", alignment="right")
        self.valueField = NumberEditText((controlInputLeft, 75, 45, 22), "1", callback=self.settingsEditCallback)
        self.valueNote = vanilla.TextBox((153, 77, 50, 17), "units")
        self.exceptionOption = vanilla.CheckBox((controlInputLeft, 110, 220, 20), "Remove redundant exceptions", value=True, callback=self.settingsEditCallback)
        self.setEditTextColors()

    def set(self, item):
        self._item = item
        if item is None:
            return
        self.sourceField.set(item["pattern"])
        self.valueField.set(item["value"])
        self.exceptionOption.set(item["removeRedundantExceptions"])

    def setEditTextColors(self):
        allEditText = [
            self.sourceField,
            self.valueField
            ]
        if inDarkMode():
            textColor = AppKit.NSColor.whiteColor()
        else:
            textColor = AppKit.NSColor.blackColor()
        for editText in allEditText:
            editText.getNSTextField().setTextColor_(textColor)

    def settingsEditCallback(self, sender):
        self._item["inputError"] = False
        isValidPattern = self._validatePattern(self.sourceField)
        if isValidPattern:
            self._item["pattern"] = self.sourceField.get()
        else:
            self._item["inputError"] = True
        self._item["value"] = self.valueField.get()
        self._item["removeRedundantExceptions"] = self.exceptionOption.get()
        super(ThresholdControls, self).settingsEditCallback(sender)
