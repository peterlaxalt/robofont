from glyphNameFormatter.reader import *

allUnis = list(uni2name.keys())
font = CurrentFont()

# Look up glyphs
glyphsLookup = [
    'Ȁ', 'Ȃ', 'Ǳ', 'ǲ', 'Ȅ', 'Ȇ', 'Ȉ', 'Ȋ', 'Ȍ', 'Ȏ', 'Ȑ', 'Ȓ', 'Ȕ', 'Ȗ',
    'ȁ', 'ȃ', 'ǳ', 'ȅ', 'ȇ', 'ȉ', 'ȋ', 'ŉ', 'ȍ', 'ȏ', 'ȑ', 'ȓ', 'ȕ', 'ȗ'
]


# Mark True to add them to font
addToFont = True


# Let it rip
for v in allUnis:
    
    for i in glyphsLookup:
        if chr(v) == i:
            print(hex(v), chr(v), u2n(v), u2r(v))
            
            if addToFont == True:
                glyphName = u2n(v)
                font.newGlyph(glyphName, clear=False)
                font.getGlyph(glyphName).autoUnicodes()
                print(font.getGlyph(glyphName))
