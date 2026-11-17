"""Independently validate round-two source matching, samples, and FE support."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "实证结果/fiscal_fund_design_round2_20261117"
RAW = ROOT / "原始数据打包_20260401"
EVENTS = RAW / "清科政府引导基金投资事件截止到2024年/2015-2024投资事件_附基金级别分类注册地区_扩展匹配.csv"
PATENTS = RAW / "CNRDS专利数据包/非上市公司专利申请与获得"
MACRO = ROOT / "面板数据/fiscal_macro_trial_20261117.csv"
MICRO = ROOT / "面板数据/micro_fiscal_round2_20261117.csv"
CHOICE = ROOT / "面板数据/fund_choice_round2_20261117.csv"


def norm(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_influence(result):
    """Check all 40 follow-up estimates using a separate FE/pruning implementation."""
    from validate_fiscal_trial_20261117 import t_pvalue, t_critical
    path = OUT / "f2_leave_one_city.csv"
    if not path.exists():
        return result
    checks = result["checks"]
    def check(name, condition, **details):
        checks.append(dict(check="F2_influence_" + name, passed=bool(condition), **details))
    results = pd.read_csv(path)
    panel_path = ROOT / "面板数据/f2_influence_round2_20261117.csv"
    panel = pd.read_csv(panel_path)
    data = pd.read_csv(CHOICE)
    data = data[data.use_F2.eq(1)].copy()
    audit_path = OUT / "f2_influence_audit.json"
    audit = json.loads(audit_path.read_text())
    check("40_cities_no_selection", len(results) == 40 and results.omitted_city.nunique() == 40 and set(results.omitted_city) == set(data.source_city))
    check("input_hash", audit["source_sha256"] == sha(CHOICE))
    check("panel_hash", audit["output_sha256"] == sha(panel_path))
    check("starting_sample", set(panel.event_id) == set(data.event_id))
    validation = []
    for r in results.itertuples():
        s = data[data.source_city.ne(r.omitted_city)].copy()
        prior_n = -1
        while prior_n != len(s):
            prior_n = len(s)
            for effect in ["fund_id", "destination_year", "sector_id"]:
                sizes = s[effect].value_counts()
                s = s[s[effect].isin(sizes.index[sizes.ge(2)])]
            fund_years = s.groupby("fund_id").year.nunique()
            s = s[s.fund_id.isin(fund_years.index[fund_years.ge(2)])]
        n, clusters, funds = len(s), s.source_city.nunique(), s.fund_id.nunique()
        label = f"{r.variant:02d}_"
        flagged = panel[panel[f"use_drop_{r.variant:02d}"].eq(1)]
        check(label + "recursive_sample", set(s.event_id) == set(flagged.event_id))
        check(label + "sample_counts", n == r.N and clusters == r.clusters and funds == r.funds)
        if n < 40 or clusters < 20:
            check(label + "threshold_skip", r.status == "insufficient_sample")
            continue
        check(label + "estimable_status", r.status == "ok")
        x = np.column_stack([np.ones(n), s[["p", "l_gdp", "l_secondary"]].to_numpy()] + [pd.get_dummies(s[e], drop_first=True, dtype=float).to_numpy() for e in ["fund_id", "destination_year", "sector_id"]])
        inverse = np.linalg.pinv(x, rcond=1e-12)
        y = s.early.to_numpy()
        beta = inverse @ y
        residual = y - x @ beta
        rank = np.linalg.matrix_rank(x)
        correction = clusters / (clusters - 1) * (n - 1) / (n - rank)
        contributions = [inverse[1, s.source_city.eq(city)] @ residual[s.source_city.eq(city)] for city in s.source_city.unique()]
        b = float(beta[1])
        se = float(np.sqrt(np.square(contributions).sum() * correction))
        p = t_pvalue(b / se, clusters - 1)
        crit = t_critical(clusters - 1)
        check(label + "coefficient", np.isclose(b, r.b, atol=1e-7, rtol=1e-7))
        check(label + "cluster_se", np.isclose(se, r.se, atol=2e-7, rtol=1e-7))
        check(label + "pvalue", np.isclose(p, r.p, atol=2e-7, rtol=1e-7))
        check(label + "confidence_interval", np.allclose([b-crit*se, b+crit*se], [r.lo, r.hi], atol=8e-7, rtol=1e-7))
        validation.append(dict(omitted_city=r.omitted_city, N=n, clusters=clusters, funds=funds, full_design_rank=int(rank),
                               numpy_b=b, numpy_se=se, numpy_p=p, b_error=abs(b-r.b), se_error=abs(se-r.se)))
    log_path = ROOT / "运行日志与do代码/fiscal_round2_f2_influence_20261117.log"
    check("Stata_completion_marker", "F2_INFLUENCE_COMPLETED" in log_path.read_text())
    result["influence_checks"] = validation
    result["influence_summary"] = dict(variants=len(results), all_statuses_ok=bool(results.status.eq("ok").all()),
        all_coefficients_negative=bool(results.b.lt(0).all()), b_range=[float(results.b.min()), float(results.b.max())],
        p_range=[float(results.p.min()), float(results.p.max())], N_range=[int(results.N.min()), int(results.N.max())],
        clusters_range=[int(results.clusters.min()), int(results.clusters.max())],
        positive_upper_95ci=int(results.hi.gt(0).sum()), negative_upper_95ci=int(results.hi.lt(0).sum()))
    result["artifacts_sha256"].update({str(p.relative_to(ROOT)): sha(p) for p in [panel_path, path, audit_path, log_path]})
    return result


def validate_regressions(result):
    from validate_fiscal_trial_20261117 import t_pvalue, t_critical
    prior = result["checks"]
    start = next((i for i, c in enumerate(prior) if c["check"].startswith("unchanged_construction_input_")), len(prior))
    result["checks"] = prior[:start]
    checks = result["checks"]
    def check(name, condition, **details):
        checks.append(dict(check=name, passed=bool(condition), **details))
    for relative, expected in result["artifacts_sha256"].items():
        check("unchanged_construction_input_" + relative, sha(ROOT / relative) == expected)
    fund = pd.read_csv(CHOICE)
    changes_path = ROOT / "面板数据/firm_changes_round2_20261117.csv"
    changes = pd.read_csv(changes_path)
    micro = pd.read_csv(MICRO)
    micro = micro[micro.scope.eq("municipal")].set_index(["firm_id", "relative_year"])
    for relative in [-3, -2, -1, 1, 2, 3]:
        field = ("pre" if relative < 0 else "post") + str(abs(relative))
        expected = [np.log1p(micro.loc[(int(r.unit_id), relative), "apply_invention"]) if (int(r.unit_id), relative) in micro.index else np.nan for r in changes.itertuples()]
        check("firm_change_calendar_" + field, np.allclose(changes[field], expected, equal_nan=True))
    check("firm_change_one_year_formula", np.allclose(changes.change1, changes.post1 - changes.pre1, equal_nan=True))
    check("firm_pretrend_formula", np.allclose(changes.pretrend, changes.pre1 - changes.pre2, equal_nan=True))
    six = ["pre3", "pre2", "pre1", "post1", "post2", "post3"]
    expected = ((changes.post1 + changes.post2 + changes.post3) / 3 - (changes.pre1 + changes.pre2 + changes.pre3) / 3).where(changes[six].notna().all(axis=1))
    check("firm_three_year_formula", np.allclose(changes.change3, expected, equal_nan=True))
    common = changes.year.between(2016, 2022) & changes.n_initial_source_cities.eq(1) & changes.earlier_other_fund_observed.eq(0)
    for model, required in {"M1": ["change1"], "M2": ["change1", "pre1"], "M3": ["change1", "pretrend"], "M4": ["change1", "pretrend"], "M5": six, "M6": six}.items():
        expected = common & changes[["p", "l_gdp", "l_secondary"] + required].notna().all(axis=1)
        if model in ["M5", "M6"]:
            expected &= changes.year.le(2020)
        check(model + "_sample_rule", changes["use_" + model].eq(expected.astype(int)).all())
    check("M1_M2_common_sample", changes.use_M1.eq(changes.use_M2).all())
    check("M3_M4_common_sample", changes.use_M3.eq(changes.use_M4).all())
    check("M5_M6_common_sample", changes.use_M5.eq(changes.use_M6).all())
    results_path = OUT / "model_results.csv"
    coefs_path = OUT / "all_coefficients.csv"
    results = pd.read_csv(results_path)
    coefs = pd.read_csv(coefs_path)
    check("all_11_prespecified_models_present", set(results.model) == {"F1", "F2a", "F2", "F3a", "F3", "M1", "M2", "M3", "M4", "M5", "M6"})
    regression_checks = []
    for r in results.itertuples():
        data = fund if r.group == "fund" else changes
        s = data[data["use_" + r.model].eq(1)].copy()
        n, clusters = len(s), s.source_city.nunique()
        check(r.model + "_reported_sample_size", n == r.N and clusters == r.clusters)
        if r.status != "ok":
            check(r.model + "_skip_follows_threshold", r.status == "insufficient_sample" and (n < 40 or clusters < 20))
            continue
        exported = pd.read_csv(OUT / "samples" / (r.model + ".csv"))
        key = "event_id" if r.group == "fund" else "obs_id"
        check(r.model + "_stata_sample_ids", set(s[key]) == set(exported.obs_id))
        cc = coefs[coefs.model.eq(r.model)]
        active = cc[~cc.term.str.contains(r"\d+[bo]\.", regex=True) & cc.term.ne("_cons")].copy()
        vectors = {"_cons": np.ones(n)}
        for term in active.term:
            factor = re.fullmatch(r"(\d+)\.(\w+)", term)
            vectors[term] = s[factor[2]].eq(int(factor[1])).astype(float) if factor else s[term]
        design = pd.DataFrame(vectors, index=s.index)
        if r.group == "fund":
            design = pd.concat([design, pd.get_dummies(s.fund_id, prefix="fund", drop_first=True, dtype=float)], axis=1)
        x, y = design.to_numpy(dtype=float), s[r.outcome].to_numpy(dtype=float)
        inverse = np.linalg.pinv(x, rcond=1e-12)
        beta = inverse @ y
        residual = y - x @ beta
        rank = np.linalg.matrix_rank(x)
        # areg counts absorbed effects in its CR1 correction, unlike nested-FE xtreg.
        correction = clusters / (clusters - 1) * (n - 1) / (n - rank)
        contributions = np.column_stack([inverse[:, s.source_city.eq(city)] @ residual[s.source_city.eq(city)] for city in s.source_city.unique()])
        cov = (contributions @ contributions.T) * correction
        standard_errors = np.sqrt(np.maximum(np.diag(cov), 0))
        continuous = [term for term in active.term if "." not in term]
        compared = []
        for term in continuous:
            j = design.columns.get_loc(term)
            reference = cc[cc.term.eq(term)].iloc[0]
            estimate, se = float(beta[j]), float(standard_errors[j])
            p = t_pvalue(estimate / se, clusters - 1)
            critical = t_critical(clusters - 1)
            check(r.model + "_numpy_coefficient_" + term, np.isclose(estimate, reference.b, atol=1e-7, rtol=1e-7))
            check(r.model + "_numpy_cluster_se_" + term, np.isclose(se, reference.se, atol=2e-7, rtol=1e-7))
            check(r.model + "_numpy_pvalue_" + term, np.isclose(p, reference.p, atol=2e-7, rtol=1e-7))
            compared.append(dict(term=term, numpy_b=estimate, stata_b=float(reference.b), b_error=float(abs(estimate-reference.b)), numpy_se=se, stata_se=float(reference.se), se_error=float(abs(se-reference.se)), p=p))
            if term == r.target:
                check(r.model + "_numpy_confidence_interval", np.allclose([estimate - critical*se, estimate + critical*se], [r.lo, r.hi], atol=8e-7, rtol=1e-7))
        regression_checks.append(dict(model=r.model, N=n, clusters=clusters, full_design_rank=int(rank), cluster_correction=float(correction), coefficients=compared))
    check("Stata_completion_marker", "ROUND2_COMPLETED" in (ROOT / "运行日志与do代码/fiscal_fund_micro_round2_20261117.log").read_text())
    result["regressions_validated"] = True
    result["regression_checks"] = regression_checks
    result["regression_note"] = "Independent NumPy explicit-dummy OLS with source-city CR1 sandwich, full areg absorbed-effect degrees of freedom, and t inference. All continuous coefficients and standard errors checked for the nine estimable models."
    result["artifacts_sha256"].update({str(p.relative_to(ROOT)): sha(p) for p in [changes_path, results_path, coefs_path]})
    result = validate_influence(result)
    result["passed"] = all(c["passed"] for c in checks)
    return result


def main():
    if "--regressions-only" in sys.argv:
        result = json.loads((OUT / "validation.json").read_text())
        result = validate_regressions(result)
        (OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(dict(passed=result["passed"], checks=len(result["checks"]), failed=[c for c in result["checks"] if not c["passed"]]), ensure_ascii=False, indent=2))
        if not result["passed"]:
            raise SystemExit(1)
        return
    checks = []
    warnings = []

    def check(name, condition, **details):
        checks.append(dict(check=name, passed=bool(condition), **details))

    m = pd.read_csv(MICRO)
    f = pd.read_csv(CHOICE)
    macro = pd.read_csv(MACRO)
    check("micro_unique_scope_firm_year", not m.duplicated(["scope", "firm_id", "year"]).any(), rows=len(m))
    check("micro_outcome_year_through_2023", m.year.le(2023).all())
    check("micro_relative_year", m.relative_year.eq(m.year - m.first_year).all())
    check("micro_exact_initial_lag_year", m.initial_gap_year.eq(m.first_year - 1).all())
    check("micro_cohort_flags", m.main_cohort_2016_2022.eq(m.first_year.between(2016, 2022).astype(int)).all())
    check("micro_left_censor_flag", m.left_censored_2015.eq(m.first_year.eq(2015).astype(int)).all())
    check("micro_no_assignment_of_multiple_initial_cities", m.loc[m.n_initial_source_cities.gt(1), ["source_city", "p_initial"]].isna().all().all())
    check("micro_fiscal_initial_macro_match", True)
    x = m[["source_city", "first_year", "p_initial"]].drop_duplicates()
    x["macro_year"] = x.first_year - 1
    x = x.merge(macro[["city", "year", "fiscal_gap"]], left_on=["source_city", "macro_year"], right_on=["city", "year"], how="left", validate="many_to_one")
    checks[-1]["passed"] = bool(np.allclose(x.p_initial, x.fiscal_gap, equal_nan=True))
    for outcome in ["apply", "grant"]:
        check(outcome + "_missing_source_stays_missing", m.loc[m["has_" + outcome + "_row"].eq(0), [outcome + "_total", outcome + "_invention"]].isna().all().all())
        check(outcome + "_nonnegative_integer", ((m[outcome + "_invention"].dropna() >= 0) & (m[outcome + "_invention"].dropna() % 1 == 0)).all())

    associations = pd.read_csv(OUT / "micro_firm_source_associations.csv")
    group = associations.groupby(["scope", "firm_id"])
    first_expected = group.event_year.min().rename("first_expected")
    firm = m.sort_values("year").groupby(["scope", "firm_id"]).first().reset_index()
    j = firm.merge(first_expected, on=["scope", "firm_id"], validate="one_to_one")
    check("micro_first_is_earliest_observed_within_scope", j.first_year.eq(j.first_expected).all())
    initial = associations[associations.is_initial_year.eq(1)].groupby(["scope", "firm_id"]).source_city.agg(lambda s: sorted(set(s)))
    check("micro_initial_city_count", all(len(initial.loc[(r.scope, r.firm_id)]) == r.n_initial_source_cities for r in firm.itertuples()))

    raw = list(csv.DictReader(EVENTS.open(encoding="utf-8-sig", newline="")))
    metadata = {"投资事件来源", "基金级别", "基金分类", "注册地区_基金目录", "标注匹配方式", "标注来源表", "命中别名"}
    economic_fields = [c for c in raw[0] if c not in metadata]
    attribution = defaultdict(set)
    first_any = defaultdict(list)
    raw_names = set()
    for r in raw:
        attribution[tuple(r[c] for c in economic_fields)].add(tuple(r[c] for c in ["基金级别", "基金分类", "注册地区_基金目录"]))
        text = r["融资主体"]
        raw_names.add(text)
        yr = re.match(r"^(\d{4})(?:[/-]|$)", r["投资时间"].strip())
        year = int(yr[1]) if yr else None
        if year is None:
            for date_format in ["%y-%b", "%b-%y"]:
                try:
                    year = datetime.strptime(r["投资时间"].strip(), date_format).year
                    break
                except ValueError:
                    pass
        if year is not None and 2015 <= year <= 2024:
            first_any[norm(text)].append(year)
    conflicts = sum(len(v) > 1 for v in attribution.values())
    check("event_dedup_has_no_conflicting_attributions_in_this_input", conflicts == 0, conflicts=conflicts)
    if conflicts:
        warnings.append("Micro builder deduplicates economic fields without attribution: preserve/review conflicting assignments before using a changed input.")
    check("micro_first_any_matches_original_export", all(r.first_any_observed_fund_year == min(first_any[r.firm_name]) for r in firm.itertuples()))
    check("micro_earlier_other_exposure_flag", m.earlier_other_fund_observed.eq(m.first_any_observed_fund_year.lt(m.first_year).astype(int)).all())

    # Re-read the original patent shards, independently recomputing only target names.
    target_names = set(m.firm_name)
    patent_validation = {}
    for outcome, prefix, cols in [
        ("apply", "非上市公司专利申请情况", ["Invia", "Umia", "Desia", "Invja", "Umja", "Desja"]),
        ("grant", "非上市公司专利获得情况", ["Invig", "Umig", "Desig", "Invjg", "Umjg", "Desjg"]),
    ]:
        expected = {}
        counts = Counter()
        label_sets = set()
        normal_only_names = set()
        for path in sorted(PATENTS.rglob(prefix + "_*.csv")):
            for r in csv.DictReader(path.open(encoding="utf-8-sig", newline="")):
                if not re.fullmatch(r"\d{4}", r["Year"]):
                    label_sets.add(tuple(r[c] for c in cols))
                    continue
                counts["all_valid_source_rows"] += 1
                name = norm(r["Coname"])
                if name not in target_names:
                    continue
                cells = [int(float(r[c])) if re.fullmatch(r"\d+(?:\.0+)?", r[c].strip()) else None for c in cols]
                total = sum(cells) if all(c is not None for c in cells) else np.nan
                invention = cells[0] + cells[3] if cells[0] is not None and cells[3] is not None else np.nan
                key = name, int(r["Year"])
                value = total, invention
                if key in expected:
                    check(outcome + "_no_conflicting_duplicate_" + str(key), expected[key] == value)
                expected[key] = value
                counts["matched_rows"] += 1
                counts["explicit_total_zeros"] += total == 0
                counts["explicit_invention_zeros"] += invention == 0
                if r["Coname"] not in raw_names:
                    normal_only_names.add(name)
        wanted = [(r.firm_name, int(r.year)) for r in m.itertuples()]
        expected_total = np.array([expected.get(key, (np.nan, np.nan))[0] for key in wanted])
        expected_invention = np.array([expected.get(key, (np.nan, np.nan))[1] for key in wanted])
        expected_presence = np.array([key in expected for key in wanted], dtype=int)
        check(outcome + "_panel_values_equal_original_six_cells", np.allclose(m[outcome + "_total"], expected_total, equal_nan=True))
        check(outcome + "_invention_equals_independent_plus_joint", np.allclose(m[outcome + "_invention"], expected_invention, equal_nan=True))
        check(outcome + "_source_presence_equals_original", np.array_equal(m["has_" + outcome + "_row"], expected_presence))
        check(outcome + "_labels_independent_then_joint", all("独立" in labels[0] and "联合" in labels[3] for labels in label_sets))
        check(outcome + "_all_matches_exist_as_exact_raw_names", len(normal_only_names) == 0, normalized_only_names=sorted(normal_only_names))
        for r in firm.itertuples():
            e = int((r.firm_name, r.first_year - 1) in expected and (r.firm_name, r.first_year + 1) in expected and r.first_year + 1 <= 2023)
            actual = getattr(r, outcome + "_pair1")
            if actual != e:
                check(outcome + "_pair_flag_" + str(r.firm_id), False)
        patent_validation[outcome] = dict(counts= dict(counts), labels=[list(v) for v in label_sets])
        print("Validated original " + outcome + " rows", flush=True)

    # FE support uses a second implementation of complete-case recursive pruning.
    specs = {
        "F1": (["early", "p", "l_gdp", "l_secondary"], ["fund_id", "year", "sector_id"], "p", ["l_gdp", "l_secondary"]),
        "F2": (["early", "p", "l_gdp", "l_secondary", "recipient_city"], ["fund_id", "destination_year", "sector_id"], "p", ["l_gdp", "l_secondary"]),
        "F3": (["early", "p", "l_gdp", "l_secondary", "debt"], ["fund_id", "year", "sector_id"], "pd", ["p", "debt", "l_gdp", "l_secondary"]),
    }
    support = []
    for model, (required, effects, target, controls) in specs.items():
        s = f.dropna(subset=required).copy()
        old_index = None
        while old_index != tuple(s.index):
            old_index = tuple(s.index)
            valid = pd.Series(True, index=s.index)
            for effect in effects:
                valid &= s.groupby(effect)[effect].transform("size").ge(2)
            valid &= s.groupby("fund_id").year.transform("nunique").ge(2)
            s = s.loc[valid]
        check(model + "_recursive_pruning_matches", set(s.index) == set(f.index[f["use_" + model].eq(1)]))
        check(model + "_funds_have_multiple_years", s.groupby("fund_id").year.nunique().ge(2).all())
        for effect in effects:
            check(model + "_no_singletons_" + effect, s.groupby(effect).size().ge(2).all())
        design = np.column_stack([np.ones(len(s)), s[controls].to_numpy()] + [pd.get_dummies(s[e], drop_first=True, dtype=float).to_numpy() for e in effects])
        residual = s[target].to_numpy() - design @ np.linalg.lstsq(design, s[target].to_numpy(), rcond=None)[0]
        rss_by_city = pd.Series(residual ** 2).groupby(s.source_city.to_numpy()).sum().sort_values(ascending=False)
        shares = rss_by_city / rss_by_city.sum()
        row = dict(model=model, N=len(s), source_cities=s.source_city.nunique(), residual_sd=float(np.std(residual)),
                   residual_support_cities=int(rss_by_city.gt(1e-10).sum()),
                   top_city_residual_variation_share=float(shares.iloc[0]), top5_city_residual_variation_share=float(shares.iloc[:5].sum()),
                   inverse_hhi_residual_variation=float(1 / (shares ** 2).sum()),
                   top5_cities={k: float(v) for k, v in shares.iloc[:5].items()})
        if model == "F2":
            by_dest = s.groupby("destination_year").source_city.nunique()
            row["destination_year_groups"] = len(by_dest)
            row["destination_year_with_multiple_sources"] = int(by_dest.gt(1).sum())
            row["events_in_multi_source_destination_year"] = int(s.destination_year.isin(by_dest.index[by_dest.gt(1)]).sum())
            baseline = np.column_stack([np.ones(len(s)), s[controls].to_numpy()] + [pd.get_dummies(s[e], drop_first=True, dtype=float).to_numpy() for e in ["fund_id", "year", "sector_id"]])
            residual0 = s.p.to_numpy() - baseline @ np.linalg.lstsq(baseline, s.p.to_numpy(), rcond=None)[0]
            row["residual_variance_remaining_vs_F2a"] = float((residual @ residual) / (residual0 @ residual0))
        support.append(row)
    check("F2_and_F2a_same_sample", f.use_F2.eq(f.use_F2a).all())
    check("F3_and_F3a_same_sample", f.use_F3.eq(f.use_F3a).all())
    lag = macro[["city", "year", "fiscal_gap", "debt_ratio", "ln_gdp", "secondary_share"]].copy()
    lag.year += 1
    fm = f.merge(lag, left_on=["source_city", "year"], right_on=["city", "year"], how="left", validate="many_to_one")
    for a, b in [("p", "fiscal_gap"), ("debt", "debt_ratio"), ("l_gdp", "ln_gdp"), ("l_secondary", "secondary_share")]:
        check("fund_calendar_lag_" + a, np.allclose(fm[a], fm[b], equal_nan=True))
    warnings += [
        "Micro firms are conditioned on observed positive-total patent source rows; missing firm-years remain unknown, not zero. An explicit invention zero can coexist with positive non-invention patents.",
        "Earliest observed 2015-2024 investment is not first-ever investment; report left censoring and earlier investments from other scopes.",
        "F2 absorbs destination-year shocks and identifies fiscal variation from connected cross-source observations. Residual-share concentration is a support diagnostic, not a replacement cluster degrees-of-freedom calculation.",
        "First-year source-city uniqueness refers to all events in that calendar year, not one precise first-day financing event.",
    ]
    result = dict(passed=all(c["passed"] for c in checks), checks=checks, warnings=warnings, patent_source_validation=patent_validation, fund_identification_support=support,
                  artifacts_sha256={str(p.relative_to(ROOT)): sha(p) for p in [MICRO, CHOICE, MACRO, EVENTS]},
                  regressions_validated=False, regression_note="This pass validates construction and support; Stata result verification follows after estimation.")
    if (OUT / "model_results.csv").exists():
        result = validate_regressions(result)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(passed=result["passed"], checks=len(result["checks"]), failed=[c for c in result["checks"] if not c["passed"]], support=support), ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
