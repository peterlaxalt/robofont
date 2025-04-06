from __future__ import absolute_import

from .implementation import Implementation


class MetricsMachineImplementation(Implementation):

    owner = "metricsMachine"


class MetricsMachineError(Exception):
    pass
