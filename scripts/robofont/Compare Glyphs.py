import ezui
from mojo.subscriber import Subscriber, registerRoboFontSubscriber
from mojo.roboFont import CurrentGlyph, CurrentFont
from glyphNameFormatter.reader import *


class GlyphVisualizer(Subscriber, ezui.WindowController):

    debug = True

    def build(self):
        self.glyph = CurrentGlyph()
        self.font = CurrentFont()

        margins = 10
        windowSize = 400
        scaleAdjust = .96

        self.chars = []

        content = """
        * VerticalStack @stack
        > [______________]   @stringTextField
        > * MerzView    @merzView
        """
        descriptionData = dict(
            stringTextField=dict(
                placeholder="Compare glyphs"
            ),
            merzView=dict(
                backgroundColor=(1, 1, 1, 0),
                delegate=self
            ),
            stack=dict(
                alignment="center"
            ),
        )

        self.w = ezui.EZWindow(
            title="Glyph Visualizer",
            content=content,
            size=(windowSize, windowSize),
            descriptionData=descriptionData,
            controller=self,
            margins=margins
        )

        merzView = self.w.getItem("merzView")
        container = merzView.getMerzContainer()
        container.setContainerScale(((windowSize * scaleAdjust) - (margins * 2)) / self.glyph.width)

        # a layer for the glyph and the baseline
        self.backgroundLayer = container.appendBaseSublayer(
            size=(self.glyph.width, self.glyph.font.info.unitsPerEm),
            backgroundColor=(1, 1, 1, 0)
        )

        self.glyphLayer = self.backgroundLayer.appendPathSublayer(
            position=(0, -self.glyph.font.info.descender)
        )
        glyphPath = self.glyph.getRepresentation("merz.CGPath")
        self.glyphLayer.setPath(glyphPath)
        self.glyphLayer.setFillColor(((255 / 128), 0, (255 / 255), .5))

        self.lineLayer = self.backgroundLayer.appendLineSublayer(
            startPoint=(0, -self.glyph.font.info.descender),
            endPoint=(self.glyph.width, -self.glyph.font.info.descender),
            strokeWidth=1,
            strokeColor=(1, 0, 0, 1)
        )

    def started(self):
        self.w.open()

    def glyphEditorDidSetGlyph(self, info):
        self.glyph = info['glyph']
        glyphPath = self.glyph.getRepresentation("merz.CGPath")
        self.glyphLayer.setPath(glyphPath)
        self.backgroundLayer.setSize((self.glyph.width, self.glyph.font.info.unitsPerEm))
        self.lineLayer.setEndPoint((self.glyph.width, -self.glyph.font.info.descender))
      
    def stringTextFieldCallback(self, sender):
        print(f"stringTextField: {sender.get()} {type(sender.get())}")

        def getGlyphByUnicode(char):
          font = CurrentFont()
          if font is not None:
              print(chr(char))

              # for glyph in font:
              #     if chr(glyph) == chr(char):
              #         return glyph
              return None
          else:
              print("No current font available.")
              return None

        for char in sender.get():
          print(f"getGlyphByUnicode: {getGlyphByUnicode(char)}")

if __name__ == '__main__':
    registerRoboFontSubscriber(GlyphVisualizer)
