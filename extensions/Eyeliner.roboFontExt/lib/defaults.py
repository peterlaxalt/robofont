from colorsys import rgb_to_hsv, hsv_to_rgb
from mojo.UI import getDefault

def get_flattened_alpha(color):
    # Flatten transparency of eye, using background color preference
    gvbc = getDefault("glyphViewBackgroundColor")
    r, g, b, a = color
    r2, g2, b2, a2 = gvbc
    r3 = r2 + (r - r2) * a
    g3 = g2 + (g - g2) * a
    b3 = b2 + (b - b2) * a
    return (r3, g3, b3, 1)

def get_darkened_blue(color):
    # Darkened version of non-transparent blue zone color preference
    r, g, b, a = color
    h, s, v    = rgb_to_hsv(r*255, g*255, b*255)
    r, g, b    = hsv_to_rgb(h, s + (1 - s)/2, v*0.6)
    return (r/255, g/255, b/255, 1)


EXTENSION_KEY = 'com.ryanbugden.eyeliner.settings'
EXTENSION_DEFAULTS = {
    "showLocalGuidesCheckbox": True,
    "showGlobalGuidesCheckbox": True,
    "showFontDimensionsCheckbox": True,
    "fontDimensionsLightColorWell": get_flattened_alpha(getDefault("glyphViewFontMetricsStrokeColor")),
    "fontDimensionsDarkColorWell": get_flattened_alpha(getDefault("glyphViewFontMetricsStrokeColor.dark")),
    "showBluesCheckbox": True,
    "bluesLightColorWell": get_darkened_blue(get_flattened_alpha(getDefault("glyphViewBluesColor"))),
    "bluesDarkColorWell": get_darkened_blue(get_flattened_alpha(getDefault("glyphViewBluesColor.dark"))),
    "showFamilyBluesCheckbox": True,
    "familyBluesLightColorWell": get_darkened_blue(get_flattened_alpha(getDefault("glyphViewFamilyBluesColor"))),
    "familyBluesDarkColorWell": get_darkened_blue(get_flattened_alpha(getDefault("glyphViewFamilyBluesColor.dark"))),
    "showMarginsCheckbox": False,
    "marginsLightColorWell": (0.5, 0.5, 0.5, 1),
    "marginsDarkColorWell": (0.5, 0.5, 0.5, 1),
}