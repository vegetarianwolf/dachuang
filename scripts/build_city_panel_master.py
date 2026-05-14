import os
import re
from typing import Callable

import numpy as np
import pandas as pd


ROOT = "."
PANEL_DIR = os.path.join(ROOT, "dachuang", "面板数据")
RAW_DIR = os.path.join(ROOT, "dachuang", "原始数据打包_20260401")
CITY_DATA_DIR = os.path.join(RAW_DIR, "市级数据")
PATENT_DIR = os.path.join(RAW_DIR, "CNRDS专利数据包", "各省市创新专利情况")
DEBT_CITY_DIR = os.path.join(CITY_DATA_DIR, "地方债务", "全国地方债务余额(省级+地级市)2006-2023", "地级市")
STAGING_DIR = os.path.join(ROOT, "staging_ascii")

DIRECT_MUNICIPALITY_BARE = {"北京", "天津", "上海", "重庆"}
DIRECT_MUNICIPALITY_FULL = {f"{name}市" for name in DIRECT_MUNICIPALITY_BARE}
PROVINCE_LEVEL_NAMES = {
    "河北",
    "山西",
    "辽宁",
    "吉林",
    "黑龙江",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "海南",
    "四川",
    "贵州",
    "云南",
    "陕西",
    "甘肃",
    "青海",
    "台湾",
    "内蒙古",
    "广西",
    "西藏",
    "宁夏",
    "新疆",
    "香港",
    "澳门",
}
CITY_ALIAS_MAP = {
    "儋州市（含洋浦）": "儋州市",
    "襄樊市": "襄阳市",
    "恩施州": "恩施土家族苗族自治州",
    "吐鲁番地区": "吐鲁番市",
    "哈密地区": "哈密市",
    "山南地区": "山南市",
    "海东地区": "海东市",
    "林芝地区": "林芝市",
    "那曲地区": "那曲市",
    "毕节地区": "毕节市",
    "铜仁地区": "铜仁市",
}
PATENT_AGGREGATE_AREAS = {"省直辖县级行政区划", "自治区直辖县级行政区划"}


def find_file(name: str, start: str = ROOT) -> str:
    for current_root, _, files in os.walk(start):
        for file_name in files:
            if file_name == name:
                return os.path.join(current_root, file_name)
    raise FileNotFoundError(name)


def normalize_city_alias(text: str) -> str:
    return CITY_ALIAS_MAP.get(text, text)


def standardize_city(city: str) -> str | None:
    if city is None or (isinstance(city, float) and np.isnan(city)):
        return None
    text = str(city).strip().replace(" ", "")
    text = text.replace("哈密​​", "哈密市")
    if text in {"", "nan", "--", "未披露"}:
        return None
    text = normalize_city_alias(text)
    if text in DIRECT_MUNICIPALITY_BARE:
        return f"{text}市"
    if text in DIRECT_MUNICIPALITY_FULL:
        return text
    if text in PROVINCE_LEVEL_NAMES or text.endswith(("省", "自治区", "特别行政区")):
        return text
    if text.endswith(("市", "州", "地区", "盟", "区", "县", "旗")):
        return text
    if re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", text):
        return f"{text}市"
    return text


def extract_patent_city(province: str, prefecture: str) -> str | None:
    province_text = standardize_city(province)
    prefecture_text = "" if prefecture is None else str(prefecture).strip().replace(" ", "")
    if prefecture_text in {"", "nan", "--", "未披露"}:
        prefecture_text = ""
    prefecture_text = normalize_city_alias(prefecture_text)

    if prefecture_text in PATENT_AGGREGATE_AREAS:
        if province_text:
            return f"{province_text}_{prefecture_text}"
        return prefecture_text

    if prefecture_text in {"市辖区", "城区"} and province_text in DIRECT_MUNICIPALITY_FULL:
        return province_text
    if prefecture_text:
        return standardize_city(prefecture_text)
    if province_text in DIRECT_MUNICIPALITY_FULL:
        return province_text
    return None


def add_log1p(df: pd.DataFrame, source_col: str, target_col: str) -> None:
    values = pd.to_numeric(df[source_col], errors="coerce")
    df[target_col] = np.where(values.notna() & (values >= 0), np.log1p(values), np.nan)


