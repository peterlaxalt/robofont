from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix, side1FeaPrefix, side2FeaPrefix

# -----------------------------------
# Cloned from ancient feaTools module
# -----------------------------------

import re


class FeaToolsParserSyntaxError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


# used for removing all comments
commentRE = re.compile(r"#.*")

# used for finding all strings
stringRE = re.compile(
    r"\""         # "
    r"([^\"]*)"   # anything but "
    r"\""         # "
)

# used for removing all comments
terminatorRE = re.compile(";")

# used for finding all feature names.
feature_findAll_RE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"feature\s+"           # feature
        r"([\w\d]{4})"          # name
        r"\s*{"                 # {
        )

# used for finding the content of features.
# this regular expression will be compiled
# for each feature name found.
featureContentRE = [
        r"([\s;\{\}]|^)",       # whitepace, ; {, } or start of line
        r"feature\s+",          # feature
        # feature name         # name
        r"\s*\{",               # {
        r"([\S\s]*)",           # content
        r"}\s*",                # }
        # feature name         # name
        r"\s*;"                 # ;
        ]

# used for finding all lookup names.
lookup_findAll_RE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"lookup\s+"            # lookup
        r"([\w\d_.]+)"          # name
        r"\s*{"                 # {
        )

# used for finding the content of lookups.
# this regular expression will be compiled
# for each lookup name found.
lookupContentRE = [
        r"([\s;\{\}]|^)",       # whitepace, ; {, } or start of line
        r"lookup\s+",           # lookup
        # lookup name          # name
        r"\s*\{",               # {
        r"([\S\s]*)",           # content
        r"}\s*",                # }
        # lookup name          # name
        r"\s*;"                 # ;
        ]

# used for finding all table names.
table_findAll_RE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"table\s+"             # table
        r"([\w\d/]+)"        # name
        r"\s*{"                 # {
        )

# used for finding the content of tables.
# this regular expression will be compiled
# for each table name found.
tableContentRE = [
        r"([\s;\{\}]|^)",       # whitepace, ; {, } or start of line
        r"table\s+",            # feature
        # table name           # name
        r"\s*\{",               # {
        r"([\S\s]*)",           # content
        r"}\s*",                # }
        # table name           # name
        r"\s*;"                 # ;
        ]

# used for getting tag value pairs from tables.
tableTagValueRE = re.compile(
    r"([\w\d_.]+)"       # tag
    r"\s+"               #
    r"([^;]+)"           # anything but ;
    r";"                 # ;
)

# used for finding all class definitions.
classDefinitionRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"@"                    # @
        r"([\w\d_.]+)"          # name
        r"\s*=\s*"              #  =
        r"\["                   # [
        r"([\w\d\s_.@]+)"       # content
        r"\]"                   # ]
        r"\s*;"                 # ;
        , re.M
        )

# used for getting the contents of a class definition
classContentRE = re.compile(
        r"([\w\d_.@]+)"
        )

# used for finding inline classes within a sequence
sequenceInlineClassRE = re.compile(
        r"\["                   # [
        r"([\w\d\s_.@]+)"       # content
        r"\]"                   # ]
        )

# used for finding all substitution type 1
subType1And4RE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"substitute|sub\s+"    # sub
        r"([\w\d\s_.@\[\]]+)"   # target
        r"\s+by\s+"             #  by
        r"([\w\d\s_.@\[\]]+)"   # replacement
        r"\s*;"                 # ;
        )

# used for finding all substitution type 3
subType3RE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"substitute|sub\s+"    # sub
        r"([\w\d\s_.@\[\]]+)"   # target
        r"\s+from\s+"           #  from
        r"([\w\d\s_.@\[\]]+)"   # replacement
        r"\s*;"                 # ;
        )

# used for finding all ignore substitution type 6
ignoreSubType6RE = re.compile(
        r"([\s;\{\}]|^)"                          # whitepace, ; {, } or start of line
        r"ignore\s+substitute|ignore\s+sub\s+"    # ignore sub
        r"([\w\d\s_.@\[\]']+)"                    # preceding context, target, trailing context
        r"\s*;"                                   # ;
        )

# used for finding all substitution type 6
# XXX see failing unit test
subType6RE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"substitute|sub\s+"    # sub
        r"([\w\d\s_.@\[\]']+)"  # preceding context, target, trailing context
        r"\s+by\s+"             #  by
        r"([\w\d\s_.@\[\]]+)"   # replacement
        r"\s*;"                 # ;
        )

