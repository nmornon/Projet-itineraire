import shutil
import argparse
from pathlib import Path
from utils import CSVHandler


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

def read_timestamp_csv(csv_path):
    """
    Lit un CSV de timestamps au format :
    timestamp, chemin

    Returns
    -------
    list[dict]
        Liste de dictionnaires :
        - "timestamp"
        - "path"
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            path = row[keys[1]]

            entries.append({
                "timestamp": timestamp,
                "path": path,
            })

        except (ValueError, TypeError):
            continue

    return entries


def create_output_directory(raw_acquisition_dir, suffix="_synced"):
    """
    Crée le dossier de sortie de la synchro offline.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)
    output_dir = raw_acquisition_dir.parent / f"{raw_acquisition_dir.name}{suffix}"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "images").mkdir(exist_ok=True)
    (output_dir / "scans").mkdir(exist_ok=True)

    parameters_file = raw_acquisition_dir / "parameters.py"
    if parameters_file.exists():
        shutil.copy2(parameters_file, output_dir / "parameters.py")

    return output_dir


def synchronize_offline(raw_acquisition_dir, threshold=0.10, suffix="_synced"):
    """
    Calcule les paires caméra/LiDAR synchronisées à partir d'une acquisition brute
    et les enregistre dans un nouveau dossier.

    Parameters
    ----------
    raw_acquisition_dir : str | Path
        Dossier de l'acquisition brute.
    threshold : float
        Seuil maximal |t_cam - t_lidar| en secondes.
    suffix : str
        Suffixe ajouté au nom du dossier de sortie.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)

    # Lecture des fichiers timestamps de la caméra et du LiDAR
    frames_csv = raw_acquisition_dir / "timestamps_frames.csv"
    scans_csv = raw_acquisition_dir / "timestamps_scans.csv"

    if not frames_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {frames_csv}")
    if not scans_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {scans_csv}")

    frame_entries = read_timestamp_csv(frames_csv)
    scan_entries = read_timestamp_csv(scans_csv)

    if not frame_entries:
        raise RuntimeError("Aucune frame trouvée dans timestamps_frames.csv")
    if not scan_entries:
        raise RuntimeError("Aucun scan trouvé dans timestamps_scans.csv")

    # Création du dossier d'acquisition syncrhonisée
    output_dir = create_output_directory(raw_acquisition_dir, suffix=suffix)
    output_images_dir = output_dir / "images"
    output_scans_dir = output_dir / "scans"

    timestamps_frames_csv = init_csv(
        output_dir / "timestamps_frames.csv",
        ["timestamp", "image_file"],
    )
    timestamps_scans_csv = init_csv(
        output_dir / "timestamps_scans.csv",
        ["timestamp", "scan_file"],
    )

    # Création du fichier CSV indiquant les appariements réalisés
    synced_csv_path = output_dir / "synced_cam_lidar.csv"
    synced_csv = init_csv(synced_csv_path, [
        "pair_id",
        "frame_id",
        "t_camera",
        "scan_id",
        "t_lidar",
        "dt_s",
        "image_file",
        "scan_file",
    ])
    # Header du CSV :
    # - pair_id : Identifiant de la paire
    # - frame_id : Identifiant de l'image dans le dossier d'acquisition brut (frame_xxxxxx.jpg)
    # - t_frame : Timestamp de l'image
    # - scan_id : Identifiant du scan dans le dossier d'acquisition brut (scan_xxxxxx.csv)
    # - t_scan : Timestamp du scan
    # - dt_s : Différence absolue entre les deux timestamps
    # - image_file : Chemin du fichier image    
    # - scan_file : Chemin du fichier scan

    synced_count = 0
    used_scan_indices = set()

    for frame_id, frame_entry in enumerate(frame_entries):
        # A COMPLETER
        # Récupération du timestamp de l'image
        timestamp_frame = frame_entry["timestamp"]

        # Recherche du scan avec le timestamp le plus proche
        closest_scan = min(scan_entries, key=lambda s: abs(s["timestamp"] - timestamp_frame))

        # Récupération du timestamp du scan le plus proche temporellement
        timestamp_scan = closest_scan["timestamp"]

        # Calcul de la différence absolue entre les deux timestamps
        dt = abs(timestamp_frame - timestamp_scan)

        # Sélection de la paire si la différence de temps est inférieure à un seuil prédéfini
        if dt > threshold: # Condition pour éliminer une paire
            continue

        # Récupération de l'index du scan le plus proche (dans le dossier d'acquisition)
        scan_index = scan_entries.index(closest_scan)

        # Sélection de la paire si le scan appairé n'a pas déjà été précédemment utilisé
        if scan_index in used_scan_indices: # Condition pour éliminer une paire
            continue

        # Ajout de l'identifiant du scan dans le set des scans déjà utilisés
        used_scan_indices.add(scan_index)

        # Copie des fichiers images et scans dans le dossier d'acquisition synchronisé 
        # ATTENTION : l'identifiant des nouveaux fichiers est différents des identifiants dans l'acquisition brute
        new_frame_id = f"frame_{synced_count:04d}.jpg"
        new_scan_id = f"scan_{synced_count:04d}.csv"

        src_frame = resolve_recorded_path(frame_entry["path"], raw_acquisition_dir)
        src_scan = resolve_recorded_path(closest_scan["path"], raw_acquisition_dir)

        if not src_frame.exists() or not src_scan.exists():
            continue

        dst_frame = output_images_dir / new_frame_id
        dst_scan = output_scans_dir / new_scan_id

        shutil.copy2(src_frame, dst_frame)
        shutil.copy2(src_scan, dst_scan)

        # CSV compatibles avec une acquisition standard (replay_multisensor)
        timestamps_frames_csv.append_row([timestamp_frame, str(dst_frame)])
        timestamps_scans_csv.append_row([timestamp_scan, str(dst_scan)])

        # Ecriture de la paire dans le fichier d'appariement CSV
        synced_csv.append_row([
            synced_count,
            frame_id,
            timestamp_frame,
            scan_index,
            timestamp_scan,
            dt,
            str(dst_frame),
            str(dst_scan),
        ])

        synced_count += 1

    print(f"Dossier brut        : {raw_acquisition_dir}")
    print(f"Dossier synchronisé : {output_dir}")
    print(f"Seuil utilisé       : {threshold * 1000:.1f} ms")
    print(f"Paires conservées   : {synced_count}")


def main(raw_acquisition_dir, threshold, suffix):
    synchronize_offline(
        raw_acquisition_dir=raw_acquisition_dir,
        threshold=threshold,
        suffix=suffix,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronisation offline caméra / LiDAR à partir d'une acquisition brute."
    )

    parser.add_argument(
        "raw_acquisition_dir",
        type=str,
        help="Dossier de l'acquisition brute."
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Seuil maximal |t_cam - t_lidar| en secondes (défaut: 0.10)."
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="_synced",
        help="Suffixe du dossier de sortie (défaut: _synced)."
    )

    args = parser.parse_args()

    main(
        raw_acquisition_dir=args.raw_acquisition_dir,
        threshold=args.threshold,
        suffix=args.suffix,
    )