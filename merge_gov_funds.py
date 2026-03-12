# -*- coding: utf-8 -*-
"""
政府引导基金数据总整合脚本

数据来源（基金目录）：
  A. 政府引导基金清科目录（3）/ —— 清科目录(1)(2)(3) + 清科24-25(1)(2) + 投中(上)(下)
  B. 政府引导基金相关信息/    —— 清科更详细版本(含出资人信息)，与A部分重叠

数据来源（投资事件）：
  C. 清科政府引导基金投资事件截止到2024年/ —— 投资事件(1999-2024)
  D. 政府引导基金投资2015-2024/            —— C的子集(2015-2024)

输出目录：政府引导基金整合数据/
"""
import os
import re
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_CATALOG = os.path.join(BASE_DIR, "政府引导基金清科目录（3）")
SRC_INFO = os.path.join(BASE_DIR, "政府引导基金相关信息")
SRC_EVENTS_FULL = os.path.join(BASE_DIR, "清科政府引导基金投资事件截止到2024年")
SRC_EVENTS_1524 = os.path.join(BASE_DIR, "政府引导基金投资2015-2024")
OUT_DIR = os.path.join(BASE_DIR, "政府引导基金整合数据")
os.makedirs(OUT_DIR, exist_ok=True)

ZHIXIASHI = {"北京市", "上海市", "天津市", "重庆市", "北京", "上海", "天津", "重庆"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  通用工具
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _norm_province(p: str) -> str:
    p = p.strip()
    mapping = {"北京": "北京市", "上海": "上海市", "天津": "天津市", "重庆": "重庆市"}
    return mapping.get(p, p)


def _is_zhixiashi(p: str) -> bool:
    return p in ZHIXIASHI or p.rstrip("市") in {"北京", "上海", "天津", "重庆"}


def parse_region_pipe(raw: str):
    """解析 '|' 分隔的地区 (清科格式: 中国|省|市|区)"""
    if not isinstance(raw, str) or raw.strip() in ("", "--", "nan"):
        return None, None
    parts = [p.strip() for p in raw.split("|") if p.strip() and p.strip() != "中国"]
    if not parts:
        return None, None
    province = _norm_province(parts[0])
    if _is_zhixiashi(province):
        city = province if province.endswith("市") else province + "市"
        return city, city
    if len(parts) >= 2 and parts[1].strip() not in ("", "--"):
        return province, parts[1].strip()
    return province, None


def parse_region_dash(raw: str):
    """解析 '-' 分隔的地区 (投中格式: 省-市)"""
    if not isinstance(raw, str) or raw.strip() in ("", "--", "nan", "未披露"):
        return None, None
    sep = "-" if "-" in raw else "|"
    parts = [p.strip() for p in raw.split(sep) if p.strip()]
    if not parts:
        return None, None
    province = _norm_province(parts[0])
    if _is_zhixiashi(province):
        city = province if province.endswith("市") else province + "市"
        return city, city
    if len(parts) >= 2 and parts[1].strip() not in ("", "未披露"):
        return province, parts[1].strip()
    return province, None


def try_city_from_name(name: str):
    """从基金名称尝试提取城市"""
    if not isinstance(name, str):
        return None
    m = re.match(r"^(.{2,4}(?:市|州|地区|盟))", name)
    if m:
        return m.group(1)
    return None


def standardize_scale_text(raw):
    """将 '10亿人民币' 这类文本转为万元"""
    if not isinstance(raw, str):
        return np.nan
    raw = raw.strip().replace(",", "").replace("，", "")
    if raw in ("--", "", "nan"):
        return np.nan
    m = re.match(r"([\d.]+)\s*亿", raw)
    if m:
        return float(m.group(1)) * 10000
    m = re.match(r"([\d.]+)\s*万", raw)
    if m:
        return float(m.group(1))
    m = re.match(r"([\d.]+)", raw)
    if m:
        return float(m.group(1))
    return np.nan


def make_dedup_key(s):
    """生成去重键：去空格，统一括号"""
    if not isinstance(s, str):
        return ""
    return s.strip().replace(" ", "").replace("（", "(").replace("）", ")")


def safe_read_csv(path, **kwargs):
    """安全读取 CSV，尝试多种编码"""
    for enc in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return pd.read_csv(path, encoding="utf-8-sig", errors="replace", **kwargs)


def align_to_cols(df, cols):
    """将 df 对齐到指定列，缺失列补 NaN；自动处理重复列名"""
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep="first")]
    n = len(df)
    data = {}
    for c in cols:
        if c in df.columns:
            data[c] = df[c].values
        else:
            data[c] = [np.nan] * n
    return pd.DataFrame(data, columns=cols)


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Part 1: 基金目录整合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CATALOG_COLS = [
    "基金简称", "基金全称", "管理机构", "基金类型", "基金级别",
    "成立时间", "原始地区", "省份", "城市",
    "目标规模_万元", "管理机构是否国资", "数据来源",
]


