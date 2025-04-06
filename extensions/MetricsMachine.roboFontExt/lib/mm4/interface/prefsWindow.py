import AppKit
import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController
from mm4.interface.views.contextPrefsView import ContextPrefsView

from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.events import publishEvent


class PrefsWindow(BaseWindowController):

    def __init__(self):
        self.contextWidth = 650
        self.contextHeight = 379
        self.settingsWidth = 250
        self.settingsHeight = 335
        self.w = vanilla.Window((self.contextWidth, self.contextHeight))

        # build the toolbar
        items = [
            dict(
                itemIdentifier="showContexts",
                label="Contexts",
                imageNamed="MMprefsToolbarContexts",
                callback=self.toolbarSelectionCallback,
                selectable=True
            ),
            dict(
                itemIdentifier="showSettings",
                label="General",
                imageNamed="MMprefsToolbarSettings",
                callback=self.toolbarSelectionCallback,
                selectable=True
            )
        ]
        self.w.addToolbar(toolbarIdentifier="MetricsMachinePrefsToolbar", toolbarItems=items, addStandardItems=False)
        toolbar = self.w.getNSWindow().toolbar()
        toolbar.setAllowsUserCustomization_(False)
        toolbar.setSelectedItemIdentifier_("showContexts")
        self.w.getNSWindow().setShowsToolbarButton_(False)

        self.w.tabs = vanilla.Tabs((0, 0, -0, -0), ["Contexts", "Window Setup"], showTabs=False)
        self.w.tabs[0].contextView = self.contextView = ContextPrefsView((0, 0, -0, -0), self, self.contextHeight)
        self.w.tabs[1].settingsView = WindowSetupView()

        self.setUpBaseWindowBehavior()
        self.w.open()

    def bringWindowToFront(self):
        self.w.getNSWindow().makeKeyAndOrderFront_(None)

    def windowCloseCallback(self, sender):
        super(PrefsWindow, self).windowCloseCallback(sender)

    def toolbarSelectionCallback(self, sender):
        identifier = sender.itemIdentifier()
        if identifier == "showContexts":
            tab = 0
        else:
            tab = 1
        if self.w.tabs.get() == tab:
            return
        self.w.tabs.set(tab)
        if identifier == "showContexts":
            x, y, w, h = self.w.getPosSize()
            self.w.setPosSize((x, y, self.contextWidth, self.contextHeight))
            self.w.tabs[0].contextView = self.contextView
            self.contextView.show(True)
        else:
            del self.w.tabs[0].contextView
            self.w.tabs[1].settingsView.show(False)
            x, y, w, h = self.w.getPosSize()
            self.w.setPosSize((x, y, self.settingsWidth, self.settingsHeight))
            self.w.tabs[1].settingsView.show(True)

    def contextsRequireResize(self, height):
        self.contextHeight = height
        x, y, w, h = self.w.getPosSize()
        self.w.setPosSize((x, y, w, height))

    # ----------------------
    # import/export contexts
    # ----------------------

    def exportContexts(self):
        from mm4.interface.importExportContextsSheets import ExportContextsSheet
        ExportContextsSheet(self.w)

    def importContexts(self):
        self.showGetFile(["mmcontexts"], allowsMultipleSelection=False, callback=self._importContexts)

    def _importContexts(self, path):
        if not path:
            return
        from mm4.interface.importExportContextsSheets import ImportContextsSheet
        ImportContextsSheet(self.w, path[0], self._finishedImport)

    def _finishedImport(self):
        self.w.tabs[0].contextView.reload()


pointSizeFormatter = AppKit.NSNumberFormatter.alloc().init()
pointSizeFormatter.setFormat_("#;0;-#")
pointSizeFormatter.setAllowsFloats_(False)
pointSizeFormatter.setGeneratesDecimalNumbers_(False)
pointSizeFormatter.setMinimum_(AppKit.NSNumber.numberWithInt_(1))


