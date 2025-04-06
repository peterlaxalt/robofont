import AppKit
import vanilla


_modifierMap = {
    "command": AppKit.NSCommandKeyMask,
    "control": AppKit.NSControlKeyMask,
    "option": AppKit.NSAlternateKeyMask,
    "shift": AppKit.NSShiftKeyMask,
    "capslock": AppKit.NSAlphaShiftKeyMask,
}

_keyMap = {
    "help": AppKit.NSHelpFunctionKey,
    "home": AppKit.NSHomeFunctionKey,
    "end": AppKit.NSEndFunctionKey,
    "pageup": AppKit.NSPageUpFunctionKey,
    "pagedown": AppKit.NSPageDownFunctionKey,
    "forwarddelete": AppKit.NSDeleteFunctionKey,
    "leftarrow": AppKit.NSLeftArrowFunctionKey,
    "rightarrow": AppKit.NSRightArrowFunctionKey,
    "uparrow": AppKit.NSUpArrowFunctionKey,
    "downarrow": AppKit.NSDownArrowFunctionKey,
    "return": "\r",
    "hardreturn": "\n"
}


_stringKeyMap = {
    "home": chr(0x2196),
    "end": chr(0x2198),
    "pageup": chr(0x21DE),
    "pagedown": chr(0x21DF),
    "forwarddelete": chr(0x232B),
    "leftarrow": chr(0x2190),
    "rightarrow": chr(0x2192),
    "uparrow": chr(0x2191),
    "downarrow": chr(0x2193),
    "return": chr(0x21A9),
    "hardreturn": chr(0x2324),
    "command": chr(0x2318),
    "control": chr(0x2303),
    "option": chr(0x2325),
    "shift": chr(0x21E7),
    "capslock": chr(0x21EA),
}


def _setOrNone(value):
    if value is None:
        return set()
    return set(value)


def _noneSorting(value):
    key, modifiers, callback = value
    if modifiers is None:
        modifiers = set()
    return key, modifiers, callback


_specialCases = [
    ("w", set(["command"])),  # close window, dont subscribe afterwards
    ("`", set(["command"])),  # jump to next window, dont subscribe afterwards
    ("`", set(["command", "shift"])),  # jump to prev window, dont subscribe afterwards
]


class ShortCutInfoSheet(object):

    def __init__(self, shortcuts):
        self.w = vanilla.Sheet((400, 400), minSize=(400, 200), parentWindow=AppKit.NSApp().mainWindow())
        text = "\n"
        for char, modifiers, _, info in shortcuts:
            if info is None:
                continue
            text += "\t"
            if modifiers:
                for modifier in modifiers:
                    text += _stringKeyMap.get(modifier, "")
            text += _stringKeyMap.get(char, char.upper())
            text += "\t"
            text += info
            text += "\n"
        para = AppKit.NSMutableParagraphStyle.alloc().init()
        for tabStop in para.tabStops():
            para.removeTabStop_(tabStop)
        tabStop = AppKit.NSTextTab.alloc().initWithTextAlignment_location_options_(AppKit.NSRightTextAlignment, 60, {})
        para.addTabStop_(tabStop)
        tabStop = AppKit.NSTextTab.alloc().initWithTextAlignment_location_options_(AppKit.NSLeftTextAlignment, 75, {})
        para.addTabStop_(tabStop)
        para.setMaximumLineHeight_(20)
        para.setMinimumLineHeight_(20)
        attr = {
            AppKit.NSParagraphStyleAttributeName: para
        }
        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, attr)
        self.w.shortCuts = vanilla.TextEditor((0, 0, -0, -40), readOnly=True)
        self.w.shortCuts.getNSTextView().textStorage().setAttributedString_(text)
        self.w.shortCuts.getNSScrollView().setBorderType_(AppKit.NSNoBorder)

        self.w.shortCuts.getNSTextView().setDrawsBackground_(False)
        self.w.shortCuts.getNSScrollView().setDrawsBackground_(False)
        self.w.shortCuts.getNSTextView().setBackgroundColor_(AppKit.NSColor.clearColor())

        self.w.closeButton = vanilla.Button((-80, -30, -10, 22), "OK", callback=self.closeCallback)
        self.w.closeButton.bind(".", ["command"])
        self.w.closeButton.bind(chr(27), [])

        self.w.open()

    def closeCallback(self, sender):
        self.w.close()


class KeyEventMonitor(object):

    def __init__(self, shortCuts):
        self.monitor = None
        self._originalShortCuts = shortCuts
        self.shortCuts = [(_keyMap.get(k, k), _setOrNone(m), c) for k, m, c, i in shortCuts]
        self.shortCuts.append(("i", set(["command"]), self.showShortCutsInfo))
        self.shortCuts.sort(key=_noneSorting)
        self.shortCuts.reverse()

    def subscribe(self):
        self.unsubscribe()
        self.monitor = AppKit.NSEvent.addLocalMonitorForEventsMatchingMask_handler_(AppKit.NSKeyDownMask, self.eventHandler)

    def unsubscribe(self):
        if self.monitor is not None:
            AppKit.NSEvent.removeMonitor_(self.monitor)
        self.monitor = None

    def eventHandler(self, event):
        inputKey = event.charactersIgnoringModifiers()
        eventModifiers = event.modifierFlags()
        inputModifiers = set()
        for modifiersName, modifier in _modifierMap.items():
            if modifier & eventModifiers:
                inputModifiers.add(modifiersName)
        if not inputModifiers:
            inputModifiers = None
        foundCallback = None
        for key, modifiers, callback in self.shortCuts:
            if key == inputKey and modifiers == inputModifiers:
                foundCallback = callback
                break
        if foundCallback is None:
            self.unsubscribe()
            orderedWindows = AppKit.NSApp().orderedWindows()
            AppKit.NSApp().sendEvent_(event)
            if orderedWindows == AppKit.NSApp().orderedWindows():
                if (inputKey, inputModifiers) not in _specialCases:
                    self.subscribe()
        else:
            foundCallback(event)

    def showShortCutsInfo(self, sender):
        ShortCutInfoSheet(self._originalShortCuts)
