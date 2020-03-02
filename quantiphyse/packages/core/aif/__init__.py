"""
Quantiphyse - Histogram widget

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
from .widget import AifWidget
#from .process import AifProcess
#from .process_tests import HistogramProcessTest

QP_MANIFEST = {
    "widgets" : [AifWidget],
    #"processes" : [AifProcess],
    #"process-tests" : [HistogramProcessTest],
}
