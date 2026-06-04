import numpy as np
import pandas as pd

def imu_to_enu(roulis, tangage, lacet):
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roulis), -np.sin(roulis)],
        [0, np.sin(roulis),  np.cos(roulis)]
    ])
    Ry = np.array([
        [ np.cos(tangage), 0, np.sin(tangage)],
        [0, 1, 0],
        [-np.sin(tangage), 0, np.cos(tangage)]
    ])
    Rz = np.array([
        [np.cos(lacet), -np.sin(lacet), 0],
        [np.sin(lacet),  np.cos(lacet), 0],
        [0, 0, 1]
    ])
    return Rx @ Ry @ Rz

def calibration_multi_immobile(imu_file, gnss_file, mag_file):
    imu = pd.read_csv(imu_file)
    gnss = pd.read_csv(gnss_file)
    mag = pd.read_csv(mag_file)
    biais = {
        "accel_x": imu["accel_x"].mean(),
        "accel_y": imu["accel_y"].mean(),
        "accel_z": imu["accel_z"].mean(),

        "gyro_x": imu["gyro_x"].mean(),
        "gyro_y": imu["gyro_y"].mean(),
        "gyro_z": imu["gyro_z"].mean(),

        "gnss_longitude": gnss["longitude"].mean(),
        "gnss_latitude": gnss["latitude"].mean(),

        "mag_x": mag["mag_x"].mean(),
        "mag_y": mag["mag_y"].mean(),
        "mag_z": mag["mag_z"].mean(),
    }
    variances = {
        "accel_x": imu["accel_x"].var(),
        "accel_y": imu["accel_y"].var(),
        "accel_z": imu["accel_z"].var(),

        "gyro_x": imu["gyro_x"].var(),
        "gyro_y": imu["gyro_y"].var(),
        "gyro_z": imu["gyro_z"].var(),

        "gnss_longitude": gnss["longitude"].var(),
        "gnss_latitude": gnss["latitude"].var(),

        "mag_x": mag["mag_x"].var(),
        "mag_y": mag["mag_y"].var(),
        "mag_z": mag["mag_z"].var()
    }
    return biais, variances

def ekf_gnss_imu(df, biais, variances):
    df = df.sort_values("timestamp").copy()

    temps = df["timestamp"].to_numpy()
    dt = np.diff(temps, prepend=temps[0])

    latitude = df["latitude"].to_numpy()
    longitude = df["longitude"].to_numpy()

    ax = df["accel_x"].to_numpy()
    ay = df["accel_y"].to_numpy()
    az = df["accel_z"].to_numpy()

    wx = np.radians(df["gyro_x"].to_numpy())
    wy = np.radians(df["gyro_y"].to_numpy())
    wz = np.radians(df["gyro_z"].to_numpy())

    mx = df["mag_x"].to_numpy()
    my = df["mag_y"].to_numpy()
    mz = df["mag_z"].to_numpy()

    g = 9.81

    roulis_0 = np.arccos(biais["accel_x"] / g)
    tangage_0 = np.arcsin(biais["accel_z"] / g)
    lacet_0 = np.arctan2(biais["mag_z"], biais["mag_y"])

    R_enu = imu_to_enu(roulis_0, tangage_0, lacet_0)

    b_accel_longitude, b_accel_latitude, _ = R_enu @ np.array([biais["accel_x"], biais["accel_y"], biais["accel_z"]])
    b_gyro_lacet, b_gyro_roulis, b_gyro_tangage =  biais["gyro_x"], biais["gyro_y"], biais["gyro_z"]
    variance_accel_longitude, variance_accel_latitude, _ = R_enu @ np.array([variances["accel_x"], variances["accel_y"], variances["accel_z"]])
    variance_gyro_lacet, variance_gyro_roulis, variance_gyro_tangage = variances["gyro_x"], variances["gyro_y"], variances["gyro_z"]

    x_k = np.array([
        longitude[0],
        latitude[0],
        0.0,
        0.0,
        tangage_0,
        roulis_0,
        lacet_0,
        b_accel_longitude,
        b_accel_latitude,
        b_gyro_tangage,
        b_gyro_roulis,
        b_gyro_lacet
    ])

    P_k = np.diag([
        variances["gnss_longitude"],
        variances["gnss_latitude"],
        variance_vitesse_longitude,
        variance_vitesse_latitude,
        variance_gyro_tangage,
        variance_gyro_roulis,
        variance_gyro_lacet,
        variance_b_accel_longitude,
        variance_b_accel_latitude,
        variance_b_gyro_tangage,
        variance_b_gyro_roulis,
        variance_b_gyro_lacet
    ])

    Q_0 = np.diag([
        variance_accel_longitude,
        variance_accel_latitude,
        variance_gyro_tangage,
        variance_gyro_roulis,
        variance_gyro_lacet
    ])

    G_k = np.zeros((12, 5))

    R = np.diag([
        variances["gnss_longitude"],
        variances["gnss_latitude"],
    ])

    F_k = np.eye(12)

    H = np.array([
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ])

    historique = []

    for k in range(len(df)):
        dtk = dt[k]

        F_k[0:2, 2:4] = dtk * np.eye(2)
        F_k[0:2, 7:9] = (-dtk ** 2 / 2) * np.eye(2)
        F_k[2:4, 7:9] = -dtk * np.eye(2)
        F_k[4:7, 9:12] = -dtk * np.eye(3)

        G_k[0:2, 0:2] = (dtk ** 2 / 2) * np.eye(2)
        G_k[2:4, 0:2] = dtk * np.eye(2)
        G_k[4:7, 2:5] = dtk * np.eye(3)

        Q_k = G_k @ Q_0 @ G_k.T

        P_pred = F_k @ P_k @ F_k.T + Q_k.T

        y_k = np.array([
            latitude[k],
            longitude[k]
        ])

        r_k = y_k - H @ x_k

        S_k = H @ P_pred @ H.T + R

        K_k = P_pred @ H.T @ np.linalg.inv(S_k)

        x_k = x_k + K_k @ r_k

        P_k = (np.eye(12) - K_k @ H) @ P_pred

        historique.append(x_k.copy())

    historique = np.array(historique)

    sortie = df.copy()

    sortie["latitude_filtre"] = historique[:, 0]
    sortie["E_filtre"] = historique[:, 1]

    return sortie
