import re


def replaceKernFeature(features, kernFeature):
    leading, trailing = splitAtKern(features)
    return "\n".join([leading, kernFeature, trailing])


stringRE = re.compile(
    r"(\"[^$\"]*\")"
)
kernStartRE = re.compile(
    r"("
    r"feature"
    r"[\s\$]+"
    r"kern"
    r"[\s\$]*"
    r"\{"
    r")",
    re.MULTILINE
)
kernEndRE = re.compile(
    r"("
    r"}"
    r"[\s\$]*"
    r"kern"
    r"[\s\$]*"
    r";"
    r")",
    re.MULTILINE
)


def splitAtKern(text):
    if not text:
        return "", ""
    originalText = text
    # normalize line breaks.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # replace all strings with temporary placeholders.
    destringedLines = []
    stringReplacements = {}
    for line in text.splitlines():
        if "\"" in line:
            line = line.replace("\\\"", "__mm_temp_escaped_quote__")
            for found in stringRE.findall(line):
                temp = "__mm_temp_string_%d__" % len(stringReplacements)
                line = line.replace(found, temp, 1)
                stringReplacements[temp] = found.replace("__mm_temp_escaped_quote__", "\\\"")
            line = line.replace("__mm_temp_escaped_quote__", "\\\"")
        destringedLines.append(line)
    text = "\n".join(destringedLines)
    # replace all comments with temporary placeholders.
    decommentedLines = []
    commentReplacements = {}
    for line in text.splitlines():
        if "#" in line:
            line, comment = line.split("#", 1)
            temp = "$" * (5 + len(commentReplacements))
            commentReplacements[temp] = "#" + comment
            line += temp
        decommentedLines.append(line)
    text = "\n".join(decommentedLines)
    # search for kern
    kernStartMatch = kernStartRE.search(text)
    if kernStartMatch is None:
        return originalText + "\n", ""
    kernStart, kernEnd = kernStartMatch.span()
    kernEndMatch = kernEndRE.search(text[kernStart:])
    if kernEndMatch is not None:
        kernEnd = kernStart + kernEndMatch.span()[1]
    # split the text
    leadingText = text[:kernStart]
    trailingText = text[kernEnd:]
    # replace comments
    for temp, comment in reversed(sorted(commentReplacements.items())):
        leadingText = leadingText.replace(temp, comment)
        trailingText = trailingText.replace(temp, comment)
    # replace strings
    for temp, string in sorted(stringReplacements.items()):
        leadingText = leadingText.replace(temp, string)
        trailingText = trailingText.replace(temp, string)
    return leadingText, trailingText


splitTest1 = """
feature salt {
    sub foo by bar;
    # blah
} salt;

feature kern {
    pos foo bar -100;
} kern;

feature blah{
    sub blah by blah.alt;
} blah;
"""
splitTest1Result = """
feature salt {
    sub foo by bar;
    # blah
} salt;

---

feature blah{
    sub blah by blah.alt;
} blah;"""

splitTest2 = """
feature salt {
    sub foo by bar; # blah 1
    # blah 2
} salt;feature # blah 3
kern {pos foo bar -100;} # blah 4
kern # blah 5
;feature blah {
    sub blah by blah.alt;
} blah;
"""
splitTest2Result = """
feature salt {
    sub foo by bar; # blah 1
    # blah 2
} salt;---feature blah {
    sub blah by blah.alt;
} blah;"""

splitTest3 = """
feature salt {
    sub foo by bar;
    # blah
} salt;

feature kern {

feature blah{
    sub blah by blah.alt;
} blah;
"""
splitTest3Result = """
feature salt {
    sub foo by bar;
    # blah
} salt;

---

feature blah{
    sub blah by blah.alt;
} blah;"""

splitTest4 = """
feature salt {
    sub foo by bar;
    # blah
} salt;

feature blah{
    sub blah by blah.alt;
} blah;"""
splitTest4Result = """
feature salt {
    sub foo by bar;
    # blah
} salt;

feature blah{
    sub blah by blah.alt;
} blah;
---"""


def _testSplitAtKern(text):
    """
    >>> r = _testSplitAtKern(splitTest1)
    >>> r == splitTest1Result
    True

    >>> r = _testSplitAtKern(splitTest2)
    >>> r == splitTest2Result
    True

    >>> r = _testSplitAtKern(splitTest3)
    >>> r == splitTest3Result
    True

    >>> r = _testSplitAtKern(splitTest4)
    >>> r == splitTest4Result
    True
    """
    leading, trailing = splitAtKern(text)
    return "".join([leading, "---", trailing])


if __name__ == "__main__":
    import doctest
    doctest.testmod()