subType6TargetRE = re.compile(
        r"(\["                  # [
        r"[\w\d\s_.@]+"         # content
        r"\]"                   # ]'
        r"|"                    # <or>
        r"[\w\d_.@]+)'"         # content
        )

subType6TargetExtractRE = re.compile(
        r"([\w\d_.@]*)"       # glyph or class names
        )

# used for finding positioning type 1
posType1RE = re.compile(
    r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
    r"position|pos\s+"      # pos
    r"([\w\d\s_.@\[\]]+)"   # target
    r"\s+<"                 # <
    r"([-\d\s]+)"           # value
    r"\s*>\s*;"             # >;
    )

# used for finding positioning type 2
posType2RE = re.compile(
    r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
    r"(enum\s+|\s*)"        # enum
    r"(position|pos\s+)"    # pos
    r"([-\w\d\s_.@\[\]]+)"  # left, right, value
    r"\s*;"                 # ;
    )

# used for finding all languagesystem
languagesystemRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"languagesystem\s+"    # languagesystem
        r"([\w\d]+)"            # script tag
        r"\s+"                  #
        r"([\w\d]+)"            # language tag
        r"\s*;"                 # ;
        )

# use for finding all script
scriptRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"script\s+"            # script
        r"([\w\d]+)"            # script tag
        r"\s*;"                 # ;
        )

# used for finding all language
languageRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"language\s+"          # language
        r"([\w\d]+)"            # language tag
        r"\s*"                  #
        r"([\w\d]*)"            # include_dflt or exclude_dflt or nothing
        r"\s*;"                 # ;
        )

# use for finding all includes
includeRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"include\s*"           # include
        r"\(\s*"                # (
        r"([^\)]+)"             # anything but )
        r"\s*\)"                # )
        r"\s*;{0,1}"            # ; which will occur zero or one times (ugh!)
        )

# used for finding subtable breaks
subtableRE = re.compile(
    r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
    r"subtable\s*"          # subtable
    r"\s*;"                 # ;
)

# used for finding feature references
featureReferenceRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"feature\s+"           # feature
        r"([\w\d]{4})"          # name
        r"\s*;"                 # {
        )

# used for finding lookup references
lookupReferenceRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"lookup\s+"            # lookup
        r"([\w\d]+)"            # name
        r"\s*;"                 # {
        )

# use for finding all lookup flags
lookupflagRE = re.compile(
        r"([\s;\{\}]|^)"        # whitepace, ; {, } or start of line
        r"lookupflag\s+"        # lookupflag
        r"([\w\d,\s]+)"         # values
        r"\s*;"                 # ;
        )

