import os
import AppKit
import vanilla
from mojo.roboFont import OpenFont
from defconAppKit.windows.baseWindow import BaseWindowController
from mm4.interface.kerningExportSheet import KerningExportSettingsView

from lib.tools.debugTools import ClassNameIncrementer

class UFOPathFormatter(AppKit.NSFormatter, metaclass=ClassNameIncrementer):

    def stringForObjectValue_(self, obj):
        if obj is None or isinstance(obj, AppKit.NSNull):
            return ""
        return os.path.basename(obj)

    def objectValueForString_(self, string):
        return string


class BatchExportWindow(BaseWindowController):

    def __init__(self):
        width = 300
        self.w = vanilla.Window((width, 500), "Batch Export", minSize=(width, 300), maxSize=(width, 1000))

        columnDescriptions = [dict(title="path", formatter=UFOPathFormatter.alloc().init())]
        self.w.fontList = vanilla.List((15, 15, -15, -195), [], columnDescriptions=columnDescriptions, showColumnTitles=False,
            drawFocusRing=False, enableDelete=True,
            otherApplicationDropSettings=dict(type=AppKit.NSFilenamesPboardType, operation=AppKit.NSDragOperationCopy, callback=self.dropFontCallback))

        self.w.exportSettings = KerningExportSettingsView((15, -185, -15, 125), callback=self.exportModeCallback)
        self.w.line = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.overwriteExistingCheckBox = vanilla.CheckBox((15, -36, -110, 22), "Overwrite exsting files")
        self.w.exportButton = vanilla.Button((-100, -35, -15, 20), "Export", callback=self.exportCallback)

        self.setUpBaseWindowBehavior()
        self.w.open()

    def bringWindowToFront(self):
        self.w.getNSWindow().makeKeyAndOrderFront_(None)

    def windowCloseCallback(self, sender):
        super(BatchExportWindow, self).windowCloseCallback(sender)

    def exportModeCallback(self, sender):
        mode = sender.get()["mode"]
        adjustment = 100
        if mode == "afm":
            x, y, w, h = self.w.exportSettings.getPosSize()
            self.w.exportSettings.setPosSize((x, y + adjustment, w, h - adjustment))
            x, y, w, h = self.w.fontList.getPosSize()
            self.w.fontList.setPosSize((x, y, w, h + adjustment))
        else:
            x, y, w, h = self.w.exportSettings.getPosSize()
            self.w.exportSettings.setPosSize((x, y - adjustment, w, h + adjustment))
            x, y, w, h = self.w.fontList.getPosSize()
            self.w.fontList.setPosSize((x, y, w, h - adjustment))

    # ---------
    # File Drop
    # ---------

    def dropFontCallback(self, sender, dropInfo):
        isProposal = dropInfo["isProposal"]
        paths = dropInfo["data"]
        paths = [dict(path=path) for path in paths if os.path.splitext(path)[-1].lower() == ".ufo"]
        paths = [path for path in paths if path not in self.w.fontList]
        if not paths:
            return False
        if not isProposal:
            self.w.fontList.extend(paths)
        return True

    # ------
    # Export
    # ------

    def exportCallback(self, sender):
        # gather unsaved documents
        unsavedChanges = []
        docController = AppKit.NSDocumentController.sharedDocumentController()
        if docController.hasEditedDocuments():
            for document in docController.documents():
                if document.isDocumentEdited():
                    url = document.fileURL()
                    path = url.path()
                    unsavedChanges.append(path)
        # gather paths
        invalidPaths = []
        validPaths = []
        for d in self.w.fontList:
            path = d["path"]
            if not os.path.exists(path):
                invalidPaths.append(("File does not exist", path))
                continue
            if path in unsavedChanges:
                invalidPaths.append(("Font has unsaved changes", path))
                continue
            validPaths.append(path)
        # export
        if validPaths:
            bundle = AppKit.NSBundle.mainBundle()
            info = bundle.infoDictionary()
            version = info["CFBundleVersion"]
            settings = self.w.exportSettings.get()
            mode = settings["mode"]
            destination = settings["destination"]
            subtableBreaks = settings["subtable"]
            overwrite = self.w.overwriteExistingCheckBox.get()
            progress = self.startProgress(text="Exporting...", tickCount=len(validPaths))
            # AFM
            if mode == "afm":
                for path in validPaths:
                    font = OpenFont(path, showInterface=False)
                    d = os.path.dirname(path)
                    b = os.path.splitext(os.path.basename(path))[0]
                    if overwrite:
                        path = makeFileName(directory=d, baseName=b, extension="afm")
                    else:
                        path = findAvailableFileName(directory=d, baseName=b, extension="afm")
                    font.naked().kerning.metricsMachine.exportKerningToAFMFile(path, glyphs=font.keys(), appVersion=version)
                    del font
                    progress.update()
            # feature
            else:
                for path in validPaths:
                    # into font
                    if destination == "ufo":
                        font = OpenFont(path, showInterface=False).naked()
                        font.kerning.metricsMachine.exportKerningToFeatureFile(None, appVersion=version, subtableBreaks=subtableBreaks)
                        formatVersion = font.ufoFormatVersion
                        font.info.dirty = False
                        font.groups.dirty = False
                        font.kerning.dirty = False
                        if formatVersion == 2:
                            font.lib.dirty = False
                        font.save()
                        del font
                    # external file
                    else:
                        font = OpenFont(path, showInterface=False).naked()
                        d = os.path.dirname(path)
                        b = os.path.splitext(os.path.basename(path))[0]
                        b = "%s kern" % b
                        if overwrite:
                            path = makeFileName(directory=d, baseName=b, extension="fea")
                        else:
                            path = findAvailableFileName(directory=d, baseName=b, extension="fea")
                        font.kerning.metricsMachine.exportKerningToFeatureFile(path, appVersion=version, subtableBreaks=subtableBreaks)
                        del font
                    progress.update()
            progress.close()
        # report
        if invalidPaths:
            if len(invalidPaths) > 1:
                messageText = "Could not export for all fonts."
            else:
                messageText = "Could not export kerning for a font."
            informativeText = []
            for reason, path in sorted(invalidPaths):
                t = "%s: %s" % (reason, os.path.basename(path))
                informativeText.append(t)
            informativeText = "\n".join(informativeText)
            self.showMessage(messageText=messageText, informativeText=informativeText)


def makeFileName(directory, baseName, extension, counter=None):
    if counter:
        b = "%s %d.%s" % (baseName, counter, extension)
    else:
        b = "%s.%s" % (baseName, extension)
    return os.path.join(directory, b)

def findAvailableFileName(directory, baseName, extension, counter=0):
    # add number
    if counter:
        fileName = makeFileName(directory, baseName, extension, counter)
    # no number
    else:
        fileName = makeFileName(directory, baseName, extension)
    # recurse if necessary
    if os.path.exists(fileName):
        fileName = findAvailableFileName(directory, baseName, extension, counter+1)
    # done
    return fileName
