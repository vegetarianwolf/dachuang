# -*- coding: utf-8 -*-
"""
build_panel_v3.py — City-year panel for fiscal pressure & innovation regression.

Outputs: regression_v3/panel_v3.csv  (and panel_v3.dta via stata if needed)

Panel: ~290 cities × 2010-2023 = ~4800 obs (before listwise deletion)
"""

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

# ── Hardcoded absolute paths ──────────────────────────────────────────────────
BASE   = Path("C:/Users/21288/Desktop/DACHUANG/dachuang")
OUTDIR = BASE / "regression_v3"
OUT_CSV = OUTDIR / "panel_v3.csv"

YEAR_MIN, YEAR_MAX = 2010, 2023

# Data paths
PATENT_GRANTED = BASE / "CNRDS专利数据包/各省市创新专利情况/各省市专利获得情况/各省市专利获得情况.csv"
PATENT_APPLIED = BASE / "CNRDS专利数据包/各省市创新专利情况/各省市专利申请情况/各省市专利申请情况.csv"
FISCAL_REV     = BASE / "地级市财政收入.csv"
FISCAL_EXP     = BASE / "地级市财政支出.csv"
GDPPC          = BASE / "地级市人均GDP.csv"
GDP_TOTAL      = BASE / "地级市总GDP.csv"
SECOND_IND     = BASE / "地级市第二产业.csv"
SCI_EXP        = BASE / "财政支出：科学：地级市.csv"
DEBT           = BASE / "地方政府债务：地级市：余额.csv"
POP            = BASE / "常住人口.csv"
FDI            = BASE / "实际利用外资.csv"
LOAN           = BASE / "金融机构贷款余额.csv"
GGF_CITY_YEAR  = BASE / "政府引导基金整合数据/城市_投资统计_分年份_2000-2024.csv"
MARKETIZATION  = BASE / "1997-2024年市场化指数和各分项指数 的副本.csv"
FISCAL_TRANS   = BASE / "市级政府财政透明度（2013-2024年） 的副本.csv"


# ── Utility functions ─────────────────────────────────────────────────────────

def clean_city(name):
    s = (name or "").strip()
    s = s.replace("中国", "").replace(":", "")
    s = s.replace("自治区", "").replace("特别行政区", "")
    s = s.replace("省", "").replace("市", "")
    s = s.replace("地区", "").replace("盟", "")
    s = re.sub(r"\s+", "", s)
    return s


def to_float(s):
    if s is None:
        return None
    t = str(s).strip().replace(",", "")
    if t in {"", "--", "NA", "N/A", "nan", "NaN", "未披露", "."}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def winsorize(values, lo=0.01, hi=0.99):
    """Return dict with winsorized values at lo/hi percentiles."""
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if not clean:
        return values
    clean_sorted = sorted(clean)
    n = len(clean_sorted)
    lo_val = clean_sorted[int(lo * n)]
    hi_val = clean_sorted[min(int(hi * n), n - 1)]
    return [
        None if v is None or math.isnan(v)
        else max(lo_val, min(hi_val, v))
        for v in values
    ]


# ── CEIC wide-table parser ────────────────────────────────────────────────────

def parse_ceic_wide(path):
    """Parse CEIC multi-row-metadata wide CSV → {(city, year): value}.

    Row 0   : header (col 0 empty; cols 1+ = 'series_name:province:city')
    Row 1   : 区域
    Row 2   : 次国家  ← city name lives here
    Rows 3-k: other metadata
    Data rows: first column matches /^\d{4}$/
    """
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        print(f"  WARNING: Not found: {path}")
        return {}

    if len(rows) < 4:
        return {}

    header   = rows[0]
    subnation = rows[2] if len(rows) > 2 else []

    # Find first data row (year)
    data_start = None
    for i, r in enumerate(rows):
        if r and re.fullmatch(r"\d{4}", (r[0] or "").strip()):
            data_start = i
            break
    if data_start is None:
        return {}

    result = {}
    ncols = len(header)
    for r in rows[data_start:]:
        if not r:
            continue
        y = (r[0] or "").strip()
        if not re.fullmatch(r"\d{4}", y):
            continue
        year = int(y)
        if year < YEAR_MIN or year > YEAR_MAX:
            continue
        for j in range(1, ncols):
            # Prefer subnation row for city name; fall back to last token after ':' in header
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


# ── Year-indicator two-line parser ────────────────────────────────────────────

