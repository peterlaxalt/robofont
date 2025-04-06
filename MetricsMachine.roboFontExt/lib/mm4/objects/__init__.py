import defcon

from mm4.implementation import registerImplementation

from .mmFont import MMFont
from .mmGlyph import MMGlyph
from .mmGroups import MMGroups
from .mmKerning import MMKerning


registerImplementation(MMFont, defcon.Font, allowsOverwrite=True)
registerImplementation(MMGlyph, defcon.Glyph, allowsOverwrite=True)
registerImplementation(MMKerning, defcon.Kerning, allowsOverwrite=True)
registerImplementation(MMGroups, defcon.Groups, allowsOverwrite=True)
