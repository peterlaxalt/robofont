import fnmatch
from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix

"""
operators
    and
    or
    not

kerning pair variables
    exception
    all
    group
    glyph

objects
    glyphName
        * = any number of anything
        ? = 1 of anything
    groupName
        [] = group indicator
        * = any number of anything
        ? = 1 of anything
    groupLookup
        {} = group lookup indicator
        * = any number of anything
        ? = 1 of anything
    referenceGroupName
        () = reference group indicator
        * = any number of anything
        ? = 1 of anything

separator
    , = pair break

"""


# ----------
# Validators
# ----------

def isValidExpression(expression, allowGroups=False, allowReferenceGroups=False):
    if not expression.strip():
        return False
    expression = _tokenize(expression)
    if expression is None:
        return False
    for e in expression:
        tp = e["type"]
        validType = False
        if allowGroups and tp in ("groupName", "groupLookup"):
            validType = True
        elif allowReferenceGroups and tp == "referenceGroupName":
            validType = True
        elif tp == "glyphName":
            validType = True
        if not validType:
            return False
    return True


def isValidKerningExpression(expression, allowGroups=True, allowVariables=True):
    if not expression.strip():
        return False
    # split into sides
    sides, partCount = _splitKerningExpression(expression)
    if sides is None:
        return False
    # tokenize each side
    expression = []
    for side in sides:
        e = _tokenize(side)
        # bad expression
        if not e:
            return False
        expression += e
    # nothing to evaluate
    if not expression:
        return False
    # evaluate tokenized
    for e in expression:
        tp = e["type"]
        if tp == "groupName" and not allowGroups:
            return False
        elif tp == "groupLookup" and not allowGroups:
            return False
        elif tp == "variable" and not allowVariables:
            return False
    return True


# ----------
# Glyph List
# ----------

def searchGlyphList(expression, glyphList, groups=None, expandGroups=False):
    allowGroups = groups is not None
    if allowGroups:
        return _evaluateGlyphExpression(expression, glyphList, groups=groups, expandGroups=expandGroups)
    else:
        return _evaluateGlyphExpression(expression, glyphList)


def expressionMatchesGlyphName(expression, glyphName, groups):
    return bool(searchGlyphList(expression, [glyphName], groups=groups))

# ------------
# Kerning List
# ------------


def searchKerningPairList(expression, pairList, font, allowVariables=True):
    return _evaluateKerningExpression(expression, pairList, font, allowVariables)


def createGlyphListFromPairList(expression, pairList, font, side):
    sides, count = _splitKerningExpression(expression)
    if sides is None:
        return []
    sideIndex = side == "side2"
    expression = sides[sideIndex]
    expression = _tokenize(expression)
    result = None
    for subExpression in expression:
        tp = subExpression["type"]
        operator = subExpression["operator"]
        # expand
        v = None
        if tp == "variable":
            pattern = subExpression["pattern"]
            kerning = font.kerning
            if pattern == "all":
                v = set(list(font.keys()) + [i for i in font.groups.keys() if i.startswith("public.kern")])
            elif pattern == "glyph":
                v = set(font.keys())
            elif pattern == "group":
                v = set([i for i in font.groups.keys() if i.startswith("public.kern")])
            elif pattern == "exception":
                v = set([pair[sideIndex] for pair in pairList if kerning.getPairType(pair)[sideIndex] == "exception"])
        elif tp == "glyphName":
            v = _expandGlyphName(subExpression, font.keys())
        elif tp == "groupName":
            v = _expandGroupName(subExpression, font.groups)
        elif tp == "groupLookup":
            v = _expandGroupLookup(subExpression, font.groups)
        elif tp == "referenceGroupName":
            v = _expandReferenceGroupName(subExpression, font.groups)
            e = set([])
            for groupName in v:
                e = e | set(font.groups.metricsMachine.getReferenceGroup(groupName))
            v = e
        # handle the operator
        result = _handleOperator(operator, result, v)
    if result is None:
        result = set([])
    return list(result)

# --------
# Internal
# --------

# pair splitter


