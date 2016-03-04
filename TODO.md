

TODO
====

- Fix PK modelling cmd line script (done)
- Add T10 calculation command line script (done)
- Add CNR restriction option to PK modelling
- Add smoothing for the maps
- Update documentation and links from help buttons
- add tests for pkmodelling and T10 mapping
- use TravisCI to build for ubuntu and osx
- ...
- Profit?

- Just use as a viewer for supervoxels. Possibly add script later on

# idea:

- Use this viewer to view subregions in my bag of words approach
- release this viewer with that paper
- possibly also show subregions for these words and pk maps of the subregions for effect


# windows exe issues

- disable T10 mapping on windows because uses c++11 code that's not supported with python 2.7
                - use python 3.5 once pyside (pyside 2) has support for this. 
- downgraded setuptools to 19.2 on windows
- manually copy mkl files from 
C:\Users\engs1170\AppData\Local\Continuum\Anaconda2\Library\bin
- add multiprocessing.freeze_support()
- added .bat file to run more easily
