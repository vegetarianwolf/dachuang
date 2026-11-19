version 18
clear all
set more off
set type double
capture log close
args root
if `"`root'"' == "" local root `"`c(pwd)'"'
capture confirm file "`root'/面板数据/firm_choice_fiscal_round3_20261119.csv"
if _rc local root "`c(pwd)'/.."
local outdir "`root'/实证结果/fiscal_fund_choice_round3_20261119"
local basename "fiscal_choice_debt_diagnostics_20261119"
log using "`root'/运行日志与do代码/`basename'.log", replace text

tempfile macro estimates influence slopes
tempname results leaveout marginal cutoff
import delimited using "`root'/面板数据/fiscal_macro_trial_20261117.csv", clear encoding(UTF-8) asdouble
keep city year debt_ratio debt_gdp_ratio
rename (city year debt_ratio) (source_city lag_year macro_debt)
isid source_city lag_year
save `macro'
import delimited using "`root'/面板数据/firm_choice_fiscal_round3_20261119.csv", clear encoding(UTF-8) asdouble
generate int lag_year = year - 1
merge m:1 source_city lag_year using `macro', keep(master match) nogen
assert missing(debt) == missing(macro_debt)
assert abs(debt - macro_debt) < 1e-10 if !missing(debt)
generate byte common = entry_rows > 0 & !missing(debt)
quietly summarize debt if common, detail
local center = r(mean)
scalar `cutoff' = r(p95)
local q25 = r(p25)
local q50 = r(p50)
local q75 = r(p75)
display "Debt ratio: mean " `center' ", p95 " `cutoff'
generate double debt_c = debt - `center' if common
generate double p_debt = p*debt_c
generate double p_sq = p^2
generate double debt_sq = debt_c^2
generate byte below95 = common & debt <= scalar(`cutoff')
generate byte gdp_debt_common = common & !missing(debt_gdp_ratio)
quietly summarize debt_gdp_ratio if gdp_debt_common, meanonly
generate double gdp_debt_c = debt_gdp_ratio - r(mean) if gdp_debt_common
generate double p_gdp_debt = p*gdp_debt_c
generate byte common_noapr = common & entry_rows_noapr > 0

program define diagnostic
    syntax, MODEL(name) Y(name) RHS(string) TARGET(name) FLAG(name) RESULTS(name)
    display "DIAGNOSTIC `model'"
    regress `y' `rhs' if `flag', vce(cluster source_id)
    quietly lincom `target'
    post `results' ("`model'") ("`y'") ("`target'") (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub)) (e(N)) (e(N_clust))
end

postfile `results' str24 model str20 outcome str16 target double b se p_value ci_lo ci_hi n clusters using `estimates', replace
local base "p l_gdp l_secondary i.year"
local interaction "`base' debt_c p_debt"
local handle "results(`results')"
diagnostic, model(Q3_replicated) y(follow2) rhs("`interaction' pre2_round") target(p_debt) flag(common) `handle'
diagnostic, model(below_debt_p95) y(follow2) rhs("`interaction' pre2_round") target(p_debt) flag(below95) `handle'
diagnostic, model(quadratic_main_terms) y(follow2) rhs("`interaction' pre2_round p_sq debt_sq") target(p_debt) flag(common) `handle'
diagnostic, model(debt_gdp_same_sample) y(follow2) rhs("`interaction' pre2_round") target(p_debt) flag(gdp_debt_common) `handle'
diagnostic, model(debt_over_gdp) y(follow2) rhs("`base' gdp_debt_c p_gdp_debt pre2_round") target(p_gdp_debt) flag(gdp_debt_common) `handle'
diagnostic, model(pre_post_before) y(pre2_round) rhs("`interaction'") target(p_debt) flag(common) `handle'
diagnostic, model(pre_post_after) y(follow2) rhs("`interaction'") target(p_debt) flag(common) `handle'
diagnostic, model(april_common_full) y(follow2) rhs("`interaction' pre2_round") target(p_debt) flag(common_noapr) `handle'
diagnostic, model(april_rows_excluded) y(follow2_noapr) rhs("`interaction' pre2_round_noapr") target(p_debt) flag(common_noapr) `handle'
postclose `results'

postfile `marginal' str3 percentile double debt b_pp se_pp ci_lo_pp ci_hi_pp using `slopes', replace
quietly regress follow2 `interaction' pre2_round if common, vce(cluster source_id)
foreach q in 25 50 75 {
    local offset = `q`q'' - `center'
    quietly lincom 10*(p + `offset'*p_debt)
    post `marginal' ("p`q'") (`q`q'') (r(estimate)) (r(se)) (r(lb)) (r(ub))
}
postclose `marginal'

quietly regress p_debt `base' debt_c pre2_round if common
predict double residual_interaction if e(sample), residuals
generate double residual_sq = residual_interaction^2
quietly summarize residual_sq if common, meanonly
local total = r(sum)
quietly levelsof source_id if common, local(cities)
postfile `leaveout' int source_id str50 source_city double partial_variation_share b se p_value ci_lo ci_hi n clusters using `influence', replace
foreach city of local cities {
    quietly levelsof source_city if source_id == `city', local(name) clean
    quietly summarize residual_sq if common & source_id == `city', meanonly
    local share = r(sum)/`total'
    quietly regress follow2 `interaction' pre2_round if common & source_id != `city', vce(cluster source_id)
    quietly lincom p_debt
    post `leaveout' (`city') ("`name'") (`share') (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub)) (e(N)) (e(N_clust))
}
postclose `leaveout'

use `estimates', clear
export delimited using "`outdir'/debt_diagnostics.csv", replace
list model n clusters b ci_lo ci_hi, noobs
use `slopes', clear
export delimited using "`outdir'/debt_marginal_effects.csv", replace
list, noobs
use `influence', clear
export delimited using "`outdir'/debt_leave_one_city.csv", replace
display "DEBT_DIAGNOSTICS_COMPLETED"
log close