def _splitKerningExpression(expression):
    """
    >>> _splitKerningExpression("a, b")
    (('a', 'b'), 2)
    >>> _splitKerningExpression("a")
    (('a', 'a'), 1)
    >>> _splitKerningExpression("a, a, a")
    (None, 0)
    """
    parts = []
    current = []
    inReferenceGroup = False
    for c in expression.strip():
        if c == "(":
            inReferenceGroup = True
        elif c == ")":
            inReferenceGroup = False
        elif c == "," and not inReferenceGroup:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(c)
    parts.append("".join(current).strip())
    if len(parts) == 0 or len(parts) > 2:
        return None, 0
    elif len(parts) == 1:
        return (parts[0], parts[0]), 1
    else:
        return (parts[0], parts[1]), 2


# tokenizer

_operators = set("and or not".split(" "))
_variables = set("exception all group glyph".split(" "))


def _tokenize(text):
    """
    # nothing
    >>> _tokenize("")
    []

    # glyph name
    >>> _testPrint(_tokenize("a"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'glyphName')]]

    # group name
    >>> _testPrint(_tokenize("[a]"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'groupName')]]
    >>> _testPrint(_tokenize("[a"))
    [[('groupPrefix', 'public.kern2.'), ('operator', None), ('pattern', 'a'), ('type', 'groupName')]]
    >>> _testPrint(_tokenize("a]"))
    [[('groupPrefix', 'public.kern1.'), ('operator', None), ('pattern', 'a'), ('type', 'groupName')]]
    >>> _tokenize("[]")

    # group lookup
    >>> _testPrint(_tokenize("{a}"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'groupLookup')]]
    >>> _testPrint(_tokenize("{a"))
    [[('groupPrefix', 'public.kern2.'), ('operator', None), ('pattern', 'a'), ('type', 'groupLookup')]]
    >>> _testPrint(_tokenize("a}"))
    [[('groupPrefix', 'public.kern1.'), ('operator', None), ('pattern', 'a'), ('type', 'groupLookup')]]
    >>> _tokenize("{}")

    # reference group name
    >>> _testPrint(_tokenize("(a)"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'referenceGroupName')]]
    >>> _tokenize("()")
    >>> _tokenize("(public.kern)")

    # variables
    >>> _testPrint(_tokenize("all"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'all'), ('type', 'variable')]]

    >>> _testPrint(_tokenize("exception"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'exception'), ('type', 'variable')]]

    >>> _testPrint(_tokenize("group"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'group'), ('type', 'variable')]]

    >>> _testPrint(_tokenize("glyph"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'glyph'), ('type', 'variable')]]

    # operators
    >>> _testPrint(_tokenize("a not a"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'glyphName')], [('groupPrefix', None), ('operator', 'not'), ('pattern', 'a'), ('type', 'glyphName')]]
    >>> _testPrint(_tokenize("a or a"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'glyphName')], [('groupPrefix', None), ('operator', 'or'), ('pattern', 'a'), ('type', 'glyphName')]]
    >>> _testPrint(_tokenize("a and a"))
    [[('groupPrefix', None), ('operator', None), ('pattern', 'a'), ('type', 'glyphName')], [('groupPrefix', None), ('operator', 'and'), ('pattern', 'a'), ('type', 'glyphName')]]

    >>> _tokenize("not a")
    >>> _tokenize("or a")
    >>> _tokenize("and a")

    >>> _tokenize("a not not a")
    >>> _tokenize("a or or a")
    >>> _tokenize("a and and a")

    >>> _tokenize("a a")

    >>> _tokenize("[ab}")
    >>> _tokenize("{ab]")
    >>> _tokenize("(ab")
    >>> _tokenize("ab)")
    >>> _tokenize("[ab)")
    >>> _tokenize("(ab]")
    >>> _tokenize("(ab[")
    >>> _tokenize("{ab)")
    >>> _tokenize("(ab}")
    >>> _tokenize("(ab{")
    >>> _tokenize("(ab(")
    """
    text = text.strip()
    if not text:
        return []

    parts = []
    current = []
    inReferenceGroup = False
    for c in text:
        if c == "(":
            inReferenceGroup = True
        elif c == ")":
            inReferenceGroup = False
        elif c == " " and not inReferenceGroup:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(c)
    parts.append("".join(current).strip())

    members = []
    operator = None
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part in _operators:
            # double operator
            if operator is not None:
                return None
            operator = part
        else:
            members.append((operator, part))
            operator = None
    # operator at the end
    if operator is not None:
        return None
    expression = []
    for operator, pattern in members:
        groupPrefix = None
        # unbalanced tokens
        unbalanced = [
            ("{", "]"),
            ("{", ")"),
            ("[", "}"),
            ("[", ")"),
            ("(", "}"),
            ("(", "{"),
            ("(", "]"),
            ("(", "["),
            ("(", "("),
        ]
        for l, r in unbalanced:
            if pattern.startswith(l) and pattern.endswith(r):
                return None
        # work through
        if pattern in _variables:
            tp = "variable"
        elif pattern.startswith("[") or pattern.endswith("]"):
            tp = "groupName"
            # determine side
            if not pattern.startswith("["):
                groupPrefix = "public.kern1."
            elif not pattern.endswith("]"):
                groupPrefix = "public.kern2."
            # strip []
            pattern = pattern.replace("[", "").replace("]", "")
            if not pattern:
                return None
        elif pattern.startswith("{") or pattern.endswith("}"):
            tp = "groupLookup"
            # determine side
            if not pattern.startswith("{"):
                groupPrefix = "public.kern1."
            elif not pattern.endswith("}"):
                groupPrefix = "public.kern2."
            # strip {}
            pattern = pattern.replace("{", "").replace("}", "")
            if not pattern:
                return None
        elif pattern.startswith("(") or pattern.endswith(")"):
            tp = "referenceGroupName"
            # unbalanced ()
            if not pattern.startswith("(") and pattern.endswith(")"):
                return None
            if pattern.startswith("(") and not pattern.endswith(")"):
                return None
            # strip ()
            pattern = pattern[1:-1]
            if not pattern:
                return None
            # prevent internal groups
            if pattern.startswith("public.kern"):
                return None
        else:
            tp = "glyphName"
        e = dict(operator=operator, type=tp, pattern=pattern, groupPrefix=groupPrefix)
        expression.append(e)
    # operator at the beginning
    if expression:
        if expression[0]["operator"] is not None:
            return None
    # no operator after first object
    if expression:
        for e in expression[1:]:
            if e["operator"] is None:
                return None
    return expression

