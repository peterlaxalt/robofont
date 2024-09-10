from vanilla import *
from mojo.UI import CurrentFontWindow, OpenSpaceCenter, CurrentGlyphWindow
from mojo.events import addObserver, removeObserver
from glyphNameFormatter.reader import *
from AppKit import NSPasteboard, NSStringPboardType

class KerningVisualizer:
    def __init__(self):
        self.f = CurrentFont()
        
        # Load Unicode groups
        self.unicode_groups = list(set(u2r(u) for u in uni2name.keys()))
        self.unicode_groups.sort()
        
        # Find index of "Basic Latin"
        self.basic_latin_index = self.unicode_groups.index("Basic Latin") if "Basic Latin" in self.unicode_groups else 0
        
        # Grid configuration
        self.columns = 4
        self.rows = 16
        self.chars_per_page = self.columns * self.rows
        
        # Calculate window size
        windowWidth = 380  # Reduced width
        windowHeight = 660  # Adjusted height
        
        self.w = FloatingWindow((windowWidth, windowHeight), "Kerning Pairs")
        
        # Pair 1 Column
        self.w.pair1Group = Group((10, 10, 172, -120))
        
        # Divider
        self.w.divider = VerticalLine((190, 10, 1, -120))
        
        # Pair 2 Column
        self.w.pair2Group = Group((198, 10, 172, -120))
        
        # Setup both columns
        self.setupPairColumn(self.w.pair1Group, "Pair 1", True)
        self.setupPairColumn(self.w.pair2Group, "Pair 2", False)
        
        # Preview
        self.w.previewInput = EditText((10, -110, -70, 22), "", placeholder="Preview of generated string")
        self.w.copyButton = Button((-60, -110, 50, 22), "Copy", callback=self.copyToClipboard)
        
        # Update Space Center button
        self.w.updateButton = Button((10, -80, -10, 30), "Update Space Center",
                                     callback=self.updateSpaceCenter)
        self.w.updateButton.enable(True)
        
        # Statistics
        self.w.stats = TextBox((10, -40, -10, 22), "", alignment="center")
        
        self.spaceCenter = None
        
        self.w.open()
        
        # Initial update of preview and stats
        self.updatePreviewAndStats()
        self.selectAll(self)
    
    def setupPairColumn(self, group, title, isFirstPair):
        group.title = TextBox((0, 0, -0, 20), title)
        
        # Unicode group dropdown
        group.groupDropdown = PopUpButton((0, 30, -0, 20), self.unicode_groups, callback=self.groupSelected)
        group.groupDropdown.set(self.basic_latin_index)  # Set "Basic Latin" as default
        
        # Prefix and suffix inputs
        group.prefixInput = EditText((0, 60, -25, 20), placeholder="prefix")
        group.suffixInput = EditText((0, 90, -25, 20), placeholder="suffix")
        
        # 'Use current glyph' buttons
        group.prefixButton = Button((-20, 60, 20, 20), "+", callback=self.useCurrentGlyph, sizeStyle="small")
        group.suffixButton = Button((-20, 90, 20, 20), "+", callback=self.useCurrentGlyph, sizeStyle="small")
        
        # Set tooltips
        group.prefixButton.getNSButton().setToolTip_("use current glyph")
        group.suffixButton.getNSButton().setToolTip_("use current glyph")
        
        # Character grid
        group.characterContainer = Group((0, 120, -0, 400))
        
        # Select All / None buttons (only for Pair 2)
        if not isFirstPair:
            button_width = (group.getPosSize()[2] - 8) / 2  # 8px padding between
            group.selectAllButton = Button((0, -50, button_width, 20), "All", callback=self.selectAll)
            group.selectNoneButton = Button((button_width + 8, -50, button_width, 20), "None", callback=self.selectNone)
        
        # Pagination
        group.prevButton = Button((0, -22, 30, 20), "«", callback=self.prevPage)
        group.nextButton = Button((-30, -22, 30, 20), "»", callback=self.nextPage)
        group.pageInfo = TextBox((35, -22, -35, 20), "1/1", alignment="center")
        
        # Initialize attributes
        group.selected_chars = set()
        group.current_page = 1
        group.all_chars = []
        
        self.updateCharacterGrid(group)
    
    def groupSelected(self, sender):
        # Determine which group the sender belongs to
        if sender == self.w.pair1Group.groupDropdown:
            group = self.w.pair1Group
        elif sender == self.w.pair2Group.groupDropdown:
            group = self.w.pair2Group
        else:
            return  # This should not happen, but just in case
        
        group.selected_chars.clear()
        group.current_page = 1
        self.updateCharacterGrid(group)
        self.updatePreviewAndStats()
    
    def updateCharacterGrid(self, group):
        # Clear existing checkboxes
        for attr in list(group.characterContainer.__dict__.keys()):
            if attr.startswith('char_'):
                delattr(group.characterContainer, attr)
        
        # Get characters for the selected Unicode group
        group_name = self.unicode_groups[group.groupDropdown.get()]
        group.all_chars = [chr(u) for u in uni2name.keys() if u2r(u) == group_name and chr(u) != ' ']
        
        # Calculate pagination
        start_index = (group.current_page - 1) * self.chars_per_page
        end_index = start_index + self.chars_per_page
        chars = group.all_chars[start_index:end_index]
        
        # Create new checkboxes
        buttonSize = (40, 20)  # Adjusted width
        gutter = 2
        
        for i, char in enumerate(chars):
            x = (i % self.columns) * (buttonSize[0] + gutter)
            y = (i // self.columns) * (buttonSize[1] + gutter)
            checkbox = CheckBox((x, y, buttonSize[0], buttonSize[1]), char, callback=self.characterSelected)
            checkbox.set(char in group.selected_chars)
            setattr(group.characterContainer, f'char_{i}', checkbox)
        
        # Update pagination
        total_pages = (len(group.all_chars) - 1) // self.chars_per_page + 1
        group.pageInfo.set(f"{group.current_page}/{total_pages}")
        group.prevButton.enable(group.current_page > 1)
        group.nextButton.enable(group.current_page < total_pages)
        group.prevButton.show(total_pages > 1)
        group.nextButton.show(total_pages > 1)
        group.pageInfo.show(total_pages > 1)
        
        # Select first character by default for Pair 1
        if group == self.w.pair1Group and not group.selected_chars:
            first_checkbox = getattr(group.characterContainer, 'char_0', None)
            if first_checkbox:
                first_checkbox.set(True)
                group.selected_chars.add(first_checkbox.getTitle())
        
        # Update All/None button for Pair 2
        if group == self.w.pair2Group:
            self.updateAllNoneButton()
    
    def prevPage(self, sender):
        group = self.w.pair1Group if sender == self.w.pair1Group.prevButton else self.w.pair2Group
        if group.current_page > 1:
            group.current_page -= 1
            self.updateCharacterGrid(group)
    
    def nextPage(self, sender):
        group = self.w.pair1Group if sender == self.w.pair1Group.nextButton else self.w.pair2Group
        total_pages = (len(group.all_chars) - 1) // self.chars_per_page + 1
        if group.current_page < total_pages:
            group.current_page += 1
            self.updateCharacterGrid(group)
    
    def characterSelected(self, sender):
        group = self.w.pair1Group if sender.getPosSize()[0] < 190 else self.w.pair2Group
        if sender.get():
            group.selected_chars.add(sender.getTitle())
        else:
            group.selected_chars.discard(sender.getTitle())
        if group == self.w.pair2Group:
            self.updateAllNoneButton()
        self.updatePreviewAndStats()
    
    def selectAll(self, sender):
        self.w.pair2Group.selected_chars = set(self.w.pair2Group.all_chars)
        self.updateCharacterGrid(self.w.pair2Group)
        self.updateAllNoneButton()
        self.updatePreviewAndStats()
    
    def selectNone(self, sender):
        self.w.pair2Group.selected_chars.clear()
        self.updateCharacterGrid(self.w.pair2Group)
        self.updateAllNoneButton()
        self.updatePreviewAndStats()
    
    def updateAllNoneButton(self):
        all_selected = len(self.w.pair2Group.selected_chars) == len(self.w.pair2Group.all_chars)
        self.w.pair2Group.selectAllButton.enable(not all_selected)
        self.w.pair2Group.selectNoneButton.enable(all_selected)
    
    def useCurrentGlyph(self, sender):
        group = self.w.pair1Group if sender in (self.w.pair1Group.prefixButton, self.w.pair1Group.suffixButton) else self.w.pair2Group
        input_field = group.prefixInput if sender in (self.w.pair1Group.prefixButton, self.w.pair2Group.prefixButton) else group.suffixInput
        
        glyph_window = CurrentGlyphWindow()
        if glyph_window:
            glyph = glyph_window.getGlyph()
            if glyph and glyph.unicode is not None:
                current = input_field.get()
                input_field.set(current + chr(glyph.unicode))
                self.updatePreviewAndStats()
    
    def updatePreviewAndStats(self):
        pair1_prefix = self.w.pair1Group.prefixInput.get()
        pair1_suffix = self.w.pair1Group.suffixInput.get()
        pair2_prefix = self.w.pair2Group.prefixInput.get()
        pair2_suffix = self.w.pair2Group.suffixInput.get()
        
        pairs = []
        for char1 in self.w.pair1Group.selected_chars:
            for char2 in self.w.pair2Group.selected_chars:
                pairs.append(f"{pair1_prefix}{char1}{pair1_suffix}{pair2_prefix}{char2}{pair2_suffix}")
        
        text = " ".join(pairs).replace("\\", "\\\\")
        self.w.previewInput.set(text)
        
        total_chars = sum(len(pair) for pair in pairs)
        num_pairs = len(pairs)
        num_groups = len(self.w.pair1Group.selected_chars)
        
        stats = f"({total_chars} characters, {num_pairs} pairs, {num_groups} groups)"
        self.w.stats.set(stats)
    
    def copyToClipboard(self, sender):
        text = self.w.previewInput.get()
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setString_forType_(text, NSStringPboardType)
    
    def updateSpaceCenter(self, sender):
        text = self.w.previewInput.get()
        
        if self.spaceCenter is None or not hasattr(self.spaceCenter, 'window'):
            self.spaceCenter = OpenSpaceCenter(self.f)
        
        self.spaceCenter.set(text)
        self.spaceCenter.setPointSize(36)
    
    def windowCloses(self, sender):
        if self.spaceCenter and hasattr(self.spaceCenter, 'window'):
            self.spaceCenter.window.close()

KerningVisualizer()