def load_pedata_catalog():
    """读取 政府引导基金清科目录（3）/ 下的清科目录(1)(2)(3)"""
    rename_map = {
        "管理机构全称": "管理机构",
        "基金分类": "基金类型",
        "注册地区": "原始地区",
        "目标规模(人民币/百万)": "目标规模_百万",
    }
    keep = ["基金简称", "基金全称", "管理机构", "基金类型", "基金级别",
            "原始地区", "成立时间", "目标规模_百万", "管理机构是否国资", "数据来源"]

    frames = []
    for fn in ["政府引导基金清科目录（1).csv",
               "政府引导基金清科目录（2).csv",
               "政府引导基金清科目录（3）.csv"]:
        path = os.path.join(SRC_CATALOG, fn)
        if not os.path.exists(path):
            continue
        df = safe_read_csv(path, skiprows=1, dtype=str)
        df.columns = df.columns.str.strip()
        df = df.rename(columns=rename_map)
        df["数据来源"] = f"清科目录-{fn}"
        for c in keep:
            if c not in df.columns:
                df[c] = np.nan
        frames.append(df[keep].copy())

    if not frames:
        return pd.DataFrame(columns=CATALOG_COLS)

    combined = pd.concat(frames, ignore_index=True)
    combined["目标规模_百万"] = (
        combined["目标规模_百万"].astype(str)
        .str.replace(",", "").str.replace("，", "").str.strip()
    )
    combined["目标规模_万元"] = pd.to_numeric(combined["目标规模_百万"], errors="coerce") * 100
    combined.drop(columns=["目标规模_百万"], inplace=True, errors="ignore")

    parsed = combined["原始地区"].apply(parse_region_pipe)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return align_to_cols(combined, CATALOG_COLS)


def load_pedata_info():
    """读取 政府引导基金相关信息/ 下的详细清科数据（含出资人多行）"""
    rename_map = {
        "管理机构全称": "管理机构",
        "基金分类": "基金类型",
        "注册地区": "原始地区",
        "目标规模(人民币/百万)": "目标规模_百万",
    }

    frames = []
    for fn in sorted(os.listdir(SRC_INFO)):
        if not fn.endswith(".csv"):
            continue
        path = os.path.join(SRC_INFO, fn)
        df = safe_read_csv(path, dtype=str)
        df.columns = df.columns.str.strip()
        # 过滤 LP 续行（基金简称为空的行）
        df = df[df["基金简称"].notna() & (df["基金简称"].astype(str).str.strip() != "")]
        df = df.rename(columns=rename_map)
        df["数据来源"] = f"清科详细-{fn}"
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=CATALOG_COLS)

    combined = pd.concat(frames, ignore_index=True)
    combined["目标规模_百万"] = (
        combined["目标规模_百万"].astype(str)
        .str.replace(",", "").str.replace("，", "").str.strip()
    )
    combined["目标规模_万元"] = pd.to_numeric(combined["目标规模_百万"], errors="coerce") * 100
    combined.drop(columns=["目标规模_百万"], inplace=True, errors="ignore")

    parsed = combined["原始地区"].apply(parse_region_pipe)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return align_to_cols(combined, CATALOG_COLS)


