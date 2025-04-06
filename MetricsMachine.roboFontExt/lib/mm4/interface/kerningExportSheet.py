
import vanilla
from defconAppKit.windows.baseWindow import BaseWindowController


class KerningExportSettingsSheet(BaseWindowController):

    def __init__(self, parentWindow, callback):
        self.callback = callback

        self.w = vanilla.Sheet((190, 200), parentWindow=parentWindow)
        self.w.settings = KerningExportSettingsView((15, 15, -15, 125), self.modeCallback)

        self.w.bottomLine = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((15, -35, 75, 20), "Cancel", callback=self.cancelCallback)
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])
        self.w.okButton = vanilla.Button((-90, -35, 75, 20), "OK", callback=self.okCallback)
        self.w.setDefaultButton(self.w.okButton)

        self.w.open()

    def cancelCallback(self, sender):
        self.callback = None
        self.w.close()

    def okCallback(self, sender):
        self.w.close()
        self.callback(self.w.settings.get())
        self.callback = None

    def modeCallback(self, sender):
        mode = sender.get()["mode"]
        adjustment = 100
        x, y, w, h = self.w.getPosSize()
        if mode == "afm":
            h -= adjustment
        else:
            h += adjustment
        self.w.setPosSize((x, y, w, h))


class KerningExportSettingsView(vanilla.Group):

    def __init__(self, posSize, callback):
        self.callback = callback
        super(KerningExportSettingsView, self).__init__(posSize)
        self.mode = 0
        self.modePopUp = vanilla.PopUpButton((0, 0, -0, 20), ["Feature File", "AFM"], callback=self.modeCallback)
        self.line1 = vanilla.HorizontalLine((0, 35, -0, 1))
        self.subtableCheckBox = vanilla.CheckBox((0, 45, 160, 20), "Insert subtable breaks")
        self.line2 = vanilla.HorizontalLine((0, 75, -0, 1))
        self.destinationRadioGroup = vanilla.RadioGroup((0, 85, 160, 40), ["Write external file", "Insert into font"])
        self.destinationRadioGroup.set(0)

    def _breakCycles(self):
        self.callback = None
        super(KerningExportSettingsView, self)._breakCycles()

    def modeCallback(self, sender):
        mode = sender.get()
        if mode == self.mode:
            return
        self.mode = mode
        showFeaOptions = mode == 0
        self.subtableCheckBox.show(showFeaOptions)
        self.destinationRadioGroup.show(showFeaOptions)
        self.line1.show(showFeaOptions)
        self.line2.show(showFeaOptions)
        self.callback(self)

    def get(self):
        mode = ["feature", "afm"][self.modePopUp.get()]
        subtable = self.subtableCheckBox.get()
        destination = ["external", "ufo"][self.destinationRadioGroup.get()]
        return dict(mode=mode, subtable=subtable, destination=destination)
