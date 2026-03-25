# -*- coding: utf-8 -*-
"""
Build a minimal city-year panel for baseline OLS of fiscal gap on innovation.

Data inputs:
- CNRDS patent granted city-year file (Invg)
- CEIC wide tables: fiscal revenue/expenditure, GDP per capita, second industry, total GDP, science spending

Output:
- regression_v2/ols_fiscal_gap_panel.csv
"""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "regression_v2" / "ols_fiscal_gap_panel.csv"


def clean_city(name: str) -> str:
    s = (name or "").strip()
    s = s.replace("中国", "").replace(":", "")
    s = s.replace("自治区", "").replace("特别行政区", "")
    s = s.replace("省", "").replace("市", "")
    s = s.replace("地区", "").replace("盟", "")
    s = re.sub(r"\s+", "", s)
    return s


def to_float(s: str) -> float | None:
    if s is None:
        return None
    t = str(s).strip().replace(",", "")
    if t in {"", "--", "NA", "N/A", "nan", "NaN"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def parse_ceic_wide(path: Path) -> dict[tuple[str, int], float]:
    """Parse CEIC exported wide CSV into {(city, year): value}.

    CEIC files contain many metadata rows. We detect yearly rows by first column == YYYY.
    City names are taken from the 3rd row (subnational row), and fallback to the header tail after ':'.
    """
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rows = list(csv.reader(f))

    if len(rows) < 4:
        return {}

    header = rows[0]
    subnation = rows[2] if len(rows) > 2 else []

    data_start = None
    for i, r in enumerate(rows):
        if r and re.fullmatch(r"\d{4}", (r[0] or "").strip()):
            data_start = i
            break
    if data_start is None:
        return {}

    result: dict[tuple[str, int], float] = {}
    ncols = len(header)
    for r in rows[data_start:]:
        if not r:
            continue
        y = (r[0] or "").strip()
        if not re.fullmatch(r"\d{4}", y):
            continue
        year = int(y)
        for j in range(1, ncols):
            raw_city = ""
            if j < len(subnation) and subnation[j].strip():
                raw_city = subnation[j].strip()
            elif j < len(header):
                h = header[j]
                raw_city = h.split(":")[-1].strip() if h else ""

            city = clean_city(raw_city)
            if not city:
                continue

            val = to_float(r[j] if j < len(r) else None)
            if val is None:
                continue
            result[(city, year)] = val

    return result


def parse_patent_granted(path: Path) -> dict[tuple[str, int], float]:
    """Parse CNRDS city-year patent granted table using Invg as Y."""
    agg: dict[tuple[str, int], float] = defaultdict(float)
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rd = csv.DictReader(f)
        for row in rd:
            y = (row.get("Year") or "").strip()
            if not re.fullmatch(r"\d{4}", y):
                continue
            year = int(y)
            city = clean_city(row.get("Pftn") or "")
            if not city:
                continue
            invg = to_float(row.get("Invg"))
            if invg is None:
                continue
            agg[(city, year)] += invg
    return dict(agg)


def main() -> None:
    patent = parse_patent_granted(
        BASE / "CNRDS专利数据包" / "各省市创新专利情况" / "各省市专利获得情况" / "各省市专利获得情况.csv"
    )
    fiscal_rev = parse_ceic_wide(BASE / "地级市财政收入.csv")
    fiscal_exp = parse_ceic_wide(BASE / "地级市财政支出.csv")
    gdp_pc = parse_ceic_wide(BASE / "地级市人均GDP.csv")
    second_ind = parse_ceic_wide(BASE / "地级市第二产业.csv")
    gdp_total = parse_ceic_wide(BASE / "地级市总GDP.csv")
    sci_exp = parse_ceic_wide(BASE / "财政支出：科学：地级市.csv")

    # Build contemporaneous rows first.
    by_city_year = {}
    keys = set(patent.keys())
    for k in keys:
        city, year = k
        y = patent.get(k)
        rev = fiscal_rev.get(k)
        exp = fiscal_exp.get(k)
        if y is None or rev is None or exp is None or exp <= 0:
            continue

        fiscal_gap = (exp - rev) / exp
        row = {
            "city": city,
            "year": year,
            "ln_invg": math.log(y + 1.0),
            "fiscal_gap": fiscal_gap,
            "ln_gdppc": None,
            "second_share": None,
            "sci_share": None,
        }

        gpc = gdp_pc.get(k)
        if gpc is not None and gpc > 0:
            row["ln_gdppc"] = math.log(gpc)

        sec = second_ind.get(k)
        gdp = gdp_total.get(k)
        if sec is not None and gdp is not None and gdp > 0:
            row["second_share"] = sec / gdp

        sci = sci_exp.get(k)
        if sci is not None and exp > 0:
            row["sci_share"] = sci / exp

        by_city_year[k] = row

    # Generate lagged fiscal gap.
    by_city_year_lag = {}
    city_years: dict[str, list[int]] = defaultdict(list)
    for city, year in by_city_year.keys():
        city_years[city].append(year)

    for city, years in city_years.items():
        years = sorted(set(years))
        for year in years:
            prev = year - 1
            cur_key = (city, year)
            prev_key = (city, prev)
            if prev_key not in by_city_year:
                continue
            row = dict(by_city_year[cur_key])
            row["fiscal_gap_l1"] = by_city_year[prev_key]["fiscal_gap"]
            by_city_year_lag[cur_key] = row

    rows = sorted(by_city_year_lag.values(), key=lambda x: (x["city"], x["year"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "city",
            "year",
            "ln_invg",
            "fiscal_gap_l1",
            "ln_gdppc",
            "second_share",
            "sci_share",
        ])
        for r in rows:
            w.writerow([
                r["city"],
                r["year"],
                f"{r['ln_invg']:.10f}" if r["ln_invg"] is not None else "",
                f"{r['fiscal_gap_l1']:.10f}" if r["fiscal_gap_l1"] is not None else "",
                f"{r['ln_gdppc']:.10f}" if r["ln_gdppc"] is not None else "",
                f"{r['second_share']:.10f}" if r["second_share"] is not None else "",
                f"{r['sci_share']:.10f}" if r["sci_share"] is not None else "",
            ])

    print(f"Saved panel: {OUT}")
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    main()
