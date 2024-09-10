import ezui
from mojo.UI import CurrentSpaceCenter
from mojo.subscriber import Subscriber, registerSpaceCenterSubscriber

class SpaceCenterTuner(Subscriber, ezui.WindowController):

    def build(self):
        """
    	Fine-tune Space Center sizing and spacing.
	
    	Ryan Bugden
    	2023.07.11 — EZUI
    	2020.06.17
    	2020.05.18
    	2019.06.02
    	"""
        
        self.csc = CurrentSpaceCenter()
        self.x_off, self.y_off = self.csc.getOffset()
        self.lv = self.csc.glyphLineView
        
        current_size = self.csc.getPointSize()
        current_lh = self.csc.getLineHeight()
        
        content = """
        * TwoColumnForm    @form

        > : Size:
        > ---X--- [__]     @sizeSlider

        > : Line-height:
        > ---X--- [__]     @lhSlider

        > : Top-pad:
        > ---X--- [__]     @topPadSlider
        
        > : Side-pad:
        > ---X--- [__]     @sidePadSlider
        """
        descriptionData = dict(
            form=dict(
                titleColumnWidth=80,
                itemColumnWidth=300
            ),
            sizeSlider=dict(
                valueType="integer",
                minValue=0, 
                maxValue=300, 
                value=current_size,
                continuous=True, 
                sizeStyle='regular'
            ),
            lhSlider=dict(
                valueType="integer",
                minValue=-200, 
                maxValue=1000, 
                tickMarks=49,
                stopOnTickMarks=True,
                value=current_lh,
                continuous=True, 
                sizeStyle='regular'
            ),
            topPadSlider=dict(
                valueType="integer",
                minValue=0, 
                maxValue=500, 
                value=self.y_off,
                continuous=True, 
                sizeStyle='regular'
            ),
            sidePadSlider=dict(
                valueType="integer",
                minValue=0, 
                maxValue=1000, 
                value=self.x_off,
                continuous=True, 
                sizeStyle='regular'
            )
        )
        self.w = ezui.EZWindow(
            title='Space Center Tuner',
            content=content,
            descriptionData=descriptionData,
            controller=self,
            size="auto"
        )

    def started(self):
        self.w.open()
        
    def spaceCenterDidKeyDown(self, info):
        self.update_sliders()
    def spaceCenterDidChangeText(self, info):
        self.update_sliders()
        
    def update_sliders(self):
        self.csc = CurrentSpaceCenter()
        self.w.getItem('sizeSlider').set(self.csc.getPointSize())
        self.w.getItem('lhSlider').set(self.csc.getLineHeight())

    def sizeSliderCallback(self, sender):
        self.csc = CurrentSpaceCenter()
        self.des_size = sender.get()
        self.csc.setPointSize(self.des_size)
        
    def lhSliderCallback(self, sender):
        self.csc = CurrentSpaceCenter()
        self.des_lh = sender.get()
        self.csc.setLineHeight(self.des_lh)

    def topPadSliderCallback(self, sender):
        self.csc = CurrentSpaceCenter()
        self.y_off = sender.get()
        self.csc.setOffset((self.x_off, self.y_off))
        
    def sidePadSliderCallback(self, sender):
        self.csc = CurrentSpaceCenter()
        self.x_off = sender.get()
        self.csc.setOffset((self.x_off, self.y_off))

registerSpaceCenterSubscriber(SpaceCenterTuner)