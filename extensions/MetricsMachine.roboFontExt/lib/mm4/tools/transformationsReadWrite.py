import codecs
from io import StringIO
from xml.parsers.expat import ExpatError
from xml.etree.ElementTree import fromstring
from fontTools.misc.xmlWriter import XMLWriter
from mm4 import MetricsMachineError


def readTransformations(path):
    f = open(path, "rb")
    text = f.read()
    f.close()
    return _readTransformations(text)


def _readTransformations(text):
    """
    >>> read = _readTransformations(testTransformationsXML)
    >>> read == testTransformations
    True

    >>> read = _readTransformations(testTransformationsXML_old)
    >>> read == testTransformations
    True
    """
    # parse the XML
    try:
        tree = fromstring(text)
    except ExpatError:
        raise MetricsMachineError("Invalid XML syntax.")
    # get the transformations element
    transformations = tree.find("transformations")
    # no transformations
    if transformations is None:
        raise MetricsMachineError("No transformations in file.")
    # load the found transformations
    readTransformations = []
    for trans in transformations:
        transType = trans.tag
        # unknown transformation
        if transType not in ("copy", "remove", "scale", "shift", "round", "threshold"):
            raise MetricsMachineError("Unknown transformation type: %s" % transType)
        settings = dictFromItems(trans.items())
        # copy
        if transType == "copy":
            # convert old attribute names
            if "leftReplacement" in settings:
                settings["side1Replacement"] = settings.pop("leftReplacement")
            if "rightReplacement" in settings:
                settings["side2Replacement"] = settings.pop("rightReplacement")
            for key in ("pattern", "side1Replacement", "side2Replacement"):
                if key not in settings or not isinstance(settings[key], str):
                    raise MetricsMachineError("Invalid copy transformation definition.")
        # remove
        elif transType == "remove":
            if "pattern" not in settings and not isinstance(settings["pattern"], str):
                raise MetricsMachineError("Invalid remove transformation definition.")
        # scale
        elif transType == "scale":
            if "pattern" not in settings and not isinstance(settings["pattern"], str):
                raise MetricsMachineError("Invalid scale transformation definition.")
            if "value" not in settings:
                raise MetricsMachineError("Invalid scale transformation definition.")
            try:
                settings["value"] = float(settings["value"])
            except ValueError:
                raise MetricsMachineError("Invalid value specified in scale transformation.")
        # shift
        elif transType == "shift":
            if "pattern" not in settings and not isinstance(settings["pattern"], str):
                raise MetricsMachineError("Invalid shift transformation definition.")
            if "value" not in settings:
                raise MetricsMachineError("Invalid shift transformation definition.")
            try:
                settings["value"] = int(settings["value"])
            except ValueError:
                raise MetricsMachineError("Invalid value specified in shift transformation.")
        # round
        elif transType == "round":
            if "pattern" not in settings and not isinstance(settings["pattern"], str):
                raise MetricsMachineError("Invalid round transformation definition.")
            if "value" not in settings:
                raise MetricsMachineError("Invalid round transformation definition.")
            try:
                settings["value"] = int(settings["value"])
            except ValueError:
                raise MetricsMachineError("Invalid value specified in round transformation.")
            if "removeRedundantExceptions" not in settings:
                raise MetricsMachineError("Invalid round transformation definition.")
            try:
                settings["removeRedundantExceptions"] = bool(int(settings["removeRedundantExceptions"]))
            except ValueError:
                raise MetricsMachineError("Invalid removeRedundantExceptions specified in round transformation.")
        # threshold
        elif transType == "threshold":
            if "pattern" not in settings and not isinstance(settings["pattern"], str):
                raise MetricsMachineError("Invalid threshold transformation definition.")
            if "value" not in settings:
                raise MetricsMachineError("Invalid threshold transformation definition.")
            try:
                settings["value"] = int(settings["value"])
            except ValueError:
                raise MetricsMachineError("Invalid value specified in threshold transformation.")
            if "removeRedundantExceptions" not in settings:
                raise MetricsMachineError("Invalid threshold transformation definition.")
            try:
                settings["removeRedundantExceptions"] = bool(int(settings["removeRedundantExceptions"]))
            except ValueError:
                raise MetricsMachineError("Invalid removeRedundantExceptions specified in threshold transformation.")
        # store
        readTransformations.append(dict(type=transType.title(), settings=settings))
    # done
    return readTransformations


