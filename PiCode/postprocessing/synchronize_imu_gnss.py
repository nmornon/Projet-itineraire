import shutil
import argparse
from pathlib import Path
from utils import CSVHandler


INVALID_GNSS_DOP = 9999.0


def resolve_recorded_path(path_str, acquisition_dir):
    """
    Résout un chemin lu dans le CSV (absolu ou relatif au dossier d'acquisition).
    """
    path_obj = Path(path_str)
    if path_obj.is_absolute():
        return path_obj

    # Cas fréquent: chemin déjà relatif à la racine du projet (ex: data/acquisition...)
    if path_obj.exists():
        return path_obj.resolve()

    # Cas alternatif: chemin relatif au dossier d'acquisition
    candidate = (acquisition_dir / path_obj)
    if candidate.exists():
        return candidate.resolve()

    # Fallback explicite (sera filtré plus tard par exists())
    return candidate.resolve()


def init_csv(csv_path, header):
    """
    Crée un CSV propre avec en-tête (écrase l'ancien fichier si présent).
    """
    csv_path = Path(csv_path)
    if csv_path.exists():
        csv_path.unlink()

    handler = CSVHandler(str(csv_path))
    handler.create_csv_with_header(header)
    return handler

def read_gnss_csv(csv_path):
    """
    Lit un CSV de relevés GNSS au format :
    timestamp, latitude, longitude

    Returns
    -------
    list[dict]
        Liste de dictionnaires :
        - "timestamp"
        - "latitude"
        - "longitude"
    """
    return CSVHandler(str(csv_path)).read_dict_rows()


def create_output_directory(raw_acquisition_dir, suffix="_synced_imu_gnss"):
    """
    Crée le dossier de sortie de la synchro offline.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)
    output_dir = raw_acquisition_dir.parent / f"{raw_acquisition_dir.name}{suffix}"

    output_dir.mkdir(parents=True, exist_ok=True)

    parameters_file = raw_acquisition_dir / "parameters.py"
    if parameters_file.exists():
        shutil.copy2(parameters_file, output_dir / "parameters.py")

    return output_dir


def synchronize_imu_gnss(raw_acquisition_dir, threshold=0.10, suffix="_synced_imu_gnss"):
    """
    Synchronise les données IMU et GNSS à partir d'une acquisition brute
    et les enregistre dans un nouveau dossier.

    Parameters
    ----------
    raw_acquisition_dir : str | Path
        Dossier de l'acquisition brute.
    threshold : float
        Seuil maximal |t_imu - t_gnss| en secondes.
    suffix : str
        Suffixe ajouté au nom du dossier de sortie.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)

    # Lecture des fichiers timestamps de l'IMU et du GNSS
    imu_csv = raw_acquisition_dir / "imu.csv"
    gnss_csv = raw_acquisition_dir / "gnss.csv"

    if not imu_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {imu_csv}")
    if not gnss_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {gnss_csv}")

    imu_entries = CSVHandler(str(imu_csv)).read_dict_rows()
    gnss_entries = CSVHandler(str(gnss_csv)).read_dict_rows()

    if not imu_entries:
        raise RuntimeError("Aucune donnée IMU trouvée dans imu.csv")
    if not gnss_entries:
        raise RuntimeError("Aucune donnée GNSS trouvée dans gnss.csv")

    # Création du dossier d'acquisition synchronisée
    output_dir = create_output_directory(raw_acquisition_dir, suffix=suffix)
    
    # Création du fichier CSV indiquant les appariements réalisés
    synced_csv_path = output_dir / "synced_imu_gnss.csv"
    synced_csv = init_csv(synced_csv_path, [
    "timestamp",
    "accel_x", "accel_y", "accel_z",
    "gyro_x", "gyro_y", "gyro_z",
    "mag_x", "mag_y", "mag_z",
    "latitude", "longitude",
    "hdop", "pdop", "vdop",
    "gnss_valid"
])

    synced_count = 0
    imu_count = 0
    unmatched_count = 0
    used_gnss_indices = set()
    last_valid_gnss = None

    for imu_entry in imu_entries:
        imu_count += 1
        timestamp_imu = float(imu_entry["timestamp"])

        closest_gnss = None
        closest_gnss_index = None
        dt = None

        if gnss_entries:
            # Recherche du relevé GNSS avec le timestamp le plus proche
            closest_gnss_index, closest_gnss = min(
                enumerate(gnss_entries),
                key=lambda item: abs(float(item[1]["timestamp"]) - timestamp_imu),
            )
            timestamp_gnss = float(closest_gnss["timestamp"])
            dt = abs(timestamp_imu - timestamp_gnss)

            if dt <= threshold and closest_gnss_index in used_gnss_indices:
                closest_gnss = None
                closest_gnss_index = None

        if closest_gnss is None or dt is None or dt > threshold:
            unmatched_count += 1
            latitude = last_valid_gnss["latitude"] if last_valid_gnss is not None else ""
            longitude = last_valid_gnss["longitude"] if last_valid_gnss is not None else ""
            synced_csv.append_row([
		    timestamp_imu,
		    imu_entry["accel_x"], imu_entry["accel_y"], imu_entry["accel_z"],
		    imu_entry["gyro_x"], imu_entry["gyro_y"], imu_entry["gyro_z"],
		    imu_entry["mag_x"], imu_entry["mag_y"], imu_entry["mag_z"],
		    latitude, longitude,
		    "", "", "",
		    0
		])
            continue

        used_gnss_indices.add(closest_gnss_index)
        last_valid_gnss = closest_gnss

        # Ecriture des données synchronisées dans le fichier CSV
        synced_csv.append_row([
	    timestamp_imu,
	    imu_entry["accel_x"], imu_entry["accel_y"], imu_entry["accel_z"],
	    imu_entry["gyro_x"], imu_entry["gyro_y"], imu_entry["gyro_z"],
	    imu_entry["mag_x"], imu_entry["mag_y"], imu_entry["mag_z"],
	    closest_gnss["latitude"], closest_gnss["longitude"],
	    closest_gnss["hdop"], closest_gnss["pdop"], closest_gnss["vdop"],
	    1
	])

        synced_count += 1

    print(f"Dossier brut        : {raw_acquisition_dir}")
    print(f"Dossier synchronisé : {output_dir}")
    print(f"Seuil utilisé       : {threshold * 1000:.1f} ms")
    print(f"IMU traitées        : {imu_count}")
    print(f"Paires GNSS/IMU     : {synced_count}")
    print(f"IMU sans GNSS       : {unmatched_count}")


def main(raw_acquisition_dir, threshold, suffix):
    synchronize_imu_gnss(
        raw_acquisition_dir=raw_acquisition_dir,
        threshold=threshold,
        suffix=suffix,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronisation offline IMU / GNSS à partir d'une acquisition brute."
    )

    parser.add_argument(
        "raw_acquisition_dir",
        type=str,
        help="Dossier de l'acquisition brute."
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Seuil maximal |t_imu - t_gnss| en secondes (défaut: 0.05)."
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="_synced_imu_gnss",
        help="Suffixe du dossier de sortie (défaut: _synced_imu_gnss)."
    )

    args = parser.parse_args()

    main(
        raw_acquisition_dir=args.raw_acquisition_dir,
        threshold=args.threshold,
        suffix=args.suffix,
    )