# expression expansion


# =============
# = glyphName =
# =============

def _expandGlyphName(subExpression, glyphList):
    """
    >>> font = _setupTestFont()
    >>> sorted(_expandGlyphName(dict(operator=None, pattern="A"), font.keys()))
    ['A']
    >>> sorted(_expandGlyphName(dict(operator=None, pattern="A*"), font.keys()))
    ['A', 'Aacute']
    """
    pattern = subExpression["pattern"]
    result = set([glyphName for glyphName in glyphList if fnmatch.fnmatchcase(glyphName, pattern)])
    return result


def _expandGlyphNameInPairs(subExpression, pairList, side):
    """
    >>> font = _setupTestFont()
    >>> list(_expandGlyphNameInPairs(dict(operator=None, pattern="B"), font.kerning.keys(), 0))
    [('B', 'public.kern2.A')]
    >>> list(_expandGlyphNameInPairs(dict(operator=None, pattern="B"), font.kerning.keys(),1))
    [('public.kern1.A', 'B')]
    """
    pattern = subExpression["pattern"]
    result = set([pair for pair in pairList if not (pair[side].startswith(side1Prefix) and pair[side].startswith(side2Prefix)) and fnmatch.fnmatchcase(pair[side], pattern)])
    return result

# =============
# = groupName =
# =============


def _expandGroupName(subExpression, groups):
    """
    >>> font = _setupTestFont()
    >>> result = _expandGroupName(dict(operator=None, pattern="A", groupPrefix=None), font.groups)
    >>> sorted(result)
    ['public.kern1.A', 'public.kern2.A']
    """
    pattern = subExpression["pattern"]
    groupPrefix = subExpression["groupPrefix"]
    if groupPrefix is None:
        groupPrefix = "public.kern?."
    pattern = groupPrefix + pattern
    result = set([groupName for groupName in groups.keys() if fnmatch.fnmatchcase(groupName, pattern)])
    return result


