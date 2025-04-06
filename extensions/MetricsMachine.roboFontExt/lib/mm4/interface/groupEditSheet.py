import os
import AppKit
from objc import super, python_method
import vanilla
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
from defconAppKit.windows.popUpWindow import InformationPopUpWindow, HUDTextBox, HUDHorizontalLine
from mm4.objects.mmGroups import userFriendlyGroupName
from mm4.interface.views.groupStackView import GroupStackView
from mm4.tools.patternMatching import searchGlyphList, isValidExpression
from mm4.interface.colors import *
from mm4.interface.formatters import ValidatingGroupNameFormatter, GroupNameFormatter
from mm4.interface.glyphSortDescriptors import sortGlyphNames
from mm4.interface.importGroupsSheet import ImportGroupsSheet
from mm4.interface.views.countListCell import CountListCell
from mm4.interface.glyphCellItem import MMGlyphCellItem
from mojo.UI import inDarkMode
from mojo.events import addObserver, removeObserver


groupIndicatingRepresentationKey = "GroupIndicatingGlyphCell"
groupEditDetailRepresentationKey = "GroupEditDetail"
noLayerGlyphCellRepresentationKey = "NoLayerGlyphCell"


class GroupEditSheet(BaseWindowController):

    def __init__(self, parentWindow, font, progressSheet=None, groupsHaveChanged=False):
        self.parentWindow = parentWindow
        self.font = font
        if hasattr(font.metricsMachine, "mutableGroups"):
            self.groups = font.metricsMachine.mutableGroups
        else:
            self.groups = font.groups.metricsMachine.mutableCopy()

        self.groups.addObserver(self, "_groupsChanged", "MMGroups.Changed")
        addObserver(self, "appearanceChanged", "appearanceChanged")
        self._groupsHaveChanged = groupsHaveChanged

        sortedGlyphNames = sortGlyphNames(font)
        self._allGlyphs = [font[glyphName] for glyphName in sortedGlyphNames]

        size = (688, 600)
        self.w = vanilla.Sheet(size, parentWindow, minSize=size)

        # source
        formatter = GroupNameFormatter.alloc().init()
        columnDescriptions = [
            dict(title="Name"),
            dict(title="Side 1 Group", key="side1GroupName", formatter=formatter),
            dict(title="Side 2 Group", key="side2GroupName", formatter=formatter),
        ]
        self.w.sourceCellView = self.sourceCellView = GlyphCollectionView((15, 15, -320, -97),
            listColumnDescriptions=columnDescriptions, listShowColumnTitles=True,
            allowDrag=True, doubleClickCallback=self.glyphListDoubleClickCallback,
            selectionCallback=self.glyphListSelectionCallback,
            cellRepresentationName=groupIndicatingRepresentationKey, glyphDetailWindowClass=SelectionInformationPopUpWindow)
        self.w.sourceCellView.glyphCellItemClass = MMGlyphCellItem
        self.w.sourceCellView.getGlyphCellView().setGlyphDetailModifiers_mouseDown_mouseUp_mouseDragged_mouseMoved_(
            modifiers=[AppKit.NSControlKeyMask], mouseDown=False, mouseUp=False, mouseDragged=False, mouseMoved=True)
        self.w.sourceCellView.setCellSize((42, 56))
        self.w.sourceCellView.set(self._allGlyphs)
        self.w.sourceSearchBox = vanilla.SearchBox((15, -87, -422, 22), callback=self.filterGlyphListCallback)
        self.w.sourceIgnoreGroupedCheckBox = vanilla.CheckBox((-412, -85, 92, 18), "Hide grouped", callback=self.filterGlyphListCallback, sizeStyle="small")
        self.w.getNSWindow().setAcceptsMouseMovedEvents_(True)

        # groups
        self.w.groupTabs = vanilla.Tabs((-310, 15, -15, -335), ["Side 1", "Side 2"], callback=self.groupTabSelectionCallback)

        columnDescriptions = [
            dict(title="color", width=17, editable=False, cell=GroupColorCell.alloc().init()),
            dict(title="name", width=160, editable=True, formatter=ValidatingGroupNameFormatter.alloc().initWithPrefix_groups_(side1Prefix, self.groups)),
            dict(title="count", width=63, editable=False, cell=CountListCell.alloc().initWithColor_(groupListViewPillColor))
        ]
        side1GroupTab = self.w.groupTabs[0]
        side1GroupTab.side1GroupList = self.side1GroupList = GroupList((10, 10, -35, -10), [],
            columnDescriptions=columnDescriptions, showColumnTitles=False,
            allowsMultipleSelection=True, allowsEmptySelection=True,
            editCallback=self.renameGroupCallback, selectionCallback=self.groupSelectionCallback, dropCallback=self.groupsDropCallback)
        side1GroupTab.addButton = vanilla.Button((-31, 10, 23, 25), "+",
            callback=self.addGroupCallback)
        side1GroupTab.addButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)
        side1GroupTab.removeButton = vanilla.Button((-31, 33, 23, 25), "-",
            callback=self.deleteGroupCallback)
        side1GroupTab.removeButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)
        side1GroupTab.colorWell = self.side1GroupColorWell = vanilla.ColorWell((-30, 60, 20, 40), callback=self.groupColorEditCallback)

        columnDescriptions = [
            dict(title="color", width=16, editable=False, cell=GroupColorCell.alloc().init()),
            dict(title="name", width=150, editable=True, formatter=ValidatingGroupNameFormatter.alloc().initWithPrefix_groups_(side2Prefix, self.groups)),
            dict(title="count", width=63, editable=False, cell=CountListCell.alloc().initWithColor_(groupListViewPillColor))
        ]
        side2GroupTab = self.w.groupTabs[1]
        side2GroupTab.side2GroupList = self.side2GroupList = GroupList((10, 10, -35, -10), [],
            columnDescriptions=columnDescriptions, showColumnTitles=False,
            allowsMultipleSelection=True, allowsEmptySelection=True,
            editCallback=self.renameGroupCallback, selectionCallback=self.groupSelectionCallback, dropCallback=self.groupsDropCallback)
        side2GroupTab.addButton = vanilla.Button((-31, 10, 23, 25), "+",
            callback=self.addGroupCallback)
        side2GroupTab.addButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)
        side2GroupTab.removeButton = vanilla.Button((-31, 33, 23, 25), "-",
            callback=self.deleteGroupCallback)
        side2GroupTab.removeButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)
        side2GroupTab.colorWell = self.side2GroupColorWell = vanilla.ColorWell((-30, 60, 20, 40), callback=self.groupColorEditCallback)

        # group contents
        self.w.contentTabs = vanilla.Tabs((-310, -325, -15, -65), ["Glyphs", "Stack"])

        cellTab = self.w.contentTabs[0]
        dropSettings = dict(
            callback=self.contentsDropCallback,
            allowsDropOnRows=False,
            allowsDropBetweenRows=False
        )
        cellTab.cellView = self.contentsCellView = GlyphCollectionView((10, 10, -10, -10),
            deleteCallback=self.contentsDeleteCallback, selfWindowDropSettings=dropSettings,
            glyphDetailWindowClass=None,
            allowDrag=True, enableDelete=True,
            cellRepresentationName=noLayerGlyphCellRepresentationKey)
        cellTab.cellView.setCellSize((42, 56))
        cellTab.cellView.setCellRepresentationArguments(drawHeader=True)

        stackTab = self.w.contentTabs[1]
        stackTab.stackView = self.contentsStackView = GroupStackView((10, 10, -10, -10), "side1", dropCallback=self.contentsDropCallback)

        self.w.line = vanilla.HorizontalLine((15, -50, -15, 1))

        self.w.importButton = vanilla.Button((15, -35, 70, 20), "Import", self.importGroupsCallback)
        self.w.exportButton = vanilla.Button((95, -35, 70, 20), "Export", self.exportGroupsCallback)

        self.w.autoButton = vanilla.Button((175, -35, 70, 20), "Auto", callback=self.autoGroupsCallback)
        self.w.copyButton = vanilla.Button((255, -35, 70, 20), "Copy", callback=self.copyGroupsCallback)

        self.w.autoGroupsColorButton = vanilla.Button((335, -35, 70, 20), "Color", callback=self.autoGroupColorsCallback)

        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self._setGroupLists()
        self.groupTabSelectionCallback(self.w.groupTabs)

        self.setUpBaseWindowBehavior()

        if progressSheet:
            self._forceGlyphCellsToLoad()
            progressSheet.close()

        # register the cell representation with the mutable groups
        kwargs = self.w.sourceCellView.getCellRepresentationArguments()
        width, height = self.w.sourceCellView.getCellSize()
        kwargs["width"] = width
        kwargs["height"] = height

        self.appearanceChanged(None)
        
        # self.groups.registerGroupDependentRepresentation(groupIndicatingRepresentationKey, kwargs)

        self.w.open()

    def _forceGlyphCellsToLoad(self):
        self.w.sourceCellView.preloadGlyphCellImages()

    def _finalize(self):
        self.w.close()
        self.groups.removeObserver(self, "MMGroups.Changed")
        self.groups = None
        removeObserver(self, "appearanceChanged")

    def cancelCallback(self, sender):
        if self._groupsHaveChanged:
            messageText = "Are you sure you want to cancel?"
            informativeText = "All group editing from this session will be lost."
            self.showAskYesNo(messageText, informativeText, self._cancel)
        else:
            self._cancel(1)

    def _cancel(self, result):
        if result:
            # XXX small hack to work around a puzzling error.
            # the cell view is trying to retain selection
            # even though there are no glyphs.
            self.w.sourceCellView.setSelection([])
            self.w.sourceCellView.set([])
            # tear down mutable groups and representations
            self.groups.metricsMachine.cancelEverything()
            # close the window
            self._finalize()

    def applyCallback(self, sender):
        progress = self.startProgress("Searching for conflicts...")
        groups = self.groups
        needResolution = groups.metricsMachine.applyGroups()
        progress.close()
        self._finalize()
        if needResolution:
            from mm4.interface.conflictResolutionSheet import ConflictResolutionSheet
            ConflictResolutionSheet(self.parentWindow, self.font)
        else:
            groups.metricsMachine.applyKerning()

    def updateGlyphCollectionBGColor(self): 
        if inDarkMode():
            backgroundColor = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .2, .2, 1.0)
        else:
            backgroundColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.6, 1.0)
        glyphCellViews = [self.w.sourceCellView, self.contentsCellView]
        for glyphCellView in glyphCellViews:
            glyphCellView._glyphCellView.backgroundColor = backgroundColor
            glyphCellView._glyphCellView.gridColor = backgroundColor
            glyphCellView._glyphCellView.setNeedsDisplay_(True)
            if hasattr(glyphCellView, "_list"):
                glyphCellView._list.getNSScrollView().setBackgroundColor_(backgroundColor)

    # --------------
    # global actions
    # --------------

    # import

    def importGroupsCallback(self, sender):
        self.showGetFile(["ufo", "mmg", "fea"], self._importGroups1)

    def _importGroups1(self, result):
        if not result:
            return
        path = result[0]
        if path == self.font.path:
            return
        groupNames = None
        sourceType = None
        if path.lower().endswith("ufo"):
            sourceType = "UFO"
            progress = self.startProgress("Importing groups...")
            groupNames = self.groups.metricsMachine.getAvailableGroupsForImportFromUFO(path)
            progress.close()
        elif path.lower().endswith("fea"):
            sourceType = "feature file"
            progress = self.startProgress("Importing groups...")
            errorMessage, groupNames = self.groups.metricsMachine.getAvailableGroupsForImportFromFeatureFile(path)
            if errorMessage:
                progress.close()
                self.showMessage("Import failed.", errorMessage)
                return
            self._forceGlyphCellsToLoad()
            progress.close()
        else:
            sourceType = "MMG file"
            progress = self.startProgress("Importing groups...")
            try:
                groupNames = self.groups.metricsMachine.getAvailableGroupsForImportFromMMG(path)
            except:
                progress.close()
                progress = None
                self.showMessage("The file could not be loaded.", "The file contains invalid syntax.")
                return
            self._forceGlyphCellsToLoad()
            progress.close()
        if not groupNames:
            self.showMessage(messageText="No groups to import.", informativeText="Please select a %s containing groups." % sourceType)
            return
        ImportGroupsSheet(groupNames, self.w, self._importGroups2, path)

    def _importGroups2(self, groupNames, clearExisting, path):
        if not groupNames and not clearExisting:
            return
        if path.lower().endswith("ufo"):
            progress = self.startProgress("Importing groups...")
            self.groups.metricsMachine.importGroupsFromUFO(path, groupNames, clearExisting)
            self._forceGlyphCellsToLoad()
            progress.close()
        elif path.lower().endswith("fea"):
            progress = self.startProgress("Importing groups...")
            self.groups.metricsMachine.importGroupsFromFeatureFile(path, groupNames, clearExisting)
            self._forceGlyphCellsToLoad()
            progress.close()
        else:
            progress = self.startProgress("Importing groups...")
            self.groups.metricsMachine.importGroupsFromMMG(path, groupNames, clearExisting)
            self._forceGlyphCellsToLoad()
            progress.close()

    # export

    def exportGroupsCallback(self, sender):
        if self.font.path is None:
            fileName = None
            directory = None
        else:
            path = os.path.splitext(self.font.path)[0] + ".mmg"
            directory, fileName = os.path.split(path)
        self.showPutFile(["mmg"], callback=self._exportGroups, fileName=fileName, directory=directory)

    def _exportGroups(self, path):
        if not path:
            return
        self.groups.metricsMachine.exportGroupsToMMG(path)

    def autoGroupsCallback(self, sender):
        from mm4.interface.autoGroupsSheet import AutoGroupsSheet
        AutoGroupsSheet(self.font, callback=self._autoGroupsCallback, parentWindow=self.w)

    def _autoGroupsCallback(self, followDecomposition, suffixesToFollowBase):
        if not followDecomposition and not suffixesToFollowBase:
            return
        progress = self.startProgress("Analyzing glyphs...")
        self.groups.metricsMachine.autoGroups(followDecomposition=followDecomposition, suffixesToFollowBase=suffixesToFollowBase)
        self._forceGlyphCellsToLoad()
        progress.close()

    def copyGroupsCallback(self, sender):
        from mm4.interface.copyGroupsSheet import CopyGroupsSheet
        if self.w.groupTabs.get() == 0:
            leftToRight = False
        else:
            leftToRight = True
        CopyGroupsSheet(self.font, leftToRight=leftToRight, parentWindow=self.w)

    def autoGroupColorsCallback(self, sender):
        progress = self.startProgress("Coloring...")
        self.groups.metricsMachine.autoGroupColors()
        self._forceGlyphCellsToLoad()
        progress.close()

    # -------------
    # notifications
    # -------------

    def appearanceChanged(self, notification):
        self._clearAllRepresentations()
        self.updateGlyphCollectionBGColor()

    def _groupsChanged(self, notification):
        groups = self.groups
        font = self.font
        groupNames = notification.data
        if not groupNames:
            groupNames = {}
        # was a group deleted?
        for groupName in groupNames:
            if groupName not in groups and groupName in self._wrappedItems:
                if groupName.startswith(side1Prefix):
                    groupList = self.side1GroupList
                elif groupName.startswith(side2Prefix):
                    groupList = self.side2GroupList
                else:
                    continue
                item = self._wrappedItems[groupName]
                groupList.remove(item)
                del self._wrappedItems[groupName]
        # was a group added?
        for groupName in sorted(groupNames):
            if groupName in groups and groupName not in self._wrappedItems:
                if groupName.startswith(side1Prefix):
                    sideGroups = groups.metricsMachine.getSide1Groups()
                    groupList = self.side1GroupList
                elif groupName.startswith(side2Prefix):
                    sideGroups = groups.metricsMachine.getSide2Groups()
                    groupList = self.side2GroupList
                else:
                    continue
                index = list(sorted(sideGroups)).index(groupName)
                group = groups[groupName]
                item = self._wrapGroup(groupName)
                self._wrappedItems[groupName] = item
                groupList.insert(index, item)
        # was a group changed?
        for groupName in groupNames:
            if groupName in groups:
                group = groups[groupName]
                item = self._wrappedItems[groupName]
                item["name"] = groupName
                item["storedName"] = groupName
                item["count"] = len(group)
                item["color"] = groups.metricsMachine.getColorForGroup(groupName)
                self._removeRepresentation(groups[groupName])

        # update the views
        self.groupTabSelectionCallback(self.w.groupTabs)
        # self.sourceCellView.getGlyphCellView().setNeedsDisplay_(True)
        self.filterGlyphListCallback(None)
        self._groupsHaveChanged = True

    # -----------
    # source list
    # -----------

    def filterGlyphListCallback(self, sender):
        pattern = self.w.sourceSearchBox.get()
        if pattern.strip() and not isValidExpression(pattern, allowGroups=True, allowReferenceGroups=True):
            self.w.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.redColor())
            return
        else:
            if inDarkMode():
                self.w.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.whiteColor())
            else:
                self.w.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.blackColor())
        glyphNames = [glyph.name for glyph in self._allGlyphs]
        ignoreGrouped = self.w.sourceIgnoreGroupedCheckBox.get()
        if ignoreGrouped:
            groupList = self._getVisibleGroupList()
            if groupList == self.side1GroupList:
                glyphNames = [glyphName for glyphName in glyphNames if self.groups.metricsMachine.getSide1GroupForGlyph(glyphName) is None]
            else:
                glyphNames = [glyphName for glyphName in glyphNames if self.groups.metricsMachine.getSide2GroupForGlyph(glyphName) is None]
        if pattern:
            glyphNames = searchGlyphList(pattern, glyphNames, groups=self.font.groups, expandGroups=True)
        existingGlyphNames = self.sourceCellView.getGlyphNames()
        if existingGlyphNames != glyphNames:
            self.sourceCellView.setGlyphNames(glyphNames)
        else:
            self.sourceCellView.getGlyphCellView().setNeedsDisplay_(True)

    def glyphListDoubleClickCallback(self, sender):
        selection = sender.getSelection()
        if len(selection) != 1:
            return
        selection = selection[0]
        selection = sender[selection]
        glyphName = selection.name
        groupList = self._getVisibleGroupList()
        if groupList == self.side1GroupList:
            groupName = self.groups.metricsMachine.getSide1GroupForGlyph(glyphName)
        else:
            groupName = self.groups.metricsMachine.getSide2GroupForGlyph(glyphName)
        groupSelection = []
        for index, group in enumerate(groupList.get()):
            if group["name"] == groupName:
                groupSelection = [index]
                break
        groupList.setSelection(groupSelection)
        groupList.scrollToSelection()

    def glyphListSelectionCallback(self, sender):
        # initializing window
        if not hasattr(self.w, "groupTabs"):
            return
        # have full window
        selection = sender.getSelection()
        glyphs = [sender[i] for i in selection]
        window = self.w.sourceCellView.getGlyphCellView().glyphDetailWindow()
        window.setGroups(self.groups)
        if window is None:
            return
        groupList = self._getVisibleGroupList()
        visibleSide = "side1"
        if groupList == self.side1GroupList:
            visibleSide = "side2"
        window.setSelection(glyphs, visibleSide)

    # ----------
    # group list
    # ----------

    def _wrapGroup(self, groupName):
        d = dict(name=groupName, count=len(self.groups[groupName]), storedName=groupName, color=self.groups.metricsMachine.getColorForGroup(groupName))
        return AppKit.NSMutableDictionary.dictionaryWithDictionary_(d)

    def _setGroupLists(self):
        self._wrappedItems = {}
        side1Items = []
        for groupName in sorted(self.groups.metricsMachine.getSide1Groups()):
            d = self._wrapGroup(groupName)
            self._wrappedItems[groupName] = d
            side1Items.append(d)
        side2Items = []
        for groupName in sorted(self.groups.metricsMachine.getSide2Groups()):
            d = self._wrapGroup(groupName)
            self._wrappedItems[groupName] = d
            side2Items.append(d)
        self.side1GroupList.set(side1Items)
        self.side2GroupList.set(side2Items)

    def _getVisibleGroupList(self):
        if self.w.groupTabs.get() == 0:
            return self.side1GroupList
        else:
            return self.side2GroupList

    def groupTabSelectionCallback(self, sender):
        self.groupSelectionCallback(self._getVisibleGroupList())
        self.glyphListSelectionCallback(self.w.sourceCellView)

    def groupSelectionCallback(self, sender):
        selection = sender.getSelection()
        if len(selection) != 1:
            glyphList = []
            if inDarkMode():
                color = AppKit.NSColor.blackColor()
            else:
                color = AppKit.NSColor.whiteColor()
        else:
            index = selection[0]
            item = sender[index]
            groupName = item["name"]
            glyphList = self.groups[groupName]
            color = item["color"]
            r, g, b, a = color
            color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
        self._setContentGlyphs(glyphList)
        if self._getVisibleGroupList() == self.side1GroupList:
            colorWell = self.side1GroupColorWell
        else:
            colorWell = self.side2GroupColorWell
        colorWell.set(color)
        self.filterGlyphListCallback(None)

    def _findAvailableGroupName(self, groupNames, prefix, index=1):
        name = prefix + ("MyGroup%d" % index)
        if name in groupNames:
            return self._findAvailableGroupName(groupNames, prefix, index + 1)
        return name

    def _findAvailableGroupNameWithGlyphs(self, glyphNames, groupNames, prefix):
        groupName = None
        for glyphName in glyphNames:
            test = prefix + glyphName
            if test not in groupNames:
                groupName = test
                break
        if groupName is None:
            groupName = self._findAvailableGroupName(groupNames, prefix)
        return groupName

    def addGroupCallback(self, sender):
        visibleList = self._getVisibleGroupList()
        glyphNames = [self.sourceCellView[i].name for i in self.sourceCellView.getSelection()]
        if visibleList == self.side1GroupList:
            prefix = side1Prefix
            groupNames = self.groups.metricsMachine.getSide1Groups()
        else:
            prefix = side2Prefix
            groupNames = self.groups.metricsMachine.getSide2Groups()
        # if the command key is down, try to name
        # the group with the first glyph name.
        modifiers = AppKit.NSApp().currentEvent().modifierFlags()
        commandKey = modifiers & AppKit.NSCommandKeyMask
        if glyphNames and commandKey:
            groupName = self._findAvailableGroupNameWithGlyphs(glyphNames, groupNames, prefix)
        # otherwise, fallback to a generic name.
        else:
            groupName = self._findAvailableGroupName(groupNames, prefix)
        self.groups.metricsMachine.newGroup(groupName)
        groupNames.append(groupName)
        index = list(sorted(groupNames)).index(groupName)
        visibleList.setSelection([index])
        visibleList.scrollToSelection()
        # if the option key is down, add the selected glyphs to the new group
        optionKey = modifiers & AppKit.NSAlternateKeyMask
        if optionKey:
            self.groups.metricsMachine.addToGroup(groupName, glyphNames)

    def deleteGroupCallback(self, sender):
        visibleList = self._getVisibleGroupList()
        selection = visibleList.getSelection()
        if not selection:
            return
        showMessage = False
        for index in selection:
            item = visibleList[index]
            groupName = item["name"]
            if self.groups.metricsMachine.isGroupReferencedByKerning(groupName):
                showMessage = True
                break
        if showMessage:
            messageText = "Decompose referencing pairs?"
            informativeText = "Pairs containing the group will be broken down into individual pairs referencing the glyphs in the group."
            self.showAskYesNo(messageText, informativeText, callback=self._deleteGroup)
        else:
            self._deleteGroup(True)

    def _deleteGroup(self, result):
        visibleList = self._getVisibleGroupList()
        selection = visibleList.getSelection()
        if not selection:
            return
        for index in reversed(sorted(selection)):
            item = visibleList[index]
            groupName = item["name"]
            self._removeRepresentation(self.groups[groupName])
            self.groups.metricsMachine.removeGroup(groupName, decompose=result)

    def renameGroupCallback(self, sender):
        selection = sender.getSelection()
        if len(selection) != 1:
            return
        index = selection[0]
        if index >= len(sender):
            return
        # update the list item
        item = sender[index]
        newName = item["name"]
        oldName = item["storedName"]
        if newName == oldName:
            return
        if newName in self.groups:
            messageText = "The name %s is used by another group." % userFriendlyGroupName(newName)
            informativeText = "Please use a diferent group name."
            self.showMessage(messageText, informativeText)
            item["name"] = oldName
            return
        item["storedName"] = newName
        del self._wrappedItems[oldName]
        self._wrappedItems[newName] = item
        # inform the groups object
        self.groups.metricsMachine.renameGroup(oldName, newName)
        # sort and set the selection
        sender.remove(item)
        if newName.startswith(side1Prefix):
            allNames = self.groups.metricsMachine.getSide1Groups()
        elif newName.startswith(side2Prefix):
            allNames = self.groups.metricsMachine.getSide2Groups()
        index = list(sorted(allNames)).index(newName)
        sender.insert(index, item)
        sender.setSelection([index])
        sender.scrollToSelection()

    def groupsDropCallback(self, sender, glyphs, row, isProposal):
        if row < 0 or len(sender) == 0:
            return False
        if isProposal:
            return True
        item = sender[row]
        groupName = item["name"]
        glyphNames = [glyph.name for glyph in glyphs]
        self.groups.metricsMachine.addToGroup(groupName, glyphNames)
        return True

    def groupColorEditCallback(self, sender):
        visibleList = self._getVisibleGroupList()
        selection = visibleList.getSelection()
        if len(selection) != 1:
            return
        selection = selection[0]
        color = sender.get()
        color = color.colorUsingColorSpaceName_(AppKit.NSCalibratedRGBColorSpace)
        color = color.getRed_green_blue_alpha_(None, None, None, None)
        item = visibleList[selection]
        groupName = item["name"]
        self.groups.metricsMachine.setColorForGroup(groupName, color)

    # --------
    # contents
    # --------

    def _getVisibleContentView(self):
        selection = self.w.contentTabs.get()
        if selection == 0:
            return self.contentsCellView
        elif selection == 2:
            return self.contentsStackView

    def _setContentGlyphs(self, glyphNames):
        # cells
        glyphNames = sortGlyphNames(self.font, glyphNames)
        glyphs = [self.font[glyphName] for glyphName in glyphNames]
        self.contentsCellView.set(glyphs)
        # stack
        if self._getVisibleGroupList() == self.side1GroupList:
            self.contentsStackView.setVisibleSide("side2")
        else:
            self.contentsStackView.setVisibleSide("side1")
        self.contentsStackView.set(glyphs)

    def contentsDropCallback(self, sender, dropInfo):
        visibleList = self._getVisibleGroupList()
        selection = visibleList.getSelection()
        if len(selection) != 1:
            return False
        isProposal = dropInfo["isProposal"]
        glyphs = dropInfo["data"]
        if not isProposal:
            index = selection[0]
            item = visibleList[index]
            groupName = item["name"]
            glyphNames = [glyph.name for glyph in glyphs]
            self.groups.metricsMachine.addToGroup(groupName, glyphNames)
        return True

    def contentsDeleteCallback(self, sender):
        groupList = self._getVisibleGroupList()
        groupSelectionCallback = groupList.getSelection()
        if not groupSelectionCallback:
            return
        groupIndex = groupSelectionCallback[0]
        groupItem = groupList[groupIndex]
        groupName = groupItem["name"]
        newMembers = [glyph.name for glyph in sender.get()]
        oldMembers = self.groups[groupName]
        removedMembers = [name for name in oldMembers if name not in newMembers]
        self.groups.metricsMachine.removeFromGroup(groupName, removedMembers)
        self._removeRepresentation(removedMembers)

    def _removeRepresentation(self, glyphNames):
        font = self.font
        for glyphName in glyphNames:
            if glyphName in font:
                font[glyphName].destroyRepresentation(groupIndicatingRepresentationKey)

    def _clearAllRepresentations(self):
        repKeys = [groupIndicatingRepresentationKey, groupEditDetailRepresentationKey, noLayerGlyphCellRepresentationKey]
        font = self.font
        for glyphName in font.keys():
            for key in repKeys:
                font[glyphName].destroyRepresentation(key)


