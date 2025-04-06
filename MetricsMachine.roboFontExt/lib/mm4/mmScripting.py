import os
from mojo import roboFont
from fontParts.base import normalizers
from mojo.extensions import getExtensionDefault, ExtensionBundle

bundle = ExtensionBundle("MetricsMachine")
version = str(bundle.version)

class MetricsMachineScriptingError(Exception): pass

# -----
# World
# -----

def AllFonts():
    fonts = []
    for font in roboFont.AllFonts():
        fonts.append(MetricsMachineFont(font.naked()))
    return tuple(fonts)

def CurrentFont():
    font = roboFont.CurrentFont()
    return MetricsMachineFont(font.naked())

# -------
# Objects
# -------

class MetricsMachineKerning(roboFont.RKerning):

    def _get_metricsMachine(self):
        """
        >>> font = makeTestFont()
        >>> t = font.kerning._metricsMachine
        """
        return self.naked().metricsMachine

    _metricsMachine = property(_get_metricsMachine)

    # fontParts Behavior

    def _items(self):
        """
        >>> font = makeTestFont()
        >>> dict(font.kerning) == dict(testKerning.items())
        True
        """
        return self._metricsMachine.items()

    def _contains(self, pair):
        """
        >>> font = makeTestFont()
        >>> ("public.kern1.X", "public.kern2.O") in font.kerning
        True
        >>> ("X.1", "O.1") in font.kerning
        True
        >>> ("X.2", "O.2") in font.kerning
        False
        """
        return pair in self._metricsMachine

    def _setItem(self, pair, value):
        """
        >>> font = makeTestFont()

        # high level pair
        >>> font.kerning["public.kern1.X", "public.kern2.O"] = 2
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        2

        # exception
        >>> font.kerning["X.1", "O.1"] = -2
        >>> font.kerning["X.1", "O.1"]
        -2

        # low level pair that is not an exception
        >>> font.kerning["X.2", "O.2"] = 3
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        3
        >>> font.kerning["X.2", "O.2"]
        Traceback (most recent call last):
            ...
        KeyError
        """
        self._metricsMachine[pair] = value

    def _getItem(self, pair):
        """
        >>> font = makeTestFont()
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        1
        >>> font.kerning["X.1", "O.1"]
        -1
        >>> font.kerning["X.2", "O.2"]
        Traceback (most recent call last):
            ...
        KeyError
        """
        if pair not in self._metricsMachine:
            raise KeyError
        return self._metricsMachine[pair]

    def _get(self, pair, default=None):
        """
        >>> font = makeTestFont()
        >>> font.kerning.get(("public.kern1.X", "public.kern2.O"))
        1
        >>> font.kerning.get(("X.1", "O.1"))
        -1
        >>> font.kerning.get(("X.2", "O.2"))
        """
        if pair not in self._metricsMachine:
            return default
        return self._metricsMachine[pair]

    def _find(self, pair, default=0):
        """
        >>> font = makeTestFont()
        >>> font.kerning.find(("public.kern1.X", "public.kern2.O"))
        1
        >>> font.kerning.find(("X.1", "O.1"))
        -1
        >>> font.kerning.find(("X.2", "O.2"))
        1
        """
        if default is None:
            default = 0
        if default != 0:
            raise MetricsMachineScriptingError("The default value for the `find` method must be 0 not %r in MetricsMachine." % default)
        return self._metricsMachine[pair]

    def _pop(self, pair, default=None):
        """
        >>> font = makeTestFont()
        >>> font.kerning.pop(("public.kern1.X", "public.kern2.O"))
        1
        >>> font.kerning["X.1", "O.1"]
        -1
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        Traceback (most recent call last):
            ...
        KeyError
        """
        if pair not in self._metricsMachine:
            return default
        value = self._metricsMachine[pair]
        del self._metricsMachine[pair]
        return value

    def _delItem(self, pair):
        """
        >>> font = makeTestFont()
        >>> del font.kerning["public.kern1.X", "public.kern2.O"]
        >>> font.kerning["X.1", "O.1"]
        -1
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        Traceback (most recent call last):
            ...
        KeyError
        """
        del self._metricsMachine[pair]

    def _clear(self):
        """
        >>> font = makeTestFont()
        >>> font.kerning.clear()
        >>> font.kerning.items()
        []
        """
        self._metricsMachine.clear()

    def _update(self, other):
        """
        >>> font = makeTestFont()
        >>> addition = {("X.2", "O.2") : 3}
        >>> font.kerning.update(addition)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        1
        >>> font.kerning["X.2", "O.2"]
        3
        """
        self._metricsMachine.update(other)

    # Pair Search

    def getActualPair(self, pair):
        """
        >>> font = makeTestFont()
        >>> font.kerning.getActualPair(("X.1", "O.1"))
        ('X.1', 'O.1')
        >>> font.kerning.getActualPair(("X.2", "O.1"))
        ('public.kern1.X', 'public.kern2.O')
        """
        side1, side2 = pair
        side1Group = None
        side2Group = None
        for group in self.font.groups.findGlyph(side1):
            if group.startswith("public.kern1"):
                side1Group = group
                break
        for group in self.font.groups.findGlyph(side2):
            if group.startswith("public.kern2"):
                side2Group = group
                break
        orderedPairs = [
            (side1, side2),
            (side1Group, side2),
            (side1, side2Group),
            (side1Group, side2Group)
        ]
        for (s1, s2) in orderedPairs:
            if s1 is None or s2 is None:
                continue
            if (s1, s2) in self:
                return (s1, s2)

    # Transformations

    def _scale(self, factor):
        self.scaleTransformation(self.keys(), factor)

    def scaleTransformation(self, factor, pairs=None):
        """
        >>> font = makeTestFont()
        >>> font.kerning.scaleTransformation(4)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        4
        >>> font.kerning["X.1", "O.1"]
        -4

        >>> font = makeTestFont()
        >>> font.kerning.scaleTransformation(4, pairs=[("X.1", "O.1")])
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        1
        >>> font.kerning["X.1", "O.1"]
        -4
        """
        if pairs is None:
            pairs = self.keys()
        pairs = [normalizers.normalizeKerningKey(pair) for pair in pairs]
        factor = normalizers.normalizeTransformationScale(factor)[0]
        self.naked().holdNotifications(note="Hold put in place by mmScripting.scaleTransformation.")
        self._metricsMachine.transformationScale(pairs, factor)
        self.naked().releaseHeldNotifications()

    def _round(self, multiple=1):
        self.applyTransformationRound(self.keys(), multiple)

    def roundTransformation(self, increment, pairs=None, removeRedundantExceptions=True):
        """
        >>> font = makeTestFont()
        >>> font.kerning["public.kern1.X", "public.kern2.O"] = 7
        >>> font.kerning["X.1", "O.1"] = 6
        >>> font.kerning.roundTransformation(10)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        10
        >>> font.kerning["X.1", "O.1"]
        Traceback (most recent call last):
            ...
        KeyError

        >>> font = makeTestFont()
        >>> font.kerning["public.kern1.X", "public.kern2.O"] = 7
        >>> font.kerning["X.1", "O.1"] = 6
        >>> font.kerning.roundTransformation(10, removeRedundantExceptions=False)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        10
        >>> font.kerning["X.1", "O.1"]
        10

        >>> font = makeTestFont()
        >>> font.kerning["public.kern1.X", "public.kern2.O"] = 7
        >>> font.kerning["X.1", "O.1"] = 6
        >>> font.kerning.roundTransformation(10, pairs=[("public.kern1.X", "public.kern2.O")])
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        10
        >>> font.kerning["X.1", "O.1"]
        6
        """
        if pairs is None:
            pairs = self.keys()
        pairs = [normalizers.normalizeKerningKey(pair) for pair in pairs]
        increment = normalizers.normalizeVisualRounding(increment)
        self.naked().holdNotifications(note="Hold put in place by mmScripting.roundTransformation.")
        self._metricsMachine.transformationRound(pairs, increment, removeRedundantExceptions)
        self.naked().releaseHeldNotifications()

    def shiftTransformation(self, value, pairs=None):
        """
        >>> font = makeTestFont()
        >>> font.kerning.shiftTransformation(1)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        2
        >>> font.kerning["X.1", "O.1"]
        0

        >>> font = makeTestFont()
        >>> font.kerning.shiftTransformation(1, pairs=[("public.kern1.X", "public.kern2.O")])
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        2
        >>> font.kerning["X.1", "O.1"]
        -1
        """
        if pairs is None:
            pairs = self.keys()
        pairs = [normalizers.normalizeKerningKey(pair) for pair in pairs]
        value = normalizers.normalizeX(value)
        self.naked().holdNotifications(note="Hold put in place by mmScripting.shiftTransformation.")
        self._metricsMachine.transformationShift(pairs, value)
        self.naked().releaseHeldNotifications()

    def thresholdTransformation(self, value, pairs=None, removeRedundantExceptions=True):
        """
        >>> font = makeTestFont()
        >>> font.kerning["public.kern1.X", "public.kern2.O"] = 11
        >>> font.kerning["X.1", "O.1"] = 9
        >>> font.kerning.thresholdTransformation(10)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        11
        >>> font.kerning["X.1", "O.1"]
        Traceback (most recent call last):
            ...
        KeyError

        >>> font = makeTestFont()
        >>> font.kerning["public.kern1.X", "public.kern2.O"] = 11
        >>> font.kerning["X.1", "O.1"] = 9
        >>> font.kerning.thresholdTransformation(10, pairs=[("public.kern1.X", "public.kern2.O")])
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        11
        >>> font.kerning["X.1", "O.1"]
        9
        """
        if pairs is None:
            pairs = self.keys()
        pairs = [normalizers.normalizeKerningKey(pair) for pair in pairs]
        value = normalizers.normalizeX(value)
        self.naked().holdNotifications(note="Hold put in place by mmScripting.thresholdTransformation.")
        self._metricsMachine.transformationThreshold(pairs, value, removeRedundantExceptions)
        self.naked().releaseHeldNotifications()

    def removeTransformation(self, pairs=None):
        """
        >>> font = makeTestFont()
        >>> font.kerning.removeTransformation()
        >>> font.kerning.items()
        []

        >>> font = makeTestFont()
        >>> font.kerning.removeTransformation(pairs=[("public.kern1.X", "public.kern2.O")])
        >>> font.kerning["X.1", "O.1"]
        -1
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        Traceback (most recent call last):
            ...
        KeyError
        """
        if pairs is None:
            pairs = self.keys()
        pairs = [normalizers.normalizeKerningKey(pair) for pair in pairs]
        self.naked().holdNotifications(note="Hold put in place by mmScripting.removeTransformation.")
        self._metricsMachine.transformationRemove(pairs)
        self.naked().releaseHeldNotifications()

    def copyTransformation(self, side1Source, side2Source, side1Replacement, side2Replacement, pairs=None):
        """
        >>> font = makeTestFont()
        >>> font.kerning.copyTransformation(
        ...     side1Source=["public.kern1.X"],
        ...     side1Replacement=["I.1"],
        ...     side2Source=["public.kern2.O"],
        ...     side2Replacement=["public.kern2.I"],
        ... )
        >>> font.kerning[("I.1", "public.kern2.I")]
        1
        """
        from defcon import Font
        if pairs is None:
            pairs = self.keys()
        pairs = [normalizers.normalizeKerningKey(pair) for pair in pairs]
        side1Source = normalizers.normalizeGroupValue(side1Source)
        side2Source = normalizers.normalizeGroupValue(side2Source)
        side1Replacement = normalizers.normalizeGroupValue(side1Replacement)
        side2Replacement = normalizers.normalizeGroupValue(side2Replacement)
        # dry run to test validity of settings
        testSubjectBase = Font()
        testSubjectBase.groups.update(self.font.groups)
        testSubjectBase.kerning.update(self.font.kerning)
        testSubject = MetricsMachineFont(testSubjectBase, showInterface=False)
        result, report = testSubject.kerning._metricsMachine.transformationCopy(
            pairs,
            side1Source=side1Source, side2Source=side2Source,
            side1Replacement=side1Replacement, side2Replacement=side2Replacement
        )
        errors = []
        for pair, value in report.items():
            if pair.startswith("error.") and value:
                errors.append(pair)
        if errors:
            raise MetricsMachineScriptingError("The copyTransformation method data is not valid: %s" % " ".join(errors))
        # apply
        self.naked().holdNotifications(note="Hold put in place by mmScripting.copyTransformation.")
        self._metricsMachine.transformationCopy(
            pairs,
            side1Source=side1Source, side2Source=side2Source,
            side1Replacement=side1Replacement, side2Replacement=side2Replacement
        )
        self.naked().releaseHeldNotifications()

    # Exceptions

    def getPairType(self, pair):
        """
        >>> font = makeTestFont()
        >>> font.kerning.getPairType(("public.kern1.X", "public.kern2.O"))
        ('group', 'group')
        >>> font.kerning.getPairType(("I.1", "N.1"))
        ('glyph', 'glyph')
        >>> font.kerning.getPairType(("X.1", "O.1"))
        ('exception', 'exception')
        """
        pair = normalizers.normalizeKerningKey(pair)
        return self._metricsMachine.getPairType(pair)

    def isException(self, pair):
        """
        >>> font = makeTestFont()
        >>> font.kerning.isException(("public.kern1.X", "public.kern2.O"))
        False
        >>> font.kerning.isException(("X.1", "O.1"))
        True
        """
        pair = normalizers.normalizeKerningKey(pair)
        return self._metricsMachine.isException(pair)

    def makeException(self, pair, value):
        """
        >>> font = makeTestFont()
        >>> font.kerning.makeException(("X.2", "O.2"), 3)
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        1
        >>> font.kerning["X.1", "O.1"]
        -1
        >>> font.kerning["X.2", "O.2"]
        3
        """
        pair = normalizers.normalizeKerningKey(pair)
        value = normalizers.normalizeKerningValue(value)
        kerning = self._metricsMachine
        possiblePairs = kerning.getPossibleExceptions(pair)
        if len(possiblePairs) == 0 or pair not in possiblePairs:
            return
        for removePair in kerning.getConflictingExceptions(pair).keys():
            del kerning[removePair]
        self._metricsMachine.makeException(pair)
        self._metricsMachine[pair] = value

    def breakException(self, pair):
        """
        >>> font = makeTestFont()
        >>> font.kerning.breakException(("X.1", "O.1"))
        >>> font.kerning["public.kern1.X", "public.kern2.O"]
        1
        >>> font.kerning["X.1", "O.1"]
        Traceback (most recent call last):
            ...
        KeyError
        """
        pair = normalizers.normalizeKerningKey(pair)
        self._metricsMachine.breakException(pair)

    # Feature Text

    def compileFeatureText(self, insertSubtableBreaks=False):
        """
        >>> font = makeTestFont()
        >>> text = font.kerning.compileFeatureText()
        >>> isinstance(text, str)
        True
        >>> text = font.kerning.compileFeatureText(insertSubtableBreaks=True)
        >>> isinstance(text, str)
        True
        """
        return self._metricsMachine.exportKerningToFeatureText(
            subtableBreaks=insertSubtableBreaks,
            appVersion=version
        )

    def exportFeatureText(self, path, insertSubtableBreaks=False):
        """
        >>> import os
        >>> import tempfile
        >>> font = makeTestFont()
        >>> path = tempfile.mkstemp()[1]
        >>> font.kerning.exportFeatureText(path)
        >>> font.kerning.exportFeatureText(path, insertSubtableBreaks=True)
        >>> os.remove(path)
        """
        assert path is not None
        self._metricsMachine.exportKerningToFeatureFile(
            path=path,
            subtableBreaks=insertSubtableBreaks,
            appVersion=version
        )

    def insertFeatureText(self, insertSubtableBreaks=False):
        """
        >>> font = makeTestFont()
        >>> before = font.features.text
        >>> font.kerning.insertFeatureText()
        >>> font.features.text == before
        False

        >>> font = makeTestFont()
        >>> before = font.features.text
        >>> font.kerning.insertFeatureText(insertSubtableBreaks=True)
        >>> font.features.text == before
        False
        """
        self._metricsMachine.exportKerningToFeatureFile(
            path=None,
            subtableBreaks=insertSubtableBreaks,
            appVersion=version
        )

    # Import

    def importKerning(self, path):
        """
        >>> import shutil
        >>> import tempfile
        >>> font = makeTestFont()
        >>> path = tempfile.mkdtemp(suffix=".ufo")
        >>> font.save(path)
        >>> font.kerning.importKerning(path)
        >>> shutil.rmtree(path)
        """
        if not os.path.exists(path):
            raise MetricsMachineScriptingError("No file located at %s." % path)
        ext = os.path.splitext(path)[-1].lower()
        if ext == ".ufo":
            self._metricsMachine.importKerningFromUFO(path)
        else:
            raise MetricsMachineScriptingError("The file located at %s is in an unknown format." % path)


