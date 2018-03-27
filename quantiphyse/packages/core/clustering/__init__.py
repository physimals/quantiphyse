from .widgets import ClusteringWidget
from .kmeans import KMeans3DProcess, KMeansPCAProcess
from .tests import ClusteringWidgetTest

QP_MANIFEST = {
    "widgets" : [ClusteringWidget],
    "widget-tests" : [ClusteringWidgetTest,],
    "processes" : [KMeans3DProcess, KMeansPCAProcess],
}
