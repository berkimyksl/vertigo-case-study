# Task 1 runner

"""
Uses src/retention.py and src/ab_test_task_1.py


Simulating:
- DAU for Variant A and B
- Revenue up to Day 15 and Day 30
- Effect of a 10-day sale
- Effect of adding a new user source
"""

import os
import numpy as np
import matplotlib.pyplot as plt

plt.style.use("Solarize_Light2")

from src.ab_test_task_1 import (
    VariantConfig,
    simulate_dau,
    combine_sources,
    simulate_revenue
)

from src.retention import (
    linear_retention,
    retention_new_variant_a,
    retention_new_variant_b
)

# Define retention for ORIGINAL source - day 1 = install day. D1 Retention = Age 2 and so on so on
retention_points_a = {
    1: 1.0, # install day
    2: 0.53, # D1 = 53%
    4: 0.27, # D3 = 27%
    8: 0.17, # D7 = 17%
    15: 0.06 # D14 = 6%
}

retention_points_b = {
    1: 1.0, # install day
    2: 0.48, # D1 = 48%
    4: 0.25, # D3 = 25%
    8: 0.19, # D7 = 19%
    15: 0.09 # D14 = 9%
}

def retention_a_original(day: int) -> float:
    return linear_retention(day, retention_points_a)

def retention_b_original(day:int) -> float:
    return linear_retention(day, retention_points_b)

# 2. Defining variants A and B
variant_a = VariantConfig(
    name="A",
    base_purchase_rate=0.0305,
    ecpm=9.80,
    ad_impressions_per_dau=2.3
)

variant_b = VariantConfig(
    name="B",
    base_purchase_rate=0.0315,
    ecpm=10.80,
    ad_impressions_per_dau=1.6
)

# 3. Printing Totals
def print_totals(label, rev_a, rev_b):
    print(f"\n{label}")
    print(f"  Variant A total revenue: {rev_a:,.2f}")
    print(f"  Variant B total revenue: {rev_b:,.2f}")
    if rev_a > rev_b:
        print("  -> Winner: A")
    elif rev_b > rev_a:
        print("  -> Winner: B")
    else:
        print("  -> Tie")

def plots_dir():
    os.makedirs("plots", exist_ok=True)

