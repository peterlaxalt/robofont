from glyphNameFormatter.reader import *

allUnis = list(uni2name.keys())
font = CurrentFont()

# Look up glyphs
glyphsLookup = ['々', '仝', 'ヽ', 'ヾ', 'ゝ', 'ゞ', '〃', '〱', '〲', '〳', '〵', '〴', '〵', '「', '」', '『', '』', '（', '）', '〔', '〕', '［', '］', '｛', '｝', '｟', '｠', '〈', '〉', '《', '》', '【', '】', '〖', '〗', '〘', '〙', '〚', '〛', 'っ', 'ッ', 'ー', '゛', '゜', '。', '、', '・', '゠', '＝', '〆', '〜', '…', '‥', '•', '◦', '﹅', '﹆', '※', '＊', '〽', '〓', '〇', '〒', '〶', '〠', '〄', 'Ⓧ', 'Ⓛ', 'Ⓨ']



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
