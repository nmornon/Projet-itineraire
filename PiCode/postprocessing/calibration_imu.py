import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def calibrate_imu(imu_csv_path: Path, axe_attraction_terrestre: str):
    """
    Calibre les données brutes d'un capteur IMU en les centrant.

    Le script effectue les opérations suivantes :
    1. Lit les données depuis un fichier CSV.
    2. Calcule la moyenne et l'écart-type pour chaque variable (accel, gyro).
    3. Centre les données en soustrayant la moyenne de chaque colonne.
    4. Enregistre les données calibrées dans un nouveau fichier CSV avec le suffixe "_calibrated".

    Parameters
    ----------
    imu_csv_path : Path
        Chemin vers le fichier CSV contenant les données IMU brutes.
    axe_attraction_terrestre : str
        Axe de l'attraction terrestre (x, y ou z) pour le centrage de l'accéléromètre.
    """
    if not imu_csv_path.is_file():
        raise FileNotFoundError(f"Le fichier spécifié n'existe pas : {imu_csv_path}")

    # Charger les données IMU depuis le CSV
    try:
        df = pd.read_csv(imu_csv_path)
    except Exception as e:
        raise IOError(f"Erreur lors de la lecture du fichier CSV : {e}")

    # Définir les colonnes à calibrer
    columns_to_calibrate = [
        'accel_x', 'accel_y', 'accel_z',
        'gyro_x', 'gyro_y', 'gyro_z'
    ]

    # Vérifier que les colonnes existent dans le DataFrame
    for col in columns_to_calibrate:
        if col not in df.columns:
            raise ValueError(f"La colonne '{col}' est absente du fichier CSV.")

    # Calculer la moyenne et l'écart-type pour chaque variable
    means = df[columns_to_calibrate].mean()
    stds = df[columns_to_calibrate].std()

    print("Statistiques des données brutes :")
    print("\nMoyennes :")
    print(means)
    print("\nÉcarts-types :")
    print(stds)

    # Centrer les données (soustraction de la moyenne)
    df_calibrated = df.copy()
    df_calibrated[columns_to_calibrate] = df[columns_to_calibrate] - means
    df_calibrated['accel_' + axe_attraction_terrestre] += 1  # Ajouter la gravité à l'axe spécifié

    # Créer le chemin du fichier de sortie
    output_filename = imu_csv_path.stem + "_calibrated.csv"
    output_path = imu_csv_path.parent / output_filename

    # Réécrire les données calibrées dans un nouveau fichier CSV
    try:
        df_calibrated.to_csv(output_path, index=False)
        print(f"\nLes données calibrées ont été enregistrées dans : {output_path}")
    except Exception as e:
        raise IOError(f"Erreur lors de l'écriture du fichier CSV calibré : {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Calibre les données d'un fichier IMU CSV en les centrant."
    )
    parser.add_argument(
        "imu_csv_path",
        type=str,
        help="Chemin vers le fichier CSV contenant les données IMU."
    )

    parser.add_argument(
        "axe_attraction_terrestre",
        type=str,
        help="axe de l'attraction terrestre (x, y ou z) pour le centrage de l'accéléromètre."
    )

    if parser.parse_args().axe_attraction_terrestre not in ['x', 'y', 'z']:
        raise ValueError("L'axe de l'attraction terrestre doit être 'x', 'y' ou 'z'.")
    
    args = parser.parse_args()

    imu_file_path = Path(args.imu_csv_path)
    calibrate_imu(imu_file_path, args.axe_attraction_terrestre)


if __name__ == "__main__":
    main()