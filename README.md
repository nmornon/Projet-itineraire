# Projet Intégratif : Fusion de Capteurs (GNSS / IMU) & Réalité Augmentée

Ce dépôt contient le code source, les jeux de données et les analyses réalisés dans le cadre du **Projet Intégratif - Itinéraire**.

L'objectif principal du projet est d'exploiter les capteurs de la plateforme embarquée **ITIPhone** (Raspberry Pi 4 équipée d'un récepteur GNSS, d'une IMU, d'une caméra et d'un LiDAR) pour des applications d'estimation de mouvement, de géolocalisation et d'interaction en réalité augmentée.

## Organisation du dépôt

Le projet se divise en deux parties majeures, complétées par des dossiers de prétraitement et d'analyse statistique :

```text
.
├── kalman/
│   └── kalman_final.ipynb     # Notebook principal de fusion GNSS/IMU (Partie 1)
├── PiCode/
│   ├── guerreDesTetes/        # Code source du jeu en Réalité Augmentée (Partie 2)
│   └── ...                    # Scripts d'acquisition et enregistrements bruts
├── postprocessing/            # Scripts de nettoyage, lissage et synchronisation des données
└── stat/                      # Évaluations statistiques, calibration des biais et tests
```

---

## Partie 1 : Estimation de trajectoire par fusion GNSS / IMU

La première partie vise à reconstruire précisément la trajectoire 2D d'un utilisateur piéton en combinant la position absolue GNSS et l'accélérométrie/gyrométrie haute fréquence de l'IMU.

### Pipeline de traitement
1. **Nettoyage des données GNSS** :
   * **Détection des points aberrants isolés** : Filtrage basé sur la cohérence de distance entre points voisins successifs.
   * **Cohérence spatiale globale** : Filtrage par rapport au centre moyen de la zone d'acquisition pour éliminer les sauts consécutifs prolongés.
2. **Lissage géométrique** : Application d'un filtre de **Savitzky-Golay** sur les positions cartésiennes locales afin de réduire l'oscillation haute fréquence tout en préservant la géométrie des virages.
3. **Changement de repère** : Conversion des coordonnées sphériques $(\text{latitude}, \text{longitude})$ vers un repère cartésien local en mètres $(x, y)$ centré sur le premier point GNSS.
4. **Calibration IMU & Initialisation** :
   * Estimation des biais statiques en accélération $(b_{a,x}, b_{a,y})$ et en vitesse angulaire $(b_{g,z})$ sur des séries d'acquisitions immobiles.
   * Estimation du cap initial $\theta_0$ via le magnétomètre : $\theta_0 = \arctan2(m_y, m_x)$.
5. **Filtre de Kalman Étendu (EKF)** :
   * **Vecteur d'état** : $x_k = \begin{bmatrix} x_k & y_k & v_{x,k} & v_{y,k} & \theta_k \end{bmatrix}^T$.
   * **Prédiction** : Intégration cinématique des accélérations IMU projetées dans le repère monde.
   * **Correction dynamiquement pondérée par le HDOP** : La covariance de mesure $R_k$ s'ajuste dynamiquement selon la qualité du signal GNSS :
     $$R_k = R_{\text{base}} \times 40 \times \text{HDOP}_k^2$$
6. **Évaluation expérimentale** : Comparaison des trajectoires reconstruites avec une trace de référence **Strava** (calcul de l'erreur moyenne, RMSE et erreur maximale).

###  Exécution du Notebook EKF
1. Ouvrir le notebook : `kalman/kalman_final.ipynb`.
2. Suivre les instructions dans les cellules.
3. Renseigner les chemins d'accès aux fichiers demandés :
   * Fichier d'acquisition synchronisée (`.csv`).
   * Fichier GPX de référence exporté depuis **Strava**.
4. Les visualisations (cartes, trajectoires comparées, métriques) seront générées automatiquement.

---

## Partie 2 : Jeu en Réalité Augmentée — *La Guerre des Têtes*

Situé dans `PiCode/guerreDesTetes/`, cette partie développe un jeu interactif inspiré de *La Guerre des Têtes* (Nintendo 3DS) exploitant la caméra, l'IMU et le LiDAR en temps réel.

### Fonctionnalités & Architecture
* **Phase Photo** :
  * Capture d'un visage via la caméra.
  * Détection de visage avec **OpenCV (Classifieur Haar Cascade)** et découpe sous forme d'ovale $128 \times 128$.
* **Phase de Jeu & Projection 3D → 2D** :
  * Les ennemis sont modélisés en coordonnées polaires dans le repère monde ($\theta, r, z$).
  * **Chaîne de transformation géométrique** : Repère Monde $\rightarrow$ Repère LiDAR (orienté via gyromètre IMU) $\rightarrow$ Repère Caméra $\rightarrow$ Projection Image 2D $(u, v)$ via la matrice intrinsèque $K$ de la caméra.
  * **Suivi de tête IMU** : Les mouvements de rotation du joueur mettent à jour la matrice d'orientation en temps réel, maintenant la cohérence spatiale des ennemis virtuels dans le flux vidéo.
* **Minimap LiDAR** :
  * Ajout d'une mini-carte en haut à droite de l'écran affichant le nuage de points du LiDAR (obstacles environnants), la position du joueur, le cône de vision et la position relative des ennemis.
* **Streaming sans fil (Flask MJPEG)** :
  * Diffusion du flux vidéo de jeu en temps réel via un serveur web léger Flask (`multipart/x-mixed-replace`), permettant de jouer depuis n'importe quel navigateur mobile sans câble HDMI.

---

## Stack technique & Dépendances

* **Langage principal** : Python 
* **Traitement de données & Calcul** : `numpy`, `pandas`, `scipy`
* **Vision par ordinateur & Rendu** : `opencv-python` (`cv2`), `libcamera`
* **Streaming & Web** : `Flask`
* **Analyse & Visualisation** : `matplotlib`, `Jupyter Notebook`

---

---

## Équipe de projet

* **Adam EL MARZOUKI**
* **Axel LÊ TRONG**
* **Roger-Parfait MBAITORNDIA**
* **Noémie MORNON**
* **Théo SAVARY**

---


