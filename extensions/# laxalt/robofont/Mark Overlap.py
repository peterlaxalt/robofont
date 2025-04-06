f = CurrentFont()

for g in f:
    testglyph = g.copy()
    testglyph.removeOverlap()
    
    if len(g) != len(testglyph):
        g.markColor = (0.5, 0, 0, 0.9)