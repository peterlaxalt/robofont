import json
import os
from mojo.UI import OpenWindow
from mojo.roboFont import CurrentFont
from vanilla import *

class KoreanFontGenerator:
    def __init__(self):
        self.w = Window((300, 100), "Korean Font Generator")
        self.w.addComponentsButton = Button((10, 10, -10, 20), "Add Hangul Components", callback=self.addHangulComponents)
        self.w.open()

    def addHangulComponents(self, sender):
        font = CurrentFont()
        if not font:
            print("Please open a font first.")
            return

        # Load the component map
        script_dir = os.path.dirname(os.path.abspath(__file__))
        component_map_path = os.path.join(script_dir, "..", "resources", "koreanComponentMap.json")
        with open(component_map_path, 'r') as f:
            component_map = json.load(f)

        # Add consonants
        for hangul, glyph_name in component_map["consonants"].items():
            self.addTemplateGlyph(font, glyph_name)
            self.addUnicodeGlyph(font, hangul, glyph_name)

        # Add vowels
        for hangul, glyph_name in component_map["vowels"].items():
            self.addTemplateGlyph(font, glyph_name)
            self.addUnicodeGlyph(font, hangul, glyph_name)

        font.update()
        print("Hangul components added successfully.")

    def addTemplateGlyph(self, font, glyph_name):
        if glyph_name not in font:
            glyph = font.newGlyph(glyph_name)
            glyph.width = 600  # Set a default width
            glyph.template = True

    def addUnicodeGlyph(self, font, hangul, template_name):
        unicode_value = ord(hangul)
        glyph = font.newGlyph(hangul)
        glyph.unicode = unicode_value
        glyph.appendComponent(template_name)
        glyph.width = 600  # Set a default width

KoreanFontGenerator()