def main():
    days = 30
    day_axis = np.arange(1, days + 1)
    base_installs = [20000] * days # 20k installs/day for both variants

    # Original source

    dau_a_old = simulate_dau(base_installs, retention_a_original)
    dau_b_old = simulate_dau(base_installs, retention_b_original)

    # DAU on day 15
    dau15_a = dau_a_old[14]
    dau15_b = dau_b_old[14]
    print("Original Source")
    print(f" (a) Day 15 DAU - A: {dau15_a:.0f}, B: {dau15_b:.0f}")
    print("-> Winner (DAU after 15 days):", "A" if dau15_a > dau15_b else "B")

    # Revenue without 10-day sale 
    rev_a_base = simulate_revenue(variant_a, base_installs, dau_a_old)
    rev_b_base = simulate_revenue(variant_b, base_installs, dau_b_old)

    rev15_a = sum(rev_a_base[:15])
    rev15_b = sum(rev_b_base[:15])
    print_totals("(b) Total revenue by Day 15", rev15_a, rev15_b)

    rev30_a = sum(rev_a_base[:30])
    rev30_b = sum(rev_b_base[:30])
    print_totals("(c) Total revenue by Day 30", rev30_a, rev30_b)

    # 10-day sale results
    sale_period = (15, 24)
    sale_boost = 0.01 # +1 percentage point

    rev_a_sale = simulate_revenue(
        variant_a,
        daily_installs_total=base_installs,
        dau_total=dau_a_old,
        sale_period=sale_period,
        sale_boost_abs=sale_boost,
    )

    rev_b_sale = simulate_revenue(
        variant_b,
        daily_installs_total=base_installs,
        dau_total=dau_b_old,
        sale_period=sale_period,
        sale_boost_abs=sale_boost,
    )

    rev30_a_sale = sum(rev_a_sale[:30])
    rev30_b_sale = sum(rev_b_sale[:30])
    print_totals("(d) Total revenue by Day 30 with 10-day sale", rev30_a_sale, rev30_b_sale)

    # New user source after Day 20
    installs_old = [20000] * 19 + [12000] * 11
    installs_new = [0] * 19 + [8000] * 11
    totals_installs = [o + n for o, n in zip(installs_old, installs_new)]

    # DAU from old and new sources for A and B variants
    dau_a_old_mix = simulate_dau(installs_old, retention_a_original)
    dau_a_new_mix = simulate_dau(installs_new, retention_new_variant_a)
    dau_a_total = combine_sources(dau_a_old_mix, dau_a_new_mix)

    dau_b_old_mix = simulate_dau(installs_old, retention_b_original)
    dau_b_new_mix = simulate_dau(installs_new, retention_new_variant_b)
    dau_b_total = combine_sources(dau_b_old_mix, dau_b_new_mix)

    # Revenue with the total
    rev_a_newsource = simulate_revenue(
        variant_a,
        daily_installs_total=totals_installs,
        dau_total=dau_a_total
    )

    rev_b_newsource = simulate_revenue(
        variant_b,
        daily_installs_total=totals_installs,
        dau_total=dau_b_total,
    )

    rev30_a_new = sum(rev_a_newsource[:30])
    rev30_b_new = sum(rev_b_newsource[:30])
    print_totals("(e) Total revenue by Day 30 with new user source", rev30_a_new, rev30_b_new)


    # Sale vs new user source
    inc_a_sale = rev30_a_sale - rev30_a
    inc_b_sale = rev30_b_sale - rev30_b

    inc_a_new = rev30_a_new - rev30_a
    inc_b_new = rev30_b_new - rev30_b

    print("\n(f) Incremental lift vs. original source by Day 30:")
    print(f"  Variant A - sale:    {inc_a_sale:,.2f}")
    print(f"  Variant A - new source:    {inc_a_new:,.2f}")
    print(f"  Variant B - sale:    {inc_b_sale:,.2f}")
    print(f"  Variant B - new source:    {inc_b_new:,.2f}")

    if inc_a_new + inc_b_new > inc_a_sale + inc_b_sale:
        print("\n-> (f) Overall, the new permanent user source creates more value than the temporary sale.")
    else:
        print("\n-> (f) Overall, the temporary sale creates more value than the new user source.")

    # PLOTS
    cum_rev_a_base = np.cumsum(rev_a_base)
    cum_rev_b_base = np.cumsum(rev_b_base)
    
    cum_rev_a_sale = np.cumsum(rev_a_sale)
    cum_rev_b_sale = np.cumsum(rev_b_sale)


    cum_rev_a_new = np.cumsum(rev_a_newsource)
    cum_rev_b_new = np.cumsum(rev_b_newsource)


    # Plot 1: DAU over time
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(day_axis, dau_a_old, label="Variant A", linewidth=2)
    ax.plot(day_axis, dau_b_old, label="Variant B", linewidth=2)

    # Highlight Day 15
    ax.axvline(15, color="gray", linestyle="--", linewidth=1)
    ax.text(15.1, max(dau_a_old + dau_b_old) * 0.2, "(Day 15)", fontsize=9, color="gray")
    ax.set_title("Task 1 - DAU over time\nVariant B retains slightly more users", fontsize=12)
    ax.set_xlabel("Day")
    ax.set_ylabel("DAU")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plots/task_1_dau_story.png")
    plt.close(fig)

    # Plot 2: Cumulative revenue A vs B (original user source)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(day_axis, cum_rev_a_base, label="Variant A", linewidth=2)
    ax.plot(day_axis, cum_rev_b_base, label="Variant B", linewidth=2)

    # Mark Day 15 and Day 30
    for d, label in [(15, "Day 15"), (30, "Day 30")]:
        ax.axvline(d, color="gray", linestyle="--", linewidth=1)
        ax.text(d + 0.2, cum_rev_a_base[-1] * 0.05, label, fontsize=8, color="gray")

    # Annotate the gap at Day 30
    ax.annotate(
        "A earns more\nby Day 30",
        xy=(30, cum_rev_a_base[-1]),
        xytext=(20, cum_rev_a_base[-1] * 0.9),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9,
    )

    ax.set_title("Task 1 - Cumulative revenue (original user source)\nVariant A monetizes better than Variant B", fontsize=12)
    ax.set_xlabel("Day")
    ax.set_ylabel("Cumulative revenue")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plots/task_1_cumulative_revenue_original.png")
    plt.close(fig)

    # Plot 3: Variant A (original user source vs sale vs new source)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(day_axis, cum_rev_a_base, label="A - original", linewidth=2.4, linestyle="--", color="red")
    ax.plot(day_axis, cum_rev_a_sale, label="A - with sale", linewidth=2, color="blue")
    ax.plot(day_axis, cum_rev_a_new, label="A - with new source", linewidth=2, color="green")

    # Sale period
    ax.axvspan(15, 24, color="yellow", alpha=0.15)
    ax.text(15.2, cum_rev_a_sale[-1] * 0.2, "10-day sale", fontsize=9)

    # Start of new source
    ax.axvline(20, color="green", linestyle=":", linewidth=1)
    ax.text(20.2, cum_rev_a_sale[-1] * 0.5, "New user\nsource starts here", fontsize=8)
    ax.set_title(" Task 1 - Variant A\nSale clearly outperforms the new source", fontsize=12)
    ax.set_xlabel("Day")
    ax.set_ylabel("Cumulative revenue (A)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plots/task_1_cumrevenue_A_scenerios.png")
    plt.close(fig)

    # Plot 4: Variant B (original user source vs sale vs new source)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(day_axis, cum_rev_b_base, label="B – original", linewidth=2.4, linestyle="--", color="red")
    ax.plot(day_axis, cum_rev_b_sale, label="B – with sale", linewidth=2, color="blue")
    ax.plot(day_axis, cum_rev_b_new, label="B – with new source", linewidth=2, color="green")

    # Sale period
    ax.axvspan(15, 24, color="yellow", alpha=0.15)
    ax.text(15.2, cum_rev_b_sale[-1] * 0.2, "10-day sale", fontsize=9)

    # Start of new source
    ax.axvline(20, color="green", linestyle=":", linewidth=1)
    ax.text(20.2, cum_rev_b_sale[-1] * 0.5, "New user\nsource starts here", fontsize=8)
    ax.set_title("Task 1 – Variant B\nSame story: sale > new source", fontsize=12)
    ax.set_xlabel("Day")
    ax.set_ylabel("Cumulative revenue (B)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("plots/task_1_cumrevenue_B_scenerios.png")
    plt.close(fig)

if __name__ == "__main__":
    main()