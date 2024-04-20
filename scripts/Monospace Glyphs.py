# menuTitle : Monospace Glyphs Menu

from mojo.subscriber import Subscriber, registerFontOverviewSubscriber
from mojo.UI import PostBannerNotification
from mojo.UI import AskString
from mojo.UI import AskYesNoCancel
from mojo.roboFont import version
from statistics import median

class monospaceGlyphsMenu(Subscriber):
    
    '''
    Monospace glyphs menu (median)
    
    2020.07.24
    Ryan Bugden
    '''
    
    maxTitleLength = 20


    def build(self):
        self.f = None
        
    def fontOverviewWantsContextualMenuItems(self, info):
        self.f = CurrentFont()
        if self.f.selectedGlyphNames:
            myMenuItems = [
                ("Monospace glyphs", self.monospaceCallback)
            ]
            info['itemDescriptions'].extend(myMenuItems)
        else:
            pass
        
    def monospaceCallback(self, sender):

        # if no selection, do all
        if self.f.selectedGlyphNames == ():
            sel = self.f.keys()
        else:
            sel = self.f.selectedGlyphNames
            
        ws = []
        
        for g_name in sel:
            g = self.f[g_name]
            ws.append(g.width)

        try: 
            des = int(median(ws))
        except:
            des  = 1000
            
        set_width = int(AskString(
            "Set width:",
            f"{des}",
            "Monospace Selected Glyphs"
            ))
        reset_left_right_margins = AskYesNoCancel(
            "Reset left/right margins?", 
            title='Margin control', 
            default=0, 
            informativeText='This will center your glyph in your new width and remove margins'
            )
            
        if reset_left_right_margins == -1:
            print("\nMargins reset cancelled, bailing", reset_left_right_margins)
            return

        for g_name in sel:
            g = self.f[g_name]
    
            # for Robofont 3+
            if version >= "3.0":
                print("\nVersion >= 3.0")
                if g.bounds:
                    
                    print("\nMargins reset", reset_left_right_margins)
                    
                    if reset_left_right_margins == 1:
                        print("\nResetting left/right margins to 0")
                        g.leftMargin = 0
                        g.rightMargin = 0    
                        
                    print("\nBounds detected")
                    print("\nLeft margin:", g.leftMargin)
                    print("\nRight margin:", g.rightMargin)
                    print("\nBounds:", g.bounds)
                    print("\nWidth:", g.width)
                    diff = set_width - g.width
                    g.leftMargin = diff/2
                    g.rightMargin = diff/2
                    g.width = set_width
        
                else:
                    g.width = set_width
                g.changed()
                self.f.changed()
            
            # for Robofont 1
            else:
                if g.box:
                    print("\nSetting bounds (legacy)")
                    diff = set_width - g.width
                    g.leftMargin += diff/2
                    g.rightMargin += diff/2
                    g.width = set_width
        
                else:
                    print("\nNot setting bounds")
                    g.width = set_width
                g.changed()
                self.f.changed()

        PostBannerNotification("Monospaced selected glyphs", f"Width: {set_width}")

        print("\nMonospaced selected glyphs with width: " + str(set_width))
        print("Selected glyphs included: ", self.f.selectedGlyphNames)
        
        
#===================
        
if __name__ == "__main__":    
    registerFontOverviewSubscriber(monospaceGlyphsMenu)