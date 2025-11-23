# Task 2 runner

from src.task_2_analysis import (
    load_all_data,
    preprocess,
    overview,
    platform_country_performance,
    engagement_vs_monetization,
    frustration_signals,
    cohort_retention,
    average_cohort_retention
)

def main():
    df_raw = load_all_data(sample_frac=0.2)
    df = preprocess(df_raw)

    overview(df)
    platform_country_performance(df)
    engagement_vs_monetization(df)
    frustration_signals(df)
    retention_table = cohort_retention(df, max_age=7)
    average_cohort_retention(retention_table)

if __name__ == "__main__":
    main()
