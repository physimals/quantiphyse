from .widgets import ClusteringWidget, MeanValuesWidget
from .kmeans import KMeansProcess, MeanValuesProcess
from .tests import ClusteringWidgetTest, KMeansProcessTest, MeanValuesProcessTest

QP_MANIFEST = {
    "widgets" : [MeanValuesWidget, ClusteringWidget],
    "widget-tests" : [ClusteringWidgetTest,],
    "process-tests" : [KMeansProcessTest, MeanValuesProcessTest],
    "processes" : [KMeansProcess, MeanValuesProcess],
}
