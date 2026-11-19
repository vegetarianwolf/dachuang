"""Independent reconstruction and NumPy CR1 verification of Choice round three.

Reads production inputs/outputs only; writes independent_validation.json.
No model search, source edits, or production-code imports are performed.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from validate_fiscal_trial_20261117 import t_critical, t_pvalue

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "实证结果/fiscal_fund_choice_round3_20261119"
PANEL = ROOT / "面板数据/firm_choice_fiscal_round3_20261119.csv"
PREP = ROOT / "实证结果/choice_download_20261117/prepare"
EXPLICIT = {"种子轮", "天使轮", "Pre-A轮", "A轮", "A+轮", "B轮", "B+轮", "Pre-B轮", "C轮", "C+轮", "D轮", "E轮", "F轮"}
CHECKS = []


def check(name, value, **detail):
    CHECKS.append(dict(check=name, passed=bool(value), **detail))


def close(a, b, atol=1e-10, rtol=1e-10):
    return np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(s):
    return "".join(unicodedata.normalize("NFKC", s).split())


def estimate(s, outcome, extras):
    terms = ["_cons", "p", "l_gdp", "l_secondary"]
    vectors = [np.ones(len(s))] + [s[k].to_numpy(float) for k in terms[1:]]
    for year in sorted(s.year.unique())[1:]:
        terms.append(f"{year}.year")
        vectors.append(s.year.eq(year).to_numpy(float))
    for k in extras:
        terms.append(k)
        vectors.append(s[k].to_numpy(float))
    x = np.column_stack(vectors)
    y = s[outcome].to_numpy(float)
    inverse = np.linalg.pinv(x, rcond=1e-12)
    b = inverse @ y
    residual = y - x @ b
    rank = int(np.linalg.matrix_rank(x))
    cities = s.source_id.unique()
    g, n = len(cities), len(s)
    correction = g / (g - 1) * (n - 1) / (n - rank)
    contributions = np.column_stack([inverse[:, s.source_id.eq(city)] @ residual[s.source_id.eq(city)] for city in cities])
    cov = contributions @ contributions.T * correction
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    crit = t_critical(g - 1)
    pv = np.array([t_pvalue(v / e, g - 1) for v, e in zip(b, se)])
    r2 = 1 - residual @ residual / ((y - y.mean()) @ (y - y.mean()))
    return dict(terms=terms, b=b, se=se, p=pv, lo=b-crit*se, hi=b+crit*se, cov=cov,
                n=n, g=g, rank=rank, correction=correction, r2=r2, x=x, residual=residual, yhat=x@b)


def compare_result(label, fit, row, target):
    j = fit["terms"].index(target)
    check(label + "_n_clusters", int(row["n"]) == fit["n"] and int(row["clusters"]) == fit["g"])
    check(label + "_coefficient", close(fit["b"][j], row["b"], 1e-7, 1e-7))
    check(label + "_cluster_se", close(fit["se"][j], row["se"], 2e-7, 1e-7))
    check(label + "_pvalue", close(fit["p"][j], row["p_value"], 2e-7, 1e-7))
    check(label + "_confidence_interval", close([fit["lo"][j], fit["hi"][j]], [row["ci_lo"], row["ci_hi"]], 8e-7, 1e-7))
    return dict(model=label, n=fit["n"], clusters=fit["g"], rank=fit["rank"], cr1_correction=float(fit["correction"]),
                target=target, b=float(fit["b"][j]), se=float(fit["se"][j]), p_value=float(fit["p"][j]),
                ci_lo=float(fit["lo"][j]), ci_hi=float(fit["hi"][j]),
                coefficient_error=float(abs(fit["b"][j]-row["b"])), se_error=float(abs(fit["se"][j]-row["se"])))


def stata_percentile(values, probability):
    x = np.sort(np.asarray(values, float))
    h = len(x) * probability
    if h.is_integer():
        return float((x[int(h)-1] + x[int(h)]) / 2)
    return float(x[int(np.ceil(h))-1])


def main():
    audit = json.loads((OUT / "data_audit.json").read_text())
    inputs = {k: sha(ROOT/k) for k in audit["input_sha256"]}
    for k, v in inputs.items():
        check("input_hash_" + k, audit["input_sha256"][k] == v)
    check("panel_hash", sha(PANEL) == audit["panel_sha256"])
    panel = pd.read_csv(PANEL).sort_values("obs_id").reset_index(drop=True)
    check("unique_cohort_identifiers", panel.obs_id.is_unique and panel.unit_id.is_unique and panel.unit_name.map(norm).is_unique)
    original = pd.read_csv(ROOT / "面板数据/firm_changes_round2_20261117.csv")
    eligible = original.year.between(2016, 2022) & original.n_initial_source_cities.eq(1) & original.earlier_other_fund_observed.eq(0) & np.isfinite(original[["p", "l_gdp", "l_secondary"]]).all(axis=1)
    source = original.loc[eligible].sort_values("obs_id").reset_index(drop=True)
    check("cohort_rules_reconstructed", panel.obs_id.tolist() == source.obs_id.tolist())
    for field in ["unit_id", "unit_name", "source_id", "source_city", "year"]:
        check("original_identity_" + field, panel[field].equals(source[field]))
    for field in ["p", "l_gdp", "l_secondary", "pre1", "change1"]:
        check("original_value_" + field, close(panel[field], source[field]))
    old_m1 = pd.read_csv(ROOT / "实证结果/fiscal_fund_design_round2_20261117/samples/M1.csv")
    check("fixed_M1_membership", set(panel.loc[panel.patent_m1.eq(1), "obs_id"]) == set(old_m1.obs_id) and panel.patent_m1.eq(source.use_M1).all())

    micro = pd.read_csv(ROOT / "面板数据/micro_fiscal_round2_20261117.csv")
    municipal = micro[micro.scope.eq("municipal")].copy()
    check("micro_calendar_years", municipal.year.eq(municipal.first_year+municipal.relative_year).all())
    for field, relative in [("pre1", -1), ("post1", 1)]:
        m = municipal[municipal.relative_year.eq(relative)].set_index("firm_id")
        expected = np.log1p(m.apply_invention.reindex(panel.unit_id).to_numpy())
        if field == "pre1":
            check("calendar_pre1", close(panel.pre1, expected))
            pre = expected
        else:
            check("calendar_change1", close(panel.change1, expected-pre))
    macro = pd.read_csv(ROOT / "面板数据/fiscal_macro_trial_20261117.csv")
    lag = panel.assign(lag_year=panel.year-1).merge(macro, left_on=["source_city", "lag_year"], right_on=["city", "year"], how="left", suffixes=("", "_macro"), validate="many_to_one")
    for field, original_field in [("p", "fiscal_gap"), ("l_gdp", "ln_gdp"), ("l_secondary", "secondary_share"), ("debt", "debt_ratio")]:
        check("exact_prior_calendar_fiscal_"+field, close(lag[field], lag[original_field]))
    panel["debt_gdp_ratio"] = lag.debt_gdp_ratio.to_numpy()

    names = set(panel.unit_name.map(norm))
    events = defaultdict(list)
    with gzip.open(PREP / "choice_events_normalized.csv.gz", "rt", encoding="utf-8-sig", newline="") as h:
        for e in csv.DictReader(h):
            name = norm(e["firm_legal_name"])
            if name in names:
                check("matched_choice_fullname", name == e["firm_name_normalized"])
                check("matched_choice_ownership_unknown", e["government_status"] == "unknown")
                events[name].append(dict(id=e["event_id"], date=e["event_date"], year=int(e["event_year"]), explicit=e["round_raw"] in EXPLICIT))
    rebuilt, notes = [], []
    for r in panel.itertuples():
        ev = sorted(events[norm(r.unit_name)], key=lambda e: (e["date"], e["id"]))
        first = min((e["year"] for e in ev), default=np.nan)
        d = dict(choice_match=int(bool(ev)), choice_first_year=first, choice_visible_by_entry=int(bool(ev) and first <= r.year))
        for suffix, selected in [("", ev), ("_noapr", [e for e in ev if not e["date"].startswith("2020-04-")])]:
            prior = [e["id"] for e in selected if e["explicit"] and e["year"] < r.year]
            pre2 = [e["id"] for e in selected if e["explicit"] and r.year-2 <= e["year"] <= r.year-1]
            post2 = [e["id"] for e in selected if e["explicit"] and r.year+1 <= e["year"] <= r.year+2]
            d.update({"entry_rows"+suffix: sum(e["year"] == r.year for e in selected),
                      "history"+suffix: int(bool(prior)) if selected else np.nan,
                      "pre2_round"+suffix: int(bool(pre2)) if selected else np.nan,
                      "follow2"+suffix: int(bool(post2)) if selected else np.nan})
            check("prior_source_ids"+suffix, json.loads(getattr(r, "prior_ids"+suffix)) == prior, obs_id=r.obs_id)
            check("follow_source_ids"+suffix, json.loads(getattr(r, "follow_ids"+suffix)) == post2, obs_id=r.obs_id)
        rebuilt.append(d)
    expected = pd.DataFrame(rebuilt)
    for column in expected:
        check("history_window_"+column, close(panel[column], expected[column]))
    check("all_two_year_windows_query_covered", (panel.year-2).ge(2012).all() and (panel.year+2).le(2024).all())
    check("unmatched_history_missing", panel.loc[panel.choice_match.eq(0), ["history", "pre2_round", "follow2"]].isna().all().all())

    flags = dict(patent_m1=panel.patent_m1.eq(1), patent_common=panel.patent_m1.eq(1)&panel.choice_match.eq(1),
                 patent_at_entry=panel.patent_m1.eq(1)&panel.choice_visible_by_entry.eq(1),
                 follow=panel.entry_rows.gt(0), follow_noapr=panel.entry_rows_noapr.gt(0),
                 follow_debt=panel.entry_rows.gt(0)&panel.debt.notna())
    derived_counts = dict(cohort_firms=len(panel), patent_m1_firms=int(flags["patent_m1"].sum()),
        patent_linked_firms=int(flags["patent_common"].sum()), patent_linked_by_entry_firms=int(flags["patent_at_entry"].sum()),
        patent_prior_explicit_firms=int(panel.loc[flags["patent_common"],"history"].sum()),
        follow_firms=int(flags["follow"].sum()), follow_source_cities=panel.loc[flags["follow"],"source_id"].nunique(),
        follow_observed_explicit_firms=int(panel.loc[flags["follow"],"follow2"].sum()),
        follow_prior_explicit_firms=int(panel.loc[flags["follow"],"pre2_round"].sum()),
        follow_no_april_firms=int(flags["follow_noapr"].sum()),
        follow_no_april_same_sample_full_outcome_ones=int(panel.loc[flags["follow_noapr"],"follow2"].sum()),
        follow_no_april_outcome_ones=int(panel.loc[flags["follow_noapr"],"follow2_noapr"].sum()),
        follow_debt_firms=int(flags["follow_debt"].sum()), follow_debt_outcome_ones=int(panel.loc[flags["follow_debt"],"follow2"].sum()))
    for name, value in derived_counts.items():
        check("audit_count_"+name,audit[name]==value)
    debt_mean = float(panel.loc[flags["follow_debt"], "debt"].mean())
    panel["debt_c"] = (panel.debt - debt_mean).where(flags["follow_debt"])
    panel["p_debt"] = panel.p * panel.debt_c
    specs = {
        "P0": ("change1", "patent_m1", [], "p"), "P1": ("change1", "patent_common", [], "p"),
        "P2": ("change1", "patent_common", ["history"], "p"), "P3": ("change1", "patent_common", ["pre1"], "p"),
        "P4": ("change1", "patent_common", ["pre1", "history"], "p"), "P5": ("change1", "patent_at_entry", [], "p"),
        "P6": ("change1", "patent_at_entry", ["history"], "p"), "Q0": ("follow2", "follow", [], "p"),
        "Q1": ("follow2", "follow", ["pre2_round"], "p"), "Q2a": ("follow2", "follow_noapr", ["pre2_round"], "p"),
        "Q2": ("follow2_noapr", "follow_noapr", ["pre2_round_noapr"], "p"),
        "Q3a": ("follow2", "follow_debt", ["pre2_round"], "p"),
        "Q3": ("follow2", "follow_debt", ["pre2_round", "debt_c", "p_debt"], "p_debt")}
    results = pd.read_csv(OUT / "model_results.csv").set_index("model")
    coefficients = pd.read_csv(OUT / "all_coefficients.csv")
    membership = pd.read_csv(OUT / "estimation_membership.csv").set_index("obs_id").reindex(panel.obs_id)
    check("all_13_models", set(results.index) == set(specs) and len(results) == len(specs))
    check("membership_all_cohort_ids", membership.index.tolist() == panel.obs_id.tolist() and membership.unit_id.tolist() == panel.unit_id.tolist())
    check("debt_centering", close(membership.debt_c, panel.debt_c) and close(membership.p_debt, panel.p_debt))
    regressions, all_errors, fits = [], [], {}
    for model, (y, flag, extras, target) in specs.items():
        s = panel.loc[flags[flag]].copy()
        check(model+"_membership", membership["used_"+model].to_numpy().tolist() == flags[flag].astype(int).tolist())
        check(model+"_no_implicit_listwise_loss", np.isfinite(s[[y,"p","l_gdp","l_secondary"]+extras]).all().all())
        fit = fits[model] = estimate(s, y, extras)
        check(model+"_estimability", fit["n"]>=40 and fit["g"]>=20 and fit["rank"]==len(fit["terms"]))
        regressions.append(compare_result(model, fit, results.loc[model], target))
        check(model+"_r2", close(fit["r2"], results.loc[model,"r2"], 1e-7, 1e-7))
        cc = coefficients[coefficients.model.eq(model)].set_index("term")
        expected_terms = set(fit["terms"]) | {f"{s.year.min()}b.year"}
        check(model+"_coefficient_terms", set(cc.index) == expected_terms)
        for j, term in enumerate(fit["terms"]):
            row = cc.loc[term]
            check(model+"_all_coefficients_"+term, close([fit["b"][j],fit["se"][j],fit["p"][j],fit["lo"][j],fit["hi"][j]], [row.b,row.se,row.p_value,row.ci_lo,row.ci_hi], 1e-6, 1e-7))
            all_errors.append(dict(model=model, term=term, b_error=float(abs(fit["b"][j]-row.b)), se_error=float(abs(fit["se"][j]-row.se))))
    for models in [("P1","P2","P3","P4"),("P5","P6"),("Q0","Q1"),("Q2a","Q2"),("Q3a","Q3")]:
        check("common_sample_"+"_".join(models), all(membership["used_"+models[0]].eq(membership["used_"+m]).all() for m in models[1:]))
    old_results = pd.read_csv(ROOT/"实证结果/fiscal_fund_design_round2_20261117/model_results.csv")
    old = old_results[old_results.model.eq("M1")].iloc[0]
    check("P0_reproduces_M1", close([results.loc["P0","b"],results.loc["P0","se"]], [old.b,old.se]))
    check("Stata_completion", "ROUND3_COMPLETED" in (ROOT/"运行日志与do代码/fiscal_fund_choice_round3_20261119.log").read_text())

    sensitivity = dict(q2_common_n=int(flags["follow_noapr"].sum()),
        q2_outcome_changes=int(panel.loc[flags["follow_noapr"],"follow2"].ne(panel.loc[flags["follow_noapr"],"follow2_noapr"]).sum()),
        q2_prior_control_changes=int(panel.loc[flags["follow_noapr"],"pre2_round"].ne(panel.loc[flags["follow_noapr"],"pre2_round_noapr"]).sum()),
        q2_removed_cohort_firms=panel.loc[flags["follow"] & ~flags["follow_noapr"],["unit_name","source_city","year"]].to_dict("records"),
        p5_removed_post_entry_only_names=panel.loc[flags["patent_common"] & ~flags["patent_at_entry"],["unit_name","year","choice_first_year"]].to_dict("records"))
    diagnostics = {}
    diag_path = OUT / "debt_diagnostics.csv"
    if diag_path.exists():
        common = flags["follow_debt"]
        cutoff = stata_percentile(panel.loc[common,"debt"], .95)
        panel["p_sq"], panel["debt_sq"] = panel.p**2, panel.debt_c**2
        gdp_common = common & panel.debt_gdp_ratio.notna()
        panel["gdp_debt_c"] = (panel.debt_gdp_ratio-panel.loc[gdp_common,"debt_gdp_ratio"].mean()).where(gdp_common)
        panel["p_gdp_debt"] = panel.p*panel.gdp_debt_c
        interaction = ["debt_c","p_debt"]
        diag_specs = {
            "Q3_replicated": ("follow2", common, interaction+["pre2_round"], "p_debt"),
            "below_debt_p95": ("follow2", common & panel.debt.le(cutoff), interaction+["pre2_round"], "p_debt"),
            "quadratic_main_terms": ("follow2", common, interaction+["pre2_round","p_sq","debt_sq"], "p_debt"),
            "debt_gdp_same_sample": ("follow2", gdp_common, interaction+["pre2_round"], "p_debt"),
            "debt_over_gdp": ("follow2", gdp_common, ["gdp_debt_c","p_gdp_debt","pre2_round"], "p_gdp_debt"),
            "pre_post_before": ("pre2_round", common, interaction, "p_debt"),
            "pre_post_after": ("follow2", common, interaction, "p_debt"),
            "april_common_full": ("follow2", common & flags["follow_noapr"], interaction+["pre2_round"], "p_debt"),
            "april_rows_excluded": ("follow2_noapr", common & flags["follow_noapr"], interaction+["pre2_round_noapr"], "p_debt")}
        dr = pd.read_csv(diag_path).set_index("model")
        check("nine_posthoc_diagnostics", set(dr.index)==set(diag_specs))
        diagnostics["models"] = [compare_result(model, estimate(panel.loc[flag],y,extras), dr.loc[model],target)
                                 for model,(y,flag,extras,target) in diag_specs.items()]
        diagnostics["debt_p95"] = cutoff
        q3 = fits["Q3"]
        q3s = panel.loc[common]
        j = q3["terms"].index("p_debt")
        z = np.delete(q3["x"],j,axis=1)
        residual_interaction = q3s.p_debt.to_numpy() - z @ (np.linalg.pinv(z) @ q3s.p_debt.to_numpy())
        shares = pd.Series(residual_interaction**2,index=q3s.index).groupby(q3s.source_id).sum()
        shares /= shares.sum()
        leave = pd.read_csv(OUT/"debt_leave_one_city.csv")
        check("all_source_cities_left_out", set(leave.source_id)==set(q3s.source_id.unique()) and len(leave)==q3s.source_id.nunique())
        leave_checks=[]
        for r in leave.to_dict("records"):
            s=q3s[q3s.source_id.ne(r["source_id"])]
            fit=estimate(s,"follow2",["debt_c","p_debt","pre2_round"])
            v=compare_result("leave_"+str(r["source_id"]),fit,r,"p_debt")
            check("partial_variation_"+str(r["source_id"]),close(shares.loc[r["source_id"]],r["partial_variation_share"],1e-7,1e-7))
            v.update(source_city=r["source_city"],partial_variation_share=float(shares.loc[r["source_id"]]))
            leave_checks.append(v)
        diagnostics["leave_one_city"] = leave_checks
        diagnostics["leave_one_city_summary"] = dict(models=len(leave_checks), b_min=min(x["b"] for x in leave_checks),b_max=max(x["b"] for x in leave_checks),
            p_min=min(x["p_value"] for x in leave_checks),p_max=max(x["p_value"] for x in leave_checks),
            top_city_variation_share=float(shares.max()),top5_variation_share=float(shares.nlargest(5).sum()))
        marginal=pd.read_csv(OUT/"debt_marginal_effects.csv")
        check("three_marginal_quantiles",set(marginal.percentile)=={"p25","p50","p75"})
        slopes=[]
        for r in marginal.itertuples():
            debt=stata_percentile(q3s.debt,int(r.percentile[1:])/100)
            w=np.zeros(len(q3["terms"]));w[q3["terms"].index("p")]=10;w[j]=10*(debt-debt_mean)
            b=float(w@q3["b"]);se=float(np.sqrt(w@q3["cov"]@w));crit=t_critical(q3["g"]-1)
            check("marginal_"+r.percentile,close([debt,b,se,b-crit*se,b+crit*se],[r.debt,r.b_pp,r.se_pp,r.ci_lo_pp,r.ci_hi_pp],1e-6,1e-7))
            slopes.append(dict(percentile=r.percentile,debt=debt,b_pp=b,se_pp=se,ci_lo_pp=b-crit*se,ci_hi_pp=b+crit*se))
        diagnostics["marginal_effects"] = slopes
        diagnostics["marginal_units"] = "Percentage-point change in source-observed follow-on probability for a 10-percentage-point fiscal-gap increase; 0.1 coefficient units times 100."
        diagnostics["Q3_LPM_predictions_outside_0_1"] = int(((q3["yhat"]<0)|(q3["yhat"]>1)).sum())
        check("diagnostics_completion","DEBT_DIAGNOSTICS_COMPLETED" in (ROOT/"运行日志与do代码/fiscal_choice_debt_diagnostics_20261119.log").read_text())

    for path, before in inputs.items():
        check("source_unchanged_"+path,sha(ROOT/path)==before)
    artifact_paths=[PANEL,OUT/"model_results.csv",OUT/"all_coefficients.csv",OUT/"estimation_membership.csv",OUT/"data_audit.json",
                    ROOT/"scripts/build_choice_fiscal_round3_20261119.py",ROOT/"运行日志与do代码/fiscal_fund_choice_round3_20261119.do"]
    artifact_paths += [p for p in [diag_path,OUT/"debt_leave_one_city.csv",OUT/"debt_marginal_effects.csv"] if p.exists()]
    result=dict(passed=all(c["passed"] for c in CHECKS),checks=CHECKS,failed_checks=[c for c in CHECKS if not c["passed"]],
        method="Independent cohort/calendar-window reconstruction from original round-two and finalized Choice inputs; NumPy OLS with explicit year dummies, source-city CR1 G/(G-1)*(N-1)/(N-rank), t(G-1) inference.",
        original_inputs_sha256=inputs,artifacts_sha256={str(p.relative_to(ROOT)):sha(p) for p in artifact_paths},
        validation_script_sha256=sha(Path(__file__)),cohort_rows=len(panel),debt_common_center=debt_mean,
        independently_recomputed_counts=derived_counts,
        regression_checks=regressions,max_all_coefficient_error=max(x["b_error"] for x in all_errors),
        max_all_se_error=max(x["se_error"] for x in all_errors),april_and_observability_sensitivity=sensitivity,
        posthoc_debt_diagnostics=diagnostics,
        interpretation="Outcomes and history are source-observed events; no observed follow-on is not proof of no financing. Fiscal location remains fund-registration proxy. Earlier general financing does not identify government/private ownership. Post-hoc debt checks are separately labeled.")
    (OUT/"independent_validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["passed","failed_checks","cohort_rows","max_all_coefficient_error","max_all_se_error"]},ensure_ascii=False,indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
