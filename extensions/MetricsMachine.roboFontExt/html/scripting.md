###### [Home](index.html)

---

## Scripting

MetricsMachine provides a scripting API for interacting with the interface and manipulating object data.


### Accessing Objects

##### `MetricsMachineFont(otherFont)`

	import metricsMachine
	font = metricsMachine.MetricsMachineFont(other)

Wrap `other` as an instance of `MetricsMachineFont`. `other` must be a font object provided by RoboFont's `CurrentFont`, `AllFonts`, `OpenFont` or similar functions.

##### `AllFonts()`

	import metricsMachine
	fonts = metricsMachine.AllFonts()

Returns a list of all fonts, as instances of `MetricsMachineFont`.

##### `CurrentFont()`

	import metricsMachine
	font = metricsMachine.CurrentFont()

Returns the current font as an instance of `MetricsMachineFont`.


### Object API

These objects inherit the behavior of the [RoboFont fontParts objects.](https://robofont.com/documentation/building-tools/toolkit/fontparts/) All MetricsMachine objects have the same API and functionality, unless otherwise stated.

#### MetricsMachineKerning

The MetricsMachine kerning object scripting API is built on top of the same conflict-preventing behavior that is seen in the MetricsMachine UI. This means that incoming data is automatically normalized so that conflicting kerning pairs are not created. If you require fine-grained control, use the RoboFont kerning object instead of `MetricsMachineKerning`.

##### Manipulating Individual Pairs

All of the standard `fontParts` dictionary-like methods for inspecting and manipulating kerning data are supported. However, getting and setting has the same behavior as the UI. The pair that you are getting or setting *may not* be the actual pair that is stored in the font's kerning. MetricsMachine always converts a pair to the highest-level pair that represents the given pair. For example, let's say that your font has these two groups:

- `public.kern1.A` contains A, Aacute.
- `public.kern2.B` contains B, B.alt1.

If you ask MetricsMachine for the kerning value for `("A", "B")` it will look for four possible values, in this order:

1. `("A", "B")`
2. `("public.kern1.A", "B")`
3. `("A", "public.kern2.B")`
4. `("public.kern1.A", "public.kern2.B")`

The first of these that is found in the stored kerning data is the highest-level representation of `("A", "B")` and the stored value is *the* value for `("A", "B")`. Thus, interacting with `("A", "B")` may not result in interacting directly with `("A", "B")`. For further information on pair levels, refer to the [kerning.plist section of the UFO Specification](http://unifiedfontobject.org/versions/ufo3/kerning.plist/).

The only exception to this are, er, exceptions.

##### Exceptions

###### `makeException(pair, value)`

	font.kerning.makeException(("A", "B"), 0)

Make `pair` an exception with `value`. This will not resolve to a higher-level pair. The pair that you give as `pair` is the exact pair that will be created. This will automatically remove any conflicting exceptions created by the addition of the exception for `pair`.

###### `breakException(pair)`

	font.kerning.breakException(("A", "B"))

Remove the exception for `pair`. This will not resolve to a higher-level pair. The pair that you give as `pair` is the exact pair that will be removed.

###### `getPairType(pair)`

Return a tuple of two strings indicating the pair type. Each string will be one of the following:

- `"group"`
- `"glyph"`
- `"exception"`

This only indicates if `pair` would be an exception, it does not indicate that `pair` currently exists in the kerning.

###### `getActualPair(pair)`

	font.kerning.getActualPair(("A", "V"))

Return a tuple of the pair that represents `pair` as stored in the kerning. If there is no pair this will return `None`.

###### `isException(pair)`

	font.kerning.isException(("A", "B"))

Return a `boolean` indicating if `pair` would be an exception or not. This only indicates if `pair` would be an exception, it does not indicate that `pair` currently exists in the kerning.

##### Transformations

These methods correspond directly to their counterparts in the UI. For full reference about what these do, refer to the main transformation documentation. The only difference between these and their equivalents in the UI is that the API directly uses glyph and group names whereas the UI uses search strings.

###### `scaleTransformation(factor, pairs=None)`

	font.kerning.scaleTransformation(2.0, pairs=[("A", "A"), ("A", "B")])

Scale `pairs` by `factor`. If `pairs` is `None` the transformation will apply to all kerning pairs. This functions exactly the same as the *scale* transformation in the UI.

###### `roundTransformation(increment, pairs=None, removeRedundantExceptions=True)`

	font.kerning.roundTransformation(5, pairs=[("A", "A"), ("A", "B")])

Round all `pairs` to increments of `increment`. If `pairs` is `None` the transformation will apply to all kerning pairs. If `removeRedundantExceptions` is `True`, redundant exceptions will be removed. This functions exactly the same as the *round* transformation in the UI.

###### `shiftTransformation(value, pairs=None)`

	font.kerning.shiftTransformation(10, pairs=[("A", "A"), ("A", "B")])

Add `value` to all `pairs`. If `pairs` is `None` the transformation will apply to all kerning pairs. This functions exactly the same as the *shift* transformation in the UI.

###### `thresholdTransformation(value, pairs=None, removeRedundantExceptions=True)`

	font.kerning.thresholdTransformation(10, pairs=[("A", "A"), ("A", "B")])

Remove any `pairs` that have a value below `value`. If `pairs` is `None` the transformation will apply to all kerning pairs. If `removeRedundantExceptions` is `True`, redundant exceptions will be removed. This functions exactly the same as the *threshold* transformation in the UI.

###### `removeTransformation(pairs=None)`

	font.kerning.removeTransformation([("A", "A"), ("A", "B")])

Remove `pairs`. If `pairs` is `None` the transformation will apply to all kerning pairs. This functions exactly the same as the *remove* transformation in the UI.

###### `copyTransformation(side1Source, side2Source, side1Replacement, side2Replacement, pairs=None)`

	font.kerning.copyTransformation(
		side1Source=["A", "B"],
		side2Source=["A", "B"],
		side1Replacement=["A.sc", "B.sc"],
		side2Replacement=["A.sc", "B.sc"],
		pairs=[("A", "A"), ("A", "B")]
	)

Copy `pairs` by aligning members of `side1Source` to `side1Replacement` and `side2Source` to `side2Replacement`. If `pairs` is `None` the transformation will apply to all kerning pairs. This functions exactly the same as the *copy* transformation in the UI.

##### Import and Export

###### `compileFeatureText(insertSubtableBreaks=False)`

	font.kerning.compileFeatureText()

Compile a kern feature to a string. If `insertSubtableBreaks` is `True` subtable breaks will be inserted.

###### `importKerning(path)`

	font.kerning.importKerning("/path/to/font.ufo")

Import all kerning and kerning groups from `path`. `path` must be a path to a `UFO` file.

###### `exportFeatureText(path, insertSubtableBreaks=False)`

	font.kerning.exportFeatureText("/path/to/here.fea")

Compile a kern feature into a file located at `path`. If `insertSubtableBreaks` is `True` subtable breaks will be inserted.

###### `insertFeatureText(insertSubtableBreaks=False)`

	font.kerning.insertFeatureText()

Compile a kern feature and insert it into `font.features`. If `insertSubtableBreaks` is `True` subtable breaks will be inserted.

#### MetricsMachineGroups

Groups are not editable apart from the `importKerningGroups` and `importReferenceGroups` methods. All other manipulation methods will raise a `MetricsMachineScriptingError` traceback. *Why is this so strict?* Because editing groups can cause kerning conflicts and these are not easily resolvable with a script. If you need to edit groups, please contact the MetricsMachine developers and we'll consider building support for this.

###### `importKerningGroups(pathOrGroups)`

	font.groups.importKerningGroups("/path/to/font.ufo")

Import all kerning groups from `pathOrGroups`. `pathOrGroups` may be a path to a `MMG` file, a path to a `UFO` file or a dictionary of groups.

###### `exportkerningGroups(path)`

	font.groups.exportkerningGroups("/path/to/groups.mmg")

Export all kerning groups to a MMG file located at `path`.

###### `importReferenceGroups(pathOrGroups)`

	font.groups.importReferenceGroups("/path/to/font.ufo")

Import all reference groups from `pathOrGroups`. `pathOrGroups` may be a path to a `UFO` file or a dictionary of groups.


### Interface

These functions get data from, set data to and trigger actions in the MetricsMachine window. So, obviously, the woindow needs to be open.

###### `LoadPairList(path, font=None)`

	metricsMachine.LoadPairList("/path/to/list.txt")

Load the pair list from `path` into the window for `font`. If `font` is `None`, the current font will be used.

###### `SetPairList(pairList, font=None)`

	pairs = [
		("A", "A"),
		("A", "B"),
	]
	metricsMachine.SetPairList(pairs)

Set the `pairs` into the window for `font`. The pair list must be formatted as a list of glyph name pairs. If `font` is `None`, the current font will be used.

###### `GetPairList(font=None)`

	metricsMachine.GetPairList()

Get the pair list in the window for `font`. If `font` is `None`, the current font will be used.

###### `SetCurrentPair(pair, font=None)`

	metricsMachine.SetCurrentPair(("A", "B"))

Set `pair` in the window for `font`. If `font` is `None`, the current font will be used.

###### `GetCurrentPair(font=None)`

Get the pair in the window for `font`. If `font` is `None`, the current font will be used.

###### `GetPreviewText(font=None)`

Get the string representing the contents of the preview panel in the window for `font`. If `font` is `None`, the current font will be used.

###### `SetPreviewText(text, font=None)`

	metricsMachine.SetPreviewText("Hello World")

Set the `text` as the string representing the contents of the preview panel in the window for `font`. The `text` string may contain characters or `/` delimited glyph names. If `font` is `None`, the current font will be used.

###### `OpenGroupEditor(font=None)`

Open the group editor sheet for `font`. If `font` is `None`, the current font will be used.

###### `OpenReferenceGroupEditor(font=None)`

Open the reference group editor sheet for `font`. If `font` is `None`, the current font will be used.

###### `OpenTransformationEditor(font=None)`

Open the transformation sheet for `font`. If `font` is `None`, the current font will be used.

###### `OpenSpreadsheetEditor(font=None)`

Open the spreadsheet for `font`. If `font` is `None`, the current font will be used.

###### `OpenPairListEditor(font=None)`

Open the pair list builder sheet for `font`. If `font` is `None`, the current font will be used.

### Events

Events are posted through `mojo.events`.

###### `MetricsMachine.ControllerWillOpen`

Posted when the main MetricsMachine window is about to open. The info dictionary contains: `font`, `controller`

###### `MetricsMachine.ControllerWillClose`

Posted when the main MetricsMachine window is about to close. The info dictionary contains: `font`, `controller `

###### `MetricsMachine.currentPairChanged`

Posted when the pair on display in the window is changed. The info dictionary contains: `font`, `pair`

---

###### [Next: Home](index.html)