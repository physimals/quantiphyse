"""
Quantiphyse - Analysis widgets

Copyright (c) 2013-2018 University of Oxford
"""
from .widgets import MultiVoxelAnalysis, DataStatistics, RoiAnalysisWidget, SimpleMathsWidget, VoxelAnalysis, MeasureWidget
from .processes import CalcVolumesProcess, ExecProcess, DataStatisticsProcess, OverlayStatsProcess
from .tests import DataStatisticsTest, MultiVoxelAnalysisTest, VoxelAnalysisTest, MeasureWidgetTest
from .process_tests import AnalysisProcessTest

QP_MANIFEST = {
    "widgets" : [MultiVoxelAnalysis, DataStatistics, RoiAnalysisWidget, SimpleMathsWidget, VoxelAnalysis, MeasureWidget],
    "widget-tests" : [DataStatisticsTest, MultiVoxelAnalysisTest, VoxelAnalysisTest, MeasureWidgetTest],
    "process-tests" : [AnalysisProcessTest],
    "processes" : [CalcVolumesProcess, ExecProcess, OverlayStatsProcess, DataStatisticsProcess],
}
