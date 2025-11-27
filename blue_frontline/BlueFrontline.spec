# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('sounds', 'sounds'),
        ('src/utils/map.tmx', 'src/utils'),
        ('data', 'data'),
    ],
    hiddenimports=[
        # Bibliothèques externes
        'pygame',
        'pytmx',
        'pytmx.util_pygame',
        'pytmx.TiledObjectGroup',
        'pytmx.TiledObject',
        'pyscroll',
        'perlin_noise',
        'numpy',
        'numpy._core',
        'numpy._core.multiarray',
        'shapely',
        'shapely.geometry',
        
        # Modules src
        'src',
        'src.config',
        'src.core',
        'src.menus',
        'src.sound',
        'src.system',
        'src.tutorial',
        'src.units',
        'src.units.IA',
        'src.utils',
        
        # Config
        'src.config.audio',
        'src.config.controls_manager',
        'src.config.game_constants',
        'src.config.mapping',
        'src.config.paths',
        'src.config.settings_manager',
        'src.config.units',
        'src.config.visuals',
        
        # Core
        'src.core.Camera',
        'src.core.ExplosionRenderer',
        'src.core.Game',
        'src.core.GameInitializer',
        'src.core.GameUpdater',
        'src.core.Renderer',
        'src.core.Timer',
        
        # Menus
        'src.menus.AchievementsMenu',
        'src.menus.CreditsMenu',
        'src.menus.Menu',
        'src.menus.OptionsMenu',
        'src.menus.OverlayMenu',
        
        # Sound
        'src.sound.Sound',
        'src.sound.SoundAPI',
        
        # System
        'src.system.AchievementsNotification',
        'src.system.AchievementsSystem',
        'src.system.AchievementsSystemRouge',
        'src.system.AchievementsSystemVert',
        'src.system.Combat',
        'src.system.EventHandler',
        'src.system.Hud',
        'src.system.Perlin',
        'src.system.Petrole',
        'src.system.Piece',
        
        # Tutorial
        'src.tutorial.TutorialManager',
        
        # Units
        'src.units.Bateau',
        'src.units.Chaloupe',
        'src.units.Eclaireur',
        'src.units.Paquebot',
        'src.units.PlateformePetroliere',
        'src.units.PompePetroliere',
        'src.units.Sousmarin',
        'src.units.Unit',
        
        # IA
        'src.units.IA.ChaloupeAI',
        'src.units.IA.ChaloupeQLearning',
        'src.units.IA.IA_Eclaireur',
        'src.units.IA.PathfindingLogic',
        
        # Utils
        'src.utils.Utils',
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
        'PIL',
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
    # icon='assets/icon.ico',  # Décommentez si vous avez une icône
)