class MetricsMachineGroups(roboFont.RGroups):

    def _get_metricsMachine(self):
        """
        >>> font = makeTestFont()
        >>> t = font.groups._metricsMachine
        """
        return self.naked().metricsMachine

    _metricsMachine = property(_get_metricsMachine)

    # fontParts Behavior

    def _setItem(self, pair, value):
        raise MetricsMachineScriptingError("Groups are (mostly) immutable.")

    def _pop(self, pair, default=None):
        raise MetricsMachineScriptingError("Groups are (mostly) immutable.")

    def _delItem(self, pair):
        raise MetricsMachineScriptingError("Groups are (mostly) immutable.")

    def _clear(self):
        raise MetricsMachineScriptingError("Groups are (mostly) immutable.")

    # From MM UI

    def importKerningGroups(self, pathOrGroups):
        """
        >>> font = makeTestFont()
        >>> newGroups = {
        ...     "public.kern1.O" : "O.1 O.2 O.3".split(" "),
        ...     "public.kern2.X" : "X.1 X.2 X.3".split(" ")
        ... }
        >>> font.groups.importKerningGroups(newGroups)
        >>> len(font.kerning)
        0
        >>> font.groups.side1KerningGroups
        {'public.kern1.O': ('O.1', 'O.2', 'O.3')}
        >>> font.groups.side2KerningGroups
        {'public.kern2.X': ('X.1', 'X.2', 'X.3')}
        """
        self.font.kerning.clear()
        self._metricsMachine.clear()
        if isinstance(pathOrGroups, str):
            if not os.path.exists(pathOrGroups):
                raise MetricsMachineScriptingError("No file located at %s." % pathOrGroups)
            ext = os.path.splitext(pathOrGroups)[-1].lower()
            if ext == ".ufo":
                names = self._metricsMachine.getAvailableGroupsForImportFromUFO(pathOrGroups)
                self._metricsMachine.importGroupsFromUFO(pathOrGroups, names, clearExisting=True)
            elif ext == ".mmg":
                names = self._metricsMachine.getAvailableGroupsForImportFromMMG(pathOrGroups)
                self._metricsMachine.importGroupsFromMMG(pathOrGroups, names, clearExisting=True)
            else:
                raise MetricsMachineScriptingError("The file located at %s is in an unknown format." % pathOrGroups)
        elif hasattr(pathOrGroups, "items"):
            normalized = {}
            for key, value in pathOrGroups.items():
                key = normalizers.normalizeGroupKey(key)
                if not key.startswith("public.kern1.") and not key.startswith("public.kern2."):
                    raise MetricsMachineScriptingError("All kerning groups must have the appropriate prefix.")
                value = normalizers.normalizeGroupValue(value)
                normalized[key] = value
            self._metricsMachine.update(normalized)
        else:
            raise MetricsMachineScriptingError("The object supplied for `pathOrGroups` is not a path or a dict.")

    def exportKerningGroups(self, path):
        """
        >>> import os
        >>> import tempfile
        >>> font = makeTestFont()
        >>> path = tempfile.mkstemp()[1]
        >>> font.groups.exportKerningGroups(path)
        >>> os.remove(path)
        """
        self._metricsMachine.exportGroupsToMMG(path)

    def importReferenceGroups(self, pathOrGroups):
        """
        >>> font = makeTestFont()
        >>> newGroups = {
        ...     "test" : "O.1 O.2 O.3".split(" ")
        ... }
        >>> font.groups.importReferenceGroups(newGroups)
        >>> font.groups["test"]
        ('O.1', 'O.2', 'O.3')
        """
        if isinstance(pathOrGroups, str):
            if not os.path.exists(pathOrGroups):
                raise MetricsMachineScriptingError("No file located at %s." % pathOrGroups)
            ext = os.path.splitext(pathOrGroups)[-1].lower()
            if ext == ".ufo":
                names = self._metricsMachine.getAvailableReferenceGroupsForImportFromUFO(pathOrGroups).keys()
                self._metricsMachine.importReferenceGroupsFromUFO(pathOrGroups, names, clearExisting=False)
            else:
                raise MetricsMachineScriptingError("The file located at %s is in an unknown format." % pathOrGroups)
        elif hasattr(pathOrGroups, "items"):
            normalized = {}
            for key, value in pathOrGroups.items():
                key = normalizers.normalizeGroupKey(key)
                if key.startswith("public.kern1.") or key.startswith("public.kern2."):
                    raise MetricsMachineScriptingError("Reference groups must not start with a kerning prefix.")
                value = normalizers.normalizeGroupValue(value)
                normalized[key] = value
            self._metricsMachine.update(normalized)
        else:
            raise MetricsMachineScriptingError("The object supplied for `pathOrGroups` is not a path or a dict.")


