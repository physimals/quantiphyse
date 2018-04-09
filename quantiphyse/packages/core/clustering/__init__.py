from .widgets import ClusteringWidget
from .kmeans import KMeansProcess
from .tests import ClusteringWidgetTest

QP_MANIFEST = {
    "widgets" : [ClusteringWidget],
    "widget-tests" : [ClusteringWidgetTest,],
    "processes" : [KMeansProcess],
}
