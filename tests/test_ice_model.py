from modeling.ice_models.stefan import LakeParams, estimate_depth_m, freeze_over_fdd_threshold, simulate_season


def test_stefan_thickness_matches_sqrt_fdd():
    params = LakeParams(area_km2=0.02, depth_m=2.0, elevation_m=3200, waterbody_type="Lake/Pond")
    dates = [f"2026-01-{day:02d}" for day in range(1, 21)]
    tmean = [-10.0] * 20
    series = simulate_season(dates, tmean, params=params)
    last = series[-1]
    assert last.ice_on
    assert last.estimated_ice_thickness_cm is not None
    assert last.lower_thickness_cm < last.estimated_ice_thickness_cm < last.upper_thickness_cm
    assert last.estimated_ice_coverage_pct is not None
    assert last.estimated_ice_coverage_pct > 80


def test_warm_weather_is_open_water():
    params = LakeParams(area_km2=5.0, depth_m=15.0, elevation_m=1400, waterbody_type="Reservoir")
    dates = [f"2026-07-{day:02d}" for day in range(1, 16)]
    series = simulate_season(dates, [18.0] * 15, params=params)
    last = series[-1]
    assert last.ice_state == "open_water"
    assert last.estimated_ice_thickness_cm is None
    assert last.estimated_ice_coverage_pct == 0


def test_missing_temperature_is_not_invented():
    params = LakeParams(area_km2=0.1, depth_m=None, elevation_m=2500, waterbody_type="Lake/Pond")
    series = simulate_season(["2026-01-01", "2026-01-02"], [None, None], params=params)
    assert series[-1].ice_state == "unknown"
    assert series[-1].estimated_ice_thickness_cm is None


def test_larger_lakes_need_more_cold():
    small = freeze_over_fdd_threshold(LakeParams(0.01, 1.5, 3000, "Lake/Pond"))
    large = freeze_over_fdd_threshold(LakeParams(40.0, 20.0, 2300, "Reservoir"))
    assert large > small * 2


def test_estimated_depth_is_positive():
    assert 0.8 <= estimate_depth_m(0.001) <= 35
    assert estimate_depth_m(50) >= estimate_depth_m(0.05)
