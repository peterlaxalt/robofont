import weakref
import AppKit
import vanilla

from mojo.extensions import getExtensionDefault, setExtensionDefault

defaultRule = dict(type="glyphName", comparison="is", value="")
defaultContext = dict(
    name="New Context",
    enabled=True,
    longContext=["$LEFT", "$RIGHT"],
    shortContext=["$LEFT", "$RIGHT"],
    suffixMatching=False,
    pseudoUnicodes=False,
    leftPattern=dict(
        matches="any",
        rules=[dict(defaultRule)]
    ),
    rightPattern=dict(
        matches="any",
        rules=[dict(defaultRule)]
    )
)


class ContextPrefsView(vanilla.Group):

    def __init__(self, posSize, windowController, defaultWindowHeight):
        self._loadContextsFromDefaults()
        self.defaultWindowHeight = defaultWindowHeight
        self.windowController = weakref.ref(windowController)

        super(ContextPrefsView, self).__init__(posSize)

        columnDescriptions = [
            dict(title="Name", key="name", width=200),
            dict(title="Long Context", key="longContext", formatter=ContextFormatter.alloc().init(), width=250),
            dict(title="Short Context", key="shortContext", formatter=ContextFormatter.alloc().init()),
        ]
        dropSettings = dict(callback=self.dropContextCallback, type="ContextPrefsItemPboardType", operation=AppKit.NSDragOperationMove)
        dragSettings = dict(callback=self.dragContextCallback, type="ContextPrefsItemPboardType")
        self.contextList = ContextList((15, 15, -15, 150), self._data, columnDescriptions=columnDescriptions,
            allowsMultipleSelection=False, selectionCallback=self.stringSelection,
            dragSettings=dragSettings, selfDropSettings=dropSettings)
        tableView = self.contextList.getNSTableView()
        tableView.setAllowsColumnReordering_(False)
        tableView.setAllowsColumnSelection_(False)

        self.addContextButton = vanilla.Button((15, 172, 90, 20), "Add", callback=self.addContextCallback)
        self.removeContextButton = vanilla.Button((110, 172, 90, 20), "Remove", callback=self.removeContextCallback)
        self.duplicateContextButton = vanilla.Button((205, 172, 90, 20), "Duplicate", callback=self.duplicateContextCallback)
        self.importContextButton = vanilla.Button((-200, 172, 90, 20), "Import", callback=self.importCallback)
        self.exportContextButton = vanilla.Button((-105, 172, 90, 20), "Export", callback=self.exportCallback)

        self.line = vanilla.HorizontalLine((15, 202, -15, 1))

        self.nameTitle = vanilla.TextBox((15, 217, 100, 17), "Name:", alignment="right")
        self.nameField = vanilla.EditText((120, 215, -170, 22), callback=self.dataChangedCallback)
        self.longContextTitle = vanilla.TextBox((15, 247, 100, 17), "Long Context:", alignment="right")
        self.longContextField = vanilla.EditText((120, 245, -170, 22), formatter=ContextFormatter.alloc().init(), callback=self.dataChangedCallback)
        self.shortContextTitle = vanilla.TextBox((15, 277, 100, 17), "Short Context:", alignment="right")
        self.shortContextField = vanilla.EditText((120, 275, -170, 22), formatter=ContextFormatter.alloc().init(), callback=self.dataChangedCallback)

        self.enabled = vanilla.CheckBox((-150, 215, -15, 22), "Enabled", callback=self.dataChangedCallback)
        self.suffixMatching = vanilla.CheckBox((-150, 245, -15, 22), "Suffix Matching", callback=self.dataChangedCallback)
        self.pseudoUnicodes = vanilla.CheckBox((-150, 275, -15, 22), "Pseudo Unicodes", callback=self.dataChangedCallback)

        self.patternTabs = vanilla.Tabs((15, 317, -15, -15), ["Left", "Right"], callback=self.patternTabSelection)
        self.patternTabs[0].patternGroup = PatternGroup()
        self.patternTabs[1].patternGroup = PatternGroup()

        self.stringSelection(self.contextList)

    def _breakCycles(self):
        self.windowController = None
        super(ContextPrefsView, self)._breakCycles()

    # -------
    # loading
    # -------

    def reload(self):
        self._loadContextsFromDefaults()
        self.contextList.set(self._data)

    def _loadContextsFromDefaults(self):
        contexts = getExtensionDefault("com.typesupply.MM4.contextStrings")
        mutable = []
        for context in contexts:
            d = self._makeMutableContext(context)
            mutable.append(d)
        self._data = mutable

    def _makeMutableContext(self, context):
        d = AppKit.NSMutableDictionary.dictionary()
        d["name"] = context["name"]
        d["longContext"] = context["longContext"]
        d["shortContext"] = context["shortContext"]
        d["pseudoUnicodes"] = context["pseudoUnicodes"]
        d["suffixMatching"] = context["suffixMatching"]
        d["enabled"] = context["enabled"]
        d["leftPattern"] = AppKit.NSMutableDictionary.dictionary()
        d["leftPattern"]["matches"] = context["leftPattern"]["matches"]
        d["leftPattern"]["rules"] = self._makeMutableRules(context["leftPattern"]["rules"])
        d["rightPattern"] = AppKit.NSMutableDictionary.dictionary()
        d["rightPattern"]["matches"] = context["rightPattern"]["matches"]
        d["rightPattern"]["rules"] = self._makeMutableRules(context["rightPattern"]["rules"])
        return d

    def _makeMutableRules(self, rules):
        a = AppKit.NSMutableArray.array()
        for rule in rules:
            d = AppKit.NSMutableDictionary.dictionaryWithDictionary_(rule)
            a.append(d)
        return a

    # ------
    # saving
    # ------

    def _writeContextsToDefaults(self):
        setExtensionDefault("com.typesupply.MM4.contextStrings", self._data)
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.postNotificationName_object_("MM4.MMContextStringsChanged", None)

    # ---------
    # selection
    # ---------

    def stringSelection(self, sender):
        selection = sender.getSelection()
        if not selection:
            self.nameField.set("")
            self.nameField.enable(False)
            self.longContextField.set("")
            self.longContextField.enable(False)
            self.shortContextField.set("")
            self.shortContextField.enable(False)
            self.enabled.set(False)
            self.enabled.enable(False)
            self.suffixMatching.set(False)
            self.suffixMatching.enable(False)
            self.pseudoUnicodes.set(False)
            self.pseudoUnicodes.enable(False)
            self._setPatterns(None, None)
        else:
            index = selection[0]
            item = sender[index]
            self.nameField.set(item["name"])
            self.nameField.enable(True)
            self.longContextField.set(item["longContext"])
            self.longContextField.enable(True)
            self.shortContextField.set(item["shortContext"])
            self.shortContextField.enable(True)
            self.enabled.set(item["enabled"])
            self.enabled.enable(True)
            self.suffixMatching.set(item["suffixMatching"])
            self.suffixMatching.enable(True)
            self.pseudoUnicodes.set(item["pseudoUnicodes"])
            self.pseudoUnicodes.enable(True)
            self._setPatterns(item["leftPattern"], item["rightPattern"])

    # -------
    # editing
    # -------

    def dragContextCallback(self, sender, indexes):
        return indexes

    def dropContextCallback(self, sender, dropInfo):
        isProposal = dropInfo["isProposal"]
        indexes = [int(i) for i in sorted(dropInfo["data"])]
        if len(indexes) != 1:
            return False
        if not isProposal:
            index = indexes[0]
            rowIndex = dropInfo["rowIndex"]
            item = self._data.pop(index)
            if rowIndex > index:
                newIndex = rowIndex - 1
            else:
                newIndex = rowIndex
            self._data.insert(newIndex, item)
            self.contextList.set(self._data)
            self._writeContextsToDefaults()
        return True

    def dataChangedCallback(self, sender):
        index = self.contextList.getSelection()[0]
        item = self.contextList[index]
        item["name"] = self.nameField.get()
        item["longContext"] = self.longContextField.get()
        item["shortContext"] = self.shortContextField.get()
        item["enabled"] = bool(self.enabled.get())
        item["suffixMatching"] = bool(self.suffixMatching.get())
        item["pseudoUnicodes"] = bool(self.pseudoUnicodes.get())
        self._writeContextsToDefaults()

    def addContextCallback(self, sender):
        self._data.append(self._makeMutableContext(defaultContext))
        self.contextList.set(self._data)
        self.contextList.setSelection([len(self._data) - 1])
        self._writeContextsToDefaults()

    def removeContextCallback(self, sender):
        index = self.contextList.getSelection()[0]
        del self._data[index]
        self.contextList.set(self._data)
        self._writeContextsToDefaults()

    def duplicateContextCallback(self, sender):
        index = self.contextList.getSelection()[0]
        item = self.contextList[index]
        item = self._makeMutableContext(item)
        item["name"] += " Copy"
        index += 1
        self._data.insert(index, item)
        self.contextList.set(self._data)
        self.contextList.setSelection([index])
        self._writeContextsToDefaults()

    # -------------
    # pattern group
    # -------------

    def patternTabSelection(self, sender):
        self._resizeWindow()

    def _setPatterns(self, left, right):
        self.patternTabs[0].patternGroup.set(left)
        self.patternTabs[1].patternGroup.set(right)
        self._resizeWindow()

    def _resizeWindow(self):
        visibleIndex = self.patternTabs.get()
        visibleTab = self.patternTabs[visibleIndex]
        group = getattr(visibleTab, "patternGroup")
        height = self.defaultWindowHeight + group.getRequiredHeight()
        self.windowController().contextsRequireResize(height)

    def patternChanged(self):
        self._writeContextsToDefaults()
        self._resizeWindow()

    # -------------
    # import/export
    # -------------

    def exportCallback(self, sender):
        self.windowController().exportContexts()

    def importCallback(self, sender):
        self.windowController().importContexts()


