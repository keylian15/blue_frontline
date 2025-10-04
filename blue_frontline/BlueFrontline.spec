# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('blue_frontline_sounds', 'blue_frontline_sounds'),
        ('map.tmx', '.'),
    ],
    hiddenimports=[
        # Bibliothèques externes
        'pygame',
        'pytmx',
        'pyscroll',
        'perlin_noise',
        'shapely',
        'shapely.geometry',
        'numpy',
        'numpy.core',
        
        # Modules du jeu (Class/)
        'Class.menu',
        'Class.Game',
        'Class.Combat',
        'Class.EventHandler',
        'Class.Renderer',
        'Class.InputManager',
        'Class.GameUpdater',
        'Class.GameInitializer',
        'Class.Perlin',
        'Class.Camera',
        'Class.HUD',
        'Class.Petrole',
        'Class.Piece',
        'Class.Timer',
        'Class.OptionsMenu',
        'Class.AchievementSystem',
        'Class.AchievementNotification',
        'Class.PlateformePetroliere',
        
        # Unités
        'Class.units',
        'Class.units.Unit',
        'Class.units.Bateau',
        'Class.units.Chaloupe',
        'Class.units.Eclaireur',
        'Class.units.Paquebot',
        'Class.units.Sousmarin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'mkdocs',
        'mkdocs_material',
        'mkdocstrings',
        'pytest',
        'matplotlib',
        'scipy',
        'IPython',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BlueFrontline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = pas de console, True = avec console (pour debug)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',
)