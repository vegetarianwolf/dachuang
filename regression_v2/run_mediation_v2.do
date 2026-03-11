/*===========================================================================
  regression_v2/run_mediation_v2.do
  中介效应模型回归分析（Stata版）
  
  对应 Python 版本 run_mediation_v2.py 的完整复现
  
  模型: 财政约束(X) → 政府风险偏好(M) → 地区创新产出(Y)
  方法: 双向固定效应 + 城市层面聚类标准误
  数据处理: 去除发明专利=0 + 1%/99%缩尾
===========================================================================*/

clear all
set more off

local basedir "C:/Users/21288/Desktop/DACHUANG/dachuang"
local datapath "`basedir'/cleaned_data/final_regression_panel_v4.csv"
local outdir "`basedir'/regression_v2"

cap log close _all
log using "`outdir'/stata_results_log.txt", replace text name(main)

di "============================================================"
di "  中介效应模型回归分析（Stata版 v2）"
di "  运行时间: $S_DATE $S_TIME"
di "============================================================"

*===========================================================================
* 1. 数据导入与变量重命名
*===========================================================================
di _n "========== 1. 数据导入 =========="

import delimited "`datapath'", clear encoding(utf-8) varnames(1)
di "原始数据: " _N " 行, 34 列"

rename 省份              province
rename 城市              city
rename 年份              year
rename 发明受理数        inv_cnt
rename 专利受理总数      pat_cnt
rename 发明专利受理量_对数   ln_inv
rename 专利受理总量_对数     ln_pat
rename 发明专利占比          inv_share
rename 财政缺口率            fiscal_gap
rename 财政缺口率_滞后一期   fiscal_gap_l1
rename 债务率                debt_ratio
rename 债务率_滞后一期       debt_ratio_l1
rename 人均gdp_对数          gdp_pc_ln
rename 第二产业占比          ind2_share
rename 科技支出占比          tech_exp
rename 外资依存度            fdi_ratio
rename 金融深度              fin_depth
rename 人均专利受理量        pat_per_cap
rename 基金投资总次数_滞后一期     fund_cnt_l1
rename 基金投资总金额_百万_滞后一期  fund_amt_l1
rename 早期投资次数_滞后一期       early_cnt_l1
rename 早期投资金额_百万_滞后一期  early_amt_l1
rename 早期投资次数占比_滞后一期   early_deal_l1
rename 早期投资金额占比_滞后一期   early_amt_ratio_l1

*===========================================================================
* 2. 数据清洗
*===========================================================================
di _n "========== 2. 数据清洗 =========="

* 2a. 去除发明专利受理数=0
di "去除前: " _N
drop if inv_cnt == 0
di "去除发明受理数=0后: " _N

* 2b. 构造 ln(债务率_滞后一期)
gen ln_debt_l1 = ln(debt_ratio_l1) if debt_ratio_l1 > 0
label variable ln_debt_l1 "ln(债务率)(滞后一期)"

* 2c. 构造中介变量 —— 仅对有基金活动的城市-年份定义
gen M_deal = early_deal_l1 if fund_cnt_l1 > 0 & fund_cnt_l1 < .
gen M_amount = early_amt_ratio_l1 if fund_amt_l1 > 0 & fund_amt_l1 < .
label variable M_deal "早期投资次数占比(L1,仅有基金)"
label variable M_amount "早期投资金额占比(L1,仅有基金)"

di "M_deal 有效: " 
count if M_deal < .
di "M_amount 有效: "
count if M_amount < .

* 2d. 缩尾处理 1%/99%
foreach v in ln_inv ln_pat inv_share fiscal_gap_l1 ln_debt_l1 ///
             M_deal M_amount gdp_pc_ln ind2_share tech_exp fdi_ratio fin_depth {
    quietly {
        sum `v', detail
        if r(N) > 20 {
            local p1 = r(p1)
            local p99 = r(p99)
            replace `v' = `p1' if `v' < `p1' & `v' < .
            replace `v' = `p99' if `v' > `p99' & `v' < .
        }
    }
}
di "缩尾处理完成 (1%/99%)"

