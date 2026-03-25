# -*- coding: utf-8 -*-
"""
按城市-年份统计政府引导基金 2000-2024 投资指标（面板数据）

指标：
  总投资额、总投资次数、
  早期投资额/次数/占比（种子期+初创期），
  广义早期投资额/次数/占比（种子期+初创期+扩张期）

城市：基金注册地级市（来自基金目录）
投资金额：投资金额_RMB百万（百万元人民币）
"""
import os
import re
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "政府引导基金整合数据")

# ── 工具 ──────────────────────────────────────────────────

def parse_amount(val):
    """解析投资金额字段：'200.00', '1,722.22', '10.00(e)', '--', '< 0.01(e)' → float or NaN"""
    if not isinstance(val, str):
        return np.nan
    v = val.strip()
    if v in ("--", "", "nan"):
        return np.nan
    v = v.replace(",", "").replace("，", "")
    v = re.sub(r"\(e\)", "", v, flags=re.IGNORECASE)
    v = re.sub(r"^[<>]\s*", "", v)
    try:
        return float(v)
    except ValueError:
        return np.nan


def make_key(s):
    if not isinstance(s, str):
        return ""
    return s.strip().replace(" ", "").replace("（", "(").replace("）", ")")


# ── 读取数据 ──────────────────────────────────────────────

print("读取基金目录...")
catalog = pd.read_csv(
    os.path.join(DATA_DIR, "政府引导基金_基金目录_整合.csv"),
    encoding="utf-8-sig", dtype=str
)
catalog["_key"] = catalog["基金全称"].apply(make_key)
# 基金全称 → 城市 映射（优先有城市信息的行）
fund_city_map = (
    catalog[catalog["城市"].notna() & (catalog["城市"].astype(str).str.strip() != "")]
    .drop_duplicates(subset=["_key"], keep="first")
    .set_index("_key")["城市"]
    .to_dict()
)
print(f"  基金目录: {len(catalog)} 条，建立城市映射 {len(fund_city_map)} 条")

print("读取投资事件...")
events = pd.read_csv(
    os.path.join(DATA_DIR, "政府引导基金_投资事件_整合.csv"),
    encoding="utf-8-sig", dtype=str
)
print(f"  投资事件: {len(events)} 条")

# ── 数据清洗 ──────────────────────────────────────────────

# 年份过滤：2000-2024
events["_year"] = pd.to_numeric(
    events["投资时间"].astype(str).str[:4], errors="coerce"
)
events = events[events["_year"].between(2000, 2024)].copy()
print(f"  2000-2024: {len(events)} 条")

# 解析金额（RMB百万）
events["_amt"] = events["投资金额_RMB百万"].apply(parse_amount)

# 映射城市
events["_key"] = events["基金全称"].apply(make_key)
events["注册城市"] = events["_key"].map(fund_city_map)

matched = events["注册城市"].notna().sum()
print(f"  匹配到城市: {matched} / {len(events)} ({matched/len(events)*100:.1f}%)")

# 仅保留匹配到城市的记录
df = events[events["注册城市"].notna()].copy()

# 投资阶段标准化
stage_col = "投资阶段"
early_stages      = {"种子期", "初创期"}
broad_early_stages = {"种子期", "初创期", "扩张期"}

df["_is_early"]       = df[stage_col].isin(early_stages)
df["_is_broad_early"] = df[stage_col].isin(broad_early_stages)

# ── 聚合 ──────────────────────────────────────────────────

print("按城市-年份聚合...")

def city_year_agg(g):
    total_count = len(g)
    total_amt   = g["_amt"].sum()

    early       = g[g["_is_early"]]
    broad_early = g[g["_is_broad_early"]]

    early_count = len(early)
    early_amt   = early["_amt"].sum()

    broad_count = len(broad_early)
    broad_amt   = broad_early["_amt"].sum()

    def safe_ratio(num, den):
        if np.isnan(den) or den == 0 or np.isnan(num):
            return np.nan
        return round(num / den, 4)

    return pd.Series({
        "总投资次数":          total_count,
        "总投资额_百万元":      round(total_amt, 4) if not np.isnan(total_amt) else np.nan,
        "早期投资次数":         early_count,
        "早期投资额_百万元":    round(early_amt, 4) if not np.isnan(early_amt) else np.nan,
        "早期投资次数占比":     round(early_count / total_count, 4) if total_count > 0 else np.nan,
        "早期投资额占比":       safe_ratio(early_amt, total_amt),
        "广义早期投资次数":      broad_count,
        "广义早期投资额_百万元": round(broad_amt, 4) if not np.isnan(broad_amt) else np.nan,
        "广义早期投资次数占比":  round(broad_count / total_count, 4) if total_count > 0 else np.nan,
        "广义早期投资额占比":    safe_ratio(broad_amt, total_amt),
    })

result = df.groupby(["注册城市", "_year"]).apply(city_year_agg).reset_index()
result = result.rename(columns={"注册城市": "城市", "_year": "年份"})
result["年份"] = result["年份"].astype(int)

# 省份映射
city_province = (
    catalog[catalog["城市"].notna() & (catalog["城市"].astype(str).str.strip() != "")]
    [["城市", "省份"]]
    .dropna()
    .drop_duplicates(subset=["城市"], keep="first")
    .set_index("城市")["省份"]
    .to_dict()
)
result.insert(1, "省份", result["城市"].map(city_province))
result = result.sort_values(["城市", "年份"]).reset_index(drop=True)

# ── 百分比列（便于阅读） ──────────────────────────────────

for col in ["早期投资次数占比", "早期投资额占比", "广义早期投资次数占比", "广义早期投资额占比"]:
    pct_col = col.replace("占比", "占比%")
    result[pct_col] = result[col].apply(
        lambda x: f"{x*100:.2f}%" if pd.notna(x) else "--"
    )

# ── 保存 ──────────────────────────────────────────────────

out_path = os.path.join(DATA_DIR, "城市_投资统计_分年份_2000-2024.csv")
result.to_csv(out_path, index=False, encoding="utf-8-sig")

n_cities = result["城市"].nunique()
n_years  = result["年份"].nunique()
print(f"\n已保存: {out_path}")
print(f"城市数: {n_cities}，年份数: {n_years}，行数: {len(result)}")
print(f"涉及投资事件: {len(df)}")

# 打印深圳市前5年样例
sample = result[result["城市"] == result["城市"].iloc[0]].head(5)
print(f"\n样例（{result['城市'].iloc[0]}）:")
print(sample[["城市", "年份", "总投资次数", "总投资额_百万元",
              "早期投资次数占比", "广义早期投资次数占比"]].to_string(index=False))
