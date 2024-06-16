import vanilla
from AppKit import NSFont, NSFontManager, NSFontAttributeName, NSParagraphStyleAttributeName, NSMutableParagraphStyle, NSAttributedString

class ReferenceCharacterWindow:
    def __init__(self):
        self.fonts = self.getSystemFonts()
        
        # Set default font_name based on availability
        self.font_name = "NotoSansJP-Bold" if "NotoSansJP-Bold" in self.fonts else (self.fonts[0] if self.fonts else "NotoSansJP-Bold")
        
        self.character = "う"
        
        # Calculate initial window size based on character size
        font = NSFont.fontWithName_size_(self.font_name, 100)
        if font:
            text_size = self.calculateTextSize(self.character, font)
            initial_width = max(int(text_size.width) + 20, 200)  # Minimum width 200 pixels
            initial_height = int(text_size.height) + 50
        else:
            initial_width = 200
            initial_height = 150
        
        self.w = vanilla.Window((initial_width, initial_height), "Reference Character Viewer")
        
        # Centered and line-height adjusted textBox
        self.w.textBox = vanilla.TextBox((10, 40, -10, -10), "", alignment='center')
        
        # Inputs
        self.w.characterInput = vanilla.EditText((10, 10, -10, 24), self.character, callback=self.updateCharacter)
        self.w.fontInput = vanilla.PopUpButton((10, 40, -10, 24), self.fonts, callback=self.updateFont)
        
        # Select NotoSansJP-Bold if it exists in self.fonts
        if "NotoSansJP-Bold" in self.fonts:
            self.w.fontInput.set(self.fonts.index("NotoSansJP-Bold"))
        
        self.updateDisplay()
        self.w.open()
    
    def updateCharacter(self, sender):
        self.character = sender.get()
        self.updateDisplay()
    
    def updateFont(self, sender=None):
        index = self.w.fontInput.get()
        self.font_name = self.fonts[index]
        self.updateDisplay()
    
    def updateDisplay(self):
        try:
            font = NSFont.fontWithName_size_(self.font_name, 100)
            if not font:
                raise ValueError(f"Font '{self.font_name}' not found.")
            
            attributes = {
                NSFontAttributeName: font,
                NSParagraphStyleAttributeName: self.centeredParagraphStyle(),
            }
            
            attrString = NSAttributedString.alloc().initWithString_attributes_(self.character, attributes)
            
            self.w.textBox.set(attrString)

            # Resize the window to fit the current character size
            text_size = self.calculateTextSize(self.character, font)
            new_width = max(int(text_size.width) + 40, 200)  # Minimum width 200 pixels
            new_height = int(text_size.height) + 60
            self.w.setPosSize((self.w.getPosSize()[0], self.w.getPosSize()[1], new_width, new_height))

        except Exception as e:
            self.w.textBox.set(f"Error: {e}")
    
    def centeredParagraphStyle(self):
        paragraphStyle = NSMutableParagraphStyle.alloc().init()
        paragraphStyle.setAlignment_(1)  # 1 for center alignment
        return paragraphStyle
    
    def calculateTextSize(self, text, font):
        attributes = {NSFontAttributeName: font}
        attrString = NSAttributedString.alloc().initWithString_attributes_(text, attributes)
        return attrString.size()
    
    def getSystemFonts(self):
        manager = NSFontManager.sharedFontManager()
        font_list = manager.availableFonts()
        filtered_fonts = [font for font in font_list if not font.startswith('.')]
        return filtered_fonts

if __name__ == "__main__":
    ReferenceCharacterWindow()