def load_pedata_2425():
    """读取清科24-25新增目录"""
    frames = []
    for fn in ["引导基金基金清科目录24-25（1）.csv", "引导基金基金清科目录24-25（2）.csv"]:
        path = os.path.join(SRC_CATALOG, fn)
        if not os.path.exists(path):
            continue
        df = safe_read_csv(path, skiprows=1, dtype=str)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "基金名称": "基金全称",
            "基金管理人": "管理机构",
            "基金类型": "基金类型",
            "注册地区": "原始地区",
            "成立时间": "成立时间",
            "目标规模": "目标规模_原始",
        })
        df["基金简称"] = np.nan
        df["数据来源"] = f"清科24-25-{fn}"
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=CATALOG_COLS)

    combined = pd.concat(frames, ignore_index=True)
    combined["目标规模_万元"] = combined["目标规模_原始"].apply(standardize_scale_text)
    combined.drop(columns=["目标规模_原始"], inplace=True, errors="ignore")

    parsed = combined["原始地区"].apply(parse_region_pipe)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return align_to_cols(combined, CATALOG_COLS)


def load_cvs():
    """读取投中数据（上）（下）"""
    frames = []

    # 上
    path_up = os.path.join(SRC_CATALOG, "投中数据全部政府引导基金名录（上）.csv")
    if os.path.exists(path_up):
        df = safe_read_csv(path_up, skiprows=1, dtype=str)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "所在地": "原始地区",
            "基金类型": "基金类型",
            "募集目标规模（万元）": "目标规模_万元",
            "管理机构": "管理机构",
        })
        df["数据来源"] = "投中-名录（上）"
        frames.append(df)

    # 下
    path_down = os.path.join(SRC_CATALOG, "投资数据全部政府引导基金目录（下）.csv")
    if os.path.exists(path_down):
        df = safe_read_csv(path_down, skiprows=1, dtype=str)
        df.columns = df.columns.str.strip()
        if df.columns.duplicated().any():
            df = df.loc[:, ~df.columns.duplicated(keep="first")]
        df = df.rename(columns={
            "所在地": "原始地区",
            "基金类型": "基金类型",
            "管理公司": "管理机构",
        })
        if "募集目标规模" in df.columns:
            vals = pd.to_numeric(
                df["募集目标规模"].astype(str).str.replace(",", "").str.replace("，", ""),
                errors="coerce"
            )
            df["目标规模_万元"] = vals  # 默认万元
        else:
            df["目标规模_万元"] = np.nan
        df["数据来源"] = "投中-目录（下）"
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=CATALOG_COLS)

    combined = pd.concat(frames, ignore_index=True)
    combined["目标规模_万元"] = pd.to_numeric(
        combined["目标规模_万元"].astype(str).str.replace(",", "").str.replace("，", ""),
        errors="coerce"
    )

    parsed = combined["原始地区"].apply(parse_region_dash)
    combined["省份"] = parsed.apply(lambda x: x[0])
    combined["城市"] = parsed.apply(lambda x: x[1])

    return align_to_cols(combined, CATALOG_COLS)


