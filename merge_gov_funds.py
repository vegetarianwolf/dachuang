# -*- coding: utf-8 -*-
"""
整合政府引导基金数据，并匹配地级市/城市信息。

数据来源：
  - 清科数据：政府引导基金清科目录（1）（2）（3）
  - 清科数据（24-25新增）：引导基金基金清科目录24-25（1）（2）
  - 投中数据：投中数据全部政府引导基金名录（上）（下）

输出：
  - 政府引导基金整合数据/政府引导基金_整合.csv
  - 政府引导基金整合数据/数据整合说明.md
"""
import os
import re
import json
import pandas as pd
import numpy as np
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "政府引导基金清科目录（3）")
OUT_DIR = os.path.join(BASE_DIR, "政府引导基金整合数据")
os.makedirs(OUT_DIR, exist_ok=True)

ZHIXIASHI = {"北京市", "上海市", "天津市", "重庆市", "北京", "上海", "天津", "重庆"}
ZHIXIASHI_NORM = {"北京": "北京市", "上海": "上海市", "天津": "天津市", "重庆": "重庆市"}

# ── 地区解析工具 ──────────────────────────────────────────────

def _norm_province(p: str) -> str:
    """统一省份名称（去掉'中国|'前缀，保留省/市/自治区全称）"""
    p = p.strip()
    if p in ZHIXIASHI_NORM:
        return ZHIXIASHI_NORM[p]
    return p


def parse_region_pedata(raw: str):
    """
    解析清科注册地区字段。
    格式: "中国|江苏省|南京市|溧水区" 或 "安徽省|亳州市|谯城区"
    返回 (省份, 城市)
    """
    if not isinstance(raw, str) or raw.strip() in ("", "--", "nan"):
        return None, None
    parts = [p.strip() for p in raw.split("|") if p.strip() and p.strip() != "中国"]
    if not parts:
        return None, None

    province = _norm_province(parts[0])

    if province in ZHIXIASHI or province.rstrip("市") in {"北京", "上海", "天津", "重庆"}:
        return province if province.endswith("市") else province + "市", province if province.endswith("市") else province + "市"

    if len(parts) >= 2:
        city = parts[1].strip()
        if city and city != "--":
            return province, city
    return province, None


def parse_region_cvs(raw: str):
    """
    解析投中所在地字段。
    格式: "浙江省-台州市" 或 "未披露"
    返回 (省份, 城市)
    """
    if not isinstance(raw, str) or raw.strip() in ("", "--", "nan", "未披露"):
        return None, None
    sep = "-" if "-" in raw else "|"
    parts = [p.strip() for p in raw.split(sep) if p.strip()]
    if not parts:
        return None, None

    province = _norm_province(parts[0])

    if province in ZHIXIASHI or province.rstrip("市") in {"北京", "上海", "天津", "重庆"}:
        return province if province.endswith("市") else province + "市", province if province.endswith("市") else province + "市"

    if len(parts) >= 2:
        city = parts[1].strip()
        if city and city != "未披露":
            return province, city
    return province, None


def _try_extract_city_from_name(fund_name: str):
    """
    从基金名称中尝试提取城市信息。
    例如 "亳州市文化和数字创意产业投资基金" → "亳州市"
    """
    if not isinstance(fund_name, str):
        return None
    m = re.match(r"^(.{2,4}(?:市|州|地区|盟))", fund_name)
    if m:
        return m.group(1)
    m = re.match(r"^(.{2,4}(?:新区|高新区|经开区))", fund_name)
    if m:
        return m.group(1)
    return None