def _expandGroupNameInPairs(subExpression, pairList, side):
    """
    >>> font = _setupTestFont()

    # left

    >>> result = _expandGroupNameInPairs(dict(operator=None, pattern="A", groupPrefix=None), font.kerning.keys(), 0)
    >>> sorted(result)
    [('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandGroupNameInPairs(dict(operator=None, pattern="A", groupPrefix="public.kern1."), font.kerning.keys(), 0)
    >>> sorted(result)
    [('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    # right

    >>> result = _expandGroupNameInPairs(dict(operator=None, pattern="A", groupPrefix=None), font.kerning.keys(), 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandGroupNameInPairs(dict(operator=None, pattern="A", groupPrefix="public.kern2."), font.kerning.keys(), 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]
    """
    pattern = subExpression["pattern"]
    groupPrefix = subExpression["groupPrefix"]
    if groupPrefix is None:
        groupPrefix = "public.kern?."
    pattern = groupPrefix + pattern
    result = set([pair for pair in pairList if pair[side].startswith("public.kern") and fnmatch.fnmatchcase(pair[side], pattern)])
    return result


# ===============
# = groupLookup =
# ===============

def _expandGroupLookup(subExpression, groups):
    """
    >>> font = _setupTestFont()
    >>> result = _expandGroupName(dict(operator=None, pattern="A", groupPrefix=None), font.groups)
    >>> sorted(result)
    ['public.kern1.A', 'public.kern2.A']
    >>> result = _expandGroupName(dict(operator=None, pattern="A", groupPrefix="public.kern1."), font.groups)
    >>> sorted(result)
    ['public.kern1.A']
    >>> result = _expandGroupName(dict(operator=None, pattern="A", groupPrefix="public.kern2."), font.groups)
    >>> sorted(result)
    ['public.kern2.A']
    """
    pattern = subExpression["pattern"]
    groupPrefix = subExpression["groupPrefix"]
    # find all glyphs matching the name pattern
    font = groups.getParent()
    matchedGlyphs = _expandGlyphName(dict(operator=None, pattern=pattern), font.keys())
    # find the groups for all matched glyphs
    result = set()
    for glyphName in matchedGlyphs:
        if groupPrefix != "public.kern2.":
            g = groups.metricsMachine.getSide1GroupForGlyph(glyphName)
            if g is not None:
                result.add(g)
        if groupPrefix != "public.kern1.":
            g = groups.metricsMachine.getSide2GroupForGlyph(glyphName)
            if g is not None:
                result.add(g)
    return result


def _expandGroupLookupInPairs(subExpression, pairList, groups, side):
    """
    >>> font = _setupTestFont()

    >>> result = _expandGroupLookupInPairs(dict(operator=None, pattern="A", groupPrefix=None), font.kerning.keys(), font.groups, 0)
    >>> sorted(result)
    [('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]
    >>> result = _expandGroupLookupInPairs(dict(operator=None, pattern="A", groupPrefix="public.kern1."), font.kerning.keys(), font.groups, 0)
    >>> sorted(result)
    [('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandGroupLookupInPairs(dict(operator=None, pattern="A", groupPrefix=None), font.kerning.keys(), font.groups, 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]
    >>> result = _expandGroupLookupInPairs(dict(operator=None, pattern="A", groupPrefix="public.kern2."), font.kerning.keys(), font.groups, 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]
    """
    pattern = subExpression["pattern"]
    groupPrefix = subExpression["groupPrefix"]
    # find all glyphs matching the name pattern
    font = groups.getParent()
    matchedGlyphs = _expandGlyphName(dict(operator=None, pattern=pattern), font.keys())
    # find the groups for all matched glyphs
    matchedGroups = set()
    for glyphName in matchedGlyphs:
        if groupPrefix != "public.kern2.":
            g = groups.metricsMachine.getSide1GroupForGlyph(glyphName)
            if g is not None:
                matchedGroups.add(g)
        if groupPrefix != "public.kern1.":
            g = groups.metricsMachine.getSide2GroupForGlyph(glyphName)
            if g is not None:
                matchedGroups.add(g)
    # run through all the pairs and grab the ones containing one of the found groups
    result = set([pair for pair in pairList if pair[side] in matchedGroups])
    return result