def with_lag(df: pd.DataFrame, value_cols: list[str], city_col: str = "城市", year_col: str = "年份") -> pd.DataFrame:
    df = df.sort_values([city_col, year_col]).copy()
    for col in value_cols:
        df[f"{col}_滞后一期"] = df.groupby(city_col)[col].shift(1)
    return df


def read_csv_any(path: str, **kwargs) -> pd.DataFrame:
    if "encoding" not in kwargs:
        kwargs["encoding"] = "utf-8-sig"
    return pd.read_csv(path, **kwargs)


def read_excel_any(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_excel(path, **kwargs)


def load_establishment_panel() -> pd.DataFrame:
    staged = os.path.join(STAGING_DIR, "fund_setup.csv")
    path = staged if os.path.exists(staged) else find_file("市级基金设立规模面板_2015_2025.csv", PANEL_DIR)
    df = read_csv_any(path)
    df = df.rename(
        columns={
            "city": "城市",
            "year": "年份",
            "fund_established_count": "基金当年设立数量",
            "fund_established_scale_rmb_m": "基金当年设立规模_人民币万元",
            "cumulative_fund_established_count": "基金累计设立数量",
            "cumulative_fund_established_scale_rmb_m": "基金累计设立规模_人民币万元",
            "rolling5_fund_established_count": "基金近五年设立数量",
            "rolling5_fund_established_scale_rmb_m": "基金近五年设立规模_人民币万元",
        }
    )
    df["城市"] = df["城市"].map(standardize_city)
    df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
    return df


def load_investment_panel() -> pd.DataFrame:
    staged = os.path.join(STAGING_DIR, "fund_invest.csv")
    panel_path = find_file("市级基金投资事件面板_2015_2024.csv", PANEL_DIR)
    path = panel_path if os.path.exists(panel_path) else staged
    df = read_csv_any(path)
    df = df.rename(
        columns={
            "city": "城市",
            "year": "年份",
            "total_investment_amount_rmb_m": "基金投资总额_人民币万元",
            "total_investment_count": "基金投资事件总数",
            "early_investment_amount_rmb_m": "早期投资金额_人民币万元",
            "early_investment_count": "早期投资事件数",
            "early_investment_amount_share": "早期投资金额占比",
            "early_investment_count_share": "早期投资事件占比",
        }
    )
    df["城市"] = df["城市"].map(standardize_city)
    df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
    return df


def load_social_capital_panel() -> pd.DataFrame:
    staged = os.path.join(STAGING_DIR, "social_capital.csv")
    raw_path = find_file("city_social_capital_panel.csv", CITY_DATA_DIR)
    path = raw_path if os.path.exists(raw_path) else staged
    df = read_csv_any(path)
    df = df.rename(
        columns={
            "city_name": "城市",
            "year": "年份",
            "fund_count": "社会资本口径基金数量",
            "social_amt": "社会资本认缴额",
            "government_amt": "政府认缴额",
            "gp_amt": "GP认缴额",
            "unknown_amt": "未知类型认缴额",
            "total_amt": "基金总认缴额",
            "matched_amt": "已匹配认缴额",
            "social_share_total": "社会资本占总认缴比",
            "government_share_total": "政府出资占总认缴比",
            "social_to_government_ratio": "社会资本撬动效率",
            "matched_share_total": "已匹配认缴额占比",
        }
    )
    df["城市"] = df["城市"].map(standardize_city)
    df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
    return df


def load_patent_panel() -> pd.DataFrame:
    staged_apply = os.path.join(STAGING_DIR, "patent_apply.csv")
    staged_grant = os.path.join(STAGING_DIR, "patent_grant.csv")
    apply_path = staged_apply if os.path.exists(staged_apply) else find_file("各省市专利申请情况.csv", PATENT_DIR)
    grant_path = staged_grant if os.path.exists(staged_grant) else find_file("各省市专利获得情况.csv", PATENT_DIR)
    apply_df = read_csv_any(apply_path)
    grant_df = read_csv_any(grant_path)

    apply_df = apply_df.rename(
        columns={
            "Prvn": "省份",
            "Pftn": "城市",
            "Year": "年份",
            "Inva": "发明申请量",
            "Uma": "实用新型申请量",
            "Desa": "外观设计申请量",
        }
    )
    grant_df = grant_df.rename(
        columns={
            "Prvn": "省份",
            "Pftn": "城市",
            "Year": "年份",
            "Invg": "发明获得量",
            "Umg": "实用新型获得量",
            "Desg": "外观设计获得量",
        }
    )

    # Drop the human-readable description row.
    apply_df = apply_df[pd.to_numeric(apply_df["年份"], errors="coerce").notna()].copy()
    grant_df = grant_df[pd.to_numeric(grant_df["年份"], errors="coerce").notna()].copy()

    apply_df["城市"] = [
        extract_patent_city(province, prefecture)
        for province, prefecture in zip(apply_df["省份"], apply_df["城市"])
    ]
    grant_df["城市"] = [
        extract_patent_city(province, prefecture)
        for province, prefecture in zip(grant_df["省份"], grant_df["城市"])
    ]

    apply_df = apply_df[["城市", "年份", "发明申请量", "实用新型申请量", "外观设计申请量"]].copy()
    grant_df = grant_df[["城市", "年份", "发明获得量", "实用新型获得量", "外观设计获得量"]].copy()

    for df in (apply_df, grant_df):
        df["城市"] = df["城市"].map(standardize_city)
        df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
        df.dropna(subset=["城市"], inplace=True)
        for col in df.columns:
            if col not in {"城市", "年份"}:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        value_cols = [col for col in df.columns if col not in {"城市", "年份"}]
        grouped = (
            df.groupby(["城市", "年份"], as_index=False)[value_cols]
            .sum(min_count=1)
            .reindex(columns=["城市", "年份"] + value_cols)
        )
        df.drop(df.index, inplace=True)
        for col in grouped.columns:
            df[col] = grouped[col].to_numpy()

    df = apply_df.merge(grant_df, on=["城市", "年份"], how="outer")
    df["专利申请总量"] = df[["发明申请量", "实用新型申请量", "外观设计申请量"]].sum(axis=1, min_count=1)
    df["专利获得总量"] = df[["发明获得量", "实用新型获得量", "外观设计获得量"]].sum(axis=1, min_count=1)

    for col in [
        "发明申请量",
        "实用新型申请量",
        "外观设计申请量",
        "发明获得量",
        "实用新型获得量",
        "外观设计获得量",
        "专利申请总量",
        "专利获得总量",
    ]:
        add_log1p(df, col, f"{col}_对数")
    return df


def load_fiscal_pressure_panel() -> pd.DataFrame:
    try:
        staged = os.path.join(STAGING_DIR, "fiscal_pressure.xlsx")
        path = staged if os.path.exists(staged) else find_file("2000-2024年290+地级市财政收支压力.xlsx", RAW_DIR)
        df = read_excel_any(path)
        rename_map = {}
        for col in df.columns:
            text = str(col)
            if text == "城市" or ("地市" in text and "名称" in text):
                rename_map[col] = "城市"
            elif "年份" in text:
                rename_map[col] = "年份"
            elif "财政收支压力" in text:
                rename_map[col] = "财政收支压力"
        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()].copy()
        keep = [c for c in ["城市", "年份", "财政收支压力"] if c in df.columns]
        df = df[keep].copy()
        df["城市"] = df["城市"].map(standardize_city)
        df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
        df["财政收支压力"] = pd.to_numeric(df["财政收支压力"], errors="coerce")
        return with_lag(df, ["财政收支压力"])
    except Exception:
        return pd.DataFrame(columns=["城市", "年份", "财政收支压力", "财政收支压力_滞后一期"])


