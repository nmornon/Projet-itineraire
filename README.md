# Projet GNSS / IMU - Fusion de données

## Organisation du dépôt

Le dépôt est organisé en deux parties principales :

### PiCode

Le dossier `PiCode` contient l'ensemble des scripts développés pour les parties 1 et 2 du projet :
Les acquisitions réalisées sont également stockées dans ce dossier.

### La guerre des têtes

Le jeu est disponible dans le dossier `PiCode/guerreDesTetes`

### Kalman

Le dossier `kalman` contient l'ensemble du travail réalisé pour la fusion GNSS/IMU.

Le notebook principal est :

```text
kalman/kalman_final.ipynb
```

Ce notebook permet :

* de charger les acquisitions synchronisées ;
* d'appliquer le filtre de Kalman étendu ;
* de comparer les résultats obtenus avec différentes méthodes de traitement ;
* de comparer la trajectoire estimée à une référence Strava ;
* de réaliser les différentes analyses présentées dans le rapport.

## Utilisation du notebook

Pour exécuter le notebook :

1. Ouvrir `kalman_final.ipynb`.
2. Suivre les indications présentes dans les cellules de code.
3. Lorsque cela est demandé, renseigner les chemins vers :

   * le fichier d'acquisition synchronisée 
   * le fichier GPX exporté depuis Strava

Le notebook indique directement à quels endroits ces fichiers doivent être fournis.

## Résultats

Les résultats générés (trajectoires, cartes, comparaisons et figures) sont créés automatiquement lors de l'exécution du notebook.

## Autres dossiers 
Les dossiers postprocessing et stat conservent également une trace des différentes étapes de traitement et des analyses réalisées au cours du projet. Ils regroupent les scripts utilisés pour le nettoyage des données, la synchronisation, les études statistiques ainsi que les expérimentations menées.


