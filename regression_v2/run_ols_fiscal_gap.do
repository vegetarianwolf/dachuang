clear all
set more off

cd "c:/Users/21288/Desktop/DACHUANG/dachuang"

* 1) Load prepared minimal panel
import delimited using "regression_v2/ols_fiscal_gap_panel.csv", varnames(1) encoding(utf8) clear

destring year ln_invg fiscal_gap_l1 ln_gdppc second_share sci_share, replace force
keep if !missing(year, ln_invg, fiscal_gap_l1)

encode city, gen(city_id)

* 2) Main OLS (pooled OLS with year FE + city-clustered SE)
reg ln_invg fiscal_gap_l1 ln_gdppc second_share sci_share i.year, vce(cluster city_id)

* Save coefficient summary for fiscal_gap_l1
capture postutil clear
tempname pf
postfile `pf' str30 model double b se t p N using "regression_v2/ols_main_coef.dta", replace
post `pf' ("OLS_core_yearFE") (_b[fiscal_gap_l1]) (_se[fiscal_gap_l1]) (_b[fiscal_gap_l1]/_se[fiscal_gap_l1]) (2*ttail(e(df_r), abs(_b[fiscal_gap_l1]/_se[fiscal_gap_l1]))) (e(N))
postclose `pf'

* 3) Graph A: raw scatter + linear fit (main x-y relationship)
twoway ///
    (scatter ln_invg fiscal_gap_l1, mcolor(gs12) msize(vtiny)) ///
    (lfit ln_invg fiscal_gap_l1, lcolor(navy) lwidth(medthick)), ///
    title("OLS: Fiscal Gap vs ln(Invention Grants)") ///
    xtitle("fiscal_gap_l1") ytitle("ln_invg") legend(order(2 "Linear fit") pos(6) ring(0))

graph export "regression_v2/ols_fiscal_gap_scatter_fit.png", replace width(2200)

* 4) Graph B: binned relationship (robust, no add-on packages)
preserve
keep if e(sample)
xtile gap_bin = fiscal_gap_l1, nq(20)
collapse (mean) ln_invg fiscal_gap_l1, by(gap_bin)
twoway ///
    (scatter ln_invg fiscal_gap_l1, mcolor(navy) msize(small)) ///
    (line ln_invg fiscal_gap_l1, sort lcolor(maroon) lwidth(medthick)), ///
    title("Binned Fiscal Gap vs ln(Invention Grants)") ///
    xtitle("fiscal_gap_l1 (bin means)") ytitle("ln_invg (bin means)") legend(off)
graph export "regression_v2/ols_fiscal_gap_binned.png", replace width(2200)
restore

* 5) Export a lightweight coefficient CSV
preserve
use "regression_v2/ols_main_coef.dta", clear
export delimited using "regression_v2/ols_main_coef.csv", replace
restore

display "Done. Outputs in regression_v2/:"
display " - ols_main_coef.dta"
display " - ols_main_coef.csv"
display " - ols_fiscal_gap_scatter_fit.png"
display " - ols_fiscal_gap_binned.png"
