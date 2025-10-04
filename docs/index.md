# Bienvenue sur Blue Frontline

Ceci est la documentation du projet **Blue Frontline**.

Dans un monde moderne bouleversé par la chute d’une météorite, l’environnement s’est transformé en un archipel d’îles quantiques. Deux grandes puissances s’affrontent pour contrôler cette zone et y mener des recherches. Votre objectif: détruire la base adverse.

- Plateformes: Windows et Linux
- Mode de jeu: 1 contre 1 (Joueur vs IA ou IA vs IA)

## Sections

- L'histoire
- Le menu
- Le jeu
- Les contrôles
- HUD
- Les unités
- Les marées et les iles quantiques

## L'histoire

La chute d’une météorite a altéré le monde et créé des **îles quantiques** changeantes. Deux puissances rivales se disputent la zone de l’impact pour y conduire des recherches. Dans ce théâtre mouvant, chaque bataille a un but clair: **détruire la base ennemie**.

## Le menu

- **Jouer**: lancer une partie 1v1 (Joueur vs IA, ou IA vs IA pour observer).
- **Succès**: consulter les succès débloqués.
- **Options**: réglages, notamment le **remapping des touches**.
- **Quitter**: fermer le jeu.

![Menu principal](images/menu.png)

![Options](images/option.png)
![Succès](images/succes.png)

## Le jeu

![Aperçu de la carte](images/map.png)

- Objectif: détruire la **base adverse**.  
![Base](images/base.png)


- La carte évolue au rythme des **marées** (toutes les 3 minutes: haute/basse), modifiant le terrain.
- Des zones sont masquées par le **brouillard**: envoyez des **éclaireurs** pour les révéler et découvrir de nouvelles îles quantiques.
![Brouillard non découvert](images/brouillard_non_decouvert.png)

**Ressources**  
![Compteurs de ressources](images/compteur_resources.png)  
- **Pétrole**: achat d’unités. Généré passivement, accélérable grace aux **pompes**.
- **Argent**: obtenu en détruisant des unités ennemies. Sert aux **améliorations**.



## Les contrôles

- **ZQSD**: se déplacer sur la carte.
- **Flèches directionnelles Gauche Droite**: choisir l’unité à poser.
- **Clic gauche**: sélectionner une unité, puis cliquer sur une destination pour la déplacer.
- **T**: tirer lorsqu’une unité ennemie est à portée.
- **V**: changer la vitesse du jeu.
- **H**: afficher/masquer l’interface.
- **J**: changer d’équipe.
- **E**: menu debug.

Remapping: possible dans le **menu Options**.

## HUD

![HUD](images/HUD.png)

1 **Timer**: temp passée depuis le debut de la partie.  
2 **Icône de marée**: état actuel (haute/basse).  
3 **menu d'unité**: permet de deployer des unités.    
4 **Compteurs de ressources**: **pétrole** et **argent** disponibles.  

## Les unités
- Sélectionner une unité dans le menu des unité a l'aide des fleches directionnels puis appuyer sur entré pour la faire apparait au prêt de votre base 
![Menu unités](images/menu_unite.png)
- Cliquez sur une unité pour la **sélectionner**, puis sur une **destination** pour la déplacer.
- Appuyez sur **T** pour tirer lorsqu’une cible est à portée.
![Menu unités](images/tir.png)

il ya plusieurs unités disponibles:

### Les chaloupes
![unite](images/chaloupe.png)  
**Description**  
Les chaloupes sont les unité de bases elle sont rapide et peu cher mais fragiles  
**Stats**  
**Coût**:20  
**PV max**:20  
**Vitesse**:80px/s  
**Portée**:2  
**Dégâts**:2  
**cadence**:1/s  
__________________________________  
### Les bateaux
![unite](images/bateaux.png)  
**Description**  
Les bateaux sont les unité moyenne elle sont plus résistante que les chaloupes tire plus mais sont légèrement plus lente et plus cher   
**Stats**  
**Coût**:60  
**PV max**:30  
**Vitesse**:70px/s  
**Portée**:6  
**Dégâts**:6  
**cadence**:1/s 
__________________________________  
### Les paquebot
![unite](images/paquebot.png)  
**Description**  
La meilleur unité disponible , elle est **très lente** mais compense sa lenteur grace a ca robustesse et ca puissance de tire accrue  
**Stats**  
**Coût**:120  
**PV max**:50  
**Vitesse**:60px/s  
**Portée**:8  
**Dégâts**:10  
**cadence**:0.8/s
__________________________________  
### Les éclaireurs
![unite](images/eclaireurs.png)  
**Description**  
Les éclaireurs ne sont pas une unité de combats ils servent principalement a découvrir les zones de brouillard sur la carte et donc de pouvoir traverser les zone d'iles quantique  
**Stats**  
**Coût**:40    
**PV max**:15    
**Vitesse**:100px/s    
**Portée**:-  
**Dégâts**:-  
**cadence**:-  
__________________________________  
### Les sous marin
![unite](images/sous_marin.png)  
**Description**    
Les sous marin sont des unité classique mais on la particularité de pouvoir déposé des mines  
**Stats**  
**Coût**:180    
**PV max**:35   
**Vitesse**:65px/s    
**Portée**:5  
**Dégâts**:18   
**cadence**:0.5/s    
__________________________________  
### Pompes
![unite](images/pompe.png)  
**Description**  
Les pompes permettent d'amélioré votre rendement de pétrole  

## Les marées et les iles quantiques

- La **marée** alterne toutes les 3 minutes entre **haute** et **basse**, changeant la topographie.
- Les **îles quantiques** se **submergent** puis **réapparaissent** différemment après chaque cycle.

![Île quantique](images/ilequantique.png)

