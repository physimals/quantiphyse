from .process import SmoothingProcess
from .widget import SmoothingWidget
from .tests import SmoothingWidgetTests

QP_MANIFEST = {
    "widgets" : [SmoothingWidget,],
    "widget-tests" : [SmoothingWidgetTests,],
    "processes" : [SmoothingProcess,]
}
