import argparse
import csv
import json
import math
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "castnet" / "raw"
DEFAULT_OUT = REPO_ROOT / "data" / "castnet" / "processed" / "current_reading.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a small CASTNET reading JSON from EPA ZIP files.")
    parser.add_argument("--lat", type=float, default=40.9478, help="Demo latitude. Defaults to Galesburg, IL.")
    parser.add_argument("--lon", type=float, default=-90.3712, help="Demo longitude. Defaults to Galesburg, IL.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    sites = _load_sites(args.raw_dir / "site.zip")
    nearest_sites = sorted(sites, key=lambda site: _distance(args.lat, args.lon, site["latitude"], site["longitude"]))

    ozone_by_site = _latest_ozone(args.raw_dir / "ozone_2026.zip")
    co_by_site = _latest_gas(args.raw_dir / "hourly_gas_2026.zip", parameter="CO")
    drychem_by_site = _latest_drychem(args.raw_dir / "drychem.zip")

    selected = _select_site(nearest_sites, ozone_by_site, drychem_by_site, co_by_site)
    site_id = selected["site_id"]
    ozone = ozone_by_site[site_id]
    drychem = drychem_by_site[site_id]
    co = co_by_site[site_id]

    reading = {
        "site_id": site_id,
        "location": f"{selected['site_name']}, {selected['state']}",
        "ozone_ppb": ozone["ozone_ppb"],
        "sulfate_ug_m3": drychem["sulfate_ug_m3"],
        "nitrate_ug_m3": drychem["nitrate_ug_m3"],
        "co_ppb": co["co_ppb"],
        "measurement_date": ozone["date_time"].split(" ")[0],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reading, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reading, indent=2))


def _load_sites(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as zf, zf.open("site.csv") as file:
        for row in csv.DictReader(_decoded_lines(file)):
            latitude = _float(row.get("LATITUDE"))
            longitude = _float(row.get("LONGITUDE"))
            if latitude is None or longitude is None:
                continue
            rows.append(
                {
                    "site_id": row["SITE_ID"],
                    "site_name": row["SITE_NAME"],
                    "state": row["STATE"],
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )
    return rows


def _latest_ozone(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(path) as zf, zf.open("ozone_2026.csv") as file:
        for row in csv.DictReader(_decoded_lines(file)):
            value = _float(row.get("OZONE"))
            if value is None:
                continue
            _keep_latest(
                latest,
                row["SITE_ID"],
                row["DATE_TIME"],
                {"date_time": row["DATE_TIME"], "ozone_ppb": value},
            )
    return latest


def _latest_gas(path: Path, parameter: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(path) as zf, zf.open("hourly_gas_2026.csv") as file:
        for row in csv.DictReader(_decoded_lines(file)):
            if row.get("PARAMETER") != parameter:
                continue
            value = _float(row.get("VALUE"))
            if value is None:
                continue
            _keep_latest(
                latest,
                row["SITE_ID"],
                row["DATE_TIME"],
                {"date_time": row["DATE_TIME"], "co_ppb": value},
            )
    return latest


def _latest_drychem(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(path) as zf, zf.open("drychem.csv") as file:
        for row in csv.DictReader(_decoded_lines(file)):
            sulfate = _float(row.get("TSO4"))
            nitrate = _float(row.get("TNO3"))
            if sulfate is None or nitrate is None:
                continue
            _keep_latest(
                latest,
                row["SITE_ID"],
                row["DATEOFF"],
                {
                    "date_time": row["DATEOFF"],
                    "sulfate_ug_m3": sulfate,
                    "nitrate_ug_m3": nitrate,
                },
            )
    return latest


def _select_site(
    nearest_sites: list[dict[str, Any]],
    ozone_by_site: dict[str, dict[str, Any]],
    drychem_by_site: dict[str, dict[str, Any]],
    co_by_site: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    for site in nearest_sites:
        site_id = site["site_id"]
        if site_id in ozone_by_site and site_id in drychem_by_site and site_id in co_by_site:
            return site
    raise RuntimeError("No nearby CASTNET site has ozone, dry chemistry, and CO data.")


def _keep_latest(latest: dict[str, dict[str, Any]], site_id: str, date_text: str, payload: dict[str, Any]) -> None:
    date_value = _parse_date(date_text)
    current = latest.get(site_id)
    if current is None or date_value > current["_date_value"]:
        latest[site_id] = {"_date_value": date_value, **payload}


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _distance(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    earth_radius_km = 6371.0
    d_lat = math.radians(lat_b - lat_a)
    d_lon = math.radians(lon_b - lon_a)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat_a)) * math.cos(math.radians(lat_b)) * math.sin(d_lon / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _decoded_lines(file: Any):
    for line in file:
        yield line.decode("utf-8-sig")


if __name__ == "__main__":
    main()
