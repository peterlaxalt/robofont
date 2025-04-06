import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController
from mm4.objects.mmGroups import userFriendlyGroupName


class CopyGroupsSheet(BaseWindowController):

    def __init__(self, font, leftToRight, parentWindow):
        self.font = font

        if not leftToRight:
            i = "side 2"
            j = "side 1"
            groups = font.metricsMachine.mutableGroups.metricsMachine.getSide2Groups()
        else:
            groups = font.metricsMachine.mutableGroups.metricsMachine.getSide1Groups()
            i = "side 1"
            j = "side 2"

        self.groupNames = sorted(groups)
        userGroups = [userFriendlyGroupName(name) for name in self.groupNames]

        w = 240
        self.w = vanilla.Sheet((w, 300), parentWindow=parentWindow, minSize=(w, 200), maxSize=(w, 10000))

        t = "Select the '%s' groups you want to copy to the '%s' groups." % (i, j)
        self.w.title = vanilla.TextBox((15, 15, -15, 34), t)

        self.w.list = vanilla.List((15, 60, -15, -65), userGroups, drawFocusRing=False)

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((-165, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.applyButton = vanilla.Button((-85, -35, 70, 20), "Apply", callback=self.applyCallback)

        self.setUpBaseWindowBehavior()
        self.w.open()

    def cancelCallback(self, sender):
        self.w.close()

    def applyCallback(self, sender):
        groups = [self.groupNames[index] for index in self.w.list.getSelection()]
        if groups:
            self.font.metricsMachine.mutableGroups.metricsMachine.copyAndFlipGroups(groups)
        self.w.close()