def _parseUnknown(writer, text):
    text = text.strip()
    ## extract all table names
    tableNames = table_findAll_RE.findall(text)
    for precedingMark, tableName in tableNames:
        # a regular expression specific to this lookup must
        # be created so that nested lookups are safely handled
        thisTableContentRE = list(tableContentRE)
        thisTableContentRE.insert(2, tableName)
        thisTableContentRE.insert(6, tableName)
        thisTableContentRE = re.compile("".join(thisTableContentRE))
        found = thisTableContentRE.search(text)
        tableText = found.group(2)
        start, end = found.span()
        precedingText = text[:start]
        if precedingMark:
            precedingText += precedingMark
        _parseUnknown(writer, precedingText)
        _parseTable(writer, tableName, tableText)
        text = text[end:]
    ## extract all feature names
    featureNames = feature_findAll_RE.findall(text)
    for precedingMark, featureName in featureNames:
        # a regular expression specific to this lookup must
        # be created so that nested lookups are safely handled
        thisFeatureContentRE = list(featureContentRE)
        thisFeatureContentRE.insert(2, featureName)
        thisFeatureContentRE.insert(6, featureName)
        thisFeatureContentRE = re.compile("".join(thisFeatureContentRE))
        found = thisFeatureContentRE.search(text)
        featureText = found.group(2)
        start, end = found.span()
        precedingText = text[:start]
        if precedingMark:
            precedingText += precedingMark
        _parseUnknown(writer, precedingText)
        _parseFeature(writer, featureName, featureText)
        text = text[end:]
    ## extract all lookup names
    lookupNames = lookup_findAll_RE.findall(text)
    for precedingMark, lookupName in lookupNames:
        # a regular expression specific to this lookup must
        # be created so that nested lookups are safely handled
        thisLookupContentRE = list(lookupContentRE)
        thisLookupContentRE.insert(2, lookupName)
        thisLookupContentRE.insert(6, lookupName)
        thisLookupContentRE = re.compile("".join(thisLookupContentRE))
        found = thisLookupContentRE.search(text)
        lookupText = found.group(2)
        start, end = found.span()
        precedingText = text[:start]
        if precedingMark:
            precedingText += precedingMark
        _parseUnknown(writer, precedingText)
        _parseLookup(writer, lookupName, lookupText)
        text = text[end:]
    ## extract all class data
    classes = classDefinitionRE.findall(text)
    for precedingMark, className, classContent in classes:
        text = _executeSimpleSlice(precedingMark, text, classDefinitionRE, writer)
        className = "@" + className
        _parseClass(writer, className, classContent)
    ## extract substitutions
    # sub type 1 and 4
    subType1s = subType1And4RE.findall(text)
    for precedingMark, target, replacement in subType1s:
        text = _executeSimpleSlice(precedingMark, text, subType1And4RE, writer)
        _parseSubType1And4(writer, target, replacement)
    # sub type 3
    subType3s = subType3RE.findall(text)
    for precedingMark, target, replacement in subType3s:
        text = _executeSimpleSlice(precedingMark, text, subType3RE, writer)
        _parseSubType3(writer, target, replacement)
    # sub type 6
    subType6s = subType6RE.findall(text)
    for precedingMark, target, replacement in subType6s:
        text = _executeSimpleSlice(precedingMark, text, subType6RE, writer)
        _parseSubType6(writer, target, replacement)
    # ignore sub type 6
    ignoreSubType6s = ignoreSubType6RE.findall(text)
    for precedingMark, target in ignoreSubType6s:
        text = _executeSimpleSlice(precedingMark, text, ignoreSubType6RE, writer)
        _parseSubType6(writer, target, replacement=None, ignore=True)
    ## extract positions
    # pos type 1
    posType1s = posType1RE.findall(text)
    for precedingMark, target, value in posType1s:
        text = _executeSimpleSlice(precedingMark, text, posType1RE, writer)
        _parsePosType1(writer, target, value)
    # pos type 2
    posType2s = posType2RE.findall(text)
    for precedingMark, enumTag, posTag, targetAndValue in posType2s:
        text = _executeSimpleSlice(precedingMark, text, posType2RE, writer)
        _parsePosType2(writer, targetAndValue)
    ## extract other data
    # XXX look at FDK spec. sometimes a language tag of dflt will be passed
    # it should be handled differently than the other tags.
    # languagesystem
    languagesystems = languagesystemRE.findall(text)
    for precedingMark, scriptTag, languageTag in languagesystems:
        text = _executeSimpleSlice(precedingMark, text, languagesystemRE, writer)
        writer.languageSystem(scriptTag, languageTag)
    # script
    scripts = scriptRE.findall(text)
    for precedingMark, scriptTag in scripts:
        text = _executeSimpleSlice(precedingMark, text, scriptRE, writer)
        writer.script(scriptTag)
    # language
    languages = languageRE.findall(text)
    for precedingMark, languageTag, otherKeyword in languages:
        text = _executeSimpleSlice(precedingMark, text, languageRE, writer)
        if not otherKeyword or otherKeyword == "include_dflt":
            writer.language(languageTag)
        elif otherKeyword == "exclude_dflt":
            writer.language(languageTag, includeDefault=False)
    # include
    inclusions = includeRE.findall(text)
    for precedingMark, path in inclusions:
        text = _executeSimpleSlice(precedingMark, text, includeRE, writer)
        writer.include(path)
    # feature reference
    featureReferences = featureReferenceRE.findall(text)
    for precedingMark, featureName in featureReferences:
        text = _executeSimpleSlice(precedingMark, text, featureReferenceRE, writer)
        writer.featureReference(featureName)
    # lookup reference
    lookupReferences = lookupReferenceRE.findall(text)
    for precedingMark, lookupName in lookupReferences:
        text = _executeSimpleSlice(precedingMark, text, lookupReferenceRE, writer)
        writer.lookupReference(lookupName)
    # lookupflag
    lookupflags = lookupflagRE.findall(text)
    for precedingMark, lookupflagValues in lookupflags:
        text = _executeSimpleSlice(precedingMark, text, lookupflagRE, writer)
        _parseLookupFlag(writer, lookupflagValues)
    # subtable break
    subtables = subtableRE.findall(text)
    for precedingMark in subtables:
        text = _executeSimpleSlice(precedingMark, text, subtableRE, writer)
        writer.subtableBreak()
    text = text.strip()
    if text:
        raise FeaToolsParserSyntaxError("Invalid Syntax: %s" % text)

