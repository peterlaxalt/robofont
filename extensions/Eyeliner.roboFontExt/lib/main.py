import math
from fontTools.misc.fixedTools import otRound
from fontParts.world import RGlyph
from fontPens.digestPointPen import DigestPointPen
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber, listRegisteredSubscribers
from mojo.tools import IntersectGlyphWithLine
from mojo.UI import CurrentGlyphWindow, getGlyphViewDisplaySettings, getDefault, appearanceColorKey, inDarkMode
from mojo.pens import DecomposePointPen
import merz
from merz.tools.drawingTools import NSImageDrawingTools
from mojo.extensions import getExtensionDefault
from defaults import get_flattened_alpha, get_darkened_blue, EXTENSION_KEY, EXTENSION_DEFAULTS



def eyeliner_symbol(
        radius      = 5,
        stretch     = 0.7,
        strokeColor = (0, 0, 0, 1),
        strokeWidth = 1,
        fillColor   = (1, 1, 1, 0)
        ):
    # Calculate the width and height
    width  = radius * 6 * stretch * 2 + strokeWidth * 2
    height = radius * 2 + strokeWidth * 2
    # Create a NSImage drawing bot 
    bot = NSImageDrawingTools((width, height))
    # Get a pen
    pen = bot.BezierPath()
    # Draw the eye
    pen.moveTo((6 * radius * stretch, 0))
    pen.curveTo(
        (2 * radius * stretch, 0),
        (1.25 * radius * stretch, -radius),
        (0, -radius))
    pen.curveTo(
        (-1.25 * radius * stretch, -radius),
        (-2 * radius * stretch, 0),
        (-6 * radius * stretch, 0))
    pen.curveTo(
        (-2 * radius * stretch, 0),
        (-1.25 * radius * stretch, radius),
        (0, radius))
    pen.curveTo(
        (1.25 * radius * stretch, radius),
        (2 * radius * stretch, 0),
        (6 * radius * stretch, 0))
    pen.closePath()
    bot.fill(*fillColor)
    bot.stroke(*strokeColor)
    bot.strokeWidth(strokeWidth)
    bot.translate(width / 2 + 0.25, height / 2 + 0.25)
    bot.drawPath(pen)
    return bot.getImage()
    
merz.SymbolImageVendor.registerImageFactory("eyeliner.eye", eyeliner_symbol)


def is_on_diagonal(pta, angle, ptb, tol=0.08):
    if pta == ptb: 
        return True
        
    ar = math.radians(angle)%math.pi
    ca = math.cos(ar)
    sa = math.sin(ar)
    x_diff = ptb[0] - pta[0]
    y_diff = ptb[1] - pta[1]

    if not math.isclose(ca, 0, abs_tol=tol) and not math.isclose(sa, 0, abs_tol=tol):
        # Diagonal, distances for x and y should match
        tdx = x_diff / ca
        tdy = y_diff / sa
        return math.isclose(tdx, tdy, abs_tol=5)
        
    elif math.isclose(ca, 1, abs_tol=tol) and math.isclose(sa, 0, abs_tol=tol):
        # Horizontal, so y should match
        return math.isclose(pta[1], ptb[1], abs_tol=tol)
        
    elif math.isclose(ca, 0, abs_tol=tol) and math.isclose(sa, 1, abs_tol=tol):
        # Vertical, so x should match
        return math.isclose(pta[0], ptb[0], abs_tol=tol)
        
    return False



