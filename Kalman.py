import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd

def normalisation_angle(angle):
    return (angle+np.pi)%(2*np.pi)-np.pi


def gps_to_xy(lat,long):
    
    R_earth=6378000
    
    lat=np.deg2rad(lat)
    lon=np.deg2rad(lon)
    
    #comment convertir les corrdonées du gps qui sotn en lat et long 
    
    
    
def f(x,u,dt):
    """
    Etat x = [x, y, theta]
    Entrée u = [v, omega]
    """
    
    v,omega=u
    
    theta=x[2,0]
    
    x_next=np.array([
        [x[0,0]+v*dt*np.cos(theta)],
        [x[1,0]+v*dt*np.sin(theta)],
        [normalisation_angle(theta+omega*dt)]
        ])
    
    return x_next

def F(x,u,dt):
    
    v,omega=u
    
    theta=x[2,0]
    
    F=np.array([
       [ 1,0,-v*dt*np.sin(theta)],
       [0,1,-v*dt*np.cos(theta)],
       [0,0,1]
       ])
    
    return F

def h(x):
    
    return np.array([
        [x[0,0]],
        [x[1,0]]
        ])

def H():
    return np.array([
        [1,0,0],
        [0,1,0]
        ])

#pour lisser 
def moving_average(x, window=5):

    y = np.zeros(len(x))

    for i in range(len(x)):

        start = max(0, i - window//2)
        end = min(len(x), i + window//2 + 1)

        y[i] = np.mean(x[start:end])

    return y


#chargement des données

data=pd.read_csv("acquisition.csv")

time=data["timestamp"].to_numpy()
lat=data["lat"].to_numpy()
long=data["lon"].to_numpy()
gz=data["gz"].to_numpy()

x_gps,y_gps=gps_to_xy(lat, long)
N=len(time)


#calcul du dt

dt_array=np.diff(time)
dt_mean=np.mena(dt_array)

print("dt moyen", dt_mean)


#estimation de la vitesse avec le GPS

dx=np.diff(x_gps)
dy=np.diff(y_gps)
dt=np.diff(time)

v_gps=np.sqrt(dx**2+dy**2)/dt

v_gps=np.insert(v_gps,0,v_gps[0]) #pour remettre à la même taille


v_lisse=moving_average(v_gps,window=5) #pour lisser la vitesse si top bruité


#estimation de R : bruit GPS

x_gps_lisse=moving_average(x_gps,window=10)
y_gps_lisse=moving_average(y_gps,window=10)

erreur_x_gps=x_gps-x_gps_lisse
erreur_y_gps=x_gps-y_gps_lisse

sigma_gps_x2=np.var(erreur_x_gps)
sigma_gps_y2=np.var(erreur_y_gps)
sigma_gps_xy=np.var(erreur_x_gps,erreur_y_gps)[0,1]

R=np.array([
    [sigma_gps_x2,sigma_gps_xy],
    [sigma_gps_xy,sigma_gps_y2]
    ])

print("R GPS=",R)

#estimation de Q : bruit sur v et omega

erreur_v=v_gps-v_lisse
sigma_v2=np.var(erreur_v)

gz_lisse = moving_average(gz, window=10)
erreur_omega = gz - gz_lisse
sigma_omega2 = np.var(erreur_omega)


Q = np.array([
    [sigma_v2, 0.0],
    [0.0, sigma_omega2]
    ])

print("Q : ",Q)

#inialisation EKF

x=np.array([
    [x_gps[0]],
    [y_gps[0]],
    [0]
    ])


P=np.diag([1,2,3]) #incertitude initiale sur x y et theta

x_filt = np.zeros((N, 3))
innovation_hist = np.zeros((N, 2))

H = H()
I = np.eye(3)

#Boucle EKF

for k in range(N):
    
    if k==0:
        dt_k=dt_mean
    else:
        dt_k=time[k]-time[k-1]
        
    u=np.array([
        v_lisse[k],
        gz[k]
        ])
    
    x_pred=f(x,u,dt_k)
    
    F=F(x,u,dt_k)
    
    theta=x[2,0]
    
    Gamma = np.array([
        [dt_k * np.cos(theta), 0.0],
        [dt_k * np.sin(theta), 0.0],
        [0.0,                  dt_k]
        ])
    
    Q=Gamma@Q@Gamma.T
    
    P_pred=F@P@F.T+Q
    
    #position mesurée par le GPS
    z_gps=np.array([
        [x_gps[k]],
        [y_gps[k]]
        ])
    
    #position mesurée par le modèle
    z_pred = np.array([
        [x_pred[0, 0]],
        [x_pred[1, 0]]
        ])
    
    erreur=z_gps-z_pred
    
    S=H@P_pred@H.T+R
    
    K=P_pred@H.Y@np.linalg.inv(S)
    
    x=x_pred+K@erreur
    
    x[2,0]=normalisation_angle(x[2,0])
    
    P=(I-K@H)@P_pred
    
    #sauvegarde des résultats
    x_filt[k, :] = x.ravel()
    innovation_hist[k, :] = erreur.ravel()
    
plt.plot(x_gps,y_gps,lebel="GPS brut")
plt.plot(x_gps_lisse,y_gps_lisse,label="GPS lissé")
plt.plot(x_filt[:, 0], x_filt[:, 1], label="EKF GPS + IMU")
plt.legend()
plt.xlabel("x (m)")
plt.ylabel("y (m)")
plt.title("Estimation de trajectoire")
plt.show()

plt.plot(time, innovation_hist[:,0], label="innovation x")
plt.plot(time, innovation_hist[:,1], label="innovation y")
plt.legend()
plt.xlabel("temps (s)")
plt.title("Innovation GPS")
plt.show()

plt.plot(time, v_gps, label="v GPS brute")
plt.plot(time, v_lisse, label="v lissée")
plt.xlabel("temps (s)")
plt.ylabel("v (m/s)")
plt.title("Vitesse estimée depuis le GPS")
plt.show()
    
    





