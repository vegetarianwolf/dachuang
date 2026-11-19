version 18
clear all
set more off
set type double
capture log close
args root
if `"`root'"' == "" local root `"`c(pwd)'"'
local basename "fiscal_fund_choice_round3_20261119"
local data "`root'/面板数据/firm_choice_fiscal_round3_20261119.csv"
capture confirm file "`data'"
if _rc {
    local root "`c(pwd)'/.."
    local data "`root'/面板数据/firm_choice_fiscal_round3_20261119.csv"
}
local outdir "`root'/实证结果/`basename'"
log using "`root'/运行日志与do代码/`basename'.log", replace text

tempname results coefficients
tempfile resultfile coefficientfile
postfile `results' str3 model str16 outcome str16 target double b se p_value ci_lo ci_hi n clusters r2 using `resultfile', replace
postfile `coefficients' str3 model str32 term double b se p_value ci_lo ci_hi using `coefficientfile', replace

program define fit
    syntax, MODEL(name) Y(name) RHS(string) TARGET(name) FLAG(name) RESULTS(name) COEFFICIENTS(name)
    quietly count if `flag'
    local expected = r(N)
    display "ROUND3 `model' `y' `rhs'"
    regress `y' `rhs' if `flag', vce(cluster source_id)
    assert e(N) == `expected'
    assert e(N) >= 40 & e(N_clust) >= 20
    assert _se[`target'] > 0 & _se[`target'] < .
    generate byte used_`model' = e(sample)
    local critical = invttail(e(df_r), .025)
    local b = _b[`target']
    local se = _se[`target']
    local pv = 2*ttail(e(df_r),abs(`b'/`se'))
    post `results' ("`model'") ("`y'") ("`target'") (`b') (`se') (`pv') (`b'-`critical'*`se') (`b'+`critical'*`se') (e(N)) (e(N_clust)) (e(r2))
    local terms : colnames e(b)
    foreach term of local terms {
        local b = _b[`term']
        local se = _se[`term']
        local pv = cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        post `coefficients' ("`model'") ("`term'") (`b') (`se') (`pv') (`b'-`critical'*`se') (`b'+`critical'*`se')
    }
end

import delimited using "`data'", clear varnames(1) encoding(UTF-8) asdouble
isid obs_id
isid unit_id
generate byte patent_common = patent_m1 & choice_match
generate byte patent_at_entry = patent_m1 & choice_visible_by_entry
generate byte follow = entry_rows > 0
generate byte follow_noapr = entry_rows_noapr > 0
generate byte follow_debt = follow & !missing(debt)
quietly summarize debt if follow_debt, meanonly
local debt_mean = r(mean)
display "Debt mean in Q3 common sample = " %15.9f `debt_mean'
generate double debt_c = debt - `debt_mean' if follow_debt
generate double p_debt = p*debt_c if follow_debt

local base "p l_gdp l_secondary i.year"
local handles "results(`results') coefficients(`coefficients')"
fit, model(P0) y(change1) rhs("`base'") target(p) flag(patent_m1) `handles'
fit, model(P1) y(change1) rhs("`base'") target(p) flag(patent_common) `handles'
fit, model(P2) y(change1) rhs("`base' history") target(p) flag(patent_common) `handles'
fit, model(P3) y(change1) rhs("`base' pre1") target(p) flag(patent_common) `handles'
fit, model(P4) y(change1) rhs("`base' pre1 history") target(p) flag(patent_common) `handles'
fit, model(P5) y(change1) rhs("`base'") target(p) flag(patent_at_entry) `handles'
fit, model(P6) y(change1) rhs("`base' history") target(p) flag(patent_at_entry) `handles'
fit, model(Q0) y(follow2) rhs("`base'") target(p) flag(follow) `handles'
fit, model(Q1) y(follow2) rhs("`base' pre2_round") target(p) flag(follow) `handles'
fit, model(Q2a) y(follow2) rhs("`base' pre2_round") target(p) flag(follow_noapr) `handles'
fit, model(Q2) y(follow2_noapr) rhs("`base' pre2_round_noapr") target(p) flag(follow_noapr) `handles'
fit, model(Q3a) y(follow2) rhs("`base' pre2_round") target(p) flag(follow_debt) `handles'
fit, model(Q3) y(follow2) rhs("`base' pre2_round debt_c p_debt") target(p_debt) flag(follow_debt) `handles'

assert used_P1 == used_P2 & used_P2 == used_P3 & used_P3 == used_P4
assert used_P5 == used_P6
assert used_Q0 == used_Q1 & used_Q2a == used_Q2 & used_Q3a == used_Q3
keep obs_id unit_id debt_c p_debt used_*
export delimited using "`outdir'/estimation_membership.csv", replace

postclose `results'
postclose `coefficients'
use `resultfile', clear
export delimited using "`outdir'/model_results.csv", replace
list model b se p_value ci_lo ci_hi n clusters, noobs
use `coefficientfile', clear
export delimited using "`outdir'/all_coefficients.csv", replace
display "ROUND3_COMPLETED"
log close