class PatternGroup(vanilla.Group):

    def __init__(self):
        super(PatternGroup, self).__init__((10, 10, -10, -10))
        self.ifTitle = vanilla.TextBox((0, 2, 15, 17), "If")
        self.matchPopup = vanilla.PopUpButton((20, 0, 60, 20), ["any", "all"], callback=self.anyAllCallback)
        self.conditionsTitle = vanilla.TextBox((85, 2, -0, 17), "of the following conditions are met:")
        self.line = vanilla.HorizontalLine((0, 35, -0, 1))

        self.pattern = None
        self._ruleAttributes = []
        self._ruleViews = []

    def _breakCycles(self):
        self._ruleViews = []
        super(PatternGroup, self)._breakCycles()

    def _changed(self):
        tab = self.getNSView().superview()
        tabView = tab.superview()
        groupView = tabView.superview().vanillaWrapper()
        groupView.patternChanged()

    # --------------
    # rule callbacks
    # --------------

    def anyAllCallback(self, sender):
        if sender.get() == 0:
            value = "any"
        else:
            value = "all"
        self.pattern["matches"] = value
        self._changed()

    def addRuleAfter(self, rule):
        index = self._ruleViews.index(rule) + 1
        count = len(self._ruleAttributes)
        attr = "ruleView%d" % count
        top = 45 + ((index - 1) * 35)
        rule = AppKit.NSMutableDictionary.dictionaryWithDictionary_(defaultRule)
        view = RuleView((0, top, -0, 35), bool(index))
        view.set(rule)
        setattr(self, attr, view)
        self._ruleAttributes.insert(index, attr)
        self._ruleViews.insert(index, view)
        self.pattern["rules"].insert(index, rule)
        for rule in self._ruleViews[index:]:
            x, y, w, h = rule.getPosSize()
            y += 35
            rule.setPosSize((x, y, w, h))
        self._changed()

    def removeRule(self, rule):
        index = self._ruleViews.index(rule)
        attr = self._ruleAttributes[index]
        delattr(self, attr)
        del self._ruleAttributes[index]
        del self._ruleViews[index]
        del self.pattern["rules"][index]
        for rule in self._ruleViews[index:]:
            x, y, w, h = rule.getPosSize()
            y -= 35
            rule.setPosSize((x, y, w, h))
        self._changed()

    def ruleChanged(self, rule):
        index = self._ruleViews.index(rule)
        self.pattern["rules"][index].update(rule.get())
        self._changed()

    # -----------------
    # data input/output
    # -----------------

    def set(self, pattern):
        self.pattern = pattern
        if not pattern:
            self.setPosSize((10, 10, -10, -10))
            self.ifTitle.show(False)
            self.matchPopup.show(False)
            self.conditionsTitle.show(False)
            self.line.show(False)
            for name in self._ruleAttributes:
                delattr(self, name)
            self._ruleAttributes = []
            self._ruleViews = []
            return
        # tear down old views
        for name in self._ruleAttributes:
            delattr(self, name)
            self._ruleAttributes = []
            self._ruleViews = []
        # add new views
        self.ifTitle.show(True)
        self.matchPopup.show(True)
        self.conditionsTitle.show(True)
        self.line.show(True)
        self.matchPopup.set(["any", "all"].index(pattern["matches"]))
        for index, rule in enumerate(pattern["rules"]):
            count = len(self._ruleAttributes)
            attr = "ruleView%d" % count
            top = 45 + (count * 35)
            view = RuleView((0, top, -0, 35), bool(index))
            view.set(rule)
            setattr(self, attr, view)
            self._ruleAttributes.append(attr)
            self._ruleViews.append(view)

    def getRequiredHeight(self):
        if not self.pattern:
            return 0
        return 45 + (len(self._ruleAttributes) * 35)


