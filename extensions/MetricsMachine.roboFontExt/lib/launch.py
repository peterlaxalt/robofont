import AppKit
import os

import defcon
from mojo.extensions import ExtensionBundle

import metricsMachine

import mm4.objects
from mm4.interface.documentWindow import MMDocumentWindowController
from mm4.tools.icon import getIconMenuImage
import mm4.defaults

from mm4.menubar import SharedMenubar
from mojo.events import addObserver


from mm4.interface.representations.groupIndicatingGlyphCell import GroupIndicatingGlyphCellFactory
from mm4.interface.representations.noLayerGlyphCell import NoLayerGlyphCellFactory
from mm4.interface.representations.pairCountIndicatingGlyphCell import PairCountIndicatingGlyphCellFactory
from mm4.interface.representations.groupEditDetail import GroupEditDetailFactory

defcon.registerRepresentationFactory(defcon.Glyph, "GroupIndicatingGlyphCell", GroupIndicatingGlyphCellFactory)
defcon.registerRepresentationFactory(defcon.Glyph, "NoLayerGlyphCell", NoLayerGlyphCellFactory)
defcon.registerRepresentationFactory(defcon.Glyph, "PairCountIndicatingGlyphCell", PairCountIndicatingGlyphCellFactory)
defcon.registerRepresentationFactory(defcon.Glyph, "GroupEditDetail", GroupEditDetailFactory)


_images = {}


def loadImages(root):
    for fileName in os.listdir(root):
        name, ext = os.path.splitext(fileName)
        if ext in [".png", ".pdf", ".icns", "tiff"]:
            imagePath = os.path.join(root, fileName)
            _images[name] = AppKit.NSImage.alloc().initWithContentsOfFile_(imagePath)
            _images[name].setName_(name)


loadImages(os.path.join(os.path.dirname(__file__), "Images"))


