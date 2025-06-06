import argparse
import subprocess
from pathlib import Path

import pandas as pd


def main(csv_path, output_dir):
    df = pd.read_csv(csv_path)
    if "video_uri" not in df.columns:
        raise ValueError("CSV must contain a 'video_uri' column.")

    uris = df["video_uri"].dropna().unique()
    if len(uris) == 0:
        print("No URIs to download.")
        return

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(uris)} files to {output_dir.resolve()} ...")

    # Run gsutil with -m and -I
    proc = subprocess.Popen(
        ["gsutil", "-m", "cp", "-I", str(output_dir)],
        stdin=subprocess.PIPE,
        text=True
    )
    for uri in uris:
        proc.stdin.write(uri + "\n")
    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        print("Download completed with errors.")
    else:
        print("Download completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GCS video URIs from CSV using gsutil -m cp -I.")
    parser.add_argument("csv", help="CSV file with a video_uri column")
    parser.add_argument("out", help="Destination folder to download videos")
    args = parser.parse_args()

    main(args.csv, args.out)
