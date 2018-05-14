from .process import PcaProcess
from .widget import PcaWidget
from .tests import PcaWidgetTest
    
QP_MANIFEST = {
    "widgets" : [PcaWidget,],
    "processes" : [PcaProcess,],
    "widget-tests" : [PcaWidgetTest,],
}
