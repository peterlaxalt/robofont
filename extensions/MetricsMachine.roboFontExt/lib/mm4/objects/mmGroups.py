from io import StringIO

import defcon

from ufo2fdk.kernFeatureWriter import side1Prefix, side2Prefix

from mm4 import MetricsMachineImplementation, MetricsMachineError
from mm4.objects.orderedSet import OrderedSet
from mm4.objects.mmGroupsFactories import glyphToGroupMapFactory


defcon.registerRepresentationFactory(defcon.Groups, "metricsMachine.glyphToGroupsMap", glyphToGroupMapFactory)


groupColorKey = "com.typesupply.metricsMachine4.groupColors"
groupColorCycle = [
    (1.0, 0.0, 0.0, 0.35),
    (1.0, 0.5, 0.0, 0.35),
    (1.0, 1.0, 0.0, 0.35),
    # (0.5, 1.0, 0.0, 0.35),
    (0.0, 1.0, 0.0, 0.35),
    # (0.0, 1.0, 0.5, 0.35),
    (0.0, 1.0, 1.0, 0.35),
    (0.0, 0.5, 1.0, 0.35),
    (0.0, 0.0, 1.0, 0.35),
    (0.5, 0.0, 1.0, 0.35),
    (1.0, 0.0, 1.0, 0.35),
    (1.0, 0.0, 0.5, 0.35)
]
fallbackGroupColor = (.3, .3, .3, .2)


