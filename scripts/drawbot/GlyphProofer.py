'''Glyph Proofer'''

from glyphNameFormatter.reader import *

f = CurrentFont()
allUnis = list(uni2name.keys())

def _c(value):
    return value / 255

# settings
glyphScale = 0.4
canvasWidth = 562
canvasHeight = 1000
captionSize = 13
unicodeGroups = True
unicodeFilters = ['Hiragana', 'Katakana']
returnAllGlyphs = False

## color palette: dark blue bg and pink fg
captionColor = _c(255), _c(218), _c(218), 1
backgroundColor = _c(0), _c(0), _c(31), 1
glyphFillColor = _c(255), _c(218), _c(218), .75
glyphOutlineColor = _c(255), _c(218), _c(218), 1
glyphBoundaryColor = 255, 255, 255, .1
guidesColor = _c(255), _c(218), _c(218), .25

## color palette: dark blue bg and pink fg
# captionColor = _c(0), _c(0), _c(31), 1
# backgroundColor = _c(250), _c(247), _c(245), 1
# glyphFillColor = _c(217), _c(83), _c(0), .75
# glyphOutlineColor = _c(217), _c(83), _c(0), 1
# glyphBoundaryColor = _c(217), _c(83), _c(0), .1
# guidesColor = _c(217), _c(83), _c(0), .25


def setBackgroundColor():
    fill(*backgroundColor)
    rect(0, 0, canvasWidth, canvasHeight)

# collect vertical metrics
metricsY = {
    0,
    f.info.descender,
    f.info.xHeight,
    f.info.capHeight,
    f.info.ascender,
}

# get box height
boxHeight = (max(metricsY) - min(metricsY)) * glyphScale
boxY = (canvasHeight - boxHeight) * 0.5

# get glyph names
glyphNames = f.selectedGlyphNames if len(f.selectedGlyphs) else f.keys()

# filter by group
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
            # loop through glyphs
            for i, glyphName in enumerate(f.glyphOrder):
            
                if not glyphName in glyphNames:
                    continue
                    
                if glyphName == 'space':
                    continue
                
                # check glyph
                uniValue = n2u(glyphName)
                uniRange = u2r(uniValue)
                
                # draw glyph
                if groupName == uniRange:
                    # get glyph
                    g = f[glyphName]
                    boxWidth = g.width * glyphScale

                    # make new page
                    newPage(canvasWidth, canvasHeight)
                    setBackgroundColor()

                    # calculate origin position
                    x = (canvasWidth - boxWidth) * 0.5
                    y = boxY + abs(f.info.descender) * glyphScale

                    # collect horizontal metrics
                    guidesX = {x, x + boxWidth}

                    # --------
                    # draw box
                    # --------

                    save()
                    fill(*glyphBoundaryColor)
                    rect(x, boxY, boxWidth, boxHeight)
                    restore()

                    # -----------
                    # draw guides
                    # -----------

                    save()
                    lineDash(6, 3)
                    stroke(*guidesColor)

                    # draw guides x
                    for guideX in guidesX:
                        line((guideX, 0), (guideX, height()))

                    # draw guides y
                    for guideY in metricsY:
                        guideY = y + guideY * glyphScale
                        line((0, guideY), (width(), guideY))

                    restore()

                    # ----------
                    # draw glyph
                    # ----------

                    save()
                    fill(*glyphFillColor)
                    stroke(*glyphOutlineColor)
                    strokeWidth(2)
                    lineJoin('round')
                    translate(x, y)
                    scale(glyphScale)
                    drawGlyph(g)
                    restore()

                    # ------------
                    # draw anchors
                    # ------------

                    radius = 10
                    save()
                    fill(0, 0, 0)
                    stroke(1, 0, 0)
                    translate(x, y)
                    for anchor in g.anchors:
                        aX, aY = anchor.position
                        aX *= glyphScale
                        aY *= glyphScale
                        oval(aX - radius, aY - radius, radius * 2, radius * 2)
                        line((aX - radius, aY), (aX + radius, aY))
                        line((aX, aY - radius), (aX, aY + radius))
                    restore()

                    # ------------
                    # draw caption
                    # ------------

                    captionX = captionSize
                    captionW = width() - captionSize * 2
                    captionH = captionSize * 2

                    save()
                    font('Menlo-Bold')
                    fontSize(captionSize)
                    fill(*captionColor)

                    # top
                    captionY = height() - captionSize * 3
                    captionBox = captionX, captionY, captionW, captionH
                    textBox(g.name, captionBox, align='left')
                    if g.unicode:
                        uni = str(hex(g.unicode)).replace("0x", '')
                        uni = uni.zfill(4).upper()
                        textBox(uni, captionBox, align='right')

                    # bottom
                    captionY = 0
                    captionBox = captionX, captionY, captionW, captionH
                    textBox('%.2f' % g.width, captionBox, align='center')
                    if g.bounds:
                        textBox('%.2f' % g.leftMargin, captionBox, align='left')
                        textBox('%.2f' % g.rightMargin, captionBox, align='right')

                    restore()

                    

