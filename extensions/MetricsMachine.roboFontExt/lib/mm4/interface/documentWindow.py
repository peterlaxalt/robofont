import AppKit
import os
import weakref

from defconAppKit.windows.baseWindow import BaseWindowController
import vanilla

from lib.UI.windows import TitleWindow

from mm4.interface.views.pairList import PairList
from mm4.interface.views.typingGroup import TypingGroup
from mm4.interface.views.pairGroup import PairGroup
from mm4.keyEventMonitor import KeyEventMonitor

from mojo.extensions import getExtensionDefault, ExtensionBundle
from mojo.tools import CallbackWrapper
from mojo.events import publishEvent


class MMDocumentWindowController(BaseWindowController):

    def __init__(self, font):
        self.font = font

        self.w = TitleWindow((1000, 700), minSize=(1000, 400))
        self.w.vanillaWrapper = weakref.ref(self)
        self.w.setTitleCallback(self.getWindowTitleValue)
        self.w.getNSWindow().setWindowName_("MetricsMachineMainWindow")

        shortcuts = [
            ("e", ["command"], self.makeException, "Make exception"),
            ("e", ["command", "option"], self.breakException, "Break exception"),
            ("L", ["command", "shift"], self.loadPairList, "Load pair list"),
            ("l", ["command"], self.togglePairList, "Toggle pair list"),
            ("t", ["command"], self.toggleTypingPane, "Toggle typing pane"),
            ("f", ["command"], self.flipCurrentPair, "Flip Pair"),
            ("f", ["command", "option"], self.togglePairListFilter, "Toggle pair list filter"),
            ("i", ["command", "option"], self.toggleEditGlyphInfo, "Toggle glyph info"),
            ("I", ["command", "option", "shift"], self.toggleTypingGlyphInfo, "Toggle typeing glyph info"),
            ("G", ["command", "shift"], self.toggleEditGroupPreview, "Toggle group preview"),
            ("g", ["command"], self.toggleEditGroupStack, "Toggle groups stack"),
            ("=", ["command"], self.editTextLarger, "Make text bigger"),
            ("-", ["command"], self.editTextSmaller, "Make text smaller"),
            ("2", ["command"], self.showGroupEditor, "Show group editor"),
            ("3", ["command"], self.showReferenceGroupEditor, "Show refernece group editor"),
            ("4", ["command"], self.showSpreadsheet, "Show spreadsheet"),
            ("5", ["command"], self.showTransformations, "Show transformations"),
            ("0", ["command"], self.showPairListBuilder, "Show pair list builder"),
        ]
        self._keyEventMonitor = KeyEventMonitor(shortcuts)
        self._keyEventMonitor.subscribe()

        self.pairListLeftPosition = (0, 0, 241, -0)
        self.pairListLeftEditViewPosition = (240, 0, -1, -0)
        self.pairListLeftClosedEditViewPosition = (0, 0, -1, -0)
        self.pairListRightPosition = (-241, 0, 240, -0)
        self.pairListRightEditViewPosition = (0, 0, -240, -0)
        self.pairListRightClosedEditViewPosition = (0, 0, -1, -0)

        if getExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListOnLeft"):
            self.pairListPosition = self.pairListLeftPosition
            self.editViewPositionWithPairList = self.pairListLeftEditViewPosition
            self.editViewPositionWithoutPairList = self.pairListLeftClosedEditViewPosition
        else:
            self.pairListPosition = self.pairListRightPosition
            self.editViewPositionWithPairList = self.pairListRightEditViewPosition
            self.editViewPositionWithoutPairList = self.pairListRightClosedEditViewPosition

        self.editView = PairGroup(self.editViewPositionWithPairList, self.font, selectionCallback=self.editViewSelection)

        self.pairList = PairList(self.pairListPosition, self.font, selectionCallback=self.pairListSelectionCallback)
        self.pairList.frameAdjustments = (-1, 0, 1, 1)
        self.pairListTitle = ""
        self.pairList.set(font.kerning.metricsMachine.pairsSortedByUnicode())

        self.typingView = TypingGroup((0, 0, -0, -0), font, pseudoFeatures=True)

        self.topGroup = vanilla.Group((0, 0, -0, -0))
        self.topGroup.pairList = self.pairList
        self.topGroup.editView = self.editView

        paneDescriptions = [
            dict(view=self.topGroup, canCollapse=False, minSize=200, identifier="editPane"),
            dict(view=self.typingView, canCollapse=False, minSize=100, identifier="typingPane")
        ]
        splitView = vanilla.SplitView(
            (0, 0, -0, -0),
            paneDescriptions=paneDescriptions,
            isVertical=False,
            dividerStyle="thick",
        )
        splitView.frameAdjustments = (0, 0, 2, 0)

        self.editView.pairView.setPosSize(self.editView.pairView.getPosSize())
        self.typingView.typingView.setPosSize(self.editView.pairView.getPosSize())

        self.w.splitView = splitView

        # reset the pos size to get it right
        # self.editView.setPosSize(self.editView.getPosSize())

        self.applyWindowDefaults()

        self.font.addObserver(self, "fontChangedCallback", "Font.Changed")
        self.setUpBaseWindowBehavior()

        self.editView.setupKeyLoop(self.w)

        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()

        self.__contextStringChangedCallback = CallbackWrapper(self.contextStringChanged)
        notificationCenter.addObserver_selector_name_object_(self.__contextStringChangedCallback, "action:", "MM4.MMContextStringsChanged", None)
        self.__defaultWindowSettingsChangedCallback = CallbackWrapper(self.defaultWindowSettingsChanged)
        notificationCenter.addObserver_selector_name_object_(self.__defaultWindowSettingsChangedCallback, "action:", "MM4.DefaultWindowSettingsChanged", None)

        publishEvent("MetricsMachine.ControllerWillOpen", font=self.font, controller=self.w)

        self.w.open()

    # -----------
    # convenience
    # -----------

    def _get_document(self):
        return self.w.getNSWindow().document()

    document = property(_get_document)

    def assignToDocument(self, document):
        self.w.assignToDocument(document)

    def getWindowTitleValue(self):
        pairCount = len(self.font.kerning)
        groupCount = self.font.groups.metricsMachine.kerningGroupCount
        fileName = "Untitled"
        if self.font.path:
            fileName = os.path.basename(self.font.path)
        return f"{fileName} - {pairCount} pairs, {groupCount} groups"

    def updateWindowTitle(self):
        self.w.setTitle(self.getWindowTitleValue())

    # -----
    # prefs
    # -----

    def applyWindowDefaults(self):
        # pair list
        pairListState = self.pairList.isVisible()
        # position
        pairListOnLeft = getExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListOnLeft")
        if pairListOnLeft and self.pairListPosition == self.pairListLeftPosition:
            pass
        else:
            if pairListOnLeft:
                self.pairListPosition = self.pairListLeftPosition
                self.editViewPositionWithPairList = self.pairListLeftEditViewPosition
                self.editViewPositionWithoutPairList = self.pairListLeftClosedEditViewPosition
            else:
                self.pairListPosition = self.pairListRightPosition
                self.editViewPositionWithPairList = self.pairListRightEditViewPosition
                self.editViewPositionWithoutPairList = self.pairListRightClosedEditViewPosition
            del self.topGroup.pairList
            del self.topGroup.editView
            self.pairList.setPosSize(self.pairListPosition)
            editViewPosSize = self.editViewPositionWithPairList
            if not pairListState:
                editViewPosSize = self.editViewPositionWithoutPairList
            self.editView.setPosSize(editViewPosSize)
            self.topGroup.pairList = self.pairList
            self.topGroup.editView = self.editView
        # show
        showPairList = getExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListVisibleByDefault")
        if showPairList != pairListState:
            self.togglePairList()
        # typing pane
        showTypingPane = getExtensionDefault("com.typesupply.MM4.windowSettings.main.typingPaneVisibleByDefault")
        typingPaneState = self.w.splitView.isPaneVisible("typingPane")
        if showTypingPane == typingPaneState:
            self.toggleTypingPane()
        # info
        showInfo = getExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.glyphInfoVisibleByDefault")
        infoState = self.editView.isInfoVisible()
        if showInfo != infoState:
            self.toggleEditGlyphInfo()
        # group preview
        showPreview = getExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupPreviewVisibleByDefault")
        previewState = self.editView.isGroupPreviewVisible()
        if showPreview != previewState:
            self.toggleEditGroupPreview()
        # group stack
        showStack = getExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupStackVisibleByDefault")
        stackState = self.editView.isGroupStackVisible()
        self.editView.pairView._pairView.flushFrame()
        if showStack != stackState:
            self.toggleEditGroupStack()

    # ---------
    # callbacks
    # ---------

    def pairListSelectionCallback(self, sender):
        if not hasattr(self, "editView"):
            return
        selection = sender.getSelection()
        if not selection:
            return
        pair, context, index = selection
        self.editView.set(pair, context=context, index=index)

    def editViewSelection(self, sender):
        pair = sender.get()
        self.pairList.setSelection(pair)

    # -------------
    # notifications
    # -------------

    def fontChangedCallback(self, notification):
        document = self.document
        if document is None:
            return
        document.updateChangeCount_(AppKit.NSChangeDone)
        self.updateWindowTitle()

    def contextStringChanged(self, notification):
        defaultStrings = getExtensionDefault("com.typesupply.MM4.contextStrings")
        self.font.metricsMachine.contextStrings.set(defaultStrings)

    def defaultWindowSettingsChanged(self, notification):
        self.applyWindowDefaults()

    def windowCloseCallback(self, sender):
        self._keyEventMonitor.unsubscribe()
        self._keyEventMonitor = None
        self.font.removeObserver(self, "Font.Changed")
        publishEvent("MetricsMachine.ControllerWillClose", font=self.font, controller=self.w)

        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self.__contextStringChangedCallback)
        notificationCenter.removeObserver_(self.__defaultWindowSettingsChangedCallback)
        del self.__contextStringChangedCallback
        del self.__defaultWindowSettingsChangedCallback

        super(MMDocumentWindowController, self).windowCloseCallback(sender)

    def windowSelectCallback(self, sender):
        self._keyEventMonitor.subscribe()

    def windowDeselectCallback(self, sender):
        self._keyEventMonitor.unsubscribe()

    # ----------
    # menu items
    # ----------

    # kerning

    def makeException(self, sender=None):
        self.editView.makeException()

    def breakException(self, sender=None):
        self.editView.breakException()

    # file

    def importKerning(self):
        messageText = "Are you sure you want to import kerning?"
        informativeText = "This will replace all kerning and all groups in this font. This cannot be undone."
        self.showAskYesNo(messageText, informativeText, self._importKerningConfirmation)

    def _importKerningConfirmation(self, result):
        if not result:
            return
        self.showGetFile(["ufo", "fea"], self._importKerning, allowsMultipleSelection=False)

    def _importKerning(self, path):
        if not path:
            return
        path = path[0]
        if path.lower().endswith("ufo"):
            self.font.kerning.metricsMachine.importKerningFromUFO(path)
        else:
            errorMessage = self.font.kerning.metricsMachine.importKerningFromFeatureFile(path)
            if errorMessage:
                self.showMessage("Import failed.", errorMessage)

    def exportKerning(self):
        from mm4.interface.kerningExportSheet import KerningExportSettingsSheet
        KerningExportSettingsSheet(self.w, self._exportKerningResult)

    def _exportKerningResult(self, settings):
        if settings["destination"] == "ufo":
            bundle = ExtensionBundle("Metrics Machine")
            version = str(bundle.version)
            subtableBreaks = settings["subtable"]
            self.font.kerning.metricsMachine.exportKerningToFeatureFile(None, appVersion=version, subtableBreaks=subtableBreaks)
        else:
            self.exportSettings = settings
            if settings["mode"] == "afm":
                suffix = "afm"
                path = os.path.splitext(self.font.path)[0] + ".afm"
            else:
                suffix = "fea"
                path = os.path.splitext(self.font.path)[0] + " kern.fea"
            directory, fileName = os.path.split(path)
            self.showPutFile([suffix], callback=self._exportKerningExternalResult, fileName=fileName, directory=directory)

    def _exportKerningExternalResult(self, path):
        if path is not None:
            bundle = ExtensionBundle("Metrics Machine")
            version = str(bundle.version)
            mode = self.exportSettings["mode"]
            subtableBreaks = self.exportSettings["subtable"]
            if mode == "afm":
                self.font.kerning.metricsMachine.exportKerningToAFMFile(path, glyphs=self.font.keys(), appVersion=version)
            else:
                self.font.kerning.metricsMachine.exportKerningToFeatureFile(path, appVersion=version, subtableBreaks=subtableBreaks)
        del self.exportSettings

    def loadPairList(self, sender=None):
        self.showGetFile(["txt"], self._loadPairListResult, allowsMultipleSelection=False)

    def _loadPairListResult(self, path):
        if not path:
            return
        path = path[0]
        with open(path, "r") as f:
            text = f.read()
        self._setPairList(text)

    def _setPairList(self, text):
        from mm4.tools.pairListParser import parsePairList
        result = parsePairList(text, self.font)
        if isinstance(result, str):
            self.showMessage("The file could not be loaded.", result)
        else:
            pairs, mode, title = result
            # XXX deal with forced mode switch here
            self.pairList.set(pairs)
            self.pairListTitle = title
            self.editView.setPairListCount(len(pairs)-1)
            self.pairListSelectionCallback(self.pairList)

    # edit

    def clearAllKerning(self):
        self.showAskYesNo("Clear all kerning?", "This cannot be undone.", callback=self._clearAllKerning)

    def _clearAllKerning(self, result):
        if not result:
            return
        self.font.kerning.clear()

    # navigation

    def selectNextPair(self):
        self.pairList.selectNextPair()

    def selectPreviousPair(self):
        self.pairList.selectPreviousPair()

    # view

    def togglePairList(self, sender=None):
        if self.pairList.isVisible():
            self.pairList.show(False)
            self.editView.setPosSize(self.editViewPositionWithoutPairList)
        else:
            self.pairList.show(True)
            self.editView.setPosSize(self.editViewPositionWithPairList)

    def togglePairListFilter(self, sender=None):
        self.pairList.toggleFilter()

    def toggleTypingPane(self, sender=None):
        self.w.splitView.togglePane("typingPane", animate=False)

    def flipCurrentPair(self, sender=None):
        self.editView.flipCurrentPair()

    def toggleEditGlyphInfo(self, sender=None):
        self.editView.toggleGlyphInfo()

    def toggleEditGroupPreview(self, sender=None):
        self.editView.toggleGroupPreview()

    def toggleEditGroupStack(self, sender=None):
        self.editView.toggleGroupStack()

    def editTextLarger(self, sender=None):
        self.editView.increasePointSize()

    def editTextSmaller(self, sender=None):
        self.editView.decreasePointSize()

    def toggleTypingGlyphInfo(self, sender=None):
        self.typingView.toggleGlyphInfo()

    def showFontInfo(self):
        from mm4.interface.fontInfoSheet import FontInfoSheet
        FontInfoSheet(self.w, self.font, self.pairListTitle, self.editView.get())

    def showGroupEditor(self, sender=None):
        from mm4.interface.groupEditSheet import GroupEditSheet
        progress = self.startProgress("Loading groups...")
        GroupEditSheet(self.w, self.font, progress)

    def showReferenceGroupEditor(self, sender=None):
        from mm4.interface.referenceGroupEditSheet import ReferenceGroupEditSheet
        progress = self.startProgress("Loading groups...")
        ReferenceGroupEditSheet(self.w, self.font, progress)

    def showSpreadsheet(self, sender=None):
        from mm4.interface.spreadsheetSheet import SpreadsheetSheet
        progress = self.startProgress("Analyzing kerning...")
        SpreadsheetSheet(self.w, self.font, progress)

    def showTransformations(self, sender=None):
        from mm4.interface.transformationSheet import TransformationSheet
        TransformationSheet(self.w, self.font)

    def showPairListBuilder(self, sender=None):
        from mm4.interface.pairListBuilderSheet import PairListBuilderSheet
        progress = self.startProgress("Loading glyphs...")
        PairListBuilderSheet(self.w, self.font, progress, setCallback=self._setPairList)
