import os
import re
from collections import Counter

import pandas as pd


BASE_DIR = os.path.join(".", "dachuang", "原始数据打包_20260401", "政府引导基金清科投中目录")
OUTPUT_DIR = os.path.join(".", "dachuang", "原始数据打包_20260401", "市级数据")
MUNICIPALITIES = {"北京市", "天津市", "上海市", "重庆市"}


def find_file_by_suffix(root: str, suffix: str) -> str:
    for current_root, _, files in os.walk(root):
        for name in files:
            if name.endswith(suffix):
                return os.path.join(current_root, name)
    raise FileNotFoundError(suffix)


def read_named_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    # These files are exported with placeholder columns 0..n-1 and the first row stores real headers.
    raw_headers = df.iloc[0].tolist()
    deduped_headers = []
    counts = Counter()
    for header in raw_headers:
        counts[header] += 1
        if counts[header] == 1:
            deduped_headers.append(header)
        else:
            deduped_headers.append(f"{header}_{counts[header]}")
    df.columns = deduped_headers
    df = df.iloc[1:].reset_index(drop=True)
    return df


def split_items(value: str) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    parts = re.split(r"[\r\n]+", str(value))
    return [p.strip() for p in parts if p and p.strip()]


def normalize_name(value: str) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"[\s　]+", "", text)
    replacements = [
        ("（有限合伙）", ""),
        ("(有限合伙)", ""),
        ("有限责任公司", ""),
        ("股份有限公司", ""),
        ("有限公司", ""),
        ("投资合伙企业", "投资"),
        ("合伙企业", ""),
        ("创业投资企业", "创投"),
        ("创业投资", "创投"),
        ("股权投资基金", "股投基金"),
        ("股权投资", "股投"),
        ("私募基金", "基金"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def parse_amount(value: str) -> float | None:
    if value is None:
        return None
    text = re.sub(r"[^0-9.\-]", "", str(value))
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def extract_city(location: str) -> str | None:
    if location is None:
        return None
    text = str(location).strip()
    if not text or text in {"未披露", "--", "nan"}:
        return None
    if "|" in text:
        parts = [p.strip() for p in text.split("|") if p.strip()]
        if parts and parts[0] in MUNICIPALITIES:
            return parts[0]
        # Prefer prefecture-level unit and ignore county/district when an upper city exists.
        for idx, part in enumerate(parts):
            if part.endswith(("市", "州", "地区", "盟")) and idx >= 1:
                next_part = parts[idx + 1] if idx + 1 < len(parts) else ""
                if not next_part.endswith(("区", "县", "旗")):
                    return part
                return part
        return parts[1] if len(parts) > 1 else None
    if "-" in text:
        parts = [p.strip() for p in text.split("-") if p.strip()]
        if parts and parts[0] in MUNICIPALITIES:
            return parts[0]
        for idx, part in enumerate(parts):
            if part.endswith(("市", "州", "地区", "盟")) and idx >= 1:
                next_part = parts[idx + 1] if idx + 1 < len(parts) else ""
                if not next_part.endswith(("区", "县", "旗")):
                    return part
                return part
        return parts[1] if len(parts) > 1 else None
    if "省" in text or "自治区" in text:
        parts = re.split(r"[省自治区]", text)
        for part in parts:
            part = part.strip()
            if part.endswith(("市", "州", "地区", "盟")):
                return part
    if text.endswith(("市", "州", "地区", "盟")):
        return text
    return None


def assign_year(date_str: str) -> int | None:
    if date_str is None:
        return None
    text = str(date_str).strip()
    if not text or text in {"未披露", "--", "nan"}:
        return None
    dt = pd.to_datetime(text, errors="coerce")
    if pd.isna(dt):
        return None
    year = int(dt.year)
    # Funds established after June are assigned to next year.
    if int(dt.month) > 6:
        year += 1
    return year


def classify_unmatched_name(name: str) -> str:
    text = str(name)
    gov_keywords = [
        "引导基金",
        "产业基金",
        "财政",
        "国资",
        "国有",
        "城投",
        "产投",
        "金控",
        "国控",
        "资本运营",
        "投资控股集团",
        "开发区",
        "高新区",
        "经开区",
        "人民政府",
        "财政局",
        "资产经营",
        "城市投资",
        "国有资产",
    ]
    gp_keywords = [
        "管理有限公司",
        "投资管理",
        "基金管理",
        "资产管理",
        "私募基金管理",
        "普通合伙人",
        "执行事务合伙人",
    ]
    social_keywords = [
        "企业",
        "集团",
        "科技",
        "实业",
        "银行",
        "证券",
        "保险",
        "信托",
        "创投",
        "风投",
        "投资公司",
        "资本",
        "控股",
    ]

    if any(keyword in text for keyword in gov_keywords):
        return "government"
    if any(keyword in text for keyword in gp_keywords):
        return "gp_manager"
    if any(keyword in text for keyword in social_keywords):
        return "social"
    if re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", text):
        return "gp_manager"
    return "unknown"


def build_best_fund_table() -> pd.DataFrame:
    upper_path = find_file_by_suffix(BASE_DIR, "投中数据全部政府引导基金名录（上）.csv")
    lower_path = find_file_by_suffix(BASE_DIR, "投资数据全部政府引导基金目录（下）.csv")

    upper = read_named_csv(upper_path)
    lower = read_named_csv(lower_path)
    upper["source"] = "upper"
    lower["source"] = "lower"

    for df in (upper, lower):
        for column in ["基金简称", "基金全称", "成立时间", "所在地", "LP名称", "LP类型", "股东名称", "出资比例"]:
            if column not in df.columns:
                df[column] = ""

    upper["认缴金额统一"] = upper["认缴金额（万元）"] if "认缴金额（万元）" in upper.columns else ""
    lower["认缴金额统一"] = lower["认缴金额"] if "认缴金额" in lower.columns else ""

    merged = pd.concat([upper, lower], ignore_index=True, sort=False)
    merged["基金全称_key"] = merged["基金全称"].fillna("").astype(str).str.strip()

    for column in ["LP名称", "LP类型", "股东名称", "出资比例", "认缴金额统一", "所在地", "成立时间"]:
        merged[column] = merged[column].fillna("").astype(str)
        merged[f"{column}_nonempty"] = merged[column].str.strip().ne("")

    merged["score"] = (
        merged["股东名称_nonempty"].astype(int) * 4
        + merged["认缴金额统一_nonempty"].astype(int) * 4
        + merged["出资比例_nonempty"].astype(int) * 2
        + merged["LP名称_nonempty"].astype(int) * 2
        + merged["LP类型_nonempty"].astype(int) * 2
        + merged["所在地_nonempty"].astype(int)
        + merged["成立时间_nonempty"].astype(int)
    )
    merged = merged.sort_values(["基金全称_key", "score"], ascending=[True, False])
    return merged.drop_duplicates(subset=["基金全称_key"], keep="first").copy()


def classify_shareholder_amounts(fund_row: pd.Series) -> dict:
    social_lp_types = {"企业投资者", "VC/PE投资机构"}

    lp_names = split_items(fund_row["LP名称"])
    lp_types = split_items(fund_row["LP类型"])
    sh_names = split_items(fund_row["股东名称"])
    amounts = split_items(fund_row["认缴金额统一"])

    lp_map = {}
    for idx, lp_name in enumerate(lp_names):
        lp_type = lp_types[idx] if idx < len(lp_types) else ""
        lp_map[normalize_name(lp_name)] = lp_type.strip()

    social_amt = 0.0
    government_amt = 0.0
    gp_amt = 0.0
    unknown_amt = 0.0
    total_amt = 0.0
    matched_amt = 0.0
    exact_matches = 0
    fuzzy_matches = 0

    for idx, shareholder_name in enumerate(sh_names):
        amount = parse_amount(amounts[idx] if idx < len(amounts) else None)
        if amount is None:
            continue

        total_amt += amount
        norm_shareholder = normalize_name(shareholder_name)
        lp_type = lp_map.get(norm_shareholder, "")
        group = None

        if lp_type:
            matched_amt += amount
            exact_matches += 1
            group = "social" if lp_type in social_lp_types else "government"
        else:
            candidates = [candidate_type for candidate_name, candidate_type in lp_map.items() if candidate_name and (candidate_name in norm_shareholder or norm_shareholder in candidate_name)]
            if candidates:
                lp_type = candidates[0]
                matched_amt += amount
                fuzzy_matches += 1
                group = "social" if lp_type in social_lp_types else "government"
            else:
                group = classify_unmatched_name(shareholder_name)

        if group == "social":
            social_amt += amount
        elif group == "government":
            government_amt += amount
        elif group == "gp_manager":
            gp_amt += amount
        else:
            unknown_amt += amount

    return {
        "social_amt": social_amt,
        "government_amt": government_amt,
        "gp_amt": gp_amt,
        "unknown_amt": unknown_amt,
        "total_amt": total_amt,
        "matched_amt": matched_amt,
        "match_ratio_amt": matched_amt / total_amt if total_amt > 0 else None,
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
    }


def build_city_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    fund_table = build_best_fund_table()
    fund_rows = []
    stats = Counter()

    for _, row in fund_table.iterrows():
        city_name = extract_city(row["所在地"])
        year = assign_year(row["成立时间"])
        classified = classify_shareholder_amounts(row)

        if classified["total_amt"] > 0:
            stats["funds_with_amount"] += 1
        if classified["social_amt"] > 0:
            stats["funds_with_social"] += 1
        if classified["government_amt"] > 0:
            stats["funds_with_government"] += 1
        if classified["social_amt"] > 0 and classified["government_amt"] > 0:
            stats["funds_with_both"] += 1
        if city_name:
            stats["funds_with_city"] += 1
        if year:
            stats["funds_with_year"] += 1
        if city_name and year and classified["total_amt"] > 0:
            stats["funds_city_year_amount"] += 1

        fund_rows.append(
            {
                "基金简称": row["基金简称"],
                "基金全称": row["基金全称"],
                "source": row["source"],
                "成立时间": row["成立时间"],
                "city_name": city_name,
                "year": year,
                **classified,
            }
        )

    fund_level = pd.DataFrame(fund_rows)
    city_sample = fund_level.dropna(subset=["city_name", "year"]).copy()
    city_sample = city_sample[city_sample["total_amt"] > 0].copy()

    city_panel = (
        city_sample.groupby(["city_name", "year"], as_index=False)
        .agg(
            fund_count=("基金全称", "count"),
            social_amt=("social_amt", "sum"),
            government_amt=("government_amt", "sum"),
            gp_amt=("gp_amt", "sum"),
            unknown_amt=("unknown_amt", "sum"),
            total_amt=("total_amt", "sum"),
            matched_amt=("matched_amt", "sum"),
        )
        .sort_values(["city_name", "year"])
    )

    city_panel["social_share_total"] = city_panel["social_amt"] / city_panel["total_amt"]
    city_panel["government_share_total"] = city_panel["government_amt"] / city_panel["total_amt"]
    city_panel["social_to_government_ratio"] = city_panel["social_amt"] / city_panel["government_amt"]
    city_panel["matched_share_total"] = city_panel["matched_amt"] / city_panel["total_amt"]

    summary = pd.DataFrame(
        [
            {"metric": "dedup_funds", "value": len(fund_level)},
            {"metric": "funds_with_amount", "value": stats["funds_with_amount"]},
            {"metric": "funds_with_social", "value": stats["funds_with_social"]},
            {"metric": "funds_with_government", "value": stats["funds_with_government"]},
            {"metric": "funds_with_both", "value": stats["funds_with_both"]},
            {"metric": "funds_with_city", "value": stats["funds_with_city"]},
            {"metric": "funds_with_year", "value": stats["funds_with_year"]},
            {"metric": "funds_city_year_amount", "value": stats["funds_city_year_amount"]},
            {"metric": "city_year_rows", "value": len(city_panel)},
            {"metric": "city_count", "value": city_panel["city_name"].nunique()},
            {"metric": "match_ratio_amt_mean", "value": fund_level.loc[fund_level["total_amt"] > 0, "match_ratio_amt"].mean()},
            {"metric": "match_ratio_amt_median", "value": fund_level.loc[fund_level["total_amt"] > 0, "match_ratio_amt"].median()},
        ]
    )

    return fund_level, city_panel, summary


def main() -> None:
    fund_level, city_panel, summary = build_city_panel()

    fund_out = os.path.join(OUTPUT_DIR, "fund_social_capital_classified.csv")
    city_out = os.path.join(OUTPUT_DIR, "city_social_capital_panel.csv")
    summary_out = os.path.join(OUTPUT_DIR, "city_social_capital_panel_summary.csv")

    fund_level.to_csv(fund_out, index=False, encoding="utf-8-sig")
    city_panel.to_csv(city_out, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_out, index=False, encoding="utf-8-sig")

    print("fund_out =", fund_out)
    print("city_out =", city_out)
    print("summary_out =", summary_out)
    print(summary.to_string(index=False))
    print(city_panel.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
