# Terrain preparation tool

`tools/asc_to_obj.py` converts a clipped ESRI ASCII grid DTM into a triangulated OBJ
and a companion JSON provenance/coordinate record. It uses Python 3.10+ and the standard library.
This is an intermediate terrain asset for inspection and modeling, not a compiled CS2 map.
Automated tests use synthetic data. Two downloaded provincial DTM tiles, one for each campus
candidate, also passed an initial conversion check at `--step 10`: each produced 10,201 vertices
and 20,000 triangles. Their hashes matched the download records and their sample-centre extents
were preserved. This checks conversion, not geographic alignment or appearance in CS2.
See [the source provenance](../data/raw/terrain/provenance.json) for those inputs and licensing.

Prepare a small area in QGIS first. Verify the source CRS, horizontal units, elevation units,
and vertical datum from its documentation; reproject or convert units there if necessary.
This tool expects east/north coordinates and elevations in metres. It performs no reprojection,
datum conversion, or unit conversion. The CRS and datum arguments only record supplied labels.
EPSG:25832 is a candidate project CRS, not an assumption about any downloaded source.

Choose and record a project origin before export. The elevation origin must use the same
vertical reference as the source; it is a local offset, not a datum conversion.
For example, the following uses **synthetic coordinates and labels only**:

```sh
python3 tools/asc_to_obj.py /tmp/synthetic.asc /tmp/terrain.obj \
  --origin-easting 100 --origin-northing 200 --origin-elevation 1 \
  --crs 'synthetic projected metre grid' --vertical-datum 'synthetic' \
  --step 1
```

Accepted input has `ncols`, `nrows`, `cellsize`, either the paired `xllcorner`/`yllcorner`
or `xllcenter`/`yllcenter` headers, and optional `NODATA_value`. Header names are case insensitive.
The source's first row is north. Output vertices sample cell centres, with X east, Y north,
and Z up; faces wind counterclockwise when viewed from above. NoData must be a finite numeric
sentinel. The tool rejects nonfinite numbers, inconsistent sample counts, duplicate headers,
grids smaller than 2×2, and grids above 4,000,000 cells. Clip large sources before running it.

`--step N` keeps every Nth row/column and always the final row/column. Boundary **sample centres**
are retained; the tool does not extend the mesh by half a cell to the raster's outer edges.
Decimation loses terrain detail. Triangles touching NoData are omitted; a coarse quad with
NoData at discarded samples is omitted entirely to avoid bridging a hole. An empty mesh fails.

Both output paths must be unused unless `--force` is supplied. Their parent directory must exist.
Invalid input does not publish OBJ/JSON outputs. The sidecar includes the exact source SHA-256,
declared coordinate labels, local transform, sampling settings, mesh counts, and accuracy limits.
The OBJ has no materials, UVs, skirts, or gameplay collision. Check it in Blender against the
source terrain before translating it into Hammer's game units and constructing gameplay geometry.

Run the synthetic checks from the project root:

```sh
python3 -m unittest discover -s tests -v
```