def standardize_scale(raw):
    """
    将目标规模统一为 '万元人民币' 数值。
    - 清科(1)(2)(3): 单位 百万人民币
    - 清科24-25: 文本如 "10亿人民币"
    - 投中(上): 单位 万元
    - 投中(下): 数值 + 单位列
    """
    if isinstance(raw, (int, float)):
        return raw
    if not isinstance(raw, str):
        return np.nan
    raw = raw.strip().replace(",", "").replace("，", "")
    if raw in ("--", "", "nan"):
        return np.nan
    m = re.match(r"([\d.]+)\s*亿\s*(?:人民币|美元|元)?", raw)
    if m:
        return float(m.group(1)) * 10000  # 亿 → 万
    m = re.match(r"([\d.]+)\s*万\s*(?:人民币|美元|元)?", raw)
    if m:
        return float(m.group(1))
    m = re.match(r"([\d.]+)\s*(?:人民币|美元|元)?", raw)
    if m:
        return float(m.group(1))
    return np.nan


# ── 读取清科目录 (1)(2)(3) ──────────────────────────────────

def read_pedata_old(filename, extra_cols=None):
    """读取清科旧格式目录文件（数字表头 + 真实表头）"""
    path = os.path.join(SRC_DIR, filename)
    df = pd.read_csv(path, encoding="utf-8-sig", skiprows=1, dtype=str)
    df.columns = df.columns.str.strip()
    return df


def process_pedata_123():
    """处理清科目录（1）（2）（3）"""
    keep_cols = ["基金简称", "基金全称", "管理机构", "基金类型", "基金级别",
                 "原始地区", "成立时间", "目标规模_百万", "管理机构是否国资", "数据来源"]
    frames = []

    rename_map = {
        "管理机构全称": "管理机构",
        "基金分类": "基金类型",
        "注册地区": "原始地区",
        "目标规模(人民币/百万)": "目标规模_百万",
    }

    for fn in ["政府引导基金清科目录（1).csv",
               "政府引导基金清科目录（2).csv",
               "政府引导基金清科目录（3）.csv"]:
        df = read_pedata_old(fn)
        df = df.rename(columns=rename_map)
        df["数据来源"] = f"清科-{fn}"
        for c in keep_cols:
            if c not in df.columns:
                df[c] = np.nan
        frames.append(df[keep_cols].copy())

    combined = pd.concat(frames, ignore_index=True)

    combined["目标规模_百万"] = (
        combined["目标规模_百万"]
        .astype(str)
        .str.replace(",", "")
        .str.replace("，", "")
        .str.strip()
    )
    combined["目标规模_万元"] = pd.to_numeric(combined["目标规模_百万"], errors="coerce") * 100
    combined.drop(columns=["目标规模_百万"], inplace=True, errors="ignore")

    parsed = combined["原始地区"].apply(parse_region_pedata)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return combined


# ── 读取清科24-25 ──────────────────────────────────────────

def process_pedata_2425():
    """处理引导基金基金清科目录24-25（1）（2）"""
    frames = []
    for fn in ["引导基金基金清科目录24-25（1）.csv", "引导基金基金清科目录24-25（2）.csv"]:
        path = os.path.join(SRC_DIR, fn)
        df = pd.read_csv(path, encoding="utf-8-sig", skiprows=1, dtype=str)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "基金名称": "基金全称",
            "基金管理人": "管理机构",
            "基金类型": "基金类型",
            "注册地区": "原始地区",
            "成立时间": "成立时间",
            "目标规模": "目标规模_原始",
            "认缴规模": "认缴规模_原始",
        })
        df["基金简称"] = np.nan
        df["数据来源"] = f"清科24-25-{fn}"
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    combined["目标规模_万元"] = combined["目标规模_原始"].apply(standardize_scale)
    combined.drop(columns=["目标规模_原始"], inplace=True, errors="ignore")

    parsed = combined["原始地区"].apply(parse_region_pedata)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return combined


# ── 读取投中数据 ──────────────────────────────────────────

