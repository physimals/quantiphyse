from .widgets import SECurve, DataStatistics, RoiAnalysisWidget, SimpleMathsWidget, ModelCurves
from .processes import CalcVolumesProcess, ExecProcess, DataStatisticsProcess, RadialProfileProcess, HistogramProcess
from .tests import DataStatisticsTest

QP_MANIFEST = {
    "widgets" : [SECurve, DataStatistics, RoiAnalysisWidget, SimpleMathsWidget, ModelCurves],
    "widget-tests" : [DataStatisticsTest,],
    "processes" : [CalcVolumesProcess, ExecProcess, DataStatisticsProcess, RadialProfileProcess, HistogramProcess],
}
