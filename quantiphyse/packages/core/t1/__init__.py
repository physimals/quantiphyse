from .widgets import T10Widget
from .process import T10Process
from .tests import T10WidgetTest

QP_MANIFEST = {
    "widgets" : [T10Widget],
    "widget-tests" : [T10WidgetTest,],
    "processes" : [T10Process],
}