def process_cvs():
    """处理投中数据（上）（下）"""
    frames = []

    # (上)
    path_up = os.path.join(SRC_DIR, "投中数据全部政府引导基金名录（上）.csv")
    df_up = pd.read_csv(path_up, encoding="utf-8-sig", skiprows=1, dtype=str)
    df_up.columns = df_up.columns.str.strip()
    df_up = df_up.rename(columns={
        "基金简称": "基金简称",
        "基金全称": "基金全称",
        "成立时间": "成立时间",
        "所在地": "原始地区",
        "基金类型": "基金类型",
        "募集目标规模（万元）": "目标规模_万元",
        "管理机构": "管理机构",
    })
    df_up["数据来源"] = "投中-名录（上）"
    frames.append(df_up)

    # (下)
    path_down = os.path.join(SRC_DIR, "投资数据全部政府引导基金目录（下）.csv")
    df_down = pd.read_csv(path_down, encoding="utf-8-sig", skiprows=1, dtype=str)
    df_down.columns = df_down.columns.str.strip()
    df_down = df_down.rename(columns={
        "基金简称": "基金简称",
        "基金全称": "基金全称",
        "成立时间": "成立时间",
        "所在地": "原始地区",
        "基金类型": "基金类型",
        "管理公司": "管理机构",
    })
    # 目标规模：募集目标规模 + 单位
    if "募集目标规模" in df_down.columns:
        df_down["目标规模_万元"] = pd.to_numeric(
            df_down["募集目标规模"].astype(str).str.replace(",", "").str.replace("，", ""),
            errors="coerce"
        )
        mask_yi = df_down["单位"].astype(str).str.contains("亿", na=False) if "单位" in df_down.columns else pd.Series(False, index=df_down.index)
        df_down.loc[mask_yi, "目标规模_万元"] = df_down.loc[mask_yi, "目标规模_万元"] * 10000
    else:
        df_down["目标规模_万元"] = np.nan

    df_down["数据来源"] = "投中-目录（下）"
    frames.append(df_down)

    combined = pd.concat(frames, ignore_index=True)

    # 规模统一
    combined["目标规模_万元"] = pd.to_numeric(
        combined["目标规模_万元"].astype(str).str.replace(",", "").str.replace("，", ""),
        errors="coerce"
    )

    parsed = combined["原始地区"].apply(parse_region_cvs)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return combined


# ── 从基金名称补充城市信息 ───────────────────────────────────

def supplement_city(df):
    """对城市为空的记录，从基金全称/简称中尝试提取"""
    mask = df["城市"].isna() | (df["城市"].astype(str).str.strip() == "")
    for idx in df[mask].index:
        name = df.at[idx, "基金全称"] if pd.notna(df.at[idx, "基金全称"]) else df.at[idx, "基金简称"]
        city = _try_extract_city_from_name(str(name) if pd.notna(name) else "")
        if city:
            df.at[idx, "城市"] = city
    return df