def load_debt_panel() -> pd.DataFrame:
    staged = os.path.join(STAGING_DIR, "debt_panel.csv")
    path = staged if os.path.exists(staged) else find_file("整合.csv", DEBT_CITY_DIR)
    df = read_csv_any(path)
    df = df.rename(
        columns={
            "城市": "城市",
            "year": "年份",
            "地方政府债-债券余额(亿)": "地方政府债余额_亿",
            "城投债-债券余额(亿)": "城投债余额_亿",
            "总计-债券余额(亿)": "债券余额合计_亿",
            "GDP(亿)": "GDP_债务表_亿",
            "公共财政收入(亿)": "公共财政收入_亿",
            "公共财政支出(亿)": "公共财政支出_亿",
            "债务负担(%)": "债务负担",
            "负债率(%)": "债务压力",
            "财政自给率(%)": "财政自给率",
        }
    )
    keep_cols = [
        "城市",
        "年份",
        "地方政府债余额_亿",
        "城投债余额_亿",
        "债券余额合计_亿",
        "GDP_债务表_亿",
        "公共财政收入_亿",
        "公共财政支出_亿",
        "债务负担",
        "债务压力",
        "财政自给率",
    ]
    df = df[keep_cols].copy()
    df["城市"] = df["城市"].map(standardize_city)
    df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
    for col in keep_cols[2:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return with_lag(df, ["债务负担", "债务压力", "财政自给率"])


def load_fiscal_transparency_panel() -> pd.DataFrame:
    staged = os.path.join(STAGING_DIR, "fiscal_transparency.csv")
    path = staged if os.path.exists(staged) else find_file("市级政府财政透明度（2013-2024年） 的副本.csv", CITY_DATA_DIR)
    df = read_csv_any(path)
    value_cols = [c for c in df.columns if str(c).startswith("财政透明度")]
    long_df = df.melt(id_vars=["城市"], value_vars=value_cols, var_name="年份变量", value_name="政府财政透明度")
    long_df["年份"] = long_df["年份变量"].str.extract(r"(\d{4})").astype("Int64")
    long_df["城市"] = long_df["城市"].map(standardize_city)
    long_df["政府财政透明度"] = pd.to_numeric(long_df["政府财政透明度"], errors="coerce")
    return long_df[["城市", "年份", "政府财政透明度"]]


def load_financing_constraint_panels() -> pd.DataFrame:
    mapping = {
        "sa_index.csv": "地级市SA融资约束均值",
        "fc_index.csv": "地级市FC融资约束均值",
        "kz_index.csv": "地级市KZ融资约束均值",
        "ww_index.csv": "地级市WW融资约束均值",
    }
    merged = None
    for file_name, target in mapping.items():
        staged = os.path.join(STAGING_DIR, file_name)
        path = staged if os.path.exists(staged) else find_file(file_name, CITY_DATA_DIR)
        df = read_csv_any(path)
        city_col = "city_name"
        year_col = "year"
        value_col = "city_index_mean" if "city_index_mean" in df.columns else "city_sa_mean"
        df = df.rename(columns={city_col: "城市", year_col: "年份", value_col: target, "firm_count": f"{target}_样本企业数"})
        keep = ["城市", "年份", target, f"{target}_样本企业数"]
        if "city_index_median" in df.columns:
            df = df.rename(columns={"city_index_median": f"{target}_中位数"})
            keep.append(f"{target}_中位数")
        if "city_sa_median" in df.columns:
            df = df.rename(columns={"city_sa_median": f"{target}_中位数", "city_sa_raw_mean": f"{target}_原值均值"})
            keep.extend([f"{target}_中位数", f"{target}_原值均值"])
        df = df[keep].copy()
        df["城市"] = df["城市"].map(standardize_city)
        df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on=["城市", "年份"], how="outer")
    return merged