* 2e. 去除财政缺口率<0的异常值
drop if fiscal_gap_l1 < 0 & fiscal_gap_l1 < .
di "最终样本: " _N

*===========================================================================
* 3. 面板设定
*===========================================================================
di _n "========== 3. 面板设定 =========="

encode city, gen(city_id)
xtset city_id year
di "面板结构设定完成"

*===========================================================================
* 4. 描述性统计
*===========================================================================
di _n "========== 4. 描述性统计 =========="

tabstat ln_inv ln_pat inv_share fiscal_gap_l1 ln_debt_l1 ///
    M_deal M_amount gdp_pc_ln ind2_share tech_exp, ///
    stat(N mean sd min p25 p50 p75 max) columns(statistics) format(%9.4f)

*===========================================================================
* 5. 基准回归 (H1: 财政约束 → 创新产出)
*===========================================================================
di _n "============================================================"
di "  5. 基准回归 (H1)"
di "============================================================"

local controls_core "gdp_pc_ln ind2_share tech_exp"
local controls_full "gdp_pc_ln ind2_share tech_exp fdi_ratio fin_depth"

* --- 5a. 无控制变量 ---
di _n "--- 5a. 无控制变量 ---"

* (1) ln(发明专利) ~ 财政缺口率
xtreg ln_inv fiscal_gap_l1 i.year, fe vce(cluster city_id)
estimates store base_nc_fg_inv

* (2) ln(专利总量) ~ 财政缺口率
xtreg ln_pat fiscal_gap_l1 i.year, fe vce(cluster city_id)
estimates store base_nc_fg_pat

* (3) 发明专利占比 ~ 财政缺口率
xtreg inv_share fiscal_gap_l1 i.year, fe vce(cluster city_id)
estimates store base_nc_fg_share

* (4) ln(发明专利) ~ ln(债务率)
xtreg ln_inv ln_debt_l1 i.year, fe vce(cluster city_id)
estimates store base_nc_debt_inv

* (5) ln(专利总量) ~ ln(债务率)
xtreg ln_pat ln_debt_l1 i.year, fe vce(cluster city_id)
estimates store base_nc_debt_pat

* (6) 发明专利占比 ~ ln(债务率)
xtreg inv_share ln_debt_l1 i.year, fe vce(cluster city_id)
estimates store base_nc_debt_share

* --- 5b. 核心控制变量 ---
di _n "--- 5b. 核心控制变量 ---"

* (1) ln(发明专利) ~ 财政缺口率 + 核心控制
xtreg ln_inv fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store base_cc_fg_inv

* (2) ln(专利总量) ~ 财政缺口率 + 核心控制
xtreg ln_pat fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store base_cc_fg_pat

* (3) 发明专利占比 ~ 财政缺口率 + 核心控制
xtreg inv_share fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store base_cc_fg_share

* (4) ln(发明专利) ~ ln(债务率) + 核心控制
xtreg ln_inv ln_debt_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store base_cc_debt_inv

* --- 5c. 完整控制变量 ---
di _n "--- 5c. 完整控制变量 ---"

xtreg ln_inv fiscal_gap_l1 `controls_full' i.year, fe vce(cluster city_id)
estimates store base_fc_fg_inv

xtreg ln_inv ln_debt_l1 `controls_full' i.year, fe vce(cluster city_id)
estimates store base_fc_debt_inv

* --- 基准回归汇总表 ---
di _n "========== 基准回归结果汇总 =========="

di _n ">>> 表1: 无控制变量"
estimates table base_nc_fg_inv base_nc_fg_pat base_nc_fg_share ///
    base_nc_debt_inv base_nc_debt_pat base_nc_debt_share, ///
    keep(fiscal_gap_l1 ln_debt_l1) b(%9.4f) se(%9.4f) stats(N r2_w)