class MetricsMachineFont(roboFont.RFont):

    kerningClass = MetricsMachineKerning
    groupsClass = MetricsMachineGroups

    def __init__(self, other, showInterface=False):
        if hasattr(other, "naked"):
            other = other.naked()
        super(MetricsMachineFont, self).__init__(other, showInterface=showInterface)


# -----------
# Object Test
# -----------

testGlyphNames = "X.1 X.2 X.3 O.1 O.2 O.3 I.1 I.2 I.3 N.1".split(" ")
testKerningGroups = {
    "public.kern1.X" : "X.1 X.2 X.3".split(" "),
    "public.kern2.O" : "O.1 O.2 O.3".split(" "),
    "public.kern2.I" : "I.1 I.2 I.3".split(" ")
}
testReferenceGroups = {
    "all" : testGlyphNames,
    "none" : []
}
testKerning = {
    # group group
    ("public.kern1.X", "public.kern2.O") : 1,
    # exception
    ("X.1", "O.1") : -1
}

def makeTestFont(showInterface=False):
    font = roboFont.NewFont(showInterface=showInterface)
    for name in testGlyphNames:
        font.newGlyph(name)
    font.groups.update(testKerningGroups)
    font.groups.update(testReferenceGroups)
    font.kerning.update(testKerning)
    return MetricsMachineFont(font.naked(), showInterface=showInterface)

