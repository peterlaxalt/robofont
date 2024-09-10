# menuTitle : (Menu) Copy Glyph Characters to Clipboard

from AppKit import NSPasteboard, NSStringPboardType
from mojo.subscriber import Subscriber, registerFontOverviewSubscriber

class CopyGlyphCharactersToClipboard(Subscriber):
    
    '''
    2024.06.16
    Peter Laxalt
    '''

    def build(self):
        self.f = None
        self.message = "Copy Glyph Characters"

    def fontOverviewWantsContextualMenuItems(self, info):
        self.f = CurrentFont()

        if self.f.selectedGlyphNames and len(self.f.selectedGlyphNames) != len(self.f.keys()):
            menu_items = [
                (self.message, [
                    ('Copy selected characters', self.copy_glyph_characters),
                    ]
                )
            ]
            info['itemDescriptions'].extend(menu_items)
        
    def copy_glyph_characters(self, sender):        
        if self.f is not None:
            charactersToCopy = ""

            for glyphName in self.f.selectedGlyphNames:
                glyph = self.f[glyphName]
                if glyph.unicode is not None:
                    charactersToCopy += chr(glyph.unicode)
                else:
                    print(f"Glyph '{glyphName}' has no Unicode value")
            
            if charactersToCopy:
                # Copy the characters to the clipboard
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.declareTypes_owner_([NSStringPboardType], None)
                pasteboard.setString_forType_(charactersToCopy, NSStringPboardType)
                
                print(f"Characters '{charactersToCopy}' copied to clipboard")
            else:
                print("No valid glyphs selected")
        else:
            print("No font open")
        
        
#===================
        
if __name__ == "__main__":    
    registerFontOverviewSubscriber(CopyGlyphCharactersToClipboard)