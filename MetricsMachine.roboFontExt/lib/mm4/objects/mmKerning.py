import time

from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix, side1FeaPrefix, side2FeaPrefix, KernFeatureWriter

from mm4 import MetricsMachineImplementation


GROUP_GROUP = 0
GROUP_GLYPH = 1
GLYPH_GROUP = 2
GLYPH_GLYPH = 3


kernOrder = {
    (True, True): GROUP_GROUP,
    (True, False): GROUP_GLYPH,
    (False, True): GLYPH_GROUP,
    (False, False): GLYPH_GLYPH,
}


def kerningSortKeyFunc(pair):
    g1, g2 = pair
    g1grp = g1.startswith(side1Prefix)
    g2grp = g2.startswith(side2Prefix)
    return (kernOrder[g1grp, g2grp], pair)


def getKerningValue(pair, kerning, mmgroups):
    side1, side2 = pair
    # glyph, glyph or explicit pair request
    if (side1, side2) in kerning:
        return kerning[side1, side2]
    # look up group names
    if side1.startswith(side1Prefix):
        side1Group = side1
        side1 = None
    else:
        side1Group = mmgroups.getSide1GroupForGlyph(side1)
    if side2.startswith(side2Prefix):
        side2Group = side2
        side2 = None
    else:
        side2Group = mmgroups.getSide2GroupForGlyph(side2)
    # group, glyph
    if (side1Group, side2) in kerning:
        return kerning[side1Group, side2]
    # glyph, group
    elif (side1, side2Group) in kerning:
        return kerning[side1, side2Group]
    # group, group
    elif (side1Group, side2Group) in kerning:
        return kerning[side1Group, side2Group]
    # fallback to zero
    else:
        return 0


