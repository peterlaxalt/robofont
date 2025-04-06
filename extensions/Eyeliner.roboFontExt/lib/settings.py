import ezui
from mojo.subscriber import getRegisteredSubscriberEvents, registerSubscriberEvent
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.events import postEvent
from defaults import get_flattened_alpha, get_darkened_blue, EXTENSION_KEY, EXTENSION_DEFAULTS


class EyelinerSettings(ezui.WindowController):

    def build(self):
        content = """

        * TwoColumnForm        @form1
        
        > : Show Eyes:
        > [X] Font Dimensions  @showFontDimensionsCheckbox
        > [X] Local Guides     @showLocalGuidesCheckbox
        > [X] Global Guides    @showGlobalGuidesCheckbox
        > [X] Blue Zones       @showBluesCheckbox
        > [X] Family Blues     @showFamilyBluesCheckbox
        > [ ] Margins          @showMarginsCheckbox
        
        ---
        
        * TwoColumnForm        @form2
        
        > : Font Dimensions:
        > * HorizontalStack    @fontDimensionsColorStack
        >> * ColorWell         @fontDimensionsLightColorWell
        >> * ColorWell         @fontDimensionsDarkColorWell

        > : Blue Zones:
        > * HorizontalStack    @bluesColorStack
        >> * ColorWell         @bluesLightColorWell
        >> * ColorWell         @bluesDarkColorWell

        > : Family Blues:
        > * HorizontalStack    @familyBluesColorStack
        >> * ColorWell         @familyBluesLightColorWell
        >> * ColorWell         @familyBluesDarkColorWell

        > : Margins:
        > * HorizontalStack    @marginsColorStack
        >> * ColorWell         @marginsLightColorWell
        >> * ColorWell         @marginsDarkColorWell
        
        > :
        > * HorizontalStack    @labelStack
        >> Light Mode          @lightModeLabel
        >> Dark Mode           @darkModeLabel
        
        > ---
        
        > (Reset Defaults)     @resetDefaultsButton
        """
        title_column_width = 120
        item_column_width = 160
        colorwell_width = item_column_width / 2 - 5
        colorwell_height = 20
        descriptionData = dict(
            form1=dict(
                titleColumnWidth=title_column_width,
                itemColumnWidth=item_column_width
            ),
            form2=dict(
                titleColumnWidth=title_column_width,
                itemColumnWidth=item_column_width
            ),
            form3=dict(
                titleColumnWidth=title_column_width,
                itemColumnWidth=item_column_width
            ),
            fontDimensionsLightColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            fontDimensionsDarkColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            bluesLightColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            bluesDarkColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            familyBluesLightColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            familyBluesDarkColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            marginsLightColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            marginsDarkColorWell=dict(
                width=colorwell_width,
                height=colorwell_height
            ),
            lightModeLabel=dict(
                width=colorwell_width,
                sizeStyle='mini',
            ),
            darkModeLabel=dict(
                width=colorwell_width,
                sizeStyle='mini',
            ),
            resetDefaultsButton=dict(
                width='fill'
            )

        )
        self.w = ezui.EZPanel(
            title="Eyeliner Settings",
            content=content,
            descriptionData=descriptionData,
            controller=self
        )
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)
        prefs = getExtensionDefault(EXTENSION_KEY, fallback=EXTENSION_DEFAULTS)
        try:
            self.w.setItemValues(prefs)
        except KeyError as e:
            print(f"Eyeliner Settings error: {e}")
        
    def started(self):
        self.w.open()
        
    def contentCallback(self, sender):
        self.update_extension_settings()
        
    def resetDefaultsButtonCallback(self, sender):
        self.w.setItemValues(EXTENSION_DEFAULTS)
        self.update_extension_settings()
        
    def update_extension_settings(self):
        setExtensionDefault(EXTENSION_KEY, self.w.getItemValues())
        postEvent(f"{EXTENSION_KEY}.eyelinerSettingsDidChange")
        

if __name__ == '__main__':
    # Register a subscriber event for when Eyeliner settings change
    event_name = f"{EXTENSION_KEY}.eyelinerSettingsDidChange"
    if event_name not in getRegisteredSubscriberEvents():
        registerSubscriberEvent(
            subscriberEventName=event_name,
            methodName="eyelinerSettingsDidChange",
            lowLevelEventNames=[event_name],
            dispatcher="roboFont",
            documentation="Sent when Eyeliner extension settings have changed.",
            delay=None
        )
    EyelinerSettings()