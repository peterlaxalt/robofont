from mm4 import MetricsMachineImplementation


class MMGlyph(MetricsMachineImplementation):

    # group name

    def _get_side1GroupName(self):
        font = self.font
        if hasattr(font.metricsMachine, "mutableGroups"):
            groups = font.metricsMachine.mutableGroups
        else:
            groups = font.groups
        return groups.metricsMachine.getSide1GroupForGlyph(self.super().name)

    side1GroupName = property(_get_side1GroupName)

    def _get_side2GroupName(self):
        font = self.font
        if hasattr(font.metricsMachine, "mutableGroups"):
            groups = font.metricsMachine.mutableGroups
        else:
            groups = font.groups
        return groups.metricsMachine.getSide2GroupForGlyph(self.super().name)

    side2GroupName = property(_get_side2GroupName)
