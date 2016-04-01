# -*- mode: python -*-

block_cipher = None

added_files = [('pkview/icons', 'icons'), ('pkview/resources', 'resources')]
bin_files = [ ( 'C:\\Users\\engs1170\\AppData\\Local\\Continuum\\Anaconda2\\Library\\bin\\mkl_avx.dll', 'dlls' ),
              ('C:\\Users\\engs1170\\AppData\\Local\\Continuum\\Anaconda2\\Library\\bin\\mkl_def.dll', 'dlls' )]



a = Analysis(['pkviewer2.py'],
             pathex=['C:\\Users\\engs1170\\Documents\\PkView'],
             binaries=bin_files,
             datas=added_files,
             hiddenimports=[],
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='pkviewer2',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon='C:\\Users\\engs1170\\Documents\\PkView\\pkview\\icons\\main_icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='pkviewer2')