nameComparisons = [
    ("is", "is"),
    ("isNot", "is not"),
    ("contains", "contains"),
    ("doesNotContain", "does not contain"),
    ("startsWith", "begins with"),
    ("doesNotStartWith", "does not begin with"),
    ("endsWith", "ends with"),
    ("doesNotEndWith", "does not end with"),
    ("matchesPattern", "matches pattern"),
    ("doesNotMatchPattern", "does not match pattern")
]

unicodeValueComparisons = [
    ("is", "is"),
    ("isNot", "is not"),
    ("isInRange", "is in the range"),
    ("isNotInRange", "is not in the range")
]

unicodeCategoryComparisons = [
    ("is", "is"),
    ("isNot", "is not")
]

unicodeScriptComparisons = [
    ("is", "is"),
    ("isNot", "is not")
]

unicodeBlockComparisons = [
    ("is", "is"),
    ("isNot", "is not")
]

unicodeCategoryValues = [
    ("Lu", "Letter, Uppercase"),
    ("Ll", "Letter, Lowercase"),
    ("Lt", "Letter, Titlecase"),
    ("Lm", "Letter, Modifier"),
    ("Lo", "Letter, Other"),
    ("Mn", "Mark, Nonspacing"),
    ("Mc", "Mark, Spacing Combining"),
    ("Me", "Mark, Enclosing"),
    ("Nd", "Number, Decimal Digit"),
    ("Nl", "Number, Letter"),
    ("No", "Number, Other"),
    ("Pc", "Punctuation, Connector"),
    ("Pd", "Punctuation, Dash"),
    ("Ps", "Punctuation, Open"),
    ("Pe", "Punctuation, Close"),
    ("Pi", "Punctuation, Initial quote"),
    ("Pf", "Punctuation, Final quote"),
    ("Po", "Punctuation, Other"),
    ("Sm", "Symbol, Math"),
    ("Sc", "Symbol, Currency"),
    ("Sk", "Symbol, Modifier"),
    ("So", "Symbol, Other"),
    ("Zs", "Separator, Space"),
    ("Zl", "Separator, Line"),
    ("Zp", "Separator, Paragraph"),
    ("Cc", "Other, Control"),
    ("Cf", "Other, Format"),
    ("Cs", "Other, Surrogate"),
    ("Co", "Other, Private Use"),
    ("Cn", "Other, Not Assigned"),
]

