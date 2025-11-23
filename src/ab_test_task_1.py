# Task 1 - A/B Test setup

"""
- Simulates DAU using simple cohort + retention logic
- Combines DAU from multiple user sources (old + new)
- Estimates revenue from IAP + ads for each variant
"""

from dataclasses import dataclass

@dataclass
class VariantConfig:
    """
    Configuration of the A/B Test variant

    base_purchase_rate : float
        Daily purchase probability per install (example: 0.0305 = 3.05%)
    ecpm : float
        Ad eCPM (revenue per 1000 impressions)
    ad_impressions_per_dau : float
        AVG number of ad impressions per active user each day
    """
    name: str
    base_purchase_rate: float
    ecpm: float
    ad_impressions_per_dau: float

def simulate_dau(daily_installs, retention_fn):
    """
    Simulate DAU for one user source

    Parameters
    ----------
    daily_installs : list[int]
        Installs on each day
    retention_fn : function
        Function that takes 'age in days since install' and returns retention fraction (0-1)

    Returns
    -------
    list[float]
        DAU each day
    """
    days = len(daily_installs)
    dau = []

    for current_day in range(1, days + 1):
        active_users = 0.0
    
        # Loop over all past cohorts
        for install_day in range(1, current_day + 1):
            installs = daily_installs[install_day - 1]
            age = current_day - install_day + 1
            active_users += installs * retention_fn(age)

        dau.append(active_users)
    
    return dau

def combine_sources(*dau_sources):
    """
    Combine DAU from multiple variant sources (old + new)
    Each dau_sources[i] should be a list[float] with the same length

    Returns
    -------
    list[float]
        Total DAU each day
    """
    if not dau_sources:
        return[]
    
    days = len(dau_sources[0])
    total_dau = []

    for day_idx in range(days):
        day_sum = 0.0
        for source in dau_sources:
            day_sum += source[day_idx]
        total_dau.append(day_sum)

    return total_dau

def simulate_revenue(
        variant,
        daily_installs_total,
        dau_total,
        sale_period=None,
        sale_boost_abs=0.0,
        arppu=5.0,
):
    """
    Simulate daily revenue (IAP + ads) for one variant

    Parameters
    ----------
    variant : VariantConfig
        Config for A or B variant.
    daily_installs_total : list[int]
        Total installs per day (all sources combined)
    dau_total : list[float]
        Total DAU each day (all sources combined)
    sale_period : tuple (start_day, end_day)
        If not None, those days get a boost in purchase rate.
    sale_boost_abs: float
        Absolute boost to purchase rate during the sale.
    arppu : float
        Average revenue per paying user.

    Returns
    -------
    list[float]
        Daily revenue values.
    """
    assert len(daily_installs_total) == len(dau_total)

    daily_revenue = []

    for day_idx in range(len(dau_total)):
        day_number = day_idx + 1

        purchase_rate = variant.base_purchase_rate

        # Applying sale boost if in sale window
        if sale_period is not None:
            start, end = sale_period
            if start <= day_number <= end:
                purchase_rate += sale_boost_abs

        installs = daily_installs_total[day_idx]
        dau = dau_total[day_idx]

        # IAP revenue
        iap_revenue = installs * purchase_rate * arppu

        # Ad revenue
        ad_impressions = dau * variant.ad_impressions_per_dau
        ad_revenue = (ad_impressions * variant.ecpm) / 1000.0

        total = iap_revenue + ad_revenue
        daily_revenue.append(total)
    
    return daily_revenue