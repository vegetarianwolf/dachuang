version 18
clear all
set more off
set type double
capture log close
args root
if `"`root'"' == "" local root `"`c(pwd)'"'
local datafile "`root'/面板数据/fiscal_fund_trial_20261117.csv"
local outdir "`root'/实证结果/fiscal_fund_trial_20261117"
local basename "xtreg_fiscal_fund_trial_20261117"
local logfile "`root'/运行日志与do代码/`basename'.log"
log using "`logfile'", replace text
global trial_out "`outdir'"
import delimited using "`datafile'", clear varnames(1) encoding(UTF-8) case(preserve)
isid sample city year
xtset panel_id year
tempname results coefficients margins
tempfile results_file coefficients_file margins_file
postfile `results' str12 scope str6 model str24 outcome str60 target str30 status double b se p lo hi N clusters year_min year_max r2w using `results_file', replace
postfile `coefficients' str12 scope str6 model str80 term double b se p lo hi using `coefficients_file', replace
postfile `margins' str12 scope str6 model str20 kind double p_value d_value estimate se p lo hi using `margins_file', replace
global trial_results `results'
global trial_coefficients `coefficients'
global trial_margins `margins'

capture program drop trial
program define trial
    syntax, scope(string) model(string) outcome(name) rhs(string) target(string) flag(name) [weight(name) margin(integer 0)]
    tempvar eligible tag used
    gen byte `eligible' = sample == "`scope'" & `flag' == 1
    quietly count if `eligible'
    local n = r(N)
    quietly egen `tag' = tag(city_id) if `eligible'
    quietly count if `tag' == 1
    local clusters = r(N)
    if `n' < 40 | `clusters' < 20 {
        post $trial_results ("`scope'") ("`model'") ("`outcome'") ("`target'") ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (.) (.) (.)
        exit
    }
    local w ""
    if "`weight'" != "" local w "[aw=`weight']"
    noisily display "TRIAL `scope' `model': `outcome' `rhs'"
    if "`weight'" == "" {
        capture noisily xtreg `outcome' `rhs' i.year if `eligible', fe vce(cluster city_id)
    }
    else {
        capture noisily areg `outcome' `rhs' i.year if `eligible' `w', absorb(panel_id) vce(cluster city_id)
    }
    local rc = _rc
    if `rc' != 0 {
        post $trial_results ("`scope'") ("`model'") ("`outcome'") ("`target'") ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (.) (.) (.)
        exit
    }
    gen byte `used' = e(sample)
    quietly summarize year if `used', meanonly
    local ymin = r(min)
    local ymax = r(max)
    local critical = invttail(e(df_r), .025)
    local b = _b[`target']
    local se = _se[`target']
    local p = cond(`se' > 0, 2*ttail(e(df_r), abs(`b'/`se')), .)
    local status "ok"
    if `se' == 0 local status "target_omitted"
    local r2w = .
    if "`weight'" == "" local r2w = e(r2_w)
    post $trial_results ("`scope'") ("`model'") ("`outcome'") ("`target'") ("`status'") (`b') (`se') (`p') (`b'-`critical'*`se') (`b'+`critical'*`se') (e(N)) (`clusters') (`ymin') (`ymax') (`r2w')
    local terms : colnames e(b)
    foreach term of local terms {
        local b = _b[`term']
        local se = _se[`term']
        local p = cond(`se' > 0, 2*ttail(e(df_r), abs(`b'/`se')), .)
        post $trial_coefficients ("`scope'") ("`model'") ("`term'") (`b') (`se') (`p') (`b'-`critical'*`se') (`b'+`critical'*`se')
    }
    if `margin' == 1 {
        quietly summarize p if `used', detail
        local points "`r(p5)' `r(p25)' `r(p50)' `r(p75)' `r(p95)'"
        foreach point of local points {
            quietly lincom g + `point'*c.g#c.p
            post $trial_margins ("`scope'") ("`model'") ("fund_slope") (`point') (.) (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub))
        }
    }
    if `margin' == 2 {
        quietly summarize d if `used', detail
        local dpoints "`r(p25)' `r(p50)' `r(p75)'"
        foreach point of local dpoints {
            quietly lincom c.g#c.p + `point'*c.g#c.p#c.d
            post $trial_margins ("`scope'") ("`model'") ("fiscal_moderation") (.) (`point') (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub))
        }
    }
    preserve
    keep if `used'
    keep city city_id year sample inv_count known_count early_share p d g l_gdp l_secondary y1 y2 grant1
    export delimited using "$trial_out/samples/`scope'_`model'.csv", replace
    restore
end

* MODEL_CALLS

postclose `results'
postclose `coefficients'
postclose `margins'
use `results_file', clear
export delimited using "`outdir'/model_results.csv", replace
list scope model status b se p N clusters, noobs sepby(scope)
use `coefficients_file', clear
export delimited using "`outdir'/all_coefficients.csv", replace
use `margins_file', clear
export delimited using "`outdir'/marginal_effects.csv", replace
macro drop trial_out trial_results trial_coefficients trial_margins
display "TRIAL_COMPLETED"
log close
