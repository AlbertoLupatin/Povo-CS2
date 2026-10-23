# Geographic source register

Researched 22 October 2026. Metadata availability is distinct from downloaded, inspected data. Source resolution is not a guarantee of positional accuracy or present-day completeness.

## Core candidates

| Source | Useful content | Licence and verification | Outstanding work |
| --- | --- | --- | --- |
| [PAT LiDAR collection](https://www.provincia.tn.it/News/Approfondimenti/Rilievo-Lidar-del-territorio-della-Provincia-di-Trento) | Terrain DTM, surface DSM, building-surface DBM in ASC/XYZ; raw LAZ | Collection verified; check individual resources | Identify campus tiles, survey dates and actual file headers |
| [PAT DTM metadata](https://siatservices.provincia.tn.it/geonetwork/srv/api/records/p_TN:79c6cdf0-c73a-46ba-870c-704bf4e27ac3) | Ground surface; abstract specifies 0.5 m cells; 2013–2015 acquisition plus 2018 updates | CC BY 4.0 in resource metadata | Metadata also contains a generic 1 m field; verify actual tile resolution. Confirm projected CRS |
| [PAT DBM metadata](https://siatservices.provincia.tn.it/geonetwork/srv/api/records/p_TN:ee78298d-818c-492b-bdeb-07a2ef173716) | 0.5 m building-surface raster; useful for estimating roofs against ground | CC BY 4.0 in resource metadata | Check alignment with DTM and imagery; this is not a building mesh |
| [Comune 2024 orthophoto](https://gis.comune.trento.it/it/map/cartografia-generale/qdjango/42/) | 10 cm source imagery, acquired 28–29 August 2024; EPSG:25832 | Layer metadata states CC0 1.0 Universal | WMS extracts are resampled reference images, not the full-resolution original raster |
| [Comune polygon technical map](https://dati.trentino.it/dataset/carta-tecnica-poligoni-open-data/resource/adde936e-c517-4f83-b3dd-e01daec6e905) | 1:2,000 technical polygons in GeoJSON/SHP; candidate building outlines | Resource says CC BY 4.0; parent dataset says CC0. Preserve attribution and resolve discrepancy before release | 2010 edition from a 2009 flight. Inspect classification codes and check campus additions against newer imagery |
| [Comune linear technical map](https://dati.trentino.it/dataset/carta-tecnica-linee-open-data/resource/aecf8436-868d-4c78-b0e8-5f0fdb8e81ad) | Candidate walls, road edges, and other linear features | SHP resource says CC BY 4.0 | Same older survey; classify and inspect locally |
| [Provincial CTP 2025](https://www.provincia.tn.it/News/Approfondimenti/Carta-Tecnica-Provinciale-CTP) | 1:10,000 tiles with vector ZIP, georeferenced TIFF and PDF; roads, buildings, paths, vegetation | [RNDT metadata](https://geodati.gov.it/geoportale/visualizzazione-metadati/scheda-metadati?metadataid=p_TN:4c97af5d-d4c7-4cca-8b33-5851ea84955f) states CC BY 4.0 | Approved February 2026, but feature dates vary; lower nominal scale than municipal mapping |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Supplementary paths, stairs, roads, building tags | ODbL 1.0; attribution and database obligations apply | Local completeness and height coverage unverified. Preserve source separation and review derived-database obligations |

DTM and DBM metadata describe ETRF2000, epoch 2008.0, within ETRS89, with orthometric elevations using ITALGEO 2005. Keep the exact horizontal and vertical references supplied with each file. Do not relabel a dataset to make it align; reproject correctly. The [official tile-index evidence](../data/reference/metadata/pat_dtm_horizontal_crs_evidence.json) corroborates EPSG:25832 for the exact Povo DTM tile. Use it as the common horizontal working CRS while retaining the more specific source reference-frame lineage. No vertical datum conversion is applied.

## Acquired and checked

- Two 500 × 500 m DTM tiles (Povo and Mesiano), each 1000 × 1000 cells at 0.5 m spacing, fully parsed with no NoData cells. Original files, metadata and checksums are in [terrain provenance](../data/raw/terrain/provenance.json).
- Matching Povo DBM tile with the same grid dimensions and origin, also parsed with no NoData. See [DBM provenance](../data/raw/terrain/povo_dbm_provenance.json).
- Two 1000 × 1000 pixel aerial references at 0.5 m output spacing. The original source imagery is finer. Visual inspection confirms the Povo crop includes the main Polo Ferrari buildings. The Mesiano crop covers its western approach with much of the campus beyond the eastern edge; expand it if that map proceeds.
- Exact [municipal imagery metadata](../data/reference/metadata/trento_ortho2024_layer_metadata.json) preserves the CC0 declaration, flight dates and source pixel spacing from the [official configuration endpoint](https://gis.comune.trento.it/api/config/2/qdjango/42).
- Povo's DBM roof patterns and aerial roof positions were compared visually and agree at blockout scale. This does not establish survey-grade facade positions, building heights, or accurate interiors.

The Povo massing configuration uses manually approximated rectangular roof envelopes and representative DBM roof elevations. Ground-level footprints, doors, overhangs, terraces and true internal floor levels remain to be reconstructed. Buildings are divided into modules to preserve visible courtyard gaps; the connector slab's thickness is an explicit assumption.

## Municipal services actually queried

[Municipal cartography guide](https://www.comune.trento.it/Vivere-il-Comune/Guide/Cartografia) documents the OGC endpoint `https://gis.comune.trento.it/ogc`.

Live GetCapabilities checks on 22 October 2026 established:

- WMS 1.3.0 publishes **`ortofoto_2024`**. Use the live name, including the underscore; some descriptive documentation uses a different spelling.
- This imagery supports EPSG:25832 and CRS:84. The EPSG:25832 layer extent is E655950–670050, N5092950–5114050.
- WFS 1.1.0 exposes **`civici`** (addresses) and **`grafo`** (road graph). It does not advertise building polygons.
- The WFS default CRS is EPSG:25832, but the sampled default GeoJSON output used longitude/latitude. Use explicit GML CRS requests or inspect output coordinates; never assume the default service CRS applies to every output format.
- `civici` records for the university addresses were queried to locate the reference crops. The service advertises no access constraints; that alone does not establish an asset-redistribution licence for the address/road database.

The imagery downloader stores a PNG, world file, and JSON provenance for each reference crop. The crop is a **500 × 500 m reconnaissance area**, not an agreed playable boundary. In QGIS, load the PNG with its adjacent `.pgw` and assign EPSG:25832 if not detected. The manifest records the extent and pixel spacing independently.

Municipal polygon download (entire collection; no bbox parameter verified):

```text
https://gis.comune.trento.it/dbexport?db=base&sc=carta_tecnica&ly=territorio_polygon&fr=geojson
```

Do not start by importing an entire city dataset into the game editor. Clip the selected area and a modest visual buffer first.

## Reference and 3D leads

- [UniTN addresses](https://www.unitn.it/it/contatti-e-orari): Povo 1, Via Sommarive 5; Povo 2, Via Sommarive 9; Mesiano, Via Mesiano 77.
- [UniTN Povo space maps](https://www.dicam.unitn.it/17/mappa-spazi-polo-ferrari): potential interior reference; no reuse licence established. Public visibility is not a modelling licence.
- [Mesiano park reconstruction research](https://iris.unitn.it/handle/11572/390292): evidence of a local reconstruction project, but no usable downloadable asset licence verified.
- [Piazza Duomo research dataset](https://doi.org/10.5281/zenodo.18493751): a future city-centre lead. The [university catalogue](https://research.aalto.fi/en/datasets/public-works-in-nineteenth-century-trento-a-fair-dataset-of-urban/) lists CC BY 4.0 point-cloud GLBs and surveyed drawings. Files have not been inspected and are not game-ready assets.
- [FBK NeRFBK](https://github.com/3DOM-FBK/NeRFBK/blob/master/README.md): Duomo photography and reconstruction data, CC BY-NC-SA 4.0. Keep outside the core asset pipeline until those restrictions are compatible with intended distribution.

The user-reviewed photographic set in `data/reference/povo_photos/` now includes
facades, courtyard/stairwell/library views, and the connecting bridge inside and
out. Its manifest preserves individual sources, author credits, licences, hashes,
and user filename corrections. P016/P017 are user-supplied plan images with
upstream source/licence not specified.

The user also supplied the [mappe-povo repository](https://github.com/agusmeroli/mappe-povo).
Two PDFs and two floor-plan PNGs are retained under
`data/reference/povo_plans/mappe-povo/` with provenance. The README calls these
unofficial maps and cites an earlier classroom-map source. No licence file was
listed in the inspected tree. They establish useful room groups, stair positions
and route relationships, but not surveyed dimensions or absolute floor heights.
See [the architecture/plan review](POVO_ARCHITECTURE.md) for the provisional fit
to the campus footprint and the distinct academic/lift/stair floor labels.

No source currently establishes complete, measured campus interiors. Use selected documented rooms only, and label assumptions.

## Google Maps and Street View

Google's published terms restrict extracting content and creating geometry/data from it. The [EEA Maps Platform terms](https://cloud.google.com/terms/maps-platform/eea) address scraping and derived content; the [Geo Guidelines](https://about.google/brand-resource-center/products-and-services/geo-guidelines/) explicitly address Earth reconstruction and tracing data from Street View. An API subscription is not permission to export those assets into a CS2 package. This project therefore uses independently reusable geographic sources and original/licensed photographs for geometry and textures.

## Per-asset record

For each acquired dataset retain: provider and original URL, acquisition time, survey date, licence URL/text, attribution, file checksum, horizontal CRS, vertical datum, source resolution, clip extent, transformations, and measured/assumed status. Preserve the original separately from edited game assets. Record unresolved rights before distributing derived content.