unicodeScriptValues = [
    "Arabic",
    "Armenian",
    "Balinese",
    "Bengali",
    "Bopomofo",
    "Braille",
    "Buginese",
    "Buhid",
    "Canadian_Aboriginal",
    "Cherokee",
    "Common",
    "Coptic",
    "Cuneiform",
    "Cypriot",
    "Cyrillic",
    "Deseret",
    "Devanagari",
    "Ethiopic",
    "Georgian",
    "Glagolitic",
    "Gothic",
    "Greek",
    "Gujarati",
    "Gurmukhi",
    "Han",
    "Hangul",
    "Hanunoo",
    "Hebrew",
    "Hiragana",
    "Inherited",
    "Kannada",
    "Katakana",
    "Kharoshthi",
    "Khmer",
    "Lao",
    "Latin",
    "Limbu",
    "Linear_B",
    "Malayalam",
    "Mongolian",
    "Myanmar",
    "New_Tai_Lue",
    "Nko",
    "Ogham",
    "Old_Italic",
    "Old_Persian",
    "Oriya",
    "Osmanya",
    "Phags_Pa",
    "Phoenician",
    "Runic",
    "Shavian",
    "Sinhala",
    "Syloti_Nagri",
    "Syriac",
    "Tagalog",
    "Tagbanwa",
    "Tai_Le",
    "Tamil",
    "Telugu",
    "Thaana",
    "Thai",
    "Tibetan",
    "Tifinagh",
    "Ugaritic",
    "Yi"
]