def _executeSimpleSlice(precedingMark, text, regex, writer):
    first = regex.search(text)
    start, end = first.span()
    precedingText = text[:start]
    if precedingMark:
        precedingText += precedingMark
    _parseUnknown(writer, precedingText)
    text = text[end:]
    return text

def _parseFeature(writer, name, feature):
    featureWriter = writer.feature(name)
    parsed = _parseUnknown(featureWriter, feature)

def _parseLookup(writer, name, lookup):
    lookupWriter = writer.lookup(name)
    parsed = _parseUnknown(lookupWriter, lookup)

def _parseTable(writer, name, table):
    tagValueTables = ["head", "hhea", "OS/2", "vhea"]
    # skip unknown tables
    if name not in tagValueTables:
        return
    _parseTagValueTable(writer, name, table)

def _parseTagValueTable(writer, name, table):
    valueTypes = {
        "head" : {
            "FontRevision" : float
        },
        "hhea" : {
            "CaretOffset" : float,
            "Ascender"    : float,
            "Descender"   : float,
            "LineGap"     : float,
        },
        "OS/2" : {
            "FSType"        : int,
            "Panose"        : "listOfInts",
            "UnicodeRange"  : "listOfInts",
            "CodePageRange" : "listOfInts",
            "TypoAscender"  : float,
            "TypoDescender" : float,
            "TypoLineGap"   : float,
            "winAscent"     : float,
            "winDescent"    : float,
            "XHeight"       : float,
            "CapHeight"     : float,
            "WeightClass"   : float,
            "WidthClass"    : float,
            "Vendor"        : str
        },
        "vhea" : {
            "VertTypoAscender"  : float,
            "VertTypoDescender" : float,
            "VertTypoLineGap"   : float
        }
    }
    tableTypes = valueTypes[name]
    parsedTagValues = []
    for tag, value in tableTagValueRE.findall(table):
        tag = tag.strip()
        value = value.strip()
        if tag not in tableTypes:
            raise FeaToolsParserSyntaxError("Unknown Tag: %s" % tag)
        desiredType = tableTypes[tag]
        if desiredType == "listOfInts":
            v = []
            for line in value.splitlines():
                for i in line.split():
                    v.append(i)
            value = v
            values = []
            for i in value:
                try:
                    i = int(i)
                    values.append(i)
                except ValueError:
                    raise FeaToolsParserSyntaxError("Invalid Syntax: %s" % i)
            value = values
        elif desiredType == str:
            raise NotImplementedError
        elif not isinstance(value, desiredType):
            try:
                value = desiredType(value)
            except ValueError:
                raise FeaToolsParserSyntaxError("Invalid Syntax: %s" % i)
        parsedTagValues.append((tag, value))
    writer.table(name, parsedTagValues)

def _parseClass(writer, name, content):
    content = classContentRE.findall(content)
    writer.classDefinition(name, content)

def _parseSequence(sequence):
    parsed = []
    for content in sequenceInlineClassRE.findall(sequence):
        first = sequenceInlineClassRE.search(sequence)
        start, end = first.span()
        precedingText = sequence[:start]
        parsed.extend(_parseSequence(precedingText))
        parsed.append(_parseSequence(content))
        sequence = sequence[end:]
    content = [i for i in sequence.split(" ") if i]
    parsed.extend(content)
    return parsed

def _parseSubType1And4(writer, target, replacement):
    target = _parseSequence(target)
    # replacement will always be one item.
    # either a single glyph/class or a list
    # reresenting an inline class.
    replacement = _parseSequence(replacement)
    replacement = replacement[0]
    if len(target) == 1:
        target = target[0]
        writer.gsubType1(target, replacement)
    else:
        # target will always be a list representing a sequence.
        # the list may contain strings representing a single
        # glyph/class or a list representing an inline class.
        writer.gsubType4(target, replacement)

