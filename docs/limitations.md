# Limitations

- The inventory is NHDPlus-scale, not every 3DHP puddle.
- Navajo Reservoir and other border waterbodies may extend outside Colorado.
- Blue Mesa and similar reservoirs appear as multiple source polygons.
- Weather is a 0.25° cell, which is coarse for cirque lakes.
- DEM centroid elevation is not lake stage.
- Most lakes have no bathymetry, no measured snow on the ice, no current, and no groundwater data.
- Sentinel-2 scenes are not pixel-classified; many days are cloudy.
- There are no attached field thickness measurements in v1.
- Intermittent lakes may be dry.
- The Stefan coefficient is a literature range, not a Colorado calibration.
- Ice thickness varies across a single lake. Shore, inlets, and aerators are unresolved.
- Free-tier APIs (Open-Meteo, OpenTopoData, Planetary Computer, OpenFreeMap, Esri imagery) can throttle or change terms.

Nothing in the interface should be read as permission to go onto ice.