unicodeBlockValues = [
    "Aegean Numbers",
    "Alphabetic Presentation Forms",
    "Ancient Greek Musical Notation",
    "Ancient Greek Numbers",
    "Arabic",
    "Arabic Presentation Forms-A",
    "Arabic Presentation Forms-B",
    "Arabic Supplement",
    "Armenian",
    "Arrows",
    "Balinese",
    "Basic Latin",
    "Bengali",
    "Block Elements",
    "Bopomofo",
    "Bopomofo Extended",
    "Box Drawing",
    "Braille Patterns",
    "Buginese",
    "Buhid",
    "Byzantine Musical Symbols",
    "CJK Compatibility",
    "CJK Compatibility Forms",
    "CJK Compatibility Ideographs",
    "CJK Compatibility Ideographs Supplement",
    "CJK Radicals Supplement",
    "CJK Strokes",
    "CJK Symbols and Punctuation",
    "CJK Unified Ideographs",
    "CJK Unified Ideographs Extension A",
    "CJK Unified Ideographs Extension B",
    "Cherokee",
    "Combining Diacritical Marks",
    "Combining Diacritical Marks Supplement",
    "Combining Diacritical Marks for Symbols",
    "Combining Half Marks",
    "Control Pictures",
    "Coptic",
    "Counting Rod Numerals",
    "Cuneiform",
    "Cuneiform Numbers and Punctuation",
    "Currency Symbols",
    "Cypriot Syllabary",
    "Cyrillic",
    "Cyrillic Supplement",
    "Deseret",
    "Devanagari",
    "Dingbats",
    "Enclosed Alphanumerics",
    "Enclosed CJK Letters and Months",
    "Ethiopic",
    "Ethiopic Extended",
    "Ethiopic Supplement",
    "General Punctuation",
    "Geometric Shapes",
    "Georgian",
    "Georgian Supplement",
    "Glagolitic",
    "Gothic",
    "Greek Extended",
    "Greek and Coptic",
    "Gujarati",
    "Gurmukhi",
    "Halfwidth and Fullwidth Forms",
    "Hangul Compatibility Jamo",
    "Hangul Jamo",
    "Hangul Syllables",
    "Hanunoo",
    "Hebrew",
    "High Private Use Surrogates",
    "High Surrogates",
    "Hiragana",
    "IPA Extensions",
    "Ideographic Description Characters",
    "Kanbun",
    "Kangxi Radicals",
    "Kannada",
    "Katakana",
    "Katakana Phonetic Extensions",
    "Kharoshthi",
    "Khmer",
    "Khmer Symbols",
    "Lao",
    "Latin Extended Additional",
    "Latin Extended-A",
    "Latin Extended-B",
    "Latin Extended-C",
    "Latin Extended-D",
    "Latin-1 Supplement",
    "Letterlike Symbols",
    "Limbu",
    "Linear B Ideograms",
    "Linear B Syllabary",
    "Low Surrogates",
    "Malayalam",
    "Mathematical Alphanumeric Symbols",
    "Mathematical Operators",
    "Miscellaneous Mathematical Symbols-A",
    "Miscellaneous Mathematical Symbols-B",
    "Miscellaneous Symbols",
    "Miscellaneous Symbols and Arrows",
    "Miscellaneous Technical",
    "Modifier Tone Letters",
    "Mongolian",
    "Musical Symbols",
    "Myanmar",
    "NKo",
    "New Tai Lue",
    "Number Forms",
    "Ogham",
    "Old Italic",
    "Old Persian",
    "Optical Character Recognition",
    "Oriya",
    "Osmanya",
    "Phags-pa",
    "Phoenician",
    "Phonetic Extensions",
    "Phonetic Extensions Supplement",
    "Private Use Area",
    "Runic",
    "Shavian",
    "Sinhala",
    "Small Form Variants",
    "Spacing Modifier Letters",
    "Specials",
    "Superscripts and Subscripts",
    "Supplemental Arrows-A",
    "Supplemental Arrows-B",
    "Supplemental Mathematical Operators",
    "Supplemental Punctuation",
    "Supplementary Private Use Area-A",
    "Supplementary Private Use Area-B",
    "Syloti Nagri",
    "Syriac",
    "Tagalog",
    "Tagbanwa",
    "Tags",
    "Tai Le",
    "Tai Xuan Jing Symbols",
    "Tamil",
    "Telugu",
    "Thaana",
    "Thai",
    "Tibetan",
    "Tifinagh",
    "Ugaritic",
    "Unified Canadian Aboriginal Syllabics",
    "Variation Selectors",
    "Variation Selectors Supplement",
    "Vertical Forms",
    "Yi Radicals",
    "Yi Syllables",
    "Yijing Hexagram Symbols"
]


