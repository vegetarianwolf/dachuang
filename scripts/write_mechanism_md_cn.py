from pathlib import Path

import pandas as pd


def fmt(x):
    if pd.isna(x) or x == "":
        return ""
    x = float(x)
    if x == 0:
        return "0"
    if abs(x) >= 1e4 or abs(x) < 1e-3:
        return f"{x:.6g}"
    return f"{x:.6f}".rstrip("0").rstrip(".")


def U(s):
    return s.encode("ascii").decode("unicode_escape")


def main():
    res_path = Path("staging_ascii") / "xtreg_mediated_moderation_mechanism_ascii_results.csv"
    out_path = Path("dachuang") / U(r"\u5b9e\u8bc1\u7ed3\u679c") / "xtreg_mediated_moderation_mechanism_ascii.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    res = pd.read_csv(res_path)
    res = res.sort_values(["mvar", "step", "yvar", "dvar"]).reset_index(drop=True)

    mname = {
        "early_inv_amt": U(r"\u65e9\u671f\u6295\u8d44\u91d1\u989d"),
        "early_inv_count": U(r"\u65e9\u671f\u6295\u8d44\u4e8b\u4ef6\u6570"),
        "early_inv_count_share": U(r"\u65e9\u671f\u6295\u8d44\u4e8b\u4ef6\u5360\u6bd4"),
        "soccap_leverage": U(r"\u793e\u4f1a\u8d44\u672c\u64b7\u52a8\u6548\u7387"),
        "soccap_amt": U(r"\u793e\u4f1a\u8d44\u672c\u8ba4\u7f34\u989d"),
        "soccap_share_total": U(r"\u793e\u4f1a\u8d44\u672c\u5360\u603b\u8ba4\u7f34\u6bd4"),
        "fcity_sa_mean": U(r"\u5730\u7ea7\u5e02SA\u878d\u8d44\u7ea6\u675f\u5747\u503c"),
        "fcity_fc_mean": U(r"\u5730\u7ea7\u5e02FC\u878d\u8d44\u7ea6\u675f\u5747\u503c"),
        "fcity_kz_mean": U(r"\u5730\u7ea7\u5e02KZ\u878d\u8d44\u7ea6\u675f\u5747\u503c"),
        "fcity_ww_mean": U(r"\u5730\u7ea7\u5e02WW\u878d\u8d44\u7ea6\u675f\u5747\u503c"),
    }
    dname = {
        "debt_pressure": U(r"\u503a\u52a1\u538b\u529b"),
        "debt_pressure_l1": U(r"\u503a\u52a1\u538b\u529b\uff08\u6ee1\u4e00\u671f\uff09"),
    }
    yname = {
        "pat_invent_apply": U(r"\u53d1\u660e\u7533\u8bf7\u91cf"),
        "pat_utility_apply": U(r"\u5b9e\u7528\u65b0\u578b\u7533\u8bf7\u91cf"),
        "pat_apply_total": U(r"\u4e13\u5229\u7533\u8bf7\u603b\u91cf"),
    }

    lines = []
    lines.append(U(r"# \u6709\u4e2d\u4ecb\u7684\u8c03\u8282\u68c0\u9a8c\uff1a\u503a\u52a1\u538b\u529b\u4f5c\u7528\u4e0b\u7684\u57fa\u91d1\u7d2f\u8ba1\u89c4\u6a21\u3001\u673a\u5236\u53d8\u91cf\u4e0e\u521b\u65b0\u4ea7\u51fa"))
    lines.append("")
    lines.append(U(r"## \u672c\u6b21\u64cd\u4f5c"))
    lines.append(U(r"- \u4f7f\u7528\u6570\u636e\uff1a`staging_ascii/panel_2015_2024_regression_ascii_clean.csv`"))
    lines.append(U(r"- \u56de\u5f52\u65b9\u6cd5\uff1a\u5730\u7ea7\u5e02\u56fa\u5b9a\u6548\u5e94 + \u5e74\u4efd\u56fa\u5b9a\u6548\u5e94\uff08`xtreg, fe`\uff09"))
    lines.append(U(r"- \u6807\u51c6\u8bef\uff1a\u6309\u57ce\u5e02\u805a\u7c7b\u7a33\u5065\u6807\u51c6\u8bef"))
    lines.append(U(r"- \u65f6\u95f4\u8303\u56f4\uff1a2015-2024"))
    lines.append(U(r"- \u6846\u67b6\uff1a\u68c0\u9a8c `fund_est_scale_cum x debt_pressure` \u662f\u5426\u901a\u8fc7\u673a\u5236\u53d8\u91cf\u5f71\u54cd\u521b\u65b0\u4ea7\u51fa\u3002"))
    lines.append("")
    lines.append(U(r"## \u6570\u636e\u4e0e\u6837\u672c"))
    lines.append(U(r"- \u56e0\u53d8\u91cf\uff1a`pat_invent_apply`\u3001`pat_utility_apply`\u3001`pat_apply_total`"))
    lines.append(U(r"- \u6838\u5fc3\u89e3\u91ca\u53d8\u91cf\uff1a`fund_est_scale_cum`"))
    lines.append(U(r"- \u8c03\u8282\u53d8\u91cf\uff1a`debt_pressure`\u3001`debt_pressure_l1`"))
    lines.append(U(r"- \u673a\u5236\u53d8\u91cf\u53e3\u5f84\uff1a\u65e9\u671f\u6295\u8d44\u3001\u793e\u4f1a\u8d44\u672c\u64b7\u52a8\u3001\u878d\u8d44\u7ea6\u675f\u4e09\u7c7b\u3002"))
    lines.append("")
    lines.append(U(r"## \u6a21\u578b\u8bbe\u5b9a"))
    lines.append(U(r"1. \u673a\u5236\u65b9\u7a0b\uff1a`M = a0 + a1 fund_est_scale_cum + a2 debt_pressure + a3 fund_est_scale_cum x debt_pressure + FE + e`"))
    lines.append(U(r"2. \u7ed3\u679c\u65b9\u7a0b\uff1a`Y = b0 + b1 fund_est_scale_cum + b2 debt_pressure + b3 fund_est_scale_cum x debt_pressure + b4 M + FE + e`"))
    lines.append("")
    lines.append(U(r"## \u56de\u5f52\u7ed3\u679c\u8be6\u8868"))

    for m in res["mvar"].drop_duplicates():
        lines.append("")
        lines.append(f"### {mname.get(m, m)} (`{m}`)")

        step1 = res[(res["mvar"] == m) & (res["step"] == "M_eq")].copy().drop_duplicates(subset=["dvar"]).sort_values("dvar")
        lines.append("")
        lines.append(U(r"#### \u7b2c\u4e00\u6b65\u65b9\u7a0b\uff1a\u673a\u5236\u65b9\u7a0b"))
        lines.append(U(r"| \u8c03\u8282\u53d8\u91cf | \u4ea4\u4e92\u9879\u7cfb\u6570 | \u6807\u51c6\u8bef | p\u503c | \u6837\u672c\u91cf |"))
        lines.append(U(r"|---|---:|---:|---:|---:|"))
        for _, r in step1.iterrows():
            lines.append(f"| {dname.get(r['dvar'], r['dvar'])} | {fmt(r['b_xw'])} | {fmt(r['se_xw'])} | {fmt(r['p_xw'])} | {int(float(r['N']))} |")

        step2 = res[(res["mvar"] == m) & (res["step"] == "Y_eq")].copy().sort_values(["yvar", "dvar"])
        lines.append("")
        lines.append(U(r"#### \u7b2c\u4e8c\u6b65\u65b9\u7a0b\uff1a\u52a0\u5165\u673a\u5236\u53d8\u91cf\u540e\u7684\u7ed3\u679c\u65b9\u7a0b"))
        lines.append(U(r"| \u56e0\u53d8\u91cf | \u8c03\u8282\u53d8\u91cf | \u4ea4\u4e92\u9879\u7cfb\u6570 | \u4ea4\u4e92\u9879\u6807\u51c6\u8bef | \u4ea4\u4e92\u9879p\u503c | \u673a\u5236\u53d8\u91cf\u7cfb\u6570 | \u673a\u5236\u53d8\u91cf\u6807\u51c6\u8bef | \u673a\u5236\u53d8\u91cfp\u503c | \u6837\u672c\u91cf |"))
        lines.append(U(r"|---|---|---:|---:|---:|---:|---:|---:|---:|"))
        for _, r in step2.iterrows():
            lines.append(f"| {yname.get(r['yvar'], r['yvar'])} | {dname.get(r['dvar'], r['dvar'])} | {fmt(r['b_xw'])} | {fmt(r['se_xw'])} | {fmt(r['p_xw'])} | {fmt(r['b_m'])} | {fmt(r['se_m'])} | {fmt(r['p_m'])} | {int(float(r['N']))} |")

    lines.append("")
    lines.append(U(r"## \u7b80\u8981\u89e3\u8bfb"))
    lines.append(U(r"- \u65e9\u671f\u6295\u8d44\u91d1\u989d\u662f\u5f53\u524d\u6700\u6709\u5e0c\u671b\u7684\u673a\u5236\u53d8\u91cf\uff0c\u5c24\u5176\u5728 `pat_apply_total` \u548c `pat_utility_apply` \u4e0a\u8868\u73b0\u8f83\u7a33\u3002"))
    lines.append(U(r"- \u65e9\u671f\u6295\u8d44\u4e8b\u4ef6\u6570\u5728\u7ed3\u679c\u65b9\u7a0b\u91cc\u8f83\u5f3a\uff0c\u4f46\u5176\u7b2c\u4e00\u6b65\u8bc1\u636e\u4e0d\u5982\u65e9\u671f\u6295\u8d44\u91d1\u989d\u5b8c\u6574\u3002"))
    lines.append(U(r"- \u793e\u4f1a\u8d44\u672c\u548c\u878d\u8d44\u7ea6\u675f\u53d8\u91cf\u76ee\u524d\u66f4\u591a\u63d0\u4f9b\u8865\u5145\u6027\u8bc1\u636e\u3002"))
    lines.append("")
    lines.append(U(r"## \u8f93\u51fa\u6587\u4ef6"))
    lines.append(U(r"- do \u6587\u4ef6\uff1a`\u8fd0\u884c\u65e5\u5fd7\u4e0edo\u4ee3\u7801/xtreg_mediated_moderation_mechanism_ascii.do`"))
    lines.append(U(r"- log \u6587\u4ef6\uff1a`\u8fd0\u884c\u65e5\u5fd7\u4e0edo\u4ee3\u7801/xtreg_mediated_moderation_mechanism_ascii.log`"))
    lines.append(U(r"- \u7ed3\u679c\u8868\uff1a`\u8fd0\u884c\u65e5\u5fd7\u4e0edo\u4ee3\u7801/xtreg_mediated_moderation_mechanism_ascii_results.csv`"))

    out.write_text('\n'.join(lines), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