# ---------
# Interface
# ---------

"""
This interface interaction is going to be incredibly nasty until the
interface gets its design overhaul. In the meantime, I'd rather make
this ugly than do a lot of work to make this nice.

                                     {
                                   ( ) }
                  "--____            ))
           "      ) -_(        |/   (
      ___-´ |     | _(        0  o
        )_-  `_   / (__-+`''-------=.         _____
          )_-  |,/-'       ,--______:     .--´   /      ___
    __.-----_)_-|        <(    V v v  ---'     _'=-----'/
  .´    --   /             `-----___. -__     {__ `----'_
  |   ,    .´          ___----------'    `-_     '-----___----'
 (    /'--'|         --                     `--.__---''
 (    /   '         /
  |  /_   |        |
  (  _-)  |        \
   '-_)    '.       |_
              -_       |_
                `--_     `-__
                    `-__     `-_
                /|      `-_     \
        --.__A-/__|       _)     |          B  U  R  N  I  N  A  T  E  D  !
             `--   `-/|_-'     _/
                `-__      ___-'
                  | `-.--'
                  |    \
                  L__   |_.-
"""

def _getMainWindowControllerForFont(font=None):
    if font is None:
        font = CurrentFont()
    for other in roboFont.AllFonts():
        if other != font:
            continue
        document = other.document()
        for controller in document.windowControllers():
            window = controller.window()
            if hasattr(window, "windowName") and window.windowName() == "MetricsMachineMainWindow":
                delegate = window.delegate()
                mmController = delegate.vanillaWrapper()
                return mmController
    raise MetricsMachineScriptingError("A MetricsMachine window is not open for %r." % font)