def build_fund_catalog():
    """整合所有基金目录来源"""
    print("  [A1] 清科目录(1)(2)(3)...")
    df_cat = load_pedata_catalog()
    print(f"       → {len(df_cat)} 条")

    print("  [A2] 清科详细信息(含出资人)...")
    df_info = load_pedata_info()
    print(f"       → {len(df_info)} 条")

    print("  [A3] 清科24-25新增...")
    df_2425 = load_pedata_2425()
    print(f"       → {len(df_2425)} 条")

    print("  [A4] 投中数据(上)(下)...")
    df_cvs = load_cvs()
    print(f"       → {len(df_cvs)} 条")

    df_all = pd.concat([df_cat, df_info, df_2425, df_cvs], ignore_index=True)

    # 去除空行
    mask_empty = (
        (df_all["基金全称"].isna() | (df_all["基金全称"].astype(str).str.strip() == "")) &
        (df_all["基金简称"].isna() | (df_all["基金简称"].astype(str).str.strip() == ""))
    )
    df_all = df_all[~mask_empty].reset_index(drop=True)
    total_before = len(df_all)
    print(f"  [A5] 合并 (去空行后): {total_before} 条")

    # 去重
    df_all["_key"] = df_all["基金全称"].apply(make_dedup_key)
    df_all = df_all.sort_values(["_key", "成立时间"], na_position="last")
    df_all = df_all.drop_duplicates(subset=["_key"], keep="first")
    df_all.drop(columns=["_key"], inplace=True)
    df_all = df_all.reset_index(drop=True)
    total_after = len(df_all)
    print(f"  [A6] 去重后: {total_after} 条 (去除 {total_before - total_after} 条)")

    # 从基金名称补充城市
    missing_before = df_all["城市"].isna().sum() + (df_all["城市"].astype(str).str.strip() == "").sum()
    mask = df_all["城市"].isna() | (df_all["城市"].astype(str).str.strip() == "")
    for idx in df_all[mask].index:
        name = df_all.at[idx, "基金全称"] if pd.notna(df_all.at[idx, "基金全称"]) else df_all.at[idx, "基金简称"]
        city = try_city_from_name(str(name) if pd.notna(name) else "")
        if city:
            df_all.at[idx, "城市"] = city
    missing_after = df_all["城市"].isna().sum() + (df_all["城市"].astype(str).str.strip() == "").sum()
    print(f"  [A7] 从基金名称补充城市: {missing_before - missing_after} 条")

    return df_all, {
        "catalog_total_before_dedup": total_before,
        "catalog_total_after_dedup": total_after,
        "catalog_duplicates_removed": total_before - total_after,
        "catalog_city_supplemented": missing_before - missing_after,
        "sub_pedata_catalog": len(df_cat),
        "sub_pedata_info": len(df_info),
        "sub_pedata_2425": len(df_2425),
        "sub_cvs": len(df_cvs),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Part 2: 投资事件整合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EVENT_COLS = [
    "基金名称", "基金全称", "管理机构", "管理机构全称",
    "被投企业", "被投企业全称", "企业标签", "行业_清科",
    "被投企业地区_原始", "被投企业省份", "被投企业城市",
    "投资类型", "投资阶段", "投资时间",
    "投资币种", "投资金额_百万", "投资金额_RMB百万", "投资金额_USD百万",
    "股权比例", "轮次",
    "数据来源",
]


def load_investment_events():
    """
    读取全部投资事件 CSV (优先用截止到2024年全量文件夹，
    再补充2015-2024文件夹中可能多出来的文件)。
    """
    loaded_files = set()
    frames = []

    # 第一优先级：全量文件夹 (1999-2024)
    for folder, label in [
        (SRC_EVENTS_FULL, "清科投资事件(全)"),
        (SRC_EVENTS_1524, "清科投资事件(15-24)"),
    ]:
        if not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith(".csv"):
                continue
            # 基于文件名去重（两个文件夹同名文件只读一次）
            if fn in loaded_files:
                continue
            loaded_files.add(fn)
            path = os.path.join(folder, fn)
            try:
                df = safe_read_csv(path, dtype=str)
            except Exception as e:
                print(f"    [WARN] 读取失败 {fn}: {e}")
                continue
            df.columns = df.columns.str.strip()
            # 去除 Unnamed 列
            df = df[[c for c in df.columns if not c.startswith("Unnamed")]]
            df["数据来源"] = f"{label}-{fn}"
            frames.append(df)

    if not frames:
        return pd.DataFrame(columns=EVENT_COLS)

    combined = pd.concat(frames, ignore_index=True)

    # 统一列名
    combined = combined.rename(columns={
        "基金名称": "基金名称",
        "基金全称": "基金全称",
        "机构名称": "管理机构",
        "机构全称": "管理机构全称",
        "企业": "被投企业",
        "融资主体": "被投企业全称",
        "企业标签": "企业标签",
        "行业(清科)": "行业_清科",
        "地区": "被投企业地区_原始",
        "投资类型": "投资类型",
        "投资阶段": "投资阶段",
        "投资时间": "投资时间",
        "投资币种": "投资币种",
        "投资金额(M)": "投资金额_百万",
        "投资金额(RMB/M)": "投资金额_RMB百万",
        "投资金额(USD/M)": "投资金额_USD百万",
        "股权%": "股权比例",
        "轮次": "轮次",
    })

    # 解析被投企业地区
    parsed = combined["被投企业地区_原始"].apply(parse_region_pipe)
    combined["被投企业省份"] = parsed.apply(lambda x: x[0])
    combined["被投企业城市"] = parsed.apply(lambda x: x[1])

    result = align_to_cols(combined, EVENT_COLS)

    # 去重（同一基金+同一企业+同一时间+同一金额 视为重复）
    total_before = len(result)
    result["_key"] = (
        result["基金全称"].apply(make_dedup_key) + "|" +
        result["被投企业全称"].apply(make_dedup_key) + "|" +
        result["投资时间"].astype(str).str.strip() + "|" +
        result["投资金额_RMB百万"].astype(str).str.strip()
    )
    result = result.drop_duplicates(subset=["_key"], keep="first")
    result.drop(columns=["_key"], inplace=True)
    result = result.reset_index(drop=True)
    total_after = len(result)

    return result, {
        "events_files_loaded": len(loaded_files),
        "events_total_before_dedup": total_before,
        "events_total_after_dedup": total_after,
        "events_duplicates_removed": total_before - total_after,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Part 3: 交叉补充 — 用投资事件丰富基金目录的地区信息
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def enrich_catalog_from_events(df_catalog, df_events):
    """
    投资事件中的 '被投企业地区' 不是基金注册地区，但投资事件中包含
    '基金全称'，可以与目录中基金进行关联。此处提取投资事件中出现
    但目录中尚缺地区的基金，尝试从基金名称补充。
    同时将投资事件中出现的唯一基金列表作为补充来源。
    """
    # 从投资事件中提取唯一基金
    event_funds = df_events[["基金名称", "基金全称", "管理机构", "管理机构全称"]].drop_duplicates()
    event_funds = event_funds[
        event_funds["基金全称"].notna() &
        (event_funds["基金全称"].astype(str).str.strip() != "") &
        (event_funds["基金全称"].astype(str).str.strip() != "--")
    ]
    event_funds["_key"] = event_funds["基金全称"].apply(make_dedup_key)

    # 找目录中已有的基金key
    catalog_keys = set(df_catalog["基金全称"].apply(make_dedup_key).values)

    # 找投资事件中有但目录中没有的基金
    new_funds = event_funds[~event_funds["_key"].isin(catalog_keys)].copy()
    new_funds = new_funds.drop_duplicates(subset=["_key"], keep="first")

    if len(new_funds) > 0:
        new_rows = pd.DataFrame()
        new_rows["基金简称"] = new_funds["基金名称"].values
        new_rows["基金全称"] = new_funds["基金全称"].values
        new_rows["管理机构"] = new_funds["管理机构全称"].values
        new_rows["数据来源"] = "投资事件补充"

        # 从基金名称提取城市
        for idx in new_rows.index:
            name = new_rows.at[idx, "基金全称"]
            city = try_city_from_name(str(name) if pd.notna(name) else "")
            if city:
                new_rows.at[idx, "城市"] = city

        new_aligned = align_to_cols(new_rows, CATALOG_COLS)
        df_catalog = pd.concat([df_catalog, new_aligned], ignore_index=True)

    return df_catalog, len(new_funds) if len(new_funds) > 0 else 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  主流程
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 64)
    print("  政府引导基金数据 · 总整合")
    print("=" * 64)

    # ── Part A: 基金目录 ──
    print("\n[Part A] 基金目录整合")
    df_catalog, cat_stats = build_fund_catalog()

    # ── Part B: 投资事件 ──
    print("\n[Part B] 投资事件整合")
    df_events, evt_stats = load_investment_events()
    print(f"  读取文件数: {evt_stats['events_files_loaded']}")
    print(f"  合并行数: {evt_stats['events_total_before_dedup']}")
    print(f"  去重后: {evt_stats['events_total_after_dedup']} "
          f"(去除 {evt_stats['events_duplicates_removed']})")

    # ── Part C: 交叉补充 ──
    print("\n[Part C] 用投资事件中的基金补充目录")
    df_catalog, new_from_events = enrich_catalog_from_events(df_catalog, df_events)
    print(f"  从投资事件新增基金: {new_from_events} 条")
    cat_stats["catalog_new_from_events"] = new_from_events

    # ── 统计 ──
    total_cat = len(df_catalog)
    has_prov = df_catalog["省份"].notna().sum()
    has_city_mask = df_catalog["城市"].notna() & (df_catalog["城市"].astype(str).str.strip() != "")
    has_city = has_city_mask.sum()

    total_evt = len(df_events)
    evt_has_city_mask = df_events["被投企业城市"].notna() & (df_events["被投企业城市"].astype(str).str.strip() != "")
    evt_has_city = evt_has_city_mask.sum()

    print("\n" + "=" * 64)
    print("  [*] 基金目录")
    print(f"    总量: {total_cat}")
    print(f"    匹配省份: {has_prov} ({has_prov/total_cat*100:.1f}%)")
    print(f"    匹配城市: {has_city} ({has_city/total_cat*100:.1f}%)")
    print(f"    未匹配城市: {total_cat - has_city} ({(total_cat-has_city)/total_cat*100:.1f}%)")
    print(f"  [*] 投资事件")
    print(f"    总量: {total_evt}")
    print(f"    被投企业匹配城市: {evt_has_city} ({evt_has_city/total_evt*100:.1f}%)")
    print("=" * 64)

    # ── 保存 ──
    cat_path = os.path.join(OUT_DIR, "政府引导基金_基金目录_整合.csv")
    df_catalog.to_csv(cat_path, index=False, encoding="utf-8-sig")
    print(f"\n  已保存: {cat_path}")

    evt_path = os.path.join(OUT_DIR, "政府引导基金_投资事件_整合.csv")
    df_events.to_csv(evt_path, index=False, encoding="utf-8-sig")
    print(f"  已保存: {evt_path}")

    # ── 汇总统计 ──
    province_stats = df_catalog["省份"].value_counts().head(20).to_dict()
    city_stats = df_catalog["城市"].value_counts().head(20).to_dict()
    source_stats = df_catalog["数据来源"].value_counts().to_dict()

    evt_year_counts = {}
    if "投资时间" in df_events.columns:
        years = df_events["投资时间"].astype(str).str[:4]
        evt_year_counts = years.value_counts().sort_index().to_dict()

    all_stats = {
        **cat_stats,
        **evt_stats,
        "catalog_total": total_cat,
        "catalog_has_province": int(has_prov),
        "catalog_has_city": int(has_city),
        "catalog_missing_city": int(total_cat - has_city),
        "events_total": total_evt,
        "events_has_city": int(evt_has_city),
        "catalog_source_counts": source_stats,
        "catalog_province_top20": province_stats,
        "catalog_city_top20": city_stats,
        "events_year_counts": evt_year_counts,
    }

    stats_path = os.path.join(OUT_DIR, "_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2, cls=NpEncoder)
    print(f"  统计信息: {stats_path}")

    return all_stats


if __name__ == "__main__":
    main()
