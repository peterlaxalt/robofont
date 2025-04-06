import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController


class AutoGroupsSheet(BaseWindowController):

    def __init__(self, font, callback, parentWindow):
        suffixes = font.metricsMachine.mutableGroups.metricsMachine.getSuffixesAvailableForAutoGroups()
        suffixes = sorted(suffixes)
        self.callback = callback

        w = 210
        self.w = vanilla.Sheet((w, 300), parentWindow=parentWindow, minSize=(w, 200), maxSize=(w, 10000))

        self.w.followDecompositionCheckBox = vanilla.CheckBox((15, 15, -15, 22), "Use decomposition rules")

        self.w.suffixTitle = vanilla.TextBox((15, 43, -15, 34), "Match base grouping for the selected suffixes:")
        self.w.suffixList = vanilla.List((15, 83, -15, -65), suffixes, drawFocusRing=False)

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self.setUpBaseWindowBehavior()
        self.w.open()

    def cancelCallback(self, sender):
        self.w.close()

    def applyCallback(self, sender):
        followDecomposition = self.w.followDecompositionCheckBox.get()
        suffixList = self.w.suffixList
        suffixes = [suffixList[i] for i in suffixList.getSelection()]
        self.w.close()
        self.callback(followDecomposition=followDecomposition, suffixesToFollowBase=suffixes)
