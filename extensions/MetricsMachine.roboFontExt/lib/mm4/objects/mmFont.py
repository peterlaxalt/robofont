from __future__ import absolute_import

from mm4 import MetricsMachineImplementation

from mm4.objects.contextStrings import MMContextStrings

from mojo.extensions import getExtensionDefault


class MMFont(MetricsMachineImplementation):

    def init(self):
        self.contextStrings = MMContextStrings(self.super())
        defaultStrings = getExtensionDefault("com.typesupply.MM4.contextStrings")
        self.contextStrings.set(defaultStrings)

    def __del__(self):
        self.contextStrings = None
        self._storedKerning = None
        super(MMFont, self).__del__()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