def parse_year_indicator(path):
    """Parse two-line-header wide CSV → {(city, year): value}.

    Row 0: year labels (col 0 = 'city' label; cols 1+ = years as strings)
    Row 1: indicator names (same structure, col 0 = '' or indicator name)
    Data rows: col 0 = city name, cols 1+ = values for each year
    """
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        print(f"  WARNING: Not found: {path}")
        return {}

    if len(rows) < 3:
        return {}

    year_row = rows[0]
    # Collect year columns
    year_cols = {}   # col_index → year
    for j in range(1, len(year_row)):
        y = (year_row[j] or "").strip()
        if re.fullmatch(r"\d{4}", y):
            year_cols[j] = int(y)

    result = {}
    for r in rows[2:]:
        if not r:
            continue
        raw_city = (r[0] or "").strip()
        if not raw_city:
            continue
        city = clean_city(raw_city)
        if not city:
            continue
        for j, year in year_cols.items():
            if year < YEAR_MIN or year > YEAR_MAX:
                continue
            val = to_float(r[j] if j < len(r) else None)
            if val is None:
                continue
            result[(city, year)] = val
    return result


# ── CNRDS patent parser ───────────────────────────────────────────────────────

def parse_cnrds_patent(path, value_cols):
    """Parse CNRDS patent CSV (row 1 = English header, row 2 = Chinese, data from row 3).

    value_cols: list of column names to sum (e.g. ['Invg', 'Umg', 'Desg'])
    Returns {(city, year): {col: total, ...}}
    """
    agg = defaultdict(lambda: defaultdict(float))
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
            reader = csv.DictReader(f)
            # Skip Chinese description row (it's the first data row in DictReader)
            headers = reader.fieldnames
            first = True
            for row in reader:
                if first:
                    # Check if this is the Chinese description row
                    if row.get("Year", "").strip() in {"会计年度", ""}:
                        first = False
                        continue
                    first = False
                y = (row.get("Year") or "").strip()
                if not re.fullmatch(r"\d{4}", y):
                    continue
                year = int(y)
                if year < YEAR_MIN or year > YEAR_MAX:
                    continue
                # For municipalities (北京/上海/天津/重庆): Pftn is empty, use Prvn
                pftn = (row.get("Pftn") or "").strip()
                prvn = (row.get("Prvn") or "").strip()
                if not pftn:
                    pftn = prvn
                city = clean_city(pftn)
                if not city:
                    continue
                province = clean_city(prvn)
                for col in value_cols:
                    val = to_float(row.get(col))
                    if val is not None:
                        agg[(city, year)][col] += val
    except FileNotFoundError:
        print(f"  WARNING: Not found: {path}")
    return {k: dict(v) for k, v in agg.items()}


# ── GGF investment parser ─────────────────────────────────────────────────────

def parse_ggf_city_year(path):
    """Parse 城市_投资统计_分年份 → {(city, year): row_dict}."""
    result = {}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                y = to_float(row.get("年份"))
                if y is None:
                    continue
                year = int(y)
                if year < YEAR_MIN or year > YEAR_MAX:
                    continue
                city = clean_city(row.get("城市") or "")
                if not city:
                    continue
                result[(city, year)] = row
    except FileNotFoundError:
        print(f"  WARNING: Not found: {path}")
    return result


# ── Marketization index ───────────────────────────────────────────────────────

def parse_marketization(path):
    """Parse province-level marketization index → {(province, year): index_value}."""
    result = {}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                y = to_float(row.get("year"))
                if y is None:
                    continue
                year = int(y)
                if year < YEAR_MIN or year > YEAR_MAX:
                    continue
                prov = clean_city(row.get("省份") or "")
                val = to_float(row.get("market"))
                if prov and val is not None:
                    result[(prov, year)] = val
    except FileNotFoundError:
        print(f"  WARNING: Not found: {path}")
    return result


# ── Fiscal transparency ───────────────────────────────────────────────────────

def parse_fiscal_transparency(path):
    """Parse wide city-level fiscal transparency → {(city, year): score}."""
    result = {}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = clean_city(row.get("城市") or "")
                if not city:
                    continue
                for col, val_str in row.items():
                    m = re.match(r"财政透明度(\d{4})", col)
                    if not m:
                        continue
                    year = int(m.group(1))
                    if year < YEAR_MIN or year > YEAR_MAX:
                        continue
                    val = to_float(val_str)
                    if val is not None:
                        result[(city, year)] = val
    except FileNotFoundError:
        print(f"  WARNING: Not found: {path}")
    return result


# ── Main assembly ─────────────────────────────────────────────────────────────

