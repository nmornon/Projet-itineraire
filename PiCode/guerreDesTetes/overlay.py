import cv2

def load_heads(size=(130,130)):
    """charge les têtes depuis le dossier heads/"""

    heads=[]

    files=["heads/tete1.png",
            "heads/tete2.png"]

    for file in files :

        img=cv2.imread(file)

        if img is None:
            print("impossible de charger : ",file)
            continue

        img=cv2.resize(img,size)

        heads.append(img)

    return heads 

    
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
