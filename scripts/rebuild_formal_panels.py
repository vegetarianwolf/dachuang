import os
import sys
from pathlib import Path

import pandas as pd


ROOT = os.path.join(".", "dachuang")
PANEL_DIR = os.path.join(ROOT, "面板数据")
STAGING_DIR = os.path.join(".", "staging_ascii")


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def write_csv_with_fallback(df: pd.DataFrame, path: str) -> str:
    ensure_parent(path)
    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path
    except PermissionError:
        base, ext = os.path.splitext(path)
        fallback = f"{base}__rebuilt{ext}"
        df.to_csv(fallback, index=False, encoding="utf-8-sig")
        return fallback


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    import build_city_panel_master as master_mod
    import build_city_fund_investment_panel as invest_mod
    import build_social_capital_city_panel as soccap_mod
    import make_regression_ascii_panel as rename_mod

    # Rebuild city-level investment-event panel from the raw matched event table.
    invest_source = invest_mod.find_source_file(Path(ROOT))
    invest_rows, invest_audit = invest_mod.build_panel(invest_source)
    invest_out = os.path.join(PANEL_DIR, "市级基金投资事件面板_2015_2024.csv")
    invest_mod.write_panel(invest_rows, Path(invest_out))
    print("investment_panel_out", invest_out)
    for key in sorted(invest_audit):
        print(f"investment_{key}", invest_audit[key])

    # Rebuild social-capital sources first so the master panel consumes fixed city names.
    fund_level, city_panel, summary = soccap_mod.build_city_panel()
    raw_city_dir = os.path.join(ROOT, "原始数据打包_20260401", "市级数据")
    write_csv_with_fallback(fund_level, os.path.join(raw_city_dir, "fund_social_capital_classified.csv"))
    write_csv_with_fallback(city_panel, os.path.join(raw_city_dir, "city_social_capital_panel.csv"))
    write_csv_with_fallback(summary, os.path.join(raw_city_dir, "city_social_capital_panel_summary.csv"))

    panel = master_mod.build_master_panel().sort_values(["城市", "年份"]).reset_index(drop=True)
    missing = master_mod.build_missing_summary(panel)
    sample_summary = pd.DataFrame(
        [
            {"指标": "总样本量", "数值": len(panel)},
            {"指标": "城市数", "数值": panel["城市"].nunique()},
            {"指标": "年份最小值", "数值": panel["年份"].min()},
            {"指标": "年份最大值", "数值": panel["年份"].max()},
        ]
    )

    cn_master = os.path.join(PANEL_DIR, "地级市总面板_编制版.csv")
    cn_master_missing = os.path.join(PANEL_DIR, "地级市总面板_缺失统计.csv")
    cn_master_sample = os.path.join(PANEL_DIR, "地级市总面板_样本统计.csv")
    cn_master_out = write_csv_with_fallback(panel, cn_master)
    cn_master_missing_out = write_csv_with_fallback(missing, cn_master_missing)
    cn_master_sample_out = write_csv_with_fallback(sample_summary, cn_master_sample)

    formal_master_cn = os.path.join(STAGING_DIR, "formal_master_cn.csv")
    formal_master_cn_out = write_csv_with_fallback(panel, formal_master_cn)
    master_rows = len(panel)

    panel_2015 = panel[(panel["年份"] >= 2015) & (panel["年份"] <= 2024)].copy()
    patent_cols = [
        "发明申请量",
        "实用新型申请量",
        "外观设计申请量",
        "发明获得量",
        "实用新型获得量",
        "外观设计获得量",
        "专利申请总量",
        "专利获得总量",
        "发明申请量_对数",
        "实用新型申请量_对数",
        "外观设计申请量_对数",
        "发明获得量_对数",
        "实用新型获得量_对数",
        "外观设计获得量_对数",
        "专利申请总量_对数",
        "专利获得总量_对数",
    ]
    panel_2015 = master_mod.with_lag(panel_2015, [col for col in patent_cols if col in panel_2015.columns])
    panel_2015 = panel_2015.sort_values(["城市", "年份"]).reset_index(drop=True)
    missing_2015 = master_mod.build_missing_summary(panel_2015)
    sample_2015 = pd.DataFrame(
        [
            {"指标": "总样本量", "数值": len(panel_2015)},
            {"指标": "城市数", "数值": panel_2015["城市"].nunique()},
            {"指标": "最小年份", "数值": panel_2015["年份"].min()},
            {"指标": "最大年份", "数值": panel_2015["年份"].max()},
        ]
    )

    cn_2015 = os.path.join(PANEL_DIR, "地级市总面板_2015_2024版.csv")
    cn_2015_missing = os.path.join(PANEL_DIR, "地级市总面板_2015_2024版_缺失统计.csv")
    cn_2015_sample = os.path.join(PANEL_DIR, "地级市总面板_2015_2024版_样本统计.csv")
    cn_2015_out = write_csv_with_fallback(panel_2015, cn_2015)
    cn_2015_missing_out = write_csv_with_fallback(missing_2015, cn_2015_missing)
    cn_2015_sample_out = write_csv_with_fallback(sample_2015, cn_2015_sample)

    formal_2015_cn = os.path.join(STAGING_DIR, "formal_2015_cn.csv")
    formal_2015_cn_out = write_csv_with_fallback(panel_2015, formal_2015_cn)
    regression_cn = os.path.join(STAGING_DIR, "panel_2015_2024_regression.csv")
    regression_cn_out = write_csv_with_fallback(panel_2015, regression_cn)

    rename_mod.SRC = regression_cn_out
    rename_mod.OUT = os.path.join(STAGING_DIR, "panel_2015_2024_regression_ascii.csv")
    rename_mod.main()

    english_panel = pd.read_csv(rename_mod.OUT, encoding="utf-8-sig")
    english_panel_out = write_csv_with_fallback(english_panel, os.path.join(PANEL_DIR, "地级市总面板_2015_2024_英文版.csv"))
    formal_2015_en_out = write_csv_with_fallback(english_panel, os.path.join(STAGING_DIR, "formal_2015_en.csv"))

    print("master_rows", master_rows)
    print("panel_2015_rows", len(panel_2015))
    print("master_out", cn_master_out)
    print("master_missing_out", cn_master_missing_out)
    print("master_sample_out", cn_master_sample_out)
    print("formal_master_cn_out", formal_master_cn_out)
    print("panel_2015_out", cn_2015_out)
    print("panel_2015_missing_out", cn_2015_missing_out)
    print("panel_2015_sample_out", cn_2015_sample_out)
    print("formal_2015_cn_out", formal_2015_cn_out)
    print("regression_cn_out", regression_cn_out)
    print("english_panel_out", english_panel_out)
    print("formal_2015_en_out", formal_2015_en_out)


if __name__ == "__main__":
    main()