def main():
    print("=== build_panel_v3.py ===")
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("[1/12] Loading patent granted data...")
    granted = parse_cnrds_patent(PATENT_GRANTED, ["Invg", "Umg", "Desg"])

    print("[2/12] Loading patent application data...")
    applied = parse_cnrds_patent(PATENT_APPLIED, ["Inva", "Uma", "Desa"])

    print("[3/12] Loading fiscal revenue & expenditure...")
    fiscal_rev = parse_ceic_wide(FISCAL_REV)
    fiscal_exp = parse_ceic_wide(FISCAL_EXP)

    print("[4/12] Loading GDP data...")
    gdppc      = parse_ceic_wide(GDPPC)
    gdp_total  = parse_ceic_wide(GDP_TOTAL)
    second_ind = parse_ceic_wide(SECOND_IND)
    sci_exp    = parse_ceic_wide(SCI_EXP)

    print("[5/12] Loading debt data...")
    debt = parse_ceic_wide(DEBT)

    print("[6/12] Loading population, FDI, loan data...")
    pop  = parse_year_indicator(POP)
    fdi  = parse_year_indicator(FDI)
    loan = parse_year_indicator(LOAN)

    print("[7/12] Loading GGF investment data...")
    ggf = parse_ggf_city_year(GGF_CITY_YEAR)

    print("[8/12] Loading marketization index...")
    mkt = parse_marketization(MARKETIZATION)

    print("[9/12] Loading fiscal transparency...")
    ftrans = parse_fiscal_transparency(FISCAL_TRANS)

    # ── Build city-province mapping from patent data ──────────────────────────
    city_province = {}
    for path in [PATENT_GRANTED]:
        try:
            with open(path, "r", encoding="utf-8-sig", newline="", errors="ignore") as f:
                reader = csv.DictReader(f)
                first = True
                for row in reader:
                    if first:
                        if row.get("Year", "").strip() in {"会计年度", ""}:
                            first = False; continue
                        first = False
                    pftn = (row.get("Pftn") or "").strip()
                    prvn = (row.get("Prvn") or "").strip()
                    if not pftn:
                        pftn = prvn
                    city = clean_city(pftn)
                    prov = clean_city(prvn)
                    if city and prov:
                        city_province[city] = prov
        except FileNotFoundError:
            pass

    print("[10/12] Building city-year rows...")

    # All patent cities × years
    all_keys = set(granted.keys()) | set(applied.keys())
    by_city_year = {}

    for (city, year) in all_keys:
        g = granted.get((city, year), {})
        a = applied.get((city, year), {})
        invg  = g.get("Invg", 0.0)
        umg   = g.get("Umg",  0.0)
        desg  = g.get("Desg", 0.0)
        inva  = a.get("Inva", 0.0)

        total_grant = invg + umg
        inv_share   = invg / (invg + umg + desg) if (invg + umg + desg) > 0 else None

        rev = fiscal_rev.get((city, year))
        exp = fiscal_exp.get((city, year))
        if exp is None or exp <= 0:
            fiscal_gap = None
        else:
            fiscal_gap = (exp - rev) / exp if rev is not None else None

        dbt = debt.get((city, year))
        if dbt is not None and rev is not None and rev > 0:
            debt_ratio = dbt / rev
        else:
            debt_ratio = None

        gpc = gdppc.get((city, year))
        gdt = gdp_total.get((city, year))
        sec = second_ind.get((city, year))
        sci = sci_exp.get((city, year))
        p   = pop.get((city, year))
        f   = fdi.get((city, year))
        ln  = loan.get((city, year))

        gg_row  = ggf.get((city, year), {})
        invest_amt = to_float(gg_row.get("总投资额_百万元")) or 0.0
        invest_cnt = to_float(gg_row.get("总投资次数"))     or 0.0
        early_rat  = to_float(gg_row.get("早期投资次数占比"))
        broad_rat  = to_float(gg_row.get("广义早期投资次数占比"))

        prov = city_province.get(city, "")
        market = mkt.get((prov, year))
        ftrans_val = ftrans.get((city, year))

        row = {
            "city":         city,
            "province":     prov,
            "year":         year,
            # Patent outcomes (contemporaneous)
            "ln_invg":      math.log(invg + 1),
            "ln_umg":       math.log(umg + 1),
            "ln_inva":      math.log(inva + 1),
            "ln_total_grant": math.log(total_grant + 1),
            "inv_share":    inv_share,
            # Fiscal pressure (to be lagged)
            "fiscal_gap":   fiscal_gap,
            "debt_ratio":   debt_ratio,
            "ln_debt_ratio": math.log(debt_ratio) if debt_ratio is not None and debt_ratio > 0 else None,
            # GGF investment (to be lagged)
            "invest_amt":   invest_amt,
            "invest_cnt":   invest_cnt,
            "ln_invest_amt": math.log(invest_amt + 1),
            "ln_invest_cnt": math.log(invest_cnt + 1),
            "early_deal_ratio": early_rat,
            "broad_early_ratio": broad_rat,
            # Controls (contemporaneous)
            "ln_pgdp":      math.log(gpc) if gpc is not None and gpc > 0 else None,
            "sec_ratio":    sec / gdt if sec is not None and gdt is not None and gdt > 0 else None,
            "sci_ratio":    sci / exp if sci is not None and exp is not None and exp > 0 else None,
            "fdi_dep":      f / gdt if f is not None and gdt is not None and gdt > 0 else None,
            "fin_depth":    ln / gdt if ln is not None and gdt is not None and gdt > 0 else None,
            "ln_pop":       math.log(p) if p is not None and p > 0 else None,
            "market_index": market,
            "fiscal_trans": ftrans_val,
        }
        by_city_year[(city, year)] = row

    # ── Generate L1 lags ──────────────────────────────────────────────────────
    print("[11/12] Generating L1 lags...")
    lag_vars = [
        "fiscal_gap", "ln_debt_ratio",
        "ln_invest_amt", "ln_invest_cnt",
        "early_deal_ratio", "broad_early_ratio",
    ]

    lagged_rows = {}
    for (city, year), row in by_city_year.items():
        prev = (city, year - 1)
        if prev not in by_city_year:
            continue
        prev_row = by_city_year[prev]
        new_row = dict(row)
        for v in lag_vars:
            new_row[f"{v}_L1"] = prev_row.get(v)
        lagged_rows[(city, year)] = new_row

    # ── Winsorize continuous variables ────────────────────────────────────────
    print("[12/12] Winsorizing and writing output...")
    rows_list = sorted(lagged_rows.values(), key=lambda r: (r["city"], r["year"]))

    winsorise_cols = [
        "ln_invg", "ln_umg", "ln_inva", "ln_total_grant", "inv_share",
        "fiscal_gap_L1", "ln_debt_ratio_L1",
        "ln_invest_amt_L1", "ln_invest_cnt_L1",
        "early_deal_ratio_L1", "broad_early_ratio_L1",
        "ln_pgdp", "sec_ratio", "sci_ratio", "fdi_dep", "fin_depth", "ln_pop",
    ]
    for col in winsorise_cols:
        vals = [r.get(col) for r in rows_list]
        wins = winsorize(vals)
        for r, w in zip(rows_list, wins):
            r[col] = w

    # ── Output CSV ────────────────────────────────────────────────────────────
    fieldnames = [
        "city", "province", "year",
        "ln_invg", "ln_umg", "ln_inva", "ln_total_grant", "inv_share",
        "fiscal_gap", "fiscal_gap_L1",
        "debt_ratio", "ln_debt_ratio", "ln_debt_ratio_L1",
        "invest_amt", "invest_cnt",
        "ln_invest_amt", "ln_invest_cnt",
        "ln_invest_amt_L1", "ln_invest_cnt_L1",
        "early_deal_ratio", "early_deal_ratio_L1",
        "broad_early_ratio", "broad_early_ratio_L1",
        "ln_pgdp", "sec_ratio", "sci_ratio", "fdi_dep", "fin_depth", "ln_pop",
        "market_index", "fiscal_trans",
    ]

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows_list:
            writer.writerow({k: ("" if r.get(k) is None else r[k]) for k in fieldnames})

    print(f"\n  Saved: {OUT_CSV}")
    print(f"  Rows: {len(rows_list)}")

    # Summary stats
    n_cities = len({r["city"] for r in rows_list})
    years = sorted({r["year"] for r in rows_list})
    print(f"  Cities: {n_cities}")
    print(f"  Years: {min(years)}-{max(years)}")

    # Count non-missing for key vars
    for col in ["fiscal_gap_L1", "ln_debt_ratio_L1", "ln_invest_amt_L1", "early_deal_ratio_L1"]:
        n_obs = sum(1 for r in rows_list if r.get(col) != "" and r.get(col) is not None)
        print(f"  N({col}): {n_obs}")


if __name__ == "__main__":
    main()
