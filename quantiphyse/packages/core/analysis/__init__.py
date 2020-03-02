"""
Quantiphyse - Analysis widgets

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
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