def _parseSubType3(writer, target, replacement):
    # target will only be one item representing
    # a glyph/class name.
    target = classContentRE.findall(target)
    target = target[0]
    replacement = classContentRE.findall(replacement)
    writer.gsubType3(target, replacement)

def _parseSubType6(writer, target, replacement=None, ignore=False):
    # replacement will always be one item.
    # either a single glyph/class or a list
    # representing an inline class.
    # the only exception to this is if
    # this is an ignore substitution.
    # in that case, replacement will
    # be None.
    if not ignore:
        replacement = classContentRE.findall(replacement)
        if len(replacement) == 1:
            replacement = replacement[0]
    #
    targetText = target
    #
    precedingContext = ""
    targets = subType6TargetRE.findall(targetText)
    trailingContext = ""
    #
    targetCount = len(targets)
    counter = 1
    extractedTargets = []
    for target in targets:
        first = subType6TargetRE.search(targetText)
        start, end = first.span()
        if counter == 1:
            precedingContext = _parseSequence(targetText[:start])
        if counter == targetCount:
            trailingContext = _parseSequence(targetText[end:])
        # the target could be in a form like [o o.alt]
        # so it has to be broken down
        target = classContentRE.findall(target)
        if len(target) == 1:
            target = target[0]
        extractedTargets.append(target)
        counter += 1
        targetText = targetText[end:]
    writer.gsubType6(precedingContext, extractedTargets, trailingContext, replacement)

def _parsePosType1(writer, target, value):
    # target will only be one item representing
    # a glyph/class name
    value = tuple([float(i) for i in value.strip().split(" ")])
    writer.gposType1(target, value)

def _parsePosType2(writer, targetAndValue):
    # the target and value will be coming
    # in as single string.
    target = " ".join(targetAndValue.split(" ")[:-1])
    value = targetAndValue.split(" ")[-1]
    # XXX this could cause a choke
    value = float(value)
    target = _parseSequence(target)
    writer.gposType2(target, value)

def _parsePosType2WithEnum(writer, targetAndValue):
    # the target and value will be coming
    # in as single string.
    target = " ".join(targetAndValue.split(" ")[:-1])
    value = targetAndValue.split(" ")[-1]
    # XXX this could cause a choke
    value = float(value)
    target = _parseSequence(target)
    writer.gposType2(target, value)

def _parseLookupFlag(writer, values):
    values = values.replace(",", " ")
    values = [i for i in values.split(" ") if i]
    # lookupflag format B is not supported except for value 0
    if len(values) == 1:
        try:
            v = int(values[0])
            if v != 0:
                raise FeaToolsParserSyntaxError("lookupflag format B is not supported for any value other than 0")
            else:
                writer.lookupFlag()
                return
        except ValueError:
            pass
    rightToLeft = False
    ignoreBaseGlyphs = False
    ignoreLigatures = False
    ignoreMarks = False
    possibleValues = ["RightToLeft", "IgnoreBaseGlyphs", "IgnoreLigatures", "IgnoreMarks"]
    for value in values:
        if value not in possibleValues:
            raise FeaToolsParserSyntaxError("Unknown lookupflag value: %s" % value)
        if value == "RightToLeft":
            rightToLeft = True
        elif value == "IgnoreBaseGlyphs":
            ignoreBaseGlyphs = True
        elif value == "IgnoreLigatures":
            ignoreLigatures = True
        elif value == "IgnoreMarks":
            ignoreMarks = True
    writer.lookupFlag(rightToLeft=rightToLeft, ignoreBaseGlyphs=ignoreBaseGlyphs, ignoreLigatures=ignoreLigatures, ignoreMarks=ignoreMarks)

def parseFeatures(writer, text):
    # strip the strings.
    # (an alternative approach would be to escape the strings.
    # the problem is that a string could contain parsable text
    # that would fool the parsing algorithm.)
    text = stringRE.sub("", text)
    # strip the comments
    text = commentRE.sub("", text)
    # make sure there is a space after all ;
    # since it makes the text more digestable
    # for the regular expressions
    text = terminatorRE.sub("; ", text)
    _parseUnknown(writer, text)


