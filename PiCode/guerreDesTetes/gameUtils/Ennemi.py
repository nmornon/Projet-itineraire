#Classes des ennemis
class Ennemi:
    def __init__(self, nom, angle, profondeur, z):
        self.sprite = None
        self.angle = angle
        self.profondeur = profondeur
        self.z = z
    
    def setSprite(self, sprite):
        self.sprite = sprite    