# ======================
# = referenceGroupName =
# ======================

def _expandReferenceGroupName(subExpression, groups):
    """
    >>> font = _setupTestFont()
    >>> list(_expandReferenceGroupName(dict(operator=None, pattern="Uppercase", groupPrefix=None), font.groups))
    ['Uppercase']
    """
    pattern = subExpression["pattern"]
    result = set([groupName for groupName in groups.keys() if fnmatch.fnmatchcase(groupName, pattern)])
    return result


def _expandReferenceGroupNameInPairs(subExpression, pairList, groups, side):
    """
    >>> font = _setupTestFont()

    # left
    >>> result = _expandReferenceGroupNameInPairs(dict(operator=None, pattern="Uppercase", groupPrefix=None), font.kerning.keys(), font.groups, 0)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    # right
    >>> result = _expandReferenceGroupNameInPairs(dict(operator=None, pattern="Uppercase", groupPrefix=None), font.kerning.keys(), font.groups, 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]
    """
    pattern = subExpression["pattern"]
    referenceGroups = [set(groups.metricsMachine.getReferenceGroup(groupName)) for groupName in groups.metricsMachine.getReferenceGroupNames() if fnmatch.fnmatchcase(groupName, pattern)]
    result = set([])
    for pair in pairList:
        member = pair[side]
        for group in referenceGroups:
            if member.startswith("public.kern"):
                kerningGroup = groups[member]
                if not isinstance(kerningGroup, set):
                    kerningGroup = set(kerningGroup)
                if group & kerningGroup:
                    result.add(pair)
                    break
            elif pair[side] in group:
                result.add(pair)
                break
    return result


# =============
# = variables =
# =============

def _expandVariableInPairs(subExpression, pairList, font, side):
    """
    >>> font = _setupTestFont()

    # left

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="all"), font.kerning.keys(), font, 0)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="glyph"), font.kerning.keys(), font, 0)
    >>> sorted(result)
    [('B', 'public.kern2.A')]

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="group"), font.kerning.keys(), font, 0)
    >>> sorted(result)
    [('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="exception"), font.kerning.keys(), font, 0)
    >>> sorted(result)
    [('B', 'public.kern2.A')]

    # right

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="all"), font.kerning.keys(), font, 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="glyph"), font.kerning.keys(), font, 1)
    >>> sorted(result)
    [('public.kern1.A', 'B')]

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="group"), font.kerning.keys(), font, 1)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'public.kern2.A')]

    >>> result = _expandVariableInPairs(dict(modifier=None, pattern="exception"), font.kerning.keys(), font, 1)
    >>> sorted(result)
    [('public.kern1.A', 'B')]
    """
    pattern = subExpression["pattern"]
    kerning = font.kerning
    if pattern == "all":
        result = set(kerning.keys())
    elif pattern == "glyph":
        result = set([pair for pair in pairList if not pair[side].startswith("public.kern1") and not pair[side].startswith("public.kern2")])
    elif pattern == "group":
        result = set([pair for pair in pairList if pair[side].startswith("public.kern1") or pair[side].startswith("public.kern2")])
    elif pattern == "exception":
        result = set([pair for pair in pairList if kerning.metricsMachine.getPairType(pair)[side] == "exception"])
    return result


# evaluation

# glyph and group list

def _evaluateGlyphExpression(expression, glyphList, groups=None, expandGroups=False):
    # store the incoming orders
    glyphOrder = list(glyphList)
    groupOrder = list(sorted(groups.keys()))
    # tokenize
    expression = _tokenize(expression)
    # evaluate each sub-expression
    result = None
    for subExpression in expression:
        tp = subExpression["type"]
        operator = subExpression["operator"]
        v = None
        if tp == "glyphName":
            v = _expandGlyphName(subExpression, glyphList)
        elif tp == "groupName":
            v = _expandGroupName(subExpression, groups)
            if expandGroups:
                e = set([])
                for groupName in v:
                    e = e | groups[groupName]
                v = e
        elif tp == "groupLookup":
            v = _expandGroupLookup(subExpression, groups)
            if expandGroups:
                e = set([])
                for groupName in v:
                    e = e | groups[groupName]
                v = e
        elif tp == "referenceGroupName":
            v = _expandReferenceGroupName(subExpression, groups)
            e = set([])
            for groupName in v:
                e = e | set(groups.metricsMachine.getReferenceGroup(groupName))
            v = e
        result = _handleOperator(operator, result, v)
    # order the result
    final = []
    if groups:
        final += [groupName for groupName in groupOrder if groupName in result]
    final += [glyphName for glyphName in glyphOrder if glyphName in result]
    return final


