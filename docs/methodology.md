# Ice estimation methodology

Model version: `stefan_snow_v0.1`

## What is estimated

- Ice coverage (%) of the lake surface
- Ice thickness (cm) with a lower/upper range
- Ice state for map coloring
- Confidence / data-quality flags

## What is not estimated

- Safety for walking, skating, fishing, snowmobiles, cars, or trucks
- Vehicle load limits
- Ice quality (clear vs white vs slush)
- Currents, pressure ridges, or local thin spots

## Physics

Daily mean air temperature \(T\) (°C) contributes to freezing degree days when \(T < 0\):

\[
\mathrm{FDD} = \sum \max(0, -T)
\]

A freeze-over threshold \(\mathrm{FDD}_{on}\) increases with \(\log(1+\mathrm{area})\) and \(\log(1+\mathrm{depth})\). Reservoirs are penalized (unobserved through-flow). Intermittent lakes and playas are penalized because they may be dry. Elevations ≥ 3,000 m slightly lower the threshold.

After freeze-over, thickness follows a Stefan form:

\[
h = \alpha_{\mathrm{eff}} \sqrt{\mathrm{FDD}_{net}}
\]

\(\alpha_{\mathrm{clear}} = 2.1\,\mathrm{cm\,°C^{-0.5}\,d^{-0.5}}\) (range 1.3–2.9). Snow depth increases resistance (\(\alpha\) falls as snow increases). Thawing degree days reduce net FDD. Thickness below 1 cm is withheld.

Coverage uses a saturating function of FDD above the threshold, reduced by recent thaw and by wind on large waterbodies.

## Depth

NHDPlus `MeanDepth` is used when present and labeled as such. When it is missing, an area–depth heuristic supplies thermal inertia for freeze-over timing only. That heuristic is never written to `depth_m` as a measurement.

## Confidence

- **high** — weather complete enough, bathymetry present, not near the freeze-over threshold
- **moderate** — weather present, depth estimated
- **low** — intermittent/playa, incomplete weather, or near-threshold conditions
- **unavailable** — too few temperature days; ice fields are null

## Hindcast and forecast

The same model is walked through the 92-day weather window (hindcast, labeled as model estimates) and the 7-day forecast (explicitly forecast weather). Charts must keep those segments distinguishable. Previous winters can be requested later from the Open-Meteo archive API; they are also model estimates.

## Validation status

This release has not been calibrated against a Colorado ice-thickness observation network. Do not claim statewide accuracy. See `docs/limitations.md`.
