import AppKit
import vanilla
from objc import super

from mm4.objects.mmGroups import bracketedUserFriendlyGroupName, validateGroupName
from mm4.interface.colors import *


_groupNameNote = """%s is an invalid group name.

Group names must adhere to these rules:
- the name must contain only alphanumeric, _ and . characters.
- the name must start with an alphabetic character.
- the name must be shorter than 24 characters."""

prefix = "public."


class ValidatingGroupNameFormatter(AppKit.NSFormatter):

    def initWithPrefix_groups_(self, prefix, groups):
        self = super(ValidatingGroupNameFormatter, self).init()
        self._groupPrefix = prefix
        self._groups = groups
        return self

    def dealloc(self):
        self._groups = None
        super(ValidatingGroupNameFormatter, self).dealloc()

    def stringForObjectValue_(self, obj):
        if obj is None or isinstance(obj, AppKit.NSNull):
            return ""
        return obj[len(self._groupPrefix):]

    def getObjectValue_forString_errorDescription_(self, value, string, error):
        isValid = validateGroupName(self._groupPrefix + string)
        if not isValid:
            errorString = _groupNameNote % string
        else:
            errorString = False
        groupName = self._groupPrefix + string
        return isValid, groupName, errorString

    def isPartialStringValid_newEditingString_errorDescription_(self, string, newString, error):
        isValid = validateGroupName(self._groupPrefix + string)
        if not isValid:
            return False, None, None
        return True, string, None


_referenceGroupNameNote = """%s is an invalid group name.

Groups beginning with 'public.kern' are reserved for internal use by MetricsMachine."""


class ValidatingReferenceGroupNameFormatter(AppKit.NSFormatter):

    def stringForObjectValue_(self, obj):
        return obj

    def getObjectValue_forString_errorDescription_(self, value, string, error):
        isValid = not string.startswith("public.kern")
        if not isValid:
            errorString = _referenceGroupNameNote % string
        else:
            errorString = None
        return isValid, string, errorString


class PairMemberFormatter(AppKit.NSFormatter):

    def stringForObjectValue_(self, obj):
        if obj is None or isinstance(obj, AppKit.NSNull):
            return ""
        if obj.startswith("public.kern"):
            obj = bracketedUserFriendlyGroupName(obj)
        return obj

    def objectValueForString_(self, string):
        return string

    def attributedStringForObjectValue_withDefaultAttributes_(self, obj, attributes):
        if obj is None or isinstance(obj, AppKit.NSNull):
            return ""
        if obj.startswith("public.kern"):
            if attributes[AppKit.NSForegroundColorAttributeName] == AppKit.NSColor.alternateSelectedControlTextColor():
                attributes[AppKit.NSForegroundColorAttributeName] = listViewSelectedGroupColor
            else:
                attributes[AppKit.NSForegroundColorAttributeName] = listViewGroupColor
        return AppKit.NSAttributedString.alloc().initWithString_attributes_(self.stringForObjectValue_(obj), attributes)

    def getObjectValue_forString_errorDescription_(self, value, string, error):
        return True, self.objectValueForString_(string), None


class GroupNameFormatter(PairMemberFormatter):
    pass


def KerningValueFormatter():
    formatter = AppKit.NSNumberFormatter.alloc().init()
    formatter.setFormatterBehavior_(AppKit.NSNumberFormatterBehaviorDefault)
    formatter.setNumberStyle_(AppKit.NSNumberFormatterNoStyle)
    formatter.setAllowsFloats_(False)
    formatter.setGeneratesDecimalNumbers_(False)
    formatter.setFormat_("#;0;-#")
    # 10.5+
    try:
        formatter.setPartialStringValidationEnabled_(True)
    except AttributeError:
        pass
    return formatter


class NumberEditText(vanilla.EditText):

    def __init__(self, *args, **kwargs):
        self._finalCallback = kwargs.get("callback")
        kwargs["callback"] = self._textEditCallback
        super(NumberEditText, self).__init__(*args, **kwargs)

    def _breakCycles(self):
        self._finalCallback = None
        super(NumberEditText, self)._breakCycles()

    def _get(self):
        return self._nsObject.stringValue()

    def get(self):
        v = self._get()
        if not v:
            return None
        return int(v)

    def _textEditCallback(self, sender):
        value = sender._get()
        if value != "-":
            try:
                v = int(value)
            except ValueError:
                if value.startswith("-"):
                    value = value = "-"
                else:
                    value = ""
                sender.set(value)
                return
            if self._finalCallback is not None:
                self._finalCallback(sender)