_ruleViewControls = {
    "anything": [],
    "glyphName": [
        ("nameComparisons", "PopUpButton", (160, 10, 180, 20), [name for tag, name in nameComparisons], "nameComparisonsCallback"),
        ("textEntryField", "EditText", (350, 9, 189, 22), None, "valueCallback")
    ],
    "unicodeValue": [
        ("unicodeValueComparisons", "PopUpButton", (160, 10, 180, 20), [name for tag, name in unicodeValueComparisons], "unicodeValueComparisonsCallback"),
        ("textEntryField", "EditText", (350, 9, 189, 22), None, "valueCallback"),
        ("fromTitle", "TextBox", (435, 11, 20, 17), "to", None),
        ("rangeFieldMin", "EditText", (350, 9, 80, 22), None, "valueCallback"),
        ("rangeFieldMax", "EditText", (459, 9, 80, 22), None, "valueCallback")
    ],
    "unicodeCategory": [
        ("unicodeCategoryComparisons", "PopUpButton", (160, 10, 180, 20), [name for tag, name in unicodeCategoryComparisons], "unicodeCategoryComparisonsCallback"),
        ("unicodeCategoryValues", "PopUpButton", (350, 10, 189, 20), [name for tag, name in unicodeCategoryValues], "valueCallback")
    ],
    "unicodeScript": [
        ("unicodeScriptComparisons", "PopUpButton", (160, 10, 180, 20), [name for tag, name in unicodeScriptComparisons], "unicodeScriptComparisonsCallback"),
        ("unicodeScriptValues", "PopUpButton", (350, 10, 189, 20), [name.replace("_", " ") for name in unicodeScriptValues], "valueCallback")
    ],
    "unicodeBlock": [
        ("unicodeBlockComparisons", "PopUpButton", (160, 10, 180, 20), [name for tag, name in unicodeBlockComparisons], "unicodeBlockComparisonsCallback"),
        ("unicodeBlockValues", "PopUpButton", (350, 10, 189, 20), unicodeBlockValues, "valueCallback")
    ]
}