class WindowSetupView(vanilla.Group):


    def __init__(self):
        super(WindowSetupView, self).__init__((0, 0, -0, -0))

        showPairList = getExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListVisibleByDefault")
        showTypingPane = getExtensionDefault("com.typesupply.MM4.windowSettings.main.typingPaneVisibleByDefault")
        pairListOnLeft = getExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListOnLeft")
        if pairListOnLeft:
            pairListPosition = 0
        else:
            pairListPosition = 1
        showGlyphInfo = getExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.glyphInfoVisibleByDefault")
        showGroupPreview = getExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupPreviewVisibleByDefault")
        groupPreviewSize = getExtensionDefault("com.typesupply.MM4.viewSettings.general.groupPreviewPointSize")
        showGroupStack = getExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupStackVisibleByDefault")
        invertPreviews = getExtensionDefault("com.typesupply.MM4.viewSettings.general.invertPreviews", False)
        increments = getExtensionDefault("com.typesupply.MM4.viewSettings.general.kernIncrements", (1, 5, 10))

        y = 15
        self.increments = vanilla.TextBox((34, y, 150, 17), "Increments")
        y += 25
        self.incrementOption = vanilla.EditText((34, y, 50, 22), text=increments[0], formatter=pointSizeFormatter, callback=self.somethingChanged)
        self.incrementShift = vanilla.EditText((94, y, 50, 22), text=increments[1], formatter=pointSizeFormatter, callback=self.somethingChanged)
        self.incrementBasic = vanilla.EditText((154, y, 50, 22), text=increments[2], formatter=pointSizeFormatter, callback=self.somethingChanged)
        y += 25
        self.incrementOptionLabel = vanilla.TextBox((34, y, 55, 17), "Option", sizeStyle='mini')
        self.incrementShiftLabel = vanilla.TextBox((94, y, 55, 17), "Shift", sizeStyle='mini')
        self.incrementBasicLabel = vanilla.TextBox((154, y, 100, 17), "No Modifiers", sizeStyle='mini')
        y += 22
        self.line = vanilla.HorizontalLine((15, y, 220, 1))
        y += 12
        self.showTypingPane = vanilla.CheckBox((15, y, 150, 22), "Show Typing Pane", value=showTypingPane, callback=self.somethingChanged)
        y += 25
        self.showPairList = vanilla.CheckBox((15, y, 150, 22), "Show Pair List", value=showPairList, callback=self.somethingChanged)
        y += 25
        self.pairListPosition = vanilla.RadioGroup((30, y, 120, 40), ["Left", "Right"], callback=self.somethingChanged)
        self.pairListPosition.set(pairListPosition)
        y += 45
        self.showGlyphInfo = vanilla.CheckBox((15, y, 150, 22), "Show Glyph Info", value=showGlyphInfo, callback=self.somethingChanged)
        y += 25
        self.showGroupPreview = vanilla.CheckBox((15, y, 150, 22), "Show Group Preview", value=showGroupPreview, callback=self.somethingChanged)
        y += 25
        self.groupPreviewSize = vanilla.EditText((34, y, 40, 22), groupPreviewSize, formatter=pointSizeFormatter, callback=self.somethingChanged)
        self.groupPreviewSizeTitle = vanilla.TextBox((78, y, 50, 17), "pt.")
        y += 25
        self.showGroupStack = vanilla.CheckBox((15, y, 150, 22), "Show Group Stack", value=showGroupStack, callback=self.somethingChanged)
        y += 25
        self.invertPreviews = vanilla.CheckBox((15, y, 230, 22), "Invert Previews", value=invertPreviews, callback=self.somethingChanged)


    def somethingChanged(self, sender):
        setExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListVisibleByDefault", self.showPairList.get())
        setExtensionDefault("com.typesupply.MM4.windowSettings.main.typingPaneVisibleByDefault", self.showTypingPane.get())
        setExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.glyphInfoVisibleByDefault", self.showGlyphInfo.get())
        setExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupPreviewVisibleByDefault", self.showGroupPreview.get())
        setExtensionDefault("com.typesupply.MM4.viewSettings.general.groupPreviewPointSize", self.groupPreviewSize.get())
        setExtensionDefault("com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupStackVisibleByDefault", self.showGroupStack.get())
        setExtensionDefault("com.typesupply.MM4.viewSettings.general.kernIncrements", (self.incrementOption.get(), self.incrementShift.get(), self.incrementBasic.get()))
        setExtensionDefault("com.typesupply.MM4.viewSettings.general.invertPreviews", self.invertPreviews.get())
        if self.pairListPosition.get() == 0:
            setExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListOnLeft", True)
        else:
            setExtensionDefault("com.typesupply.MM4.windowSettings.main.pairListOnLeft", False)
        # post notifications
        try:
            if sender.getTitle() == "Invert Previews":
                publishEvent("com.typesupply.MM4.invertPreviewsSettingDidChange", invert=self.invertPreviews.get())
        except:
            pass
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.postNotificationName_object_("MM4.DefaultWindowSettingsChanged", None)
        if sender == self.groupPreviewSize:
            notificationCenter.postNotificationName_object_("MM4.GroupPreviewPointSizeChanged", None)
