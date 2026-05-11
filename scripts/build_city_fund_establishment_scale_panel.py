from __future__ import annotations

import csv
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


TARGET_NAME = "2015-2024\u57fa\u91d1\u76ee\u5f55_\u5408\u5e76\u53bb\u91cd_8135.csv"

COL_DATE = "\u6210\u7acb\u65f6\u95f4"
COL_SCALE = "\u76ee\u6807\u89c4\u6a21_RMB_\u767e\u4e07"
COL_REG = "\u6ce8\u518c\u5730\u533a"

MUNICIPALITIES = {
    "\u5317\u4eac\u5e02",
    "\u5929\u6d25\u5e02",
    "\u4e0a\u6d77\u5e02",
    "\u91cd\u5e86\u5e02",
}

CITY_SUFFIXES = ("\u5e02", "\u5dde", "\u5730\u533a", "\u76df")
DISTRICT_SUFFIXES = ("\u533a", "\u53bf", "\u65d7")
PROVINCE_SUFFIXES = ("\u7701", "\u81ea\u6cbb\u533a")
INVALID_NAMES = {"--", "\u672a\u62ab\u9732", "\u65e0", "\u4e0d\u8be6"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_source_file(root: Path) -> Path:
    for current_root, _, files in os.walk(root):
        if TARGET_NAME in files:
            return Path(current_root) / TARGET_NAME
    raise FileNotFoundError(TARGET_NAME)


def parse_amount(amount_text: str) -> float | None:
    if not amount_text:
        return None
    text = amount_text.strip()
    if text in {"", "--"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    return float(match.group(0))


def assign_year(date_text: str) -> int | None:
    if not date_text:
        return None
    text = date_text.strip()
    if text in {"", "--"}:
        return None
    try:
        dt = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None
    year = dt.year
    if dt.month > 6:
        year += 1
    return year


def extract_city(registration: str) -> str | None:
    if not registration:
        return None
    text = registration.strip()
    if text in {"", *INVALID_NAMES}:
        return None

    if "|" in text:
        parts = [part.strip() for part in text.split("|") if part.strip()]
    elif "-" in text:
        parts = [part.strip() for part in text.split("-") if part.strip()]
    else:
        parts = [text]

    if not parts:
        return None

    if len(parts) == 1:
        part = parts[0]
        if part in MUNICIPALITIES:
            return part
        if part.endswith(CITY_SUFFIXES):
            return part
        return None

    if len(parts) == 2:
        first, second = parts[0], parts[1]
        if second in INVALID_NAMES:
            return first if first in MUNICIPALITIES else None
        if first in MUNICIPALITIES:
            if second.endswith(DISTRICT_SUFFIXES):
                return first
            if second.endswith(CITY_SUFFIXES):
                return second
            return first
        if first.endswith(PROVINCE_SUFFIXES) or first in {"\u65b0\u7586", "\u5185\u8499\u53e4"}:
            if second.endswith(CITY_SUFFIXES):
                return second
            return None
        if first.endswith(CITY_SUFFIXES):
            return first
        if second.endswith(CITY_SUFFIXES):
            return second
        if second.endswith(DISTRICT_SUFFIXES):
            return None
        return None

    if parts[0] == "\u4e2d\u56fd":
        if len(parts) < 3:
            return None
        province = parts[1]
        third = parts[2]
        fourth = parts[3] if len(parts) >= 4 else ""
        if province in MUNICIPALITIES:
            if third.endswith(DISTRICT_SUFFIXES) or third in INVALID_NAMES:
                return province
            if third.endswith(CITY_SUFFIXES):
                return third
            return province
        if third.endswith(CITY_SUFFIXES):
            return third
        if third.endswith(DISTRICT_SUFFIXES):
            return None
        if fourth and fourth.endswith(CITY_SUFFIXES):
            return fourth
        return None

    first, second = parts[0], parts[1]
    if first in MUNICIPALITIES:
        if second.endswith(DISTRICT_SUFFIXES):
            return first
        if second.endswith(CITY_SUFFIXES):
            return second
        return first

    if first.endswith(PROVINCE_SUFFIXES) or first in {"\u65b0\u7586", "\u5185\u8499\u53e4"}:
        if second.endswith(CITY_SUFFIXES):
            return second
        return None

    if first.endswith(CITY_SUFFIXES):
        return first

    if second.endswith(CITY_SUFFIXES):
        return second

    if second.endswith(DISTRICT_SUFFIXES):
        return None

    return None


def build_panel(source_file: Path) -> list[dict[str, object]]:
    aggregates: dict[tuple[str, int], dict[str, float | int]] = defaultdict(
        lambda: {
            "fund_count": 0,
            "established_scale_rmb_m": 0.0,
            "disclosed_scale_count": 0,
        }
    )
    cities: set[str] = set()
    years: set[int] = set()

    with source_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = extract_city(row.get(COL_REG, ""))
            year = assign_year(row.get(COL_DATE, ""))
            if city is None or year is None:
                continue

            key = (city, year)
            bucket = aggregates[key]
            bucket["fund_count"] += 1

            scale = parse_amount(row.get(COL_SCALE, ""))
            if scale is not None:
                bucket["established_scale_rmb_m"] += scale
                bucket["disclosed_scale_count"] += 1

            cities.add(city)
            years.add(year)

    annual_rows_by_city: dict[str, list[dict[str, object]]] = defaultdict(list)
    for city in sorted(cities):
        for year in sorted(years):
            bucket = aggregates.get(
                (city, year),
                {
                    "fund_count": 0,
                    "established_scale_rmb_m": 0.0,
                    "disclosed_scale_count": 0,
                },
            )
            fund_count = int(bucket["fund_count"])
            disclosed_scale_count = int(bucket["disclosed_scale_count"])
            scale_sum = float(bucket["established_scale_rmb_m"])

            if fund_count > 0 and disclosed_scale_count == 0:
                scale_value: float | str = ""
            else:
                scale_value = round(scale_sum, 6)

            annual_rows_by_city[city].append(
                {
                    "city": city,
                    "year": year,
                    "fund_established_count": fund_count,
                    "fund_established_scale_rmb_m": scale_value,
                }
            )

    panel_rows: list[dict[str, object]] = []
    for city in sorted(annual_rows_by_city):
        cumulative_count = 0
        cumulative_scale = 0.0
        cumulative_scale_complete = True

        city_rows = annual_rows_by_city[city]
        for idx, row in enumerate(city_rows):
            annual_count = int(row["fund_established_count"])
            annual_scale = row["fund_established_scale_rmb_m"]

            cumulative_count += annual_count
            if annual_scale == "" and annual_count > 0:
                cumulative_scale_complete = False
            elif annual_scale != "":
                cumulative_scale += float(annual_scale)

            window_rows = city_rows[max(0, idx - 4) : idx + 1]
            rolling5_count = sum(int(window_row["fund_established_count"]) for window_row in window_rows)

            rolling5_scale_complete = True
            rolling5_scale_sum = 0.0
            for window_row in window_rows:
                window_count = int(window_row["fund_established_count"])
                window_scale = window_row["fund_established_scale_rmb_m"]
                if window_scale == "" and window_count > 0:
                    rolling5_scale_complete = False
                    break
                if window_scale != "":
                    rolling5_scale_sum += float(window_scale)

            row["cumulative_fund_established_count"] = cumulative_count
            row["cumulative_fund_established_scale_rmb_m"] = (
                round(cumulative_scale, 6) if cumulative_scale_complete else ""
            )
            row["rolling5_fund_established_count"] = rolling5_count
            row["rolling5_fund_established_scale_rmb_m"] = (
                round(rolling5_scale_sum, 6) if rolling5_scale_complete else ""
            )
            panel_rows.append(row)

    return panel_rows


def write_panel(rows: list[dict[str, object]], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "city",
        "year",
        "fund_established_count",
        "fund_established_scale_rmb_m",
        "cumulative_fund_established_count",
        "cumulative_fund_established_scale_rmb_m",
        "rolling5_fund_established_count",
        "rolling5_fund_established_scale_rmb_m",
    ]
    with output_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = project_root()
    source_file = find_source_file(root)
    output_file = root / "\u9762\u677f\u6570\u636e" / "\u5e02\u7ea7\u57fa\u91d1\u8bbe\u7acb\u89c4\u6a21\u9762\u677f_2015_2025.csv"
    rows = build_panel(source_file)
    write_panel(rows, output_file)
    print(f"source_file={source_file}")
    print(f"output_file={output_file}")
    print(f"row_count={len(rows)}")
    print(f"city_count={len({row['city'] for row in rows})}")
    print(f"year_count={len({row['year'] for row in rows})}")


if __name__ == "__main__":
    main()
