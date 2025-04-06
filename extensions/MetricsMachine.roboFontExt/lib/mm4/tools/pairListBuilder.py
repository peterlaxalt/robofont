def _makePairDict(left, right, **kwargs):
    d = dict(
        base=(left, right),
        baseOpenClose1=None,
        baseOpenClose2=None,
        baseCloseOpen1=None,
        baseCloseOpen2=None,
        flipped=None,
        flippedOpenClose1=None,
        flippedOpenClose2=None,
        flippedCloseOpen1=None,
        flippedCloseOpen2=None,
    )
    for key in list(d.keys()):
        d[key + "Compressed"] = False
    for k, v in kwargs.items():
        d[k] = v
    return d


_pairOrder = [
    "base",
    "baseOpenClose1",
    "baseOpenClose2",
    "baseCloseOpen1",
    "baseCloseOpen2",
    "flipped",
    "flippedOpenClose1",
    "flippedOpenClose2",
    "flippedCloseOpen1",
    "flippedCloseOpen2",
]


def createPairs(leftGlyphs, rightGlyphs, font=None,
        createFlipped=False, createOpenClose=False, createCloseOpen=False,
        compressGroups=False, avoidDuplicates=False, existingPairs=[]):
    pairs = []
    for left in leftGlyphs:
        for right in rightGlyphs:
            pairDict = _makePairDict(left, right)
            # flipped
            if createFlipped:
                _createFlipped(pairDict)
            # open, close
            if createOpenClose:
                _createOpenClose(pairDict, font)
            # close, open
            if createCloseOpen:
                _createCloseOpen(pairDict, font)
            pairs.append(pairDict)
    # compress groups
    if compressGroups:
        _compressGroupsInPairs(pairs, font)
        _filterGroupCompressedPairs(pairs)
    # avoid duplicates
    if avoidDuplicates:
        _filterDuplicates(pairs, existingPairs)
    # flatten
    pairs = _flattenPairs(pairs)
    # done
    return pairs


def _createFlipped(pairDict):
    """
    >>> pair = _makePairDict("A", "B")
    >>> _createFlipped(pair)
    >>> pair["flipped"]
    ('B', 'A')
    """
    left, right = pairDict["base"]
    pairDict["flipped"] = (right, left)


def _createOpenClose(pairDict, font):
    """
    >>> font = _setupTestFont()

    >>> pair = _makePairDict("parenleft", "A")
    >>> _createOpenClose(pair, font)
    >>> pair["baseOpenClose1"]
    ('A', 'parenright')
    >>> pair["baseOpenClose2"]

    >>> pair = _makePairDict("A", "parenright")
    >>> _createOpenClose(pair, font)
    >>> pair["baseOpenClose1"]
    >>> pair["baseOpenClose2"]
    ('parenleft', 'A')

    >>> pair = _makePairDict("A", "parenleft")
    >>> _createOpenClose(pair, font)
    >>> pair["baseOpenClose1"]
    >>> pair["baseOpenClose2"]

    >>> pair = _makePairDict("parenright", "A")
    >>> _createOpenClose(pair, font)
    >>> pair["baseOpenClose1"]
    >>> pair["baseOpenClose2"]
    """
    for key in ("base", "flipped"):
        pair = pairDict[key]
        if pair is None:
            continue
        left, right = pair
        leftClose = font.unicodeData.closeRelativeForGlyphName(left)
        if leftClose is not None:
            pairDict[key + "OpenClose1"] = (right, leftClose)
        rightOpen = font.unicodeData.openRelativeForGlyphName(right)
        if rightOpen is not None:
            pairDict[key + "OpenClose2"] = (rightOpen, left)


