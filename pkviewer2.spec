# -*- mode: python -*-

block_cipher = None

added_files = [('pkview/icons', 'icons'), ('pkview/resources', 'resources')]

a = Analysis(['pkviewer2.py'],
             pathex=['/home/ENG/engs1170/Code/PkView'],
             binaries=None,
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
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='pkviewer2')
