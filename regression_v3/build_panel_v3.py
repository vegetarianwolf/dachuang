# -*- coding: utf-8 -*-
"""
Build comprehensive city-year panel for regression analysis (v3).

Follows 实证方案.md: Y(patents) + X(fiscal pressure) + M(fund mechanisms) + Z(controls)
+ heterogeneity variables (marketization, fiscal transparency).

Output: regression_v3/panel_v3.csv
"""

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUTDIR = BASE / "regression_v3"
OUTDIR.mkdir(parents=True, exist_ok=True)
OUT = OUTDIR / "panel_v3.csv"

YEAR_MIN, YEAR_MAX = 2010, 2023

# Municipalities: Pftn is empty in CNRDS, use Prvn
MUNICIPALITIES = {"北京", "天津", "上海", "重庆"}

# Province-to-region mapping for heterogeneity
EAST = {"北京", "天津", "河北", "辽宁", "上海", "江苏", "浙江", "福建", "山东", "广东", "海南"}
CENTRAL = {"山西", "吉林", "黑龙江", "安徽", "江西", "河南", "湖北", "湖南"}
# Everything else is West

# Sub-provincial cities
SUB_PROVINCIAL = {"南京", "武汉", "沈阳", "广州", "西安", "成都", "杭州", "济南", "哈尔滨", "长春",
                  "大连", "青岛", "深圳", "厦门", "宁波"}


def clean_city(name):
    s = (name or "").strip()
    s = s.replace("中国", "").replace(":", "").replace("：", "")
    for suf in ["自治区", "特别行政区", "省", "市", "地区", "盟"]:
        s = s.replace(suf, "")
    s = re.sub(r"\s+", "", s)
    return s


def clean_province(name):
    s = (name or "").strip()
    for suf in ["省", "市", "自治区", "特别行政区", "壮族", "回族", "维吾尔"]:
        s = s.replace(suf, "")
    s = re.sub(r"\s+", "", s)
    return s