# ----------
# group list
# ----------


class GroupList(vanilla.List):

    def __init__(self, posSize, items, dropCallback=None, **kwargs):
        windowDropInfo = dict(
            type="DefconAppKitSelectedGlyphIndexesPboardType",
            allowsDropBetweenRows=False,
            allowsDropOnRows=True,
            callback=self._internalDropCallback
        )
        super(GroupList, self).__init__(posSize, items, selfWindowDropSettings=windowDropInfo, **kwargs)
        self._finalDropCallback = dropCallback

    def _internalDropCallback(self, sender, dropInfo):
        indexes = dropInfo["data"]
        source = dropInfo["source"]
        glyphs = [source[int(i)] for i in indexes]
        rowIndex = dropInfo["rowIndex"]
        isProposal = dropInfo["isProposal"]
        return self._finalDropCallback(self, glyphs, rowIndex, isProposal)


# -------------------------------
# cell for displaying group color
# -------------------------------

groupColorShadow = AppKit.NSShadow.alloc().init()
groupColorShadow.setShadowColor_(AppKit.NSColor.colorWithCalibratedWhite_alpha_(.3, .7))
groupColorShadow.setShadowBlurRadius_(2.0)
groupColorShadow.setShadowOffset_((0, -1.0))
groupColorStrokeColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.5, .15)