di _n ">>> 表2: 核心控制变量 (DV=ln(发明专利))"
estimates table base_cc_fg_inv base_cc_debt_inv, ///
    keep(fiscal_gap_l1 ln_debt_l1 `controls_core') b(%9.4f) se(%9.4f) stats(N r2_w)

di _n ">>> 表3: 完整控制变量 (DV=ln(发明专利))"
estimates table base_fc_fg_inv base_fc_debt_inv, ///
    keep(fiscal_gap_l1 ln_debt_l1 `controls_full') b(%9.4f) se(%9.4f) stats(N r2_w)

*===========================================================================
* 6. 中介效应检验 (H2: X → M → Y)
*===========================================================================
di _n "============================================================"
di "  6. 中介效应检验 (H2: Baron-Kenny三步法 + Sobel)"
di "============================================================"

* -----------------------------------------------------------------------
* 6.1 财政缺口率 → M_deal(次数占比) → ln(发明专利) [无控制]
* -----------------------------------------------------------------------
di _n "====== 6.1 fiscal_gap → M_deal → ln_inv (无控制) ======"

* Step 0: 总效应 X→Y
xtreg ln_inv fiscal_gap_l1 i.year, fe vce(cluster city_id)
estimates store med1_s0
local c_total = _b[fiscal_gap_l1]
local p_total = 2*ttail(e(df_r), abs(_b[fiscal_gap_l1]/_se[fiscal_gap_l1]))

* Step 1: X→M
xtreg M_deal fiscal_gap_l1 i.year, fe vce(cluster city_id)
estimates store med1_s1
local a = _b[fiscal_gap_l1]
local se_a = _se[fiscal_gap_l1]
local p_xm = 2*ttail(e(df_r), abs(`a'/`se_a'))

* Step 2: X+M→Y
xtreg ln_inv fiscal_gap_l1 M_deal i.year, fe vce(cluster city_id)
estimates store med1_s2
local c_prime = _b[fiscal_gap_l1]
local b = _b[M_deal]
local se_b = _se[M_deal]
local p_my = 2*ttail(e(df_r), abs(`b'/`se_b'))

* Sobel test
local ab = `a' * `b'
local se_sobel = sqrt(`a'^2 * `se_b'^2 + `b'^2 * `se_a'^2)
local z_sobel = `ab' / `se_sobel'
local p_sobel = 2*(1 - normal(abs(`z_sobel')))

di _n ">>> 中介效应汇总 (fiscal_gap → M_deal → ln_inv, 无控制):"
di "总效应 c = " %9.4f `c_total' "  p = " %6.4f `p_total'
di "路径 a (X→M) = " %9.4f `a' "  se = " %9.4f `se_a' "  p = " %6.4f `p_xm'
di "路径 b (M→Y|X) = " %9.4f `b' "  se = " %9.4f `se_b' "  p = " %6.4f `p_my'
di "直接效应 c' = " %9.4f `c_prime'
di "间接效应 a*b = " %9.6f `ab'
di "Sobel Z = " %9.4f `z_sobel' "  p = " %6.4f `p_sobel'
if `c_total' != 0 {
    di "中介效应占比 = " %9.2f (`ab'/`c_total'*100) "%"
}

* -----------------------------------------------------------------------
* 6.2 财政缺口率 → M_deal → ln(发明专利) [核心控制] ★主模型★
* -----------------------------------------------------------------------
di _n "====== 6.2 fiscal_gap → M_deal → ln_inv (核心控制) ★主模型★ ======"

* Step 0: 总效应
xtreg ln_inv fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store med2_s0
local c_total = _b[fiscal_gap_l1]
local p_total = 2*ttail(e(df_r), abs(_b[fiscal_gap_l1]/_se[fiscal_gap_l1]))

* Step 1: X→M
xtreg M_deal fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store med2_s1
local a = _b[fiscal_gap_l1]
local se_a = _se[fiscal_gap_l1]
local p_xm = 2*ttail(e(df_r), abs(`a'/`se_a'))

* Step 2: X+M→Y
xtreg ln_inv fiscal_gap_l1 M_deal `controls_core' i.year, fe vce(cluster city_id)
estimates store med2_s2
local c_prime = _b[fiscal_gap_l1]
local b = _b[M_deal]
local se_b = _se[M_deal]
local p_my = 2*ttail(e(df_r), abs(`b'/`se_b'))

* Sobel
local ab = `a' * `b'
local se_sobel = sqrt(`a'^2 * `se_b'^2 + `b'^2 * `se_a'^2)
local z_sobel = `ab' / `se_sobel'
local p_sobel = 2*(1 - normal(abs(`z_sobel')))

di _n ">>> 中介效应汇总 (fiscal_gap → M_deal → ln_inv, 核心控制) ★主模型★:"
di "总效应 c = " %9.4f `c_total' "  p = " %6.4f `p_total'
di "路径 a (X→M) = " %9.4f `a' "  se = " %9.4f `se_a' "  p = " %6.4f `p_xm'
di "路径 b (M→Y|X) = " %9.4f `b' "  se = " %9.4f `se_b' "  p = " %6.4f `p_my'
di "直接效应 c' = " %9.4f `c_prime'
di "间接效应 a*b = " %9.6f `ab'
di "Sobel Z = " %9.4f `z_sobel' "  p = " %6.4f `p_sobel'
if `c_total' != 0 {
    di "中介效应占比 = " %9.2f (`ab'/`c_total'*100) "%"
}

estimates table med2_s0 med2_s1 med2_s2, ///
    keep(fiscal_gap_l1 M_deal `controls_core') b(%9.4f) se(%9.4f) stats(N r2_w)

* -----------------------------------------------------------------------
* 6.3 财政缺口率 → M_amount(金额占比) → ln(发明专利) [核心控制]
* -----------------------------------------------------------------------
di _n "====== 6.3 fiscal_gap → M_amount → ln_inv (核心控制) ======"

* Step 1: X→M
xtreg M_amount fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store med3_s1
local a = _b[fiscal_gap_l1]
local se_a = _se[fiscal_gap_l1]
local p_xm = 2*ttail(e(df_r), abs(`a'/`se_a'))

* Step 2: X+M→Y
xtreg ln_inv fiscal_gap_l1 M_amount `controls_core' i.year, fe vce(cluster city_id)
estimates store med3_s2
local c_prime = _b[fiscal_gap_l1]
local b = _b[M_amount]
local se_b = _se[M_amount]
local p_my = 2*ttail(e(df_r), abs(`b'/`se_b'))

local ab = `a' * `b'
local se_sobel = sqrt(`a'^2 * `se_b'^2 + `b'^2 * `se_a'^2)
local z_sobel = `ab' / `se_sobel'
local p_sobel = 2*(1 - normal(abs(`z_sobel')))

di _n ">>> 中介效应汇总 (fiscal_gap → M_amount → ln_inv, 核心控制):"
di "路径 a (X→M) = " %9.4f `a' "  p = " %6.4f `p_xm'
di "路径 b (M→Y|X) = " %9.4f `b' "  p = " %6.4f `p_my'
di "间接效应 a*b = " %9.6f `ab'
di "Sobel Z = " %9.4f `z_sobel' "  p = " %6.4f `p_sobel'

* -----------------------------------------------------------------------
* 6.4 ln(债务率) → M_deal → ln(发明专利) [核心控制]
* -----------------------------------------------------------------------
di _n "====== 6.4 ln_debt → M_deal → ln_inv (核心控制) ======"

* Step 0: 总效应
xtreg ln_inv ln_debt_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store med4_s0
local c_total = _b[ln_debt_l1]
local p_total = 2*ttail(e(df_r), abs(_b[ln_debt_l1]/_se[ln_debt_l1]))

* Step 1: X→M
xtreg M_deal ln_debt_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store med4_s1
local a = _b[ln_debt_l1]
local se_a = _se[ln_debt_l1]
local p_xm = 2*ttail(e(df_r), abs(`a'/`se_a'))

* Step 2: X+M→Y
xtreg ln_inv ln_debt_l1 M_deal `controls_core' i.year, fe vce(cluster city_id)
estimates store med4_s2
local c_prime = _b[ln_debt_l1]
local b = _b[M_deal]
local se_b = _se[M_deal]
local p_my = 2*ttail(e(df_r), abs(`b'/`se_b'))

local ab = `a' * `b'
local se_sobel = sqrt(`a'^2 * `se_b'^2 + `b'^2 * `se_a'^2)
local z_sobel = `ab' / `se_sobel'
local p_sobel = 2*(1 - normal(abs(`z_sobel')))

di _n ">>> 中介效应汇总 (ln_debt → M_deal → ln_inv, 核心控制):"
di "总效应 c = " %9.4f `c_total' "  p = " %6.4f `p_total'
di "路径 a (X→M) = " %9.4f `a' "  p = " %6.4f `p_xm'
di "路径 b (M→Y|X) = " %9.4f `b' "  p = " %6.4f `p_my'
di "间接效应 a*b = " %9.6f `ab'
di "Sobel Z = " %9.4f `z_sobel' "  p = " %6.4f `p_sobel'
if `c_total' != 0 {
    di "中介效应占比 = " %9.2f (`ab'/`c_total'*100) "%"
}

estimates table med4_s0 med4_s1 med4_s2, ///
    keep(ln_debt_l1 M_deal `controls_core') b(%9.4f) se(%9.4f) stats(N r2_w)

*===========================================================================
* 7. 稳健性检验
*===========================================================================
di _n "============================================================"
di "  7. 稳健性检验"
di "============================================================"

* 7a. 替换被解释变量
di _n "--- 7a. 替换被解释变量 ---"
xtreg ln_pat fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store rob_pat
xtreg inv_share fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store rob_share

* 人均专利
gen ln_pat_pc = ln(pat_per_cap) if pat_per_cap > 0
quietly sum ln_pat_pc, detail
replace ln_pat_pc = r(p1) if ln_pat_pc < r(p1) & ln_pat_pc < .
replace ln_pat_pc = r(p99) if ln_pat_pc > r(p99) & ln_pat_pc < .
xtreg ln_pat_pc fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store rob_pc

di _n ">>> 稳健性: 替换被解释变量"
estimates table rob_pat rob_share rob_pc, ///
    keep(fiscal_gap_l1 `controls_core') b(%9.4f) se(%9.4f) stats(N r2_w)

* 7b. 排除极端专利城市 (top 5%)
di _n "--- 7b. 排除极端专利城市 ---"
quietly sum inv_cnt, detail
local top5 = r(p95)
preserve
drop if inv_cnt > `top5'
xtreg ln_inv fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store rob_trim
di "排除top5%(>" `top5' ")后: N=" e(N)
di "fiscal_gap_l1: beta=" %9.4f _b[fiscal_gap_l1] " p=" %6.4f 2*ttail(e(df_r), abs(_b[fiscal_gap_l1]/_se[fiscal_gap_l1]))
restore

* 7c. 替换中介变量 (M_amount)
di _n "--- 7c. 替换中介变量 (金额占比) ---"
xtreg M_amount fiscal_gap_l1 `controls_core' i.year, fe vce(cluster city_id)
estimates store rob_m_s1
xtreg ln_inv fiscal_gap_l1 M_amount `controls_core' i.year, fe vce(cluster city_id)
estimates store rob_m_s2

estimates table rob_m_s1 rob_m_s2, ///
    keep(fiscal_gap_l1 M_amount `controls_core') b(%9.4f) se(%9.4f) stats(N r2_w)

*===========================================================================
* 8. 与 Python 版本结果对比输出
*===========================================================================
di _n "============================================================"
di "  8. 与 Python v2 / regression_v1 结果对比"
di "============================================================"

di _n "--- 基准回归核心结果 (核心控制, DV=ln_inv) ---"
estimates restore base_cc_fg_inv
di "Stata: fiscal_gap_l1 -> ln_inv  beta=" %9.4f _b[fiscal_gap_l1] ///
    "  se=" %9.4f _se[fiscal_gap_l1] ///
    "  N=" e(N) "  R2w=" %9.4f e(r2_w)
di "Python v2:                      beta=1.0780  se=0.4842  N=2575  R2w=-0.0395"
di "Python v1:                      beta=1.0435  se=0.4821  N=2575  R2w=-0.0410"

estimates restore base_cc_debt_inv
di _n "Stata: ln_debt_l1 -> ln_inv  beta=" %9.4f _b[ln_debt_l1] ///
    "  se=" %9.4f _se[ln_debt_l1] ///
    "  N=" e(N) "  R2w=" %9.4f e(r2_w)
di "Python v2:                     beta=-0.0238  se=0.0723  N=1465  R2w=-0.0042"

di _n "--- 中介效应核心结果 (fiscal_gap → M_deal → ln_inv, 核心控制) ---"
estimates restore med2_s1
local a = _b[fiscal_gap_l1]
local se_a = _se[fiscal_gap_l1]
estimates restore med2_s2
local b = _b[M_deal]
local se_b = _se[M_deal]
local ab = `a' * `b'
local se_sob = sqrt(`a'^2 * `se_b'^2 + `b'^2 * `se_a'^2)
local z_sob = `ab' / `se_sob'
local p_sob = 2*(1 - normal(abs(`z_sob')))

di "Stata:    a=" %9.4f `a' "  b=" %9.4f `b' "  a*b=" %9.6f `ab' ///
    "  Sobel Z=" %9.4f `z_sob' "  p=" %6.4f `p_sob'
di "Python v2: a=0.0554  b=0.0238  a*b=0.001318  Sobel Z=0.0342  p=0.9727"
di "Python v1: a=2.0822  b=-0.0522  a*b=-0.108696  Sobel Z=-0.8859  p=0.3756"

di _n "============================================================"
di "  全部回归完成  $S_DATE $S_TIME"
di "============================================================"

log close main

*===========================================================================
* 9. 导出估计结果到文件 (如有 esttab)
*===========================================================================
cap which esttab
if _rc == 0 {
    * 基准回归表
    esttab base_nc_fg_inv base_cc_fg_inv base_fc_fg_inv ///
           base_nc_debt_inv base_cc_debt_inv base_fc_debt_inv ///
        using "`outdir'/stata_baseline_table.csv", replace ///
        keep(fiscal_gap_l1 ln_debt_l1 gdp_pc_ln ind2_share tech_exp fdi_ratio fin_depth) ///
        b(%9.4f) se(%9.4f) star(* 0.1 ** 0.05 *** 0.01) ///
        scalars(N r2_w) ///
        mtitle("(1)无ctrl" "(2)核心ctrl" "(3)完整ctrl" "(4)无ctrl" "(5)核心ctrl" "(6)完整ctrl") ///
        title("基准回归: DV=ln(发明专利)")

    * 中介效应表 (主模型)
    esttab med2_s0 med2_s1 med2_s2 ///
        using "`outdir'/stata_mediation_table.csv", replace ///
        keep(fiscal_gap_l1 M_deal gdp_pc_ln ind2_share tech_exp) ///
        b(%9.4f) se(%9.4f) star(* 0.1 ** 0.05 *** 0.01) ///
        scalars(N r2_w) ///
        mtitle("X→Y" "X→M" "X+M→Y") ///
        title("中介效应: fiscal_gap → M_deal → ln_inv (核心控制)")
}
else {
    di "esttab 未安装, 跳过CSV导出"
}

di "所有输出保存到: `outdir'/"