def parse_wide_city_table(path: str, value_selector: Callable[[str], bool], value_name: str) -> pd.DataFrame:
    raw = read_csv_any(path, header=None, dtype=str, encoding="utf-8-sig")
    years = raw.iloc[0]
    indicators = raw.iloc[1]
    # Most macro city csvs keep 4 metadata rows after the first two rows.
    data_rows = raw.iloc[5:].reset_index(drop=True)
    data_rows.iloc[:, 0] = data_rows.iloc[:, 0].map(standardize_city)

    long_records = []
    for col in raw.columns[1:]:
        year_text = str(raw.iloc[0, col]).strip()
        ind_text = str(raw.iloc[1, col]).strip()
        if not re.fullmatch(r"\d{4}年", year_text or ""):
            continue
        if not value_selector(ind_text):
            continue
        year = int(year_text[:4])
        for idx in range(len(data_rows)):
            city = data_rows.iat[idx, 0]
            value = data_rows.iat[idx, col]
            if city is None or city == "":
                continue
            long_records.append({"城市": city, "年份": year, value_name: pd.to_numeric(value, errors="coerce")})

    df = pd.DataFrame(long_records)
    if df.empty:
        return pd.DataFrame(columns=["城市", "年份", value_name])
    return df.groupby(["城市", "年份"], as_index=False)[value_name].first()


