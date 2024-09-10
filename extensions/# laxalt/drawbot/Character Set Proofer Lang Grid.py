'''
Character Set Proofer
* Peter Laxalt 2024

- Show all characters from your font
- Show reference characters for glyphs
- Show only a range of Unicode
- Group by Unicode range
- Adjust sizes and colors
- Adjust page size for print
'''

from glyphNameFormatter.reader import *

f = CurrentFont()
allUnis = list(uni2name.keys())

######################################################

### config

# colors
def setBackgroundColor():
    fill(0,0,0, 1)
    # fill(255,255,255, 1)
    rect(0, 0, pageWidth, pageHeight)

def setForegroundColor():
    fill(255,255,255, 1)
    # fill(0,0,0, 1)

# main variables
boxHeight = 110
fixedWidth = True

boxPaddingX = 20
boxPaddingY = 40
margin = 30

groupFontSize = 16
groupFontFamily = 'Dank Mono'

showReferenceFont = True
referenceFontFamily = 'Noto Sans JP Light'
# referenceFontFamily = 'Noto Serif Thai'
referenceFontSize = 20
# unicode groups
unicodeGroups = True
unicodeFilters = ['Hiragana', 'Katakana']
# unicodeFilters = ['Thai']

# return all glyphs at end
returnAllGlyphs = False
# define page size
size('TabloidLandscape')
# size('LetterLandscape')

######################################################

# set page size
pageWidth, pageHeight = width(), height()

# calculate initial positions
x = margin
y = pageHeight - margin - boxHeight

# set initial position
xBox, yBox = x, y

# calculate scale
s = float(boxHeight) / f.info.unitsPerEm

# background
setBackgroundColor()

# draw groups

uniRangeGroups = []

for i, glyphName in enumerate(f.glyphOrder):
    if glyphName == 'space':
        continue
    
    uniValue = n2u(glyphName)
    uniRange = u2r(uniValue)
    
    if uniRange not in uniRangeGroups:
        uniRangeGroups.append(uniRange)
        
print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')
print('‡‡‡ Current groups: ', uniRangeGroups)
print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')

def filter_arr(arr, filters):
    return [x for x in arr if x in filters]
        
if unicodeFilters:
    _originalGroups = uniRangeGroups
    uniRangeGroups = filter_arr(_originalGroups, unicodeFilters)
    print('')
    print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')
    print('‡‡‡ Filters: ', unicodeFilters)
    print('‡‡‡ Filtered groups: ', uniRangeGroups)
    print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')
    

if unicodeGroups and uniRangeGroups:
    for i, groupName in enumerate(uniRangeGroups):
        print(i)
            
        if groupName:

            # new page
            if i != 0:
                newPage(pageWidth, pageHeight)
                setBackgroundColor()
            
            # set position 
            xBox, yBox = x, y - (groupFontSize + margin)
            
            # add group name
            setForegroundColor()
            font(groupFontFamily, groupFontSize)
            text(groupName.upper(), (x, pageHeight - (margin + groupFontSize)))
            
            # loop through glyphs
            for i, glyphName in enumerate(f.glyphOrder):
            
                
                if glyphName == 'space':
                    continue
                
                # check glyph
                uniValue = n2u(glyphName)
                uniRange = u2r(uniValue)
                
                # draw glyph
                if groupName == uniRange:
                    g = f[glyphName]
                    print(uniValue)
                    
                    boxWidth = g.width*s
                    
                    if (fixedWidth):
                        boxWidth = boxHeight

                    # jump to next line
                    if xBox + boxWidth >= pageWidth - margin:
                        xBox = x
                        yBox -= boxHeight + boxPaddingY
                        # jump to next page
                        if yBox < margin:
                            yBox = y
                            newPage(pageWidth, pageHeight)
                            setBackgroundColor()
                            setForegroundColor()
                            font(groupFontFamily, groupFontSize)
                            text(groupName.upper() + ' (CONTINUED)', (x, pageHeight - (margin + groupFontSize)))
                            xBox, yBox = x, y - (groupFontSize + margin)

                    # draw glyph cell
                    #stroke(0, 0.5, 1)
                    fill(None)
                    rect(xBox, yBox, boxWidth, boxHeight)

                    # draw glyph
                    xGlyph = xBox
                    yGlyph = yBox - f.info.descender*s
                    save()
                    translate(xGlyph, yGlyph)
                    setForegroundColor()
                    stroke(None)
                    scale(s)
                    drawGlyph(g)
                    
                    # show reference
                    if showReferenceFont:     
                        font(referenceFontFamily, referenceFontSize * (s * 100))
                        text(chr(uniValue), (0, referenceFontSize * (s * -140)))
                        
                   
                    restore()
                                

                    # move to next glyph
                    xBox += boxWidth + boxPaddingX


######################################

# draw all glyphs

if returnAllGlyphs:
    newPage(pageWidth, pageHeight)
    setBackgroundColor()
    xBox, yBox = x, y

    for i, glyphName in enumerate(f.glyphOrder):
    
        if glyphName == 'space':
            continue

        g = f[glyphName]
        
        boxWidth = g.width*s
        
        if (fixedWidth):
            boxWidth = boxHeight

        # jump to next line
        if xBox + boxWidth >= pageWidth - margin:
            xBox = x
            yBox -= boxHeight + boxPaddingY
            # jump to next page
            if yBox < margin:
                yBox = y
                newPage(pageWidth, pageHeight)
                setBackgroundColor()

        # draw glyph cell
        # stroke(0, 0.5, 1)
        fill(None)
        rect(xBox, yBox, boxWidth, boxHeight)

        # draw glyph
        xGlyph = xBox
        yGlyph = yBox - f.info.descender*s
        save()
        translate(xGlyph, yGlyph)
        setForegroundColor()
        stroke(None)
        scale(s)
        drawGlyph(g)
        restore()

        # move to next glyph
        xBox += boxWidth + boxPaddingX