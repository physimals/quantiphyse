from .widgets import OrientDataWidget, ResampleDataWidget
from .processes import ResampleProcess
from .tests import ResampleDataWidgetTest

QP_MANIFEST = {
    "widgets" : [OrientDataWidget, ResampleDataWidget],
    "processes" : [ResampleProcess],
    "widget-tests" : [ResampleDataWidgetTest,],
}
