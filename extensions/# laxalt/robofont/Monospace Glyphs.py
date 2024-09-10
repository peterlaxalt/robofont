# menuTitle : (Menu) Monospace Glyphs

from mojo.subscriber import Subscriber, registerFontOverviewSubscriber
from mojo.UI import PostBannerNotification, AskString
from fontTools.misc.fixedTools import otRound
from statistics import median


MARK_COLOR = (1, 0, 0.2234, 0.8)

class MonospaceGlyphsMenu(Subscriber):
    
    '''
    2020.07.24
    2024.04.22
    Ryan Bugden
    '''

    def build(self):
        self.f = None
        
    def fontOverviewWantsContextualMenuItems(self, info):
        self.f = CurrentFont()
        if self.f.selectedGlyphNames and len(self.f.selectedGlyphNames) != len(self.f.keys()):
            self.message = "Monospace Selected Glyphs"
            self.span = self.f.selectedGlyphNames
            self.suggested_width = self.get_median_width()
        else:
            self.message = "Monospace All Glyphs"
            self.span = self.f.keys()
            self.suggested_width = self.get_control_glyph_width()
            
        menu_items = [
                (self.message, [
                    ('Keep Relative Spacing', self.monospace_proportionate),
                    ('Force Centered', self.monospace_centered)                
                    ]
                )
            ]
        info['itemDescriptions'].extend(menu_items)
        
        
    def get_median_width(self):
        ws = []
        for g_name in self.span:
            ws.append(self.f[g_name].width)
        try: 
            return otRound(median(ws))
        except:
            return 1000
        
        
    def get_control_glyph_width(self):
        ws = []
        for g_name in ['n', 'o']:
            if g_name in self.f.keys():
                ws.append(self.f[g_name].width)
        if ws:
            try: 
                return otRound(median(ws))
            except:
                return 1000
        else:
            return self.get_median_width()
            
            
    def space_glyph_lsb(self, g, side_value):
        # Move contours, anchors, guidelines, image
        stuff_to_move = [c for c in g.contours] + [a for a in g.anchors] + [g for g in g.guidelines] + [g.image]
        for element in stuff_to_move:
            if element:
                element.moveBy((side_value, 0))
        # Handle components that are transformed, and only if they're being manipulated by this script as well.
        for comp in g.components:
            # If the component’s base glyph isn't in the selection, then move it normally.
            if comp.baseGlyph not in self.span:
                comp.moveBy((side_value, 0))
            # If it is, then compensate for whatever changes were made to the base glyph
            else:
                # If the component is rotated at all
                if comp.transformation[0] < 0:
                    # Move it horizontally, according to how much it's rotated
                    comp.moveBy((-comp.transformation[0]*side_value*2, 0))
                # Adjust vertical offset if vertically squished
                comp.moveBy((0, -comp.transformation[1]*side_value))
            
        
    def monospace_proportionate(self, sender):
        self.monospace_glyphs("proportionate")
    def monospace_centered(self, sender):
        self.monospace_glyphs("centered")
        
        
    def monospace_glyphs(self, style):
        set_width = int(AskString(
            "Choose width:",
            f"{self.suggested_width}",
            self.message
            ))
        
        width_changed = []
        names_and_deltas = {}
        for g_name in self.span:
            
            g = self.f[g_name]
            if g.markColor == MARK_COLOR:
                g.markColor = None
            # Collect the glyphs that will have changed, and mark them
            if g.width != set_width:
                width_changed.append(g.name)
                g.markColor = MARK_COLOR
            # If there are contours or components in the glyph
            min_anchors = None
            if g.bounds:         
                content_width = g.bounds[2] - g.bounds[0]     
            # If there are anchors      
            elif g.anchors:
                a_xs = [a.x for a in g.anchors]
                min_anchors, max_anchors = min(a_xs), max(a_xs)
                content_width = max_anchors - min_anchors
            if style == "centered":
                desired_left = otRound((set_width - content_width) / 2)
                if g.angledLeftMargin:
                    left_delta = desired_left - g.angledLeftMargin
                elif min_anchors:
                    left_delta = desired_left - min_anchors
                else:
                    left_delta = 0
            elif style == "proportionate":
                left_delta = otRound((set_width - g.width) / 2)
            # Store all changes beforehand, in order to protect component changes
            if left_delta:
                names_and_deltas[g] = left_delta
                
        # Actually change the spacing 
        for g, left_delta in names_and_deltas.items():
            with g.undo(f"Monospace glyph {g.name}"):
                if left_delta:
                    self.space_glyph_lsb(g, left_delta)
                g.width = set_width
        self.f.changed()

        PostBannerNotification("Monospaced Glyphs", f"Width: {set_width}")
        print(f"\nMonospaced glyphs with width: {set_width}")
        print("Glyphs requested: ", self.span)
        print("Glyphs that changed width: ", width_changed)
        
        
#===================
        
if __name__ == "__main__":    
    registerFontOverviewSubscriber(MonospaceGlyphsMenu)