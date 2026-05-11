# 基准回归尝试：地级市基金规模与创新产出

## 本次操作
- 使用数据：`staging_ascii/panel_2015_2024_regression_ascii.csv`
- 回归方法：地级市固定效应 + 年份固定效应（`xtreg, fe`）
- 标准误：按城市聚类稳健标准误
- 时间范围：2015-2024
- 说明：本次为基准回归尝试，分别比较“不加控制变量”和“加入核心控制变量”两组模型。

## 数据与样本
- 基金规模变量：
  - `fund_est_count`：基金当年设立数量
  - `fund_est_scale`：基金当年设立规模
  - `fund_est_count_cum`：基金累计设立数量
  - `fund_est_scale_cum`：基金累计设立规模
- 创新产出变量：
  - `pat_invent_apply`：发明申请量
  - `pat_utility_apply`：实用新型申请量
  - `pat_apply_total`：专利申请总量
  - `ln_pat_invent_apply`、`ln_pat_utility_apply`、`ln_pat_apply_total`
- 控制变量版本使用：
  - `ln_gdp`
  - `ln_fiscal_scitech`
  - `ln_pop`
  - `ln_secondary`
  - `ln_fdi`
- 重复城市年份处理：在回归前按 `city-year` 进行一次 `collapse (firstnm)` 去重。

## 模型设定
- 无控制模型：
  - `xtreg y x i.year, fe vce(cluster city_id)`
- 加控制变量模型：
  - `xtreg y x ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, fe vce(cluster city_id)`

## 回归结果

### 1. 水平值因变量
- `pat_invent_apply`
  - `fund_est_count`：无控制 `b=189.4393, p<0.001, N=2670`；加控制 `b=297.1917, p<0.001, N=1149`
  - `fund_est_count_cum`：无控制 `b=65.0795, p=0.0025, N=2670`；加控制 `b=106.7968, p<0.001, N=1149`
  - `fund_est_scale_cum`：无控制 `b=0.0259, p<0.001, N=2529`；加控制 `b=0.0300, p<0.001, N=1083`
  - `fund_est_scale`：两组都不显著
- `pat_utility_apply`
  - `fund_est_count`：无控制 `b=465.4807, p<0.001, N=2670`；加控制 `b=458.0812, p<0.001, N=1149`
  - `fund_est_count_cum`：无控制 `b=75.8634, p<0.001, N=2670`；加控制 `b=151.4863, p=0.0057, N=1149`
  - `fund_est_scale_cum`：无控制 `b=0.0281, p<0.001, N=2529`；加控制 `b=0.0405, p=0.0031, N=1083`
  - `fund_est_scale`：两组都不显著
- `pat_apply_total`
  - `fund_est_count`：无控制 `b=739.5500, p<0.001, N=2670`；加控制 `b=849.5984, p=0.0018, N=1149`
  - `fund_est_count_cum`：无控制 `b=161.7675, p<0.001, N=2670`；加控制 `b=296.7709, p=0.0120, N=1149`
  - `fund_est_scale_cum`：无控制 `b=0.0612, p<0.001, N=2529`；加控制 `b=0.0800, p=0.0174, N=1083`
  - `fund_est_scale`：两组都不显著

### 2. 对数因变量
- `ln_pat_invent_apply`
  - `fund_est_scale_cum`：无控制 `b=4.01e-07, p=0.0058, N=2529`；加控制 `b=4.02e-07, p=0.0204, N=1083`
  - 其他口径不显著
- `ln_pat_utility_apply`
  - `fund_est_count`：加控制 `b=0.00381, p=0.0443, N=1149`
  - `fund_est_count_cum`：无控制 `b=-0.00128, p=0.0010, N=2670`
  - `fund_est_scale_cum`：无控制 `b=-2.91e-07, p=0.0081, N=2529`
  - 其余不显著
- `ln_pat_apply_total`
  - 各口径均不显著

## 简要解读
- 在地级市和年份固定效应下，基金“数量”口径和“累计规模”口径比“当年规模”口径更稳定。
- 发明申请量、实用新型申请量和专利申请总量对基金设立变量反应较强，说明政府引导基金扩张与技术型创新申请之间存在较明显正相关。
- 加入控制变量后，主结论总体没有消失，尤其 `fund_est_count` 和 `fund_est_scale_cum` 依旧较稳。
- 对数因变量结果明显弱于水平值因变量，且个别模型出现负号，说明 log 口径下的结果暂不宜直接作为主结论。
- 因此后续正式基准模型建议优先围绕：
  - `pat_invent_apply`
  - `pat_utility_apply`
  - `pat_apply_total`
  - 配合 `fund_est_count` 与 `fund_est_scale_cum`

## 输出文件
- do 文件：`运行日志与do代码/xtreg_fe_baseline_fund_innovation_combo_ascii.do`
- log 文件：`运行日志与do代码/xtreg_fe_baseline_fund_innovation_combo_ascii.log`
- 结果表：`运行日志与do代码/xtreg_fe_baseline_fund_innovation_combo_ascii_results.csv`