class AbstractFeatureWriter(object):

    def feature(self, name):
        return self

    def lookup(self, name):
        return self

    def table(self, name, data):
        pass

    def featureReference(self, name):
        pass

    def lookupReference(self, name):
        pass

    def classDefinition(self, name, contents):
        pass

    def lookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False):
        pass

    def gsubType1(self, target, replacement):
        pass

    def gsubType3(self, target, replacement):
        pass

    def gsubType4(self, target, replacement):
        pass

    def gsubType6(self, precedingContext, target, trailingContext, replacement):
        pass

    def gposType1(self, target, value):
        pass

    def gposType2(self, target, value):
        pass

    def languageSystem(self, languageTag, scriptTag):
        pass

    def script(self, scriptTag):
        pass

    def language(self, languageTag, includeDefault=True):
        pass

    def include(self, path):
        pass

    def subtableBreak(self):
        pass

# ------
# Onward
# ------

def extractKerningData(text):
    writer = _KernFeatureLoadingWriter()
    try:
        parseFeatures(writer, text)
    except FeaToolsParserSyntaxError as message:
        return False, message.value, None, None
    isValid, message = writer.validate()
    if not isValid:
        return False, message, None, None
    return True, None, writer.getKerning(), writer.getGroups()


class _KernFeatureLoadingWriter(AbstractFeatureWriter):

    def __init__(self, name=None):
        self._currentFeature = None
        self._groupError = False
        self._kerningError = False

        self._kerning = {}
        self._classes = {}

        self._processedKerning = None
        self._leftGroups = None
        self._rightGroups = None

    # ------------
    # external api
    # ------------

    def validate(self):
        # the parse could have caught an error
        if self._groupError:
            return False, self._groupError
        if self._kerningError:
            return False, self._kerningError
        # processing the data will catch some errors
        self._processData()
        if self._groupError:
            return False, self._groupError
        if self._kerningError:
            return False, self._kerningError
        # look for glyphs in more than one class
        leftGlyphToClass = {}
        rightGlyphToClass = {}
        for groups, glyphToClass in ((self._leftGroups, leftGlyphToClass), (self._rightGroups, rightGlyphToClass)):
            for groupName, glyphList in groups.items():
                for glyphName in glyphList:
                    if glyphName not in glyphToClass:
                        glyphToClass[glyphName] = set()
                    glyphToClass[glyphName].add(groupName)
            for glyphName, groupList in glyphToClass.items():
                if len(groupList) > 1:
                    message = "Glyph %s in more than one class: %s." % (glyphName, " ".join(sorted(groupList)))
                    return False, message
        # look for conflicting group, glyph + glyph, group exceptions
        for left, right in self._processedKerning.keys():
            if left.startswith(side1Prefix) and right.startswith(side2Prefix):
                continue
            if not left.startswith(side1Prefix) and not right.startswith(side2Prefix):
                continue
            if not left.startswith(side1Prefix) and left not in leftGlyphToClass:
                continue
            if not right.startswith(side2Prefix) and right not in rightGlyphToClass:
                continue
            if left.startswith(side1Prefix):
                rightGroup = list(rightGlyphToClass.get(right, [right]))[0]
                leftContents = self._leftGroups[left]
                for l in leftContents:
                    if (l, rightGroup) in self._processedKerning:
                        return False, "Conflicting pairs: %s, %s and %s, %s." % (left, right, l, rightGroup)
            if right.startswith(side2Prefix):
                leftGroup = list(leftGlyphToClass.get(left, [left]))[0]
                rightContents = self._rightGroups[right]
                for r in rightContents:
                    if (leftGroup, r) in self._processedKerning:
                        return False, "Conflicting pairs: %s, %s and %s, %s." % (left, right, leftGroup, r)
        return True, None

    def getKerning(self):
        if self._processedKerning is None:
            self._processData()
        return self._processedKerning

    def getGroups(self):
        if self._processedKerning is None:
            self._processData()
        return self._leftGroups, self._rightGroups

    # --------------
    # internal tools
    # --------------

    def _processData(self):
        # handle kerning
        self._processedKerning = {}
        leftGroups = set()
        rightGroups = set()
        # find all left and right referenced groups
        leftReferencedGroups = set()
        rightReferencedGroups = set()
        for left, right in self._kerning.keys():
            if isinstance(left, str) and left.startswith("@"):
                leftReferencedGroups.add(left)
            if isinstance(right, str) and right.startswith("@"):
                rightReferencedGroups.add(right)
        # work through pairs
        for (left, right), value in self._kerning.items():
            # convert lists of glyphs to group names where possible
            if isinstance(left, tuple):
                for className, glyphList in self._classes.items():
                    if set(glyphList) == set(left):
                        if className in leftReferencedGroups or className.startswith("@"):
                            left = className
                            break
            if isinstance(right, tuple):
                for className, glyphList in self._classes.items():
                    if set(glyphList) == set(right):
                        if className in rightReferencedGroups or className.startswith("@"):
                            right = className
                            break
            # catch class references, flag the class and make a MM class name.
            if isinstance(left, str) and left.startswith("@"):
                if left not in self._classes:
                    self._kerningError = "Undefined class: %s" % left
                    return
                leftGroups.add(left)
                if left.startswith("@"):
                    if left.startswith(side1FeaPrefix):
                        left = side1Prefix + left[len(side1FeaPrefix)]
                    else:
                        left = side1Prefix + left[1:]
            if isinstance(right, str) and right.startswith("@"):
                if right not in self._classes:
                    self._kerningError = "Undefined class: %s" % right
                    return
                rightGroups.add(right)
                if right.startswith("@"):
                    if right.startswith(side2FeaPrefix):
                        right = side2Prefix + right[len(side2FeaPrefix)]
                    else:
                        right = side2Prefix + right[1:]
            # convert left and right to iterables as needed
            if not isinstance(left, tuple):
                left = [left]
            if not isinstance(right, tuple):
                right = [right]
            # store the pairs
            for l in left:
                for r in right:
                    if (l, r) in self._processedKerning:
                        self._kerningError = "Pair %s, %s defined more than once." % (l, r)
                        return
                    self._processedKerning[l, r] = value
        # handle groups
        self._leftGroups = {}
        self._rightGroups = {}
        for className in leftGroups:
            self._flattenClass(className)
            if className.startswith(side1Prefix):
                groupName = className
            else:
                if className.startswith(side1FeaPrefix):
                    groupName = side1Prefix + className[len(side1FeaPrefix)]
                else:
                    groupName = side1Prefix + className[1:]
            self._leftGroups[groupName] = set(self._classes[className])
        for className in rightGroups:
            self._flattenClass(className)
            if className.startswith(side2Prefix):
                groupName = className
            else:
                if className.startswith(side2FeaPrefix):
                    groupName = side2Prefix + className[len(side2FeaPrefix)]
                else:
                    groupName = side2Prefix + className[1:]
            self._rightGroups[groupName] = set(self._classes[className])

    def _flattenClass(self, className):
        result = set()
        for name in self._classes[className]:
            if name.startswith("@"):
                self._flattenClass(name)
                result = result | self._classes[name]
            else:
                result.add(name)
        self._classes[name] = result

    # --------------
    # writer methods
    # --------------

    def feature(self, name):
        self._currentFeature = name
        return self

    def lookup(self, name):
        return self

    def classDefinition(self, name, contents):
        if self._groupError or self._kerningError:
            return
        if name in self._classes:
            self._groupError = "Class %s defined more than once." % name
        self._classes[name] = contents

    def gsubType1(self, target, replacement):
        pass

    def gsubType3(self, target, replacement):
        pass

    def gsubType4(self, target, replacement):
        pass

    def gsubType6(self, precedingContext, target, trailingContext, replacement):
        pass

    def gposType1(self, target, value):
        pass

    def gposType2(self, target, value, needEnum=False):
        if self._groupError or self._kerningError:
            return
        if self._currentFeature != "kern":
            return
        left, right = target
        if isinstance(left, list):
            left = tuple(left)
        if isinstance(right, list):
            right = tuple(right)
        if (left, right) in self._kerning:
            l = left
            r = right
            if isinstance(l, tuple):
                l = "[%s]" % " ".join(l)
            if isinstance(r, tuple):
                r = "[%s]" % " ".join(r)
            self._kerningError = "Pair %s, %s defined more than once." % (l, r)
        self._kerning[left, right] = int(round(value))

    def languageSystem(self, languageTag, scriptTag):
        pass

    def script(self, scriptTag):
        pass

    def language(self, languageTag, includeDefault=True):
        pass

    def include(self, path):
        pass

    def subtableBreak(self):
        pass