# ===========
# = kerning =
# ===========

def _evaluateKerningExpression(expression, pairList, font, allowVariables):
    """
    >>> font = _setupTestFont()

    # test the sides
    >>> result = _evaluateKerningExpression("all", font.kerning.keys(), font, True)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'B'), ('public.kern1.A', 'public.kern2.A')]
    >>> result = _evaluateKerningExpression("exception", font.kerning.keys(), font, True)
    >>> sorted(result)
    [('B', 'public.kern2.A'), ('public.kern1.A', 'B')]
    >>> result = _evaluateKerningExpression("all, glyph", font.kerning.keys(), font, True)
    >>> sorted(result)
    [('public.kern1.A', 'B')]
    >>> result = _evaluateKerningExpression("glyph, all", font.kerning.keys(), font, True)
    >>> sorted(result)
    [('B', 'public.kern2.A')]
    """
    # store the incoming order
    pairOrder = list(pairList)
    # break up the parts
    parts, partCount = _splitKerningExpression(expression)
    findOverlap = partCount == 2
    left, right = parts
    # tokenize
    left = _tokenize(left)
    right = _tokenize(right)
    # evaluate each side
    leftResults = _evaluateKerningExpressionSide(left, pairList, font, 0, allowVariables)
    rightResults = _evaluateKerningExpressionSide(right, pairList, font, 1, allowVariables)
    # combine
    if findOverlap:
        results = leftResults & rightResults
    else:
        results = leftResults | rightResults
    # reorder
    final = []
    for pair in pairOrder:
        if pair in results:
            final.append(pair)
    # return
    return final


def _evaluateKerningExpressionSide(expression, pairList, font, side, allowVariables):
    pairList = set(pairList)
    # expand each sub-expression
    result = None
    for subExpression in expression:
        tp = subExpression["type"]
        operator = subExpression["operator"]
        # expand
        v = None
        if tp == "variable" and allowVariables:
            v = _expandVariableInPairs(subExpression, pairList, font, side)
        elif tp == "glyphName":
            v = _expandGlyphNameInPairs(subExpression, pairList, side)
        elif tp == "groupName":
            v = _expandGroupNameInPairs(subExpression, pairList, side)
        elif tp == "groupLookup":
            v = _expandGroupLookupInPairs(subExpression, pairList, font.groups, side)
        elif tp == "referenceGroupName":
            v = _expandReferenceGroupNameInPairs(subExpression, pairList, font.groups, side)
        # handle the operator
        result = _handleOperator(operator, result, v)
    if result is None:
        result = set([])
    return result


# ==========
# = helper =
# ==========


def _handleOperator(operator, old, new):
    if old is None:
        return new
    else:
        if operator == "not":
            return old - new
        elif operator == "or":
            return old | new
        elif operator == "and":
            return old & new


# -------
# Testing
# -------

def _setupTestFont():
    import mm4.objects
    from defcon import Font
    font = Font()
    glyphNames = "A Aacute B C D E Egrave".split(" ")
    for glyphName in glyphNames:
        font.newGlyph(glyphName)
    groups = {
        "public.kern1.A": ["A", "Aacute"],
        "public.kern2.A": ["A", "Aacute"],
        "public.kern1.B": ["B"],
        "public.kern2.B": ["B", "D", "E", "Egrave"],
        "Uppercase": ["A", "Aacute", "B"],
    }
    font.groups.update(groups)
    kerning = {
        ("public.kern1.A", "public.kern2.A"): 100,
        ("public.kern1.A", "B"): 100,
        ("B", "public.kern2.A"): 100,
    }
    font.kerning.update(kerning)
    return font


def _testPrint(result):
    r = []
    for i in result:
        r.append(list(sorted(i.items())))
    return r


if __name__ == "__main__":
    import doctest
    doctest.testmod()
