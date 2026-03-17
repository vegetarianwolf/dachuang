* ============================================================================
* mechanism_h2_h5.do — H2/H5 机制检验: 两步法 + 交互项法
* ============================================================================

clear all
set more off

use "C:/Users/21288/Desktop/DACHUANG/dachuang/regression_v3/panel_v3.dta", clear

encode city, gen(city_fe)

* --- Generate interaction terms ---
gen FG_x_early = fiscal_gap_L1 * early_deal_ratio_L1
gen DR_x_early = ln_debt_ratio_L1 * early_deal_ratio_L1
gen FG_x_amt = fiscal_gap_L1 * ln_invest_amt_L1
gen DR_x_amt = ln_debt_ratio_L1 * ln_invest_amt_L1

label var FG_x_early "财政缺口×早期占比"
label var DR_x_early "债务率×早期占比"
label var FG_x_amt "财政缺口×投资额"
label var DR_x_amt "债务率×投资额"

* ============================================================================
* H2: 两步法第一步 X → early_deal_ratio_L1
* ============================================================================
eststo h2a: reghdfe early_deal_ratio_L1 fiscal_gap_L1 ln_pgdp sec_ratio sci_ratio, ///
    absorb(city_fe year) vce(cluster city_fe)

eststo h2b: reghdfe early_deal_ratio_L1 ln_debt_ratio_L1 ln_pgdp sec_ratio sci_ratio, ///
    absorb(city_fe year) vce(cluster city_fe)

* H2: 交互项法 X × M → Y
eststo h2c: reghdfe ln_invg fiscal_gap_L1 early_deal_ratio_L1 FG_x_early ///
    ln_pgdp sec_ratio sci_ratio, absorb(city_fe year) vce(cluster city_fe)

eststo h2d: reghdfe ln_invg ln_debt_ratio_L1 early_deal_ratio_L1 DR_x_early ///
    ln_pgdp sec_ratio sci_ratio, absorb(city_fe year) vce(cluster city_fe)

* --- Export H2 table ---
esttab h2a h2b h2c h2d using ///
    "C:/Users/21288/Desktop/DACHUANG/dachuang/regression_v3/mechanism_h2.csv", ///
    replace star(* 0.1 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_within, labels("N" "R2 (within)") fmt(0 3)) ///
    title("Table 3: Mechanism — Risk Preference Distortion (H2)") ///
    mtitles("Two-step:FG" "Two-step:DR" "Interact:FG" "Interact:DR") ///
    note("Two-step: X→M. Interaction: X×M→Y. City & year FE, clustered SE.")

eststo clear

* ============================================================================
* H5: 两步法第一步 X → ln_invest_amt_L1
* ============================================================================
eststo h5a: reghdfe ln_invest_amt_L1 fiscal_gap_L1 ln_pgdp sec_ratio sci_ratio, ///
    absorb(city_fe year) vce(cluster city_fe)

eststo h5b: reghdfe ln_invest_amt_L1 ln_debt_ratio_L1 ln_pgdp sec_ratio sci_ratio, ///
    absorb(city_fe year) vce(cluster city_fe)

* H5: 交互项法 X × M → Y
eststo h5c: reghdfe ln_invg fiscal_gap_L1 ln_invest_amt_L1 FG_x_amt ///
    ln_pgdp sec_ratio sci_ratio, absorb(city_fe year) vce(cluster city_fe)

eststo h5d: reghdfe ln_invg ln_debt_ratio_L1 ln_invest_amt_L1 DR_x_amt ///
    ln_pgdp sec_ratio sci_ratio, absorb(city_fe year) vce(cluster city_fe)

* --- Export H5 table ---
esttab h5a h5b h5c h5d using ///
    "C:/Users/21288/Desktop/DACHUANG/dachuang/regression_v3/mechanism_h5.csv", ///
    replace star(* 0.1 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_within, labels("N" "R2 (within)") fmt(0 3)) ///
    title("Table 4: Mechanism — Investment Scale Reduction (H5)") ///
    mtitles("Two-step:FG" "Two-step:DR" "Interact:FG" "Interact:DR") ///
    note("Two-step: X→M. Interaction: X×M→Y. City & year FE, clustered SE.")

eststo clear
