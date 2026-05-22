import numpy as np

def imu_to_enu(x, y, z, roulis, tangage, lacet):
    vec = np.array([x, y, z])
    R_roulis = np.array([[1, 0, 0],
                         [0, np.cos(roulis), -np.sin(roulis)],
                         [0, np.sin(roulis), np.cos(roulis)]])
    R_tangage = np.array([[np.cos(tangage), 0, np.sin(tangage)],
                          [0, 1, 0],
                          [-np.sin(tangage), 0, np.cos(tangage)]])
    R_lacet = np.array([[np.cos(lacet), -np.sin(lacet), 0],
                        [np.sin(lacet), np.cos(lacet), 0],
                        [0, 0, 1]])
    return R_roulis @ R_tangage @ R_lacet @ vec

def calibration_multi_immobile(gnss_files, imu_files, mag_files):
    imu = pd.read_csv(imu_file)
    gnss = pd.read_csv(gnss_file)
    mag = pd.read_csv(mag_file)

    # Calcul des moyennes globales des biais
    biais = {
            "accel_x": imu["accel_x"].mean(),
            "accel_y": imu["accel_y"].mean(),
            "accel_z": imu["accel_z"].mean(),
            "gyro_x": imu["gyro_x"].mean(),
            "gyro_y": imu["gyro_y"].mean(),
            "gyro_z": imu["gyro_z"].mean(),
            "magnet_x": imu["magnet_x"].mean(),
            "magnet_y": imu["magnet_y"].mean(),
            "magnet_z": imu["magnet_z"].mean(),
            }

    # Calcul du dt moyen sur le premier fichier IMU pour dimensionner Q
    dt_moyen = np.diff(pd.read_csv(imu_files[0])["timestamp"]).mean()

    var_accel = max(np.mean(var_ax), np.mean(var_ay))
    var_gyro = np.mean(var_gz)

    # Construction de la matrice Q
    Q = np.diag([
            0.05,
            0.05,
            var_accel * dt_moyen**2,
            var_accel * dt_moyen**2,
            var_gyro * dt_moyen**2])
    

    # Matrice R_gps basée sur l'immobilité (sécurité minimale à 2.5m de sigma)
    R_gps = np.diag([
        np.mean(var_gps_x),
        np.mean(var_gps_y)])

    # Matrice R_mag pour le cap du magnétomètre
    R_mag = np.array([[np.radians(25.0) ** 2]])

    print("Résultats de la Calibration Multi-Immobile")
    print(f"Biais accel_x : {biais['accel_x']:.4f}")
    print(f"Biais accel_y : {biais['accel_y']:.4f}")
    print(f"Biais gyro_z deg/s : {np.degrees(biais['gyro_z']):.4f}")
    print(f"R_gps sigma x/y : {np.sqrt(R_gps[0,0]):.2f} m, {np.sqrt(R_gps[1,1]):.2f} m")
    print(f"R_mag sigma deg : {np.degrees(np.sqrt(R_mag[0,0])):.2f}°")

    return Q, R_gps, biais, caps_initiaux

def remove_gnss_aberrant(df,lat_col="latitude",lon_col="longitude",seuil_grand=30,seuil_petit=10):
    """Supprime les points GNSS aberrants"""
    
    df=df.copy()
    #shift(1) point précédent 
    #shift(-1) point suivant
    
    df = df[(df[lat_col].between(-90, 90)) & (df[lon_col].between(-180, 180))]
    
    #Calcul de la distance entre le point préédent et le point courant
    df["d_prev"]=haversine(df[lat_col].shift(1),
                          df[lon_col].shift(1),
                          df[lat_col],
                          df[lon_col])
    
    #Calcul de la distance entre le point courant et le point suivant
    df["d_next"]=haversine(df[lat_col],
                          df[lon_col],
                          df[lat_col].shift(-1),
                          df[lon_col].shift(-1))
    
    #Calcul de la distance entre le point préédent et le point suivant
    df["d_skip"]=haversine(df[lat_col].shift(1),
                          df[lon_col].shift(1),
                          df[lat_col].shift(-1),
                          df[lon_col].shift(-1))
    
    #on ajoute une colonne pour savoir si le point courant est abberant ou non 
    df["est_aberrant"] = (
        (df["d_prev"] > seuil_grand)
        & (df["d_next"] > seuil_grand)
        & (df["d_skip"] < seuil_petit)
    )
    
    print("Nombre de points total :", len(df))
    print("Nombre de points aberrants détectés :", df["est_aberrant"].sum())
    
    return df[df["est_aberrant"]==False].copy()