def to_float(s):
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("，", "")
    if t in {"", "--", "NA", "N/A", "nan", "NaN", "未披露"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


# ============================================================================
# CEIC wide-table parser
# ============================================================================
def parse_ceic_wide(path):
    """Parse CEIC wide CSV -> {(clean_city, year): value}."""
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rows = list(csv.reader(f))
    if len(rows) < 4:
        return {}

    header = rows[0]
    subnation = rows[2] if len(rows) > 2 else []

    # Find first data row (starts with 4-digit year)
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
            if val is not None:
                result[(city, year)] = val
    return result


# ============================================================================
# year_indicator_two_line parser (常住人口, 实际利用外资, 金融机构贷款余额)
# ============================================================================
def parse_year_indicator(path: Path) -> dict[tuple[str, int], float]:
    """Parse year-indicator-two-line CSV -> {(clean_city, year): value}.
    Row 1: blank, 1990年, 1991年, ...
    Row 2: blank, indicator, indicator, ...
    Row 3+: cityName, val, val, ...
    """
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        return {}

    years_row = rows[0]
    years = []
    for cell in years_row[1:]:
        m = re.search(r"(\d{4})", (cell or "").strip())
        years.append(int(m.group(1)) if m else None)

    result: dict[tuple[str, int], float] = {}
    for r in rows[2:]:  # skip header two rows
        if not r or not r[0].strip():
            continue
        city = clean_city(r[0])
        if not city:
            continue
        for idx, yr in enumerate(years):
            if yr is None:
                continue
            col = idx + 1
            val = to_float(r[col] if col < len(r) else None)
            if val is not None:
                result[(city, yr)] = val
    return result


# ============================================================================
# CNRDS patent parsers
# ============================================================================
def parse_cnrds_patent(path: Path, value_cols: list[str]) -> dict[tuple[str, int], dict[str, float]]:
    """Parse CNRDS patent CSV -> {(clean_city, year): {col: val}}. Handles municipalities."""
    agg: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rd = csv.DictReader(f)
        skip_first = True
        for row in rd:
            # Second row in DictReader is the Chinese header => skip
            if skip_first:
                # Check if this row is the Chinese description row
                yr_val = (row.get("Year") or "").strip()
                if not re.fullmatch(r"\d{4}", yr_val):
                    skip_first = False
                    continue
                skip_first = False

            yr_val = (row.get("Year") or "").strip()
            if not re.fullmatch(r"\d{4}", yr_val):
                continue
            year = int(yr_val)

            pftn = (row.get("Pftn") or "").strip()
            prvn = (row.get("Prvn") or "").strip()

            # Municipalities: Pftn may be empty => use Prvn
            if not pftn or pftn == "":
                prvn_clean = clean_province(prvn)
                if prvn_clean in {clean_city(m) for m in MUNICIPALITIES}:
                    city = prvn_clean
                else:
                    continue
            else:
                city = clean_city(pftn)

            if not city:
                continue

            for col in value_cols:
                v = to_float(row.get(col))
                if v is not None:
                    agg[(city, year)][col] += v

    return {k: dict(v) for k, v in agg.items()}


# ============================================================================
# Fund investment parser
# ============================================================================
def parse_fund_invest(path: Path) -> dict[tuple[str, int], dict]:
    """Parse 城市_投资统计_分年份_2000-2024.csv -> {(clean_city, year): metrics}."""
    result: dict[tuple[str, int], dict] = {}
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rd = csv.DictReader(f)
        for row in rd:
            city = clean_city(row.get("城市") or "")
            yr = to_float(row.get("年份"))
            if not city or yr is None:
                continue
            year = int(yr)

            def pct_to_float(s):
                if s is None:
                    return None
                s = str(s).strip()
                if s in {"", "--", "nan"}:
                    return None
                s = s.replace("%", "")
                try:
                    return float(s) / 100.0
                except ValueError:
                    return None

            result[(city, year)] = {
                "invest_cnt": to_float(row.get("总投资次数")) or 0.0,
                "invest_amt": to_float(row.get("总投资额_百万元")) or 0.0,
                "early_deal_ratio": to_float(row.get("早期投资次数占比")),
                "early_amt_ratio": to_float(row.get("早期投资额占比")),
                "broad_early_ratio": to_float(row.get("广义早期投资次数占比")),
                "broad_early_amt_ratio": to_float(row.get("广义早期投资额占比")),
            }
    return result


# ============================================================================
# Marketization index parse
# ============================================================================
def parse_marketization(path: Path) -> dict[tuple[str, int], float]:
    """{(clean_province, year): market_index}"""
    result = {}
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rd = csv.DictReader(f)
        for row in rd:
            prov = clean_province(row.get("省份") or "")
            yr = to_float(row.get("year"))
            mkt = to_float(row.get("market"))
            if prov and yr is not None and mkt is not None:
                result[(prov, int(yr))] = mkt
    return result


# ============================================================================
# Fiscal transparency parser
# ============================================================================
def parse_fiscal_transparency(path: Path) -> dict[tuple[str, int], float]:
    """{(clean_city, year): transparency_score}"""
    result = {}
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rd = csv.DictReader(f)
        for row in rd:
            city = clean_city(row.get("城市") or "")
            if not city:
                continue
            for col_name, val_str in row.items():
                m = re.search(r"(\d{4})", col_name)
                if m:
                    yr = int(m.group(1))
                    val = to_float(val_str)
                    if val is not None:
                        result[(city, yr)] = val
    return result


# ============================================================================
# Province lookup from CNRDS
# ============================================================================
def build_city_province_map(path: Path) -> dict[str, str]:
    """Build city -> province mapping from CNRDS patent data."""
    mapping = {}
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        rd = csv.DictReader(f)
        for row in rd:
            prvn = clean_province((row.get("Prvn") or "").strip())
            pftn = clean_city((row.get("Pftn") or "").strip())
            if prvn and pftn:
                mapping[pftn] = prvn
    # Add municipalities
    for m in MUNICIPALITIES:
        mc = clean_city(m)
        mapping[mc] = mc
    return mapping


# ============================================================================
# Winsorize
# ============================================================================
def winsorize(values: list[float], lower=0.01, upper=0.99) -> tuple[float, float]:
    sv = sorted(values)
    n = len(sv)
    lo_idx = max(0, int(n * lower))
    hi_idx = min(n - 1, int(n * upper))
    return sv[lo_idx], sv[hi_idx]


def main():
    print("=== Building Panel v3 ===")

    # --- Load all data sources ---
    print("Loading patent data (granted + applied)...")
    patent_granted = parse_cnrds_patent(
        BASE / "CNRDS专利数据包" / "各省市创新专利情况" / "各省市专利获得情况" / "各省市专利获得情况.csv",
        ["Invg", "Umg", "Desg"]
    )
    patent_applied = parse_cnrds_patent(
        BASE / "CNRDS专利数据包" / "各省市创新专利情况" / "各省市专利申请情况" / "各省市专利申请情况.csv",
        ["Inva", "Uma", "Desa"]
    )
    print(f"  Patent granted obs: {len(patent_granted)}, applied: {len(patent_applied)}")

    print("Loading CEIC wide tables...")
    fiscal_rev = parse_ceic_wide(BASE / "地级市财政收入.csv")
    fiscal_exp = parse_ceic_wide(BASE / "地级市财政支出.csv")
    gdp_total = parse_ceic_wide(BASE / "地级市总GDP.csv")
    gdp_pc = parse_ceic_wide(BASE / "地级市人均GDP.csv")
    second_ind = parse_ceic_wide(BASE / "地级市第二产业.csv")
    sci_exp = parse_ceic_wide(BASE / "财政支出：科学：地级市.csv")
    debt = parse_ceic_wide(BASE / "地方政府债务：地级市：余额.csv")
    print(f"  fiscal_rev: {len(fiscal_rev)}, fiscal_exp: {len(fiscal_exp)}, debt: {len(debt)}")

    print("Loading year-indicator files...")
    pop = parse_year_indicator(BASE / "常住人口.csv")
    fdi = parse_year_indicator(BASE / "实际利用外资.csv")
    loan = parse_year_indicator(BASE / "金融机构贷款余额.csv")
    print(f"  pop: {len(pop)}, fdi: {len(fdi)}, loan: {len(loan)}")

    print("Loading fund investment data...")
    fund_inv = parse_fund_invest(BASE / "政府引导基金整合数据" / "城市_投资统计_分年份_2000-2024.csv")
    print(f"  Fund investment obs: {len(fund_inv)}")

    print("Loading heterogeneity variables...")
    mkt_index = parse_marketization(BASE / "1997-2024年市场化指数和各分项指数 的副本.csv")
    fiscal_trans = parse_fiscal_transparency(BASE / "市级政府财政透明度（2013-2024年） 的副本.csv")
    print(f"  Marketization: {len(mkt_index)}, fiscal transparency: {len(fiscal_trans)}")

    # Build city->province mapping
    city_prov = build_city_province_map(
        BASE / "CNRDS专利数据包" / "各省市创新专利情况" / "各省市专利获得情况" / "各省市专利获得情况.csv"
    )

    # --- Collect all cities ---
    all_cities = set()
    for k in fiscal_rev:
        all_cities.add(k[0])
    for k in patent_granted:
        all_cities.add(k[0])
    print(f"Total unique cities: {len(all_cities)}")

    # --- Build raw panel ---
    print("Assembling raw panel...")
    raw_rows = []
    for city in sorted(all_cities):
        for year in range(YEAR_MIN, YEAR_MAX + 1):
            k = (city, year)
            kp = (city, year - 1)  # for lags

            # Y: patent variables
            pg = patent_granted.get(k, {})
            pa = patent_applied.get(k, {})
            invg = pg.get("Invg")
            umg = pg.get("Umg")
            desg = pg.get("Desg")
            inva = pa.get("Inva")

            # X: fiscal pressure (contemporaneous, will lag below)
            rev = fiscal_rev.get(k)
            exp = fiscal_exp.get(k)
            dbt = debt.get(k)

            rev_lag = fiscal_rev.get(kp)
            exp_lag = fiscal_exp.get(kp)
            dbt_lag = debt.get(kp)

            # Compute fiscal gap (contemporaneous)
            fiscal_gap = None
            if exp is not None and rev is not None and exp > 0:
                fiscal_gap = (exp - rev) / exp

            fiscal_gap_lag = None
            if exp_lag is not None and rev_lag is not None and exp_lag > 0:
                fiscal_gap_lag = (exp_lag - rev_lag) / exp_lag

            # Debt ratio
            debt_ratio_lag = None
            if dbt_lag is not None and rev_lag is not None and rev_lag > 0 and dbt_lag > 0:
                debt_ratio_lag = math.log(dbt_lag / rev_lag)

            # M: fund mechanisms (lag)
            fi_lag = fund_inv.get(kp, {})
            invest_cnt_lag = fi_lag.get("invest_cnt", 0.0) if fi_lag else 0.0
            invest_amt_lag = fi_lag.get("invest_amt", 0.0) if fi_lag else 0.0
            early_deal_ratio_lag = fi_lag.get("early_deal_ratio") if fi_lag else None
            early_amt_ratio_lag = fi_lag.get("early_amt_ratio") if fi_lag else None
            broad_early_ratio_lag = fi_lag.get("broad_early_ratio") if fi_lag else None

            # Z: control variables
            gpc = gdp_pc.get(k)
            sec = second_ind.get(k)
            gdp = gdp_total.get(k)
            sci = sci_exp.get(k)
            population = pop.get(k)
            foreign = fdi.get(k)
            loans = loan.get(k)

            # Province for heterogeneity
            province = city_prov.get(city, "")

            # Marketization index (province-level)
            mkt = mkt_index.get((province, year))

            # Fiscal transparency
            ft = fiscal_trans.get((city, year))

            # Region
            if province in {clean_province(p) for p in EAST}:
                region = "东部"
            elif province in {clean_province(p) for p in CENTRAL}:
                region = "中部"
            else:
                region = "西部"

            # Admin level
            is_municipality = city in {clean_city(m) for m in MUNICIPALITIES}
            is_sub_provincial = city in {clean_city(sp) for sp in SUB_PROVINCIAL}
            high_admin = 1 if (is_municipality or is_sub_provincial) else 0

            row = {
                "city": city,
                "province": province,
                "year": year,
                "region": region,
                "high_admin": high_admin,
                # Y
                "invg": invg,
                "umg": umg,
                "desg": desg,
                "inva": inva,
                # X (lagged)
                "fiscal_gap_L1": fiscal_gap_lag,
                "ln_debt_ratio_L1": debt_ratio_lag,
                # M (lagged)
                "invest_cnt_L1": invest_cnt_lag,
                "invest_amt_L1": invest_amt_lag,
                "early_deal_ratio_L1": early_deal_ratio_lag,
                "early_amt_ratio_L1": early_amt_ratio_lag,
                "broad_early_ratio_L1": broad_early_ratio_lag,
                # Z (contemporaneous)
                "gdp_pc": gpc,
                "sec_ind": sec,
                "gdp_total": gdp,
                "sci_exp": sci,
                "fiscal_exp": exp,
                "pop": population,
                "fdi": foreign,
                "loan": loans,
                # Heterogeneity
                "market_index": mkt,
                "fiscal_trans": ft,
            }
            raw_rows.append(row)

    print(f"Raw panel rows (all city-years): {len(raw_rows)}")

    # --- Compute derived variables ---
    for r in raw_rows:
        # ln(1+Y)
        r["ln_invg"] = math.log(r["invg"] + 1) if r["invg"] is not None else None
        r["ln_umg"] = math.log(r["umg"] + 1) if r["umg"] is not None else None
        r["ln_inva"] = math.log(r["inva"] + 1) if r["inva"] is not None else None

        # Total grant
        if r["invg"] is not None and r["umg"] is not None and r["desg"] is not None:
            total = r["invg"] + r["umg"] + r["desg"]
            r["ln_total_grant"] = math.log(total + 1)
            r["inv_share"] = r["invg"] / total if total > 0 else None
        else:
            r["ln_total_grant"] = None
            r["inv_share"] = None

        # ln(pgdp)
        r["ln_pgdp"] = math.log(r["gdp_pc"]) if r["gdp_pc"] is not None and r["gdp_pc"] > 0 else None

        # sec_ratio
        r["sec_ratio"] = r["sec_ind"] / r["gdp_total"] if (
            r["sec_ind"] is not None and r["gdp_total"] is not None and r["gdp_total"] > 0
        ) else None

        # sci_ratio
        r["sci_ratio"] = r["sci_exp"] / r["fiscal_exp"] if (
            r["sci_exp"] is not None and r["fiscal_exp"] is not None and r["fiscal_exp"] > 0
        ) else None

        # fdi_dep
        r["fdi_dep"] = r["fdi"] / r["gdp_total"] if (
            r["fdi"] is not None and r["gdp_total"] is not None and r["gdp_total"] > 0
        ) else None

        # fin_depth
        r["fin_depth"] = r["loan"] / r["gdp_total"] if (
            r["loan"] is not None and r["gdp_total"] is not None and r["gdp_total"] > 0
        ) else None

        # ln_pop
        r["ln_pop"] = math.log(r["pop"]) if r["pop"] is not None and r["pop"] > 0 else None

        # ln fund investment (lagged)
        r["ln_invest_amt_L1"] = math.log(r["invest_amt_L1"] + 1) if r["invest_amt_L1"] is not None else None
        r["ln_invest_cnt_L1"] = math.log(r["invest_cnt_L1"] + 1) if r["invest_cnt_L1"] is not None else None

    # --- Winsorize continuous variables at 1%/99% ---
    winsorize_vars = [
        "ln_invg", "ln_umg", "ln_inva", "ln_total_grant", "inv_share",
        "fiscal_gap_L1", "ln_debt_ratio_L1",
        "ln_pgdp", "sec_ratio", "sci_ratio", "fdi_dep", "fin_depth", "ln_pop",
        "ln_invest_amt_L1", "ln_invest_cnt_L1",
        "early_deal_ratio_L1", "early_amt_ratio_L1", "broad_early_ratio_L1",
    ]
    for var in winsorize_vars:
        vals = [r[var] for r in raw_rows if r[var] is not None]
        if len(vals) < 10:
            continue
        lo, hi = winsorize(vals)
        for r in raw_rows:
            if r[var] is not None:
                r[var] = max(lo, min(hi, r[var]))

    # --- City numeric ID for FE ---
    all_city_names = sorted({r["city"] for r in raw_rows})
    city_id_map = {c: i + 1 for i, c in enumerate(all_city_names)}
    for r in raw_rows:
        r["city_id"] = city_id_map[r["city"]]

    # --- Output ---
    out_cols = [
        "city", "city_id", "province", "year", "region", "high_admin",
        # Y
        "ln_invg", "ln_umg", "ln_inva", "ln_total_grant", "inv_share",
        # X
        "fiscal_gap_L1", "ln_debt_ratio_L1",
        # M
        "ln_invest_amt_L1", "ln_invest_cnt_L1",
        "early_deal_ratio_L1", "early_amt_ratio_L1", "broad_early_ratio_L1",
        # Z
        "ln_pgdp", "sec_ratio", "sci_ratio", "fdi_dep", "fin_depth", "ln_pop",
        # Heterogeneity
        "market_index", "fiscal_trans",
    ]

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(raw_rows, key=lambda x: (x["city"], x["year"])):
            out_row = {}
            for col in out_cols:
                val = r.get(col)
                if val is None:
                    out_row[col] = ""
                elif isinstance(val, float):
                    out_row[col] = f"{val:.10f}"
                else:
                    out_row[col] = val
            w.writerow(out_row)

    # Stats
    total = len(raw_rows)
    has_y = sum(1 for r in raw_rows if r["ln_invg"] is not None)
    has_x1 = sum(1 for r in raw_rows if r["fiscal_gap_L1"] is not None)
    has_x2 = sum(1 for r in raw_rows if r["ln_debt_ratio_L1"] is not None)
    has_yz = sum(1 for r in raw_rows if r["ln_invg"] is not None and r["fiscal_gap_L1"] is not None and r["ln_pgdp"] is not None)

    print(f"\n=== Panel Summary ===")
    print(f"Total rows: {total}")
    print(f"With Y (ln_invg): {has_y}")
    print(f"With X1 (fiscal_gap_L1): {has_x1}")
    print(f"With X2 (ln_debt_ratio_L1): {has_x2}")
    print(f"With Y+X1+controls: {has_yz}")
    print(f"Output: {OUT}")


if __name__ == "__main__":
    main()
