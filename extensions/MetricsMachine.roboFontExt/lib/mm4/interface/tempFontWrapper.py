import weakref
from defcon.objects.base import BaseObject
import defcon

from mm4.objects.contextStrings import MMContextStrings

from mojo.extensions import getExtensionDefault


class FontWrapper(BaseObject):

    def __init__(self, font):
        self.font = font
        self.kerning = defcon.Kerning(font)
        self.groups = defcon.Groups(font)
        self.contextStrings = MMContextStrings(self)
        defaultStrings = getExtensionDefault("com.typesupply.MM4.contextStrings")
        self.contextStrings.set(defaultStrings)
        self._glyphs = {}

    def _get__dispatcher(self):
        return self.font._dispatcher

    dispatcher = property(_get__dispatcher)

    def _get_glyphOrder(self):
        return self.font.glyphOrder

    glyphOrder = property(_get_glyphOrder)

    def _get_info(self):
        return self.font.info

    info = property(_get_info)

    def _get_unicodeData(self):
        return self.font.unicodeData

    unicodeData = property(_get_unicodeData)

    def setGlyphs(self, glyphs):
        for glyph in glyphs:
            if glyph.name not in self._glyphs:
                self._glyphs[glyph.name] = GlyphWrapper(glyph, self)

    def setKerning(self, kerning):
        self.kerning.clear()
        self.kerning.update(kerning)

    def setGroups(self, groups):
        self.groups.clear()
        self.groups.update(groups)

    def __del__(self):
        self.kerning = None
        self._glyphs = None
        super(FontWrapper, self).__del__()

    def keys(self):
        return self.font.keys()

    def __contains__(self, glyphName):
        return glyphName in self.font

    def __getitem__(self, glyphName):
        if glyphName not in self._glyphs:
            self._glyphs[glyphName] = GlyphWrapper(self.font[glyphName], self)
        return self._glyphs[glyphName]


class GlyphWrapper(BaseObject):

    def __init__(self, glyph, font):
        super(GlyphWrapper, self).__init__()
        self.glyph = glyph
        self.glyph.metricsMachine.tempGlyphWrapper = self
        self._font = weakref.ref(font)
        self._layerSet = weakref.ref(glyph.layerSet)
        self._layer = weakref.ref(glyph.layer)
        self._dispatcher = weakref.ref(font.dispatcher)

    def __del__(self):
        self.glyph.metricsMachine.tempGlyphWrapper = None
        self.glyph = None
        self._font = None
        self._layerSet = None
        self._layer = None
        self._dispatcher = None
        super(GlyphWrapper, self).__del__()

    def getParent(self):
        return self.font

    def _get_font(self):
        if self._font is None:
            return None
        return self._font()

    font = property(_get_font, doc="The :class:`Font` that this glyph belongs to.")

    def _get_layerSet(self):
        if self._layerSet is None:
            return None
        return self._layerSet()

    layerSet = property(_get_layerSet, doc="The :class:`LayerSet` that this glyph belongs to.")

    def _get_layer(self):
        if self._layer is None:
            return None
        return self._layer()

    layer = property(_get_layer, doc="The :class:`Layer` that this glyph belongs to.")

    def _get_name(self):
        return self.glyph.name

    name = property(_get_name)

    def _get_width(self):
        return self.glyph.width

    width = property(_get_width)

    def _get_template(self):
        return self.glyph.template

    template = property(_get_template)

    def getRepresentation(self, name, **kwargs):
        return self.glyph.getRepresentation(name, **kwargs)

    # pair counts

    def _get_side1GroupPairCount(self):
        return self.font.kerning.metricsMachine.getGlyphCounts()[self.name]["side1GroupCount"]

    side1GroupPairCount = property(_get_side1GroupPairCount)

    def _get_side1GlyphPairCount(self):
        return self.font.kerning.metricsMachine.getGlyphCounts()[self.name]["side1GlyphCount"]

    side1GlyphPairCount = property(_get_side1GlyphPairCount)

    def _get_side1ExceptionPairCount(self):
        return self.font.kerning.metricsMachine.getGlyphCounts()[self.name]["side1ExceptionCount"]

    side1ExceptionPairCount = property(_get_side1ExceptionPairCount)

    def _get_side2GroupPairCount(self):
        return self.font.kerning.metricsMachine.getGlyphCounts()[self.name]["side2GroupCount"]

    side2GroupPairCount = property(_get_side2GroupPairCount)

    def _get_side2GlyphPairCount(self):
        return self.font.kerning.metricsMachine.getGlyphCounts()[self.name]["side2GlyphCount"]

    side2GlyphPairCount = property(_get_side2GlyphPairCount)

    def _get_side2ExceptionPairCount(self):
        return self.font.kerning.metricsMachine.getGlyphCounts()[self.name]["side2ExceptionCount"]

    side2ExceptionPairCount = property(_get_side2ExceptionPairCount)
