# Task 1 - Retention Logic

import math

def linear_retention(day, points):
    """
    Returns retention probability for a given day
    
    Parameters
    ----------
    day : int
        Age in days since install. (1 = the day variant was installed, 2 = D1 and so on, so on)
    points : dict
        Known retention points as {day: retention_fraction}.
        Example: {1: 1.0, 2: 0.53, 4: 0.27, 8: 0.17 15: 0.06}

    Returns
    -------
    float
        Retention fraction between 0 and 1.
        """
    # All users are retained on first day of install
    if day <= 1:
        return 1.0
    
    # Exact point
    if day in points:
        return points[day]
    
    known_days = sorted(points.keys())

    # If day is after the last known point, extrapolate linearly
    if day > known_days[-1]:
        d1, d2 = known_days[-2], known_days[-1]
        r1, r2 = points[d1], points[d2]
        slope = (r2 - r1) / (d2 - d1)
        return max(0.0, r2 + slope * (day - d2))
    
    # Else, find the interval where it falls
    prev_day = max(d for d in known_days if d < day)
    next_day = min(d for d in known_days if d > day)

    r1 = points[prev_day]
    r2 = points[next_day]
    slope = (r2 - r1) / (next_day - prev_day)

    return r1 + slope * (day - prev_day)

# New user source variant A comes in

def retention_new_variant_a(day):
    """
    New user source retention for Variant A:
    Retention = 0.58 * e^(-0.12 * (x - 1))
    """
    if day < 1:
        return 0.0
    return 0.58 * math.exp(-0.12 * (day - 1))

# New user source variant B comes in

def retention_new_variant_b(day):
    """
    New user source retention for Variant B:
    Retention = 0.52 * e^(-0.10 * (x - 1))
    """
    if day < 1:
        return 0.0
    return 0.52 * math.exp(-0.10 * (day - 1))
