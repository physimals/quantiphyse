#from .process import SmoothingProcess
from .widget import CompareDataWidget
from .tests import CompareDataWidgetTest

QP_MANIFEST = {
    "widgets" : [CompareDataWidget,],
    "widget-tests" : [CompareDataWidgetTest],
    "processes" : []
}
