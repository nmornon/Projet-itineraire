import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng()

nb_mesures = 100_000
dt = 0.001

X_opti = np.zeros((2, nb_mesures))
X_nul = np.zeros((2, nb_mesures))

a_mes = rng.normal(0.2, 0.3, nb_mesures) # non biaisées
angles = rng.normal(5.0, 1.0, nb_mesures)
erreurs = 9.81 * np.sin(np.deg2rad(angles)) # non biaisées

for i in range(1, nb_mesures):
    X_opti[1, i] = X_opti[1, i-1] + a_mes[i-1] * dt
    X_opti[0, i] = X_opti[0, i-1] + X_opti[1, i-1] * dt + a_mes[i-1] * dt**2 / 2

    a_non_biaisee = a_mes[i-1] + erreurs[i-1]

    X_nul[1, i] = X_nul[1, i-1] + a_non_biaisee * dt
    X_nul[0, i] = X_nul[0, i-1] + X_nul[1, i-1] * dt + a_non_biaisee * dt**2 / 2

t = np.arange(nb_mesures) * dt

plt.figure(figsize=(10, 6))

plt.subplot(2, 2, 1)
plt.plot(t, X_opti[0], label="Position correcte")
plt.plot(t, X_nul[0], label="Position avec erreur")
plt.xlabel("Temps (s)")
plt.ylabel("Position (m)")
plt.title("Dérive de position causée par une erreur d'inclinaison")
plt.legend()
plt.grid()

plt.subplot(2, 2, 2)
plt.plot(t, X_opti[1], label="Vitesse correcte")
plt.plot(t, X_nul[1], label="Vitesse avec erreur")
plt.xlabel("Temps (s)")
plt.ylabel("Vitesse (m/s)")
plt.title("Dérive de vitesse causée par une erreur d'inclinaison")
plt.legend()
plt.grid()

plt.subplot(2, 2, 3)
plt.hist(a_mes, 30, density=True)
plt.title("Répartition des mesures")

plt.subplot(2, 2, 4)
plt.hist(angles, 30, density=True)
plt.title("Répartition des angles d'erreur")

plt.tight_layout()
plt.show()
