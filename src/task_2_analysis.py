"""
Task 2 - User behaviour & monetization analysis

Dataset: Daily user metrics

Columns:
user_id, event_date, platform, install_date, country, total_session_count, total_session_duration, match_start_count, match_end_count, victory_count, defeat_count, server_connection_error, iap_revenue, ad_revenue

How am I going to analyze the data?
- Load & process all the data from CSV.GZ files in /data
- Create derived metrics from the original data to help with the analysis
- Run analyses for "Platform & country performance", "Engagement vs monetization", "Frustration signals (error, defeats), "Retention by install cohort"
- Create plots for these analyses and save them in /plots
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.style.use("Solarize_Light2")

data_dir = Path("data")

# Load and concatenate all .csv.gz files from /data
def load_all_data(sample_frac: float | None = None) -> pd.DataFrame:

    files = sorted(data_dir.glob("*.csv.gz"))
    if not files:
        raise FileNotFoundError(f"No .csv.gz files found in /data")

    dfs = []
    for f in files:
        print(f"Loading {f.name} ...")
        df_part = pd.read_csv(f)
        if sample_frac is not None:
            df_part = df_part.sample(frac=sample_frac, random_state=42)
        dfs.append(df_part)

    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(df):,} rows from {len(files)} files.")
    return df

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    # Clean the data + create derived metrics: convert_date, days_since_install, total_revenue, is_payer, win_rate
    df = df.copy()

    # Dates
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["install_date"] = pd.to_datetime(df["install_date"])

    # Days since install
    df["days_since_install"] = (df["event_date"] - df["install_date"]).dt.days

    # Total Revenue + is_payer
    df["total_revenue"] = df["iap_revenue"] + df["ad_revenue"]
    df["is_payer"] = df["total_revenue"] > 0

    # Win Rate
    fights = df["victory_count"] + df["defeat_count"]
    df["win_rate"] = df["victory_count"] / fights.replace({0: np.nan})

    return df

def annotate_line_points(ax, xs, ys, pct=False):
     for x, y in zip(xs, ys):
          label = f"{y*100:.1f}%" if pct else f"{y:.3f}"
          ax.text(
               x,
               y,
               label,
               ha = "center", 
               va = "bottom",
               fontsize = 8,
               bbox = dict(alpha = 0.55, boxstyle = "round, pad=0.2")
          )

def annotate_bars_vertical(ax, pct: bool = False):
    for patch in ax.patches:
        value = patch.get_height()
        label = f"{value*100:.1f}%" if pct else f"{value:.2f}"

        x = patch.get_x() + patch.get_width() / 2
        y = value

        ax.text(
            x,
            y,
            label,
            ha="center",
            va="bottom",
            fontsize=8,
            bbox=dict(alpha=0.55, boxstyle="round,pad=0.2")
        )


def annotate_bars_horizontal(ax, pct: bool = False):
    for patch in ax.patches:
        value = patch.get_width()
        label = f"{value*100:.1f}%" if pct else f"{value:.2f}"
        x = value
        y = patch.get_y() + patch.get_height() / 2

        ax.text(
            x + (abs(value) * 0.02),
            y,
            label,
            ha="left",
            va="center",
            fontsize=8,
            bbox=dict(alpha=0.55, boxstyle="round,pad=0.2")
        )

# Analysis Functions

def overview(df: pd.DataFrame) -> None:
    # Basic data overview
    print("\n=== Overview ===")
    n_rows = len(df)
    n_users = df["user_id"].nunique()
    date_min = df["event_date"].min()
    date_max = df["event_date"].max()

    print(f"Rows: {n_rows:,}")
    print(f"Unique users: {n_users:,}")
    print(f"Event date range: {date_min.date()} -> {date_max.date()}")
    print(f"Platforms: {df['platform'].unique()}")
    print(f"Countries (top 10):") 
    print(df["country"].value_counts().head(10))
    print("\nDays since install (min/median/max):",
          int(df["days_since_install"].min()),
          int(df["days_since_install"].median()),
          int(df["days_since_install"].max()))
    
def platform_country_performance(df: pd.DataFrame) -> None:
    """
    Compare platforms and top countries on users/revenue
    
    - Create tables and bar charts of revenue per platform/ ARPU for top countries"""

    print("\n=== Platform Performance ===")
    plat = (
        df.groupby("platform").agg(
            users = ("user_id", "nunique"),
            total_rev = ("total_revenue", "sum"),
            payers = ("is_payer", "sum")
        )
    )
    plat["ARPU"] = plat["total_rev"] / plat["users"]
    plat["Payer share"] = plat["payers"] / plat["users"]
    print(plat.sort_values("total_rev", ascending=False))

    # Plot Revenue per platform
    ax = plat.sort_values("total_rev").plot(
        kind = "barh",
        y = "total_rev",
        legend=False,
        title = "Total revenue by platform"
    )
    annotate_bars_horizontal(ax, pct=False)
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Platform")
    plt.tight_layout()
    plt.savefig("plots/task_2_revenue_by_platform.png")
    plt.close()

    print("\n=== Country Performance (top 10 by revenue) ===")
    country = (
        df.groupby("country").agg(
            users = ("user_id", "nunique"),
            total_rev = ("total_revenue", "sum")        
        )
    )

    country["arpu"] = country["total_rev"] / country["users"]
    arpu_top = country.sort_values("total_rev", ascending=False).head(10)

    if arpu_top.empty:
         print("No country data available.")
    else:
        print(arpu_top)

    ax = arpu_top.sort_values("arpu").plot(
         kind="barh",
        y="arpu",
        legend=False,
        title="ARPU (Top 10 Countries by Revenue)"
    )
    annotate_bars_horizontal(ax, pct=False)
    ax.set_xlabel("ARPU (revenue per user)")
    ax.set_ylabel("Country")
    plt.tight_layout()
    plt.savefig("plots/task_2_arpu_countries.png")
    plt.close()

def engagement_vs_monetization(df: pd.DataFrame) -> None:
        """
        How does engagement relate to revenue?
        
        - Group users by session count
        - Show AVG revenue per Group
        """

        print("\n=== Engagement vs Monetization ===")

        # Aggregate per user
        agg_user = (
            df.groupby("user_id").agg(
                platform = ("platform", "first"),
                country = ("country", "first"),
                total_sessions = ("total_session_count", "sum"),
                total_duration = ("total_session_duration", "sum"),
                total_rev = ("total_revenue", "sum"),
            )
        )

        # Define session groups
        groups = [0, 1, 3, 10, 30, 100, np.inf]
        labels = ["1", "2-3", "4-10", "11-30", "31-100", "100+"]
        agg_user["session_group"] = pd.cut(
            agg_user["total_sessions"], 
            bins = groups, 
            labels = labels, 
            right = True
        )

        group = (
            agg_user.groupby("session_group", observed=True).agg(
                users = ("total_rev", "size"),
                payers = ("total_rev", lambda x: (x > 0).sum()),
                avg_rev = ("total_rev", "mean")
            )
        )

        group["payer_share"] = group["payers"] / group["users"]
        print(group)

        # Average revenue by group
        ax = group["avg_rev"].plot(
            kind = "bar",
            title = "AVG Revenue per user by session group"
        )
        annotate_bars_vertical(ax, pct=False)
        ax.set_xlabel("Total sessions (group)")
        ax.set_ylabel("AVG revenue per user")
        plt.tight_layout()
        plt.savefig("plots/task_2_rev_by_group.png")
        plt.close()

def frustration_signals(df: pd.DataFrame) -> None:
        """
        Exploring the potential frustration by looking at:
        - server_connection_error occurences
        - Low win_rate
        """

        print("\n === Frustration Signals ===")
        df["has_error"] = df["server_connection_error"] > 0

        # Error rate by platform
        error_platform = (
            df.groupby("platform").agg(
                days = ("event_date", "nunique"),
                user_days = ("user_id", "size"),
                error_days = ("has_error", "sum") 
            )
        )

        error_platform["error_rate"] = error_platform["error_days"] / error_platform["user_days"]
        print("\nServer Connection error rate by platform:")
        print(error_platform.sort_values("error_rate", ascending=False))

        # Top 10 countries by error rate
        error_country = (
            df.groupby("country").agg(
                user_days = ("user_id", "size"),
                error_days = ("has_error", "sum")
            )
        )
        error_country["error_rate"] = error_country["error_days"] / error_country["user_days"]
        error_country = error_country[error_country["user_days"] > 5000] # avoid tiny countries below 5000
        
        print("\nCountries with highest error rates:")
        print(error_country.sort_values("error_rate", ascending=False).head(10))

        # Error Rate Plot
        error_top = error_country.sort_values("error_rate", ascending=False).head(10)
        ax = error_top.sort_values("error_rate").plot(
            kind = "barh",
            y = "error_rate",
            legend = False,
            title = "Top countries by error rate"
        )
        annotate_bars_horizontal(ax, pct=True)
        ax.set_xlabel("Error Rate (%)")
        ax.set_ylabel("Country")
        plt.tight_layout()
        plt.savefig("plots/task_2_error_rate_countries.png")
        plt.close()

        print("\n Debut error Rates:")
        print(error_top["error_rate"].head(10))

        # Win Rate Distribution
        vals = df["win_rate"].dropna()
        
        fig, ax = plt.subplots()
        ax = vals.plot(
             kind = "hist",
             bins = 30,
             title = "Distribution of per-day win rate"
        )

        mean_wr = vals.mean()
        ax.text(
             0.05,
             0.95,
             f"Win Rate (mean): {mean_wr*100:.1f}%",
             transform = ax.transAxes,
             ha = "left",
             va = "top",
             fontsize = 10,
             bbox = dict(alpha=0.7, boxstyle="round,pad=0.2")
        )
        ax.set_xlabel("Win Rate (%)")
        plt.tight_layout()
        plt.savefig("plots/task_2_win_rate.png")
        plt.close()

def cohort_retention(df: pd.DataFrame, max_age: int = 7) -> pd.DataFrame:
    print("\n=== Cohort retention (up to D{}) ===".format(max_age))

    # Cohort size per install_date
    cohort_size = df.groupby("install_date")["user_id"].nunique()

    # for each age, check active users
    ret = {}
    for age in range(1, max_age + 1):
        mask = df["days_since_install"] == age
        active = (
            df[mask].groupby("install_date")["user_id"].nunique()
        )
        rate = (active / cohort_size).rename(f"D{age}")
        ret[f"D{age}"] = rate

    retention_table = pd.concat(ret.values(), axis=1)
    print(retention_table.describe())
    return retention_table

def average_cohort_retention(retention_table: pd.DataFrame) -> None:
    means = retention_table.mean().reset_index()
    means["day"] = means["index"].str.extract(r"D(\d+)").astype(int)
    means = means.sort_values("day")

    ax = plt.figure().gca()
    line = ax.plot(
         means["day"],
         means[0],
         marker = "o",
         linewidth = 2,
    )[0]

    annotate_line_points(
         ax,
         means["day"].values,
         means[0].values,
         pct = True
    )

    ax.set_xlabel("Days since install")
    ax.set_ylabel("Retention rate (%)")
    ax.set_title("AVG cohort retention")
    plt.tight_layout()
    plt.savefig("plots/task_2_avg_cohort.png")
    plt.close()