from glyphNameFormatter.reader import *

allUnis = list(uni2name.keys())
counter = 0
charArray = []

for v in allUnis:
    if u2r(v) == "Hiragana" or u2r(v) == "Katakana":
        counter = counter + 1 
        charArray.append(chr(v))
        
        # Print everything
        print(counter, v, hex(v), chr(v), u2n(v), u2r(v))
        
        # Print only character
        # print(chr(v))
        
        # Add to array
        
print(charArray)
