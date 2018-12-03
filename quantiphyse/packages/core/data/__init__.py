from .widgets import OrientDataWidget, ResampleDataWidget
from .processes import ResampleProcess
from .tests import ResampleDataWidgetTest, ResampleProcessTest

QP_MANIFEST = {
    "widgets" : [OrientDataWidget, ResampleDataWidget],
    "processes" : [ResampleProcess],
    "widget-tests" : [ResampleDataWidgetTest,],
    "process-tests" : [ResampleProcessTest,],
}
