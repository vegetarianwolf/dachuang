import matplotlib.pyplot as plt

# Regression result from historical snapshot (no-controls baseline with city/year FE)
coef = -0.0391
se = 0.0146
p_value = 0.0073
n_obs = 1669

# 95% confidence interval
ci_low = coef - 1.96 * se
ci_high = coef + 1.96 * se

fig, ax = plt.subplots(figsize=(8, 5))

# Horizontal coefficient plot with CI
ax.errorbar(
    x=coef,
    y=0,
    xerr=[[coef - ci_low], [ci_high - coef]],
    fmt='o',
    color='#1f77b4',
    ecolor='#1f77b4',
    elinewidth=2,
    capsize=5,
    markersize=8,
)

# Zero reference line
ax.axvline(0, color='gray', linestyle='--', linewidth=1)

ax.set_yticks([0])
ax.set_yticklabels(['Debt ratio (L1) -> ln(Invention patents)'])
ax.set_xlabel('Estimated coefficient (95% CI)')
ax.set_title('No-controls regression result (historical snapshot)')

annotation = (
    f"coef = {coef:.4f}\n"
    f"SE = {se:.4f}\n"
    f"p = {p_value:.4f}\n"
    f"N = {n_obs}"
)
ax.text(
    0.98,
    0.05,
    annotation,
    transform=ax.transAxes,
    ha='right',
    va='bottom',
    fontsize=10,
    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
)

fig.tight_layout()
fig.savefig('debt_lag_effect_on_ln_patent.png', dpi=300)
plt.close(fig)

print('Saved figure: debt_lag_effect_on_ln_patent.png')
