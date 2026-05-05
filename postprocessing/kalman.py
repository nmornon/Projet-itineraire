import numpy as np
import matplotlib.pyplot as plt

F = np.array([[1.0, dt],
              [0.0, 1.0]])
H = np.array([[1.0, 0.0]])

'''
q = 1e-6
Q = q * np.eye(2)
'''
sigma_a = 0.8
Q = (sigma_a**2) * np.array([[dt**4/4, dt**3/2],
                             [dt**3/2, dt**2]])

R = sigma_y**2

x = np.array([[0.0],
              [0.0]])
P = np.diag([20.0, 5.0])

x_filt = np.zeros((N, 2))
r_hist = np.zeros(N)
P_hist = np.zeros((N, 2, 2))

for k in range(N):
    # --- PREDICTION ---
    x_pred = F @ x
    P_pred = F @ P @ F.T + Q

    # --- INNOVATION ---
    y_pred = H @ x_pred
    rk = y[k] - float(y_pred)
    S = float(H @ P_pred @ H.T + R)

    # --- GAIN + UPDATE ---
    K = (P_pred @ H.T) / S
    x = x_pred + K * rk
    P = (np.eye(2) - K @ H) @ P_pred

    x_filt[k, :] = x.ravel() # On stocke l’état estimé à l’instant k dans la ligne k de x_filt.
    r_hist[k] = rk
    P_hist[k, :, :] = P

    
P_diag = np.diagonal(P_hist, axis1=1, axis2=2)  # (N,2)
sigma_p = np.sqrt(P_diag[:, 0])
sigma_v = np.sqrt(P_diag[:, 1])


print("RMSE mesure (p) :", rmse(y, p_true))
print("RMSE KF (p)     :", rmse(x_filt[:,0], p_true))


# Plots
plt.figure(figsize=(10,4))
plt.plot(t, p_true, label="p vrai")
plt.plot(t, y, '.', alpha=0.25, label="mesure")
plt.plot(t, x_filt[:,0], linewidth=2, label="KF p")
plt.grid(True); plt.legend(); plt.xlabel("t"); plt.show()

plt.figure(figsize=(10,3))
plt.plot(t, r_hist, label="innovation r_k")
plt.axhline(0.0)
plt.grid(True); plt.legend(); plt.xlabel("t"); plt.show()

plt.figure()
plt.plot(sigma_p, label="sigma_p = sqrt(P11)")
plt.plot(sigma_v, label="sigma_v = sqrt(P22)")
plt.xlabel("k")
plt.ylabel("écart-type")
plt.title("Évolution de l'incertitude (écarts-types)")
plt.legend()
plt.show()
