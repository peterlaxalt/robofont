# RoboFont Script
# CharacterSet Switcher
# Alexander Lubovenko
# http://github.com/typedev

from vanilla import *
from mojo.UI import *
from fontParts.world import CurrentFont
from defconAppKit.windows.baseWindow import BaseWindowController


extversion = 'v0.3 RF3'

class CharsetsSwitcherWindow(BaseWindowController):
	def __init__ (self):
		self.w = FloatingWindow((230, 100), title = 'CharacterSet Switcher ' + extversion)
		self.w.cbCharsetsList = ComboBox((20, 20, -20, 21),
		                                 getCharacterSets().keys(),
		                                 callback = self.cbCharsetsListCallback)
		self.w.chkBox = CheckBox((20,50,80,21),'All Fonts', callback = None, value = False, sizeStyle = 'regular')
		self.w.btnApply = Button((-80, 50, 60, 21),
		                         title = 'Apply',
		                         callback = self.btnApplyCallback)

		self.w.open()

	def switchCharset(self, font):
		charsetName = self.w.cbCharsetsList.get()
		font.lib['public.glyphOrder'] = getCharacterSets()[charsetName]
		font.glyphOrder = font.lib['public.glyphOrder']
		print ('+'*80)
		print (font.info.familyName, font.info.styleName)
		print ('CharacterSet switched to', charsetName)


	def cbCharsetsListCallback (self, info):
		pass


	def btnApplyCallback (self, info):
		if not self.w.chkBox.get():
			font = CurrentFont()
			self.switchCharset(font)
		else:
			for font in AllFonts():
				self.switchCharset(font)





CharsetsSwitcherWindow()