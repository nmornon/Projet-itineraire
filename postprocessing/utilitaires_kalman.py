import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

np.random.seed(0)

def wrap_angle(a):
    return (a + np.pi) % (2*np.pi) - np.pi

def rmse(a, b):
    a = np.asarray(a).ravel(); b = np.asarray(b).ravel()
    return np.sqrt(np.mean((a-b)**2))

# ==============================
# Outils : ellipse de confiance
# ==============================
def confidence_ellipse(ax, x, y, level=0.95, **kwargs):
    """
    Trace une ellipse de confiance (gaussienne) basée sur la covariance de (x,y).
    level=0.95 -> ~ 95% (si (x,y) est ~ gaussien).
    """
    x = np.asarray(x).ravel()
    y = np.asarray(y).ravel()

    # Centrage
    x0 = x.mean()
    y0 = y.mean()
    X = np.vstack([x - x0, y - y0])

    # Covariance (population) : moyenne des produits centrés
    G = (X @ X.T) / X.shape[1]  # 2x2

    # Valeurs propres / vecteurs propres
    vals, vecs = np.linalg.eigh(G)
    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]

    # Angle de l'axe principal
    angle = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))

    # Facteur chi2 à 2 ddl (valeurs usuelles, sans SciPy)
    # 90%: 4.605, 95%: 5.991, 99%: 9.210
    chi2_2d = {0.90: 4.605, 0.95: 5.991, 0.99: 9.210}
    if level not in chi2_2d:
        raise ValueError("Choisir level parmi {0.90, 0.95, 0.99} (sans SciPy).")

    k2 = chi2_2d[level]

    # Demi-axes de l'ellipse
    width  = 2 * np.sqrt(k2 * vals[0])
    height = 2 * np.sqrt(k2 * vals[1])

    ell = Ellipse((x0, y0), width=width, height=height, angle=angle, fill=False, **kwargs)
    ax.add_patch(ell)
    return G
