'''
Character Set Proofer v2
* Peter Laxalt 2025

A DrawBot script that creates a visual proof of font characters with the following features:
- Shows all characters from your font with optional reference overlays
- Shows reference characters for glyphs in a separate font
- Can filter to show only specific Unicode ranges
- Groups glyphs by Unicode range
- Configurable sizes, colors and layout
- Adjustable page size for print output
'''

# Import Unicode name/range mapping utilities
from glyphNameFormatter.reader import *

# Get current font and list of all Unicode values
f = CurrentFont()
allUnis = list(uni2name.keys())

######################################################

### Configuration Settings ###

# Background and foreground color functions
def setBackgroundColor():
    fill(1, 1, 1, 1) # White background
    rect(0, 0, pageWidth, pageHeight)

def setForegroundColor():
    fill(0, 0, 0, 1) # Black foreground for text elements

# Colors for the glyphs
glyphColor = (0, 0.6, 1, 0.8) # Semi-transparent blue for font glyph
referenceColor = (1, 0.4, 0, 0.8) # Semi-transparent orange for reference glyph

# Layout variables
numColumns = 7  # Number of columns per page
heightRatio = 1.6  # Cell height ratio (1.0 = square, >1 = taller)

# Position adjustments for the main font glyph
xOffset = 0  # Horizontal offset from cell center
yOffset = 30  # Vertical offset from cell center  
glyphScale = 0.8  # Scale factor for main glyphs (1.0 = 100%)

# Position adjustments for the reference glyph overlay
referenceXOffset = 0  # Horizontal offset for reference glyph from main glyph
referenceYOffset = 0  # Vertical offset for reference glyph from main glyph
referenceScale = 1.0  # Scale factor for reference glyph overlay

# Position adjustments for bottom reference characters
bottomLeftXOffset = 0  # Horizontal offset for bottom left reference character
bottomLeftYOffset = 0  # Vertical offset for bottom left reference character
bottomRightXOffset = 5  # Horizontal offset for bottom right glyph
bottomRightYOffset = 0  # Vertical offset for bottom right glyph

# Page and cell spacing
margin = 20       # Page margin in points
cellPadding = 20  # Padding inside each glyph cell

# Display toggles and text settings
showGlyphInfo = True     # Show glyph name and unicode value
showGlyphBorder = True   # Show border around each glyph cell
glyphInfoSize = 12      # Size of glyph info text in points

# Group header settings
groupFontSize = 16
groupFontFamily = 'Ormsby Mono Medium'

# Reference font configuration
showReferenceFont = True # Show reference font overlay in cell
showReferenceChar = True # Show reference character in bottom left corner
referenceFontFamily = 'FiraMono-Medium' # Font family for reference glyphs
# referenceFontFamily = 'Noto Serif Thai' # Alternative reference font
referenceFontSize = 45 # Size of reference character in bottom left

# Unicode grouping options
unicodeGroups = True # Group glyphs by Unicode range
unicodeFilters = [] # List of Unicode ranges to show (empty = show all)
# unicodeFilters = ['Thai'] # Example: Show only Thai range

# Additional options
returnAllGlyphs = False # Show all glyphs on final page

# Page size settings
size('TabloidLandscape') # 11x17 landscape
# size('LetterLandscape') # 8.5x11 landscape

######################################################

# Calculate page dimensions and initial positions
pageWidth, pageHeight = width(), height()

# Calculate cell dimensions based on number of columns
boxWidth = (pageWidth - (2 * margin)) / numColumns
boxHeight = boxWidth * heightRatio

# Set starting position for first cell
x = margin
y = pageHeight - margin - boxHeight
xBox, yBox = x, y

# Calculate scale factor based on font units per em
s = float(boxWidth) / f.info.unitsPerEm * glyphScale

# Draw page background
setBackgroundColor()

# Initialize list for Unicode range groups
uniRangeGroups = []