class MMGroups(MetricsMachineImplementation):

    changeNotificationName = "MMGroups.Changed"

    def init(self):
        self._groupColors = self.font.lib.get(groupColorKey, {})
        self._isMutable = False
        self._kerningData = {}
        self._kerningGroupCount = None

    def _get_kerning(self):
        font = self.font
        if font:
            return font.kerning
        return None

    kerning = property(_get_kerning)

    def postChangeNotification(self, groupNames, glyphNames=None):
        self.super().postNotification(notification=self.changeNotificationName, data=groupNames)

    # ----
    # dict
    # ----

    def keys(self):
        return self.super().keys()

    def values(self):
        return self.super().values()

    def items(self):
        return self.super().items()

    def __contains__(self, groupName):
        return groupName in self.super()

    def __getitem__(self, groupName):
        return self.super()[groupName]

    def __setitem__(self, groupName, value):
        self.super()[groupName] = value

    def __delitem__(self, groupName):
        del self.super()[groupName]

    def mutableCopy(self):
        # this mimics the MMutableGroup in the old MM
        # copy the group data, and set the parent font object
        font = self.font
        groups = defcon.Groups(font=font)
        groups.update(self.super())
        groups.metricsMachine._loadKerningData()
        groups.metricsMachine._originalGroups = {}
        glyphToSide1Group, glyphToSide2Group = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        groups.metricsMachine._originalGlyphToSide1Group = dict(glyphToSide1Group)
        groups.metricsMachine._originalGlyphToSide2Group = dict(glyphToSide2Group)
        for name, contents in font.groups.items():
            if not name.startswith(side1Prefix) and not name.startswith(side2Prefix):
                continue
            groups.metricsMachine._originalGroups[name] = list(contents)
        groups.metricsMachine._removedGroups = set()
        groups.metricsMachine._newGroups = set()
        groups.metricsMachine._renamedGroups = {}
        groups.metricsMachine._isMutable = True
        font.metricsMachine.mutableGroups = groups
        return groups

    def newGroup(self, groupName, postNotification=True):
        if self._isMutable:
            self._newGroup(groupName, postNotification)
        else:
            self[groupName] = []
            self._makeColorForGroup(groupName)
            if postNotification:
                self.postChangeNotification(set([groupName]), set([]))

    def _newGroup(self, groupName, postNotification=True):
        """
        >>> font = _setupTestFont1()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.Test")
        >>> sorted(groups.keys())
        ['public.kern1.Test']
        """
        if groupName in self:
            return
        self[groupName] = []
        self._makeColorForGroup(groupName)
        self._newGroups.add(groupName)
        if postNotification:
            self.postChangeNotification(set([groupName]), set([]))

    def renameGroup(self, oldName, newName, postNotification=True):
        if self._isMutable:
            self._renameGroup(oldName, newName, postNotification)
        else:
            self[newName] = self[oldName]
            del self[oldName]
            if postNotification:
                self.postChangeNotification(set([]))

    def _renameGroup(self, oldName, newName, postNotification=True):
        """
        # test groups
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups.metricsMachine.renameGroup("public.kern1.A", "public.kern1.MyA")
        >>> sorted(font.groups.metricsMachine.getSide1Groups())
        ['public.kern1.B', 'public.kern1.MyA']

        # test kerning
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : 100,
        ...     ("A.alt1", "public.kern2.A") : 75,
        ...     ("A.alt1", "A.alt1") : 50,
        ...     ("public.kern1.B", "public.kern2.B") : 25,
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.renameGroup("public.kern1.A", "public.kern1.MyA")
        >>> groups.metricsMachine.applyGroups()
        False
        >>> groups.metricsMachine.applyKerning()
        >>> sorted(font.kerning.keys())
        [('A.alt1', 'A.alt1'), ('A.alt1', 'public.kern2.A'), ('public.kern1.B', 'public.kern2.B'), ('public.kern1.MyA', 'public.kern2.A')]
        """
        # update group
        # get the appropriate dict
        glyphToSide1Group, glyphToSide2Group = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        if newName.startswith(side1Prefix):
            glyphToGroup = glyphToSide1Group
        else:
            glyphToGroup = glyphToSide2Group
        # update the group dict
        groups = self.super()
        groups[newName] = groups[oldName]
        del groups[oldName]
        # update the glyph to group mapping
        for glyphName in groups[newName]:
            glyphToGroup[glyphName] = newName
        # update kerning
        self._renameGroupWithinKerning(oldName, newName, self._kerningData)
        for pair, data in self._kerningData.items():
            if newName not in pair:
                continue
            self._renameGroupWithinKerning(oldName, newName, data["existingPairs"])
            self._renameGroupWithinKerning(oldName, newName, data["existingExceptions"])
            self._renameGroupWithinKerning(oldName, newName, data["addedPairs"])
        # update group color
        self._moveColorForGroup(oldName, newName)
        # update the initial reference data
        # for the name to be tracked it must:
        # - have been in in the initial groups
        # - not have been removed. removal would mean
        #   that this is not a renaming of the old group.
        oldestName = self._renamedGroups.get(oldName, oldName)
        if oldestName not in self._removedGroups and oldestName in self._originalGroups:
            if oldName in self._renamedGroups:
                self._renamedGroups[newName] = self._renamedGroups[oldName]
            else:
                self._renamedGroups[newName] = oldName
        # if this is a new group, replace the old name in the new group list
        if oldName in self._newGroups:
            self._newGroups.remove(oldName)
            self._newGroups.add(newName)

    def removeGroup(self, groupName, decompose=False, postNotification=True):
        if self._isMutable:
            self._removeGroup(groupName, decompose, postNotification)
        else:
            del self[groupName]
            if postNotification:
                self.postChangeNotification([groupName])

    def _removeGroup(self, groupName, decompose=False, postNotification=True):
        """
        # test groups
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.removeGroup("public.kern1.A")
        >>> sorted(groups.metricsMachine.getSide1Groups())
        ['public.kern1.B']

        # test kerning

        # decompose off
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : 100,
        ...     ("A.alt1", "public.kern2.A") : 75,
        ...     ("A.alt1", "A.alt1") : 50,
        ...     ("public.kern1.B", "public.kern2.B") : 25,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.removeGroup("public.kern2.A")
        >>> expected = {('public.kern1.A', 'A.alt1'): {'addedPairs': {('A.alt1', 'A.alt1'): 50},
        ...                               'existingExceptions': {},
        ...                               'existingPairs': {},
        ...                               'initialValue': None},
        ...             ('public.kern1.B', 'public.kern2.B'): {'addedPairs': {},
        ...                                 'existingExceptions': {},
        ...                                 'existingPairs': {('public.kern1.B', 'public.kern2.B'): 25},
        ...                                 'initialValue': 25}}

        # decompose on
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1", "A.alt2"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1", "A.alt2"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : 100,
        ...     ("A.alt1", "public.kern2.A") : 75,
        ...     ("A.alt1", "A.alt1") : 50,
        ...     ("public.kern1.B", "public.kern2.B") : 25,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.removeGroup("public.kern2.A", True)
        >>> expected = {('public.kern1.A', 'A'): {'addedPairs': {('public.kern1.A', 'A'): 100, ('A.alt1', 'A'): 75},
        ...                         'existingExceptions': {},
        ...                         'existingPairs': {},
        ...                         'initialValue': None},
        ...             ('public.kern1.A', 'A.alt1'): {'addedPairs': {('public.kern1.A', 'A.alt1'): 100, ('A.alt1', 'A.alt1'): 50},
        ...                              'existingExceptions': {},
        ...                              'existingPairs': {},
        ...                              'initialValue': None},
        ...             ('public.kern1.A', 'A.alt2'): {'addedPairs': {('public.kern1.A', 'A.alt2'): 100, ('A.alt1', 'A.alt2'): 75},
        ...                              'existingExceptions': {},
        ...                              'existingPairs': {},
        ...                              'initialValue': None},
        ...             ('public.kern1.B', 'public.kern2.B'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.B', 'public.kern2.B'): 25},
        ...                                'initialValue': 25}}
        >>> groups.metricsMachine._kerningData == expected
        True
        """
        # get the appropriate dict
        glyphToSide1Group, glyphToSide2Group = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        if groupName.startswith(side1Prefix):
            glyphToGroup = glyphToSide1Group
            isSide1Group = True
        else:
            glyphToGroup = glyphToSide2Group
            isSide1Group = False
        # remove kerning references
        pairsToSave = {}
        # gather all real pairs that should be saved
        for pair, data in self._kerningData.items():
            if groupName not in pair:
                continue
            for subPair, value in data["existingPairs"].items():
                if groupName in subPair:
                    continue
                pairsToSave[subPair] = value
            for subPair, value in data["existingExceptions"].items():
                if groupName in subPair:
                    continue
                pairsToSave[subPair] = value
            for subPair, value in data["addedPairs"].items():
                if groupName in subPair:
                    continue
                pairsToSave[subPair] = value
        # decompose grouped pairs
        if decompose:
            glyphList = self[groupName]
            for pair, data in self._kerningData.items():
                if groupName not in pair:
                    continue
                # 1. added pairs
                self._decomposePairs(groupName, glyphList, data["addedPairs"], pairsToSave, isSide1Group)
                # 2. existing exceptions
                self._decomposePairs(groupName, glyphList, data["existingExceptions"], pairsToSave, isSide1Group)
                # 3. existing pairs
                self._decomposePairs(groupName, glyphList, data["existingPairs"], pairsToSave, isSide1Group)
        # delete references
        for pair in list(self._kerningData.keys()):
            if groupName not in pair:
                continue
            del self._kerningData[pair]
        # handle groups
        # remove glyph to group mapping
        glyphList = self[groupName]
        for glyphName in glyphList:
            del glyphToGroup[glyphName]
        # remove the group
        del self[groupName]
        # store the kerning
        self._storePairs(pairsToSave)
        # remove the color
        if groupName in self._groupColors:
            self._removeColorForGroup(groupName)
        # update the initial reference data
        oldestName = self._renamedGroups.get(groupName, groupName)
        if oldestName in self._originalGroups:
            self._removedGroups.add(oldestName)
        if groupName in self._renamedGroups:
            del self._renamedGroups[groupName]
        # post a notification
        if postNotification:
            self.postChangeNotification(set([groupName]), set(glyphList))

    def addToGroup(self, groupName, glyphList, postNotification=True):
        if self._isMutable:
            self._addToGroup(groupName, glyphList, postNotification)
        else:
            existing = self[groupName]
            existing += [glyphName for glyphName in glyphList if glyphName not in existing]
            self[groupName] = existing
            self.postChangeNotification([groupName])

    def _addToGroup(self, groupName, glyphList, postNotification=True):
        """
        # test groups
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["A.alt2"])
        >>> groups["public.kern1.A"]
        ['A', 'A.alt1', 'A.alt2']

        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["B"])
        >>> groups["public.kern1.A"]
        ['A', 'A.alt1', 'A.alt2', 'B']
        >>> groups["public.kern1.B"]
        []
        >>> groups.metricsMachine.getSide1GroupForGlyph("B")
        'public.kern1.A'

        # test kerning
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : 100,
        ...     ("A.alt1", "public.kern2.A") : 75,
        ...     ("A.alt1", "A.alt1") : 50,
        ...     ("public.kern1.B", "public.kern2.B") : 25,
        ...     ("A.alt2", "A.alt2") : -25,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["A.alt2"])
        >>> expected = {('public.kern1.A', 'public.kern2.A'): {'addedPairs': {},
        ...                                'existingExceptions': {('A.alt1', 'public.kern2.A'): 75, ('A.alt1', 'A.alt1'): 50},
        ...                                'existingPairs': {('public.kern1.A', 'public.kern2.A'): 100},
        ...                                'initialValue': 100},
        ...             ('public.kern1.A', 'A.alt2'): {'addedPairs': {('A.alt2', 'A.alt2'): -25},
        ...                              'existingExceptions': {},
        ...                              'existingPairs': {},
        ...                              'initialValue': None},
        ...             ('public.kern1.B', 'public.kern2.B'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.B', 'public.kern2.B'): 25},
        ...                                'initialValue': 25}}
        >>> groups.metricsMachine._kerningData == expected
        True

        >>> groups.metricsMachine.addToGroup("public.kern2.A", ["A.alt2"])
        >>> expected = {('public.kern1.A', 'public.kern2.A'): {'addedPairs': {('A.alt2', 'A.alt2'): -25},
        ...                                'existingExceptions': {('A.alt1', 'public.kern2.A'): 75, ('A.alt1', 'A.alt1'): 50},
        ...                                'existingPairs': {('public.kern1.A', 'public.kern2.A'): 100},
        ...                                'initialValue': 100},
        ...             ('public.kern1.B', 'public.kern2.B'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.B', 'public.kern2.B'): 25},
        ...                                'initialValue': 25}}

        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A"],
        ...     "public.kern2.A" : ["A"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : 100,
        ...     ("B", "B") : 25,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["B"])
        >>> groups.metricsMachine.newGroup("public.kern1.B")
        >>> groups.metricsMachine.addToGroup("public.kern1.B", ["B"])
        >>> expected = {('public.kern1.A', 'public.kern2.A'): {'addedPairs': {},
        ...                            'existingExceptions': {},
        ...                            'existingPairs': {('public.kern1.A', 'public.kern2.A'): 100},
        ...                            'initialValue': 100},
        ...             ('public.kern1.B', 'B'): {'addedPairs': {('B', 'B'): 25},
        ...                            'existingExceptions': {},
        ...                            'existingPairs': {},
        ...                            'initialValue': None}}
        >>> groups.metricsMachine._kerningData == expected
        True

        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern2.O" : ["O", "C"]
        ... }
        >>> kerning = {
        ...     ("A", "C") : 100
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.addToGroup("public.kern2.O", ["O", "C"])
        >>> expected = {('A', 'public.kern2.O'): {'addedPairs': {},
        ...                     'existingExceptions': {('A', 'C'): 100},
        ...                     'initialValue': None,
        ...                     'existingPairs': {}}}
        >>> groups.metricsMachine._kerningData == expected
        True

        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern2.O" : ["O", "C"]
        ... }
        >>> kerning = {
        ...     ("A", "C") : 100
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.addToGroup("public.kern2.O", ["C"])
        >>> expected = {('A', 'public.kern2.O'): {'addedPairs': {},
        ...                     'existingExceptions': {('A', 'C'): 100},
        ...                     'initialValue': None,
        ...                     'existingPairs': {}}}
        >>> groups.metricsMachine._kerningData == expected
        True

        >>> font = _setupTestFont2()
        >>> groups = {
        ...     "public.kern2.h" : ["h", "k", "l"],
        ...     "public.kern1.AE" : ["AE"]
        ... }
        >>> kerning = {
        ...     ("public.kern1.AE", "b") : 100
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.addToGroup("public.kern2.h", ["b"])
        >>> groups.metricsMachine.applyGroups()
        True
        >>> expected = {('public.kern1.AE', 'public.kern2.h'):
        ...     {'haveConflict': True,
        ...     'finalValue': 0,
        ...     'pairs': {
        ...         ('public.kern1.AE', 'public.kern2.h'): {'resolution': 'group value', 'value': 0},
        ...         ('public.kern1.AE', 'b'): {'resolution': 'exception', 'value': 100}
        ...         }
        ...     }}
        >>> expected == groups.metricsMachine._kerningResolutionData
        True
        """
        glyphList = set(glyphList)
        # remove anything from the glyph list that is already in the group
        glyphList = glyphList - set(self[groupName])
        # all glyphs in the glyph list were already in the group.
        if not glyphList:
            return
        # get the appropriate glyph to group dict
        glyphToSide1Group, glyphToSide2Group = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        if groupName.startswith(side1Prefix):
            glyphToGroup = glyphToSide1Group
            isSide1Group = True
        else:
            glyphToGroup = glyphToSide2Group
            isSide1Group = False
        # delete and hold kerning references
        # remove glyphs from all old groups
        oldGroups = {}
        for glyphName in glyphList:
            oldGroup = glyphToGroup.get(glyphName)
            if oldGroup is None:
                continue
            if oldGroup not in oldGroups:
                oldGroups[oldGroup] = []
            if glyphName not in oldGroups[oldGroup]:
                oldGroups[oldGroup].append(glyphName)
        for oldGroupName, oldGroup in list(oldGroups.items()):
            self.removeFromGroup(oldGroupName, oldGroup)
        # remove any empty top level pairs
        for pair, data in list(self._kerningData.items()):
            if not data["existingPairs"] and not data["existingExceptions"] and not data["addedPairs"]:
                del self._kerningData[pair]
        # hold kerning referencing members of the glyph list
        holdingPairs = {}
        for (side1, side2), data in list(self._kerningData.items()):
            usableData = None
            if isSide1Group and side1 in glyphList:
                usableData = data
            elif not isSide1Group and side2 in glyphList:
                usableData = data
            if usableData is not None:
                holdingPairs.update(data["existingPairs"])
                holdingPairs.update(data["existingExceptions"])
                holdingPairs.update(data["addedPairs"])
                del self._kerningData[side1, side2]
        # handle the groups
        changedGroups = set()
        changedGlyphs = set()
        # remove glyphs from existing groups
        for glyphName in glyphList:
            if glyphName in glyphToGroup:
                if glyphToGroup[glyphName] != groupName:
                    otherGroupName = glyphToGroup[glyphName]
                    otherGroup = self[otherGroupName]
                    otherGroup.remove(glyphName)
                    changedGroups.add(otherGroupName)
        # add glyphs to the group
        changedGroups.add(groupName)
        group = self[groupName]
        for glyphName in sorted(glyphList):
            if glyphName not in group:
                group.append(glyphName)
            glyphToGroup[glyphName] = groupName
            changedGlyphs.add(glyphName)
        # store the kerning data
        self._storePairs(holdingPairs)
        # post a notification
        if postNotification:
            self.postChangeNotification(changedGroups, changedGlyphs)

    def removeFromGroup(self, groupName, glyphList, postNotification=True):
        if self._isMutable:
            self._removeFromGroup(groupName, glyphList, postNotification=True)
        else:
            existing = self[groupName]
            existing = [glyphName for glyphName in existing if glyphName not in glyphList]
            self[groupName] = existing
            if postNotification:
                self.postChangeNotification([groupName])

    def _removeFromGroup(self, groupName, glyphList, postNotification=True):
        """
        # test groups
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.removeFromGroup("public.kern1.A", ["A"])
        >>> groups["public.kern1.A"]
        ['A.alt1']

        # test kerning
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "public.kern2.A") : 100,
        ...     ("A.alt1", "public.kern2.A") : 75,
        ...     ("A.alt1", "A.alt1") : 50,
        ...     ("public.kern1.B", "public.kern2.B") : 25,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> groups.metricsMachine.removeFromGroup("public.kern1.A", ["A.alt1"])
        >>> expected = {('public.kern1.A', 'public.kern2.A'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.A', 'public.kern2.A'): 100},
        ...                                'initialValue': 100},
        ...             ('public.kern1.B', 'public.kern2.B'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.B', 'public.kern2.B'): 25},
        ...                                'initialValue': 25},
        ...             ('A.alt1', 'public.kern2.A'): {'addedPairs': {('A.alt1', 'public.kern2.A'): 75, ('A.alt1', 'A.alt1'): 50},
        ...                              'existingExceptions': {},
        ...                              'existingPairs': {},
        ...                              'initialValue': None}}
        >>> groups.metricsMachine._kerningData == expected
        True

        >>> groups.metricsMachine.removeFromGroup("public.kern1.B", ["B"])
        >>> expected = {('public.kern1.A', 'public.kern2.A'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.A', 'public.kern2.A'): 100},
        ...                                'initialValue': 100},
        ...             ('public.kern1.B', 'public.kern2.B'): {'addedPairs': {},
        ...                                'existingExceptions': {},
        ...                                'existingPairs': {('public.kern1.B', 'public.kern2.B'): 25},
        ...                                'initialValue': 25},
        ...             ('A.alt1', 'public.kern2.A'): {'addedPairs': {('A.alt1', 'public.kern2.A'): 75, ('A.alt1', 'A.alt1'): 50},
        ...                              'existingExceptions': {},
        ...                              'existingPairs': {},
        ...                              'initialValue': None}}
        >>> groups.metricsMachine._kerningData == expected
        True
        """
        changedGlyphs = set(glyphList)
        # get the appropriate glyph to group dict
        glyphToSide1Group, glyphToSide2Group = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        if groupName.startswith(side1Prefix):
            glyphToGroup = glyphToSide1Group
            isLeftGroup = True
        else:
            glyphToGroup = glyphToSide2Group
            isLeftGroup = False
        # remove and hold references to the glyphs
        holdingPairs = {}
        for pair, data in self._kerningData.items():
            if groupName not in pair:
                continue
            for glyphName in glyphList:
                holdingPairs.update(self._removeAndHoldKerningReferences(glyphName, None, data["existingPairs"], isLeftGroup))
                holdingPairs.update(self._removeAndHoldKerningReferences(glyphName, None, data["existingExceptions"], isLeftGroup))
                holdingPairs.update(self._removeAndHoldKerningReferences(glyphName, None, data["addedPairs"], isLeftGroup))
        # do the removal from the group
        group = self[groupName]
        for glyphName in glyphList:
            group.remove(glyphName)
            del glyphToGroup[glyphName]
        # store the kerning data
        self._storePairs(holdingPairs)
        # post a notification
        if postNotification:
            self.postChangeNotification(set([groupName]), changedGlyphs)

    def copyAndFlipGroups(self, groupNames):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern2.A" : ["A", "A.alt2"],
        ...     "public.kern2.B" : ["B"]
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "X") : -100,
        ...     ("X", "B") : -100,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()

        >>> mutableGroups.metricsMachine.copyAndFlipGroups(["public.kern2.A", "public.kern2.B"])
        >>> mutableGroups.metricsMachine.getSide1Groups()
        ['public.kern1.A', 'public.kern1.B']
        >>> mutableGroups["public.kern1.A"]
        ['A', 'A.alt2']
        >>> mutableGroups["public.kern1.B"]
        ['B']
        """
        changedGroups = set()
        changedGlyphs = set()
        for groupName in groupNames:
            if groupName.startswith(side1Prefix):
                flipName = side2Prefix + userFriendlyGroupName(groupName)
            else:
                flipName = side1Prefix + userFriendlyGroupName(groupName)
            if flipName in self:
                toRemove = OrderedSet(self[flipName]) - OrderedSet(self[groupName])
                self.removeFromGroup(flipName, toRemove, postNotification=False)
            else:
                self.newGroup(flipName, postNotification=False)
            glyphList = self[groupName]
            self.addToGroup(flipName, glyphList, postNotification=False)
            changedGroups.add(flipName)
            changedGlyphs = changedGlyphs | set(glyphList)
            # handle the color
            self.setColorForGroup(flipName, self.getColorForGroup(groupName), postNotification=False)
        self.postChangeNotification(changedGroups, changedGlyphs)

    def autoGroups(self, followDecomposition=False, suffixesToFollowBase=None):
        allChangedGroups = set()
        allChangedGlyphs = set()
        if suffixesToFollowBase:
            suffixesToFollowBase = set(suffixesToFollowBase)
            changedGroups, changedGlyphs = self._autoGroupsBasedOnSuffix(suffixesToFollowBase)
            allChangedGroups = allChangedGroups | changedGroups
            allChangedGlyphs = allChangedGlyphs | changedGlyphs
        if followDecomposition:
            changedGroups, changedGlyphs = self._autoGroupsBasedOnDecomposition()
            allChangedGroups = allChangedGroups | changedGroups
            allChangedGlyphs = allChangedGlyphs | changedGlyphs
        # post notification
        self.postChangeNotification(allChangedGroups, allChangedGlyphs)

    def getSuffixesAvailableForAutoGroups(self):
        """
        >>> font = _setupTestFont2()
        >>> for glyphName in list(font.keys()):
        ...    if glyphName.endswith(".alt"):
        ...         continue
        ...    glyph = font.newGlyph(glyphName + ".sc")
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.O" : ["O", "Otilde"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> sorted(groups.metricsMachine.getSuffixesAvailableForAutoGroups())
        ['alt', 'sc']
        """
        font = self.font
        suffixes = set()
        for glyphName in font.keys():
            if "." not in glyphName or glyphName.startswith("."):
                continue
            baseGlyphName, suffix = glyphName.split(".", 1)
            side1GroupName = self.getSide1GroupForGlyph(glyphName)
            if side1GroupName is None:
                suffixes.add(suffix)
                continue
            side2GroupName = self.getSide2GroupForGlyph(glyphName)
            if side2GroupName is None:
                suffixes.add(suffix)
        return suffixes

    def _autoGroupsBasedOnDecomposition(self):
        """
        >>> font = _setupTestFont2()
        >>> groups = {
        ...     "public.kern1.FlatLeft" : ["H", "N", "N.alt"],
        ...     "public.kern1.O" : [],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.autoGroups(followDecomposition=True)
        >>> sorted(groups["public.kern1.A"])
        ['A', 'Aacute', 'Abreve', 'Acircumflex', 'Adieresis', 'Agrave', 'Amacron', 'Aogonek', 'Aring', 'Aringacute', 'Atilde']
        >>> sorted(groups["public.kern1.FlatLeft"])
        ['H', 'Hcircumflex', 'N', 'N.alt', 'Nacute', 'Ncaron', 'Ntilde', 'Ntilde.alt']

        >>> # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        >>> # somehow the Ncommaacent is missing, probebly due to a change in AGL...
        >>> # ['H', 'Hcircumflex', 'N', 'N.alt', 'Nacute', 'Ncaron', 'Ncommaaccent', 'Ntilde', 'Ntilde.alt']
        >>> # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        >>> groups["public.kern1.O"]
        []
        """
        font = self.font
        # find the base of all composed glyphs
        bases = {}
        for glyphName in font.keys():
            glyph = font[glyphName]
            uniValue = glyph.unicode
            # skip ligatures here
            if "_" in glyphName:
                continue
            if uniValue is None:
                uniValue = font.unicodeData.pseudoUnicodeForGlyphName(glyphName)
            if uniValue is None:
                continue
            base = font.unicodeData.decompositionBaseForGlyphName(glyphName, True)
            if glyphName == base:
                continue
            if base not in bases:
                bases[base] = set([base])
            bases[base].add(glyphName)
        # compile the groups
        changedGroups = set()
        changedGlyphs = set()
        for base, glyphList in sorted(bases.items()):
            # left
            baseGroupName = self.getSide1GroupForGlyph(base)
            if baseGroupName is None:
                baseGroupName = self._findBaseGroupNameForAutoGroups(side1Prefix, base)
                self.newGroup(baseGroupName)
            toAdd = [glyphName for glyphName in glyphList if self.getSide1GroupForGlyph(glyphName) is None]
            self.addToGroup(baseGroupName, toAdd, postNotification=False)
            changedGroups.add(baseGroupName)
            changedGlyphs = changedGlyphs | set(toAdd)
            # right
            baseGroupName = self.getSide2GroupForGlyph(base)
            if baseGroupName is None:
                baseGroupName = self._findBaseGroupNameForAutoGroups(side2Prefix, base)
                self.newGroup(baseGroupName)
            toAdd = [glyphName for glyphName in glyphList if self.getSide2GroupForGlyph(glyphName) is None]
            self.addToGroup(baseGroupName, toAdd, postNotification=False)
            changedGroups.add(baseGroupName)
            changedGlyphs = changedGlyphs | set(toAdd)
        return changedGroups, changedGlyphs

    def _autoGroupsBasedOnSuffix(self, suffixesToFollowBase):
        """
        >>> font = _setupTestFont2()
        >>> for glyphName in list(font.keys()): # pack it into a list, this is a defcon issue
        ...    glyph = font.newGlyph(glyphName + ".sc")
        >>> groups = {
        ...     "public.kern1.A" : ["A", "Aacute", "Agrave"],
        ...     "public.kern2.O" : ["O", "Otilde"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.autoGroups(suffixesToFollowBase=["sc"])
        >>> sorted(groups["public.kern1.A.sc"])
        ['A.sc', 'Aacute.sc', 'Agrave.sc']
        >>> sorted(groups["public.kern2.O.sc"])
        ['O.sc', 'Otilde.sc']
        """
        font = self.font
        side1Additions = {}
        side2Additions = {}
        for glyphName in font.keys():
            if "." not in glyphName or glyphName.startswith("."):
                continue
            baseGlyphName, suffix = glyphName.split(".", 1)
            if suffix not in suffixesToFollowBase:
                continue
            # side1
            if self.getSide1GroupForGlyph(glyphName) is None:
                baseGroupName = self.getSide1GroupForGlyph(baseGlyphName)
                if baseGroupName is not None:
                    baseGroupName = userFriendlyGroupName(baseGroupName)
                    groupName = baseGroupName + "." + suffix
                    groupName = self._findBaseGroupNameForAutoGroups(side1Prefix, groupName)
                    if groupName not in side1Additions:
                        side1Additions[groupName] = set()
                    side1Additions[groupName].add(glyphName)
            # side2
            if self.getSide2GroupForGlyph(glyphName) is None:
                baseGroupName = self.getSide2GroupForGlyph(baseGlyphName)
                if baseGroupName is not None:
                    baseGroupName = userFriendlyGroupName(baseGroupName)
                    groupName = baseGroupName + "." + suffix
                    groupName = self._findBaseGroupNameForAutoGroups(side2Prefix, groupName)
                    if groupName not in side2Additions:
                        side2Additions[groupName] = set()
                    side2Additions[groupName].add(glyphName)
        changedGroups = set(side1Additions.keys()) | set(side2Additions.keys())
        changedGlyphs = set()
        for groupName, glyphList in list(side1Additions.items()) + list(side2Additions.items()):
            self.newGroup(groupName)
            self.addToGroup(groupName, glyphList, postNotification=False)
            changedGlyphs = changedGlyphs | glyphList
        return changedGroups, changedGlyphs

    def _findBaseGroupNameForAutoGroups(self, prefix, glyphName, count=0):
        if not count:
            name = prefix + glyphName
        else:
            name = prefix + glyphName + "_%d" % count
        if name in self:
            return self._findBaseGroupNameForAutoGroups(prefix, glyphName, count + 1)
        return name

    def clear(self, removeColors=True):
        groups = self.super()
        groups.holdNotifications()
        for groupName in list(groups.keys()):
            if groupName.startswith(side1Prefix) or groupName.startswith(side2Prefix):
                del groups[groupName]
        groups.releaseHeldNotifications()
        # remove colors
        if removeColors:
            font = self.font
            if groupColorKey in font.lib:
                del font.lib[groupColorKey]

    def update(self, other):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B"],
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> sorted(font.groups.items())
        [('public.kern1.A', ['A', 'A.alt1']), ('public.kern1.B', ['B']), ('public.kern2.A', ['A', 'A.alt1']), ('public.kern2.B', ['B'])]

        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt2"],
        ...     "public.kern1.C" : ["C", "Ccedilla"],
        ...     "public.kern2.C" : ["C", "Ccedilla"],
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> sorted(font.groups.items())
        [('public.kern1.A', ['A', 'A.alt2']), ('public.kern1.B', ['B']), ('public.kern1.C', ['C']), ('public.kern2.A', ['A', 'A.alt1']), ('public.kern2.B', ['B']), ('public.kern2.C', ['C'])]

        >>> groups = {
        ...     "public.kern1.A.alt2" : ["A.alt2"]
        ... }
        >>> try:
        ...     font.groups.metricsMachine.update(groups)
        ... except Exception as e:
        ...     e
        MetricsMachineError('Glyph A.alt2 is in more than one side 1 group.',)
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "NotInFont"]
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups["public.kern1.A"]
        ['A']
        """
        font = self.font
        groups = self.super()
        groups.holdNotifications()
        for groupName, glyphList in other.items():
            # filter out glyphs not in the font
            if groupName.startswith(side1Prefix) or groupName.startswith(side2Prefix):
                glyphList = [glyphName for glyphName in glyphList if glyphName in font]
            # don't turn other groups into sets
            else:
                glyphList = list(glyphList)
            groups[groupName] = glyphList
        groups.releaseHeldNotifications()
        # just call it
        groups.getRepresentation("metricsMachine.glyphToGroupsMap")

    def updateGroupColors(self, otherFont):
        """
        >>> groups = {
        ...     "public.kern1.A" : ["A"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern1.C" : ["C"],
        ... }
        >>> colors = {
        ...     "public.kern1.A" : (1, 1, 1, 1),
        ...     "public.kern1.B" : (0, 0, 0, 0),
        ... }
        >>> font = _setupTestFont1()
        >>> font.groups.metricsMachine.update(groups)
        >>> sourceFont = _setupTestFont1()
        >>> sourceFont.groups.update(groups)
        >>> sourceFont.lib[groupColorKey] = colors

        >>> font.groups.metricsMachine.updateGroupColors(sourceFont)
        >>> font.lib[groupColorKey]["public.kern1.A"]
        (1, 1, 1, 1)
        >>> font.lib[groupColorKey]["public.kern1.B"]
        (0, 0, 0, 0)
        >>> font.lib[groupColorKey].get("public.kern1.C")
        """

        font = self.font
        colors = font.lib.get(groupColorKey, {})
        otherColors = otherFont.lib.get(groupColorKey, {})
        for groupName in self.keys():
            if groupName in otherColors:
                colors[groupName] = otherColors[groupName]
        if colors:
            font.lib[groupColorKey] = colors

    # ------------
    # side lookups
    # ------------

    def getSide1Groups(self):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern2.E" : ["E", "E.alt1"]
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups.metricsMachine.getSide1Groups()
        ['public.kern1.A']
        """
        return [groupName for groupName in self.keys() if groupName.startswith(side1Prefix)]

    def getSide2Groups(self):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern2.E" : ["E", "E.alt1"]
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups.metricsMachine.getSide2Groups()
        ['public.kern2.E']
        """
        return [groupName for groupName in self.keys() if groupName.startswith(side2Prefix)]

    def getSide1GroupForGlyph(self, glyphName):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"]
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups.metricsMachine.getSide1GroupForGlyph("A")
        'public.kern1.A'
        >>> font.groups.metricsMachine.getSide1GroupForGlyph("X")
        """
        glyphToSide1Group, _ = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        return glyphToSide1Group.get(glyphName)

    def getSide2GroupForGlyph(self, glyphName):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern2.A" : ["A", "A.alt1"]
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups.metricsMachine.getSide2GroupForGlyph("A")
        'public.kern2.A'
        >>> font.groups.metricsMachine.getSide2GroupForGlyph("X")
        """
        _, glyphToSide2Group = self.super().getRepresentation("metricsMachine.glyphToGroupsMap")
        return glyphToSide2Group.get(glyphName)

    def _get_kerningGroupCount(self):
        return len(self.getSide1Groups() + self.getSide2Groups())

    kerningGroupCount = property(_get_kerningGroupCount)

    # --------------------
    # group representative
    # --------------------

    def getRepresentativeForGroup(self, groupName):
        """
        >>> font = _setupTestFont2()
        >>> groups = {
        ...     "public.kern1.H" : ["H", "I", "M"],
        ...     "public.kern1.O_L" : ["O", "D", "Q"],
        ...     "public.kern1.Nacute_L" : ["N", "Nacute", "Ntitle"],
        ...     "public.kern1.Foo" : ["A", "Aacute", "Abreve"]
        ... }
        >>> font.groups.metricsMachine.update(groups)
        >>> font.groups.metricsMachine.getRepresentativeForGroup("public.kern1.H")
        'H'
        >>> font.groups.metricsMachine.getRepresentativeForGroup("public.kern1.O_L")
        'O'
        >>> font.groups.metricsMachine.getRepresentativeForGroup("public.kern1.Nacute_L")
        'Nacute'
        >>> font.groups.metricsMachine.getRepresentativeForGroup("public.kern1.Foo")
        'A'
        """
        glyphs = self[groupName]
        base = userFriendlyGroupName(groupName)
        # base is a glyph name and the group contains the glyph name
        if base in glyphs:
            return base
        # find glyphs that match the beginning of the base
        # and use the one that is the closest match
        matches = {}
        for glyphName in glyphs:
            if base.startswith(glyphName):
                count = len(glyphName)
                if count not in matches:
                    matches[count] = []
                matches[count].append(glyphName)
        if matches:
            maxCount = max(matches.keys())
            matches = matches[maxCount]
            return sorted(matches)[0]
        # fall back to returning the first alphabetical member
        return sorted(glyphs)[0]

    # ------
    # colors
    # ------

    def autoGroupColors(self):
        for groupName in self.keys():
            self._removeColorForGroup(groupName)
        cycleCount = len(groupColorCycle)
        changedGlyphs = set()
        changedGroups = set()
        for index, groupName in enumerate(sorted(self.getSide1Groups())):
            colorIndex = index % cycleCount
            color = groupColorCycle[colorIndex]
            self.setColorForGroup(groupName, color, postNotification=False)
            changedGlyphs = changedGlyphs | set(self[groupName])
            changedGroups.add(groupName)
        for index, groupName in enumerate(sorted(self.getSide2Groups())):
            colorIndex = index % cycleCount
            color = groupColorCycle[colorIndex]
            self.setColorForGroup(groupName, color, postNotification=False)
            changedGlyphs = changedGlyphs | set(self[groupName])
            changedGroups.add(groupName)
        self.postChangeNotification(groupNames=set(changedGroups), glyphNames=changedGlyphs)

    def getColorForGroup(self, groupName):
        """
        >>> font = _setupTestFont1()
        >>> font.groups.metricsMachine.update({"public.kern1.A" : ["A"]})
        >>> color = font.groups.metricsMachine.getColorForGroup("public.kern1.A")
        >>> color == fallbackGroupColor
        True
        >>> font.groups.metricsMachine.newGroup("public.kern1.B")
        >>> color = font.groups.metricsMachine.getColorForGroup("public.kern1.B")
        >>> color == groupColorCycle[1]
        True
        """
        color = self._groupColors.get(groupName, fallbackGroupColor)
        return color

    def setColorForGroup(self, groupName, color, postNotification=True):
        """
        >>> font = _setupTestFont1()
        >>> font.groups.metricsMachine.newGroup("public.kern1.A")
        >>> color = (1, 1, 1, 1)
        >>> font.groups.metricsMachine.setColorForGroup("public.kern1.A", color)
        >>> color == font.groups.metricsMachine.getColorForGroup("public.kern1.A")
        True
        >>> font.groups.metricsMachine.copyAndFlipGroups(["public.kern1.A"])
        >>> color == font.groups.metricsMachine.getColorForGroup("public.kern2.A")
        True
        """
        self._groupColors[groupName] = color
        if postNotification:
            self.postChangeNotification(groupNames=set([groupName]), glyphNames=set(self[groupName]))

    def _makeColorForGroup(self, groupName):
        """
        >>> font = _setupTestFont1()
        >>> font.groups.metricsMachine.newGroup("public.kern1.A")
        >>> color = font.groups.metricsMachine.getColorForGroup("public.kern1.A")
        >>> color == groupColorCycle[0]
        True
        >>> font.groups.metricsMachine.newGroup("public.kern1.B")
        >>> color = font.groups.metricsMachine.getColorForGroup("public.kern1.B")
        >>> color == groupColorCycle[1]
        True
        >>> font.groups.metricsMachine.newGroup("public.kern1.C")
        >>> font.groups.metricsMachine.newGroup("public.kern1.D")
        >>> font.groups.metricsMachine.newGroup("public.kern1.E")
        >>> font.groups.metricsMachine.newGroup("public.kern1.F")
        >>> font.groups.metricsMachine.newGroup("public.kern1.G")
        >>> font.groups.metricsMachine.newGroup("public.kern1.H")
        >>> font.groups.metricsMachine.newGroup("public.kern1.I")
        >>> font.groups.metricsMachine.newGroup("public.kern1.J")
        >>> font.groups.metricsMachine.newGroup("public.kern1.K")
        >>> color = font.groups.metricsMachine.getColorForGroup("public.kern1.K")
        >>> color == groupColorCycle[0]
        True
        """
        if groupName.startswith(side1Prefix):
            groups = self.getSide1Groups()
        else:
            groups = self.getSide2Groups()
        colorIndex = (len(groups) - 1) % len(groupColorCycle)
        color = groupColorCycle[colorIndex]
        self._groupColors[groupName] = color

    def _moveColorForGroup(self, oldName, newName):
        """
        >>> font = _setupTestFont1()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.A")
        >>> color = groups.metricsMachine.getColorForGroup("public.kern1.A")
        >>> groups.metricsMachine.renameGroup("public.kern1.A", "public.kern1.B")
        >>> color == groups.metricsMachine.getColorForGroup("public.kern1.B")
        True
        """
        color = self._groupColors.get(oldName)
        if color is None:
            return
        self._groupColors[newName] = color
        del self._groupColors[oldName]

    def _removeColorForGroup(self, groupName):
        """
        >>> font = _setupTestFont1()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.A")
        >>> groups.metricsMachine.removeGroup("public.kern1.A")
        >>> color = groups.metricsMachine.getColorForGroup("public.kern1.A")
        >>> color == fallbackGroupColor
        True
        """
        if groupName not in self._groupColors:
            return
        del self._groupColors[groupName]

    def _storeGroupColors(self):
        lib = self.font.lib
        lib[groupColorKey] = dict(self._groupColors)

    # -------------
    # kerning tools
    # -------------

    def _defaultKerningDataStructure(self):
        d = dict(
            initialValue=None,
            existingPairs={},
            existingExceptions={},
            addedPairs={}
        )
        return d

    def _loadKerningData(self):
        kerning = self.font.kerning
        kerningData = self._kerningData = {}
        for pair, value in sorted(kerning.items()):
            # get the highest level pair
            highestPair = self._getHighestLevelPair(pair)
            # make a place to store the data
            data = kerningData.get(highestPair)
            if not data:
                data = self._defaultKerningDataStructure()
            # get the pair type
            isException = "exception" in kerning.metricsMachine.getPairType(pair)
            # store the pair and value
            if isException:
                data["existingExceptions"][pair] = value
            else:
                data["existingPairs"][pair] = value
                assert len(data["existingPairs"]) == 1
            if pair == highestPair:
                data["initialValue"] = value
            # store the data
            if highestPair not in kerningData:
                kerningData[highestPair] = data

    def _getHighestLevelPair(self, pair):
        side1, side2 = pair
        if side1.startswith(side1Prefix):
            side1Group = side1
        else:
            side1Group = self.getSide1GroupForGlyph(side1)
        if side2.startswith(side2Prefix):
            side2Group = side2
        else:
            side2Group = self.getSide2GroupForGlyph(side2)
        highestSide1 = side1
        if side1Group is not None:
            highestSide1 = side1Group
        highestSide2 = side2
        if side2Group is not None:
            highestSide2 = side2Group
        return highestSide1, highestSide2

    def _removeAndHoldKerningReferences(self, glyphName, groupName, data, isSide1Group):
        holdingPairs = {}
        for pair, value in list(data.items()):
            if groupName and groupName in pair:
                holdingPairs[pair] = value
                del data[pair]
            elif not groupName and glyphName in pair:
                if isSide1Group and pair[0] != glyphName:
                    continue
                elif not isSide1Group and pair[1] != glyphName:
                    continue
                else:
                    holdingPairs[pair] = value
                    del data[pair]
        return holdingPairs

    def _renameGroupWithinKerning(self, oldName, newName, data):
        newData = {}
        keysToRemove = []
        for pair, value in data.items():
            if oldName not in pair:
                continue
            side1, side2 = pair
            if side1 == oldName:
                side1 = newName
            if side2 == oldName:
                side2 = newName
            if (side1, side2) != pair:
                newData[side1, side2] = value
                keysToRemove.append(pair)
        for pair in keysToRemove:
            del data[pair]
        data.update(newData)

    def _decomposePairs(self, groupName, glyphList, data, storage, isSide1Group):
        for pair, value in data.items():
            if groupName not in pair:
                continue
            for glyphName in glyphList:
                side1, side2 = pair
                if isSide1Group:
                    testPair = (glyphName, side2)
                else:
                    testPair = (side1, glyphName)
                if testPair not in storage:
                    storage[testPair] = value

    def _storePairs(self, pairs):
        for pair, value in pairs.items():
            highestPair = self._getHighestLevelPair(pair)
            data = self._kerningData.get(highestPair)
            if not data:
                data = self._defaultKerningDataStructure()
            data["addedPairs"][pair] = value
            if highestPair not in self._kerningData:
                self._kerningData[highestPair] = data

    # ------------
    # finalization
    # ------------

    def _tearDownGroups(self):
        font = self.font
        if hasattr(font.metricsMachine, "mutableGroups"):
            del font.metricsMachine.mutableGroups

    # def _tearDownRepresentations(self):
    #     font = self.font
    #     for glyph in font:
    #         for name, kwargs in self._representationsToDestroy:
    #             glyph.destroyRepresentation(name, **kwargs)

    # def registerGroupDependentRepresentation(self, name, kwargs):
    #     self._representationsToDestroy.append((name, kwargs))

    def cancelEverything(self):
        self._tearDownGroups()
        # self._tearDownRepresentations()

    def applyGroups(self):
        """
        >>> kerning = {
        ...     ("Aogonek", "j") : 25
        ... }
        >>> font = _setupTestFont3()
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.A")
        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["A", "Aogonek", "Aacute"])
        >>> groups.metricsMachine.applyGroups()
        True
        >>> data = groups.metricsMachine._kerningResolutionData["public.kern1.A", "j"]
        >>> data["finalValue"]
        0
        >>> data["pairs"]["Aogonek", "j"]["resolution"]
        'exception'


        Test Case:
        The kerning has an exception, but the super pair has
        an implicit value of zero. The groups are nout touched.

        >>> kerning = {
        ...     ("Q", "semicolon") : 20
        ... }
        >>> groups = {
        ...     "public.kern1.O" : ["O", "Q"]
        ... }
        >>> font = _setupTestFont3()
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.applyGroups()
        False
        >>> groups.metricsMachine._kerningResolutionData["public.kern1.O", "semicolon"]["finalValue"]
        0

        Test Case:
        Flat kerning, then grouped. There are no conflicts.
        >>> kerning = {
        ...     ("E", "O") : 1,
        ...     ("E", "Q") : 1,
        ...     ("E", "OE") : 1,
        ...     ("AE", "O") : 1,
        ...     ("AE", "Q") : 1,
        ...     ("AE", "OE") : 1,
        ... }
        >>> font = _setupTestFont3()
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.E")
        >>> groups.metricsMachine.addToGroup("public.kern1.E", ["E", "AE"])
        >>> groups.metricsMachine.newGroup("public.kern2.O")
        >>> groups.metricsMachine.addToGroup("public.kern2.O", ["O", "Q", "OE"])
        >>> groups.metricsMachine.applyGroups()
        False
        >>> groups.metricsMachine._kerningResolutionData["public.kern1.E", "public.kern2.O"]["finalValue"]
        1

        Test Case:
        Remove a group and make sure that the resulting pairs aren't flagged as conflicts.
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.H" : ["H"],
        ...     "public.kern2.O" : ["O", "Q"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.H", "public.kern2.O") : 100,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.removeGroup("public.kern1.H", decompose=True)
        >>> groups.metricsMachine.applyGroups()
        False
        """
        # flag all glyphs referenced by the kerning
        glyphHasKerning = self._searchForGlyphKerning()
        # work out the resolutions
        self._kerningResolutionData = {}
        for superPair, superPairData in self._kerningData.items():
            # determine the final pair and the final value.
            # if no pairs were assigned to this super pair
            # before the group editing began, there will
            # be no final value determined here.

            # if this pair could have existed before, meaning the
            # groups existed, and it didn't exist, it has an implied
            # final value of zero. so, force this into the data.
            superSide1, superSide2 = superPair
            if not superPairData["existingPairs"] and superPairData["addedPairs"] and superPair not in superPairData["addedPairs"]:
                leftIsValid = False
                if superSide1.startswith(side1Prefix) and self._isOriginalGroup(superSide1):
                    leftIsValid = True
                if not superSide1.startswith(side1Prefix) and not self._glyphWasGroupedOnSide1(superSide1):
                    leftIsValid = True
                rightIsValid = False
                if superSide2.startswith(side2Prefix) and self._isOriginalGroup(superSide2):
                    rightIsValid = True
                if not superSide2.startswith(side2Prefix) and not self._glyphWasGroupedOnSide2(superSide2):
                    rightIsValid = True
                if leftIsValid and rightIsValid:
                    superPairData["existingPairs"][superPair] = 0

            finalPairs = dict(superPairData["existingPairs"])
            finalValue = set(finalPairs.values())
            if len(finalValue) == 0:
                # if there are existing exceptions, the implied final
                # value is zero. otherwise, there is no known final value.
                if superPairData["existingExceptions"]:
                    finalValue = 0
                else:
                    finalValue = None
            elif len(finalValue) == 1:
                finalValue = list(finalValue)[0]
            else:
                raise NotImplementedError

            # determine if a conflict exists based on the added pairs
            pairs, haveConflict = self._searchForConflict(superPairData, superPair, finalValue)
            # if not, and if no final value exists, grab the final value
            if finalValue is None and not haveConflict and pairs:
                finalValue = list(pairs.values())[0]["value"]

            # force the exceptions into the pairs
            exceptions = dict(superPairData["existingExceptions"])
            for subPair, value in exceptions.items():
                pairs[subPair] = dict(value=value, resolution="exception")

            # handle conflicts
            if haveConflict:
                # insert all possible implied pairs.
                impliedPairs = self._insertImpliedPairs(pairs, superPair)
                # if a final value is present, tag the pairs appropriately.
                if finalValue is not None:
                    self._resolveConflictsWithFinalValue(pairs, finalValue, impliedPairs)
                    # push the super pair into the pairs
                    if superPair not in pairs:
                        pairs[superPair] = dict(value=finalValue, resolution="group value")
                # otherwise, apply the resolution guessing algorithm.
                else:
                    finalValue = self._resolveConflictsWithoutFinalValue(pairs, superPair, impliedPairs, glyphHasKerning)
                # look for possible exceptions
                self._extendExceptionsToDecomposable(pairs, impliedPairs)
                # raise the exceptions if possible
                self._raiseExceptionLevel(pairs, superPair)

            # wrap it all up and store it
            data = dict(finalValue=finalValue, pairs=pairs, haveConflict=haveConflict)
            self._kerningResolutionData[superPair] = data

        # let the caller know if resolution is needed
        needResolution = bool(self.getAllPairsNeedingResolution())
        return needResolution

    def applyKerning(self):
        kerning = self.font.kerning
        groups = self.font.groups
        final = {}
        for pair, data in self._kerningResolutionData.items():
            value = data["finalValue"]
            exceptions = {}
            for subPair, pairData in data["pairs"].items():
                resolution = pairData["resolution"]
                if resolution == "exception":
                    exceptions[subPair] = pairData["value"]
            if value == 0:
                if exceptions:
                    final[pair] = value
            else:
                final[pair] = value
            exceptions = self._compressFinalExceptions(exceptions, pair)
            final.update(exceptions)
        groups.clear()
        groups.update(self)
        kerning.clear()
        kerning.update(final)
        self._storeGroupColors()
        self._tearDownGroups()

    # ------------------------------------------
    # conflict resolution intelligence internals
    # ------------------------------------------

    def _searchForGlyphKerning(self):
        """
        >>> kerning = {
        ...     ("A", "B") : 0,
        ...     ("B", "C") : 0,
        ... }
        >>> font = _setupTestFont3()
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> glyphHasKerning = groups.metricsMachine._searchForGlyphKerning()
        >>> glyphHasKerning["A"]
        True
        >>> glyphHasKerning["B"]
        True
        >>> glyphHasKerning["C"]
        True
        >>> glyphHasKerning["D"]
        False
        """
        font = self.font
        glyphHasKerning = dict.fromkeys(font.keys(), False)
        for (side1, side2) in self._kerningData.keys():
            glyphHasKerning[side1] = True
            glyphHasKerning[side2] = True
        return glyphHasKerning

    def _searchForConflict(self, superPairData, superPair, finalValue):
        """
        >>> font = _setupTestFont3()
        >>> groups = font.groups.metricsMachine.mutableCopy()

        >>> addedPairs = {
        ...     ("A", "A") : 1,
        ...     ("A", "B") : 2,
        ...     ("A", "C") : 3,
        ... }
        >>> finalValue = 1
        >>> superPairData = dict(addedPairs=addedPairs)
        >>> pairs, haveConflict = groups.metricsMachine._searchForConflict(superPairData, ("public.kern1.A", "public.kern2.X"), finalValue)
        >>> haveConflict
        True
        >>> pairs.keys() == addedPairs.keys()
        True

        >>> addedPairs = {
        ...     ("A", "A") : 1,
        ...     ("A", "B") : 1,
        ...     ("A", "C") : 1,
        ... }
        >>> finalValue = 1
        >>> superPairData = dict(addedPairs=addedPairs)
        >>> pairs, haveConflict = groups.metricsMachine._searchForConflict(superPairData, ("public.kern1.A", "public.kern2.X"), finalValue)
        >>> haveConflict
        False
        >>> pairs.keys() == addedPairs.keys()
        True
        """
        # look for conflict
        if finalValue is None:
            haveConflict = self._tryToCompressPair(superPairData, superPair)
        else:
            haveConflict = False
            for subPair, value in superPairData["addedPairs"].items():
                if value != finalValue:
                    haveConflict = True
                    break
        # wrap pairs
        pairs = {}
        for subPair, value in superPairData["addedPairs"].items():
            pairs[subPair] = dict(value=value, resolution=None)
        return pairs, haveConflict

    def _tryToCompressPair(self, pairData, superPair):
        """
        >>> kerning = {
        ...     ("A", "C") : -5,
        ...     ("A", "Ccedilla") : -5,
        ...     ("Aacute", "C") : -5,
        ...     ("Aacute", "Ccedilla") : -5,
        ... }
        >>> font = _setupTestFont3()
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.A")
        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["A", "Aacute"])
        >>> groups.metricsMachine.newGroup("public.kern2.C")
        >>> groups.metricsMachine.addToGroup("public.kern2.C", ["C", "Ccedilla"])
        >>> groups.metricsMachine.applyGroups()
        False

        >>> pairData = dict(
        ...     addedPairs= {
        ...         ("A", "C") : dict(value=-5, resolution=None),
        ...         ("A", "Ccedilla") : dict(value=-5, resolution=None),
        ...         ("Aacute", "C") : dict(value=-5, resolution=None),
        ...         ("Aacute", "Ccedilla") : dict(value=-5, resolution=None),
        ...     },
        ...     finalValue = None,
        ...     existingPairs = [],
        ...     existingExceptions = [],
        ... )
        >>> groups.metricsMachine._tryToCompressPair(pairData, ("public.kern1.A", "public.kern2.C"))
        False
        """
        superSide1, superSide2 = superPair
        addedPairs = pairData["addedPairs"]
        # test to make sure that all pairs have the same value
        haveCommonValue = True
        testValue = None
        for pair, value in addedPairs.items():
            if testValue is None:
                testValue = value
            elif value != testValue:
                haveCommonValue = False
                break
        if testValue is None or not haveCommonValue:
            return True
        # test to see if any higher level pairs are possible
        higherLevelPairs = set()
        for left, right in addedPairs.keys():
            higherLeft = None
            higherRight = None
            if not left.startswith(side1Prefix):
                higherLeft = self.getSide1GroupForGlyph(left)
            if not right.startswith(side2Prefix):
                higherRight = self.getSide2GroupForGlyph(right)
            if higherLeft is None and higherRight is None:
                continue
            higherLevelPairs.add((higherLeft, higherRight))
        if not higherLevelPairs:
            return False
        # test to make sure that all possible pairs are here
        allPossiblePairs = set()
        if superSide1.startswith(side1Prefix):
            left = self[superSide1]
        else:
            left = [superSide1]
        if superSide2.startswith(side2Prefix):
            right = self[superSide2]
        else:
            right = [superSide2]
        for l in left:
            for r in right:
                allPossiblePairs.add((l, r))
        knownPairs = set(addedPairs.keys())
        # match
        if allPossiblePairs == knownPairs:
            return False
        # fallback
        return True

    def _insertImpliedPairs(self, pairs, superPair):
        """
        >>> font = _setupTestFont3()

        >>> font.kerning.clear()
        >>> kerning = pairs = {
        ...     ("A", "H") : 0,
        ...     ("Aacute", "H") : 0,
        ...     ("Agrave", "H") : 0,
        ...     ("Atilde", "H") : 0,
        ... }
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.A")
        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["A", "Aacute", "Agrave", "Atilde", "Aring"])
        >>> sorted(groups.metricsMachine._insertImpliedPairs(pairs, ("public.kern1.A", "H")))
        [('Aring', 'H')]
        >>> groups.metricsMachine.cancelEverything()

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("public.kern1.A", "H") : 0,
        ...     ("Aacute", "H") : 0,
        ...     ("Agrave", "H") : 0,
        ...     ("Atilde", "H") : 0,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A"]
        ... }
        >>> pairs = {
        ...     ("Aacute", "H") : 0,
        ...     ("Agrave", "H") : 0,
        ...     ("Atilde", "H") : 0,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["Aacute", "Agrave", "Atilde", "Aring"])
        >>> sorted(groups.metricsMachine._insertImpliedPairs(pairs, ("public.kern1.A", "H")))
        [('Aring', 'H')]
        >>> groups.metricsMachine.cancelEverything()

        >>> font.kerning.clear()
        >>> kerning = pairs = {
        ...     ("A", "H") : 0,
        ...     ("A", "B") : 0,
        ...     ("A", "D") : 0,
        ...     ("A", "E") : 0,
        ... }
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern2.H")
        >>> groups.metricsMachine.addToGroup("public.kern2.H", ["H", "B", "D", "E", "F"])
        >>> sorted(groups.metricsMachine._insertImpliedPairs(pairs, ("A", "public.kern2.H")))
        [('A', 'F')]
        >>> groups.metricsMachine.cancelEverything()

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("A", "public.kern2.H") : 0,
        ...     ("A", "B") : 0,
        ...     ("A", "D") : 0,
        ...     ("A", "E") : 0,
        ... }
        >>> groups = {
        ...     "public.kern2.H" : ["H"]
        ... }
        >>> pairs = {
        ...     ("A", "B") : 0,
        ...     ("A", "D") : 0,
        ...     ("A", "E") : 0,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.addToGroup("public.kern2.H", ["B", "D", "E", "F"])
        >>> sorted(groups.metricsMachine._insertImpliedPairs(pairs, ("A", "public.kern2.H")))
        [('A', 'F')]
        >>> groups.metricsMachine.cancelEverything()

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("public.kern1.A", "V") : 25
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A"]
        ... }
        >>> pairs = {
        ...     ("public.kern1.A", "V") : 0
        ... }
        >>> font = _setupTestFont3()
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern2.V")
        >>> groups.metricsMachine.addToGroup("public.kern2.V", ["V", "W"])
        >>> sorted(groups.metricsMachine._insertImpliedPairs(pairs, ("public.kern1.A", "public.kern2.V")))
        [('public.kern1.A', 'W')]
        >>> groups.metricsMachine.cancelEverything()
        """
        left, right = superPair
        leftGroup = rightGroup = None
        if left.startswith(side1Prefix):
            leftGroup = left
            left = [left] + list(self[left])
        else:
            left = [left]
        if right.startswith(side2Prefix):
            rightGroup = right
            right = [right] + list(self[right])
        else:
            right = [right]
        impliedPairs = set()
        for l in left:
            for r in right:
                # if the left or right is a group and the group was not in the
                # initial groups, the pair cannot be implied since one member
                # didn't exist prior to this group editing session.
                if l.startswith(side1Prefix) and not self._isOriginalGroup(l):
                    continue
                if r.startswith(side2Prefix) and not self._isOriginalGroup(r):
                    continue
                # one of the glyphs was already part of this group at start up.
                # therefore it is covered by the group or is already a known exception.
                if leftGroup and self._isOriginalSide1GroupForGlyph(l, leftGroup):
                    continue
                if rightGroup and self._isOriginalSide2GroupForGlyph(r, rightGroup):
                    continue
                if (l, r) == superPair:
                    continue
                if (l, r) in pairs:
                    continue
                impliedPairs.add((l, r))
                pairs[l, r] = dict(value=0, resolution=None)
        return impliedPairs

    def _resolveConflictsWithFinalValue(self, pairs, finalValue, impliedPairs):
        """
        >>> font = _setupTestFont3()

        >>> pairs = {
        ...     ("A", "A") : dict(value=1, resolution=None),
        ...     ("A", "B") : dict(value=2, resolution=None),
        ...     ("A", "C") : dict(value=0, resolution=None),
        ...     ("A", "D") : dict(value=0, resolution=None),
        ... }
        >>> impliedPairs = [("A", "D")]
        >>> finalValue = 1
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine._resolveConflictsWithFinalValue(pairs, finalValue, impliedPairs)
        >>> pairs["A", "A"]["resolution"]
        'group value'
        >>> pairs["A", "B"]["resolution"]
        'exception'
        >>> pairs["A", "C"]["resolution"]
        'exception'
        >>> pairs["A", "D"]["resolution"]
        'follow group'
        """
        for subPair, subPairData in pairs.items():
            value = subPairData["value"]
            # matches final value.
            if value == finalValue:
                resolution = "group value"
            # implied zero. mark it as remove.
            elif value == 0 and subPair in impliedPairs:
                resolution = "follow group"
            # real value. mark it as an exception.
            else:
                resolution = "exception"
            subPairData["resolution"] = resolution

    def _resolveConflictsWithoutFinalValue(self, pairs, superPair, impliedPairs, glyphHasKerning):
        # rank the glyphs
        leftRankings, rightRankings = self._rankGlyphsInPairs(pairs, superPair, glyphHasKerning)
        # pick the highest ranked pair
        primaryPair = self._findMaxRank(pairs, leftRankings, rightRankings)
        finalValue = pairs[primaryPair]["value"]
        # now that a final value has been figured out, use the other resolution method.
        self._resolveConflictsWithFinalValue(pairs, finalValue, impliedPairs)
        return finalValue

    def _rankGlyphsInPairs(self, pairs, superPair, glyphHasKerning):
        """
        >>> font = _setupTestFont3()

        >>> kerning = pairs = {
        ...     ("A", "H") : 0,
        ...     ("Aacute", "H") : 0,
        ...     ("Agrave", "H") : 0,
        ...     ("Atilde", "H") : 0,
        ... }
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.A")
        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["A", "Aacute", "Agrave", "Atilde", "Aring"])
        >>> glyphHasKerning = groups.metricsMachine._searchForGlyphKerning()
        >>> groups.metricsMachine._rankGlyphsInPairs(pairs, ("public.kern1.A", "H"), glyphHasKerning)
        ({'A': 5, 'Aacute': 1, 'Agrave': 1, 'Atilde': 1}, {'H': 12})
        >>> groups.metricsMachine.cancelEverything()

        >>> font.kerning.clear()
        >>> kerning = {
        ...     ("public.kern1.A", "H") : 0,
        ...     ("Aacute", "H") : 0,
        ...     ("Agrave", "H") : 0,
        ...     ("Atilde", "H") : 0,
        ... }
        >>> groups = {
        ...     "public.kern1.A" : ["A"]
        ... }
        >>> pairs = {
        ...     ("Aacute", "H") : 0,
        ...     ("Agrave", "H") : 0,
        ...     ("Atilde", "H") : 0,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.addToGroup("public.kern1.A", ["Aacute", "Agrave", "Atilde", "Aring"])
        >>> glyphHasKerning = groups.metricsMachine._searchForGlyphKerning()
        >>> rank = groups.metricsMachine._rankGlyphsInPairs(pairs, ("public.kern1.A", "H"), glyphHasKerning)
        >>> rank == ({'A': 3, 'Aacute': 1, 'Agrave': 1, 'Atilde': 1}, {'H': 9})
        True
        >>> groups.metricsMachine.cancelEverything()
        """
        font = self.font
        superSide1, superSide2 = superPair
        # rank all of the glyphs
        leftRankings = {}
        rightRankings = {}
        for left, right in pairs.keys():
            # do the ranking
            for glyphName, groupName, ranking in [(left, superSide1, leftRankings), (right, superSide2, rightRankings)]:
                if not groupName.startswith("public.kern"):
                    groupName = None
                if glyphName not in ranking:
                    ranking[glyphName] = 0
                # glyph is actually a group.
                if glyphName.startswith("public.kern"):
                    # group is referenced by kerning. add one.
                    if glyphHasKerning[glyphName]:
                        ranking[glyphName] += 1
                # otherwise it is a glyph.
                else:
                    glyph = font[glyphName]
                    isPseudoUnicodeValue = False
                    uniValue = glyph.unicode
                    if uniValue is None:
                        uniValue = font.unicodeData.pseudoUnicodeForGlyphName(glyphName)
                        isPseudoUnicodeValue = True
                    # add one for the reference.
                    ranking[glyphName] += 1
                    # add one if it not a pseudo unicode.
                    if uniValue and not isPseudoUnicodeValue:
                        ranking[glyphName] += 1
                    # glyph can be decomposed and the base glyph is in the group.
                    # subtract one for the glyph name.
                    # add one for the base glyph name.
                    if uniValue is not None:
                        baseGlyphName = font.unicodeData.decompositionBaseForGlyphName(glyphName, True)
                        if glyphName != baseGlyphName:
                            if groupName is not None and baseGlyphName in self[groupName]:
                                if baseGlyphName not in ranking:
                                    ranking[baseGlyphName] = 0
                                ranking[baseGlyphName] += 1
                                ranking[glyphName] -= 1
                    # glyph has kerning. add one.
                    if glyphHasKerning[glyphName]:
                        ranking[glyphName] += 1
        return leftRankings, rightRankings

    def _findMaxRank(self, pairs, leftRankings, rightRankings):
        """
        >>> font = _setupTestFont3()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> pairs = {
        ...     ("A", "H") : dict(value=0),
        ...     ("A", "B") : dict(value=0),
        ...     ("A", "H.alt") : dict(value=0),
        ...     ("Aacute", "H") : dict(value=0),
        ...     ("Aacute", "B") : dict(value=0),
        ...     ("Aacute", "H.alt") : dict(value=0),
        ...     ("Atilde", "H") : dict(value=0),
        ...     ("Atilde", "B") : dict(value=0),
        ...     ("Atilde", "H.alt") : dict(value=0),
        ... }
        >>> leftRankings = {
        ...     "A" : 4,
        ...     "Aacute" : 0,
        ...     "Atilde" : -1
        ... }
        >>> rightRankings = {
        ...     "H" : 4,
        ...     "B" : 4,
        ...     "H.alt" : -1
        ... }
        >>> groups.metricsMachine._findMaxRank(pairs, leftRankings, rightRankings)
        ('A', 'H')
        """
        values = {}
        for (left, right), data in pairs.items():
            leftRank = leftRankings[left]
            rightRank = rightRankings[right]
            value = leftRank * rightRank
            if value not in values:
                values[value] = []
            values[value].append((leftRank, rightRank, abs(data["value"]), (left, right)))
        maxValue = max(values.keys())
        maxPairs = values[maxValue]
        # use the highest possible kerning value
        finalPair = max(maxPairs)[-1]
        return finalPair

    def _extendExceptionsToDecomposable(self, pairs, impliedPairs):
        """
        >>> pairs = {
        ...     ("O", "AE") : dict(value=1, resolution="group value"),
        ...     ("O", "AEacute") : dict(value=1, resolution="group value"),
        ...     ("Q", "AE") : dict(value=2, resolution="exception"),
        ...     ("Q", "AEacute") : dict(value=0, resolution="follow group"),
        ... }
        >>> impliedPairs = [("Q", "AEacute")]
        >>> font = _setupTestFont3()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine._extendExceptionsToDecomposable(pairs, impliedPairs)
        >>> pairs["Q", "AEacute"]["resolution"]
        'exception'
        >>> pairs["Q", "AEacute"]["value"]
        2
        """
        font = self.font
        # find all possible base exceptions
        baseExceptions = {}
        for (left, right), data in pairs.items():
            if data["resolution"] != "exception":
                continue
            if left.startswith(side1Prefix):
                leftBaseGlyph = left
            else:
                leftBaseGlyph = font.unicodeData.decompositionBaseForGlyphName(left, True)
            if right.startswith(side2Prefix):
                rightBaseGlyph = right
            else:
                rightBaseGlyph = font.unicodeData.decompositionBaseForGlyphName(right, True)
            if leftBaseGlyph == left and rightBaseGlyph == right:
                baseExceptions[left, right] = data["value"]
        # set the exception status where possible
        for (left, right), data in pairs.items():
            if data["resolution"] != "follow group":
                continue
            if left.startswith(side1Prefix):
                leftBaseGlyph = None
            else:
                leftBaseGlyph = font.unicodeData.decompositionBaseForGlyphName(left, True)
            if right.startswith(side2Prefix):
                rightBaseGlyph = None
            else:
                rightBaseGlyph = font.unicodeData.decompositionBaseForGlyphName(right, True)
            if (leftBaseGlyph, rightBaseGlyph) in baseExceptions:
                data["resolution"] = "exception"
                data["value"] = baseExceptions[leftBaseGlyph, rightBaseGlyph]

    def _raiseExceptionLevel(self, pairs, superPair):
        """
        >>> pairs = {
        ...     ("O", "AE") : dict(value=1, resolution="group value"),
        ...     ("O", "AEacute") : dict(value=1, resolution="group value"),
        ...     ("Q", "AE") : dict(value=2, resolution="exception"),
        ...     ("Q", "AEacute") : dict(value=2, resolution="exception")
        ... }
        >>> impliedPairs = [("Q", "AEacute")]
        >>> font = _setupTestFont3()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.O")
        >>> groups.metricsMachine.addToGroup("public.kern1.O", ["O", "Q"])
        >>> groups.metricsMachine.newGroup("public.kern2.AE")
        >>> groups.metricsMachine.addToGroup("public.kern2.AE", ["AE", "AEacute"])
        >>> groups.metricsMachine._raiseExceptionLevel(pairs, ("public.kern1.O", "public.kern2.AE"))
        >>> pairs["Q", "public.kern2.AE"]["resolution"]
        'exception'
        >>> pairs["Q", "public.kern2.AE"]["value"]
        2
        >>> ("Q", "AE") in pairs
        False
        >>> ("Q", "AEacute") in pairs
        False

        >>> pairs = {
        ...     ("Q", "i") : dict(value=1, resolution="group value"),
        ...     ("Q", "iacute") : dict(value=1, resolution="group value"),
        ...     ("Q", "j") : dict(value=2, resolution="exception")
        ... }
        >>> impliedPairs = [("Q", "jcircumflex")]
        >>> font = _setupTestFont3()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.newGroup("public.kern1.Q")
        >>> groups.metricsMachine.addToGroup("public.kern1.Q", ["Q"])
        >>> groups.metricsMachine.newGroup("public.kern2.i")
        >>> groups.metricsMachine.addToGroup("public.kern2.i", ["i", "iacute", "j", "jcircumflex"])
        >>> groups.metricsMachine._raiseExceptionLevel(pairs, ("public.kern1.Q", "public.kern2.i"))
        >>> pairs["public.kern1.Q", "j"]["resolution"]
        'exception'
        >>> pairs["public.kern1.Q", "j"]["value"]
        2
        >>> ("Q", "j") in pairs
        False
        >>> ("Q", "jcircumflex") in pairs
        False
        """
        side1GroupName, side2GroupName = superPair
        if not side1GroupName.startswith(side1Prefix) or not side2GroupName.startswith(side2Prefix):
            return
        side1Group = self[side1GroupName]
        side2Group = self[side2GroupName]
        compress = {}
        skip = set()
        for (side1, side2), data in pairs.items():
            if side1.startswith(side1Prefix) or side2.startswith(side2Prefix):
                continue
            if data["resolution"] != "exception":
                skip.add((side1, side2))
                continue
            foundside1Members = set()
            foundside2Members = set()
            compressable = set()
            for (otherside1, otherside2), otherData in pairs.items():
                if (otherside1, otherside2) in skip:
                    continue
                if otherData["resolution"] != "exception":
                    skip.add((otherside1, otherside2))
                    continue
                if otherData["value"] != data["value"]:
                    continue
                if otherside1 not in side1Group or otherside2 not in side2Group:
                    continue
                compressable.add((otherside1, otherside2))
                foundside1Members.add(otherside1)
                foundside2Members.add(otherside2)
            if len(foundside1Members) == len(side1Group):
                compress[side1GroupName, side2] = (compressable, data["value"])
                skip = skip | compressable
            elif len(foundside2Members) == len(side2Group):
                compress[side1, side2GroupName] = (compressable, data["value"])
                skip = skip | compressable
        for newPair, (subPairs, value) in compress.items():
            if newPair in pairs:
                continue
            for subPair in subPairs:
                del pairs[subPair]
            pairs[newPair] = dict(value=value, resolution="exception")

    def _compressFinalExceptions(self, exceptions, superPair):
        """
        >>> groups = {
        ...     "public.kern1.H" : ["H", "M", "N"],
        ...     "public.kern2.O" : ["O", "C", "G"],
        ... }
        >>> font = _setupTestFont3()
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> exceptions = {
        ...     ("H", "O") : 10,
        ...     ("H", "C") : 10,
        ...     ("H", "G") : 10,
        ...     ("M", "O") : 20,
        ...     ("M", "C") : 20,
        ...     ("M", "G") : 20,
        ...     ("N", "O") : 30,
        ...     ("N", "C") : 30,
        ...     ("N", "G") : 31,
        ... }
        >>> newExceptions = groups.metricsMachine._compressFinalExceptions(exceptions, ("public.kern1.H", "public.kern2.O"))
        >>> sorted(newExceptions.keys())
        [('H', 'public.kern2.O'), ('M', 'public.kern2.O'), ('N', 'C'), ('N', 'G'), ('N', 'O')]

        >>> exceptions = {
        ...     ("H", "O") : 10,
        ...     ("M", "O") : 10,
        ...     ("N", "O") : 10,
        ...     ("H", "C") : 20,
        ...     ("N", "C") : 20,
        ...     ("M", "C") : 20,
        ...     ("H", "G") : 30,
        ...     ("M", "G") : 30,
        ...     ("N", "G") : 30,
        ... }
        >>> newExceptions = groups.metricsMachine._compressFinalExceptions(exceptions, ("public.kern1.H", "public.kern2.O"))
        >>> sorted(newExceptions.keys())
        [('public.kern1.H', 'C'), ('public.kern1.H', 'G'), ('public.kern1.H', 'O')]

        >>> exceptions = {
        ...     ("H", "O") : 10,
        ...     ("M", "O") : 20,
        ...     ("N", "O") : 30,
        ...     ("H", "C") : 40,
        ...     ("N", "C") : 50,
        ...     ("M", "C") : 60,
        ...     ("H", "G") : 70,
        ...     ("M", "G") : 80,
        ...     ("N", "G") : 90,
        ... }
        >>> newExceptions = groups.metricsMachine._compressFinalExceptions(exceptions, ("public.kern1.H", "public.kern2.O"))
        >>> sorted(newExceptions.keys())
        [('H', 'C'), ('H', 'G'), ('H', 'O'), ('M', 'C'), ('M', 'G'), ('M', 'O'), ('N', 'C'), ('N', 'G'), ('N', 'O')]
        """
        superSide1, superSide2 = superPair
        possibleExceptions = set()
        if superSide1.startswith(side1Prefix):
            for side1, side2 in exceptions.keys():
                if side2.startswith(side2Prefix):
                    continue
                possibleExceptions.add((superSide1, side2))
        if superSide2.startswith(side2Prefix):
            for side1, side2 in exceptions.keys():
                if side1.startswith(side1Prefix):
                    continue
                possibleExceptions.add((side1, superSide2))
        for side1, side2 in possibleExceptions:
            toCompress = set()
            haveAll = True
            haveCommonValue = True
            testValue = None
            if side1.startswith(side1Prefix):
                if len(self[side1]) < 2:
                    continue
                for l in self[side1]:
                    if (l, side2) not in exceptions:
                        haveAll = False
                        break
                    if testValue is None:
                        testValue = exceptions[l, side2]
                    elif testValue != exceptions[l, side2]:
                        haveCommonValue = False
                        break
                    toCompress.add((l, side2))
            else:
                if len(self[side2]) < 2:
                    continue
                for r in self[side2]:
                    if (side1, r) not in exceptions:
                        haveAll = False
                        break
                    if testValue is None:
                        testValue = exceptions[side1, r]
                    elif testValue != exceptions[side1, r]:
                        haveCommonValue = False
                        break
                    toCompress.add((side1, r))
            if not haveAll or not haveCommonValue:
                continue
            for pair in toCompress:
                del exceptions[pair]
            exceptions[side1, side2] = testValue
        return exceptions

    # --------------------
    # kerning manipulation
    # --------------------

    def getBasicKerningDictForPairs(self, pairs):
        kerning = {}
        for (side1, side2) in pairs:
            side1Group = self.getSide1GroupForGlyph(side1)
            side2Group = self.getSide2GroupForGlyph(side2)
            orderedPairs = [(side1, side2), (side1, side2Group), (side1Group, side2), (side1Group, side2Group)]
            data = None
            superPair = None
            for pair in orderedPairs:
                if pair in self._kerningResolutionData:
                    data = self._kerningResolutionData[pair]
                    superPair = pair
                    break
            if data is None:
                continue
            kerning[superPair] = data["finalValue"]
            for subPair, subPairData in data["pairs"].items():
                if subPairData["resolution"] == "exception":
                    kerning[subPair] = subPairData["value"]
        return kerning

    def isGroupReferencedByKerning(self, groupName):
        for pair, data in self._kerningData.items():
            if groupName not in pair:
                continue
            for subPair in data["existingPairs"].keys():
                if groupName in subPair:
                    return True
            for subPair in data["existingExceptions"].keys():
                if groupName in subPair:
                    return True
            for subPair in data["addedPairs"].keys():
                if groupName in subPair:
                    return True
        return False

    def getAllPairsNeedingResolution(self):
        pairs = {}
        for pair, data in self._kerningResolutionData.items():
            if not data["haveConflict"]:
                pass
            else:
                pairs[pair] = data["finalValue"]
        return pairs

    def getValueForPair(self, pair):
        return self._kerningResolutionData[pair]["finalValue"]

    def getConflictsForPair(self, pair):
        return self._kerningResolutionData[pair]["pairs"]

    def setResolutionForPair(self, topLevelPair, pair, resolution):
        data = self._kerningResolutionData[topLevelPair]
        pairs = data["pairs"]
        if pairs[pair]["resolution"] == resolution:
            return False
        if resolution != "group value":
            pairs[pair]["resolution"] = resolution
            # if no primary pair value is set, set zero
            # to be the primary value.
            havePrimary = False
            for otherPair, otherData in pairs.items():
                if otherData["resolution"] == "group value":
                    havePrimary = True
                    break
            if not havePrimary:
                data["finalValue"] = 0
                for otherPair, otherData in pairs.items():
                    if otherData["value"] == 0:
                        otherData["resolution"] = "group value"
        else:
            value = pairs[pair]["value"]
            # set all pairs with the same value to be primary
            # and set all pairs previously set as primary
            # to exception. if a pair is zero and not in the
            # old kerning (meaning it is implied zero) and
            # it is not set to exception, set it to remove.
            for otherPair, otherData in pairs.items():
                if otherData["value"] != value:
                    if otherData["value"] == 0 and not self._isOriginalKerningPair(otherPair):
                        if otherData["resolution"] != "exception":
                            otherData["resolution"] = "follow group"
                    else:
                        otherData["resolution"] = "exception"
                elif otherData["value"] == value:
                    otherData["resolution"] = "group value"
            # update the final values
            if data["finalValue"] != value:
                data["finalValue"] = value
        return True

    # ---------------------
    # original data lookups
    # ---------------------

    def _isOriginalGroup(self, groupName):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern1.C" : ["C"],
        ...     "public.kern1.D" : ["D"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine._isOriginalGroup("public.kern1.A")
        True
        >>> groups.metricsMachine.removeGroup("public.kern1.B")
        >>> groups.metricsMachine._isOriginalGroup("public.kern1.B")
        False
        >>> groups.metricsMachine.renameGroup("public.kern1.C", "public.kern1.CC")
        >>> groups.metricsMachine._isOriginalGroup("public.kern1.CC")
        True
        >>> groups.metricsMachine.removeGroup("public.kern1.D")
        >>> groups.metricsMachine.newGroup("public.kern1.D", [])
        >>> groups.metricsMachine._isOriginalGroup("public.kern1.D")
        False
        """
        if groupName in self._newGroups:
            return False
        oldestName = self._renamedGroups.get(groupName, groupName)
        if oldestName in self._removedGroups:
            return False
        return oldestName in self._originalGroups

    def _isOriginalSide1GroupForGlyph(self, glyphName, groupName):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern1.A" : ["A"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern1.C" : ["C"],
        ...     "public.kern1.D" : ["D"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine._isOriginalSide1GroupForGlyph("A", "public.kern1.A")
        True
        >>> groups.metricsMachine.removeGroup("public.kern1.B")
        >>> groups.metricsMachine._isOriginalSide1GroupForGlyph("B", "public.kern1.B")
        False
        >>> groups.metricsMachine.renameGroup("public.kern1.C", "public.kern1.CC")
        >>> groups.metricsMachine._isOriginalSide1GroupForGlyph("C", "public.kern1.CC")
        True
        >>> groups.metricsMachine.removeGroup("public.kern1.D")
        >>> groups.metricsMachine.newGroup("public.kern1.D", [])
        >>> groups.metricsMachine._isOriginalSide1GroupForGlyph("D", "public.kern1.D")
        False
        """
        if not self._isOriginalGroup(groupName):
            return False
        oldestName = self._renamedGroups.get(groupName, groupName)
        return self._originalGlyphToSide1Group.get(glyphName) == oldestName

    def _isOriginalSide2GroupForGlyph(self, glyphName, groupName):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern2.A" : ["A"],
        ...     "public.kern2.B" : ["B"],
        ...     "public.kern2.C" : ["C"],
        ...     "public.kern2.D" : ["D"],
        ... }
        >>> font.groups.update(groups)
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine._isOriginalSide2GroupForGlyph("A", "public.kern2.A")
        True
        >>> groups.metricsMachine.removeGroup("public.kern2.B")
        >>> groups.metricsMachine._isOriginalSide2GroupForGlyph("B", "public.kern2.B")
        False
        >>> groups.metricsMachine.renameGroup("public.kern2.C", "public.kern2.CC")
        >>> groups.metricsMachine._isOriginalSide2GroupForGlyph("C", "public.kern2.CC")
        True
        >>> groups.metricsMachine.removeGroup("public.kern2.D")
        >>> groups.metricsMachine.newGroup("public.kern2.D", [])
        >>> groups.metricsMachine._isOriginalSide2GroupForGlyph("D", "public.kern2.D")
        False
        """
        if not self._isOriginalGroup(groupName):
            return False
        oldestName = self._renamedGroups.get(groupName, groupName)
        return self._originalGlyphToSide2Group.get(glyphName) == oldestName

    def _isOriginalKerningPair(self, pair):
        """
        >>> font = _setupTestFont1()
        >>> groups = {
        ...     "public.kern2.A" : ["A"],
        ...     "public.kern2.B" : ["B"],
        ...     "public.kern2.C" : ["C"],
        ...     "public.kern2.D" : ["D"],
        ...     "public.kern1.A" : ["A"],
        ...     "public.kern1.B" : ["B"],
        ...     "public.kern1.C" : ["C"],
        ...     "public.kern1.D" : ["D"],
        ... }
        >>> kerning = {
        ...     ("public.kern1.A", "A") : 100,
        ...     ("public.kern1.B", "A") : 100,
        ...     ("public.kern1.C", "A") : 100,
        ...     ("public.kern1.D", "A") : 100,
        ...     ("A", "public.kern2.A") : 100,
        ...     ("A", "public.kern2.B") : 100,
        ...     ("A", "public.kern2.C") : 100,
        ...     ("A", "public.kern2.D") : 100,
        ... }
        >>> font.groups.update(groups)
        >>> font.kerning.update(kerning)
        >>> keys = font.kerning.keys()
        >>> groups = font.groups.metricsMachine.mutableCopy()
        >>> groups.metricsMachine.removeGroup("public.kern1.B")
        >>> groups.metricsMachine.renameGroup("public.kern1.C", "public.kern1.CC")
        >>> groups.metricsMachine.removeGroup("public.kern1.D")
        >>> groups.metricsMachine.newGroup("public.kern1.D", [])
        >>> groups.metricsMachine.removeGroup("public.kern2.B")
        >>> groups.metricsMachine.renameGroup("public.kern2.C", "public.kern2.CC")
        >>> groups.metricsMachine.removeGroup("public.kern2.D")
        >>> groups.metricsMachine.newGroup("public.kern2.D", [])
        >>> groups.metricsMachine._isOriginalKerningPair(("public.kern1.A", "A"))
        True
        >>> groups.metricsMachine._isOriginalKerningPair(("A", "public.kern2.A"))
        True
        >>> groups.metricsMachine._isOriginalKerningPair(("public.kern1.B", "A"))
        False
        >>> groups.metricsMachine._isOriginalKerningPair(("A", "public.kern2.B"))
        False
        >>> groups.metricsMachine._isOriginalKerningPair(("public.kern1.CC", "A"))
        True
        >>> groups.metricsMachine._isOriginalKerningPair(("A", "public.kern2.CC"))
        True
        >>> groups.metricsMachine._isOriginalKerningPair(("public.kern1.D", "A"))
        False
        >>> groups.metricsMachine._isOriginalKerningPair(("A", "public.kern2.D"))
        False
        """
        side1, side2 = pair
        if side1.startswith(side1Prefix) and not self._isOriginalGroup(side1):
            return False
        if side2.startswith(side2Prefix) and not self._isOriginalGroup(side2):
            return False
        if side1.startswith(side1Prefix):
            side1 = self._renamedGroups.get(side1, side1)
        if side2.startswith(side2Prefix):
            side2 = self._renamedGroups.get(side2, side2)
        return (side1, side2) in self.font.kerning

    def _glyphWasGroupedOnSide1(self, glyphName):
        return glyphName in self._originalGlyphToSide1Group

    def _glyphWasGroupedOnSide2(self, glyphName):
        return glyphName in self._originalGlyphToSide2Group

    # -------------
    # import/export
    # -------------

    # UFO

    def getAvailableGroupsForImportFromUFO(self, path):
        return self._importGroupsFromUFO(path, groupNames=[], clearExisting=False, apply=False)

    def importGroupsFromUFO(self, path, groupNames, clearExisting):
        self._importGroupsFromUFO(path, groupNames=groupNames, clearExisting=clearExisting, apply=True)

    def _importGroupsFromUFO(self, path, apply, groupNames=[], clearExisting=False):
        from defcon import Font
        other = Font(path)
        return self._importGroupsFromFont(other, groupNames=groupNames, clearExisting=clearExisting, apply=apply)

    def _importGroupsFromFont(self, otherFont, groupNames, clearExisting, apply):
        """
        # set up the source font
        >>> otherFont = _setupTestFont1()
        >>> glyph = otherFont.newGlyph("NotInDestination")
        >>> mutableGroups = otherFont.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.A")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.A", ["A", "A.alt1"])
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.B")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.B", ["B", "NotInDestination"])
        >>> mutableGroups.metricsMachine.newGroup("public.kern2.B")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern2.B", ["B"])
        >>> mutableGroups.metricsMachine.applyGroups()
        False
        >>> mutableGroups.metricsMachine.applyKerning()

        # set up the destination font
        >>> font = _setupTestFont1()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.A")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.A", ["A", "A.alt2"])
        >>> mutableGroups.metricsMachine.applyGroups()
        False
        >>> mutableGroups.metricsMachine.applyKerning()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()

        # get available group names
        >>> groupNames = mutableGroups.metricsMachine._importGroupsFromFont(otherFont, [], False, False)
        >>> sorted(groupNames)
        ['public.kern1.A', 'public.kern1.B', 'public.kern2.B']
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A']

        # the import
        >>> r = mutableGroups.metricsMachine._importGroupsFromFont(otherFont, groupNames, True, True)
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A', 'public.kern1.B', 'public.kern2.B']
        >>> mutableGroups["public.kern1.A"]
        ['A', 'A.alt1']
        >>> mutableGroups["public.kern1.B"]
        ['B']
        """
        otherGroups = otherFont.groups.metricsMachine.mutableCopy()
        newGroupNames = otherGroups.metricsMachine.getSide1Groups() + otherGroups.metricsMachine.getSide2Groups()
        newGroups = {}
        for groupName in newGroupNames:
            newGroups[groupName] = (otherFont.groups[groupName], otherGroups.metricsMachine.getColorForGroup(groupName))
        if apply:
            self._importGroups(newGroups, groupNames=groupNames, clearExisting=clearExisting)
        return newGroups.keys()

    # MMG

    def getAvailableGroupsForImportFromMMG(self, path):
        f = open(path, "rb")
        text = f.read()
        f.close()
        return self._importGroupsFromMMG(text, groupNames=[], clearExisting=False, apply=False)

    def importGroupsFromMMG(self, path, groupNames, clearExisting):
        f = open(path, "rb")
        text = f.read()
        f.close()
        self._importGroupsFromMMG(text, groupNames=groupNames, clearExisting=clearExisting, apply=True)

    def _importGroupsFromMMG(self, text, groupNames, clearExisting, apply):
        """
        # set up the destination font
        >>> font = _setupTestFont1()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.A")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.A", ["A", "A.alt2"])
        >>> mutableGroups.metricsMachine.applyGroups()
        False
        >>> mutableGroups.metricsMachine.applyKerning()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()

        # get available group names
        >>> groupNames = mutableGroups.metricsMachine._importGroupsFromMMG(_testMMG, [], False, False)
        >>> sorted(groupNames)
        ['public.kern1.A', 'public.kern1.B', 'public.kern2.B']
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A']

        # the import
        >>> r = mutableGroups.metricsMachine._importGroupsFromMMG(_testMMG, groupNames, True, True)
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A', 'public.kern1.B', 'public.kern2.B']
        >>> mutableGroups["public.kern1.A"]
        ['A', 'A.alt1']
        >>> mutableGroups["public.kern1.B"]
        ['B']
        """
        from xml.etree.ElementTree import fromstring
        newGroups = {}
        tree = fromstring(text)
        for element in tree:
            if element.tag == "group":
                typ = element.get("type")
                if typ != "kerning":
                    continue
                name = element.get("name")
                side = element.get("side")
                color = element.get("color")
                if side == "left" or side == "side1":
                    name = side1Prefix + name
                elif side == "right" or side == "side2":
                    name = side2Prefix + name
                else:
                    raise MetricsMachineError
                if color:
                    try:
                        color = tuple([float(i) for i in color.split(" ") if i])
                    except ValueError:
                        raise MetricsMachineError
                glyphNames = None
                for subelement in element:
                    if subelement.tag != "glyphs":
                        raise MetricsMachineError
                    if glyphNames is not None:
                        raise MetricsMachineError
                    glyphNames = [i.strip() for i in subelement.text.splitlines() if i.strip()]
                    glyphNames = OrderedSet(glyphNames)
                newGroups[name] = (glyphNames, color)
        if apply:
            self._importGroups(newGroups, groupNames=groupNames, clearExisting=clearExisting)
        return newGroups.keys()

    # Feature File

    def getAvailableGroupsForImportFromFeatureFile(self, path):
        f = open(path, "rb")
        text = f.read()
        f.close()
        return self._importGroupsFromFeatureText(text, groupNames=[], clearExisting=False, apply=False)

    def importGroupsFromFeatureFile(self, path, groupNames, clearExisting):
        f = open(path, "rb")
        text = f.read()
        f.close()
        self._importGroupsFromFeatureText(text, groupNames=groupNames, clearExisting=clearExisting, apply=True)

    def _importGroupsFromFeatureText(self, text, groupNames, clearExisting, apply):
        from mm4.tools.feaImport import extractKerningData
        success, errorMessage, kerning, groups = extractKerningData(text)
        if not success:
            return errorMessage, {}
        side1Groups, side2Groups = groups
        groups = {}
        groups.update(side1Groups)
        groups.update(side2Groups)
        _groups = {}
        for name, glyphList in groups.items():
            _groups[name] = (glyphList, None)
        groups = _groups
        if apply:
            self._importGroups(groups, groupNames=groupNames, clearExisting=clearExisting)
        return errorMessage, groups.keys()

    # universal import method

    def _importGroups(self, newGroups, groupNames, clearExisting):
        """
        >>> groups = {
        ...  "public.kern1.A" : (["A"], None),
        ...  "public.kern2.A" : (["A"], None),
        ...  "public.kern1.B" : (["B"], None),
        ...  "public.kern2.B" : (["B"], None),
        ... }

        # import all groups, clear existing
        >>> font = _setupTestFont1()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.X")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.X", ["X"])
        >>> mutableGroups.metricsMachine.applyGroups()
        False
        >>> mutableGroups.metricsMachine.applyKerning()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine._importGroups(groups, groups.keys(), True)
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A', 'public.kern1.B', 'public.kern2.A', 'public.kern2.B']
        >>> mutableGroups["public.kern1.A"]
        ['A']
        >>> mutableGroups["public.kern1.B"]
        ['B']

        # import all groups, do not clear existing
        >>> font = _setupTestFont1()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.X")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.X", ["X"])
        >>> mutableGroups.metricsMachine.applyGroups()
        False
        >>> mutableGroups.metricsMachine.applyKerning()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine._importGroups(groups, groups.keys(), False)
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A', 'public.kern1.B', 'public.kern1.X', 'public.kern2.A', 'public.kern2.B']
        >>> mutableGroups["public.kern1.A"]
        ['A']
        >>> mutableGroups["public.kern1.B"]
        ['B']

        # import selected groups, clear existing
        >>> font = _setupTestFont1()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.newGroup("public.kern1.X")
        >>> mutableGroups.metricsMachine.addToGroup("public.kern1.X", ["X"])
        >>> mutableGroups.metricsMachine.applyGroups()
        False
        >>> mutableGroups.metricsMachine.applyKerning()
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine._importGroups(groups, ["public.kern1.A", "public.kern2.A"], True)
        >>> sorted(mutableGroups.keys())
        ['public.kern1.A', 'public.kern2.A']
        """
        # this tries to preserve as much kerning as possible.
        # to do this, groups not in the new groups will have
        # their kerning decomposed. groups that are in the new
        # groups, even if they do not contain the same glyphs,
        # will have their kerning preserved as is.

        # filter only to desired groups
        _newGroups = {}
        for groupName, glyphList in newGroups.items():
            if groupName not in groupNames:
                continue
            _newGroups[groupName] = glyphList
        newGroups = _newGroups

        font = self.font
        changedGroups = set()
        changedGlyphs = set()
        # remove groups
        if clearExisting:
            for groupName in sorted(self.keys()):
                if not groupName.startswith(side1Prefix) and not groupName.startswith(side2Prefix):
                    continue
                if groupName not in newGroups:
                    changedGroups.add(groupName)
                    changedGlyphs = changedGlyphs | set(self[groupName])
                    self.removeGroup(groupName, decompose=True, postNotification=True)
        # create new groups
        for groupName, (glyphList, color) in sorted(newGroups.items()):
            if groupName in self:
                toRemove = set(self[groupName]) - set(glyphList)
                self.removeFromGroup(groupName, toRemove, postNotification=False)
                changedGlyphs = changedGlyphs | set(toRemove)
            else:
                self.newGroup(groupName, postNotification=False)
            glyphList = [glyphName for glyphName in glyphList if glyphName in font]
            self.addToGroup(groupName, glyphList, postNotification=False)
            changedGroups.add(groupName)
            changedGlyphs = changedGlyphs | set(glyphList)
            # handle color
            if color is not None:
                self.setColorForGroup(groupName, color, postNotification=False)
        # post notification
        self.postChangeNotification(changedGroups, changedGlyphs)

    # MMG

    def exportGroupsToMMG(self, path):
        text = self._exportGroupsToMMG()
        with open(path, "wb") as f:
            f.write(text.encode("utf-8"))


    def _exportGroupsToMMG(self):
        """
        >>> import os
        >>> path = os.path.join(os.path.dirname(__file__), "_testMMG.mmg")

        >>> groups = {
        ...     "public.kern1.A" : ["A", "A.alt1"],
        ...     "public.kern1.B" : ["B", "B.alt1"],
        ...     "public.kern2.A" : ["A", "A.alt1"],
        ...     "public.kern2.B" : ["B", "B.alt1"],
        ... }
        >>> font = _setupTestFont1()
        >>> font.groups.update(groups)
        >>> mutableGroups = font.groups.metricsMachine.mutableCopy()
        >>> mutableGroups.metricsMachine.exportGroupsToMMG(path)
        >>> f = open(path, "rb")
        >>> text = f.read().decode("utf-8")
        >>> f.close()
        >>> os.remove(path)
        >>> text == _expectedMMGOutput
        True
        """
        from fontTools.misc.xmlWriter import XMLWriter
        ioFile = StringIO()
        writer = XMLWriter(ioFile)
        writer.begintag("xml")
        writer.newline()
        # side 1
        for groupName in sorted(self.getSide1Groups()):
            color = self.getColorForGroup(groupName)
            if color != fallbackGroupColor:
                color = " ".join([str(round(float(i), 2)) for i in color])
                writer.begintag("group", name=userFriendlyGroupName(groupName), side="side1", type="kerning", color=color)
            else:
                writer.begintag("group", name=userFriendlyGroupName(groupName), side="side1", type="kerning")
            writer.newline()
            writer.begintag("glyphs")
            writer.newline()
            for glyphName in sorted(self[groupName]):
                writer.write(glyphName)
                writer.newline()
            writer.endtag("glyphs")
            writer.newline()
            writer.endtag("group")
            writer.newline()
        # side 2
        for groupName in sorted(self.getSide2Groups()):
            color = self.getColorForGroup(groupName)
            if color != fallbackGroupColor:
                color = " ".join([str(round(float(i), 2)) for i in color])
                writer.begintag("group", name=userFriendlyGroupName(groupName), side="side2", type="kerning", color=color)
            else:
                writer.begintag("group", name=userFriendlyGroupName(groupName), side="side2", type="kerning")
            writer.newline()
            writer.begintag("glyphs")
            writer.newline()
            for glyphName in sorted(self[groupName]):
                writer.write(glyphName)
                writer.newline()
            writer.endtag("glyphs")
            writer.newline()
            writer.endtag("group")
            writer.newline()
        writer.endtag("xml")
        text = ioFile.getvalue()
        return text

    # ----------------
    # reference groups
    # ----------------

    def getReferenceGroupNames(self):
        return [name for name in self.keys() if not name.startswith(side1Prefix) and not name.startswith(side2Prefix)]

    def getReferenceGroup(self, name):
        return self[name]

    def getReferenceGroupsForGlyph(self, glyphName):
        found = []
        for groupName, glyphList in self.items():
            if groupName.startswith(side1Prefix):
                continue
            if groupName.startswith(side2Prefix):
                continue
            if glyphName in glyphList:
                found.append(groupName)
        return sorted(found)

    def newReferenceGroup(self, groupName, postNotification=True):
        self[groupName] = []
        if postNotification:
            self.postChangeNotification(set([groupName]))

    def renameReferenceGroup(self, oldName, newName, postNotification=True):
        self[newName] = self[oldName]
        del self[oldName]
        if postNotification:
            self.postChangeNotification(set([]))

    def removeReferenceGroup(self, name, postNotification=True):
        del self[name]
        if postNotification:
            self.postChangeNotification(set([name]))

    def addToReferenceGroup(self, groupName, glyphList, postNotification=True):
        existing = self[groupName]
        existing += [glyphName for glyphName in glyphList if glyphName not in existing]
        self[groupName] = existing
        if postNotification:
           self.postChangeNotification(set([groupName]))

    def removeFromReferenceGroup(self, groupName, glyphList, postNotification=True):
        existing = self[groupName]
        existing = [glyphName for glyphName in existing if glyphName not in glyphList]
        self[groupName] = existing
        if postNotification:
            self.postChangeNotification(set([groupName]))

    def getAvailableReferenceGroupsForImportFromUFO(self, path):
        return self._getReferenceGroupsFromUFO(path).keys()

    def _getReferenceGroupsFromUFO(self, path):
        other = defcon.Font(path)
        groups = {}
        for groupName, glyphList in other.groups.items():
            if groupName.startswith(side1Prefix):
                continue
            if groupName.startswith(side2Prefix):
                continue
            groups[groupName] = list(glyphList)
        return groups

    def importReferenceGroupsFromUFO(self, path, groupNames, clearExisting):
        # clear exising groups
        if clearExisting:
            toRemove = self.getReferenceGroupNames()
            for groupName in toRemove:
                self.removeReferenceGroup(groupName)
        else:
            toRemove = []
        # import new groups
        canImport = self._getReferenceGroupsFromUFO(path)
        toImport = {}
        for groupName, glyphList in canImport.items():
            if groupName not in groupNames:
                continue
            toImport[groupName] = list(glyphList)
        for groupName, glyphList in toImport.items():
            self.newReferenceGroup(groupName, postNotification=False)
            self.addToReferenceGroup(groupName, glyphList, postNotification=False)
        # post notification
        changed = list(set(toRemove) | set(toImport))
        self.postChangeNotification(changed)

# -----
# tools
# -----

def validateGroupName(name):
    """
    >>> validateGroupName("public.kern1.ABC.abc_123")
    True

    >>> validateGroupName("ABC.abc_123")
    False
    >>> validateGroupName("public.kern1.A123456789012345678901234567890")
    False

    >>> validateGroupName("public.kern1.A12345678901234567890123456789")
    True

    >>> validateGroupName("public.kern1.1ABC")
    False

    >>> validateGroupName("public.kern1..ABC")
    False

    >>> validateGroupName("public.kern1.ABC$")
    False

    >>> validateGroupName("public.kern1")
    False

    >>> validateGroupName("public.kern2.ABC.abc_123")
    True

    >>> validateGroupName("ABC.abc_123")
    False
    >>> validateGroupName("public.kern2.A123456789012345678901234567890")
    False

    >>> validateGroupName("public.kern2.A12345678901234567890123456789")
    True

    >>> validateGroupName("public.kern2.1ABC")
    False

    >>> validateGroupName("public.kern2..ABC")
    False

    >>> validateGroupName("public.kern2.ABC$")
    False

    >>> validateGroupName("public.kern2")
    False

    >>> validateGroupName("@test")
    False
    """
    # adapted from the FDK syntax spec:
    # http://partners.adobe.com/public/developer/opentype/afdko/topic_feature_file_syntax.html
    if not name.startswith(side1Prefix) and not name.startswith(side2Prefix):
        return False
    if len(name) <= len(side1Prefix):
        return False
    name = name[len(side1Prefix):]
    numbers = "0123456789"
    # "its maximum length is 30"
    if len(name) > 30:
        return False
    # "must not start with a digit or period"
    if name[0] in numbers or name[0] == ".":
        return False
    # "must be entirely comprised of characters from the following set:"
    validCharacters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._"
    for char in name:
        if char not in validCharacters:
            return False
    return True


def userFriendlyGroupName(groupName):
    """
    >>> userFriendlyGroupName("public.kern1.A")
    'A'
    """
    suffix = side1Prefix
    return groupName[len(suffix):]


def bracketedUserFriendlyGroupName(groupName):
    """
    >>> bracketedUserFriendlyGroupName("public.kern1.A")
    'A]'
    >>> bracketedUserFriendlyGroupName("public.kern2.A")
    '[A'
    """
    if groupName.startswith(side1Prefix):
        s = "%s]"
    else:
        s = "[%s"
    return s % userFriendlyGroupName(groupName)


# ------------
# test support
# ------------

def _setupBaseTestFont(glyphs):
    from mm4.implementation import registerImplementation
    from mm4.objects.mmGroups import MMGroups
    import defcon
    registerImplementation(MMGroups, defcon.Groups, allowsOverwrite=True)
    font = defcon.Font()
    for glyphName, uniValue in sorted(glyphs.items()):
        glyph = font.newGlyph(glyphName)
        glyph.unicode = uniValue
    return font


def _setupTestFont1():
    glyphs = {}
    for glyphName in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        glyphs[glyphName] = None
        for i in range(1, 3):
            glyphs["%s.alt%d" % (glyphName, i)] = None
    return _setupBaseTestFont(glyphs)


def _setupTestFont2():
    from fontTools.agl import AGL2UV
    glyphs = {}
    for glyphName, uniValue in AGL2UV.items():
        if isinstance(uniValue, list):
            uniValue = uniValue[0]
        glyphs[glyphName] = uniValue
    glyphs["N.alt"] = None
    glyphs["Ntilde.alt"] = None
    return _setupBaseTestFont(glyphs)


def _setupTestFont3():
    from fontTools.agl import AGL2UV
    glyphs = {}
    for glyphName, uniValue in AGL2UV.items():
        if isinstance(uniValue, list):
            uniValue = uniValue[0]
        glyphs[glyphName] = uniValue
    return _setupBaseTestFont(glyphs)


_testMMG = """<?xml version="1.0" encoding="UTF-8"?>
<xml>
 <group name="A" side="side1" type="kerning">
  <glyphs>
    A
    A.alt1
  </glyphs>
 </group>
 <group name="B" side="side1" type="kerning">
  <glyphs>
    B
    NotInDestination
  </glyphs>
 </group>
 <group name="B" side="side2" type="kerning">
  <glyphs>
    B
  </glyphs>
 </group>
</xml>
"""

_expectedMMGOutput = """<?xml version="1.0" encoding="UTF-8"?>
<xml>
  <group name="A" side="side1" type="kerning">
    <glyphs>
      A
      A.alt1
    </glyphs>
  </group>
  <group name="B" side="side1" type="kerning">
    <glyphs>
      B
      B.alt1
    </glyphs>
  </group>
  <group name="A" side="side2" type="kerning">
    <glyphs>
      A
      A.alt1
    </glyphs>
  </group>
  <group name="B" side="side2" type="kerning">
    <glyphs>
      B
      B.alt1
    </glyphs>
  </group>
</xml>"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()
