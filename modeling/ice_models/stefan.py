"""Physics-informed lake ice model (Stefan-type growth with snow insulation).

Model version: stefan_snow_v0.1

This is an environmental estimate, not a field measurement. Thickness is not
observed. Coverage is modeled from thermal history and lake morphometry, then
optionally compared with satellite surface classifications when those exist.

References (methods, not calibration data):
- Stefan, J. (1891). Über die Theorie der Eisbildung.
- Ashton, G. D. (1986). *River and Lake Ice Engineering*.
- USACE ice engineering manuals: simplified ice growth h ≈ α √FDD.
- Typical α ranges ~0.5–3.5 cm °C^-0.5 day^-0.5 depending on snow, wind, and
  radiation. This implementation uses a snow-insulated effective α and
  morphometry-dependent freeze-over thresholds.

Unavailable information is never invented: missing weather yields an
unavailable prediction; missing depth is replaced with a clearly flagged
heuristic used only for freeze-over timing, not reported as measured depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

MODEL_VERSION = "stefan_snow_v0.1"
MODEL_NAME = "Stefan-type ice growth with snow insulation"
SEASON_MONTH_START = 8
SEASON_DAY_START = 15

# Stefan coefficient in cm per sqrt(°C · day). Mid-range clear-ice value.
ALPHA_CLEAR_CM = 2.1
ALPHA_CLEAR_LOW_CM = 1.3
ALPHA_CLEAR_HIGH_CM = 2.9


@dataclass(frozen=True)
class LakeParams:
    area_km2: float
    depth_m: float | None
    elevation_m: float | None
    waterbody_type: str
    fcode_desc: str | None = None
    depth_is_estimated: bool = False


@dataclass
class DailyEstimate:
    date: str
    is_forecast: bool
    tmin_c: float | None
    tmax_c: float | None
    tmean_c: float | None
    snow_depth_m: float | None
    snowfall_cm: float | None
    wind_speed_kmh: float | None
    precipitation_mm: float | None
    shortwave_mjm2: float | None
    fdd_c_day: float
    tdd_c_day: float
    ice_on: bool
    estimated_ice_coverage_pct: float | None
    estimated_ice_thickness_cm: float | None
    lower_thickness_cm: float | None
    upper_thickness_cm: float | None
    ice_state: str
    confidence: str
    notes: list[str] = field(default_factory=list)


def estimate_depth_m(area_km2: float) -> float:
    """Heuristic mean depth when bathymetry is missing.

    Uses a concave area–depth curve typical of small temperate lakes.
    Result must be flagged as estimated and never stored as measured depth.
    """
    area = max(float(area_km2), 0.001)
    return float(np.clip(1.2 + 4.5 * np.sqrt(area), 0.8, 35.0))


def freeze_over_fdd_threshold(params: LakeParams) -> float:
    """Accumulated freezing degree days typically needed before freeze-over.

    Larger and deeper waterbodies have more thermal inertia. Flow-through
    reservoirs and intermittent playas are penalized because water movement
    and dry beds are unobserved.
    """
    area = max(float(params.area_km2), 0.001)
    if params.depth_m is not None and params.depth_m > 0:
        depth = float(params.depth_m)
    else:
        depth = estimate_depth_m(area)
    threshold = 8.0 + 16.0 * np.log1p(area) + 5.5 * np.log1p(depth)
    wtype = (params.waterbody_type or "").lower()
    desc = (params.fcode_desc or "").lower()
    if "reservoir" in wtype or "reservoir" in desc:
        threshold *= 1.15
    if "intermittent" in desc or "playa" in wtype or "playa" in desc:
        threshold *= 1.1
    if "treatment" in desc or "disposal" in desc or "tailings" in desc:
        threshold *= 1.05
    if params.elevation_m is not None and params.elevation_m >= 3000:
        threshold *= 0.92
    return float(np.clip(threshold, 6.0, 220.0))


def _effective_alpha(snow_depth_m: float | None, wind_kmh: float | None) -> tuple[float, float, float]:
    snow_cm = 0.0 if snow_depth_m is None else max(float(snow_depth_m) * 100.0, 0.0)
    # Snow is a strong insulator; wind slightly offsets by compacting/removing snow.
    denom = 1.0 + 0.075 * snow_cm
    wind_factor = 1.0
    if wind_kmh is not None:
        wind_factor = 1.0 + 0.04 * min(max(float(wind_kmh) - 8.0, 0.0), 25.0) / 25.0
    alpha = ALPHA_CLEAR_CM * wind_factor / denom
    alpha_lo = ALPHA_CLEAR_LOW_CM / (1.0 + 0.11 * snow_cm)
    alpha_hi = ALPHA_CLEAR_HIGH_CM * wind_factor / (1.0 + 0.04 * snow_cm)
    return float(alpha), float(alpha_lo), float(alpha_hi)


def _coverage_pct(
    fdd: float,
    tdd_recent: float,
    threshold: float,
    area_km2: float,
    tmean_c: float | None,
    wind_kmh: float | None,
) -> float:
    excess = fdd - threshold
    if excess <= 0:
        if tmean_c is not None and tmean_c < -4 and area_km2 < 0.05:
            return 12.0
        return 0.0
    scale = 14.0 + 18.0 * np.log1p(area_km2)
    coverage = 100.0 * (1.0 - np.exp(-excess / scale))
    coverage *= np.exp(-tdd_recent / 18.0)
    if wind_kmh is not None and area_km2 >= 4.0:
        coverage *= max(0.72, 1.0 - 0.01 * max(float(wind_kmh) - 15.0, 0.0))
    return float(np.clip(coverage, 0.0, 100.0))


def _ice_state(coverage: float | None, thickness: float | None, confidence: str) -> str:
    if coverage is None or confidence == "unavailable":
        return "unknown"
    if coverage < 15:
        return "open_water"
    if coverage < 70:
        return "partial"
    if coverage < 90 or thickness is None or thickness < 4:
        return "extensive"
    return "frozen"


def _confidence(
    params: LakeParams,
    weather_days: int,
    missing_frac: float,
    coverage: float | None,
    threshold: float,
    fdd: float,
) -> str:
    if weather_days < 10 or missing_frac > 0.35:
        return "unavailable" if weather_days < 5 else "low"
    near_threshold = abs(fdd - threshold) < 12
    if params.depth_is_estimated or params.depth_m is None:
        base = "moderate"
    else:
        base = "high"
    desc = (params.fcode_desc or "").lower()
    if "intermittent" in desc or "playa" in (params.waterbody_type or "").lower():
        base = "low"
    if near_threshold or (coverage is not None and 20 <= coverage <= 80):
        if base == "high":
            base = "moderate"
        elif base == "moderate":
            base = "low"
    return base


def simulate_season(
    dates: Iterable[str],
    tmean_c: Iterable[float | None],
    tmin_c: Iterable[float | None] | None = None,
    tmax_c: Iterable[float | None] | None = None,
    snow_depth_m: Iterable[float | None] | None = None,
    snowfall_cm: Iterable[float | None] | None = None,
    wind_speed_kmh: Iterable[float | None] | None = None,
    precipitation_mm: Iterable[float | None] | None = None,
    shortwave_mjm2: Iterable[float | None] | None = None,
    is_forecast: Iterable[bool] | None = None,
    params: LakeParams | None = None,
) -> list[DailyEstimate]:
    """Accumulate FDD and emit a modeled ice series.

    Degree-days use daily mean air temperature relative to 0 °C. Ice thickness
    uses a Stefan √FDD form after the freeze-over threshold is reached, with
    thawing degree days reducing net FDD. Thickness is omitted (None) until
    freeze-over is modeled; it is never filled with a placeholder measurement.
    """
    params = params or LakeParams(area_km2=0.05, depth_m=None, elevation_m=None, waterbody_type="Lake/Pond")
    dates_l = list(dates)
    tmean = list(tmean_c)
    n = len(dates_l)
    if len(tmean) != n:
        raise ValueError("dates and tmean_c must be the same length")

    def _col(values: Iterable[float | None] | None) -> list[float | None]:
        if values is None:
            return [None] * n
        out = list(values)
        if len(out) != n:
            raise ValueError("all weather columns must match dates length")
        return out

    tmin = _col(tmin_c)
    tmax = _col(tmax_c)
    snow = _col(snow_depth_m)
    sfall = _col(snowfall_cm)
    wind = _col(wind_speed_kmh)
    precip = _col(precipitation_mm)
    sw = _col(shortwave_mjm2)
    forecast_flags = _col(is_forecast) if is_forecast is not None else [False] * n

    threshold = freeze_over_fdd_threshold(params)
    fdd = 0.0
    tdd = 0.0
    ice_on = False
    fdd_since_on = 0.0
    tdd_since_on = 0.0
    tdd_window: list[float] = []
    valid_days = 0
    missing_days = 0
    out: list[DailyEstimate] = []

    for i, date in enumerate(dates_l):
        tm = tmean[i]
        notes: list[str] = []
        if params.depth_m is None or params.depth_is_estimated:
            notes.append("Mean depth is estimated from surface area; it is not bathymetry.")
        desc = (params.fcode_desc or "").lower()
        if "intermittent" in desc or "playa" in (params.waterbody_type or "").lower():
            notes.append("Waterbody may be seasonally dry; ice is only meaningful if water is present.")

        if tm is None or not np.isfinite(tm):
            missing_days += 1
            confidence = _confidence(params, valid_days, missing_days / max(valid_days + missing_days, 1), None, threshold, fdd)
            out.append(
                DailyEstimate(
                    date=date,
                    is_forecast=bool(forecast_flags[i]),
                    tmin_c=_num(tmin[i]),
                    tmax_c=_num(tmax[i]),
                    tmean_c=None,
                    snow_depth_m=_num(snow[i]),
                    snowfall_cm=_num(sfall[i]),
                    wind_speed_kmh=_num(wind[i]),
                    precipitation_mm=_num(precip[i]),
                    shortwave_mjm2=_num(sw[i]),
                    fdd_c_day=fdd,
                    tdd_c_day=tdd,
                    ice_on=ice_on,
                    estimated_ice_coverage_pct=None if not ice_on else out[-1].estimated_ice_coverage_pct if out else None,
                    estimated_ice_thickness_cm=None,
                    lower_thickness_cm=None,
                    upper_thickness_cm=None,
                    ice_state="unknown",
                    confidence=confidence,
                    notes=notes + ["Daily mean temperature missing; estimate withheld for this date."],
                )
            )
            continue

        valid_days += 1
        if tm < 0:
            fdd += -tm
            if ice_on:
                fdd_since_on += -tm
        else:
            tdd += tm
            if ice_on:
                tdd_since_on += tm
                fdd_since_on = max(0.0, fdd_since_on - 0.65 * tm)
        tdd_window.append(max(tm, 0.0))
        tdd_window = tdd_window[-7:]
        tdd_recent = float(sum(tdd_window))

        if not ice_on and fdd >= threshold:
            ice_on = True
            fdd_since_on = max(fdd - threshold, 0.0)

        coverage = _coverage_pct(fdd, tdd_recent, threshold, params.area_km2, tm, wind[i])
        thickness = lower = upper = None
        if ice_on and fdd_since_on > 0:
            alpha, alpha_lo, alpha_hi = _effective_alpha(snow[i], wind[i])
            thickness = alpha * np.sqrt(fdd_since_on)
            lower = alpha_lo * np.sqrt(fdd_since_on)
            upper = alpha_hi * np.sqrt(fdd_since_on)
            # Overnight skim ice is not reported as a thickness measurement.
            if thickness < 1.0:
                thickness = lower = upper = None
                notes.append("Modeled ice is thinner than 1 cm; thickness withheld.")
        elif coverage >= 15 and not ice_on:
            notes.append("Partial skim ice possible from cold nights; freeze-over threshold not reached.")

        missing_frac = missing_days / max(valid_days + missing_days, 1)
        confidence = _confidence(params, valid_days, missing_frac, coverage, threshold, fdd)
        state = _ice_state(coverage, thickness, confidence)
        if bool(forecast_flags[i]):
            notes.append("This date uses forecast weather, not an observation.")
        out.append(
            DailyEstimate(
                date=date,
                is_forecast=bool(forecast_flags[i]),
                tmin_c=_num(tmin[i]),
                tmax_c=_num(tmax[i]),
                tmean_c=float(tm),
                snow_depth_m=_num(snow[i]),
                snowfall_cm=_num(sfall[i]),
                wind_speed_kmh=_num(wind[i]),
                precipitation_mm=_num(precip[i]),
                shortwave_mjm2=_num(sw[i]),
                fdd_c_day=round(fdd, 2),
                tdd_c_day=round(tdd, 2),
                ice_on=ice_on,
                estimated_ice_coverage_pct=round(coverage, 1),
                estimated_ice_thickness_cm=None if thickness is None else round(float(thickness), 1),
                lower_thickness_cm=None if lower is None else round(float(lower), 1),
                upper_thickness_cm=None if upper is None else round(float(upper), 1),
                ice_state=state,
                confidence=confidence,
                notes=notes,
            )
        )
    return out


def _num(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(v):
        return None
    return v