# Build list of unique Unicode ranges from font
for i, glyphName in enumerate(f.glyphOrder):
    if glyphName == 'space':
        continue
    
    uniValue = n2u(glyphName) # Get Unicode value for glyph
    uniRange = u2r(uniValue) # Get Unicode range name
    
    if uniRange not in uniRangeGroups:
        uniRangeGroups.append(uniRange)
        
# Print current Unicode ranges found in font
print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')
print('‡‡‡ Current groups: ', uniRangeGroups)
print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')

# Helper function to filter array by list of values
def filter_arr(arr, filters):
    return [x for x in arr if x in filters]
        
# Apply Unicode range filters if specified
if unicodeFilters:
    _originalGroups = uniRangeGroups
    uniRangeGroups = filter_arr(_originalGroups, unicodeFilters)
    print('')
    print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')
    print('‡‡‡ Filters: ', unicodeFilters)
    print('‡‡‡ Filtered groups: ', uniRangeGroups)
    print('‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡')
    
# Draw glyphs grouped by Unicode range
if unicodeGroups and uniRangeGroups:
    for i, groupName in enumerate(uniRangeGroups):
        print(i)
            
        if groupName:
            # Calculate completion percentage for this Unicode range
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

            # Create new page for each group (except first)
            if i != 0:
                newPage(pageWidth, pageHeight)
                setBackgroundColor()
            
            # Position for first glyph after group header
            xBox, yBox = x, y - (groupFontSize + margin)
            
            # Draw group header with completion percentage
            setForegroundColor()
            font(groupFontFamily, groupFontSize)
            text(f"{groupName.upper()} / {completion_percentage}% COMPLETED", (x, pageHeight - (margin + groupFontSize)))
            
            # Draw each glyph in the current Unicode range
            for i, glyphName in enumerate(f.glyphOrder):
                if glyphName == 'space':
                    continue
                
                # Check if glyph belongs to current range
                uniValue = n2u(glyphName)
                uniRange = u2r(uniValue)
                
                if groupName == uniRange:
                    g = f[glyphName]
                    print(uniValue)

                    # Start new line if reached page edge
                    if xBox + boxWidth >= pageWidth - margin:
                        xBox = x
                        yBox -= boxHeight
                        # Start new page if reached bottom
                        if yBox < margin:
                            yBox = y
                            newPage(pageWidth, pageHeight)
                            setBackgroundColor()
                            setForegroundColor()
                            font(groupFontFamily, groupFontSize)
                            text(f"{groupName.upper()} (CONTINUED) / {completion_percentage}% COMPLETED", (x, pageHeight - (margin + groupFontSize)))
                            xBox, yBox = x, y - (groupFontSize + margin)

                    # Draw cell border
                    if showGlyphBorder:
                        stroke(0, 0, 0, 0.2)  # Light border
                        fill(None)
                        rect(xBox, yBox, boxWidth, boxHeight)
                    else:
                        stroke(None)
                        fill(None)

                    # Calculate centered position for glyphs
                    xGlyph = xBox + (boxWidth - g.width*s)/2 + xOffset
                    yGlyph = yBox + (boxHeight - f.info.unitsPerEm*s)/2 + yOffset
                    
                    # Draw main font glyph
                    save()
                    translate(xGlyph, yGlyph)
                    fill(*glyphColor)
                    stroke(None)
                    scale(s)
                    drawGlyph(g)
                    restore()
                    
                    # Draw reference glyph overlay
                    if showReferenceFont:
                        save()
                        blendMode("multiply") # Blend with main glyph
                        font(referenceFontFamily, f.info.unitsPerEm * s * referenceScale)
                        fill(*referenceColor)
                        text(chr(uniValue), 
                             (xGlyph + referenceXOffset,
                              yGlyph + referenceYOffset))
                        restore()
                    
                    # Draw glyph information
                    setForegroundColor()
                    font(groupFontFamily, glyphInfoSize)
                    
                    # Draw Unicode value in top left with lower opacity
                    fill(0, 0, 0, 0.65)
                    stroke(None)
                    text(f"U+{uniValue:04X}", (xBox + cellPadding, yBox + boxHeight - cellPadding - glyphInfoSize))
                    
                    # Draw glyph name below Unicode value
                    fill(0, 0, 0, 1)
                    stroke(None)
                    text(glyphName, (xBox + cellPadding, yBox + boxHeight - cellPadding - glyphInfoSize*2))
                    
                    # Draw reference character in bottom left
                    if showReferenceChar:
                        font(referenceFontFamily, referenceFontSize)
                        stroke(None)
                        text(chr(uniValue), (xBox + cellPadding + bottomLeftXOffset, yBox + cellPadding + bottomLeftYOffset))
                        
                    # Draw current font character in bottom right
                    save()
                    translate(xBox + boxWidth - cellPadding - g.width*s*0.4 + bottomRightXOffset, 
                            yBox + cellPadding + bottomRightYOffset)
                    fill(0, 0, 0, 1)
                    stroke(None)
                    scale(s*0.33)
                    drawGlyph(g)
                    restore()

                    # Move to next cell position
                    xBox += boxWidth


