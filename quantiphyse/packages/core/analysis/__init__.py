"""
Quantiphyse - Analysis widgets

Copyright (c) 2013-2018 University of Oxford
"""
from .widgets import MultiVoxelAnalysis, DataStatistics, RoiAnalysisWidget, SimpleMathsWidget, VoxelAnalysis, MeasureWidget
from .processes import CalcVolumesProcess, ExecProcess, DataStatisticsProcess
from .tests import DataStatisticsTest, MultiVoxelAnalysisTest, VoxelAnalysisTest
from .process_tests import AnalysisProcessTest

QP_MANIFEST = {
    "widgets" : [MultiVoxelAnalysis, DataStatistics, RoiAnalysisWidget, SimpleMathsWidget, VoxelAnalysis, MeasureWidget],
    "widget-tests" : [DataStatisticsTest, MultiVoxelAnalysisTest, VoxelAnalysisTest],
    "process-tests" : [AnalysisProcessTest],
    "processes" : [CalcVolumesProcess, ExecProcess, DataStatisticsProcess],
}
