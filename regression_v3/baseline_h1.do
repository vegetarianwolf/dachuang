* ============================================================================
* baseline_h1.do — H1 基准回归: 财政压力 -> 创新绩效
* 双向固定效应 + 城市聚类标准误
* ============================================================================

clear all
set more off

* --- Load panel ---
use "C:/Users/21288/Desktop/DACHUANG/dachuang/regression_v3/panel_v3.dta", clear

* --- Encode string variables for FE ---
encode city, gen(city_fe)
encode province, gen(prov_fe)

* --- Label variables ---
label var ln_invg "ln(1+发明授权)"
label var ln_umg "ln(1+实用新型授权)"
label var ln_inva "ln(1+发明申请)"
label var ln_total_grant "ln(1+总授权量)"
label var inv_share "发明占比"
label var fiscal_gap_L1 "财政缺口率(L1)"
label var ln_debt_ratio_L1 "ln(债务率)(L1)"
label var ln_invest_amt_L1 "ln(1+投资额)(L1)"
label var ln_invest_cnt_L1 "ln(1+投资笔数)(L1)"
label var early_deal_ratio_L1 "早期投资占比(L1)"
label var broad_early_ratio_L1 "广义早期占比(L1)"
label var ln_pgdp "ln(人均GDP)"
label var sec_ratio "第二产业占比"
label var sci_ratio "科技支出占比"
label var fdi_dep "外资依存度"
label var fin_depth "金融深度"
label var ln_pop "ln(常住人口)"
label var market_index "市场化指数"
label var fiscal_trans "财政透明度"

* --- Descriptive Statistics ---
summarize ln_invg ln_umg ln_inva ln_total_grant inv_share ///
    fiscal_gap_L1 ln_debt_ratio_L1 ///
    ln_invest_amt_L1 ln_invest_cnt_L1 early_deal_ratio_L1 broad_early_ratio_L1 ///
    ln_pgdp sec_ratio sci_ratio ln_pop ///
    market_index fiscal_trans

* ============================================================================
* H1 Baseline: fiscal_gap_L1 → ln_invg (columns 1-3)
* ============================================================================
* (1) No controls
eststo m1: reghdfe ln_invg fiscal_gap_L1, absorb(city_fe year) vce(cluster city_fe)

* (2) Core controls
eststo m2: reghdfe ln_invg fiscal_gap_L1 ln_pgdp sec_ratio sci_ratio, ///
    absorb(city_fe year) vce(cluster city_fe)

* (3) Core + extended (excluding fdi_dep/fin_depth due to missingness)
eststo m3: reghdfe ln_invg fiscal_gap_L1 ln_pgdp sec_ratio sci_ratio ln_pop, ///
    absorb(city_fe year) vce(cluster city_fe)

* ============================================================================
* H1 Baseline: ln_debt_ratio_L1 → ln_invg (columns 4-6)
* ============================================================================
* (4) No controls
eststo m4: reghdfe ln_invg ln_debt_ratio_L1, absorb(city_fe year) vce(cluster city_fe)

* (5) Core controls
eststo m5: reghdfe ln_invg ln_debt_ratio_L1 ln_pgdp sec_ratio sci_ratio, ///
    absorb(city_fe year) vce(cluster city_fe)

* (6) Core + extended
eststo m6: reghdfe ln_invg ln_debt_ratio_L1 ln_pgdp sec_ratio sci_ratio ln_pop, ///
    absorb(city_fe year) vce(cluster city_fe)

* --- Export baseline table ---
esttab m1 m2 m3 m4 m5 m6 using ///
    "C:/Users/21288/Desktop/DACHUANG/dachuang/regression_v3/baseline_h1.csv", ///
    replace star(* 0.1 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_within, labels("N" "R2 (within)") fmt(0 3)) ///
    title("Table 2: Baseline Regression — Fiscal Pressure and Innovation") ///
    mtitles("(1)" "(2)" "(3)" "(4)" "(5)" "(6)") ///
    note("All regressions include city and year FE. SE clustered at city level.")

* --- Also save coefficients for plotting ---
matrix coef_fg = J(3, 4, .)
forvalues i = 1/3 {
    estimates restore m`i'
    matrix coef_fg[`i', 1] = _b[fiscal_gap_L1]
    matrix coef_fg[`i', 2] = _se[fiscal_gap_L1]
    matrix coef_fg[`i', 3] = _b[fiscal_gap_L1] - 1.96*_se[fiscal_gap_L1]
    matrix coef_fg[`i', 4] = _b[fiscal_gap_L1] + 1.96*_se[fiscal_gap_L1]
}

matrix coef_dr = J(3, 4, .)
forvalues i = 4/6 {
    local j = `i' - 3
    estimates restore m`i'
    matrix coef_dr[`j', 1] = _b[ln_debt_ratio_L1]
    matrix coef_dr[`j', 2] = _se[ln_debt_ratio_L1]
    matrix coef_dr[`j', 3] = _b[ln_debt_ratio_L1] - 1.96*_se[ln_debt_ratio_L1]
    matrix coef_dr[`j', 4] = _b[ln_debt_ratio_L1] + 1.96*_se[ln_debt_ratio_L1]
}

eststo clear