# -----
# tests
# -----

_testInvalidSyntax_fea = """
blah;
"""


def _testInvalidSyntax():
    """
    >>> extractKerningData(_testInvalidSyntax_fea) == (False, 'Invalid Syntax: blah', None, None)
    True
    """


_testDuplicateClassName_fea = """
@foo = [x y x];

feature kern {
    @foo = [a b c];
} kern;
"""


def _testDuplicateClassName():
    """
    >>> extractKerningData(_testDuplicateClassName_fea) == (False, 'Class @foo defined more than once.', None, None)
    True
    """


_testMissingClass_fea = """
feature kern {
    pos a @foo 100;
} kern;
"""


def _testMissingClass():
    """
    >>> extractKerningData(_testMissingClass_fea) == (False, 'Undefined class: @foo', None, None)
    True
    """

# _testXXX_fea = """
# @foo = [x y z];

# feature kern {
#     pos a @foo 100 ;
# } kern;
# """

# def _testXXX():
#     """
#     >>> extractKerningData(_testXXX_fea)
#     (True, None, {('a', 'public.kern2.foo'): 100}, ({}, {'public.kern2.foo': set(['y', 'x', 'z'])}))
#     """


_testDuplicateKern1_fea = """
feature kern {
    pos a b 100;
    pos a b 100;
} kern;
"""


