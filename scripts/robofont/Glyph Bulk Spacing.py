# menuTitle : (Menu) Glyph Bulk Spacing

from mojo.subscriber import Subscriber, registerFontOverviewSubscriber
from mojo.UI import PostBannerNotification, AskString
from fontTools.misc.fixedTools import otRound
from statistics import median
import vanilla

class GlyphBulkSpacingMenu(Subscriber):
    
    '''
    2024.06.16
    Peter Laxalt
    '''

    def build(self):
        self.f = None
        
    def fontOverviewWantsContextualMenuItems(self, info):
        self.f = CurrentFont()

        if self.f.selectedGlyphNames and len(self.f.selectedGlyphNames) != len(self.f.keys()):
            self.message = "Glyph Bulk Spacing"
            self.span = self.f.selectedGlyphNames
            
        menu_items = [
                (self.message, [
                    ('Set spacing of selected glyphs', self.set_spacing),
                    ]
                )
            ]
        info['itemDescriptions'].extend(menu_items)
        
    def set_spacing(self, sender):
        # Create the dialog window
        self.w = vanilla.Window((300, 100), "Set Glyph Spacing")
        
        # Add input fields for left and right spacing
        self.w.text_left = vanilla.TextBox((10, 10, 80, 20), "Left Spacing:")
        self.w.input_left = vanilla.EditText((100, 10, 50, 20), "0")
        
        self.w.text_right = vanilla.TextBox((10, 40, 80, 20), "Right Spacing:")
        self.w.input_right = vanilla.EditText((100, 40, 50, 20), "20")
        
        # Add Apply button
        self.w.apply_button = vanilla.Button((10, 70, 140, 20), "Apply", callback=self.update_glyphs)
        self.w.cancel_button = vanilla.Button((150, 70, 140, 20), "Cancel", callback=self.cancel)
        
        # Open the window
        self.w.open()

    def cancel(self, sender):
        self.w.close()

    def update_glyphs(self, style):
        
        # Check if there is a font open
        if self.f is not None:
            try:
                for g_name in self.span:
                    g = self.f[g_name]
                    margin_left = int(self.w.input_left.get())
                    margin_right = int(self.w.input_right.get())
                    
                    g.leftMargin = margin_left
                    g.rightMargin = margin_right

                self.w.close()
                self.f.changed()
                
                message = f"Spacing applied to all glyphs: left {margin_left}, right {margin_right}."
                PostBannerNotification(message, 2)  # Show success message for 2 seconds

            except ValueError:
                print("Invalid input. Please enter integer values.")
        else:
            print("No font open")
        
        
#===================
        
if __name__ == "__main__":    
    registerFontOverviewSubscriber(GlyphBulkSpacingMenu)