# ── 主流程 ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  政府引导基金数据整合")
    print("=" * 60)

    # 1. 读取并处理各来源
    print("\n[1/6] 读取清科目录（1）（2）（3）...")
    df_pedata = process_pedata_123()
    print(f"      清科旧目录合计: {len(df_pedata)} 条")

    print("[2/6] 读取清科24-25目录...")
    df_pe2425 = process_pedata_2425()
    print(f"      清科24-25合计: {len(df_pe2425)} 条")

    print("[3/6] 读取投中数据...")
    df_cvs = process_cvs()
    print(f"      投中数据合计: {len(df_cvs)} 条")

    # 2. 统一列并合并
    print("\n[4/6] 统一字段并合并...")
    common_cols = ["基金简称", "基金全称", "管理机构", "基金类型", "基金级别",
                   "成立时间", "原始地区", "省份", "城市",
                   "目标规模_万元", "管理机构是否国资", "数据来源"]

    aligned = []
    for i, df in enumerate([df_pedata, df_pe2425, df_cvs]):
        # 处理可能的重复列名
        if df.columns.duplicated().any():
            df = df.loc[:, ~df.columns.duplicated(keep="first")]
        tmp = pd.DataFrame(index=df.index)
        for col in common_cols:
            if col in df.columns:
                tmp[col] = df[col].values
            else:
                tmp[col] = np.nan
        aligned.append(tmp.reset_index(drop=True))

    df_all = pd.concat(aligned, ignore_index=True)

    # 去除基金全称和简称均为空的行
    mask_empty = (
        (df_all["基金全称"].isna() | (df_all["基金全称"].astype(str).str.strip() == "")) &
        (df_all["基金简称"].isna() | (df_all["基金简称"].astype(str).str.strip() == ""))
    )
    df_all = df_all[~mask_empty].reset_index(drop=True)

    total_before_dedup = len(df_all)
    print(f"      合并总量: {total_before_dedup} 条")

    # 3. 去重：以基金全称为准
    print("[5/6] 去重...")
    df_all["_dedup_key"] = (
        df_all["基金全称"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", "", regex=True)
        .str.replace("（", "(", regex=False)
        .str.replace("）", ")", regex=False)
    )
    df_all = df_all.sort_values(["_dedup_key", "成立时间"], na_position="last")
    df_all = df_all.drop_duplicates(subset=["_dedup_key"], keep="first")
    df_all.drop(columns=["_dedup_key"], inplace=True)
    total_after_dedup = len(df_all)
    print(f"      去重后: {total_after_dedup} 条（去除 {total_before_dedup - total_after_dedup} 条重复）")

    # 4. 从基金名称补充城市
    print("[6/6] 补充城市信息...")
    missing_city_before = df_all["城市"].isna().sum() + (df_all["城市"].astype(str).str.strip() == "").sum()
    df_all = supplement_city(df_all)
    missing_city_after = df_all["城市"].isna().sum() + (df_all["城市"].astype(str).str.strip() == "").sum()
    supplemented = missing_city_before - missing_city_after
    print(f"      从基金名称补充城市: {supplemented} 条")

    # 5. 输出统计
    total = len(df_all)
    has_province = df_all["省份"].notna().sum()
    has_city = df_all["城市"].notna().sum() - (df_all["城市"].astype(str).str.strip() == "").sum()

    print("\n" + "=" * 60)
    print(f"  整合完成！")
    print(f"  总基金数: {total}")
    print(f"  匹配到省份: {has_province} ({has_province/total*100:.1f}%)")
    print(f"  匹配到城市: {has_city} ({has_city/total*100:.1f}%)")
    print(f"  未匹配城市: {total - has_city} ({(total-has_city)/total*100:.1f}%)")
    print("=" * 60)

    # 按省份统计
    province_stats = df_all["省份"].value_counts().head(20)
    city_stats = df_all["城市"].value_counts().head(20)

    # 各来源统计
    source_stats = df_all["数据来源"].value_counts()

    # 6. 保存
    out_csv = os.path.join(OUT_DIR, "政府引导基金_整合.csv")
    df_all.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\n  已保存: {out_csv}")

    # 按来源详细计数（用于文档）
    stats_info = {
        "total_before_dedup": total_before_dedup,
        "total_after_dedup": total_after_dedup,
        "duplicates_removed": total_before_dedup - total_after_dedup,
        "total": total,
        "has_province": int(has_province),
        "has_city": int(has_city),
        "missing_city": int(total - has_city),
        "city_supplemented_from_name": supplemented,
        "source_counts": source_stats.to_dict(),
        "province_top20": province_stats.to_dict(),
        "city_top20": city_stats.to_dict(),
        "pedata_old_count": len(df_pedata),
        "pedata_2425_count": len(df_pe2425),
        "cvs_count": len(df_cvs),
    }

    # 输出统计 JSON 供文档使用
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            return super().default(obj)

    stats_path = os.path.join(OUT_DIR, "_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats_info, f, ensure_ascii=False, indent=2, cls=NpEncoder)
    print(f"  统计信息: {stats_path}")

    return stats_info


if __name__ == "__main__":
    stats = main()
