# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/keyli/Documents/IUT/blue_frontline/blue_frontline/main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/keyli/Documents/IUT/blue_frontline/blue_frontline/assets', 'assets/'), ('C:/Users/keyli/Documents/IUT/blue_frontline/blue_frontline/blue_frontline_sounds', 'blue_frontline_sounds/'), ('C:/Users/keyli/Documents/IUT/blue_frontline/blue_frontline/map.tmx', '.')],
    hiddenimports=['pygame', 'pytmx', 'pyscroll', 'perlin_noise', 'shapely', 'shapely.geometry'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['mkdocs', 'mkdocs_material', 'mkdocstrings', 'pytest', 'numpy', 'matplotlib'],
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
    name='BlueFrontline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
