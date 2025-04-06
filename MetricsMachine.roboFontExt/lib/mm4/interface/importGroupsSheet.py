import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController
from mm4.objects.mmGroups import bracketedUserFriendlyGroupName


class ImportGroupsSheet(BaseWindowController):

    def __init__(self, groupNames, parentWindow, callback, path, truncateGroupNames=True):
        self._callback = callback
        self._path = path

        self.groupNames = sorted(groupNames)
        if truncateGroupNames:
            userGroups = [bracketedUserFriendlyGroupName(name) for name in self.groupNames]
        else:
            userGroups = self.groupNames

        w = 240
        self.w = vanilla.Sheet((w, 300), parentWindow=parentWindow, minSize=(w, 200), maxSize=(w, 10000))

        self.w.clearExistingCheckBox = vanilla.CheckBox((15, 15, -15, 22), "Clear existing groups")

        t = "Please select the groups you want to import."
        self.w.title = vanilla.TextBox((15, 43, -15, 34), t)

        self.w.list = vanilla.List((15, 83, -15, -65), userGroups, drawFocusRing=False)

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self.setUpBaseWindowBehavior()
        self.w.open()

    def _finalize(self):
        self._callback = None

    def cancelCallback(self, sender):
        self.w.close()
        self._finalize()

    def applyCallback(self, sender):
        self.w.close()
        clearExisting = self.w.clearExistingCheckBox.get()
        groupNames = [self.groupNames[index] for index in self.w.list.getSelection()]
        self._callback(groupNames, clearExisting, self._path)
        self._finalize()