def parse_simple_wide_year_table(path: str, value_name: str) -> pd.DataFrame:
    raw = read_csv_any(path, header=None, dtype=str, encoding="utf-8-sig")
    # Row 0: year headers, row 1 and beyond: metadata, city data starts after metadata rows.
    year_headers = [str(x).strip() for x in raw.iloc[0].tolist()]
    start_row = 2
    for idx in range(2, len(raw)):
        first_cell = standardize_city(raw.iat[idx, 0])
        if first_cell and first_cell not in {"区域", "次国家", "频率", "单位", "数据来源"}:
            start_row = idx
            break
    city_rows = raw.iloc[start_row:].reset_index(drop=True)
    city_rows.iloc[:, 0] = city_rows.iloc[:, 0].map(standardize_city)
    records = []
    for col_idx in range(1, raw.shape[1]):
        year_text = year_headers[col_idx]
        if not re.fullmatch(r"\d{4}年", year_text or ""):
            continue
        year = int(year_text[:4])
        for row_idx in range(len(city_rows)):
            city = city_rows.iat[row_idx, 0]
            if not city:
                continue
            value = pd.to_numeric(city_rows.iat[row_idx, col_idx], errors="coerce")
            records.append({"城市": city, "年份": year, value_name: value})
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=["城市", "年份", value_name])
    return df.groupby(["城市", "年份"], as_index=False)[value_name].first()


def parse_city_rows_year_columns_table(path: str, value_name: str) -> pd.DataFrame:
    raw = read_csv_any(path, header=None, dtype=str, encoding="utf-8-sig")
    year_headers = [str(x).strip() for x in raw.iloc[0].tolist()]
    city_rows = raw.iloc[2:].reset_index(drop=True)
    city_rows.iloc[:, 0] = city_rows.iloc[:, 0].map(standardize_city)
    records = []
    for row_idx in range(len(city_rows)):
        city = city_rows.iat[row_idx, 0]
        if not city:
            continue
        for col_idx in range(1, raw.shape[1]):
            year_text = year_headers[col_idx]
            if not re.fullmatch(r"\d{4}年", year_text or ""):
                continue
            year = int(year_text[:4])
            value = pd.to_numeric(city_rows.iat[row_idx, col_idx], errors="coerce")
            records.append({"城市": city, "年份": year, value_name: value})
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=["城市", "年份", value_name])
    return df.groupby(["城市", "年份"], as_index=False)[value_name].first()


def parse_time_rows_city_columns_table(path: str, value_name: str) -> pd.DataFrame:
    raw = read_csv_any(path, header=None, dtype=str, encoding="utf-8-sig")
    city_headers = [standardize_city(x) for x in raw.iloc[2].tolist()]
    records = []
    for row_idx in range(len(raw)):
        year_text = str(raw.iat[row_idx, 0]).strip()
        if not re.fullmatch(r"\d{4}", year_text or ""):
            continue
        year = int(year_text)
        for col_idx in range(1, raw.shape[1]):
            city = city_headers[col_idx]
            if not city:
                continue
            value = pd.to_numeric(raw.iat[row_idx, col_idx], errors="coerce")
            records.append({"城市": city, "年份": year, value_name: value})
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=["城市", "年份", value_name])
    return df.groupby(["城市", "年份"], as_index=False)[value_name].first()


def load_financial_development_panel() -> pd.DataFrame:
    try:
        staged = os.path.join(STAGING_DIR, "financial_dev.xlsx")
        path = staged if os.path.exists(staged) else find_file("2.26地级市金融发展水平(2000-2024).xlsx", CITY_DATA_DIR)
        df = read_excel_any(path)
        df["城市"] = df["城市"].map(standardize_city)
        df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
        keep_cols = {
            "年末金融机构各项贷款余额(万元)": "年末金融机构各项贷款余额",
            "年末金融机构存款余额(万元)": "年末金融机构存款余额",
            "地区生产总值(万元)": "金融发展口径地区生产总值",
            "金融发展水平1": "金融发展水平1",
            "金融发展水平2": "金融发展水平2",
            "金融发展水平": "金融发展水平",
        }
        rename = {k: v for k, v in keep_cols.items() if k in df.columns}
        df = df.rename(columns=rename)
        cols = ["城市", "年份"] + list(rename.values())
        df = df[cols].copy()
        for col in cols[2:]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=["城市", "年份"])


