# BlueFrontline

BlueFrontline est un projet de jeu/application en Python avec interface graphique, exportable en exécutable, accompagné d’une documentation générée avec MkDocs.

---

## Acteurs du projet

- **les membres du groupe sont** : 
  - Romain SIAME  
  - Thomas CHAMPY
  - Hippolyte LE PALLEC
  - Keylian TURBE
  - Antoine ARNOULT
  - Samy BERGHOL 

---

## Fonctionnalités

- Interface graphique (jeu / application interactive)  
- Gestion de la logique métier et des événements  
- Export en exécutable (via **PyInstaller** ou **auto-py-to-exe**)  
- Documentation avec **MkDocs**  
- Intégration continue via **GitHub Actions**  
- Fichiers de configuration pour Read the Docs et la génération d’exécutables  

---

## Structure du projet

```py
.
├── .github/              # Workflows GitHub Actions
├── .vscode/              # Configurations VSCode
├── blue_frontline/       # Code source principal
├── docs/                 # Documentation MkDocs
├── .gitignore
├── .readthedocs.yaml     # Config Read the Docs
├── BlueFrontline.spec    # Script de build (PyInstaller)
├── mkdocs.yml            # Config MkDocs
├── requirements.txt      # Dépendances utilisateur
├── requirements-dev.txt  # Dépendances de développement
└── README.md
```
---

## Prérequis

- Python **3.8+**  
- `pip`  
- (Optionnel) `auto-py-to-exe` ou `pyinstaller` pour générer des exécutables  
- (Optionnel) `mkdocs` pour la documentation  

---

## Installation & Lancement

Cloner le dépôt et installer les dépendances :

```bash
git clone https://github.com/keylian15/blue_frontline.git
cd blue_frontline
pip install -r requirements.txt
```

Lancer le projet en développement :

```bash
cd blue_frontline
python main.py
```

## Générer un exécutable

Avec auto-py-to-exe :

```bash
pip install auto-py-to-exe
auto-py-to-exe
```


Avec PyInstaller et le fichier .spec fourni :

```bash
pyinstaller --onefile --windowed BlueFrontline.spec
```

## Documentation

La documentation est générée avec MkDocs.
Pour la visualiser en local :

```bash
pip install mkdocs
mkdocs serve
```


Ensuite, ouvrir http://127.0.0.1:8000 dans ton navigateur.