'''
Character Set Proofer v2
* Peter Laxalt 2025

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
numColumns = 7  # Number of columns per page
heightRatio = 1.6  # Height ratio (1.0 = square, >1 = taller)

# glyph positioning
xOffset = 0  # Horizontal offset from center
yOffset = 30  # Vertical offset from center
glyphScale = 0.8  # Scale factor for glyphs (1.0 = 100%)

# spacing
margin = 20       # Page margin
cellPadding = 20  # Padding inside each glyph cell

# display options
showGlyphInfo = True     # Show glyph name and unicode value
showGlyphBorder = True   # Show border around each glyph cell
glyphInfoSize = 12      # Size of glyph info text

# group display
groupFontSize = 16
groupFontFamily = 'Dank Mono'

# reference font
showReferenceFont = True
referenceFontFamily = 'Noto Sans Regular'
# referenceFontFamily = 'Noto Serif Thai'
referenceFontSize = 45

# unicode groups
unicodeGroups = True
# unicodeFilters = []
unicodeFilters = []
# unicodeFilters = ['Thai']

# return all glyphs at end
returnAllGlyphs = False

# define page size
size('TabloidLandscape')
# size('LetterLandscape')

######################################################

# set page size
pageWidth, pageHeight = width(), height()

# calculate box dimensions based on number of columns
boxWidth = (pageWidth - (2 * margin)) / numColumns
boxHeight = boxWidth * heightRatio

# calculate initial positions
x = margin
y = pageHeight - margin - boxHeight

# set initial position
xBox, yBox = x, y

# calculate scale
s = float(boxWidth) / f.info.unitsPerEm * glyphScale

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
            # Calculate completion percentage for this group
            total_chars_in_group = 0
            completed_chars = 0
            for glyphName in f.glyphOrder:
                if glyphName != 'space':
                    uniValue = n2u(glyphName)
                    if u2r(uniValue) == groupName:
                        total_chars_in_group += 1
                        if f[glyphName].contours:  # Check if glyph has outlines
                            completed_chars += 1
            
            completion_percentage = int((completed_chars / total_chars_in_group * 100) if total_chars_in_group > 0 else 0)

            # new page
            if i != 0:
                newPage(pageWidth, pageHeight)
                setBackgroundColor()
            
            # set position 
            xBox, yBox = x, y - (groupFontSize + margin)
            
            # add group name with completion percentage
            setForegroundColor()
            font(groupFontFamily, groupFontSize)
            text(f"{groupName.upper()} / {completion_percentage}% COMPLETED", (x, pageHeight - (margin + groupFontSize)))
            
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

                    # jump to next line
                    if xBox + boxWidth >= pageWidth - margin:
                        xBox = x
                        yBox -= boxHeight
                        # jump to next page
                        if yBox < margin:
                            yBox = y
                            newPage(pageWidth, pageHeight)
                            setBackgroundColor()
                            setForegroundColor()
                            font(groupFontFamily, groupFontSize)
                            text(f"{groupName.upper()} (CONTINUED) / {completion_percentage}% COMPLETED", (x, pageHeight - (margin + groupFontSize)))
                            xBox, yBox = x, y - (groupFontSize + margin)

                    # draw glyph cell border if enabled
                    if showGlyphBorder:
                        stroke(1, 1, 1, 0.2)  # Light border
                        fill(None)
                        rect(xBox, yBox, boxWidth, boxHeight)
                    else:
                        stroke(None)
                        fill(None)

                    # draw glyph
                    xGlyph = xBox + (boxWidth - g.width*s)/2 + xOffset  # Center glyph horizontally + offset
                    yGlyph = yBox + (boxHeight - f.info.unitsPerEm*s)/2 + yOffset  # Center glyph vertically + offset
                    save()
                    translate(xGlyph, yGlyph)
                    setForegroundColor()
                    stroke(None)
                    scale(s)
                    drawGlyph(g)
                    restore()
                    
                    # show glyph info
                    setForegroundColor()
                    font(groupFontFamily, glyphInfoSize)
                    
                    # Glyph name in top left
                    text(glyphName, (xBox + cellPadding, yBox + boxHeight - cellPadding - glyphInfoSize))
                    
                    # Unicode value in bottom right
                    text(f"U+{uniValue:04X}", (xBox + boxWidth - cellPadding - 50, yBox + cellPadding))
                    
                    # Reference character in bottom left
                    if showReferenceFont:
                        font(referenceFontFamily, referenceFontSize)
                        text(chr(uniValue), (xBox + cellPadding, yBox + cellPadding))

                    # move to next glyph
                    xBox += boxWidth


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

        # jump to next line
        if xBox + boxWidth >= pageWidth - margin:
            xBox = x
            yBox -= boxHeight
            # jump to next page
            if yBox < margin:
                yBox = y
                newPage(pageWidth, pageHeight)
                setBackgroundColor()

        # draw glyph cell border if enabled
        if showGlyphBorder:
            stroke(1, 1, 1, 0.2)  # Light border
            fill(None)
            rect(xBox, yBox, boxWidth, boxHeight)
        else:
            stroke(None)
            fill(None)

        # draw glyph
        xGlyph = xBox + (boxWidth - g.width*s)/2 + xOffset  # Center glyph horizontally + offset
        yGlyph = yBox + (boxHeight - f.info.unitsPerEm*s)/2 + yOffset  # Center glyph vertically + offset
        save()
        translate(xGlyph, yGlyph)
        setForegroundColor()
        stroke(None)
        scale(s)
        drawGlyph(g)
        restore()
        
        # show glyph info
        setForegroundColor()
        font(groupFontFamily, glyphInfoSize)
        
        # Glyph name in top left
        text(glyphName, (xBox + cellPadding, yBox + boxHeight - cellPadding - glyphInfoSize))
        
        # Unicode value in bottom right
        uniValue = n2u(glyphName)
        text(f"U+{uniValue:04X}", (xBox + boxWidth - cellPadding - 50, yBox + cellPadding))
        
        # Reference character in bottom left
        if showReferenceFont:
            font(referenceFontFamily, referenceFontSize)
            text(chr(uniValue), (xBox + cellPadding, yBox + cellPadding))

        # move to next glyph
        xBox += boxWidth