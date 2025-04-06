pageList = """
#KPL:M: Page List

a a
b c
endcolumn

q r
blankline
endpage
"""


def parsePairList(text, font):
    """
    >>> font = _setupTestFont()
    >>> parsePairList(_pairTest, font)
    ([(('a', 'b'), None), (('c', 'd'), None), (('one', 'two'), None)], 'pair', 'Pair Test')
    >>> parsePairList(_wordTest, font)
    ([(('u', 'r'), (['h', 'a', 'm', 'b', 'u'], ['r', 'g', 'e', 'f', 'o', 'n', 't', 's'])), (('three', 'four'), (['one', 'two', 'three'], ['four', 'five', 'six'])), (('c', 'eth'), (['a', 'b', 'c'], ['eth', 'aacute']))], 'word', 'Word Test')

    >>> parsePairList(_pairTestError, font)
    'The file contains invalid syntax on lines 1 and 3.'
    >>> parsePairList(_wordTestError, font)
    'The file contains invalid syntax on lines 1 and 3.'
    """
    text = text.strip()
    lines = text.splitlines()
    if not lines:
        return False

    mode = None
    firstLine = lines[0].strip()
    if firstLine.startswith("#KPL:W:"):
        mode = "word"
    elif firstLine.startswith("#KPL:P:"):
        mode = "pair"
    # elif firstLine.startswith("#KPL:MW:"):
    #     mode = "multiple word"
    # elif firstLine.startswith("#KPL:MP:"):
    #     mode = "multiple pair"
    if mode is None:
        return "Unknown file mode."
    title = firstLine[1:].split(" ", 1)[1]

    pairs = []
    errors = []
    for lineIndex, line in enumerate(lines):
        # skip the first
        if lineIndex == 0:
            continue
        # skip blank lines
        line = line.strip()
        if not line:
            continue
        # skip comments
        if line.startswith("#"):
            continue
        # word mode
        if mode == "word":
            if line.count(" ") != 1:
                errors.append(lineIndex)
            else:
                pairs.append(_parseLineWord(line, font))
        # pair mode
        elif mode == "pair":
            if line.count(" ") != 1:
                errors.append(lineIndex)
            else:
                pairs.append(_parseLinePair(line))
    if errors:
        if len(errors) == 1:
            message = "The file contains invalid syntax on line %d." % errors[0]
        else:
            s = "%s and %d" % (", ".join([str(i) for i in errors[:-1]]), errors[-1])
            message = "The file contains invalid syntax on lines %s." % s
        return message

    return pairs, mode, title


def _purge(l):
    return [i for i in l if i]


def _charactersToNames(l, font):
    cmap = font.unicodeData
    result = []
    for i in l:
        i = ord(i)
        if i in cmap:
            name = cmap[i][0]
            result.append(name)
    return result


def _parseLineWord(line, font):
    if line.startswith("/"):
        left, right = line.split(" ")
        left = _purge(left.split("/"))
        right = _purge(right.split("/"))
    else:
        left, right = line.split(" ")
        left = _charactersToNames(left, font)
        right = _charactersToNames(right, font)
    return ((left[-1], right[0]), (left, right))


def _parseLinePair(line):
    left, right = line.split()
    left = left.strip()
    right = right.strip()
    return ((left, right), None)


_pairTest = """
#KPL:P: Pair Test
a b
c d
one two
"""

_pairTestError = """
#KPL:P: Pair Test
a b c
c d
one
"""

_wordTest = """
#KPL:W: Word Test
hambu rgefonts
123 456
/a/b/c /eth/aacute
"""

_wordTestError = """
#KPL:W: Word Test
hambu rgefonts iv
123 456
/a/b/c/eth/aacute
"""


def _setupTestFont():
    from fontTools.agl import AGL2UV
    from defcon import Font
    font = Font()
    for i, v in AGL2UV.items():
        font.newGlyph(i)
        if isinstance(v, list):
            v = v[0]
        glyph = font[i]
        glyph.unicode = v
    return font


if __name__ == "__main__":
    import doctest
    doctest.testmod()