def _testDuplicateKern1():
    """
    >>> extractKerningData(_testDuplicateKern1_fea) == (False, 'Pair a, b defined more than once.', None, None)
    True
    """


_testDuplicateKern2_fea = """
feature kern {
    @a_group = [a aacute agrave];
    pos o @a_group 100;
    enum pos o [a aacute agrave] 100;
} kern;
"""


def _testDuplicateKern2():
    """
    >>> extractKerningData(_testDuplicateKern2_fea) == (False, 'Pair o, public.kern2.a_group defined more than once.', None, None)
    True
    """


_testGlyphInTooManyClasses_fea = """
feature kern {
    @a_group1 = [a aacute agrave];
    @a_group2 = [a];
    pos o @a_group1 100;
    pos o @a_group2 100;
} kern;
"""


def _testGlyphInTooManyClasses():
    """
    >>> extractKerningData(_testGlyphInTooManyClasses_fea) == (False, 'Glyph a in more than one class: public.kern2.a_group1 public.kern2.a_group2.', None, None)
    True
    """


_testConflictingExceptions_fea = """
feature kern {
    @left_a = [a aacute agrave];
    @right_a = [a aacute agrave];
    pos @left_a a 100;
    pos a @right_a 200;
} kern;
"""


def _testConflictingExceptions():
    """
    >>> extractKerningData(_testConflictingExceptions_fea) == (False, 'Conflicting pairs: public.kern1.left_a, a and a, public.kern2.right_a.', None, None)
    True
    """


_testDecomposedExceptions1_fea = """
feature kern {
    @kern1.H = [H I M];
    @kern2.O = [C G O Q];
    pos M Q -30;
    enum pos I [C G O Q] -20;
    pos @kern1.H @kern2.O -10;
} kern;
"""


def _testDecomposedExceptions1():
    """
    >>> expectedKerning = {
    ...     ('public.kern1.H', 'public.kern2.O'): -10,
    ...     ('I', 'public.kern2.O'): -20,
    ...     ('M', 'Q'): -30
    ... }
    >>> expectedGroups = (
    ...     {'public.kern1.H': set(['H', 'I', 'M'])},
    ...     {'public.kern2.O': set(['C', 'G', 'O', 'Q'])}
    ... )
    >>> success, message, kerning, groups = extractKerningData(_testDecomposedExceptions1_fea)
    >>> success
    True
    >>> kerning == expectedKerning
    True
    >>> groups == expectedGroups
    True
    """


_testDecomposedExceptions2_fea = """
feature kern {
    @kern1.H = [H I M];
    @kern2.O = [C G O Q];
    pos M Q -30;
    enum pos [H I M] C -20;
    pos @kern1.H @kern2.O -10;
} kern;
"""


def _testDecomposedExceptions2():
    """
    >>> expectedKerning = {
    ...     ('public.kern1.H', 'public.kern2.O'): -10,
    ...     ('public.kern1.H', 'C'): -20,
    ...     ('M', 'Q'): -30
    ... }
    >>> expectedGroups = (
    ...     {'public.kern1.H': set(['H', 'I', 'M'])},
    ...     {'public.kern2.O': set(['C', 'G', 'O', 'Q'])}
    ... )
    >>> success, message, kerning, groups = extractKerningData(_testDecomposedExceptions2_fea)
    >>> success
    True
    >>> kerning == expectedKerning
    True
    >>> groups == expectedGroups
    True
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
