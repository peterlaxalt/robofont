from mojo.extensions import registerExtensionDefaults

# --------
# defaults
# --------

"""
UC, punc
punc, UC
lc, punc
punc, lc
fig, fig
UC, fig
fig, UC
lc, fig
fig, lc
"""

contextStrings = [
    {
        "name": "Uppercase, Uppercase",
        "enabled": True,
        "longContext": ["H", "H", "$LEFT", "$RIGHT", "H", "O", "H", "O", "O"],
        "shortContext": ["H", "$LEFT", "$RIGHT", "H"],
        "suffixMatching": True,
        "pseudoUnicodes": True,
        "leftPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Lu"
                }
            ]
        },
        "rightPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Lu"
                }
            ]
        }
    },
    {
        "name": "Uppercase, lowercase",
        "enabled": True,
        "longContext": ["$LEFT", "$RIGHT", "n", "o", "n", "o", "o"],
        "shortContext": ["n", "$LEFT", "$RIGHT", "n"],
        "suffixMatching": True,
        "pseudoUnicodes": True,
        "leftPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Lu"
                }
            ]
        },
        "rightPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Ll"
                }
            ]
        }
    },
    {
        "name": "lowercase, Uppercase",
        "enabled": True,
        "longContext": ["n", "n", "$LEFT", "$RIGHT", "n", "o", "n", "o", "o"],
        "shortContext": ["n", "$LEFT", "$RIGHT", "n"],
        "suffixMatching": True,
        "pseudoUnicodes": True,
        "leftPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Ll"
                }
            ]
        },
        "rightPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Lu"
                }
            ]
        }
    },
    {
        "name": "lowercase, lowercase",
        "enabled": True,
        "longContext": ["n", "n", "$LEFT", "$RIGHT", "n", "o", "n", "o", "o"],
        "shortContext": ["n", "$LEFT", "$RIGHT", "n"],
        "suffixMatching": True,
        "pseudoUnicodes": True,
        "leftPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Ll"
                }
            ]
        },
        "rightPattern": {
            "matches": "any",
            "rules": [
                {
                    "type": "unicodeCategory",
                    "comparison": "is",
                    "value": "Ll"
                }
            ]
        }
    },
]


_defaults = {
    # window default settings
    "com.typesupply.MM4.windowSettings.main.pairListVisibleByDefault": True,
    "com.typesupply.MM4.windowSettings.main.pairListOnLeft": True,
    "com.typesupply.MM4.windowSettings.main.typingPaneVisibleByDefault": True,
    "com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.glyphInfoVisibleByDefault": True,
    "com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupPreviewVisibleByDefault": False,
    "com.typesupply.MM4.viewSettings.edit.singleFont.singlePair.groupStackVisibleByDefault": False,
    "com.typesupply.MM4.viewSettings.general.groupPreviewPointSize": 25,
    # context strings
    "com.typesupply.MM4.contextStrings": contextStrings,
    # expiration
    "com.typesupply.MM4.applicationFirstRun": -1,
}


registerExtensionDefaults(_defaults)
