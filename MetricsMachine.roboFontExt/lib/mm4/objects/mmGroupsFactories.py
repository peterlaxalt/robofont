from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix

from mm4 import MetricsMachineError


def glyphToGroupMapFactory(groups):
    glyphToSide1Group = {}
    glyphToSide2Group = {}

    for groupName, glyphList in groups.items():
        if groupName.startswith(side1Prefix):
            glyphDict = glyphToSide1Group
        elif groupName.startswith(side2Prefix):
            glyphDict = glyphToSide2Group
        else:
            continue
        for glyphName in glyphList:
            if glyphName in glyphDict and glyphDict[glyphName] != groupName:
                if groupName.startswith(side1Prefix):
                    side = "side 1"
                elif groupName.startswith(side2Prefix):
                    side = "side 2"
                raise MetricsMachineError("Glyph %s is in more than one %s group." % (glyphName, side))
            glyphDict[glyphName] = groupName
    return glyphToSide1Group, glyphToSide2Group
