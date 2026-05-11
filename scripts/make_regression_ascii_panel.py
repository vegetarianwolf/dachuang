import os

import pandas as pd


SRC = os.path.join(".", "staging_ascii", "panel_2015_2024_regression.csv")
OUT = os.path.join(".", "staging_ascii", "panel_2015_2024_regression_ascii.csv")


RENAME_MAP = {
    "城市": "city",
    "年份": "year",
    "基金当年设立数量": "fund_est_count",
    "基金当年设立规模_人民币万元": "fund_est_scale",
    "基金累计设立数量": "fund_est_count_cum",
    "基金累计设立规模_人民币万元": "fund_est_scale_cum",
    "基金近五年设立数量": "fund_est_count_roll5",
    "基金近五年设立规模_人民币万元": "fund_est_scale_roll5",
    "基金投资总额_人民币万元": "fund_inv_amt",
    "基金投资事件总数": "fund_inv_count",
    "早期投资金额_人民币万元": "early_inv_amt",
    "早期投资事件数": "early_inv_count",
    "早期投资金额占比": "early_inv_amt_share",
    "早期投资事件占比": "early_inv_count_share",
    "发明申请量": "pat_invent_apply",
    "实用新型申请量": "pat_utility_apply",
    "外观设计申请量": "pat_design_apply",
    "发明获得量": "pat_invent_grant",
    "实用新型获得量": "pat_utility_grant",
    "外观设计获得量": "pat_design_grant",
    "专利申请总量": "pat_apply_total",
    "专利获得总量": "pat_grant_total",
    "发明申请量_对数": "ln_pat_invent_apply",
    "实用新型申请量_对数": "ln_pat_utility_apply",
    "外观设计申请量_对数": "ln_pat_design_apply",
    "发明获得量_对数": "ln_pat_invent_grant",
    "实用新型获得量_对数": "ln_pat_utility_grant",
    "外观设计获得量_对数": "ln_pat_design_grant",
    "专利申请总量_对数": "ln_pat_apply_total",
    "专利获得总量_对数": "ln_pat_grant_total",
    "财政收支压力": "fiscal_pressure",
    "财政收支压力_滞后一期": "fiscal_pressure_l1",
    "地方政府债余额_亿": "lg_debt",
    "城投债余额_亿": "lgfv_debt",
    "债券余额合计_亿": "bond_total",
    "GDP_债务表_亿": "gdp_debt_src",
    "公共财政收入_亿": "fiscal_revenue",
    "公共财政支出_亿": "fiscal_expenditure",
    "债务负担": "debt_burden",
    "债务压力": "debt_pressure",
    "财政自给率": "fiscal_selfsuff",
    "债务负担_滞后一期": "debt_burden_l1",
    "债务压力_滞后一期": "debt_pressure_l1",
    "财政自给率_滞后一期": "fiscal_selfsuff_l1",
    "社会资本口径基金数量": "soccap_fund_count",
    "社会资本认缴额": "soccap_amt",
    "政府认缴额": "gov_amt",
    "GP认缴额": "gp_amt",
    "未知类型认缴额": "unknown_amt",
    "基金总认缴额": "fund_commit_total",
    "已匹配认缴额": "matched_commit_amt",
    "社会资本占总认缴比": "soccap_share_total",
    "政府出资占总认缴比": "gov_share_total",
    "社会资本撬动效率": "soccap_leverage",
    "已匹配认缴额占比": "matched_share_total",
    "政府财政透明度": "fiscal_transparency",
    "地级市SA融资约束均值": "fcity_sa_mean",
    "地级市SA融资约束均值_样本企业数": "fcity_sa_firms",
    "地级市SA融资约束均值_中位数": "fcity_sa_median",
    "地级市SA融资约束均值_原值均值": "fcity_sa_rawmean",
    "地级市FC融资约束均值": "fcity_fc_mean",
    "地级市FC融资约束均值_样本企业数": "fcity_fc_firms",
    "地级市FC融资约束均值_中位数": "fcity_fc_median",
    "地级市KZ融资约束均值": "fcity_kz_mean",
    "地级市KZ融资约束均值_样本企业数": "fcity_kz_firms",
    "地级市KZ融资约束均值_中位数": "fcity_kz_median",
    "地级市WW融资约束均值": "fcity_ww_mean",
    "地级市WW融资约束均值_样本企业数": "fcity_ww_firms",
    "地级市WW融资约束均值_中位数": "fcity_ww_median",
    "年末金融机构各项贷款余额": "loan_balance_yearend",
    "年末金融机构存款余额": "deposit_balance_yearend",
    "金融发展口径地区生产总值": "gdp_finance_src",
    "金融发展水平1": "fin_dev_1",
    "金融发展水平2": "fin_dev_2",
    "金融发展水平": "fin_dev",
    "市场化水平": "marketization",
    "地区生产总值": "gdp",
    "财政科技支出": "fiscal_scitech",
    "常住人口": "population_resident",
    "第二产业增加值": "secondary_industry",
    "实际利用外资额": "fdi_actual",
}


def main() -> None:
    df = pd.read_csv(SRC, encoding="utf-8-sig")
    df = df.rename(columns=RENAME_MAP)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(OUT)
    print(df.columns.tolist())


if __name__ == "__main__":
    main()
