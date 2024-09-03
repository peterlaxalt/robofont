from vanilla import Window, Button
from mojo.UI import AskYesNoCancel
from glyphNameFormatter.reader import u2n

# Define the component map with Unicode names prefixed by '$_'
COMPONENT_MAP = {
    "consonants": {
        "ㄱ": "$_KIYEOK",
        "ㄴ": "$_NIEUN",
        "ㄷ": "$_TIKEUT",
        "ㄹ": "$_RIEUL",
        "ㅁ": "$_MIEUM",
        "ㅂ": "$_PIEUP",
        "ㅅ": "$_SIOS",
        "ㅇ": "$_IEUNG",
        "ㅈ": "$_CIEUC",
        "ㅊ": "$_CHIEUCH",
        "ㅋ": "$_KHIEUKH",
        "ㅌ": "$_THIEUTH",
        "ㅍ": "$_PHIEUPH",
        "ㅎ": "$_HIEUH"
    },
    "vowels": {
        "ㅏ": "$_A",
        "ㅑ": "$_YA",
        "ㅓ": "$_EO",
        "ㅕ": "$_YEO",
        "ㅗ": "$_O",
        "ㅛ": "$_YO",
        "ㅜ": "$_U",
        "ㅠ": "$_YU",
        "ㅡ": "$_EU",
        "ㅣ": "$_I"
    }
}

def addTemplateGlyph(font, glyph_name):
    if glyph_name not in font:
        glyph = font.newGlyph(glyph_name)
        glyph.width = 600  # Set a default width
        glyph.template = True

def addUnicodeGlyph(font, hangul, template_name):
    unicode_value = ord(hangul)
    glyph_name = u2n(unicode_value)  # Get standardized glyph name
    glyph = font.newGlyph(glyph_name)
    glyph.unicode = unicode_value
    glyph.appendComponent(template_name)
    glyph.width = 600  # Set a default width

def addHangulComponents(sender):
    font = CurrentFont()
    if not font:
        print("Please open a font first.")
        return

    # Confirm with the user
    response = AskYesNoCancel("Add Hangul Components", "This will add Hangul component glyphs to your font. Proceed?")
    if response == 1:  # Yes
        # Add consonants
        for hangul, glyph_name in COMPONENT_MAP["consonants"].items():
            addTemplateGlyph(font, glyph_name)
            addUnicodeGlyph(font, hangul, glyph_name)

        # Add vowels
        for hangul, glyph_name in COMPONENT_MAP["vowels"].items():
            addTemplateGlyph(font, glyph_name)
            addUnicodeGlyph(font, hangul, glyph_name)

        font.update()
        print("Hangul components added successfully.")
    elif response == 0:  # No
        print("Operation cancelled.")
    else:  # Cancel
        print("Operation cancelled.")

class HangulTools:
    
    def __init__(self):
        self.w = Window((300, 100), "Hangul Tools")
        self.w.addComponentsButton = Button((10, 10, -10, 20), "Add Hangul Template Glyphs", callback=addHangulComponents)
        # Add more buttons here as needed
        self.w.open()

# Run the script
HangulTools()