# Pair List

def LoadPairList(path, font=None):
    window = _getMainWindowControllerForFont(font)
    window._loadPairListResult([path])

def SetPairList(pairs, font=None):
    pairList = [(pair, None) for pair in pairs]
    window = _getMainWindowControllerForFont(font)
    window.pairList.set(pairList)
    window.pairListTitle = ""
    window.editView.setPairListCount(len(pairList)-1)
    window.pairListSelectionCallback(window.pairList)

def GetPairList(font=None):
    window = _getMainWindowControllerForFont(font)
    pairs = [i[0] for i in window.pairList._originalList]
    return pairs

# Current Pair

def SetCurrentPair(pair, font=None):
    window = _getMainWindowControllerForFont(font)
    window.editView.set(pair)

def GetCurrentPair(font=None):
    window = _getMainWindowControllerForFont(font)
    return window.editView.get()

# Preview

def SetPreviewText(text, font=None):
    window = _getMainWindowControllerForFont(font)
    window.typingView.textEntry.set(text)
    window.typingView.textEntryCallback(window.typingView.textEntry)

def GetPreviewText(font=None):
    window = _getMainWindowControllerForFont(font)
    return window.typingView.textEntry.getNSTextField().objectValue()

# Open Sheets

def OpenGroupEditor(font=None):
    window = _getMainWindowControllerForFont(font)
    window.showGroupEditor()

def OpenReferenceGroupEditor(font=None):
    window = _getMainWindowControllerForFont(font)
    window.showReferenceGroupEditor()

def OpenTransformationEditor(font=None):
    window = _getMainWindowControllerForFont(font)
    window.showTransformations()

def OpenSpreadsheetEditor(font=None):
    window = _getMainWindowControllerForFont(font)
    window.showSpreadsheet()

def OpenPairListEditor(font=None):
    window = _getMainWindowControllerForFont(font)
    window.showPairListBuilder()