class RuleView(vanilla.Group):

    def __init__(self, posSize, showRemoveButton=True):
        super(RuleView, self).__init__(posSize)
        self.typePopUp = vanilla.PopUpButton((1, 10, 149, 20), ["Anything", "Name", "Unicode Value", "Unicode Category", "Unicode Script", "Unicode Block"], callback=self.typeCallback)

        self.addButton = vanilla.Button((-45, 10, 20, 20), "+", callback=self.addCallback)
        self.addButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)
        if showRemoveButton:
            self.removeButton = vanilla.Button((-20, 10, 20, 20), "-", callback=self.removeCallback)
            self.removeButton.getNSButton().setBezelStyle_(AppKit.NSCircularBezelStyle)

    def set(self, rule):
        ruleType = rule["type"]
        comparisonType = rule["comparison"]
        ruleValue = rule["value"]
        self._setupControlsForRuleType(ruleType)
        if ruleType == "anything":
            self.typePopUp.set(0)
        elif ruleType == "glyphName":
            self.typePopUp.set(1)
            self.nameComparisons.show(True)
            self.nameComparisons.set(self._findIndexForTag(comparisonType, nameComparisons))
            self.textEntryField.show(True)
            self.textEntryField.set(ruleValue)
        elif ruleType == "unicodeValue":
            self.typePopUp.set(2)
            self.unicodeValueComparisons.show(True)
            self.unicodeValueComparisons.set(self._findIndexForTag(comparisonType, unicodeValueComparisons))
            if comparisonType in ("isInRange", "isNotInRange"):
                self.rangeFieldMin.show(True)
                self.fromTitle.show(True)
                self.rangeFieldMax.show(True)
                self.rangeFieldMin.set(ruleValue[0])
                self.rangeFieldMax.set(ruleValue[1])
            else:
                self.textEntryField.show(True)
                self.textEntryField.set(ruleValue)
        elif ruleType == "unicodeCategory":
            self.typePopUp.set(3)
            self.unicodeCategoryComparisons.show(True)
            self.unicodeCategoryComparisons.set(self._findIndexForTag(comparisonType, unicodeCategoryComparisons))
            self.unicodeCategoryValues.show(True)
            self.unicodeCategoryValues.set(self._findIndexForTag(ruleValue, unicodeCategoryValues))
        elif ruleType == "unicodeScript":
            self.typePopUp.set(4)
            self.unicodeScriptComparisons.show(True)
            self.unicodeScriptComparisons.set(self._findIndexForTag(comparisonType, unicodeScriptComparisons))
            self.unicodeScriptValues.show(True)
            self.unicodeScriptValues.set(unicodeScriptValues.index(ruleValue))
        elif ruleType == "unicodeBlock":
            self.typePopUp.set(5)
            self.unicodeBlockComparisons.show(True)
            self.unicodeBlockComparisons.set(self._findIndexForTag(comparisonType, unicodeBlockComparisons))
            self.unicodeBlockValues.show(True)
            self.unicodeBlockValues.set(unicodeBlockValues.index(ruleValue))

    def _findIndexForTag(self, value, items):
        for index, (storeValue, viewedValue) in enumerate(items):
            if value == storeValue:
                return index
        return 0

    def _setupControlsForRuleType(self, ruleType):
        controls = _ruleViewControls[ruleType]
        for attr, typ, posSize, contents, callback in controls:
            if hasattr(self, attr):
                continue
            if callback is not None:
                callback = getattr(self, callback)
            if typ == "PopUpButton":
                control = vanilla.PopUpButton(posSize, contents, callback=callback)
            elif typ == "EditText":
                control = vanilla.EditText(posSize, callback=callback)
            elif typ == "TextBox":
                control = vanilla.TextBox(posSize, contents)
            setattr(self, attr, control)
            control.show(False)

    # -------
    # packing
    # -------

    def _changed(self):
        view = self.getNSView().superview().vanillaWrapper()
        view.ruleChanged(self)

    def get(self):
        typeIndex = self.typePopUp.get()
        if typeIndex == 0:
            ruleType = "anything"
        elif typeIndex == 1:
            ruleType = "glyphName"
        elif typeIndex == 2:
            ruleType = "unicodeValue"
        elif typeIndex == 3:
            ruleType = "unicodeCategory"
        elif typeIndex == 4:
            ruleType = "unicodeScript"
        elif typeIndex == 5:
            ruleType = "unicodeBlock"

        if ruleType == "anything":
            ruleComparison = ""
        elif ruleType == "glyphName":
            index = self.nameComparisons.get()
            ruleComparison = nameComparisons[index][0]
        elif ruleType == "unicodeValue":
            index = self.unicodeValueComparisons.get()
            ruleComparison = unicodeValueComparisons[index][0]
        elif ruleType == "unicodeCategory":
            index = self.unicodeCategoryComparisons.get()
            ruleComparison = unicodeCategoryComparisons[index][0]
        elif ruleType == "unicodeScript":
            index = self.unicodeScriptComparisons.get()
            ruleComparison = unicodeScriptComparisons[index][0]
        elif ruleType == "unicodeBlock":
            index = self.unicodeBlockComparisons.get()
            ruleComparison = unicodeBlockComparisons[index][0]

        if ruleType == "anything":
            ruleValue = ""
        elif ruleComparison in ("isInRange", "isNotInRange"):
            v1 = self.rangeFieldMin.get()
            v2 = self.rangeFieldMax.get()
            ruleValue = (v1, v2)
        elif ruleType == "unicodeCategory":
            index = self.unicodeCategoryValues.get()
            ruleValue = unicodeCategoryValues[index][0]
        elif ruleType == "unicodeScript":
            index = self.unicodeScriptValues.get()
            ruleValue = unicodeScriptValues[index]
        elif ruleType == "unicodeBlock":
            index = self.unicodeBlockValues.get()
            ruleValue = unicodeBlockValues[index]
        else:
            ruleValue = self.textEntryField.get()

        d = AppKit.NSMutableDictionary.dictionary()
        d["type"] = ruleType
        d["comparison"] = ruleComparison
        d["value"] = ruleValue

        return d

    # ------------
    # add / remove
    # ------------

    def addCallback(self, sender):
        view = self.getNSView().superview().vanillaWrapper()
        view.addRuleAfter(self)

    def removeCallback(self, sender):
        view = self.getNSView().superview().vanillaWrapper()
        view.removeRule(self)

    # ---------------
    # input callbacks
    # ---------------

    def typeCallback(self, sender):
        typeIndex = sender.get()
        if typeIndex == 0:
            ruleType = "anything"
        elif typeIndex == 1:
            ruleType = "glyphName"
        elif typeIndex == 2:
            ruleType = "unicodeValue"
        elif typeIndex == 3:
            ruleType = "unicodeCategory"
        elif typeIndex == 4:
            ruleType = "unicodeScript"
        elif typeIndex == 5:
            ruleType = "unicodeBlock"

        self._setupControlsForRuleType(ruleType)

        for otherType, controls in _ruleViewControls.items():
            if otherType == ruleType:
                continue
            for attr, typ, posSize, contents, callback in controls:
                if hasattr(self, attr):
                    control = getattr(self, attr)
                    control.show(False)
        for attr, typ, posSize, contents, callback in _ruleViewControls[ruleType]:
            control = getattr(self, attr)
            control.show(True)

        if ruleType == "anything":
            self.anythingComparisonCallback(None)
        elif ruleType == "glyphName":
            self.nameComparisonsCallback(self.nameComparisons)
        elif ruleType == "unicodeValue":
            self.unicodeValueComparisonsCallback(self.unicodeValueComparisons)
        elif ruleType == "unicodeCategory":
            self.unicodeCategoryComparisonsCallback(self.unicodeCategoryComparisons)
        elif ruleType == "unicodeScript":
            self.unicodeScriptComparisonsCallback(self.unicodeScriptComparisons)
        elif ruleType == "unicodeBlock":
            self.unicodeBlockComparisonsCallback(self.unicodeBlockComparisons)
        self._changed()

    def anythingComparisonCallback(self, sender):
        self._changed()

    def nameComparisonsCallback(self, sender):
        self._changed()

    def unicodeValueComparisonsCallback(self, sender):
        if sender.get() in (2, 3):
            self.textEntryField.show(False)
            self.rangeFieldMin.show(True)
            self.fromTitle.show(True)
            self.rangeFieldMax.show(True)
        else:
            self.textEntryField.show(True)
            self.rangeFieldMin.show(False)
            self.fromTitle.show(False)
            self.rangeFieldMax.show(False)
        self._changed()

    def unicodeCategoryComparisonsCallback(self, sender):
        self._changed()

    def unicodeScriptComparisonsCallback(self, sender):
        self._changed()

    def unicodeBlockComparisonsCallback(self, sender):
        self._changed()

    def valueCallback(self, sender):
        self._changed()