def ekf_gnss_imu(df, Q, R_gps, biais, cap_mag_init):
    # Recuperation des données à partir de la base de donnée
    df = df.sort_values("timestamp").copy()
    temps = df["timestamp"].to_numpy()

    longitudes = df["longitude"].to_numpy()
    latitudes = df["latitude"].to_numpy()

    a_x = df["accel_x"].to_numpy()
    a_y = df["accel_y"].to_numpy()
    a_z = df["accel_z"].to_numpy()

    w_x = np.radians(df["gyro_x"].to_numpy())
    w_y = np.radians(df["gyro_y"].to_numpy())
    w_z = np.radians(df["gyro_z"].to_numpy())

    m_x = df["magneto_x"].to_numpy()
    m_y = df["magneto_y"].to_numpy()
    m_z = df["magneto_z"].to_numpy()

    dt = np.diff(temps, prepend=temps[0])

    # État initial
    roulis_0 = np.arcsin(a)
    a_longitudes = imu_to_enu(a_x, a_y, a_z, )
    etat = np.array([gps_x[0], gps_y[0], 0.0, vy_init, cap_mag_init])
    P    = np.diag([R_gps_base[0, 0], R_gps_base[1, 1], 1.0, 1.0, 1.0])


    etats_sauvegardes = []

    for k in range(len(df)):
        position_x = etat[0]
        position_y = etat[1]
        vitesse_x = etat[2]
        vitesse_y = etat[3]
        theta = etat[4]
        dtk = dt[k]

        # Rotation plaque ->monde
        R_rot = Rotation.from_euler('z', theta)
        accel_x_tel_corr = accel_x_tel[k] - biais["accel_x"]
        accel_y_tel_corr = accel_y_tel[k] - biais["accel_y"]
        gyro_z_corr = gyro_z[k] - biais["gyro_z"]
        
        accel_monde = R_rot.apply([accel_x_tel_corr, accel_y_tel_corr, accel_z_tel[k]])
        
        #accélération mesurée dans le repère téléphone vers le répère monde
        accel_x = accel_monde[0]
        accel_y = accel_monde[1]
        
        #ici je suppose que la  vitesse est la même entre deux mesures GPS
        #accel_x = 0
        #accel_y = 0

        # 1. PRÉDICTION
        etat_predit = etat.copy()
        etat_predit[0] = position_x + vitesse_x * dtk + 0.5 * accel_x * dtk**2
        etat_predit[1] = position_y + vitesse_y * dtk + 0.5 * accel_y * dtk**2
        etat_predit[2] = vitesse_x + accel_x * dtk
        etat_predit[3] = vitesse_y + accel_y * dtk
        
        etat_predit[4] = theta + gyro_z_corr * dtk
        etat_predit[4] = remettre_angle_entre_moins_pi_et_pi(etat_predit[4])
        
        # matrice F
        F = np.eye(5)
        F[0, 2] = dtk  # x dépend de vx
        F[1, 3] = dtk  # y dépend de vy

        P_predit = F @ P @ F.T + Q 

        # corrcetion gps
        mesure_gps = np.array([gps_x[k], gps_y[k]])
        erreur_gps = mesure_gps - H_gps @ etat_predit

        # on ajuste R_gps
        R_gps_dynamique = R_gps_base * (hdops[k] ** 2)

        S = H_gps @ P_predit @ H_gps.T + R_gps_dynamique
        K = P_predit @ H_gps.T @ np.linalg.inv(S)

        etat_predit = etat_predit + K @ erreur_gps
        P_predit = (np.eye(5) - K @ H_gps) @ P_predit

        # enregistrement
        etat = etat_predit
        P = P_predit
        etats_sauvegardes.append(etat.copy())

    etats_sauvegardes = np.asarray(etats_sauvegardes)
    sortie = df.copy()
    
    lat_kalman, lon_kalman = xy_to_latlon(etats_sauvegardes[:, 0], etats_sauvegardes[:, 1], lat0, lon0)
    sortie["latitude"] = lat_kalman
    sortie["longitude"] = lon_kalman

    return sortie