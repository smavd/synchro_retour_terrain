# synchro_retour_terrain
Plugin Qgis permettant la synchronisation des données Qgis au retour terrain. 
Ce plugin automatise l'ajout et la mise à jour d'entités depuis une couche source (la donnée terrain) vers une couche cible (la base de donnée). Dans sa version actuelle il ne gère pas la suppression de données. 

-----------------

# Formats gérés : 
Shapefile ; geopackage

-----------------
# Pré-requis : 

- Version Qgis : 3.28 to 3.40
- Système d'exploitation : Windows (les autres n'ont pas été testé)

-----------------

# Installation : 
- téléhcrager le zip synchro_retour_terrain.zip
- dans Qgis > Menu Extensions > Installer / Gérer des extensions > Installer depuis un zip > Choisir le zip du plugin et l'installer

-----------------

# Fonctionnement : 
- La couche source et la couche cible doivent avoir une même structure attributraire.  
- La couche doit avoir un identifiant unique (IDU par défaut). Le plugin vérifie la présence et l'unicité de cet identifiant dans les deux couches.
  * Il est conseillé d'utiliser un identifiant généré automatiquement de façon aléatoire, par exemple avec la fonction uuid() de Qgis. Les identifiants incrémentés de type SERIAL sont à proscrire en cas de contributeurs mutliples.

- Une option permet d'appliquer les modifications sur une entité uniquement si un champ "date de mise à jour" (date_maj par défaut) est plus récent dans la couche source que dans la couche cible. L'objctif est d'éviter qu'un contributeur écrase les données chargées par un autre contributeur. 
  * Il est conseillé d'utiliser un champ date_maj de type DateTime et mis à jour automatiquement dans le formulaire de la couche terrain. 

-----------------

# Changelog :
- V 0.1
    Version initiale
- V1.0 16/12/2025
    Ajout de la gestion de suppression d'entités. 
    Renforcement du code - correction de bugs mineurs. 
- V1.1 20/02/2026
    Correction bug lors de la MAJ des entités. 
----------------

# To do list : 
- Ajout de nouveaux formats : PostGis ...
- Gérer lorsque la couche cible comporte des champs que la couche source n'a pas (cas d'usage : départ sur le terrain avec une couche alléegée)
- ...

Toute nouvelle contribution pour améliorer le plugin est la bienvenue. 
