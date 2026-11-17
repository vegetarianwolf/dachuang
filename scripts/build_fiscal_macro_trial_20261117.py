"""Build audited macro inputs for the fiscal/fund trial; never overwrite old panels."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "原始数据打包_20260401"
CITY = RAW / "市级数据"
OUT = ROOT / "面板数据/fiscal_macro_trial_20261117.csv"
AUDIT = ROOT / "实证结果/fiscal_fund_trial_20261117/macro_audit.json"
PANEL = ROOT / "面板数据/地级市总面板_2015_2024_英文版.csv"
FISCAL = CITY / "2000-2024年290+地级市财政收支压力/2000-2024年290+地级市财政收支压力.xlsx"
DEBT = CITY / "地方债务/全国地方债务余额(省级+地级市)2006-2023/地级市/整合.csv"
PATDIR = RAW / "CNRDS专利数据包/各省市创新专利情况"
PATAPPLY = PATDIR / "各省市专利申请情况/各省市专利申请情况.csv"
PATGRANT = PATDIR / "各省市专利获得情况/各省市专利获得情况.csv"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    old = pd.read_csv(PANEL)
    assert not old.duplicated(["city", "year"]).any()
    cities = sorted(old.city.unique())
    lookup = {c: c for c in cities}
    for city in cities:
        if city.endswith("市"):
            lookup[city[:-1]] = city
    lookup.update({"襄樊": "襄阳市", "襄樊市": "襄阳市", "哈密\u200b\u200b": "哈密市", "儋州市（含洋浦）": "儋州市", "恩施州": "恩施土家族苗族自治州", "吐鲁番地区": "吐鲁番市", "哈密地区": "哈密市", "山南地区": "山南市", "海东地区": "海东市", "林芝地区": "林芝市", "那曲地区": "那曲市", "毕节地区": "毕节市", "铜仁地区": "铜仁市"})

    def match_city(value: object) -> str | None:
        return lookup.get(str(value).strip().replace(" ", ""))

    inputs = [PANEL, FISCAL, DEBT, PATAPPLY, PATGRANT]
    data = pd.MultiIndex.from_product([cities, range(2014, 2025)], names=["city", "year"]).to_frame(index=False)
    fiscal = pd.read_excel(FISCAL)
    revenue = "一般公共\n预算收入\n(万元)"
    spending = "一般公共预\n算支出\n(万元)"
    ratio = fiscal[revenue] / fiscal[spending].where(fiscal[spending] > 0)
    ratio_error = (ratio - fiscal["财政收支压力"]).abs().max()
    assert ratio_error < 1e-10
    fiscal["city"] = fiscal["城市"].map(match_city)
    fiscal["year"] = fiscal["年份"]
    fiscal["fiscal_selfsuff"] = ratio
    fiscal["fiscal_gap"] = 1 - ratio
    fiscal["fiscal_revenue_10k"] = fiscal[revenue]
    fiscal["fiscal_expenditure_10k"] = fiscal[spending]
    fiscal["province"] = fiscal["省份"]
    fiscal["city_code"] = fiscal["城市代码"]
    fcols = ["city", "year", "province", "city_code", "fiscal_gap", "fiscal_selfsuff", "fiscal_revenue_10k", "fiscal_expenditure_10k"]
    fiscal = fiscal.loc[fiscal.city.notna(), fcols]
    assert not fiscal.duplicated(["city", "year"]).any()
    data = data.merge(fiscal, on=["city", "year"], how="left", validate="one_to_one")

    debt = pd.read_csv(DEBT)
    # Debt table also contains provincial entries such as 吉林; retain explicit city labels.
    debt_city_lookup = {c: c for c in cities}
    debt_city_lookup.update({"襄樊市": "襄阳市", "哈密\u200b\u200b": "哈密市"})
    debt["city"] = debt["城市"].map(lambda v: debt_city_lookup.get(str(v).strip()))
    debt["debt_ratio"] = pd.to_numeric(debt["负债率(%)"], errors="coerce") / 100
    debt["debt_gdp_ratio"] = pd.to_numeric(debt["债务负担(%)"], errors="coerce") / 100
    debt["bond_total_100m"] = pd.to_numeric(debt["总计-债券余额(亿)"], errors="coerce")
    debt["debt_source_revenue_100m"] = pd.to_numeric(debt["公共财政收入(亿)"], errors="coerce")
    dcols = ["city", "year", "debt_ratio", "debt_gdp_ratio", "bond_total_100m", "debt_source_revenue_100m"]
    debt = debt.loc[debt.city.notna(), dcols]
    assert not debt.duplicated(["city", "year"]).any()
    positive_revenue = debt.debt_source_revenue_100m.where(debt.debt_source_revenue_100m > 0)
    debt_ratio_error = (debt.debt_ratio - debt.bond_total_100m / positive_revenue).abs()
    data = data.merge(debt, on=["city", "year"], how="left", validate="one_to_one")

    def read_macro(name: str, column: str, unit: str) -> pd.DataFrame:
        path = CITY / name
        inputs.append(path)
        raw = pd.read_csv(path, header=None, dtype=str)
        assert set(raw.iloc[4, 1:].dropna()) == {unit}
        records = []
        for j in range(1, raw.shape[1]):
            city = match_city(raw.iat[2, j])
            if city is None:
                continue
            for i in range(raw.shape[0]):
                year = str(raw.iat[i, 0])
                if not (len(year) == 4 and year.isdigit() and 2014 <= int(year) <= 2024):
                    continue
                records.append({"city": city, "year": int(year), column: pd.to_numeric(raw.iat[i, j], errors="coerce")})
        table = pd.DataFrame(records)
        assert not table.duplicated(["city", "year"]).any()
        return table

    for name, column, unit in [
        ("地级市总GDP.csv", "gdp_billion_rmb", "十亿人民币"),
        ("地级市第二产业.csv", "secondary_billion_rmb", "十亿人民币"),
        ("财政支出：科学：地级市.csv", "scitech_million_rmb", "百万人民币"),
    ]:
        data = data.merge(read_macro(name, column, unit), on=["city", "year"], how="left", validate="one_to_one")
    data["ln_gdp"] = np.log(data.gdp_billion_rmb.where(data.gdp_billion_rmb > 0))
    data["secondary_share"] = data.secondary_billion_rmb / data.gdp_billion_rmb.where(data.gdp_billion_rmb > 0)
    data["ln_scitech"] = np.log1p(data.scitech_million_rmb.where(data.scitech_million_rmb >= 0))
    assert data.secondary_share.dropna().between(0, 1).all()

    patent_cols = ["city", "year", "pat_invent_apply", "pat_invent_grant", "pat_apply_total"]
    data = data.merge(old[patent_cols], on=["city", "year"], how="left", validate="one_to_one")
    for raw, log in [("pat_invent_apply", "ln_pat_apply"), ("pat_invent_grant", "ln_pat_grant"), ("pat_apply_total", "ln_pat_apply_total")]:
        assert data[raw].dropna().ge(0).all()
        data[log] = np.log1p(data[raw])

    # Confirm every inherited invention count against the raw CNRDS tables.
    patent_audit = {}
    for path, source, target in [(PATAPPLY, "Inva", "pat_invent_apply"), (PATGRANT, "Invg", "pat_invent_grant")]:
        raw = pd.read_csv(path)
        raw["year"] = pd.to_numeric(raw.Year, errors="coerce")
        raw["city"] = raw.Pftn.map(match_city)
        municipality = raw.Prvn.isin(["北京市", "天津市", "上海市", "重庆市"])
        raw.loc[municipality & raw.city.isna(), "city"] = raw.loc[municipality & raw.city.isna(), "Prvn"].map(match_city)
        raw["source_count"] = pd.to_numeric(raw[source], errors="coerce")
        raw = raw[raw.city.notna() & raw.year.between(2015, 2024)]
        raw = raw.groupby(["city", "year"], as_index=False).source_count.sum(min_count=1)
        check = old[["city", "year", target]].merge(raw, on=["city", "year"], how="left", validate="one_to_one")
        missing_source = int((check[target].notna() & check.source_count.isna()).sum())
        unequal = int((check[target].notna() & check.source_count.notna() & check[target].ne(check.source_count)).sum())
        patent_audit[target] = {"nonmissing_panel": int(check[target].notna().sum()), "missing_raw_match": missing_source, "unequal_count": unequal}
        assert missing_source == 0 and unequal == 0, patent_audit

    check = data[data.year >= 2015].merge(old[["city", "year", "gdp"]], on=["city", "year"], validate="one_to_one")
    restored = check.gdp.isna() & check.gdp_billion_rmb.notna()
    annual = data.groupby("year")
    pivot = data.pivot(index="city", columns="year", values="pat_invent_apply")
    ratio24 = pivot[2024] / pivot[2023]
    totals = annual[["pat_invent_apply", "pat_invent_grant", "pat_apply_total"]].sum(min_count=1)
    audit = {
        "city_universe": str(PANEL.relative_to(ROOT)),
        "n_cities": len(cities), "n_rows": len(data), "years": [2014, 2024],
        "inputs_sha256": {str(path.relative_to(ROOT)): digest(path) for path in inputs},
        "fiscal_definition": {"source_label": "财政收支压力", "actual_source_formula": "revenue / expenditure", "analysis_formula": "fiscal_gap = 1 - revenue / expenditure", "raw_valid_rows": int(ratio.notna().sum()), "max_formula_error": float(ratio_error), "input_imputation": "none in this script; upstream imputation status undocumented"},
        "debt_definition": {"debt_ratio": "(local-government bonds + LGFV bonds) / public fiscal revenue; source percent divided by 100", "debt_gdp_ratio": "source debt burden percent divided by 100", "ratio_vs_source_numerator_max_abs_difference": float(debt_ratio_error.max()), "missing_to_zero": False, "calendar_lags": "to be constructed by exact city-year joins downstream"},
        "controls": {"ln_gdp": "ln(GDP in billion RMB), positive observations", "secondary_share": "secondary value added / GDP, both billion RMB", "ln_scitech": "ln(1 + fiscal science expenditure in million RMB)", "constant_gdp_unit_rescaling": "ln(c*GDP) = ln(GDP)+ln(c); additive constant absorbed by fixed effects", "population": "excluded from primary controls: source contains transcription/mapping anomalies", "gdp_restored_city_years": int(restored.sum()), "gdp_restored_cities": sorted(check.loc[restored, "city"].unique().tolist()), "restoration_rule": "match source city names against explicit existing-panel full and bare municipal names; do not treat bare names ending in 州 as autonomous prefecture names"},
        "patent_validation": patent_audit,
        "patent_outcomes": {"ln_pat_apply": "ln(1 + invention applications)", "ln_pat_grant": "ln(1 + invention grants)", "2014": "missing: inherited panel starts in 2015", "annual_totals": {str(int(y)): {k: (float(v) if pd.notna(v) else None) for k, v in row.items()} for y, row in totals.iterrows()}, "2024_to_2023_city_application_ratio_median": float(ratio24.median()), "cities_below_0_8_in_2024": int((ratio24 < .8).sum()), "interpretation": "2024 application counts decline broadly while invention grants rise; source completeness/publication lag is not documented. Keep outcome<=2023 primary and report inclusion of 2024 separately."},
        "nonmissing_by_year": {str(int(y)): {k: int(v) for k, v in row.items()} for y, row in annual[["fiscal_gap", "debt_ratio", "ln_gdp", "secondary_share", "ln_scitech", "ln_pat_apply", "ln_pat_grant"]].count().iterrows()},
        "no_interpolation_or_winsorization": True,
    }
    assert not data.duplicated(["city", "year"]).any()
    data = data.sort_values(["city", "year"])
    OUT.parent.mkdir(exist_ok=True, parents=True)
    AUDIT.parent.mkdir(exist_ok=True, parents=True)
    data.to_csv(OUT, index=False, encoding="utf-8-sig")
    audit["output_sha256"] = digest(OUT)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "audit": str(AUDIT.relative_to(ROOT)), "rows": len(data), "columns": data.columns.tolist(), "gdp_restored": int(restored.sum())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
