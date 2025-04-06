glyphCollectionSortDescriptors = [
    dict(type="alphabetical", allowPseudoUnicode=True),
    dict(type="category", allowPseudoUnicode=True),
    dict(type="unicode", allowPseudoUnicode=True),
    dict(type="script", allowPseudoUnicode=True),
    dict(type="suffix", allowPseudoUnicode=True),
    dict(type="decompositionBase", allowPseudoUnicode=True)
]

def sortGlyphNames(font, namesToSort=None):
    if namesToSort is None:
        namesToSort = font.keys()
    ordered = []
    for name in font.glyphOrder:
        if name in namesToSort:
            ordered.append(name)
    unordered = [name for name in sorted(namesToSort) if name not in ordered]
    ordered.extend(unordered)
    ordered = [name for name in ordered if name in font and not font[name].template]
    return ordered