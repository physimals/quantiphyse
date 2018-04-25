from .widgets import OrientDataWidget, ResampleDataWidget
from .processes import ResampleProcess

QP_MANIFEST = {"widgets" : [OrientDataWidget, ResampleDataWidget],
               "processes" : [ResampleProcess]}