class ContextFormatter(AppKit.NSFormatter):

    def stringForObjectValue_(self, obj):
        if not obj:
            return ""
        value = "/" + "/".join(obj)
        return value

    def objectValueForString_(self, string):
        value = string.split("/")[1:]
        value = [i for i in value]
        return value

    def attributedStringForObjectValue_withDefaultAttributes_(self, obj, attributes):
        return AppKit.NSAttributedString.alloc().initWithString_attributes_(self.stringForObjectValue_(obj), attributes)

    def getObjectValue_forString_errorDescription_(self, value, string, error):
        return True, self.objectValueForString_(string), None


class ContextListArrayController(AppKit.NSArrayController):

    # drag

    def tableView_writeRowsWithIndexes_toPasteboard_(self, tableView, indexes, pboard):
        index = str(indexes.firstIndex())
        pboard.declareTypes_owner_(["MM4ContextListPboardType"], self)
        pboard.setString_forType_(index, "MM4ContextListPboardType")
        return True

    # drop

    def tableView_validateDrop_proposedRow_proposedDropOperation_(self, tableView, draggingInfo, row, dropOperation):
        if tableView.dataSource() != self:
            return AppKit.NSDragOperationNone
        if dropOperation != AppKit.NSTableViewDropAbove:
            return AppKit.NSDragOperationNone
        # draggingSource = draggingInfo.draggingSource()
        index = draggingInfo.draggingPasteboard().stringForType_("MM4ContextListPboardType")
        index = int(index)
        return tableView.vanillaWrapper()._proposeDrop(index, row, testing=True)

    def tableView_acceptDrop_row_dropOperation_(self, tableView, draggingInfo, row, dropOperation):
        if tableView.dataSource() != self:
            return AppKit.NSDragOperationNone
        if dropOperation != AppKit.NSTableViewDropAbove:
            return AppKit.NSDragOperationNone
        # draggingSource = draggingInfo.draggingSource()
        index = draggingInfo.draggingPasteboard().stringForType_("MM4ContextListPboardType")
        index = int(index)
        return tableView.vanillaWrapper()._proposeDrop(index, row, testing=False)


class ContextList(vanilla.List):

    _arrayControllerClass = ContextListArrayController

    def __init__(self, posSize, items, dropCallback=None, **kwargs):
        super(ContextList, self).__init__(posSize, items, **kwargs)
        self._dropCallback = dropCallback
        self._tableView.registerForDraggedTypes_(["MM4ContextListPboardType"])
        self._tableView.setDraggingSourceOperationMask_forLocal_(AppKit.NSDragOperationMove, True)
        self._tableView.setDraggingSourceOperationMask_forLocal_(AppKit.NSDragOperationNone, False)

    def _proposeDrop(self, index, row, testing):
        if self._dropCallback is not None:
            return self._dropCallback(self, index, row, testing)
        return AppKit.NSDragOperationNone
