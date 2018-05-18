from .widgets import ClusteringWidget
from .kmeans import KMeansProcess
from .tests import ClusteringWidgetTest, KMeansProcessTest

QP_MANIFEST = {
    "widgets" : [ClusteringWidget],
    "widget-tests" : [ClusteringWidgetTest,],
    "process-tests" : [KMeansProcessTest,],
    "processes" : [KMeansProcess],
}
