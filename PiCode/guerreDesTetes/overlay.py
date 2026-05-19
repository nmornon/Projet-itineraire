import cv2
import os
import numpy as np

def load_heads(size=(130,130), path="guerreDesTetes/selfies/"):
    """charge les têtes depuis le dossier heads/"""

    heads=[]

    files = [f for f in os.listdir(path) if f.endswith(".jpg") and f.startswith("sprite")]

    for file in files :

        img=cv2.imread(os.path.join(path, file))

        if img is None:
            print("impossible de charger : ",file)
            continue

        img=cv2.resize(img,size)

        heads.append(img)

    return heads 

def overlay_png_opacite(frame: np.ndarray, png: np.ndarray, x: int, y: int) -> np.ndarray:
    h, w = png.shape[:2]
    x = x - w // 2
    y = y - h // 2

    bgr = png[:, :, :3].astype(float)
    alpha = png[:, :, 3].astype(float) / 255.0

    roi = frame[y : y + h, x : x + w].astype(float)
    for c in range(3):
        roi[:, :, c] = (alpha * bgr[:, :, c] + (1.0 - alpha) * roi[:, :, c])
    frame[y : y + h, x : x + w] = roi.astype(np.uint8)
    return frame

def overlay_png(frame,png,x,y):
    """ajoute une image PNG sur une frame OpenCV
    
        frame : image de la caméra 
        png : Image 
        x,y : position du centre de la tête sur l'écran (ou on veut l'afficher)"""

    hauteur,largeur=png.shape[:2]

    #calcul des coordonnées de la zone d'affichage 

    x1=int(x-largeur/2)
    y1=int(y-hauteur/2)

    x2=x1+largeur
    y2=y1+hauteur

    #si la tête dépasse on ne l'affiche pas 
    if x1<0 or y1<0 or x2>frame.shape[1] or y2>frame.shape[0]:
        return frame 

    frame[y1:y2,x1:x2]=png

    return frame 

def viseur(frame):
    """pour dessiner une croix à l'écran en  mode viseur"""

    hauteur,largeur=frame.shape[:2]

    #centre de l'écran 
    cx=largeur//2
    cy=hauteur//2

    #ligne horizontale
    cv2.line(frame,(cx-20,cy),(cx+20,cy),(0,255,0),2)

    #ligne verticale
    cv2.line(frame,(cx,cy-20),(cx,cy+20),(0,255,0),2) 

    #cercle
    cv2.circle(frame,(cx,cy),8,(0,255,0),2)

    return frame
