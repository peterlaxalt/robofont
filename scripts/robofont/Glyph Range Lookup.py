from glyphNameFormatter.reader import *


################
# Define lookup

rangeLookup = "Thai"

################
# Variables

allUnis = list(uni2name.keys())
counter = 0
charArray = []

################
# Helpers

def contains_substring(main_string, substring):
    # Using the 'in' keyword
    if substring.lower() in main_string.lower() or main_string.lower().find(substring.lower()) != -1:
        return True
    else:
        return False

################
# Let it rip

for v in allUnis:
    if contains_substring(u2r(v), rangeLookup):
        counter = counter + 1 
        charArray.append(chr(v))
        
        # Print everything
        print(counter, v, hex(v), chr(v), u2n(v), u2r(v))
        
        # Print only character
        # print(chr(v))
        
        # Add to array
        
print('############################################')
print(charArray)
print('############################################')
print(counter, 'total glyphs')
