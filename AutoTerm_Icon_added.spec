# -*- mode: python -*-
a = Analysis(['./AutoTerm.py'],
             pathex=[],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
#Add the file like the below example
a.datas += [('app.ico', 'app.ico', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='AutoTerm.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='app.ico')
