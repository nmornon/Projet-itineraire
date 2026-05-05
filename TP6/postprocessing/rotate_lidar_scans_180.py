import argparse
import csv
import math
from pathlib import Path


def rotate_point_180_via_polar(x, y):
    """Convert Cartesian -> polar, rotate by 180 deg, then convert back."""
    r = math.hypot(x, y)
    theta = math.atan2(y, x)
    theta_rot = theta + math.pi

    x_rot = r * math.cos(theta_rot)
    y_rot = r * math.sin(theta_rot)
    return x_rot, y_rot


def process_scan_file(scan_file, output_file):
    rows_out = []

    with scan_file.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        if "x" not in fieldnames or "y" not in fieldnames:
            raise ValueError(f"Missing x/y columns in {scan_file}")

        for row in reader:
            x = float(row["x"])
            y = float(row["y"])
            x_rot, y_rot = rotate_point_180_via_polar(x, y)

            row["x"] = f"{x_rot:.12f}"
            row["y"] = f"{y_rot:.12f}"
            rows_out.append(row)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)


def iter_scan_files(scan_path):
    if scan_path.is_file():
        yield scan_path
        return

    if scan_path.name == "scans":
        pattern_root = scan_path
    else:
        pattern_root = scan_path

    for file_path in sorted(pattern_root.rglob("scan_*.csv")):
        if file_path.is_file():
            yield file_path


def main():
    parser = argparse.ArgumentParser(
        description="Rotate LiDAR scans by 180 degrees using polar conversion."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a scan CSV file, a scans directory, or a root folder containing scans.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output root/path. If omitted with --in-place, files are overwritten.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite input files in place.",
    )

    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input path not found: {args.input}")

    if not args.in_place and args.output is None:
        raise ValueError("Provide --output or use --in-place.")

    files = list(iter_scan_files(args.input))
    if not files:
        print("No scan_*.csv files found.")
        return

    processed = 0
    for src in files:
        if args.in_place:
            dst = src
        else:
            if args.output is None:
                raise ValueError("--output is required when not using --in-place.")

            if args.input.is_file():
                dst = args.output
            else:
                rel = src.relative_to(args.input)
                dst = args.output / rel

        process_scan_file(src, dst)
        processed += 1

    print(f"Processed {processed} scan file(s).")


if __name__ == "__main__":
    main()
