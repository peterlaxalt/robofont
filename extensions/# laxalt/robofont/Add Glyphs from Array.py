from glyphNameFormatter.reader import *

allUnis = list(uni2name.keys())
font = CurrentFont()

# Look up glyphs
glyphsLookup = ['가', '까', '나', '다', '따', '라', '마', '바', '빠', '사', '싸', '아', '자', '짜', '차', '카', '타', '파', '하', '마', '맘', '머', '멈', '모', '몸', '무', '뭄', '뫄', '왐', '뭐', '뭘', '왜', '웰', '의', '욀', '삐', '뺄', '긓', '꼉', '뷁']


# Mark True to add them to font
addToFont = False


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
