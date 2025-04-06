
import AppKit
import vanilla
from objc import super, python_method
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
from defconAppKit.windows.popUpWindow import InformationPopUpWindow, HUDTextBox, HUDHorizontalLine
from mm4.tools.patternMatching import searchGlyphList, isValidExpression
from mm4.interface.glyphSortDescriptors import sortGlyphNames
from mm4.interface.importGroupsSheet import ImportGroupsSheet
from mm4.interface.formatters import ValidatingReferenceGroupNameFormatter
from mm4.interface.tempFontWrapper import FontWrapper
from mojo.events import addObserver, removeObserver
from mojo.UI import inDarkMode


noLayerGlyphCellKey = "NoLayerGlyphCell"


class ReferenceGroupEditSheet(BaseWindowController):

    def __init__(self, parentWindow, font, progressSheet=None):
        self.font = font
        self.tempFontWrapper = FontWrapper(font)
        self.tempFontWrapper.setGroups(font.groups)
        self.tempFontWrapper.setKerning(font.kerning)
        self.tempFontWrapper.groups.addObserver(self, "_groupsChanged", "MMGroups.Changed")
        addObserver(self, "appearanceChanged", "appearanceChanged")

        sortedGlyphNames = sortGlyphNames(font)
        self._allGlyphs = [self.tempFontWrapper[glyphName] for glyphName in sortedGlyphNames if not font[glyphName].template]

        size = (625, 600)
        self.w = vanilla.Sheet(size, parentWindow, minSize=size)

        # source
        self.w.sourceSearchBox = vanilla.SearchBox((15, 15, -387, 22), callback=self.filterSourceCallback)
        self.w.sourceHideCurrentCheckBox = vanilla.CheckBox((-377, 17, 120, 18), "Hide current group", callback=self.filterSourceCallback, sizeStyle="small")

        self.w.sourceCellView = self.sourceCellView = GlyphCollectionView((15, 50, -257, -65),
            listShowColumnTitles=False, allowDrag=True,
            glyphDetailWindowClass=ReferenceGroupSelectionInformationPopUpWindow,
            cellRepresentationName=noLayerGlyphCellKey)
        self.w.sourceCellView.getGlyphCellView().setGlyphDetailModifiers_mouseDown_mouseUp_mouseDragged_mouseMoved_(
            modifiers=[AppKit.NSControlKeyMask], mouseDown=False, mouseUp=False, mouseDragged=False, mouseMoved=True)
        self.w.getNSWindow().setAcceptsMouseMovedEvents_(True)
        self.w.sourceCellView.setCellSize((42, 56))
        self.w.sourceCellView.setCellRepresentationArguments(drawHeader=True)
        self.w.sourceCellView.set(self._allGlyphs)

        # groups
        windowDropInfo = dict(
            type="DefconAppKitSelectedGlyphIndexesPboardType",
            allowsDropBetweenRows=False,
            allowsDropOnRows=False,
            callback=self.groupsDropCallback
        )
        columnDescriptions = [
            dict(title="name", editable=True, formatter=ValidatingReferenceGroupNameFormatter.alloc().init())
        ]
        self.w.groupList = self.leftGroupList = vanilla.List((-242, 15, -40, 250), [],
            columnDescriptions=columnDescriptions, showColumnTitles=False,
            allowsMultipleSelection=True, allowsEmptySelection=True,
            editCallback=self.renameGroupCallback, selectionCallback=self.groupSelectionCallback, selfWindowDropSettings=windowDropInfo)
        self.w.addGroupButton = vanilla.Button((-35, 15, 23, 25), "+",
            callback=self.addGroupCallback)
        self.w.addGroupButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)
        self.w.removeGroupButton = vanilla.Button((-35, 40, 23, 25), "-",
            callback=self.deleteGroupCallback)
        self.w.removeGroupButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)

        # group contents
        dropSettings = dict(
            callback=self.groupContentsDropCallback,
            allowsDropBetweenRows=False,
            allowsDropOnRows=False,
        )
        self.w.groupContentsCellView = GlyphCollectionView((-242, 275, -15, -65),
            deleteCallback=self.groupContentsDeleteCallback, selfWindowDropSettings=dropSettings,
            glyphDetailWindowClass=None, allowDrag=False,
            enableDelete=True,
            cellRepresentationName=noLayerGlyphCellKey)
        self.w.groupContentsCellView.setCellSize((42, 56))
        self.w.groupContentsCellView.setCellRepresentationArguments(drawHeader=True)

        # bottom
        self.w.line = vanilla.HorizontalLine((15, -50, -15, 1))

        self.w.importButton = vanilla.Button((15, -35, 70, 20), "Import", self.importGroupsCallback)

        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self.setUpBaseWindowBehavior()

        self._setGroupList()

        if progressSheet:
            self.w.sourceCellView.preloadGlyphCellImages()
            progressSheet.close()

        window = self.w.sourceCellView.getGlyphCellView().glyphDetailWindow()
        window.setGroups(self.tempFontWrapper.groups)

        self.appearanceChanged(None)

        self.w.open()

    def _finalize(self):
        self.tempFontWrapper.groups.removeObserver(self, "MMGroups.Changed")
        removeObserver(self, "appearanceChanged")
        self.font = None
        self.tempFontWrapper = None
        self.w.close()

    def cancelCallback(self, sender):
        self._finalize()

    def applyCallback(self, sender):
        self.font.groups.clear()
        self.font.groups.update(self.tempFontWrapper.groups)
        self._finalize()

    def updateGlyphCollectionBGColor(self): 
        if inDarkMode():
            backgroundColor = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .2, .2, 1.0)
        else:
            backgroundColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.6, 1.0)
        glyphCellViews = [self.w.sourceCellView, self.w.groupContentsCellView]
        for glyphCellView in glyphCellViews:
            glyphCellView._glyphCellView.backgroundColor = backgroundColor
            glyphCellView._glyphCellView.gridColor = backgroundColor
            glyphCellView._glyphCellView.setNeedsDisplay_(True)
            if hasattr(glyphCellView, "_list"):
                glyphCellView._list.getNSScrollView().setBackgroundColor_(backgroundColor)

    # -------------
    # notifications
    # -------------

    def appearanceChanged(self, notification):
        self._clearAllRepresentations()
        self.updateGlyphCollectionBGColor()

    def _groupsChanged(self, notification):
        groups = self.tempFontWrapper.groups
        groupNames = notification.data
        if not groupNames:
            groupNames = {}
        # was a group deleted?
        for groupName in groupNames:
            if groupName not in groups and groupName in self._wrappedItems:
                item = self._wrappedItems[groupName]
                self.w.groupList.remove(item)
                del self._wrappedItems[groupName]
        # was a group added?
        for groupName in sorted(groupNames):
            if groupName in groups and groupName not in self._wrappedItems:
                groupNames = list(self._wrappedItems.keys()) + [groupName]
                index = list(sorted(groupNames)).index(groupName)
                item = self._wrapGroup(groupName)
                self._wrappedItems[groupName] = item
                self.w.groupList.insert(index, item)
        # was a group changed?
        for groupName in groupNames:
            if groupName in groups:
                item = self._wrappedItems[groupName]
                item["name"] = groupName
                item["storedName"] = groupName
        # update the views
        self.groupSelectionCallback(self.w.groupList)
        self.filterSourceCallback(None)

    # -----------
    # source list
    # -----------

    def filterSourceCallback(self, sender):
        pattern = self.w.sourceSearchBox.get()
        if pattern.strip() and not isValidExpression(pattern, allowGroups=True, allowReferenceGroups=True):
            self.w.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.redColor())
            return
        else:
            self.w.sourceSearchBox.getNSSearchField().setTextColor_(AppKit.NSColor.blackColor())
        glyphNames = [glyph.name for glyph in self._allGlyphs]
        if self.w.sourceHideCurrentCheckBox.get():
            groupList = self.w.groupList
            selection = groupList.getSelection()
            if selection:
                item = groupList[selection[0]]
                name = item["name"]
                contents = set(self.tempFontWrapper.groups.metricsMachine.getReferenceGroup(name))
                glyphNames = [glyphName for glyphName in glyphNames if glyphName not in contents]
        if pattern:
            glyphNames = searchGlyphList(pattern, glyphNames, groups=self.tempFontWrapper.groups, expandGroups=True)

        existingGlyphNames = self.sourceCellView.getGlyphNames()
        if existingGlyphNames != glyphNames:
            self.sourceCellView.setGlyphNames(glyphNames)

    # ----------
    # group list
    # ----------

    def _wrapGroup(self, groupName):
        d = dict(name=groupName, storedName=groupName)
        return AppKit.NSMutableDictionary.dictionaryWithDictionary_(d)

    def _setGroupList(self):
        self._wrappedItems = {}
        items = []
        for groupName in sorted(self.tempFontWrapper.groups.metricsMachine.getReferenceGroupNames()):
            d = self._wrapGroup(groupName)
            self._wrappedItems[groupName] = d
            items.append(d)
        self.w.groupList.set(items)

    def addGroupCallback(self, sender):
        groupNames = self.tempFontWrapper.groups.metricsMachine.getReferenceGroupNames()
        groupName = self._findAvailableGroupName(groupNames)
        self.tempFontWrapper.groups.metricsMachine.newReferenceGroup(groupName)
        groupNames.append(groupName)
        index = list(sorted(groupNames)).index(groupName)
        self.w.groupList.setSelection([index])
        self.w.groupList.scrollToSelection()

    def _findAvailableGroupName(self, groupNames, index=1):
        name = ("MyGroup%d" % index)
        if name in groupNames:
            return self._findAvailableGroupName(groupNames, index + 1)
        return name

    def deleteGroupCallback(self, sender):
        selection = self.w.groupList.getSelection()
        if not selection:
            return
        for index in reversed(sorted(selection)):
            item = self.w.groupList[index]
            groupName = item["name"]
            self.tempFontWrapper.groups.metricsMachine.removeReferenceGroup(groupName)

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
        if newName in self.tempFontWrapper.groups:
            messageText = "The name %s is used by another group." % newName
            informativeText = "Please use a diferent group name."
            self.showMessage(messageText, informativeText)
            item["name"] = oldName
            return
        item["storedName"] = newName
        del self._wrappedItems[oldName]
        self._wrappedItems[newName] = item
        # inform the groups object
        self.tempFontWrapper.groups.metricsMachine.renameReferenceGroup(oldName, newName)
        # sort and set the selection
        sender.remove(item)
        groupNames = self.tempFontWrapper.groups.metricsMachine.getReferenceGroupNames()
        index = list(sorted(groupNames)).index(newName)
        sender.insert(index, item)
        sender.setSelection([index])
        sender.scrollToSelection()

    def groupSelectionCallback(self, sender):
        selection = sender.getSelection()
        if len(selection) != 1:
            glyphList = []
        else:
            index = selection[0]
            item = sender[index]
            groupName = item["name"]
            glyphList = self.tempFontWrapper.groups[groupName]
        glyphs = [self.tempFontWrapper[glyphName] for glyphName in glyphList if glyphName in self.font]
        self.w.groupContentsCellView.set(glyphs)
        self.filterSourceCallback(None)

    def groupsDropCallback(self, sender, dropInfo):
        indexes = dropInfo["data"]
        source = dropInfo["source"]
        glyphs = [source[int(i)] for i in indexes]
        rowIndex = dropInfo["rowIndex"]
        isProposal = dropInfo["isProposal"]
        if rowIndex < 0 or len(sender) == 0:
            return False
        if isProposal:
            return True
        item = sender[rowIndex]
        groupName = item["name"]
        glyphNames = [glyph.name for glyph in glyphs]
        self.tempFontWrapper.groups.metricsMachine.addToReferenceGroup(groupName, glyphNames)
        return True

    # ------------------------
    # group contents callbacks
    # ------------------------

    def groupContentsDropCallback(self, sender, dropInfo):
        groupList = self.w.groupList
        selection = groupList.getSelection()
        if len(selection) != 1:
            return False
        isProposal = dropInfo["isProposal"]
        glyphs = dropInfo["data"]
        if not isProposal:
            index = selection[0]
            item = groupList[index]
            groupName = item["name"]
            glyphNames = [glyph.name for glyph in glyphs]
            self.tempFontWrapper.groups.metricsMachine.addToReferenceGroup(groupName, glyphNames)
        return True

    def groupContentsDeleteCallback(self, sender):
        groupList = self.w.groupList
        selection = groupList.getSelection()
        if not selection:
            return
        groupIndex = selection[0]
        groupItem = groupList[groupIndex]
        groupName = groupItem["name"]
        newMembers = [glyph.name for glyph in sender.get()]
        oldMembers = self.tempFontWrapper.groups[groupName]
        removedMembers = [name for name in oldMembers if name not in newMembers]
        self.tempFontWrapper.groups.metricsMachine.removeFromReferenceGroup(groupName, removedMembers)

    # ---------------
    # import callback
    # ---------------

    def importGroupsCallback(self, sender):
        self.showGetFile(["ufo"], self._importGroups1)

    def _importGroups1(self, result):
        if not result:
            return
        path = result[0]
        if path == self.font.path:
            return
        groupNames = self.tempFontWrapper.groups.metricsMachine.getAvailableReferenceGroupsForImportFromUFO(path)
        if not groupNames:
            self.showMessage(messageText="No groups to import.", informativeText="Please select a UFO containing groups.")
            return
        ImportGroupsSheet(groupNames, self.w, self._importGroups2, path, truncateGroupNames=False)

    def _importGroups2(self, groupNames, clearExisting, path):
        if not groupNames and not clearExisting:
            return
        progress = self.startProgress("Importing groups...")
        self.tempFontWrapper.groups.metricsMachine.importReferenceGroupsFromUFO(path, groupNames, clearExisting)
        progress.close()

    def _clearAllRepresentations(self):
        font = self.font
        for glyphName in font.keys():
            font[glyphName].destroyRepresentation(noLayerGlyphCellKey)