def _createCloseOpen(pairDict, font):
    """
    >>> font = _setupTestFont()

    >>> pair = _makePairDict("A", "parenright")
    >>> _createCloseOpen(pair, font)
    >>> pair["baseCloseOpen1"]
    >>> pair["baseCloseOpen2"]
    ('A', 'parenleft')

    >>> pair = _makePairDict("parenleft", "A")
    >>> _createCloseOpen(pair, font)
    >>> pair["baseCloseOpen1"]
    ('parenright', 'A')
    >>> pair["baseCloseOpen2"]

    >>> pair = _makePairDict("A", "parenleft")
    >>> _createCloseOpen(pair, font)
    >>> pair["baseCloseOpen1"]
    >>> pair["baseCloseOpen2"]

    >>> pair = _makePairDict("parenright", "A")
    >>> _createCloseOpen(pair, font)
    >>> pair["baseCloseOpen1"]
    >>> pair["baseCloseOpen2"]
    """
    for key in ("base", "flipped"):
        pair = pairDict[key]
        if pair is None:
            continue
        left, right = pair
        leftClose = font.unicodeData.closeRelativeForGlyphName(left)
        if leftClose is not None:
            pairDict[key + "CloseOpen1"] = (leftClose, right)
        rightOpen = font.unicodeData.openRelativeForGlyphName(right)
        if rightOpen is not None:
            pairDict[key + "CloseOpen2"] = (left, rightOpen)


def _compressGroupsInPairs(pairs, font):
    """
    >>> pairs = [
    ...     _makePairDict("Aacute", "Egrave"),
    ...     _makePairDict("Aacute", "E"),
    ...     _makePairDict("A", "Egrave"),
    ...     _makePairDict("A", "B"),
    ...     _makePairDict("D", "C"),
    ... ]
    >>> font = _setupTestFont()
    >>> _compressGroupsInPairs(pairs, font)
    >>> pairs[0]["base"], pairs[0]["baseCompressed"]
    (('A', 'B'), True)
    >>> pairs[1]["base"], pairs[1]["baseCompressed"]
    (('A', 'B'), True)
    >>> pairs[2]["base"], pairs[2]["baseCompressed"]
    (('A', 'B'), True)
    >>> pairs[3]["base"], pairs[3]["baseCompressed"]
    (('A', 'B'), False)
    >>> pairs[4]["base"], pairs[4]["baseCompressed"]
    (('D', 'C'), False)
    """
    groups = font.groups
    # gather references
    leftReferences = set()
    rightReferences = set()
    for pairDict in pairs:
        for key, pair in pairDict.items():
            if key.endswith("Compressed"):
                continue
            if pair is None:
                continue
            left, right = pair
            leftReferences.add(left)
            rightReferences.add(right)
    # find group representatives
    leftRepresentatives = {}
    representatives = {}
    for glyph in leftReferences:
        group = groups.metricsMachine.getSide1GroupForGlyph(glyph)
        if group is not None and group not in representatives:
            representative = groups.metricsMachine.getRepresentativeForGroup(group)
            # only use the representative if it is in the source glyphs
            if representative in leftReferences:
                representatives[group] = representative
        leftRepresentatives[glyph] = representatives.get(group, glyph)
    rightRepresentatives = {}
    representatives = {}
    for glyph in rightReferences:
        group = groups.metricsMachine.getSide2GroupForGlyph(glyph)
        if group is not None and group not in representatives:
            representative = groups.metricsMachine.getRepresentativeForGroup(group)
            # only use the representative if it is in the source glyphs
            if representative in rightReferences:
                representatives[group] = representative
        rightRepresentatives[glyph] = representatives.get(group, glyph)
    # compress pairs
    for pairDict in pairs:
        for key, pair in pairDict.items():
            if key.endswith("Compressed"):
                continue
            if pair is None:
                continue
            compressed = False
            left, right = pair
            if leftRepresentatives[left] != left:
                left = leftRepresentatives[left]
                compressed = True
            if rightRepresentatives[right] != right:
                right = rightRepresentatives[right]
                compressed = True
            if compressed:
                pairDict[key] = (left, right)
                pairDict[key + "Compressed"] = True


