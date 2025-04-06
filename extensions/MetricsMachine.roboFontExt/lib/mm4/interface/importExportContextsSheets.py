import AppKit
import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController

from mojo.extensions import getExtensionDefault, setExtensionDefault


class _BaseSheet(BaseWindowController):

    def __init__(self, parentWindow, contexts):
        self.contexts = contexts
        titles = [i["name"] for i in self.contexts]

        w = 300
        self.w = vanilla.Sheet((w, 400), minSize=(w, 200), maxSize=(w, 10000), parentWindow=parentWindow)
        self.w.info = vanilla.TextBox((15, 15, -15, 17), "Select the contexts you want to %s." % self.mode)
        self.w.list = vanilla.List((15, 45, -15, -65), titles, drawFocusRing=False)

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "OK", callback=self.okCallback)
        self.w.setDefaultButton(self.w.applyButton)

        self.setUpBaseWindowBehavior()
        self.w.open()

    def cancelCallback(self, sender=None):
        self.w.close()


class ExportContextsSheet(_BaseSheet):

    def __init__(self, parentWindow):
        self.mode = "export"
        contexts = getExtensionDefault("com.typesupply.MM4.contextStrings")
        super(ExportContextsSheet, self).__init__(parentWindow, contexts)

    def _export(self, path):
        if path is not None:
            toExport = [self.contexts[i] for i in self.w.list.getSelection()]
            toExport = AppKit.NSArray.arrayWithArray_(toExport)
            toExport.writeToFile_atomically_(path, False)
        self.w.close()

    def okCallback(self, sender):
        self.showPutFile(["mmcontexts"], callback=self._export)


class ImportContextsSheet(_BaseSheet):

    def __init__(self, parentWindow, path, reloadCallback):
        self.callback = reloadCallback
        self.mode = "import"
        contexts = AppKit.NSArray.alloc().initWithContentsOfFile_(path)
        error = False
        if contexts is None:
            contexts = []
            error = True
        super(ImportContextsSheet, self).__init__(parentWindow, contexts)
        if error:
            messageText = "Import failed."
            informativeText = "The selected file could not be read. Please check the syntax and try again."
            self.showMessage(messageText, informativeText, callback=self.cancelCallback)

    def okCallback(self, sender):
        toImport = [self.contexts[i] for i in self.w.list.getSelection()]
        contexts = getExtensionDefault("com.typesupply.MM4.contextStrings")
        contexts.extend(toImport)
        setExtensionDefault("com.typesupply.MM4.contextStrings", contexts)
        self.w.close()
        self.callback()
        del self.callback
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.postNotificationName_object_("MM4.MMContextStringsChanged", None)