# draw glyphs
if returnAllGlyphs:
    for glyphName in f.glyphOrder:
        if not glyphName in glyphNames:
            continue

        # get glyph
        g = f[glyphName]
        boxWidth = g.width * glyphScale

        # make new page
        newPage(canvasWidth, canvasHeight)
        setBackgroundColor()

        # calculate origin position
        x = (canvasWidth - boxWidth) * 0.5
        y = boxY + abs(f.info.descender) * glyphScale

        # collect horizontal metrics
        guidesX = {x, x + boxWidth}

        # --------
        # draw box
        # --------

        save()
        fill(0.95)
        rect(x, boxY, boxWidth, boxHeight)
        restore()

        # -----------
        # draw guides
        # -----------

        save()
        lineDash(6, 3)
        stroke(0.5)

        # draw guides x
        for guideX in guidesX:
            line((guideX, 0), (guideX, height()))

        # draw guides y
        for guideY in metricsY:
            guideY = y + guideY * glyphScale
            line((0, guideY), (width(), guideY))

        restore()

        # ----------
        # draw glyph
        # ----------

        save()
        fill(None)
        stroke(0)
        strokeWidth(2)
        lineJoin('round')
        translate(x, y)
        scale(glyphScale)
        drawGlyph(g)
        restore()

        # ------------
        # draw anchors
        # ------------

        radius = 10
        save()
        fill(0, 0, 0)
        stroke(1, 0, 0)
        translate(x, y)
        for anchor in g.anchors:
            aX, aY = anchor.position
            aX *= glyphScale
            aY *= glyphScale
            oval(aX - radius, aY - radius, radius * 2, radius * 2)
            line((aX - radius, aY), (aX + radius, aY))
            line((aX, aY - radius), (aX, aY + radius))
        restore()

        # ------------
        # draw caption
        # ------------

        captionX = captionSize
        captionW = width() - captionSize * 2
        captionH = captionSize * 2

        save()
        font('Menlo-Bold')
        fontSize(captionSize)
        fill(*captionColor)

        # top
        captionY = height() - captionSize * 3
        captionBox = captionX, captionY, captionW, captionH
        textBox(g.name, captionBox, align='left')
        if g.unicode:
            uni = str(hex(g.unicode)).replace("0x", '')
            uni = uni.zfill(4).upper()
            textBox(uni, captionBox, align='right')

        # bottom
        captionY = 0
        captionBox = captionX, captionY, captionW, captionH
        textBox('%.2f' % g.width, captionBox, align='center')
        if g.bounds:
            textBox('%.2f' % g.leftMargin, captionBox, align='left')
            textBox('%.2f' % g.rightMargin, captionBox, align='right')

        restore()
