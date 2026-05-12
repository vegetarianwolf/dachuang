# 机制检验总览：早期投资、社会资本撬动效率与融资约束

## 本次操作
- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`
- 基准主线：`fund_est_scale_cum × debt_pressure` 与 `fund_est_scale_cum × debt_pressure_l1`
- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`
- 机制模型 A：`X × N -> M -> Y`
- 机制模型 B：先检验 `N -> M`，再在结果方程中加入 `X × M`
- 结果总行数：`608`

## 各类别显著性概览
| category | model | mvar | M_eq_sig | Y_term1_sig | Y_term2_sig | Y_term3_sig | total_rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 早期投资 | mediated | early_inv_amt_share | 3 | 7 | 0 | 0 | 16 |
| 早期投资 | mediated | early_inv_amt | 2 | 8 | 11 | 0 | 16 |
| 早期投资 | mediated | early_inv_count | 0 | 10 | 12 | 0 | 16 |
| 早期投资 | mediated | early_inv_count_share | 0 | 9 | 0 | 0 | 16 |
| 早期投资 | moderator | early_inv_count | 4 | 12 | 8 | 10 | 16 |
| 早期投资 | moderator | early_inv_count_share | 2 | 8 | 0 | 1 | 16 |
| 早期投资 | moderator | early_inv_amt_share | 2 | 7 | 0 | 1 | 16 |
| 早期投资 | moderator | early_inv_amt | 1 | 12 | 9 | 8 | 16 |
| 社会资本撬动效率 | mediated | gov_amt | 2 | 8 | 8 | 0 | 16 |
| 社会资本撬动效率 | mediated | matched_commit_amt | 2 | 8 | 8 | 0 | 16 |
| 社会资本撬动效率 | mediated | fund_commit_total | 2 | 8 | 4 | 0 | 16 |
| 社会资本撬动效率 | mediated | unknown_amt | 2 | 8 | 4 | 0 | 16 |
| 社会资本撬动效率 | mediated | gp_amt | 0 | 8 | 12 | 0 | 16 |
| 社会资本撬动效率 | mediated | soccap_amt | 0 | 8 | 6 | 0 | 16 |
| 社会资本撬动效率 | mediated | matched_share_total | 0 | 8 | 4 | 0 | 16 |
| 社会资本撬动效率 | mediated | soccap_fund_count | 0 | 8 | 2 | 0 | 16 |
| 社会资本撬动效率 | mediated | gov_share_total | 0 | 8 | 1 | 0 | 16 |
| 社会资本撬动效率 | mediated | soccap_share_total | 0 | 8 | 1 | 0 | 16 |
| 社会资本撬动效率 | mediated | soccap_leverage | 0 | 8 | 0 | 0 | 16 |
| 社会资本撬动效率 | moderator | gov_amt | 4 | 8 | 3 | 4 | 16 |
| 社会资本撬动效率 | moderator | matched_commit_amt | 4 | 8 | 3 | 4 | 16 |
| 社会资本撬动效率 | moderator | fund_commit_total | 4 | 8 | 2 | 3 | 16 |
| 社会资本撬动效率 | moderator | soccap_amt | 2 | 8 | 2 | 3 | 16 |
| 社会资本撬动效率 | moderator | unknown_amt | 2 | 8 | 2 | 3 | 16 |
| 社会资本撬动效率 | moderator | soccap_leverage | 1 | 8 | 0 | 0 | 16 |
| 社会资本撬动效率 | moderator | matched_share_total | 0 | 8 | 2 | 4 | 16 |
| 社会资本撬动效率 | moderator | gov_share_total | 0 | 10 | 1 | 4 | 16 |
| 社会资本撬动效率 | moderator | gp_amt | 0 | 8 | 0 | 4 | 16 |
| 社会资本撬动效率 | moderator | soccap_share_total | 0 | 9 | 1 | 2 | 16 |
| 社会资本撬动效率 | moderator | soccap_fund_count | 0 | 7 | 1 | 2 | 16 |
| 融资约束 | mediated | fcity_fc_mean | 4 | 10 | 0 | 0 | 16 |
| 融资约束 | mediated | fcity_ww_mean | 2 | 9 | 0 | 0 | 16 |
| 融资约束 | mediated | fcity_sa_mean | 0 | 10 | 5 | 0 | 16 |
| 融资约束 | mediated | fcity_kz_mean | 0 | 10 | 0 | 0 | 16 |
| 融资约束 | moderator | fcity_kz_mean | 4 | 6 | 2 | 2 | 16 |
| 融资约束 | moderator | fcity_fc_mean | 1 | 12 | 9 | 12 | 16 |
| 融资约束 | moderator | fcity_sa_mean | 0 | 12 | 7 | 12 | 16 |
| 融资约束 | moderator | fcity_ww_mean | 0 | 10 | 0 | 0 | 16 |

## 结论摘要
- 早期投资类中，`early_inv_amt`、`early_inv_amt_share` 在机制方程里更容易出现显著，`early_inv_count` 在结果方程里显著最多。
- 社会资本类中，`gov_amt`、`matched_commit_amt`、`fund_commit_total`、`gp_amt` 的信号相对更多，`soccap_leverage` 本身并不是最强口径。
- 融资约束类中，`fcity_fc_mean` 在机制方程里最稳定；若把机制变量视为调节变量，则 `fcity_fc_mean` 与 `fcity_sa_mean` 的 `X × M` 项显著最多。
- 大多数结果方程里，原始债务调节项 `fund_est_scale_cum × debt_pressure` 仍保持负向显著，说明债务压力削弱基金扶持创新效果这一主结论较稳。

## 输出文件
- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`
- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`
- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`