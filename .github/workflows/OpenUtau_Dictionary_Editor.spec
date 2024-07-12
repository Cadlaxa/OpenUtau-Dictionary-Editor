# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\OpenUtau-Dictionary-Editor\\OU Dictionary Editor\\OpenUtau_Dictionary_Editor.pyw'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['Assets.G2p.arpabet_plus', 'Assets.G2p.frenchG2p', 'Assets.G2p.germanG2p', 'Assets.G2p.italianG2p', 'Assets.G2p.jp_mono', 'Assets.G2p.millefeuilleG2p', 'Assets.G2p.portugueseG2p', 'Assets.G2p.russianG2p', 'Assets.G2p.spanishG2p'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OpenUtau_Dictionary_Editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\OpenUtau-Dictionary-Editor\\OU Dictionary Editor\\Assets\\icon.ico'],
)