class MetricsMachineController(object):

    def __init__(self):
        self._openControllers = {}

        self.menubar = SharedMenubar()

        self.menubarItems = [
            dict(
                title="Open Metrics Machine",
                identifier="fileOpenMetricsMachine",
                binding=("m", ["command", "shift"]),
                callback=self.menuOpenMetricsMachine
            ),
            dict(
                title="File",
                items=[
                    dict(
                        title="Import Kerning...",
                        identifier="fileImportKerning",
                        callback=self.menuFileImportKerningCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Export Kerning...",
                        identifier="fileExportKerning",
                        callback=self.menuFileExportKerningCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Clear Kerning",
                        identifier="fileClearKerning",
                        callback=self.menuFileClearKerningCallback,
                        needsMMControler=True,
                    ),
                    dict(separator=True),
                    dict(
                        title="Load Pair List...",
                        identifier="fileLoadPairList",
                        callback=self.menuFileLoadPairListCallback,
                        needsMMControler=True,
                    ),
                ]
            ),
            dict(
                title="Exception",
                items=[
                    dict(
                        title="Make",
                        identifier="exceptionMake",
                        action="makeException:",
                    ),
                    dict(
                        title="Break",
                        identifier="exceptionBreak",
                        action="breakException:",
                    ),
                    # dict(
                    #     title="Clear All",
                    #     identifier="exceptionClearAll",
                    #     callback=self.menuExceptionClearAllCallback
                    # )
                ]
            ),
            dict(
                title="View",
                items=[
                    dict(
                        title="Pair List",
                        identifier="viewPairList",
                        callback=self.menuViewPairListCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Preview",
                        identifier="viewPreview",
                        callback=self.menuViewPreviewCallback,
                        needsMMControler=True,
                    ),
                    dict(separator=True),
                    # dict(
                    #     title="Matrix",
                    #     identifier="viewMatrix",
                    #     callback=self.menuViewMatrixCallback
                    # ),
                    dict(
                        title="Group Preview",
                        identifier="viewGroupPreview",
                        callback=self.menuViewGroupPreviewCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Group Stack",
                        identifier="viewGroupStack",
                        callback=self.menuViewGroupStackCallback,
                        needsMMControler=True,
                    ),
                    # dict(
                    #     title="Apply Kerning",
                    #     identifier="viewApplyKerning",
                    #     callback=self.menuViewApplyKerningCallback
                    # ),
                    dict(separator=True),
                    dict(
                        title="Make Text Bigger",
                        identifier="viewTextBigger",
                        callback=self.menuViewTextBiggerCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Make Text Smaller",
                        identifier="viewTextSmaller",
                        callback=self.menuViewTextSmallerCallback,
                        needsMMControler=True,
                    ),
                    # dict(separator=True),
                    # dict(
                    #     title="Layer Visibility...",
                    #     identifier="viewShowLayers",
                    #     callback=self.menuViewShowLayers
                    # ),
                    dict(separator=True),
                    # dict(
                    #     title="Notes",
                    #     identifier="viewShowNotes",
                    #     callback=self.menuViewShowNotesCallback
                    # ),
                    dict(
                        title="Groups",
                        identifier="viewShowGroups",
                        callback=self.menuViewShowGroupsCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Reference Groups",
                        identifier="viewShowReferenceGroups",
                        callback=self.menuViewShowReferenceGroupsCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Spreadsheet",
                        identifier="viewShowSpreadsheet",
                        callback=self.menuViewShowSpreadsheetCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Transform",
                        identifier="viewShowTransform",
                        callback=self.menuViewShowTransformCallback,
                        needsMMControler=True,
                    ),
                    dict(
                        title="Pair List Builder",
                        identifier="viewShowPairListBuilder",
                        callback=self.menuViewShowPairListBuilder,
                        needsMMControler=True,
                    )
                ]
            ),
            dict(
                title="Pairs",
                items=[
                    dict(
                        title="Flip Pair",
                        identifier="viewFlipPair",
                        action="flipCurrentPair:",
                    ),
                    dict(
                        title="Next in Left Group",
                        identifier="viewNextInLeftGroup",
                        action="selectNextInLeftGroup:",
                    ),
                    dict(
                        title="Previous in Left Group",
                        identifier="viewPreviousInLeftGroup",
                        action="selectPreviousInLeftGroup:",
                    ),
                    dict(
                        title="Next in Right Group",
                        identifier="viewNextInRightGroup",
                        action="selectNextInRightGroup:",
                    ),
                    dict(
                        title="Previous in Right Group",
                        identifier="viewPreviousInRightGroup",
                        action="selectPreviousInRightGroup:",
                    ),
                ]
            ),
            dict(separator=True),
            dict(
                title="Batch Export...",
                identifier="batchExport",
                callback=self.menuBatchExportCallback
            ),
            dict(
                title="Preferences...",
                identifier="preferences",
                callback=self.menuPreferencesCallback
            ),
            dict(
                title="Help...",
                identifier="help",
                callback=self.menuHelpCallback
            ),
        ]
        self.menubar.buildMenu("MM4", "MetricsMachine", self.menubarItems, image=getIconMenuImage())

        addObserver(self, "fontWillClose", "fontWillClose")
        addObserver(self, "controllerWillClose", "MetricsMachine.ControllerWillClose")

        self._validateMenu()

    def fontWillClose(self, notification):
        font = notification["font"]
        self._removeController(font)

    def controllerWillClose(self, notification):
        font = notification["font"]
        self._removeController(font)

    def _removeController(self, font):
        if hasattr(font, "naked"):
            font = font.naked()
        if font in self._openControllers:
            del self._openControllers[font]
        self._validateMenu()

    def _validateMenu(self):

        enabled = bool(self.currentController())

        def _validateMenuItems(items):
            for item in items:
                _validateMenuItems(item.get("items", []))
                if item.get("identifier") and item.get("needsMMControler", False):
                    menuItem = self.menubar.getItem(item.get("identifier"))
                    if menuItem is not None:
                        menuItem.menu().setAutoenablesItems_(False)
                        menuItem.setEnabled_(enabled)

        _validateMenuItems(self.menubarItems)

    def currentController(self):
        fontPartsFont = CurrentFont()
        if fontPartsFont is not None:
            defconFont = fontPartsFont.naked()
            return self._openControllers.get(defconFont)
        return None

    def menuOpenMetricsMachine(self, sender):
        fontPartsFont = CurrentFont()
        if fontPartsFont is None:
            from vanilla.dialogs import message
            message("Metrics Machine", "Open at least one .ufo file.")
            return
        defconFont = fontPartsFont.naked()

        try:
            controller = self._openControllers[defconFont]
            controller.w.getNSWindow().makeKeyAndOrderFront_(None)
            self._validateMenu()
            return
        except Exception:
            pass

        controller = MMDocumentWindowController(defconFont)
        controller.assignToDocument(fontPartsFont.document())
        self._openControllers[defconFont] = controller
        self._validateMenu()

    def menuFileImportKerningCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.importKerning()

    def menuFileExportKerningCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.exportKerning()

    def menuFileClearKerningCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.clearAllKerning()

    def menuFileLoadPairListCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.loadPairList()

    # def menuExceptionClearAllCallback(self, sender):
    #     controller = self.currentController()
    #     if controller:
    #         controller.loadPairList()

    def menuViewPairListCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.togglePairList()

    def menuViewPreviewCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.toggleTypingPane()

    # def menuViewMatrixCallback(self, sender):
    #     print "menuViewMatrixCallback"

    def menuViewGroupPreviewCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.toggleEditGroupPreview()

    def menuViewGroupStackCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.toggleEditGroupStack()

    # def menuViewApplyKerningCallback(self, sender):
    #     print "menuViewApplyKerningCallback"

    def menuViewTextBiggerCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.editTextLarger()

    def menuViewTextSmallerCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.editTextSmaller()

    # def menuViewShowLayer(self, sender):
    #     print "menuViewShowLayer"

    # def menuViewShowLayers(self, sender):
    #     print "menuViewShowLayers"

    # def menuViewShowNotesCallback(self, sender):
    #     print "menuViewShowNotesCallback"

    def menuViewShowGroupsCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.showGroupEditor()

    def menuViewShowReferenceGroupsCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.showReferenceGroupEditor()

    def menuViewShowSpreadsheetCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.showSpreadsheet()

    def menuViewShowTransformCallback(self, sender):
        controller = self.currentController()
        if controller:
            controller.showTransformations()

    def menuViewShowPairListBuilder(self, sender):
        controller = self.currentController()
        if controller:
            controller.showPairListBuilder()

    def menuBatchExportCallback(self, sender):
        from mm4.interface.batchExportWindow import BatchExportWindow
        if hasattr(self, "batchExportWindow"):
            if self.batchExportWindow is not None:
                try:
                    self.batchExportWindow.bringWindowToFront()
                    return
                except Exception:
                    pass
        self.batchExportWindow = BatchExportWindow()

    def menuPreferencesCallback(self, sender):
        from mm4.interface.prefsWindow import PrefsWindow
        if hasattr(self, "prefsWindow"):
            if self.prefsWindow is not None:
                try:
                    self.prefsWindow.bringWindowToFront()
                    return
                except Exception:
                    pass
        self.prefsWindow = PrefsWindow()

    def menuHelpCallback(self, sender):
        ExtensionBundle("MetricsMachine").openHelp()


MetricsMachineController()
