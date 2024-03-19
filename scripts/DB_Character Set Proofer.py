'''Character Set Proofer'''

f = CurrentFont()

# colors
def setBackgroundColor():
    fill(0,0,0, 1)
    rect(0, 0, pageWidth, pageHeight)

def setForegroundColor():
    fill(255,255,255, 1)

# main variables
boxHeight = 70
boxPaddingX = 20
boxPaddingY = 20
margin = 30

# calculate scale
s = float(boxHeight) / f.info.unitsPerEm

# define page size
size('TabloidLandscape')
pageWidth, pageHeight = width(), height()

# calculate initial positions
x = margin
y = pageHeight - margin - boxHeight

# background
setBackgroundColor()

# draw glyphs
xBox, yBox = x, y

for i, glyphName in enumerate(f.glyphOrder):
    
    if glyphName == 'space':
        continue

    g = f[glyphName]
    boxWidth = g.width*s
    # boxWidth = boxHeight

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
