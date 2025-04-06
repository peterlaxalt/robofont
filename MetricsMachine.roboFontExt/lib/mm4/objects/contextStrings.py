import weakref
from defcon.objects.base import BaseObject
from mm4.tools.patternMatching import isValidExpression, expressionMatchesGlyphName


_fallback = {
    "name": "fallback",
    "enabled": True,
    "longContext": ["$LEFT", "$RIGHT"],
    "shortContext": ["$LEFT", "$RIGHT"],
    "suffixMatching": False,
    "pseudoUnicodes": False,
    "leftPattern": {},
    "rightPattern": {}
}


class MMContextStrings(BaseObject):

    def __init__(self, font=None):
        super(MMContextStrings, self).__init__()
        self._font = None
        if font is not None:
            self._font = weakref.ref(font)
        self._strings = []

    def getParent(self):
        return self.font

    def _get_font(self):
        if self._font is None:
            return None
        return self._font()

    font = property(_get_font, doc="The :class:`Font` that this glyph belongs to.")

    # -----------------
    # string management
    # -----------------

    def set(self, strings):
        self._strings = strings
        self.dispatcher.postNotification(notification="MMContextStrings.Changed", observable=self)

    def getLongContext(self, pair, name=None):
        """
        >>> font = _setupTestFont()
        >>> font.metricsMachine.contextStrings.set(_testStrings1)

        >>> r = font.metricsMachine.contextStrings.getLongContext(("A", "B"))[0]
        >>> [i.name for i in r]
        ['H', 'H', 'A', 'B', 'H', 'O', 'H', 'O', 'O']
        >>> r = font.metricsMachine.contextStrings.getLongContext(("A", "NotInFont"))[0]
        >>> [i.name for i in r]
        ['A']
        >>> r = font.metricsMachine.contextStrings.getLongContext(("NotInFont", "A"))[0]
        >>> [i.name for i in r]
        ['A']
        >>> r = font.metricsMachine.contextStrings.getLongContext(("NotInFont", "NotInFont"))[0]
        >>> [i.name for i in r]
        []
        >>> r = font.metricsMachine.contextStrings.getLongContext(("A.alt1", "B.alt1"))[0]
        >>> [i.name for i in r]
        ['H.alt1', 'H.alt1', 'A.alt1', 'B.alt1', 'H.alt1', 'O.alt1', 'H.alt1', 'O.alt1', 'O.alt1']
        """
        string = self._search(pair, name=name)
        longContext, longIndexes = self._populateString(pair, string["longContext"], string["suffixMatching"])
        return longContext, longIndexes

    def getShortContext(self, pair, name=None):
        """
        >>> font = _setupTestFont()
        >>> font.metricsMachine.contextStrings.set(_testStrings1)

        >>> r = font.metricsMachine.contextStrings.getShortContext(("A", "B"))[0]
        >>> [i.name for i in r]
        ['H', 'A', 'B', 'H']
        """
        string = self._search(pair, name=name)
        shortContext, shortIndexes = self._populateString(pair, string["shortContext"], string["suffixMatching"])
        return shortContext, shortIndexes

    def _populateString(self, pair, string, suffixMatching):
        font = self.getParent()
        left, right = pair
        if suffixMatching:
            if "." in left and not left.startswith("."):
                suffix = "." + left.split(".", 1)[1]
            elif "." in right and not right.startswith("."):
                suffix = "." + right.split(".", 1)[1]
            else:
                suffix = ""
        result = []
        indexes = []
        previous = None
        index = 0
        for glyphName in string:
            _rawName = glyphName
            if glyphName == "$LEFT":
                glyphName = left
            elif glyphName == "$RIGHT":
                glyphName = right
            elif glyphName == "$LEFTOPEN":
                glyphName = font.unicodeData.openRelativeForGlyphName(left)
            elif glyphName == "$LEFTCLOSE":
                glyphName = font.unicodeData.closeRelativeForGlyphName(left)
            elif glyphName == "$RIGHTOPEN":
                glyphName = font.unicodeData.openRelativeForGlyphName(right)
            elif glyphName == "$RIGHTCLOSE":
                glyphName = font.unicodeData.closeRelativeForGlyphName(right)
            elif suffixMatching:
                if glyphName + suffix in font:
                    glyphName += suffix
            if glyphName is None or glyphName not in font:
                continue
            glyph = font[glyphName]
            result.append(glyph)
            if previous == "$LEFT" and _rawName == "$RIGHT":
                indexes.append((index - 1, index))
            previous = _rawName
            index += 1
        return result, indexes

    def _search(self, pair, name=None):
        if name is not None:
            for string in self._strings:
                if not string["enabled"]:
                    continue
                if string["name"] == name:
                    return string
        else:
            left, right = pair
            for string in self._strings:
                if not string["enabled"]:
                    continue
                allowPseudoUnicodes = string["pseudoUnicodes"]
                leftPattern = string["leftPattern"]
                rightPattern = string["rightPattern"]
                if self._matchPattern(left, leftPattern, allowPseudoUnicodes) and self._matchPattern(right, rightPattern, allowPseudoUnicodes):
                    return string
        return _fallback

    def _matchPattern(self, glyphName, pattern, allowPseudoUnicodes):
        """
        >>> font = _setupTestFont()

        Anything
        --------

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "anything", "comparison" : "", "value" : ""},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True

        Name
        ----

        - is

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "is", "value" : "A"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("a", pattern, False)
        False

        - is not

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "isNot", "value" : "A"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("a", pattern, False)
        True

        - starts with

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "startsWith", "value" : "A"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("a", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True

        - does not start with

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "doesNotStartWith", "value" : "A"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("a", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False

        - ends with

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "endsWith", "value" : ".alt1"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True

        - does not end with

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "doesNotEndWith", "value" : ".alt1"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False

        - contains

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "contains", "value" : ".alt"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True

        - does not contain

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "doesNotContain", "value" : ".alt"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False

        - matches pattern

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "matchesPattern", "value" : "A*"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("Aacute", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("B", pattern, False)
        False
        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "matchesPattern", "value" : "[A*]"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False


        - does not match pattern

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "doesNotMatchPattern", "value" : "A*"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("Aacute", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("B", pattern, False)
        True
        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "glyphName", "comparison" : "doesNotMatchPattern", "value" : "[A*]"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False

        Unicode Category
        ----------------

        - is

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeCategory", "comparison" : "is", "value" : "Lu"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("a", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False

        - is not

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeCategory", "comparison" : "isNot", "value" : "Lu"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("a", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True

        Unicode Value
        -------------

        - is

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeValue", "comparison" : "is", "value" : "0041"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        True

        - is not

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeValue", "comparison" : "isNot", "value" : "0041"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        False

        - is in the range

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeValue", "comparison" : "isInRange", "value" : ("0042", "0059")},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("B", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("C", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("Y", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("Z", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("B.alt1", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("B.alt1", pattern, True)
        True

        - is not in the range

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeValue", "comparison" : "isNotInRange", "value" : ("0042", "0059")},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("B", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("C", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("Y", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("Z", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("B.alt1", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("B.alt1", pattern, True)
        False

        Unicode Script
        --------------

        - is

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeScript", "comparison" : "is", "value" : "Latin"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("zero", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False

        - is not

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeScript", "comparison" : "isNot", "value" : "Latin"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("zero", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True

        Unicode Block
        -------------

        - is

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeBlock", "comparison" : "is", "value" : "Basic Latin"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("zero", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        False

        - is not

        >>> pattern = {
        ...     "matches" : "all",
        ...     "rules" : [
        ...         {"type" : "unicodeBlock", "comparison" : "isNot", "value" : "Basic Latin"},
        ...     ]
        ... }
        >>> font.metricsMachine.contextStrings._matchPattern("A", pattern, False)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("zero", pattern, False)
        True
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, True)
        False
        >>> font.metricsMachine.contextStrings._matchPattern("A.alt1", pattern, False)
        True
        """
        if not pattern:
            return True
        font = self.getParent()
        matches = pattern["matches"]
        results = []
        for rule in pattern["rules"]:
            # get the value to test against
            ruleType = rule["type"]
            if ruleType == "anything":
                result = True
            else:
                testValue = None
                if ruleType == "unicodeCategory":
                    testValue = font.unicodeData.categoryForGlyphName(glyphName, allowPseudoUnicodes)
                elif ruleType == "unicodeValue":
                    testValue = None
                    if allowPseudoUnicodes:
                        testValue = font.unicodeData.pseudoUnicodeForGlyphName(glyphName)
                    else:
                        testValue = font.unicodeData.unicodeForGlyphName(glyphName)
                elif ruleType == "unicodeScript":
                    testValue = font.unicodeData.scriptForGlyphName(glyphName, allowPseudoUnicodes)
                elif ruleType == "unicodeBlock":
                    testValue = font.unicodeData.blockForGlyphName(glyphName, allowPseudoUnicodes)
                elif ruleType == "glyphName":
                    testValue = glyphName
                else:
                    raise NotImplementedError("unknown rule type: %s" % ruleType)
                # do the comparison
                comparison = rule["comparison"]
                value = rule["value"]
                if comparison == "is":
                    if ruleType == "unicodeValue":
                        try:
                            value = int(value, 16)
                        except ValueError:
                            value = -1
                    result = value == testValue
                elif comparison == "isNot":
                    if ruleType == "unicodeValue":
                        try:
                            value = int(value, 16)
                        except ValueError:
                            value = -1
                    result = value != testValue
                elif comparison == "startsWith":
                    result = testValue.startswith(value)
                elif comparison == "doesNotStartWith":
                    result = not testValue.startswith(value)
                elif comparison == "endsWith":
                    result = testValue.endswith(value)
                elif comparison == "doesNotEndWith":
                    result = not testValue.endswith(value)
                elif comparison == "contains":
                    result = value in testValue
                elif comparison == "doesNotContain":
                    result = value not in testValue
                elif comparison == "isInRange":
                    if testValue is None:
                        result = False
                    else:
                        minValue, maxValue = value
                        try:
                            minValue = int(minValue, 16)
                            maxValue = int(maxValue, 16)
                        except ValueError:
                            minValue = maxValue = -1
                        result = testValue >= minValue and testValue <= maxValue
                elif comparison == "isNotInRange":
                    if testValue is None:
                        result = True
                    else:
                        minValue, maxValue = value
                        try:
                            minValue = int(minValue, 16)
                            maxValue = int(maxValue, 16)
                        except ValueError:
                            minValue = maxValue = -1
                        result = testValue < minValue or testValue > maxValue
                elif comparison == "matchesPattern":
                    if not isValidExpression(value, allowReferenceGroups=True):
                        result = False
                    else:
                        result = expressionMatchesGlyphName(value, testValue, font.groups)
                elif comparison == "doesNotMatchPattern":
                    if not isValidExpression(value):
                        result = False
                    else:
                        result = not expressionMatchesGlyphName(value, testValue, font.groups)
                else:
                    raise NotImplementedError("unknown comparison %s for %s" % (comparison, ruleType))
            # handle the result
            results.append(result)
            if (result and matches == "any") or (not result and matches == "all"):
                break
        # test for rule match
        if matches == "any" and True in results:
            return True
        if matches == "all" and False not in results:
            return True
        return False


_testStrings1 = [
    {
        "name": "Uppercase, Uppercase",
        "enabled": True,
        "longContext": ["H", "H", "$LEFT", "$RIGHT", "H", "O", "H", "O", "O"],
        "shortContext": ["H", "$LEFT", "$RIGHT", "H"],
        "suffixMatching": True,
        "pseudoUnicodes": True,
        "leftPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Lu"
                },
                {
                    "type": "glyphName",
                    "comparison": "contains",
                    "value": ".uc"
                }
            ]
        },
        "rightPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Lu"
                },
                {
                    "type": "glyphName",
                    "comparison": "contains",
                    "value": ".uc"
                }
            ]
        }
    }
]


def _setupTestFont():
    import mm4.objects
    from defcon import Font
    font = Font()
    for glyphName in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
        font.newGlyph(glyphName)
        glyph = font[glyphName]
        glyph.unicode = ord(glyphName)
        for extension in [".alt1", ".alt2", ".sc"]:
            font.newGlyph(glyphName + extension)
    return font


if __name__ == "__main__":
    import doctest
    doctest.testmod()
