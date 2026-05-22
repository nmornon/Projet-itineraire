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

def calibration_multi_immobile(imu_file, gnss_files):
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

        "mag_x": imu["mag_x"].var(),
        "mag_y": imu["mag_y"].var(),
        "mag_z": imu["mag_z"].var()
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

    # Angles initiaux
    g = 9.81

    roulis_0 = np.arccos(biais["accel_x"] / g)
    tangage_0 = np.arcsin(biais["accel_z"] / g)
    lacet_0 = np.arctan2(biais["mag_z"], biais["mag_y"])

    biais_accel_ENU = imu_to_enu(np.array([biais["accel_x"], biais["accel_y"], biais["accel_z"]]))
    biais_gyro_ENU = imu_to_enu(np.array([biais["gyro_x"], biais["gyro_y"], biais["gyro_z"]]))
    variances_accel_ENU = imu_to_enu(np.array([variances["accel_x"], variances["accel_y"], variances["accel_z"]]))
    variances_gyro_ENU = imu_to_enu(np.array([variances["gyro_x"], variances["gyro_y"], variances["gyro_z"]]))

    x = np.array([
        latitude[0],
        longitude[0],
        0.0,
        0.0,
        tangage_0,
        roulis_0,
        lacet_0,
        biais_accel_ENU[0],
        biais_accel_ENU[1],
        biais_gyro_ENU[0],
        biais_gyro_ENU[1],
        biais_gyro_ENU[2]
    ])

    P = np.diag([
        variances[gnss_longitude],
        variances[gnss_latitude],
        1e-6,
        1e-6,
        1e-6,
        1e-6,
        1e-6,
        1e-6,
        1e-6,
        1e-6,
        1e-6,
        1e-6
    ])

    Q = np.diag([
        variances[gnss_longitude],
        variances[gnss_latitude],
        1e-6,
        1e-6,
        1e-6
    ])

    R = np.diag([
        variances_
        1e-5
    ])

    H = np.array([
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ])

    historique = []

    for k in range(len(df)):
        dtk = dt[k]

        

        P_pred = F @ P @ F.T + Q

        z = np.array([
            latitude[k],
            longitude[k]
        ])

        innovation = z - H @ x_pred

        S = H @ P_pred @ H.T + R

        K = P_pred @ H.T @ np.linalg.inv(S)

        x = x_pred + K @ innovation

        P = (np.eye(7) - K @ H) @ P_pred

        historique.append(x.copy())

    historique = np.array(historique)

    sortie = df.copy()

    sortie["latitude_filtre"] = historique[:, 0]
    sortie["longitude_filtre"] = historique[:, 1]

    return sortie