class Eyeliner(Subscriber):


    def build(self):
        self.font_dim = []
        self.tool_coords = []
        self.oncurve_coords = []
        self.comp_oncurve_coords = []
        self.trans_coords = []
        self.overlapper_coords = []
        self.anc_coords = []
        self.settings = getExtensionDefault(EXTENSION_KEY, EXTENSION_DEFAULTS)

        self.f_guide_xs    = {}
        self.f_guide_ys    = {}
        self.f_guide_diags = []
        self.g_guide_xs    = {}
        self.g_guide_ys    = {}
        self.g_guide_diags = []
        
        self.overlapper_color = (0,0,0,1)

        self.slice_tool = None
        self.shape_tool = None
        self.slice_tool_active = False
        self.shape_tool_active = False

        self.down_point, self.drag_point = (0,0), (0,0)
        self.blue_vals, self.fblue_vals = [], []

        self.update_base_sizes()
        self.update_blues_display_settings()
        self.oncurves_on = getGlyphViewDisplaySettings().get('OnCurvePoints')
        self.anchors_on = getGlyphViewDisplaySettings().get('Anchors')

        self.glyph_editor = self.getGlyphEditor()
        
        self.oncurve_container = self.glyph_editor.extensionContainer(
                    identifier="eyeliner.oncurves", 
                    location="foreground", 
                    clear=True
                )
        self.comp_container = self.glyph_editor.extensionContainer(
                    identifier="eyeliner.components", 
                    location="foreground", 
                    clear=True
                )
        self.anchor_container = self.glyph_editor.extensionContainer(
                    identifier="eyeliner.anchors", 
                    location="foreground", 
                    clear=True
                )
        self.tool_container = self.glyph_editor.extensionContainer(
                    identifier="eyeliner.otherTools", 
                    location="foreground", 
                    clear=True
                )
        self.overlapper_container = self.glyph_editor.extensionContainer(
                    identifier="eyeliner.overlapperContainer", 
                    location="foreground", 
                    clear=True
                )
        self.transmutor_container = self.glyph_editor.extensionContainer(
                    identifier="eyeliner.transmutorContainer", 
                    location="foreground", 
                    clear=True
                )
        

    def started(self):
        try:
            self.g = self.glyph_editor.getGlyph()
        except:
            self.g = None

        if self.g != None:
            self.f = self.g.font
        elif CurrentFont() != None:
            self.f = CurrentFont()
        else:
            self.f = None

        if self.f != None:
            self.update_font_info()
        self.update_color_prefs()
        
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()
        
        
    def destroy(self):
        self.oncurve_container.clearSublayers()
        self.comp_container.clearSublayers()
        self.anchor_container.clearSublayers()
        self.tool_container.clearSublayers()
        self.overlapper_container.clearSublayers()
        

    def update_base_sizes(self):
        self.point_radius = getDefault("glyphViewOnCurvePointsSize")
        self.rad_base = self.point_radius * 1.75  # Changing this value will impact how large the eye is, relative to your on-curve pt size


    def update_color_prefs(self):
        colorway = "Light"
        if inDarkMode():
            colorway = "Dark"
        self.col_font_dim = self.settings[f"fontDimensions{colorway}ColorWell"]
        self.col_glob_guides = get_flattened_alpha(getDefault(appearanceColorKey("glyphViewGlobalGuidesColor")))
        self.col_loc_guides = get_flattened_alpha(getDefault(appearanceColorKey("glyphViewLocalGuidesColor")))

        self.col_blues = self.settings[f"blues{colorway}ColorWell"]
        self.col_fblues = self.settings[f"familyBlues{colorway}ColorWell"]
        self.col_margins = self.settings[f"margins{colorway}ColorWell"]
        
        self.col_component = get_flattened_alpha(getDefault(appearanceColorKey("glyphViewComponentStrokeColor")))

        self.col_corner_pt = get_flattened_alpha(getDefault(appearanceColorKey("glyphViewCornerPointsFill")))
        self.col_curve_pt = get_flattened_alpha(getDefault(appearanceColorKey("glyphViewCurvePointsFill")))


    def roboFontDidChangePreferences(self, info):
        self.update_color_prefs()
        self.update_base_sizes()
        
        
    def eyelinerSettingsDidChange(self, info):
        self.settings = getExtensionDefault(EXTENSION_KEY, EXTENSION_DEFAULTS)
        self.update_color_prefs()
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()


    def roboFontAppearanceChanged(self, info):
        self.update_color_prefs()
        # Update guidelines have color attribute, so update that info, and check things against it.
        self.update_guidelines_info()
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()


    glyphEditorGlyphDidChangeOutlineDelay = 0
    def glyphEditorGlyphDidChangeOutline(self, info):
        self.g = info["glyph"]
        self.update_oncurve_info()
        self.check_oncurves()


    glyphEditorGlyphDidChangeContoursDelay = 0    
    def glyphEditorGlyphDidChangeContours(self, info):
        self.g = info["glyph"]
        self.update_oncurve_info()
        self.check_oncurves()


    glyphEditorGlyphDidChangeComponentsDelay = 0
    def glyphEditorGlyphDidChangeComponents(self, info):
        self.g = info["glyph"]
        self.update_component_info()
        self.check_comp()


    glyphEditorGlyphDidChangeAnchorsDelay = 0
    def glyphEditorGlyphDidChangeAnchors(self, info):
        self.g = info["glyph"]
        self.update_anchor_info()
        self.check_anchors()


    glyphEditorGlyphDidChangeGuidelinesDelay = 0
    def glyphEditorGlyphDidChangeGuidelines(self, info):
        self.g = info["glyph"]
        self.update_guidelines_info()
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()


    glyphEditorFontDidChangeGuidelinesDelay = 0
    def glyphEditorFontDidChangeGuidelines(self, info):
        self.f = info["font"]
        self.update_guidelines_info()
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()


    glyphEditorDidSetGlyphDelay = 0.0001
    def glyphEditorDidSetGlyph(self, info):
        self.g = info["glyph"]
        # Update on-curves before component info.
        self.update_oncurve_info()
        self.update_component_info()
        self.update_anchor_info()
        self.update_guidelines_info()
        self.update_font_info()
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()
        
    def glyphEditorDidChangeDisplaySettings(self, info):
        self.update_blues_display_settings()
        self.update_oncurve_info()
        self.update_anchor_info()
        self.check_oncurves()
        self.check_anchors()
        self.check_comp()
        
        
    def glyphEditorDidMouseDown(self, info):
        '''Support for slice/shape tool eyes'''
        tool = info['lowLevelEvents'][0]['tool']
        self.tool_coords = []
        
        if tool.__class__.__name__ == "SliceTool":
            self.slice_tool_active = True
            self.shape_tool_active = False
            self.slice_tool = tool
            point = self.slice_tool.sliceDown
            if point:
                self.down_point = (point.x, point.y)
        elif tool.__class__.__name__ == "DrawGeometricShapesTool":
            self.slice_tool_active = False
            self.shape_tool_active = True
            self.shape_tool = tool
        else:
            self.slice_tool_active = False
            self.shape_tool_active = False
            
        self.check_tool_points()
        
        
    def glyphEditorDidMouseDrag(self, info):
        '''Support for slice/shape tool eyes'''
        self.g = info["glyph"]
        self.tool_coords = []
        
        # Slice tool
        if self.slice_tool_active:
            point = self.slice_tool.sliceDrag
            if point:
                self.drag_point = (point.x, point.y)
                slice_line = (self.down_point, self.drag_point)
                intersects = IntersectGlyphWithLine(self.g, slice_line, canHaveComponent=False, addSideBearings=False)
                for inter in intersects:
                    x, y = otRound(inter[0]), otRound(inter[1])
                    self.tool_coords.append((x,y)) 
            else:
                self.tool_coords = []
        # Shape tool
        elif self.shape_tool_active:
            try:
                tx, ty, tw, th = self.shape_tool.getRect()
            except:
                self.tool_coords = []
                self.check_tool_points()
                return
            if self.shape_tool.shape == "rect":
                self.shape_pt_color = self.col_corner_pt
                self.shape_pt_shape = "rectangle"
                self.tool_coords = [
                        (tx, ty),
                        (tx + tw, ty),
                        (tx, ty + th),
                        (tx + tw, ty + th),
                    ]    
            elif self.shape_tool.shape == "oval":
                self.shape_pt_color = self.col_curve_pt
                self.shape_pt_shape = "oval"
                self.tool_coords = [
                        ((tx*2 + tw)/2, ty),
                        (tx + tw, (ty*2 + th)/2),
                        ((tx*2 + tw)/2, ty + th),
                        (tx, (ty*2 + th)/2),
                    ] 
            # Round the points
            for i, (coord_x, coord_y) in enumerate(self.tool_coords):
                self.tool_coords[i] = (otRound(coord_x), otRound(coord_y))
        else:
            self.tool_coords = []

        self.check_tool_points()
        
        
    def glyphEditorDidMouseUp(self, info):
        '''Support for slice/shape tool eyes'''
        # Remove eyes on undo
        self.slice_tool_active = False
        self.shape_tool_active = False

        self.check_tool_points()


    glyphEditorFontInfoDidChangeDelay = 0.1
    def glyphEditorFontInfoDidChange(self, info):
        self.update_font_info()
    fontInfoDidChangeValueDelay = 0.1
    def fontInfoDidChangeValue(self, info):
        self.update_font_info()


    overlapperDidDrawDelay = 0
    def overlapperDidDraw(self, info):
        self.overlapper_coords = []
        glyph = info['lowLevelEvents'][0]['overlapGlyph']
        self.overlapper_color = info['lowLevelEvents'][0]['strokeColor']
        if glyph:
            digest_pen = DigestPointPen()
            glyph.drawPoints(digest_pen)
            self.overlapper_coords = [entry[0] for entry in digest_pen.getDigest() if entry[1] != None and type(entry[0]) == tuple and entry[0] not in self.overlapper_coords] 
            self.overlapper_coords = [(otRound(x), otRound(y)) for (x, y) in self.overlapper_coords if (x, y) not in self.oncurve_coords]
            self.check_overlapper_points()
            
            
    def overlapperDidStopDrawing(self, info):
        self.overlapper_coords = [] 
        self.check_overlapper_points()


    def check_overlapper_points(self):
        self.overlapper_container.clearSublayers()
        if self.g == None or CurrentGlyphWindow() != self.glyph_editor:
            return
        # Overlapper future points
        if self.overlapper_coords:
            for coord in self.overlapper_coords:
                if self.check_alignment(self.overlapper_container, coord) == True:
                    self.draw_oncurve_pt(self.overlapper_container, coord, self.overlapper_color, "rectangle")


    transmutorDidDrawDelay = 0
    def transmutorDidDraw(self, info):
        self.transmutor_coords = []
        offset = info['lowLevelEvents'][0]['offset']
        glyph = info['lowLevelEvents'][0]['transmutorGlyph']
        self.transmutor_color = info['lowLevelEvents'][0]['color']
        glyph.moveBy(offset)
        if glyph:
            digest_pen = DigestPointPen()
            glyph.drawPoints(digest_pen)
            self.transmutor_coords = [entry[0] for entry in digest_pen.getDigest() if entry[1] != None and type(entry[0]) == tuple and entry[0] not in self.transmutor_coords] 
            self.transmutor_coords = [(otRound(x), otRound(y)) for (x, y) in self.transmutor_coords if (x, y) not in self.oncurve_coords]
            self.check_transmutor_points()
            
            
    def transmutorDidStopDrawing(self, info):
        self.transmutor_coords = [] 
        self.check_transmutor_points()


    def check_transmutor_points(self):
        self.transmutor_container.clearSublayers()
        if self.g == None or CurrentGlyphWindow() != self.glyph_editor:
            return
        # Tranmutor future points
        if self.transmutor_coords:
            for coord in self.transmutor_coords:
                if self.check_alignment(self.transmutor_container, coord) == True:
                    self.draw_oncurve_pt(self.transmutor_container, coord, self.transmutor_color, "rectangle")


    def update_component_info(self):
        if self.g == None:
            return
        self.f = self.g.font
        # Set up a decomposed glyph object
        self.decomp_glyph = RGlyph()
        self.decomp_glyph.width = self.g.width
        decomp_pen = DecomposePointPen(self.f, self.decomp_glyph.getPointPen())
        self.g.drawPoints(decomp_pen)
        # Get all on-curve points for the component, and nothing else
        digest_pen = DigestPointPen()
        self.decomp_glyph.drawPoints(digest_pen)
        self.comp_oncurve_coords = [entry[0] for entry in digest_pen.getDigest() if entry[1] != None and type(entry[0]) == tuple and entry[0] not in self.oncurve_coords] 


    def update_oncurve_info(self):
        self.oncurves_on = getGlyphViewDisplaySettings().get('OnCurvePoints')
        if self.g == None:
            return
        # Use a digest point pen to get only on-curves
        digest_pen = DigestPointPen()
        self.g.drawPoints(digest_pen)
        # Get all on-curve points
        self.oncurve_coords = [entry[0] for entry in digest_pen.getDigest() if entry[1] != None and type(entry[0]) == tuple] 


    def update_anchor_info(self):
        '''Store updated anchor coordinates'''
        self.anchors_on = getGlyphViewDisplaySettings().get('Anchors')
        if self.g == None:
            return
        self.anc_coords = [(a.x, a.y) for a in self.g.anchors]


    def update_guidelines_info(self):
        '''Store updated guideline coordinates'''
        # Font guidelines
        self.f_guide_xs    = {}
        self.f_guide_ys    = {}
        self.f_guide_diags = []
        if self.f != None:
            for guideline in self.f.guidelines:
                if guideline.color:
                    guide_color = guideline.color
                else:
                    guide_color = self.col_glob_guides
                if guideline.angle in [0, 180]:
                    self.f_guide_ys[otRound(guideline.y)] = guide_color
                elif guideline.angle in [90, 270]:
                    self.f_guide_xs[otRound(guideline.x)] = guide_color
                else:
                    self.f_guide_diags.append(((guideline.x, guideline.y), guideline.angle, guide_color))

        # Glyph guidelines
        if self.g != None:
            self.g_guide_xs    = {}
            self.g_guide_ys    = {}
            self.g_guide_diags = []
            for guideline in self.g.guidelines:
                if guideline.color:
                    guide_color = guideline.color
                else:
                    guide_color = self.col_loc_guides
                if guideline.angle in [0, 180]:
                    self.g_guide_ys[otRound(guideline.y)] = guide_color
                elif guideline.angle in [90, 270]:
                    self.g_guide_xs[otRound(guideline.x)] = guide_color
                else:
                    self.g_guide_diags.append(((guideline.x, guideline.y), guideline.angle, guide_color))
        
        
    def update_font_info(self):
        # Get font dimensions y's
        self.font_dim = [
            self.f.info.descender, 0, self.f.info.xHeight,
            self.f.info.ascender, self.f.info.capHeight
            ]
        
        # Get blue y's and whether they're set to be displayed
        self.blue_vals  = self.f.info.postscriptBlueValues + self.f.info.postscriptOtherBlues
        self.fblue_vals = self.f.info.postscriptFamilyBlues + self.f.info.postscriptFamilyOtherBlues
        self.update_blues_display_settings()


    def update_blues_display_settings(self):
        self.blues_on  = getGlyphViewDisplaySettings()['Blues']
        self.fblues_on = getGlyphViewDisplaySettings()['FamilyBlues']


    def check_oncurves(self):
        if self.g == None:
            return
        self.oncurve_container.clearSublayers()
        # On-curve points
        if self.oncurves_on is True:
            for coord in self.oncurve_coords:
                self.check_alignment(self.oncurve_container, coord)

                     
    def check_anchors(self):   
        if self.g == None:
            return
        self.anchor_container.clearSublayers()
        # Anchors
        if self.anchors_on is True:
            for coord in self.anc_coords:
                self.check_alignment(self.anchor_container, coord)

                
    def check_tool_points(self):
        if self.g == None or CurrentGlyphWindow() != self.glyph_editor:
            return
        self.tool_container.clearSublayers()
        # Slice tool intersections
        if self.slice_tool_active:
            for coord in self.tool_coords:
                self.check_alignment(self.tool_container, coord)
        # Shape tool future points
        elif self.shape_tool_active:
            for coord in self.tool_coords:
                if self.check_alignment(self.tool_container, coord) == True:
                    self.draw_oncurve_pt(self.tool_container, coord, self.shape_pt_color, self.shape_pt_shape)
                

    def check_comp(self):
        if self.g == None:
            return
        self.comp_container.clearSublayers()
        # Component points
        for coord in self.comp_oncurve_coords:
            if self.check_alignment(self.comp_container, coord) == True:
                self.draw_oncurve_pt(self.comp_container, coord, self.col_component, "oval")
                
                
    def check_alignment(self, container, coord):
        alignment_match = False
        x, y = coord[0], coord[1]

        if self.g != None:

            angle = 0
            color = None

            # ==== HORIZONTAL STUFF ==== #
            # Global horizontal guides
            if otRound(y) in self.f_guide_ys.keys():
                color = self.f_guide_ys[otRound(y)]
                if self.settings["showGlobalGuidesCheckbox"]:
                    self.draw_eye(container, coord, color, angle)
                    alignment_match = True

            # Local horizontal guides
            elif otRound(y) in self.g_guide_ys.keys():
                color = self.g_guide_ys[otRound(y)]
                if self.settings["showLocalGuidesCheckbox"]:
                    self.draw_eye(container, coord, color, angle)
                    alignment_match = True

            # Font dimensions
            elif otRound(y) in self.font_dim:                
                color = self.col_font_dim
                if self.settings["showFontDimensionsCheckbox"]:
                    self.draw_eye(container, coord, color, angle)
                    alignment_match = True

            # Blues
            elif otRound(y) in self.blue_vals:
                if self.blues_on is True:
                    color = self.col_blues
                    if self.settings["showBluesCheckbox"]:
                        self.draw_eye(container, coord, color, angle)
                        alignment_match = True

            # Family blues
            elif otRound(y) in self.fblue_vals:
                if self.fblues_on is True:
                    color = self.col_fblues
                    if self.settings["showFamilyBluesCheckbox"]:
                        self.draw_eye(container, coord, color, angle)
                        alignment_match = True

            # ==== VERTICAL STUFF ==== #
            angle = 90
            # Global vertical guides
            if otRound(x) in self.f_guide_xs.keys():
                color = self.f_guide_xs[otRound(x)]
                if self.settings["showGlobalGuidesCheckbox"]:
                    self.draw_eye(container, coord, color, angle)
                    alignment_match = True

            # Local vertical guides
            elif otRound(x) in self.g_guide_xs.keys():
                color = self.g_guide_xs[otRound(x)]
                if self.settings["showLocalGuidesCheckbox"]:
                    self.draw_eye(container, coord, color, angle)
                    alignment_match = True
                
            # Margins
            elif otRound(x) in [0, self.g.width]:
                color = self.col_margins
                if self.settings["showMarginsCheckbox"]:
                    self.draw_eye(container, coord, color, angle)
                    alignment_match = True

            # ==== DIAGONAL STUFF ==== #
            for gd_info in self.g_guide_diags:
                angle, color = gd_info[1], gd_info[2]
                result = is_on_diagonal(gd_info[0], angle, (x, y))
                if result:
                    ## Tested code to clean up the diagonal eye presentation
                    # diag_x, diag_y = get_diagonal_xy((gd.x, gd.y), angle, (x, y))  # Try to avoid the eye looking disjointed from the guide.
                    if self.settings["showLocalGuidesCheckbox"]:
                        self.draw_eye(container, coord, color, angle)
                        alignment_match = True
                    
            for gd_info in self.f_guide_diags:
                angle, color = gd_info[1], gd_info[2]
                result = is_on_diagonal(gd_info[0], angle, (x, y))
                if result:
                    ## Tested code to clean up the diagonal eye presentation
                    # diag_x, diag_y = get_diagonal_xy((gd.x, gd.y), angle, (x, y))  # Try to avoid the eye looking disjointed from the guide.
                    if self.settings["showGlobalGuidesCheckbox"]:
                        self.draw_eye(container, coord, color, angle)
                        alignment_match = True
                    
        return alignment_match
                
                
    def draw_eye(self, container, coord, color, angle):
        eye = container.appendSymbolSublayer(
                position      = (coord[0], coord[1]),
                rotation      = angle,
                imageSettings = dict(
                                    name        = "eyeliner.eye",
                                    radius      = self.rad_base, 
                                    strokeColor = color,
                                    fillColor   = (1,1,1,0)  # self.fill_color
                                    )
                )
                
                
    def draw_oncurve_pt(self, container, coord, color, shape):
        component_point  = container.appendSymbolSublayer(
                position = (coord[0], coord[1])
                )
        component_point.setImageSettings(
                dict(
                    name      = shape,
                    size      = (otRound(self.point_radius*2), otRound(self.point_radius*2)),
                    fillColor = tuple(color)
                )
            )
        
        
registerGlyphEditorSubscriber(Eyeliner)