def dictFromItems(items):
    d = {}
    for k, v in items:
        d[k] = v
    return d


def writeTransformations(path, transformations):
    text = _writeTransformations(transformations)
    f = codecs.open(path, "wb", encoding="utf8")
    f.write(text)
    f.close()


def _writeTransformations(transformations):
    """
    >>> written = _writeTransformations(testTransformations)
    >>> written == testTransformationsXML
    True
    """
    ioFile = StringIO()
    writer = XMLWriter(ioFile, encoding="UTF-8")
    writer.begintag("xml")
    writer.newline()
    writer.begintag("transformations")
    writer.newline()
    for trans in transformations:
        transType = trans["type"].lower()
        settings = trans["settings"]
        if transType == "copy":
            writer.simpletag(transType, pattern=settings["pattern"], side1Replacement=settings["side1Replacement"], side2Replacement=settings["side2Replacement"])
        elif transType == "remove":
            writer.simpletag(transType, pattern=settings["pattern"])
        elif transType == "scale":
            writer.simpletag(transType, pattern=settings["pattern"], value=settings["value"])
        elif transType == "shift":
            writer.simpletag(transType, pattern=settings["pattern"], value=settings["value"])
        elif transType == "round":
            writer.simpletag(transType, pattern=settings["pattern"], value=settings["value"], removeRedundantExceptions=int(bool(settings["removeRedundantExceptions"])))
        elif transType == "threshold":
            writer.simpletag(transType, pattern=settings["pattern"], value=settings["value"], removeRedundantExceptions=int(bool(settings["removeRedundantExceptions"])))
        writer.newline()
    writer.endtag("transformations")
    writer.newline()
    writer.endtag("xml")
    text = ioFile.getvalue()
    return text


testTransformations = [
    dict(
        type="Copy",
        settings=dict(pattern="abc", side1Replacement="xyz", side2Replacement="123")
    ),
    dict(
        type="Remove",
        settings=dict(pattern="abc")
    ),
    dict(
        type="Scale",
        settings=dict(pattern="abc", value=.5)
    ),
    dict(
        type="Shift",
        settings=dict(pattern="abc", value=10)
    ),
    dict(
        type="Round",
        settings=dict(pattern="abc", value=10, removeRedundantExceptions=True)
    ),
    dict(
        type="Threshold",
        settings=dict(pattern="abc", value=10, removeRedundantExceptions=True)
    )
]

testTransformationsXML_old = """<?xml version="1.0" encoding="UTF-8"?>
<xml>
  <transformations>
    <copy leftReplacement="xyz" pattern="abc" rightReplacement="123"/>
    <remove pattern="abc"/>
    <scale pattern="abc" value="0.5"/>
    <shift pattern="abc" value="10"/>
    <round pattern="abc" removeRedundantExceptions="1" value="10"/>
    <threshold pattern="abc" removeRedundantExceptions="1" value="10"/>
  </transformations>
</xml>"""

testTransformationsXML = """<?xml version="1.0" encoding="UTF-8"?>
<xml>
  <transformations>
    <copy pattern="abc" side1Replacement="xyz" side2Replacement="123"/>
    <remove pattern="abc"/>
    <scale pattern="abc" value="0.5"/>
    <shift pattern="abc" value="10"/>
    <round pattern="abc" removeRedundantExceptions="1" value="10"/>
    <threshold pattern="abc" removeRedundantExceptions="1" value="10"/>
  </transformations>
</xml>"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()