def _filterGroupCompressedPairs(pairs):
    """
    >>> pairs = [
    ...     _makePairDict("A", "B", baseCompressed=True),
    ...     _makePairDict("D", "C", baseCompressed=False),
    ...     _makePairDict("A", "B", baseCompressed=False),
    ...     _makePairDict("A", "A", baseCompressed=True),
    ...     _makePairDict("A", "A", baseCompressed=True),
    ...     _makePairDict("A", "A", baseCompressed=True),
    ... ]
    >>> _filterGroupCompressedPairs(pairs)
    >>> pairs[0]["base"]
    >>> pairs[1]["base"]
    ('D', 'C')
    >>> pairs[2]["base"]
    ('A', 'B')
    >>> pairs[3]["base"]
    ('A', 'A')
    >>> pairs[4]["base"]
    >>> pairs[5]["base"]
    """
    # find uncompressed pairs
    uncompressed = set()
    for pairDict in pairs:
        for key, pair in pairDict.items():
            if key.endswith("Compressed"):
                continue
            if pair is None:
                continue
            if pairDict[key + "Compressed"]:
                continue
            uncompressed.add(pair)
    # remove compressed pairs
    compressed = set()
    for pairDict in pairs:
        for key in _pairOrder:
            pair = pairDict[key]
            if key.endswith("Compressed"):
                continue
            if pair is None:
                continue
            if pairDict[key + "Compressed"]:
                if pair in uncompressed:
                    pairDict[key] = None
                # remove compressed pairs for which the
                # base pair does not appear
                elif pair in compressed:
                    pairDict[key] = None
                else:
                    compressed.add(pair)


def _filterDuplicates(pairs, existing):
    """
    >>> pairs = [
    ...     _makePairDict("A", "E"),
    ...     _makePairDict("D", "C"),
    ...     _makePairDict("A", "E"),
    ...     _makePairDict("C", "D"),
    ... ]
    >>> existing = [("D", "C")]
    >>> _filterDuplicates(pairs, existing)
    >>> pairs[0]["base"]
    ('A', 'E')
    >>> pairs[1]["base"]
    >>> pairs[2]["base"]
    >>> pairs[3]["base"]
    ('C', 'D')
    """
    existing = set(existing)
    seen = set()
    for pairDict in pairs:
        for key, pair in pairDict.items():
            if key.endswith("Compressed"):
                continue
            if pair is None:
                continue
            if pair in existing or pair in seen:
                pairDict[key] = None
            else:
                seen.add(pair)


def _flattenPairs(pairs):
    """
    >>> pairs = [
    ...     _makePairDict(
    ...         "Z", "Y", flipped=("A", "B"),
    ...         baseOpenClose1=("C", "D"), baseOpenClose2=("E", "F"),
    ...         baseCloseOpen1=("G", "H"), baseCloseOpen2=("I", "J"),
    ...         flippedOpenClose1=("K", "L"), flippedOpenClose2=("M", "N"),
    ...         flippedCloseOpen1=("O", "P"), flippedCloseOpen2=("Q", "R"),
    ...     )
    ... ]
    >>> _flattenPairs(pairs)
    [('Z', 'Y'), ('C', 'D'), ('E', 'F'), ('G', 'H'), ('I', 'J'), ('A', 'B'), ('K', 'L'), ('M', 'N'), ('O', 'P'), ('Q', 'R')]
    """
    flattened = []
    for pairDict in pairs:
        for key in _pairOrder:
            pair = pairDict[key]
            if pair is not None:
                flattened.append(pair)
    return flattened


# ----
# Test
# ----

def _setupTestFont():
    import mm4.objects
    from defcon import Font
    from fontTools.agl import AGL2UV
    font = Font()
    glyphNames = "A Aacute B C D E Egrave parenleft parenright".split(" ")
    for glyphName in glyphNames:
        glyph = font.newGlyph(glyphName)
        glyph.unicode = AGL2UV[glyphName]
    groups = {
        "public.kern1.A": ["A", "Aacute"],
        "public.kern2.A": ["A", "Aacute"],
        "public.kern1.B": ["B"],
        "public.kern2.B": ["B", "D", "E", "Egrave"],
        "Uppercase": ["A", "Aacute", "B"],
    }
    font.groups.update(groups)
    return font


if __name__ == "__main__":
    import doctest
    doctest.testmod()