class MMKerning(MetricsMachineImplementation):

    def _get_groups(self):
        font = self.font
        if font is not None:
            return font.groups
        return None

    groups = property(_get_groups)

    def makeCopyWithoutSubscribers(self):
        font = self.font
        other = self.super().__class__(font)
        other.update(self.super())
        return other

    def sortedPairs(self, pairs=None):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.sortedPairs()
        [('public.kern1.A', 'public.kern2.A'), ('public.kern1.A', 'A'), ('A', 'public.kern2.A'), ('A', 'A')]
        """
        if pairs is None:
            pairs = self.keys()
        return sorted(pairs, key=kerningSortKeyFunc)

    def pairsSortedByUnicode(self, keys=None):
        font = self.font
        if keys is None:
            keys = font.kerning.keys()
        pairs = []
        for side1, side2 in sorted(keys):
            if side1.startswith(side1Prefix):
                if side1 not in font.groups:
                    continue
                if len(font.groups[side1]) == 0:
                    continue
                side1 = sorted(font.groups[side1])[0]
            if side2.startswith(side2Prefix):
                if side2 not in font.groups:
                    continue
                if len(font.groups[side2]) == 0:
                    continue
                side2 = sorted(font.groups[side2])[0]
            side1Uni = side2Uni = None
            if side1 in font:
                side1Glyph = font[side1]
                side1Uni = side1Glyph.unicode
                if side1Uni is None:
                    side1Uni = font.unicodeData.pseudoUnicodeForGlyphName(side1)
            if side2 in font:
                side2Glyph = font[side2]
                side2Uni = side2Glyph.unicode
                if side2Uni is None:
                    side2Uni = font.unicodeData.pseudoUnicodeForGlyphName(side2)
            if side1Uni is None:
                side1Uni = 1000000
            if side2Uni is None:
                side2Uni = 1000000
            pairs.append(((side1Uni, side2Uni), (side1, side2), None))
        return [((side1, side2), value) for (_, _), (side1, side2), value in sorted(pairs)]

    # -------------
    # Lookup Helper
    # -------------

    def _isHigherLevelPossible(self, pair, groups=None):
        """
        Determine if there is a higher level pair possible.
        This doesn't indicate that the pair exists, it simply
        indicates that something higher than (side1, side2)
        can exist.
        """
        (side1, side2) = pair
        if groups is None:
            groups = self.groups
        if side1.startswith(side1Prefix):
            side1Group = side1
            side1Glyph = None
        else:
            side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
            side1Glyph = side1
        if side2.startswith(side2Prefix):
            side2Group = side2
            side2Glyph = None
        else:
            side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
            side2Glyph = side2

        havePotentialHigherLevelPair = False
        if side1.startswith(side1Prefix) and side2.startswith(side2Prefix):
            pass
        elif side1.startswith(side1Prefix):
            if side2Group is not None:
                if (side1, side2) in self:
                    havePotentialHigherLevelPair = True
        elif side2.startswith(side2Prefix):
            if side1Group is not None:
                if (side1, side2) in self:
                    havePotentialHigherLevelPair = True
        else:
            if side1Group is not None and side2Group is not None:
                if (side1Glyph, side2Glyph) in self:
                    havePotentialHigherLevelPair = True
                elif (side1Group, side2Glyph) in self:
                    havePotentialHigherLevelPair = True
                elif (side1Glyph, side2Group) in self:
                    havePotentialHigherLevelPair = True
            elif side1Group is not None:
                if (side1Glyph, side2Glyph) in self:
                    havePotentialHigherLevelPair = True
            elif side2Group is not None:
                if (side1Glyph, side2Glyph) in self:
                    havePotentialHigherLevelPair = True
        return havePotentialHigherLevelPair

    # ----
    # dict
    # ----

    def __contains__(self, pair):
        return pair in self.super()

    def __getitem__(self, pair):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine["A", "A"]
        1
        >>> font.kerning.metricsMachine["Aacute", "A"]
        2
        >>> font.kerning.metricsMachine["A", "Aacute"]
        3
        >>> font.kerning.metricsMachine["Aacute", "Aacute"]
        4
        >>> font.kerning.metricsMachine["A", "B"]
        0
        """
        return getKerningValue(pair, self.super(), self.groups.metricsMachine)

    def __setitem__(self, pair, value):
        """
        Basic Setting
        -------------

        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)

        >>> font.kerning.metricsMachine["A", "A"] = -1
        >>> font.kerning.metricsMachine["A", "A"]
        -1
        >>> font.kerning.metricsMachine["public.kern1.A", "A"] = -2
        >>> font.kerning.metricsMachine["public.kern1.A", "A"]
        -2
        >>> font.kerning.metricsMachine["Aacute", "A"] = 2
        >>> font.kerning.metricsMachine["public.kern1.A", "A"]
        2
        >>> font.kerning.metricsMachine["A", "public.kern2.A"] = -3
        >>> font.kerning.metricsMachine["A", "public.kern2.A"]
        -3
        >>> font.kerning.metricsMachine["A", "Aacute"] = 3
        >>> font.kerning.metricsMachine["A", "public.kern2.A"]
        3
        >>> font.kerning.metricsMachine["public.kern1.A", "public.kern2.A"] = -4
        >>> font.kerning.metricsMachine["public.kern1.A", "public.kern2.A"]
        -4
        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 4
        >>> font.kerning.metricsMachine["public.kern1.A", "public.kern2.A"]
        4

        Zero Setting
        ------------

        >>> font = _setupTestFont()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)

        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 0
        >>> sorted(font.kerning.keys())
        []
        >>> font.kerning.metricsMachine["A", "A"] = 10
        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 0
        >>> sorted(font.kerning.keys())
        []
        >>> font.kerning.metricsMachine["public.kern1.A", "public.kern2.A"] = 0
        >>> sorted(font.kerning.keys())
        []

        >>> kerning = {
        ...     ("A", "A") : 0
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine["A", "A"] = 1
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 1)]
        >>> font.kerning.metricsMachine["A", "A"] = 0
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 0)]
        >>> font.kerning.metricsMachine["A", "Aacute"] = 0
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 0)]

        Exception Handling
        ------------------

        >>> kerning = {
        ...     ("A", "A") : 1
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning["A", "A"] = -1
        >>> sorted(font.kerning.items())
        [(('A', 'A'), -1)]
        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 1
        >>> sorted(font.kerning.items())
        [(('A', 'A'), -1), (('public.kern1.A', 'public.kern2.A'), 1)]

        >>> kerning = {
        ...     ("A", "public.kern2.A") : 1
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine["A", "A"] = -1
        >>> sorted(font.kerning.items())
        [(('A', 'public.kern2.A'), -1)]
        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 1
        >>> sorted(font.kerning.items())
        [(('A', 'public.kern2.A'), -1), (('public.kern1.A', 'public.kern2.A'), 1)]

        >>> kerning = {
        ...     ("public.kern1.A", "A") : 1
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine["A", "A"] = -1
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'A'), -1)]
        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 1
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'A'), -1), (('public.kern1.A', 'public.kern2.A'), 1)]
        >>> font.kerning.metricsMachine["Aacute", "Aacute"] = 0
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'A'), -1)]
        """
        self._setValueSafely(pair, value)

    def _setValueSafely(self, pair, value):
        side1, side2 = pair
        kerning = self.super()
        groups = self.groups
        if side1.startswith(side1Prefix):
            side1Group = side1
            side1Glyph = None
        else:
            side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
            side1Glyph = side1
        if side2.startswith(side2Prefix):
            side2Group = side2
            side2Glyph = None
        else:
            side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
            side2Glyph = side2

        changed = None

        # Pair already exists. Set the new value.
        if (side1, side2) in self:
            # If the value is zero, and a higher level
            # pair is not possible, delete the pair.
            if value == 0 and not self._isHigherLevelPossible((side1, side2)):
                del kerning[side1, side2]
            # Otherwise, simply set the value.
            else:
                kerning[side1, side2] = value
            changed = set([(side1, side2)])
        # Climb up to (side1Group, side2Glyph).
        # if this exists, set it.
        elif (side1Group, side2Glyph) in self:
            if value == 0 and not self._isHigherLevelPossible((side1Group, side2Glyph)):
                del kerning[side1Group, side2Glyph]
            else:
                kerning[side1Group, side2Glyph] = value
            changed = set([(side1Group, side2Glyph)])
        # Climb up to (side1Glyph, side2Group).
        # If this exists, set it.
        elif (side1Glyph, side2Group) in self:
            if value == 0 and not self._isHigherLevelPossible((side1Glyph, side2Group)):
                del kerning[side1Glyph, side2Group]
            else:
                kerning[side1Glyph, side2Group] = value
            changed = set([(side1Glyph, side2Group)])
        # Climb up to (side1Group, side2Group).
        # If this exists, set it.
        elif (side1Group, side2Group) in self:
            if value == 0:
                del kerning[side1Group, side2Group]
            else:
                kerning[side1Group, side2Group] = value
            changed = set([(side1Group, side2Group)])
        # No higher level pairs are currently in the kerning.
        # Set the highest level pair possible.
        elif side1Group is not None and side2Group is not None:
            if value != 0:
                kerning[side1Group, side2Group] = value
                changed = set([(side1Group, side2Group)])
        elif side1Group is not None:
            if value != 0:
                kerning[side1Group, side2Glyph] = value
                changed = set([(side1Group, side2Glyph)])
        elif side2Group is not None:
            if value != 0:
                kerning[side1Glyph, side2Group] = value
                changed = set([(side1Glyph, side2Group)])
        else:
            if value != 0:
                kerning[side1Glyph, side2Glyph] = value
                changed = set([(side1Glyph, side2Glyph)])

        return changed

    def __delitem__(self, pair):
        del self.super()[pair]

    def removePairs(self, pairs):
        kerning = self.super()
        for pair in pairs:
            del kerning[pair]

    def get(self, pair, default=0):
        return self[pair]

    def items(self):
        return self.super().items()

    def keys(self):
        return self.super().keys()

    def values(self):
        return self.super().values()

    def clear(self):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("B", "B") : 2,
        ... }
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.clear()
        >>> sorted(font.kerning.items())
        []
        """
        self.super().clear()

    def update(self, other):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("B", "B") : 2,
        ... }
        >>> font.kerning.metricsMachine.update(kerning)
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 1), (('B', 'B'), 2)]
        >>> kerning = {
        ...     ("A", "A") : 3,
        ...     ("C", "C") : 4,
        ... }
        >>> font.kerning.metricsMachine.update(kerning)
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 3), (('B', 'B'), 2), (('C', 'C'), 4)]

        >>> font = _setupTestFont()
        >>> groups = {
        ...     "public.kern1.A" : ["A"]
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.NotInFont") : 1,
        ...     ("B", "NotInFont") : 2,
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.kerning.metricsMachine.update(kerning)
        >>> sorted(font.kerning.items())
        []
        """
        # filter out invalid pairs
        font = self.font
        groups = self.groups
        newOther = {}
        for (side1, sisde2), value in other.items():
            if side1.startswith(side1Prefix) and side1 not in groups:
                continue
            elif not side1.startswith(side1Prefix) and side1 not in font:
                continue
            if sisde2.startswith(side2Prefix) and sisde2 not in groups:
                continue
            elif not sisde2.startswith(side2Prefix) and sisde2 not in font:
                continue
            newOther[side1, sisde2] = value
        other = newOther
        # update the internal dict and gather changes for notification
        self.super().update(other)

    # ----------
    # exceptions
    # ----------

    def getPairType(self, pair):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.getPairType(("A", "A"))
        ('exception', 'exception')
        >>> font.kerning.metricsMachine.getPairType(("Aacute", "A"))
        ('group', 'exception')
        >>> font.kerning.metricsMachine.getPairType(("public.kern1.A", "A"))
        ('group', 'exception')
        >>> font.kerning.metricsMachine.getPairType(("A", "Aacute"))
        ('exception', 'group')
        >>> font.kerning.metricsMachine.getPairType(("A", "public.kern2.A"))
        ('exception', 'group')
        >>> font.kerning.metricsMachine.getPairType(("Aacute", "Aacute"))
        ('group', 'group')
        """
        side1, side2 = pair
        groups = self.groups
        if side1.startswith(side1Prefix):
            side1Group = side1
        else:
            side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
        if side2.startswith(side2Prefix):
            side2Group = side2
        else:
            side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
        side1Type = side2Type = "glyph"

        if pair in self:
            if side1 == side1Group:
                side1Type = "group"
            elif side1Group is not None:
                side1Type = "exception"
            if side2 == side2Group:
                side2Type = "group"
            elif side2Group is not None:
                side2Type = "exception"
        elif (side1Group, side2) in self:
            side1Type = "group"
            if side2Group is not None:
                if side2 != side2Group:
                    side2Type = "exception"
        elif (side1, side2Group) in self:
            side2Type = "group"
            if side1Group is not None:
                if side1 != side1Group:
                    side1Type = "exception"
        else:
            if side1Group is not None:
                side1Type = "group"
            if side2Group is not None:
                side2Type = "group"
        return side1Type, side2Type

    def isException(self, pair):
        if pair in self and self._isHigherLevelPossible(pair):
            return True
        else:
            return False

    def makeException(self, pair):
        if pair in self:
            return
        self.super()[pair] = self[pair]

    def breakException(self, pair):
        """
        >>> font = _setupTestFont()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)

        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.breakException(("A", "A"))
        >>> sorted(font.kerning.keys())
        [('public.kern1.A', 'public.kern2.A')]

        >>> kerning = {
        ...     ("public.kern1.A", "A") : 1,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.breakException(("A", "A"))
        >>> sorted(font.kerning.keys())
        [('public.kern1.A', 'public.kern2.A')]

        >>> kerning = {
        ...     ("A", "public.kern2.A") : 1,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.breakException(("A", "A"))
        >>> sorted(font.kerning.keys())
        [('public.kern1.A', 'public.kern2.A')]

        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("A", "public.kern2.A") : 2,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> font.kerning.clear()
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.breakException(("A", "A"))
        >>> sorted(font.kerning.keys())
        [('A', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]
        """
        groups = self.groups
        side1, side2 = pair
        # the pair will be coming in as glyph, glyph,
        # so determine exactly what the exception is
        # by looking up the pair type
        pairType = self.getPairType(pair)
        side1Type, side2Type = pairType
        if side1Type == "group":
            side1 = groups.metricsMachine.getSide1GroupForGlyph(side1)
        if side2Type == "group":
            side2 = groups.metricsMachine.getSide2GroupForGlyph(side2)
        # remove the precise pair
        del self[side1, side2]

    def getPossibleExceptions(self, pair):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : -25,
        ...     ("C", "C") : -25,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern1.C" : ["C", "Ccedilla"],
        ...     "public.kern2.C" : ["C", "Ccedilla"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)

        >>> font.kerning.metricsMachine.getPossibleExceptions(("A", "A"))
        [('public.kern1.A', 'A'), ('A', 'public.kern2.A'), ('A', 'A')]
        >>> font.kerning.metricsMachine.getPossibleExceptions(("C", "C"))
        [('public.kern1.C', 'C'), ('C', 'public.kern2.C')]
        >>> font.kerning.metricsMachine.getPossibleExceptions(("C", "X"))
        [('C', 'X')]
        """
        groups = self.groups
        side1, side2 = pair
        side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
        side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
        possible = []
        if side1Group is not None and side2Group is not None:
            if (side1Group, side2) not in self:
                possible.append((side1Group, side2))
            if (side1, side2Group) not in self:
                possible.append((side1, side2Group))
        if (side1, side2) not in self:
            possible.append((side1, side2))
        return possible

    def getExceptedPairs(self, pair):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : -25,
        ...     ("A", "public.kern2.A") : -20,
        ...     ("A", "A") : -15,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.A" : ["A", "Aacute", "Agrave"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)

        >>> font.kerning.metricsMachine.getExceptedPairs(("A", "A"))
        [('A', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]
        """
        groups = self.groups
        side1, side2 = pair
        if side1.startswith(side1Prefix):
            side1Group = side1
        else:
            side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
        if side2.startswith(side2Prefix):
            side2Group = side2
        else:
            side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
        existingPairs = []
        # group, group
        # (always exists as an implied zero if it doesn't have a real value)
        if side1Group is not None and side2Group is not None:
            existingPairs.append((side1Group, side2Group))
        # group, glyph
        if (side1Group is not None and not side1.startswith(side1Prefix)) and not side2.startswith(side2Prefix):
            if (side1Group, side2) in self:
                existingPairs.insert(0, (side1Group, side2))
        # glyph, group
        if not side1.startswith(side1Prefix) and (side2Group is not None and not side2.startswith(side2Prefix)):
            if (side1, side2Group) in self:
                existingPairs.insert(0, (side1, side2Group))
        # return the found pairs
        return existingPairs

    def getConflictingExceptions(self, pair):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("Agrave", "Agrave") : -100,
        ...     ("public.kern1.A", "Agrave") : -75,
        ...     ("public.kern1.A", "Aacute") : -50,
        ...     ("public.kern1.A", "public.kern2.A") : -25,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.A" : ["A", "Aacute", "Agrave"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)

        >>> conflictExceptions = font.kerning.metricsMachine.getConflictingExceptions(("Agrave", "public.kern2.A"))
        >>> conflictExceptions == {('public.kern1.A', 'Agrave'): -75, ('public.kern1.A', 'Aacute'): -50}
        True
        >>> font.kerning.metricsMachine.getConflictingExceptions(("A", "A"))
        {}
        """
        groups = self.groups
        side1, side2 = pair
        # glyph, glyph pairs will not have conflicts
        if not side1.startswith(side1Prefix) and not side2.startswith(side2Prefix):
            return {}
        # find all possible conflicts
        if side1.startswith(side1Prefix):
            side1 = groups[side1]
        else:
            side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
            if side1Group is None:
                side1 = [side1]
            else:
                side1 = [side1Group]
        if side2.startswith(side2Prefix):
            side2 = groups[side2]
        else:
            side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
            if side2Group is None:
                side2 = [side2]
            else:
                side2 = [side2Group]
        conflicts = {}
        for s1 in side1:
            for s2 in side2:
                if (s1, s2) in self:
                    conflicts[s1, s2] = self[s1, s2]
        return conflicts

    def removeRedundantExceptions(self, pairs=None):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 1,
        ...     ("A", "public.kern2.A") : 1,
        ...     ("public.kern1.A", "public.kern2.A") : 1,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.kerning.metricsMachine.update(kerning)
        >>> font.kerning.metricsMachine.removeRedundantExceptions()
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'public.kern2.A'), 1)]

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 1,
        ...     ("public.kern1.A", "public.kern2.A") : 2,
        ... }
        >>> font.kerning.update(kerning)
        >>> font.kerning.metricsMachine.removeRedundantExceptions()
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'A'), 1), (('public.kern1.A', 'public.kern2.A'), 2)]

        Implied Zero Values
        -------------------

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("A", "A") : 0
        ... }
        >>> font.kerning.metricsMachine.update(kerning)
        >>> font.kerning.metricsMachine.removeRedundantExceptions()
        >>> sorted(font.kerning.items())
        []

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("A", "A") : 0,
        ...     ("public.kern1.A", "public.kern2.A") : 1
        ... }
        >>> font.kerning.metricsMachine.update(kerning)
        >>> font.kerning.metricsMachine.removeRedundantExceptions()
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 0), (('public.kern1.A', 'public.kern2.A'), 1)]

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("A", "A") : 0,
        ...     ("public.kern1.A", "A") : 0,
        ...     ("public.kern1.A", "public.kern2.A") : 1
        ... }
        >>> font.kerning.metricsMachine.update(kerning)
        >>> font.kerning.metricsMachine.removeRedundantExceptions()
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'A'), 0), (('public.kern1.A', 'public.kern2.A'), 1)]

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("A", "A") : 0,
        ...     ("public.kern1.A", "A") : 0
        ... }
        >>> font.kerning.metricsMachine.update(kerning)
        >>> font.kerning.metricsMachine.removeRedundantExceptions()
        >>> sorted(font.kerning.items())
        []
        """
        if pairs is None:
            pairs = self.keys()
        groups = self.groups
        for side1, side2 in list(pairs):
            if (side1, side2) not in self:
                continue
            pairType = self.getPairType((side1, side2))
            if "exception" not in pairType:
                continue
            value = self[side1, side2]
            higherValue = None
            if pairType == ("exception", "exception"):
                side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
                side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
                if (side1Group, side2) in self:
                    higherValue = self[side1Group, side2]
                elif (side1, side2Group) in self:
                    higherValue = self[side1, side2Group]
                elif (side1Group, side2Group) in self:
                    higherValue = self[side1Group, side2Group]
            elif pairType[0] == "exception":
                side1Group = groups.metricsMachine.getSide1GroupForGlyph(side1)
                if (side1Group, side2) in self:
                    higherValue = self[side1Group, side2]
            elif pairType[1] == "exception":
                side2Group = groups.metricsMachine.getSide2GroupForGlyph(side2)
                if (side1, side2Group) in self:
                    higherValue = self[side1, side2Group]
            # values match
            if value == higherValue:
                del self[side1, side2]
            # value is zero and higher value is implied zero
            elif value == 0 and higherValue is None:
                del self[side1, side2]

    # -----------------
    # Glyph Pair Counts
    # -----------------

    def _killGlyphCounts(self):
        self._glyphCounts = None

    def getGlyphCounts(self):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ...     ("B", "C") : 5,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> expectedA = {
        ...     "side1GroupCount": 2,
        ...     "side1GlyphCount": 0,
        ...     "side1ExceptionCount": 2,
        ...     "side2GroupCount": 2,
        ...     "side2GlyphCount": 0,
        ...     "side2ExceptionCount": 2,
        ... }
        >>> expectedB = {
        ...     "side1GroupCount": 0,
        ...     "side1GlyphCount": 1,
        ...     "side1ExceptionCount": 0,
        ...     "side2GroupCount": 0,
        ...     "side2GlyphCount": 0,
        ...     "side2ExceptionCount": 0,
        ... }
        >>> expectedC = {
        ...     "side1GroupCount": 0,
        ...     "side1GlyphCount": 0,
        ...     "side1ExceptionCount": 0,
        ...     "side2GroupCount": 0,
        ...     "side2GlyphCount": 1,
        ...     "side2ExceptionCount": 0,
        ... }
        >>> expectedX = {
        ...     "side1GroupCount": 0,
        ...     "side1GlyphCount": 0,
        ...     "side1ExceptionCount": 0,
        ...     "side2GroupCount": 0,
        ...     "side2GlyphCount": 0,
        ...     "side2ExceptionCount": 0,
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.kerning.metricsMachine.update(kerning)
        >>> font.kerning.metricsMachine.getGlyphCounts()["A"] == expectedA
        True
        >>> font.kerning.metricsMachine.getGlyphCounts()["B"] == expectedB
        True
        >>> font.kerning.metricsMachine.getGlyphCounts()["C"] == expectedC
        True
        >>> font.kerning.metricsMachine.getGlyphCounts()["X"] == expectedX
        True
        """
        if not hasattr(self, "_glyphCounts") or self._glyphCounts is None:
            font = self.font
            groups = self.groups
            # setup storage
            data = {}
            for name in font.keys():
                data[name] = dict(
                    side1GroupCount=set(), side2GroupCount=set(),
                    side1GlyphCount=set(), side2GlyphCount=set(),
                    side1ExceptionCount=set(), side2ExceptionCount=set()
                )
            # gather pairs
            for side1, side2 in self.keys():
                if side1.startswith(side1Prefix):
                    side1Members = groups[side1]
                else:
                    side1Members = [side1]
                if side2.startswith(side2Prefix):
                    side2Members = groups[side2]
                else:
                    side2Members = [side2]
                side1Type, side2Type = self.getPairType((side1, side2))
                side1Key = "side1%sCount" % side1Type.title()
                side2Key = "side2%sCount" % side2Type.title()
                for name in side1Members:
                    if name in data.keys():
                        if side1Key in data[name].keys():
                            data[name][side1Key].add((side1, side2))
                for name in side2Members:
                    if name in data.keys():
                        if side2Key in data[name].keys():
                            data[name][side2Key].add((side1, side2))
            # convert to numbers
            for glyphData in data.values():
                for key, pairs in glyphData.items():
                    glyphData[key] = len(pairs)
            # done
            self._glyphCounts = data
        return self._glyphCounts

    # ------
    # import
    # ------

    def importKerningFromUFO(self, path):
        from defcon import Font
        font = Font(path)
        self._importKerningFromUFO(font)

    def _importKerningFromUFO(self, otherFont):
        """
        >>> sourceFont = _setupTestFont()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ...     "public.kern1.NotInFont" : ["NotInFont"],
        ...     "@InvalidGroupName_L" : ["B"],
        ...     "@InvalidGroupName_R" : ["B"],
        ...     "public.kern1.NotReferencedByKerning" : ["C"],
        ... }
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "public.kern2.A") : 2,
        ...     ("public.kern1.NotInFont", "A") : 3,
        ...     ("NotInFont", "A") : 4,
        ...     ("NotInFont", "public.kern2.A") : 5,
        ...     ("@InvalidGroupName_L", "A") : 6,
        ...     ("A", "@InvalidGroupName_R") : 7,
        ...     ("@ThisGroupDoesNotExist", "A") : 8,
        ...     ("A", "@ThisGroupDoesNotExist") : 9,
        ... }
        >>> sourceFont.groups.update(groups)
        >>> sourceFont.kerning.update(kerning)

        >>> font = _setupTestFont()
        >>> font.kerning.metricsMachine._importKerningFromUFO(sourceFont)
        >>> sorted(font.kerning.keys())
        [('A', 'A'), ('A', 'public.kern2.InvalidGroupName_R'), ('public.kern1.A', 'public.kern2.A'), ('public.kern1.InvalidGroupName_L', 'A'), ('public.kern1.NotInFont', 'A')]
        >>> font.kerning.metricsMachine["A", "A"]
        1
        >>> font.kerning.metricsMachine["public.kern1.A", "public.kern2.A"]
        2
        >>> sorted(font.groups.keys())
        ['public.kern1.A', 'public.kern1.InvalidGroupName_L', 'public.kern1.NotInFont', 'public.kern1.NotReferencedByKerning', 'public.kern2.A', 'public.kern2.InvalidGroupName_R']
        >>> font.groups["public.kern1.A"]
        ['A', 'Aacute']
        >>> font.groups["public.kern1.NotInFont"]
        []
        """
        font = self.font
        newKerning = {}
        newGroups = {}
        necessaryGroups = set()
        renameGroups = {}
        # groups
        for (side1, side2), value in otherFont.kerning.items():
            if side1.startswith(side1Prefix) and side1 not in otherFont.groups:
                continue
            if side2.startswith(side2Prefix) and side2 not in otherFont.groups:
                continue
            if side1.startswith("@") and not side1.startswith(side1Prefix):
                renameGroups[side1] = side1Prefix + side1[1:]
                side1 = renameGroups[side1]
            if side2.startswith("@") and not side2.startswith(side2Prefix):
                renameGroups[side2] = side2Prefix + side2[1:]
                side2 = renameGroups[side2]
            if side1.startswith(side1Prefix):
                necessaryGroups.add(side1)
            elif side1 not in font:
                continue
            if side2.startswith(side2Prefix):
                necessaryGroups.add(side2)
            elif side2 not in font:
                continue
            newKerning[side1, side2] = value
        # groups
        for groupName, glyphList in otherFont.groups.items():
            if groupName in necessaryGroups or groupName in renameGroups or groupName.startswith(side1Prefix) or groupName.startswith(side2Prefix):
                glyphList = [glyphName for glyphName in glyphList if glyphName in font]
                groupName = renameGroups.get(groupName, groupName)
                newGroups[groupName] = glyphList
        # populate
        groups = {}
        for groupName, contents in font.groups.items():
            if not groupName.startswith(side1Prefix) and not groupName.startswith(side2Prefix):
                groups[groupName] = contents
        groups.update(newGroups)
        font.groups.metricsMachine.clear()
        font.groups.metricsMachine.update(groups)
        font.groups.metricsMachine.updateGroupColors(otherFont)
        self.clear()
        self.update(newKerning)

    def importKerningFromFeatureFile(self, path):
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")
        return self._importKerningFromFeatureText(text)

    def _importKerningFromFeatureText(self, text):
        """
        >>> font = _setupTestFont()
        >>> font.kerning.metricsMachine._importKerningFromFeatureText(_importFeaTestText)
        >>> data = sorted(font.kerning.items())
        >>> data == [((u'A', u'Agrave'), -75), ((u'Aacute', u'Agrave'), -75), ((u'Agrave', u'Agrave'), -100), ((u'X', u'public.kern2.D'), -25), ((u'eight', u'B'), -49), ((u'eight', u'eight'), -49), ((u'public.kern1.A', u'Aacute'), -74), ((u'public.kern1.A', u'public.kern2.A'), -25), ((u'public.kern1.D', u'X'), -25)]
        True
        >>> data = sorted([(key, sorted(value)) for key, value in font.groups.items()])
        >>> data == [(u'public.kern1.A', [u'A', u'Aacute', u'Agrave']), (u'public.kern1.D', [u'D']), (u'public.kern2.A', [u'A', u'Aacute', u'Agrave']), (u'public.kern2.D', [u'D'])]
        True
        """
        from mm4.tools.feaImport import extractKerningData
        success, errorMessage, kerning, groups = extractKerningData(text)
        if not success:
            return errorMessage
        font = self.font
        leftGroups, rightGroups = groups
        groups = {}
        for groupName, contents in font.groups.items():
            if not groupName.startswith("public.kern"):
                groups[groupName] = contents
        groups.update(leftGroups)
        groups.update(rightGroups)
        font.groups.metricsMachine.clear()
        font.groups.metricsMachine.update(groups)
        self.clear()
        self.update(kerning)

    # --------------
    # feature export
    # --------------

    def exportKerningToFeatureFile(self, path, subtableBreaks=False, appVersion="0.0"):
        from mm4.tools.replaceKernFeature import replaceKernFeature
        import codecs
        text = self.exportKerningToFeatureText(subtableBreaks=subtableBreaks, appVersion=appVersion)
        # insert into the font
        if path is None:
            font = self.font
            font.features.text = replaceKernFeature(font.features.text, text)
        # write a file
        else:
            f = codecs.open(path, "wb", encoding="utf8")
            f.write(text)
            f.close()

    def exportKerningToFeatureText(self, subtableBreaks=False, appVersion="0.0"):
        if subtableBreaks:
            return self._getFeatureTextWithSubtableBreaks(appVersion)
        else:
            return self._getFeatureText(appVersion)

    def _getFeatureText(self, appVersion="0.0", testMode=False):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     # various pair types
        ...     ("Agrave", "Agrave") : -100,
        ...     ("public.kern1.A", "Agrave") : -75,
        ...     ("public.kern1.A", "Aacute") : -74,
        ...     ("eight", "public.kern2.B") : -49,
        ...     ("public.kern1.A", "public.kern2.A") : -25,
        ...     ("public.kern1.D", "X") : -25,
        ...     ("X", "public.kern2.D") : -25,
        ...     # empty groups
        ...     ("public.kern1.C", "public.kern2.C") : 25,
        ...     ("C", "public.kern2.C") : 25,
        ...     ("public.kern1.C", "C") : 25,
        ...     # nonexistant glyphs
        ...     ("NotInFont", "NotInFont") : 25,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern1.B" : ["B", "eight"],
        ...     "public.kern2.B" : ["B", "eight"],
        ...     "public.kern1.C" : [],
        ...     "public.kern2.C" : [],
        ...     "public.kern1.D" : ["D"],
        ...     "public.kern2.D" : ["D"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)

        >>> font.kerning.metricsMachine._getFeatureText(testMode=True).splitlines() == _expectedFeatureText1.splitlines()
        True
        """
        writer = BasicFeatureWriter(self.font)
        text = writer.write(appVersion=appVersion, testMode=testMode)
        return text

    def _getFeatureTextWithSubtableBreaks(self, appVersion="0.0", testMode=False):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     # various pair types
        ...     ("Agrave", "Agrave") : -100,
        ...     ("public.kern1.A", "Agrave") : -75,
        ...     ("public.kern1.A", "Aacute") : -74,
        ...     ("eight", "public.kern2.B") : -50,
        ...     ("eight", "public.kern2.B") : -49,
        ...     ("public.kern1.A", "public.kern2.A") : -25,
        ...     ("public.kern1.D", "X") : -25,
        ...     ("X", "public.kern2.D") : -25,
        ...     # empty groups
        ...     ("public.kern1.C", "public.kern2.C") : 25,
        ...     ("C", "public.kern2.C") : 25,
        ...     ("public.kern1.C", "C") : 25,
        ...     # nonexistant glyphs
        ...     ("NotInFont", "NotInFont") : 25,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern1.B" : ["B", "eight"],
        ...     "public.kern2.B" : ["B", "eight"],
        ...     "public.kern1.C" : [],
        ...     "public.kern2.C" : [],
        ...     "public.kern1.D" : ["D"],
        ...     "public.kern2.D" : ["D"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)

        >>> font.kerning.metricsMachine._getFeatureTextWithSubtableBreaks(testMode=True).splitlines() == _expectedFeatureText2.splitlines()
        True
        >>> font = _setupTestFontForFeatureSubtable()
        >>> lines = font.kerning.metricsMachine._getFeatureTextWithSubtableBreaks(testMode=True).splitlines()
        >>> lines == _expectedFeatureText3.splitlines()
        True
        >>> if lines != _expectedFeatureText3.splitlines():
        ...     lines
        ...     _expectedFeatureText3.splitlines()

        """
        writer = SubtableBreakWriter(self.font)
        text = writer.write(appVersion=appVersion, testMode=testMode)
        return text

    def _getFeatureSeperatedPairs(self, pairs):
        font = self.font
        groups = self.groups
        # seperate pairs
        glyphGlyph = {}
        glyphGroup = {}
        glyphGroupDecomposed = {}
        groupGlyph = {}
        groupGlyphDecomposed = {}
        groupGroup = {}
        for (side1, side2), value in pairs.items():
            if side1.startswith(side1Prefix) and side2.startswith(side2Prefix):
                if not groups[side1] or not groups[side2]:
                    continue
                groupGroup[side1, side2] = value
            elif side1.startswith(side1Prefix):
                if not groups[side1] or side2 not in font:
                    continue
                groupGlyph[side1, side2] = value
            elif side2.startswith(side2Prefix):
                if not groups[side2] or side1 not in font:
                    continue
                glyphGroup[side1, side2] = value
            else:
                if side1 not in font or side2 not in font:
                    continue
                glyphGlyph[side1, side2] = value
        # handle decomposition
        allGlyphGlyph = set(glyphGlyph.keys())
        # glyph to group
        for (side1, side2), value in list(glyphGroup.items()):
            if self._isHigherLevelPossible((side1, side2)):
                finalSide2 = tuple([s2 for s2 in sorted(groups[side2]) if (side1, s2) not in allGlyphGlyph])
                for r in finalSide2:
                    allGlyphGlyph.add((side1, r))
                glyphGroupDecomposed[side1, finalSide2] = value
                del glyphGroup[side1, side2]
        # group to glyph
        for (side1, side2), value in list(groupGlyph.items()):
            if self._isHigherLevelPossible((side1, side2)):
                finalSide1 = tuple([s1 for s1 in sorted(groups[side1]) if (s1, side2) not in glyphGlyph and (s1, side2) not in allGlyphGlyph])
                for s1 in finalSide1:
                    allGlyphGlyph.add((s1, side2))
                groupGlyphDecomposed[finalSide1, side2] = value
                del groupGlyph[side1, side2]
        # return the result
        return glyphGlyph, glyphGroupDecomposed, groupGlyphDecomposed, glyphGroup, groupGlyph, groupGroup

    # ----------
    # afm export
    # ----------

    def exportKerningToAFMFile(self, path, glyphs, appVersion="0.0"):
        """
        >>> import os
        >>> path = os.path.join(os.path.dirname(__file__), "_testAFM.afm")

        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : -100,
        ...     ("A", "B") : -100,
        ...     ("A", "C") : -100,
        ... }
        >>> font.kerning.update(kerning)

        >>> font.kerning.metricsMachine.exportKerningToAFMFile(path, glyphs=["A", "B"])
        >>> f = open(path, "rb")
        >>> text = f.read().decode("utf-8")
        >>> f.close()
        >>> os.remove(path)
        >>> text.splitlines()[2:] == _expectedAFMText.splitlines()
        True
        """
        from fontTools.afmLib import AFM
        from fontTools.misc.arrayTools import unionRect
        from fontTools.encodings.StandardEncoding import StandardEncoding

        font = self.font
        glyphs = set(glyphs)
        _kerning = self.getFlatKerning()
        kerning = {}
        for (side1, side2), value in _kerning.items():
            if side1 not in glyphs or side2 not in glyphs:
                continue
            kerning[side1, side2] = value

        afm = AFM()
        afm.addComment(u"exported from MetricsMachine Extension %s" % appVersion)
        afm._kerning = kerning

        fontBox = None
        for glyph in font:
            glyphName = glyph.name
            if glyphName not in glyphs:
                continue
            bounds = glyph.bounds
            if bounds is None:
                bounds = (0, 0, 0, 0)
            box = tuple([int(round(i)) for i in bounds])
            if fontBox is None:
                fontBox = box
            fontBox = unionRect(fontBox, box)

            codePoint = -1
            if glyphName in StandardEncoding:
                codePoint = StandardEncoding.index(glyphName)
            afm._chars[glyphName] = (codePoint, int(round(glyph.width)), box)

        info = font.info
        afm.Ascender = info.ascender
        afm.FontBBox = fontBox
        afm.CapHeight = info.capHeight
        afm.Descender = info.descender
        afm.EncodingScheme = "AdobeStandardEncoding"
        afm.FamilyName = info.familyName
        afm.FontName = info.postscriptFontName
        afm.FullName = info.postscriptFullName
        afm.ItalicAngle = info.italicAngle
        afm.XHeight = info.xHeight
        versionMajor = info.versionMajor
        versionMinor = info.versionMinor
        if versionMajor is None:
            versionMajor = 1
        if versionMinor is None:
            versionMinor = 0
        afm.Version = "%s.%s" % (str(versionMajor).zfill(3), str(versionMinor).zfill(3))
        try:
            copyright = str(info.copyright)
            afm.Notice = copyright
        except UnicodeEncodeError:
            pass

        afm.write(path, sep="\n")

    # ------------
    # flat kerning
    # ------------

    def getFlatKerning(self, pairs=None):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 1,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> sorted(font.kerning.metricsMachine.getFlatKerning().items())
        [(('A', 'A'), 1), (('A', 'Aacute'), 3), (('Aacute', 'A'), 2), (('Aacute', 'Aacute'), 4)]

        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 0,
        ...     ("public.kern1.A", "A") : 2,
        ...     ("A", "public.kern2.A") : 3,
        ...     ("public.kern1.A", "public.kern2.A") : 4,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"],
        ...     "public.kern2.A" : ["A", "Aacute"],
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> sorted(font.kerning.metricsMachine.getFlatKerning().items())
        [(('A', 'A'), 0), (('A', 'Aacute'), 3), (('Aacute', 'A'), 2), (('Aacute', 'Aacute'), 4)]
        """
        if pairs is None:
            pairs = self
        glyphGlyph, glyphGroupDecomposed, groupGlyphDecomposed, glyphGroup, groupGlyph, groupGroup = self._getFeatureSeperatedPairs(pairs)
        flattened = dict(glyphGlyph)
        groups = self.groups
        for (side1, side2List), value in glyphGroupDecomposed.items():
            for side2 in side2List:
                if (side1, side2) in flattened:
                    continue
                flattened[side1, side2] = value
        for (side1List, side2), value in groupGlyphDecomposed.items():
            for side1 in side1List:
                if (side1, side2) in flattened:
                    continue
                flattened[side1, side2] = value
        for (side1, side2Group), value in glyphGroup.items():
            for side2 in groups[side2Group]:
                if (side1, side2) in flattened:
                    continue
                flattened[side1, side2] = value
        for (side1Group, side2), value in groupGlyph.items():
            for side1 in groups[side1Group]:
                if (side1, side2) in flattened:
                    continue
                flattened[side1, side2] = value
        for (side1Group, side2Group), value in groupGroup.items():
            for side1 in groups[side1Group]:
                for side2 in groups[side2Group]:
                    if (side1, side2) in flattened:
                        continue
                    flattened[side1, side2] = value
        return flattened

    # ---------------
    # transformations
    # ---------------

    def _updateAfterTransformation(self, pairs):
        for pair, value in pairs.items():
            if value == "remove":
                del self[pair]
            else:
                self._setValueSafely(pair, value)

    def transformationCopy(self, pairs, side1Source, side2Source, side1Replacement, side2Replacement):
        # use a copy of the kerning data and manipulate it for each side
        kerning = self.super().copy()
        # process side1
        side1Report = {}
        side1Changes = {}
        side1SourcePairs = {}
        if side1Replacement:
            side1Changes, side1SourcePairs, side1Report = self._performCopyForSide(kerning, pairs, side1Source, side1Replacement, "side1")
            kerning.update(side1Changes)
        # process side2
        side2Report = {}
        side2Changes = {}
        side2SourcePairs = {}
        if side2Replacement:
            if side1Replacement:
                pairs = side1Changes.keys()
            side2Changes, side2SourcePairs, side2Report = self._performCopyForSide(kerning, pairs, side2Source, side2Replacement, "side2")
            kerning.update(side2Changes)
        # if side1 and side2 are present, keep only
        # pairs that were touched by both the side1
        # and side2 processing. fallback to each side
        # as needed.
        if side1Replacement and side2Replacement:
            newPairs = {}
            for originalPair, resultingPairs in side2SourcePairs.items():
                if originalPair in side1Changes:
                    for pair in resultingPairs:
                        newPairs[pair] = side2Changes[pair]
        elif side1Replacement:
            newPairs = side1Changes
        elif side2Replacement:
            newPairs = side2Changes
        else:
            newPairs = {}
        # create the final report
        report = {}
        for key, value in side1Report.items():
            key += " Side 1"
            report[key] = value
        for key, value in side2Report.items():
            key += " Side 2"
            report[key] = value
        # update the kerning
        self._updateAfterTransformation(newPairs)
        # done
        return newPairs, report

    def _performCopyForSide(self, kerning, pairs, source, replacement, side):
        # gather the partners
        report = dict(partners=[])
        self._getCopyType(source, replacement, report)
        self._findCopyPartners(source, replacement, side, report)
        # work out a tree of source to replacement
        partners = report["partners"]
        replacementTree = {}
        for s, r in partners:
            if s not in replacementTree:
                replacementTree[s] = set()
            replacementTree[s].add(r)
        # create new pairs
        newPairs = {}
        sourcePairs = {}
        for pair in pairs:
            value = getKerningValue(pair, kerning, self.groups)
            side1, side2 = pair
            haveReplacement = False
            if side == "side1":
                if side1 in replacementTree:
                    side1 = replacementTree[side1]
                    side2 = [side2]
                    haveReplacement = True
            else:
                if side2 in replacementTree:
                    side2 = replacementTree[side2]
                    side1 = [side1]
                    haveReplacement = True
            if haveReplacement:
                for l in side1:
                    for r in side2:
                        newPairs[l, r] = value
                        if pair not in sourcePairs:
                            sourcePairs[pair] = set()
                        sourcePairs[pair].add((l, r))
        # return
        return newPairs, sourcePairs, report

    def _getCopyType(self, source, replacement, report):
        # 1 to 1
        if len(source) == 1 and len(replacement) == 1:
            report["type"] = "One to One"
        # many to 1
        elif len(source) > 1 and len(replacement) == 1:
            report["type"] = "Many to One"
        # 1 to many
        elif len(source) == 1 and len(replacement) > 1:
            report["type"] = "One to Many"
        # many to many
        elif len(source) > 1 and len(replacement) > 1:
            report["type"] = "Many to Many"
        else:
            report["type"] = "Unknown"

    def _findCopyPartners(self, source, replacement, side, report):
        """
        >>> font = _setupTestFont()

        # 1 to 1
        >>> r = dict(partners=[], type="One to One")
        >>> font.kerning.metricsMachine._findCopyPartners(["A"], ["A.sc"], "left", r)
        >>> sorted(r["partners"])
        [('A', 'A.sc')]
        >>> r = dict(partners=[], type="One to One")
        >>> font.kerning.metricsMachine._findCopyPartners(["A"], ["B"], "left", r)
        >>> sorted(r["partners"])
        [('A', 'B')]
        >>> r = dict(partners=[], type="One to One")
        >>> font.kerning.metricsMachine._findCopyPartners(["A"], ["A"], "left", r)
        >>> sorted(r["partners"])
        []

        # many to 1
        >>> r = dict(partners=[], type="Many to One")
        >>> font.kerning.metricsMachine._findCopyPartners(["A", "B", "C"], ["A"], "left", r)
        >>> sorted(r["partners"])
        [('B', 'A'), ('C', 'A')]

        # 1 to many
        >>> r = dict(partners=[], type="One to Many")
        >>> font.kerning.metricsMachine._findCopyPartners(["A"], ["A", "B", "C"], "left", r)
        >>> sorted(r["partners"])
        [('A', 'B'), ('A', 'C')]

        # many to many
        >>> source = ["A", "B", "C", "D.sc", "E.sc", "onlyInSource", "tooManySouurce.1", "tooManySouurce.1", "tooManyReplacement.1"]
        >>> replacement = ["A.sc", "B.sc", "C.sc", "D", "E", "onlyInReplacement", "tooManySouurce.3", "tooManyReplacement.2", "tooManyReplacement.3"]
        >>> r = dict(partners=[], type="Many to Many")
        >>> font.kerning.metricsMachine._findCopyPartners(source, replacement, "left", r)
        >>> sorted(r["partners"])
        [('A', 'A.sc'), ('B', 'B.sc'), ('C', 'C.sc'), ('D.sc', 'D'), ('E.sc', 'E')]
        """
        groups = self.groups
        copyType = report["type"]
        partners = report["partners"]
        sourceIsReplacement = report["error.sourceIsReplacement"] = []
        # 1 to 1
        if copyType == "One to One":
            s = source[0]
            r = replacement[0]
            if s == r:
                sourceIsReplacement.append((s, r))
            elif (s.startswith(side1Prefix) or s.startswith(side2Prefix)) and r in groups[s]:
                sourceIsReplacement.append((s, r))
            elif (r.startswith(side1Prefix) or r.startswith(side2Prefix)) and s in groups[r]:
                sourceIsReplacement.append((s, r))
            elif (s, r) not in partners:
                partners.append((s, r))
        # many to 1
        elif copyType == "Many to One":
            r = replacement[0]
            for s in source:
                if s == r:
                    sourceIsReplacement.append((s, r))
                elif (s.startswith(side1Prefix) or s.startswith(side2Prefix)) and r in groups[s]:
                    sourceIsReplacement.append((s, r))
                elif (r.startswith(side1Prefix) or r.startswith(side2Prefix)) and s in groups[r]:
                    sourceIsReplacement.append((s, r))
                elif (s, r) not in partners:
                    partners.append((s, r))
        # 1 to many
        elif copyType == "One to Many":
            s = source[0]
            for r in replacement:
                if s == r:
                    sourceIsReplacement.append((s, r))
                elif (s.startswith(side1Prefix) or s.startswith(side2Prefix)) and r in groups[s]:
                    sourceIsReplacement.append((s, r))
                elif (r.startswith(side1Prefix) or r.startswith(side2Prefix)) and s in groups[r]:
                    sourceIsReplacement.append((s, r))
                elif (s, r) not in partners:
                    partners.append((s, r))
        # many to many
        elif copyType == "Many to Many":
            # look for common glyphs accross the source and replacement
            duplicates = []
            for name in source:
                if name in replacement:
                    duplicates.append(name)
            sourceIsReplacement.extend([(i, i) for i in duplicates])
            for name in duplicates:
                source.remove(name)
                replacement.remove(name)
            # hold groups from source and replacement
            holdingSourceGroups = [i for i in source if i.startswith(side1Prefix) or i.startswith(side2Prefix)]
            holdingReplacementGroups = [i for i in replacement if i.startswith(side1Prefix) or i.startswith(side2Prefix)]
            source = [i for i in source if not i.startswith(side1Prefix) or not i.startswith(side2Prefix)]
            replacement = [i for i in replacement if not i.startswith(side1Prefix) or not i.startswith(side2Prefix)]
            # glyphs
            # build trees of base : [glyphs]
            sourceTree = {}
            for name in source:
                base = name.split(".")[0]
                if base not in sourceTree:
                    sourceTree[base] = []
                sourceTree[base].append(name)
            replacementTree = {}
            for name in replacement:
                base = name.split(".")[0]
                if base not in replacementTree:
                    replacementTree[base] = []
                replacementTree[base].append(name)
            # look for uncommon bases
            inSourceNotReplacement = report["error.inSourceNotReplacement"] = []
            for base, glyphList in list(sourceTree.items()):
                if base not in replacementTree:
                    inSourceNotReplacement += glyphList
                    del sourceTree[base]
            inReplacementNotSource = report["error.inReplacementNotSource"] = []
            for base, glyphList in list(replacementTree.items()):
                if base not in sourceTree:
                    inReplacementNotSource += glyphList
                    del replacementTree[base]
            assert set(sourceTree.keys()) == set(replacementTree.keys())
            # look for too many glyphs associated with a base
            tooManySources = report["error.tooManySources"] = []
            tooManyReplacements = report["error.tooManyReplacements"] = []
            for base in list(sourceTree.keys()):
                problem = False
                sourceGlyphList = sourceTree[base]
                if len(sourceGlyphList) > 1:
                    tooManySources.append(sourceGlyphList)
                    problem = True
                replacementGlyphList = replacementTree[base]
                if len(replacementGlyphList) > 1:
                    tooManyReplacements.append(replacementGlyphList)
                    problem = True
                if problem:
                    del sourceTree[base]
                    del replacementTree[base]
            # search for conflicting sources or replacements
            basesToRemove = set()
            sources = []
            sourceProblems = set()
            for base, glyphList in sourceTree.items():
                for glyphName in glyphList:
                    if glyphName in sources:
                        sourceProblems.add(glyphName)
                        basesToRemove.add(base)
                    else:
                        sources.append(glyphName)
            replacements = []
            replacementProblems = set()
            for base, glyphList in sourceTree.items():
                for glyphName in glyphList:
                    if glyphName in replacements:
                        replacementProblems.add(glyphName)
                        basesToRemove.add(base)
                    else:
                        replacements.append(glyphName)
            for base in basesToRemove:
                del sourceTree[base]
                del replacementTree[base]
            report["error.conflictingSources"] = list(sourceProblems)
            report["error.conflictingReplacements"] = list(replacementProblems)
            # merge trees
            for base in sourceTree.keys():
                s = sourceTree[base][0]
                r = replacementTree[base][0]
                if (s, r) not in partners:
                    partners.append((s, r))
            # elevate glyphs into groups
            self._elevateCopyPartnerGlyphs(side, report)
            # groups
            # make base trees
            sourceTree = {}
            for groupName in holdingSourceGroups:
                glyphList = groups[groupName]
                glyphList = [glyphName.split(".")[0] for glyphName in glyphList]
                glyphList = frozenset(glyphList)
                if glyphList not in sourceTree:
                    sourceTree[glyphList] = set()
                sourceTree[glyphList].add(groupName)
            replacementTree = {}
            for groupName in holdingReplacementGroups:
                glyphList = groups[groupName]
                glyphList = [glyphName.split(".")[0] for glyphName in glyphList]
                glyphList = frozenset(glyphList)
                if glyphList not in replacementTree:
                    replacementTree[glyphList] = set()
                replacementTree[glyphList].add(groupName)
            # compare the trees to make maps
            sourceToReplacement = {}
            replacementToSource = {}
            for sourceBase, sourceGroups in sourceTree.items():
                for replacementBase, replacementGroups in replacementTree.items():
                    if sourceBase & replacementBase:
                        for s in sourceGroups:
                            if s not in sourceToReplacement:
                                sourceToReplacement[s] = []
                            sourceToReplacement[s].extend(replacementGroups)
                        for r in replacementGroups:
                            if r not in replacementToSource:
                                replacementToSource[r] = []
                            replacementToSource[r].extend(sourceGroups)
            # look for anything other than 1 to 1 mapping
            tooManyReplacementGroups = report["error.tooManyReplacementGroups"] = {}
            for sourceGroup, replacementGroups in sourceToReplacement.items():
                if len(replacementGroups) > 1:
                    tooManyReplacementGroups[sourceGroup] = replacementGroups
                    del sourceToReplacement[sourceGroup]
            tooManySourceGroups = report["error.tooManySourceGroups"] = {}
            for replacementGroup, sourceGroups in replacementToSource.items():
                if len(sourceGroups) > 1:
                    tooManySourceGroups[replacementGroup] = sourceGroups
                    del replacementToSource[replacementGroup]
            # add to partners
            for s, r in sourceToReplacement.items():
                p = (s, r[0])
                if p not in partners:
                    partners.append(p)
        # warn if replacement is glyph and glyph is in group
        # and group is not also a replacement.
        if side == "side1":
            groupLookupMethod = groups.metricsMachine.getSide1GroupForGlyph
        else:
            groupLookupMethod = groups.metricsMachine.getSide2GroupForGlyph
        warnings = report["warning.groupNotInReplacement"] = []
        for s, r in partners:
            if r.startswith(side1Prefix) or r.startswith(side2Prefix):
                continue
            rG = groupLookupMethod(r)
            sG = groupLookupMethod(s)
            if rG is not None:
                # source group, replacement group in partners
                if (sG, rG) in partners:
                    continue
                if (s, rG) not in partners:
                    warnings.append((r, rG))
        # warn if source is glyph and glyph is in group
        # and group is not also a source
        warnings = report["warning.groupNotInSource"] = []
        for s, r in partners:
            if s.startswith(side1Prefix) or s.startswith(side2Prefix):
                continue
            rG = groupLookupMethod(r)
            sG = groupLookupMethod(s)
            if sG is not None:
                # source group, replacement group in partners
                if (sG, rG) in partners:
                    continue
                if (sG, r) not in partners:
                    warnings.append((s, sG))

    def _elevateCopyPartnerGlyphs(self, side, report):
        """
        >>> font = _setupTestFontForCopy()
        >>> groups = {
        ...     # UC
        ...     "public.kern1.H" : "H I M N".split(" "),
        ...     "public.kern2.H" : "B D E F H I M N P R".split(" "),
        ...     "public.kern1.O" : "D O Q".split(" "),
        ...     "public.kern2.O" : "C G O Q".split(" "),
        ...     "public.kern1.U" : "J U".split(" "),
        ...     # sc
        ...     "public.kern1.H.sc" : "H.sc I.sc M.sc N.sc".split(" "),
        ...     "public.kern2.H.sc" : "B.sc D.sc E.sc F.sc H.sc I.sc M.sc N.sc P.sc R.sc".split(" "),
        ...     "public.kern1.O.sc" : "D.sc O.sc Q.sc".split(" "),
        ...     "public.kern2.O.sc" : "C.sc G.sc O.sc Q.sc".split(" "),
        ...     # public.kern1.U.sc not defined
        ... }
        >>> font.groups.update(groups)
        >>> r = dict(partners=[("A", "A.sc"), ("H", "H.sc"), ("U", "U.sc")])
        >>> font.kerning.metricsMachine._elevateCopyPartnerGlyphs("left", r)
        >>> r["partners"]
        [('A', 'A.sc'), ('H', 'H.sc'), ('U', 'U.sc'), ('public.kern1.H', 'public.kern1.H.sc'), ('public.kern1.U', 'U.sc')]
        """
        groups = self.groups
        if side == "side1":
            groupLookupMethod = groups.metricsMachine.getSide1GroupForGlyph
        else:
            groupLookupMethod = groups.metricsMachine.getSide2GroupForGlyph
        partners = report["partners"]
        groupedPartners = []
        for source, replacement in partners:
            # already grouped
            if source.startswith(side1Prefix) or source.startswith(side2Prefix):
                continue
            if replacement.startswith(side1Prefix) or replacement.startswith(side2Prefix):
                continue
            sourceGroup = groupLookupMethod(source)
            replacementGroup = groupLookupMethod(replacement)
            # no groups
            if sourceGroup is None and replacementGroup is None:
                continue
            # only one group
            if sourceGroup is not None and replacementGroup is None:
                groupedPartners.append((sourceGroup, replacement))
                continue
            if sourceGroup is None and replacementGroup is not None:
                groupedPartners.append((source, replacementGroup))
                continue
            # group
            g = (sourceGroup, replacementGroup)
            if g not in groupedPartners:
                groupedPartners.append(g)
        # extend partners
        report["partners"].extend(groupedPartners)

    def transformationRemove(self, pairs):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 3,
        ...     ("A", "B") : -3,
        ...     ("A", "C") : 5,
        ...     ("A", "D") : -5,
        ...     ("A", "E") : 10,
        ...     ("A", "F") : -10,
        ... }
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationRemove([("A", "A"), ("A", "B")])
        >>> sorted(font.kerning.items())
        [(('A', 'C'), 5), (('A', 'D'), -5), (('A', 'E'), 10), (('A', 'F'), -10)]
        """
        for pair in pairs:
            del self[pair]

    def transformationScale(self, pairs, factor):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 3,
        ...     ("A", "B") : -3,
        ...     ("A", "C") : 5,
        ...     ("A", "D") : -5,
        ...     ("A", "E") : 10,
        ...     ("A", "F") : -10,
        ... }
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationScale(kerning.keys(), 2)
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 6), (('A', 'B'), -6), (('A', 'C'), 10), (('A', 'D'), -10), (('A', 'E'), 20), (('A', 'F'), -20)]
        """
        changed = {}
        for pair in pairs:
            original = self.get(pair)
            v = int(round(original * factor))
            if v != original:
                changed[pair] = v
        self._updateAfterTransformation(changed)
        return changed

    def transformationShift(self, pairs, value):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 3,
        ...     ("A", "B") : -3,
        ...     ("A", "C") : 5,
        ...     ("A", "D") : -5,
        ...     ("A", "E") : 10,
        ...     ("A", "F") : -10,
        ... }
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationShift(kerning.keys(), 5)
        >>> sorted(font.kerning.items())
        [(('A', 'A'), 8), (('A', 'B'), 2), (('A', 'C'), 10), (('A', 'E'), 15), (('A', 'F'), -5)]
        """
        changed = {}
        for pair in pairs:
            original = self.get(pair)
            v = original + value
            if v != original:
                changed[pair] = v
        self._updateAfterTransformation(changed)
        return changed

    def transformationRound(self, pairs, increment, removeRedundantExceptions=False):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 2,
        ...     ("A", "B") : -2,
        ...     ("A", "C") : 5,
        ...     ("A", "D") : -5,
        ...     ("A", "E") : 10,
        ...     ("A", "F") : -10,
        ... }
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationRound(kerning.keys(), 5)
        >>> sorted(font.kerning.items())
        [(('A', 'C'), 5), (('A', 'D'), -5), (('A', 'E'), 10), (('A', 'F'), -10)]

        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 7,
        ...     ("public.kern1.A", "A") : 5,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute"]
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationRound(kerning.keys(), 5, removeRedundantExceptions=True)
        >>> sorted(font.kerning.items())
        [(('public.kern1.A', 'A'), 5)]
        """
        changed = {}
        for pair in pairs:
            original = self.get(pair)
            v = int(round(original / float(increment))) * increment
            if v != original:
                changed[pair] = v
        self._updateAfterTransformation(changed)
        if removeRedundantExceptions:
            self.removeRedundantExceptions(pairs)
        return changed

    def transformationThreshold(self, pairs, value, removeRedundantExceptions=False):
        """
        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("A", "A") : 3,
        ...     ("A", "B") : -3,
        ...     ("A", "C") : 5,
        ...     ("A", "D") : -5,
        ...     ("A", "E") : 10,
        ...     ("A", "F") : -10,
        ... }
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationThreshold(kerning.keys(), 5)
        >>> sorted(font.kerning.items())
        [(('A', 'E'), 10), (('A', 'F'), -10)]

        >>> font = _setupTestFont()
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : -140,
        ...     ("A", "public.kern2.A") : -100,
        ...     ("A", "A") : -50,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.A" : ["A", "Aacute", "Agrave"],
        ... }

        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationThreshold(kerning.keys(), 50)
        >>> sorted(font.kerning.items())
        [(('A', 'A'), -50), (('A', 'public.kern2.A'), -100), (('public.kern1.A', 'public.kern2.A'), -140)]

        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> changed = font.kerning.metricsMachine.transformationThreshold(kerning.keys(), 90)
        >>> sorted(font.kerning.items())
        [(('A', 'public.kern2.A'), -100), (('public.kern1.A', 'public.kern2.A'), -140)]
        """
        changed = {}
        for pair in pairs:
            v = self.get(pair)
            if abs(v) <= value:
                isException = self.isException(pair)
                # exception
                # remove if the difference between the highest excepted pair
                # and the exception is less than the threshold.
                if isException:
                    higherLevelPairs = self.getExceptedPairs(pair)
                    higherDiffs = []
                    for higherPair in higherLevelPairs:
                        higherValue = self[higherPair]
                        d = abs(abs(v) - abs(higherValue))
                        higherDiffs.append(d)
                    if not higherDiffs or max(higherDiffs) <= value:
                        changed[pair] = "remove"
                # basic pair
                else:
                    changed[pair] = 0
        self._updateAfterTransformation(changed)
        if removeRedundantExceptions:
            self.removeRedundantExceptions(pairs)
        return changed


# ---------------
# Feature Writers
# ---------------

inlineGroupInstance = (list, tuple, set)


class BasicFeatureWriter(KernFeatureWriter):

    def write(self, appVersion="0.0", testMode=False):
        if testMode:
            notes = []
        else:
            notes = [
                "# Class Kerning Data Generated by MetricsMachine Extension %s" % appVersion,
                u"# UFO: %s" % self.font.path,
                "# Date: %s" % time.strftime("%A %B %d, %Y %H:%M:%S"),
                ""
            ]
        notes = u"\n".join(notes)
        return super(BasicFeatureWriter, self).write(notes)

    def getReferencedGroups(self):
        left = {}
        right = {}
        for groupName, glyphList in self.font.groups.items():
            if groupName.startswith(side1Prefix):
                left[groupName] = set(glyphList)
            elif groupName.startswith(side2Prefix):
                right[groupName] = set(glyphList)
        return left, right

    def getUnreferencedGroups(self):
        return {}, {}


class SubtableBreakWriter(BasicFeatureWriter):

    def write(self, appVersion, testMode=False):
        font = self.font

        if testMode:
            notes = []
        else:
            notes = [
                "# Class Kerning Data Generated by MetricsMachine %s" % appVersion,
                u"# UFO: %s" % self.font.path,
                "# Date: %s" % time.strftime("%A %B %m, %Y %H:%M:%S"),
                ""
            ]
        notes = u"\n".join(notes)

        # break the pairs up by type
        # this will also decompose all special exceptions
        glyphGlyph, glyphGroupDecomposed, groupGlyphDecomposed, glyphGroup, groupGlyph, groupGroup = self.getSeparatedPairs(self.pairs)

        groups = dict(self.side1Groups)
        groups.update(self.side2Groups)

        # make lists of all referenced pair members
        allPairs = list(glyphGlyph.keys()) + \
                   list(glyphGroupDecomposed.keys()) + \
                   list(groupGlyphDecomposed.keys()) + \
                   list(glyphGroup.keys()) + \
                   list(groupGlyph.keys()) + \
                   list(groupGroup.keys())
        neededGlyphs = set()
        neededGroups = set()
        for left, right in allPairs:
            # break the left and right into a list of all members
            if isinstance(left, inlineGroupInstance):
                pass
            elif left.startswith(side1FeaPrefix):
                left = set([left]) | set(groups[left])
            else:
                left = [left]
            if isinstance(right, inlineGroupInstance):
                pass
            elif right.startswith(side2FeaPrefix):
                right = set([right]) | set(groups[right])
            else:
                right = [right]
            for i in set(left) | set(right):
                if i.startswith(side1FeaPrefix):
                    neededGroups.add(i)
                elif i.startswith(side2FeaPrefix):
                    neededGroups.add(i)
                else:
                    neededGlyphs.add(i)

        # figure out the script for all pair members
        glyphToScript = {}
        groupToScript = {}
        for glyphName in neededGlyphs:
            script = font.unicodeData.scriptForGlyphName(glyphName)
            glyphToScript[glyphName] = script
        for groupName in neededGroups:
            groupToScript[groupName] = set()
            for glyphName in groups[groupName]:
                script = glyphToScript[glyphName]
                groupToScript[groupName].add(script)
        # break groups into script subdivisions
        newGroups, oldGroupNameToNewGroupNames, newGroupNameToOldGroupName = self.getScriptDividedGroups(groupToScript, glyphToScript, groups)

        leftIsGlyphPairs = {}
        scriptSeparatedPairs = {}
        order = [
            ("# glyph, glyph", glyphGlyph),
            ("# glyph, group exceptions", glyphGroupDecomposed),
            ("# group exceptions, glyph", groupGlyphDecomposed),
            ("# glyph, group", glyphGroup),
            ("# group, glyph", groupGlyph),
            ("# group, group", groupGroup),
        ]
        for note, pairs in order:
            for (left, right), value in pairs.items():
                # rename right as needed
                if not isinstance(right, inlineGroupInstance) and right in oldGroupNameToNewGroupNames:
                    right = oldGroupNameToNewGroupNames[right]
                else:
                    right = [right]
                # catch lefts that are not groups
                # XXX these could be separated into script divisions as well.
                if isinstance(left, inlineGroupInstance):
                    if note not in leftIsGlyphPairs:
                        leftIsGlyphPairs[note] = {}
                    for r in right:
                        leftIsGlyphPairs[note][left, r] = value
                    continue
                elif not left.startswith(side1FeaPrefix):
                    if note not in leftIsGlyphPairs:
                        leftIsGlyphPairs[note] = {}
                    for r in right:
                        leftIsGlyphPairs[note][left, r] = value
                    continue
                # any left from here on is a group
                if left in oldGroupNameToNewGroupNames:
                    left = oldGroupNameToNewGroupNames[left]
                else:
                    left = [left]
                for l in left:
                    script = groupToScript[l]
                    assert len(script) == 1
                    script = list(script)[0]
                    if script not in scriptSeparatedPairs:
                        scriptSeparatedPairs[script] = {}
                    if note not in scriptSeparatedPairs[script]:
                        scriptSeparatedPairs[script][note] = {}

                    for r in right:
                        scriptSeparatedPairs[script][note][l, r] = value

        # write the classes
        classes = []
        skipped = set()
        for groupName in sorted(neededGroups):
            if groupName in oldGroupNameToNewGroupNames:
                skipped = skipped | set(oldGroupNameToNewGroupNames[groupName])
            elif groupName in newGroupNameToOldGroupName:
                skipped.add(groupName)
            else:
                group = newGroups[groupName]
                line = "%s = [%s];" % (groupName, " ".join(sorted(group)))
                classes.append(line)
        written = set()
        for groupName in sorted(skipped):
            if groupName in written:
                continue
            oldName = newGroupNameToOldGroupName[groupName]
            classes.append("# script subdivisions from %s" % oldName)
            for newName in sorted(oldGroupNameToNewGroupNames[oldName]):
                group = newGroups[newName]
                line = "%s = [%s];" % (newName, " ".join(sorted(group)))
                classes.append(line)
                written.add(newName)

        # write the rules
        order = [tag for tag, l in order]
        rules = []
        for note in order:
            if note not in leftIsGlyphPairs:
                continue
            rules.append("")
            rules.append(note)
            rules += self.getFeatureRulesForPairs(leftIsGlyphPairs[note])
        if leftIsGlyphPairs and scriptSeparatedPairs:
            rules.append("")
            rules.append("subtable;")
        for index, (script, groupedPairs) in enumerate(sorted(scriptSeparatedPairs.items())):
            rules.append("")
            rules.append("# %s" % ("-" * len(script)))
            rules.append("# %s" % script)
            rules.append("# %s" % ("-" * len(script)))
            for note in order:
                if note not in groupedPairs:
                    continue
                rules.append("")
                rules.append(note)
                rules += self.getFeatureRulesForPairs(groupedPairs[note])
            if index < len(scriptSeparatedPairs) - 1:
                rules.append("")
                rules.append("subtable;")

        # compile
        feature = []
        for line in classes + rules:
            if line:
                line = "    " + line
            feature.append(line)
        feature = ["feature kern {", notes] + feature + ["} kern;"]
        return "\n".join(feature)

    def getScriptDividedGroups(self, groupToScript, glyphToScript, groups):
        newGroups = {}
        oldGroupNameToNewGroupNames = {}
        newGroupNameToOldGroupName = {}
        renameCounter = 0
        for groupName, scriptList in sorted(groupToScript.items()):
            # only one script. no need to rename.
            if len(scriptList) == 1:
                newGroups[groupName] = set(groups[groupName])
                continue
            renameCounter += 1
            # create the new group names and groups
            if groupName.startswith(side1FeaPrefix):
                baseName = "%sSplit%d_" % (side1FeaPrefix, renameCounter)
            elif groupName.startswith(side2FeaPrefix):
                baseName = "%sSplit%d_" % (side2FeaPrefix, renameCounter)
            else:
                continue
            newGroupNames = [baseName + script for script in scriptList]
            oldGroupNameToNewGroupNames[groupName] = newGroupNames
            for newGroupName in newGroupNames:
                newGroups[newGroupName] = set()
            # add the glyphs to the groups
            for glyphName in groups[groupName]:
                script = glyphToScript[glyphName]
                newGroups[baseName + script].add(glyphName)
            # update the group to script map
            del groupToScript[groupName]
            for script in scriptList:
                groupToScript[baseName + script] = [script]
                newGroupNameToOldGroupName[baseName + script] = groupName
        return newGroups, oldGroupNameToNewGroupNames, newGroupNameToOldGroupName


# -----
# Tests
# -----


def _setupTestFont(path=None):
    from fontTools.agl import AGL2UV
    import mm4.objects
    from defcon import Font
    font = Font()
    for i, v in AGL2UV.items():
        glyph = font.newGlyph(i)
        glyph.unicode = v
    return font


def _setupTestFontForFeatureSubtable():
    from fontTools.agl import AGL2UV
    import mm4.objects
    from defcon import Font

    neededGlyphs = "a alpha afii10017 afii57409 period".split(" ")

    kerning = {
        ("a", "a"): 1,
        ("alpha", "alpha"): 2,
        ("afii10017", "afii10017"): 3,
        ("afii57409", "afii57409"): 4,

        ("a", "period"): 1,
        ("alpha", "period"): 2,
        ("afii10017", "period"): 3,
        ("afii57409", "period"): 4,

        ("period", "a"): 1,
        ("period", "alpha"): 2,
        ("period", "afii10017"): 3,
        ("period", "afii57409"): 4,

        ("public.kern1.a", "public.kern2.a"): -1,
        ("public.kern1.period", "public.kern2.a"): -1,
        ("public.kern1.a", "public.kern2.period"): -1,
    }

    groups = {
        "public.kern1.a": ["a", "a.alt", "alpha"],
        "public.kern2.a": ["a", "a.alt", "alpha"],
        "public.kern1.period": ["period", "period.alt"],
        "public.kern2.period": ["period", "period.alt"],
    }

    font = Font()
    for glyphName in neededGlyphs:
        glyph = font.newGlyph(glyphName)
        if glyphName in AGL2UV:
            glyph.unicode = AGL2UV[glyphName]
    font.groups.update(groups)
    font.kerning.update(kerning)
    return font


def _setupTestFontForCopy():
    from fontTools.agl import AGL2UV
    import mm4.objects
    from defcon import Font
    font = Font()
    for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        glyph = font.newGlyph(i)
        glyph.unicode = AGL2UV[i]
        font.newGlyph(i + ".sc")
    return font


_importFeaTestText = """
feature kern {
    @kern1.A = [A Aacute Agrave];
    @kern1.D = [D];
    @kern2.A = [A Aacute Agrave];
    @kern2.D = [D];

    # glyph, glyph
    pos Agrave Agrave -100;

    # glyph, group exceptions
    enum pos eight [B eight] -49;

    # group, glyph exceptions
    enum pos [A Aacute] Agrave -75;
    enum pos [A Aacute Agrave] Aacute -74;

    # glyph, group
    pos X @kern2.D -25;

    # group, glyph
    pos @kern1.D X -25;

    # group, group
    pos @kern1.A @kern2.A -25;
} kern;
"""

_expectedFeatureText1 = """feature kern {
    @kern1.A = [A Aacute Agrave];
    @kern1.B = [B eight];
    @kern1.D = [D];
    @kern2.A = [A Aacute Agrave];
    @kern2.B = [B eight];
    @kern2.D = [D];

    # glyph, glyph
    pos Agrave Agrave -100;

    # glyph, group exceptions
    enum pos eight [B eight] -49;

    # group exceptions, glyph
    enum pos [A Aacute] Agrave -75;
    enum pos [A Aacute Agrave] Aacute -74;

    # glyph, group
    pos X @kern2.D -25;

    # group, glyph
    pos @kern1.D X -25;

    # group, group
    pos @kern1.A @kern2.A -25;
} kern;"""

_expectedFeatureText2 = """feature kern {

    @kern1.A = [A Aacute Agrave];
    @kern1.D = [D];
    @kern2.A = [A Aacute Agrave];
    @kern2.D = [D];

    # glyph, glyph
    pos Agrave Agrave -100;

    # glyph, group exceptions
    enum pos eight [B eight] -49;

    # group exceptions, glyph
    enum pos [A Aacute] Agrave -75;
    enum pos [A Aacute Agrave] Aacute -74;

    # glyph, group
    pos X @kern2.D -25;

    subtable;

    # -----
    # Latin
    # -----

    # group, glyph
    pos @kern1.D X -25;

    # group, group
    pos @kern1.A @kern2.A -25;
} kern;"""

_expectedFeatureText3 = """feature kern {

    @kern1.period = [period];
    @kern2.period = [period];
    # script subdivisions from @kern1.a
    @kern1.Split1_Greek = [alpha];
    @kern1.Split1_Latin = [a];
    # script subdivisions from @kern2.a
    @kern2.Split2_Greek = [alpha];
    @kern2.Split2_Latin = [a];

    # glyph, glyph
    pos a a 1;
    pos a period 1;
    pos afii10017 afii10017 3;
    pos afii10017 period 3;
    pos afii57409 afii57409 4;
    pos afii57409 period 4;
    pos alpha alpha 2;
    pos alpha period 2;
    pos period a 1;
    pos period afii10017 3;
    pos period afii57409 4;
    pos period alpha 2;

    subtable;

    # ------
    # Common
    # ------

    # group, group
    pos @kern1.period @kern2.Split2_Greek -1;
    pos @kern1.period @kern2.Split2_Latin -1;

    subtable;

    # -----
    # Greek
    # -----

    # group, group
    pos @kern1.Split1_Greek @kern2.Split2_Greek -1;
    pos @kern1.Split1_Greek @kern2.Split2_Latin -1;
    pos @kern1.Split1_Greek @kern2.period -1;

    subtable;

    # -----
    # Latin
    # -----

    # group, group
    pos @kern1.Split1_Latin @kern2.Split2_Greek -1;
    pos @kern1.Split1_Latin @kern2.Split2_Latin -1;
    pos @kern1.Split1_Latin @kern2.period -1;
} kern;"""

_expectedAFMText = """Comment exported from MetricsMachine Extension 0.0
FontName None
FullName None
FamilyName None
ItalicAngle None
FontBBox 0 0 0 0
Version 001.000
Notice None
EncodingScheme AdobeStandardEncoding
CapHeight None
XHeight None
Ascender None
Descender None
StartCharMetrics 2
C 65 ; WX 0 ; N A ; B 0 0 0 0 ;
C 66 ; WX 0 ; N B ; B 0 0 0 0 ;
EndCharMetrics
StartKernData
StartKernPairs 2
KPX A A -100
KPX A B -100
EndKernPairs
EndKernData
EndFontMetrics
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()