class GroupColorCell(AppKit.NSActionCell):

    def drawWithFrame_inView_(self, frame, view):
        # row = view.selectedRow()
        # columnCount = len(view.tableColumns())
        # frames = [view.frameOfCellAtColumn_row_(i, row) for i in range(columnCount)]
        # selected = frame in frames

        (x, y), (w, h) = AppKit.NSInsetRect(frame, 4, 4)

        r, g, b, a = self.objectValue()
        color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

        context = AppKit.NSGraphicsContext.currentContext()
        context.saveGraphicsState()

        groupColorShadow.set()

        path = AppKit.NSBezierPath.bezierPath()
        path.appendBezierPathWithOvalInRect_(((x, y), (h, h)))
        if inDarkMode():
            AppKit.NSColor.blackColor().set()
        else:
            AppKit.NSColor.whiteColor().set()
        path.fill()
        color.set()
        path.fill()

        context.restoreGraphicsState()

        groupColorStrokeColor.set()
        path.setLineWidth_(1.0)
        path.stroke()


# -------------------------
# Information Pop Up Window
# -------------------------


class SelectionInformationPopUpWindow(InformationPopUpWindow):

    def __init__(self, screen=None):
        self._width = 170
        self._collapsedHeight = 88
        self._expandedHeight = 248
        super(SelectionInformationPopUpWindow, self).__init__((self._width, self._collapsedHeight), screen=screen)
        self.name = HUDTextBox((10, 10, -5, 17), "")

        self.line1 = HUDHorizontalLine((0, 35, -0, 1))

        self.side1GroupTitle = HUDTextBox((10, 43, 50, 17), "Side 1:", alignment="right")
        self.side1Group = HUDTextBox((60, 43, -5, 17), "")
        self.side2GroupTitle = HUDTextBox((10, 63, 50, 17), "Side 2:", alignment="right")
        self.side2Group = HUDTextBox((60, 63, -5, 17), "")

        self.line2 = HUDHorizontalLine((0, 88, -0, 1))

        self.stackView = GroupStackView((10, 98, -10, 140))
        view = self.stackView.getNSView()
        view.setVerticalBuffer_(10)
        view.setBackgroundColor_(None)
        if inDarkMode():
            view.setOneGlyphColor_(AppKit.NSColor.blackColor())
            view.setMultipleGlyphsColor_(HUDGroupStackViewGlyphColorDarkMode)
            view.setMaskColor_(HUDGroupStackViewMaskColorDarkMode)
        else:
            view.setOneGlyphColor_(AppKit.NSColor.whiteColor())
            view.setMultipleGlyphsColor_(HUDGroupStackViewGlyphColor)
            view.setMaskColor_(HUDGroupStackViewMaskColor)
        self.line2.show(False)
        self.stackView.show(False)
        self.groups = None

    @python_method
    def setGroups(self, groups):
        self.groups = groups

    @python_method
    def set(self, glyph):
        # name
        name = glyph.name
        # set
        self.name.set(name)
        if self.groups is not None:
            side1Group = self.groups.metricsMachine.getSide1GroupForGlyph(name)
            side2Group = self.groups.metricsMachine.getSide2GroupForGlyph(name)
            if not side1Group:
                side1Group = ""
            else:
                side1Group = userFriendlyGroupName(side1Group)
            if not side2Group:
                side2Group = ""
            else:
                side2Group = userFriendlyGroupName(side2Group)
            self.side1Group.set(side1Group)
            self.side2Group.set(side2Group)

    @python_method
    def setSelection(self, glyphs, visibleSide):
        self.stackView.setVisibleSide(visibleSide)
        self.stackView.set(glyphs)
        # handle resizing
        x, y, w, h = self.getPosSize()
        resize = False
        if glyphs and h == self._collapsedHeight:
            h = self._expandedHeight
            resize = True
        elif not glyphs and h == self._expandedHeight:
            h = self._collapsedHeight
            resize = True
        if resize:
            self.setPosSize((x, y, w, h))
            self.line2.show(h == self._expandedHeight)
            self.stackView.show(h == self._expandedHeight)
        # invalidate the shadow
        self._window.invalidateShadow()