######################################

# Optional: Draw all glyphs on final page without grouping

if returnAllGlyphs:
    newPage(pageWidth, pageHeight)
    setBackgroundColor()
    xBox, yBox = x, y

    for i, glyphName in enumerate(f.glyphOrder):
    
        if glyphName == 'space':
            continue

        g = f[glyphName]

        # Start new line if reached page edge
        if xBox + boxWidth >= pageWidth - margin:
            xBox = x
            yBox -= boxHeight
            # Start new page if reached bottom
            if yBox < margin:
                yBox = y
                newPage(pageWidth, pageHeight)
                setBackgroundColor()

        # Draw cell border
        if showGlyphBorder:
            stroke(0, 0, 0, 0.2)  # Light border
            fill(None)
            rect(xBox, yBox, boxWidth, boxHeight)
        else:
            stroke(None)
            fill(None)

        # Calculate centered position for glyphs
        xGlyph = xBox + (boxWidth - g.width*s)/2 + xOffset
        yGlyph = yBox + (boxHeight - f.info.unitsPerEm*s)/2 + yOffset
        
        # Draw main font glyph
        save()
        translate(xGlyph, yGlyph)
        fill(*glyphColor)
        stroke(None)
        scale(s)
        drawGlyph(g)
        restore()
        
        # Draw reference glyph overlay
        if showReferenceFont:
            save()
            blendMode("multiply")
            font(referenceFontFamily, f.info.unitsPerEm * s * referenceScale)
            fill(*referenceColor)
            text(chr(uniValue), 
                 (xGlyph + referenceXOffset,
                  yGlyph + referenceYOffset))
            restore()
        
        # Draw glyph information
        setForegroundColor()
        font(groupFontFamily, glyphInfoSize)
        
        # Draw Unicode value in top left with lower opacity
        fill(0, 0, 0, 0.65)
        stroke(None)
        text(f"U+{uniValue:04X}", (xBox + cellPadding, yBox + boxHeight - cellPadding - glyphInfoSize))
        
        # Draw glyph name below Unicode value
        fill(0, 0, 0, 1)
        stroke(None)
        text(glyphName, (xBox + cellPadding, yBox + boxHeight - cellPadding - glyphInfoSize*2))
        
        # Draw reference character in bottom left
        if showReferenceChar:
            font(referenceFontFamily, referenceFontSize)
            stroke(None)
            text(chr(uniValue), (xBox + cellPadding + bottomLeftXOffset, yBox + cellPadding + bottomLeftYOffset))
            
        # Draw current font character in bottom right
        save()
        translate(xBox + boxWidth - cellPadding - g.width*s*0.4 + bottomRightXOffset, 
                 yBox + cellPadding + bottomRightYOffset)
        fill(0, 0, 0, 1)
        stroke(None)
        scale(s*0.4)
        drawGlyph(g)
        restore()

        # Move to next cell position
        xBox += boxWidth