# -------------------------
# Information Pop Up Window
# -------------------------


class ReferenceGroupSelectionInformationPopUpWindow(InformationPopUpWindow):

    def __init__(self, screen=None):
        self._width = 170
        self._collapsedHeight = 37
        self._expandedHeight = 248
        super(ReferenceGroupSelectionInformationPopUpWindow, self).__init__((self._width, self._collapsedHeight), screen=screen)
        self.name = HUDTextBox((10, 10, -5, 17), "")

        self.line1 = HUDHorizontalLine((0, 35, -0, 1))
        self.line1.show(False)

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
        groupNames = []
        if self.groups is not None:
            groupNames = self.groups.metricsMachine.getReferenceGroupsForGlyph(name)
        # handle resizing
        x, y, w, h = self.getPosSize()
        expandedHeight = self._collapsedHeight + (17 * len(groupNames)) + 20
        resize = False
        if groupNames and h == self._collapsedHeight:
            h = expandedHeight
            resize = True
        elif groupNames and h != expandedHeight:
            h = expandedHeight
            resize = True
        elif not groupNames and h != self._collapsedHeight:
            h = self._collapsedHeight
            resize = True
        if resize:
            self.setPosSize((x, y, w, h))
            self.line1.show(h != self._collapsedHeight)
        # set the group names
        if groupNames:
            if not hasattr(self, "groupNames"):
                box = HUDTextBox((10, 43, -10, -10), "Test")
                setattr(self, "groupNames", box)
        else:
            if hasattr(self, "groupNames"):
                delattr(self, "groupNames")
        if groupNames:
            self.groupNames.set("\n".join(groupNames))
        # invalidate the shadow
        self._window.invalidateShadow()