def load_marketization_panel() -> pd.DataFrame:
    try:
        staged = os.path.join(STAGING_DIR, "marketization.xlsx")
        path = staged if os.path.exists(staged) else find_file("地级市市场化水平（2000-2024年）.xlsx", CITY_DATA_DIR)
        df = read_excel_any(path)
        df["城市"] = df["城市"].map(standardize_city)
        df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
        keep = ["城市", "年份", "市场化水平"]
        df = df[keep].copy()
        df["市场化水平"] = pd.to_numeric(df["市场化水平"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=["城市", "年份"])


def load_control_panels() -> pd.DataFrame:
    specs = [
        ("gdp.csv", "time_rows", "地区生产总值"),
        ("sci_exp.csv", "time_rows", "财政科技支出"),
        ("population.csv", "city_rows", "常住人口"),
        ("secondary.csv", "time_rows", "第二产业增加值"),
        ("fdi.csv", "selector", "实际利用外资额"),
    ]
    merged = None
    for file_name, mode, value_name in specs:
        staged = os.path.join(STAGING_DIR, file_name)
        path = staged if os.path.exists(staged) else find_file(file_name, CITY_DATA_DIR)
        if mode == "simple":
            df = parse_simple_wide_year_table(path, value_name)
        elif mode == "time_rows":
            df = parse_time_rows_city_columns_table(path, value_name)
        elif mode == "city_rows":
            df = parse_city_rows_year_columns_table(path, value_name)
        else:
            df = parse_wide_city_table(path, lambda s: "实际利用外资额" in s and "对外借款" not in s, value_name)
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on=["城市", "年份"], how="outer")
    return merged


def build_master_panel() -> pd.DataFrame:
    master = load_establishment_panel()
    panels = [
        load_investment_panel(),
        load_patent_panel(),
        load_fiscal_pressure_panel(),
        load_debt_panel(),
        load_social_capital_panel(),
        load_fiscal_transparency_panel(),
        load_financing_constraint_panels(),
        load_financial_development_panel(),
        load_marketization_panel(),
        load_control_panels(),
    ]
    for panel in panels:
        if panel is None or panel.empty:
            continue
        master = master.merge(panel, on=["城市", "年份"], how="left")

    # Missing investment rows after the left join mean "no event observed", not sample loss.
    if "基金投资事件总数" in master.columns:
        no_invest_event = master["基金投资事件总数"].isna()
        fill_zero_cols = [
            "基金投资总额_人民币万元",
            "基金投资事件总数",
            "早期投资金额_人民币万元",
            "早期投资事件数",
        ]
        for col in fill_zero_cols:
            if col in master.columns:
                master.loc[no_invest_event, col] = 0

    # control variables moved to the end by explicit ordering
    control_cols = [c for c in ["地区生产总值", "财政科技支出", "常住人口", "第二产业增加值", "实际利用外资额"] if c in master.columns]
    other_cols = [c for c in master.columns if c not in control_cols]
    master = master[other_cols + control_cols]
    return master


def build_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = pd.DataFrame(
        {
            "变量名": df.columns,
            "缺失值个数": [int(df[col].isna().sum()) for col in df.columns],
            "缺失率": [float(df[col].isna().mean()) for col in df.columns],
        }
    )
    return summary.sort_values(["缺失值个数", "变量名"], ascending=[False, True])


def main() -> None:
    panel = build_master_panel()
    panel = panel.sort_values(["城市", "年份"]).reset_index(drop=True)
    missing = build_missing_summary(panel)
    sample_summary = pd.DataFrame(
        [
            {"指标": "总样本量", "数值": len(panel)},
            {"指标": "城市数", "数值": panel["城市"].nunique()},
            {"指标": "年份最小值", "数值": panel["年份"].min()},
            {"指标": "年份最大值", "数值": panel["年份"].max()},
        ]
    )

    out_panel = os.path.join(PANEL_DIR, "地级市总面板_编制版.csv")
    out_missing = os.path.join(PANEL_DIR, "地级市总面板_缺失统计.csv")
    out_sample = os.path.join(PANEL_DIR, "地级市总面板_样本统计.csv")

    panel.to_csv(out_panel, index=False, encoding="utf-8-sig")
    missing.to_csv(out_missing, index=False, encoding="utf-8-sig")
    sample_summary.to_csv(out_sample, index=False, encoding="utf-8-sig")

    print("panel_out =", out_panel)
    print("missing_out =", out_missing)
    print("sample_out =", out_sample)
    print(sample_summary.to_string(index=False))
    print(missing.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
