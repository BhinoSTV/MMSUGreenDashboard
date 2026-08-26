"""Stage 2 — Remote sensing data acquisition.

Builds the AOI and returns cloud-masked / speckle-filtered seasonal
composites from each sensor, all harmonized to a common set of role-named
bands (blue, green, red, nir, swir1, swir2[, thermal]) so `indices.py` can
run the same formulas regardless of source sensor.
"""
import ee

import config


def build_aoi() -> ee.FeatureCollection:
    """Coastal-municipality boundaries, buffered inland, as the study AOI."""
    admin2 = ee.FeatureCollection(config.COLLECTIONS["admin2"])
    coastal = admin2.filter(
        ee.Filter.And(
            ee.Filter.eq("ADM1_NAME", config.ADM1_NAME),
            ee.Filter.inList("ADM2_NAME", config.COASTAL_MUNICIPALITIES),
        )
    )

    def buffer_feature(feature):
        return feature.buffer(config.COASTAL_BUFFER_M)

    return coastal.map(buffer_feature)


def _rename(image: ee.Image, band_map: dict) -> ee.Image:
    src = list(band_map.values())
    dst = list(band_map.keys())
    return image.select(src, dst)


def _mask_landsat_clouds(image: ee.Image) -> ee.Image:
    qa = image.select("QA_PIXEL")
    cloud_bit, shadow_bit = 3, 4
    mask = (
        qa.bitwiseAnd(1 << cloud_bit).eq(0)
        .And(qa.bitwiseAnd(1 << shadow_bit).eq(0))
    )
    scaled = image.select("SR_B.").multiply(0.0000275).add(-0.2)
    thermal = image.select("ST_B.*").multiply(0.00341802).add(149.0)
    return image.addBands(scaled, overwrite=True).addBands(thermal, overwrite=True).updateMask(mask)


def landsat_composite(aoi: ee.FeatureCollection, start: str, end: str) -> ee.Image:
    """Median composite across Landsat 5/8/9, whichever has coverage in
    [start, end], cloud-masked and rescaled to reflectance, band-harmonized.
    """
    def prep(collection_id, band_map):
        col = (
            ee.ImageCollection(collection_id)
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUD_COVER", config.MAX_CLOUD_COVER_LANDSAT))
            .map(_mask_landsat_clouds)
            .map(lambda img: _rename(img, band_map))
        )
        return col

    l5 = prep(config.COLLECTIONS["l5"], config.BANDS_L5)
    l8 = prep(config.COLLECTIONS["l8"], config.BANDS_L8)
    l9 = prep(config.COLLECTIONS["l9"], config.BANDS_L8)
    merged = l5.merge(l8).merge(l9)
    return merged.median().clip(aoi)


def _mask_s2_clouds(aoi, start, end):
    s2 = (
        ee.ImageCollection(config.COLLECTIONS["s2_sr"])
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", config.MAX_CLOUD_COVER_S2))
    )
    prob = (
        ee.ImageCollection(config.COLLECTIONS["s2_clouds"])
        .filterBounds(aoi)
        .filterDate(start, end)
    )
    joined = ee.Join.saveFirst("cloud_mask").apply(
        primary=s2,
        secondary=prob,
        condition=ee.Filter.equals(leftField="system:index", rightField="system:index"),
    )

    def apply_mask(feature):
        img = ee.Image(feature)
        cloud_prob = ee.Image(img.get("cloud_mask")).select("probability")
        mask = cloud_prob.lt(config.S2_CLOUD_PROB_THRESHOLD)
        return img.updateMask(mask).multiply(0.0001).copyProperties(img, img.propertyNames())

    return ee.ImageCollection(joined).map(apply_mask)


def sentinel2_composite(aoi: ee.FeatureCollection, start: str, end: str) -> ee.Image:
    """Cloud-probability-masked Sentinel-2 SR median composite, 10-20 m
    bands only, harmonized to role band names.
    """
    col = _mask_s2_clouds(aoi, start, end).map(lambda img: _rename(img, config.BANDS_S2))
    return col.median().clip(aoi)


def sentinel1_composite(aoi: ee.FeatureCollection, start: str, end: str) -> ee.Image:
    """Speckle-filtered (focal median) Sentinel-1 VV/VH median composite,
    IW mode, descending pass, for cloud-gap fill and moisture/flood proxies.
    """
    col = (
        ee.ImageCollection(config.COLLECTIONS["s1_grd"])
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )

    def despeckle(image):
        return image.focal_median(radius=50, units="meters")

    return col.map(despeckle).median().clip(aoi)


def modis_ndvi_series(aoi: ee.FeatureCollection, start: str, end: str) -> ee.ImageCollection:
    """16-day MODIS NDVI/EVI series — temporal densifier between Landsat /
    Sentinel-2 passes; scaled to standard NDVI/EVI ranges.
    """
    return (
        ee.ImageCollection(config.COLLECTIONS["modis_ndvi"])
        .filterBounds(aoi)
        .filterDate(start, end)
        .select(["NDVI", "EVI"])
        .map(lambda img: img.multiply(0.0001).copyProperties(img, ["system:time_start"]))
    )


def modis_lst_composite(aoi: ee.FeatureCollection, start: str, end: str) -> ee.Image:
    """Mean land-surface temperature (Kelvin) over the window, from the
    8-day MODIS LST product — used where Landsat thermal coverage is thin."""
    return (
        ee.ImageCollection(config.COLLECTIONS["modis_lst"])
        .filterBounds(aoi)
        .filterDate(start, end)
        .select("LST_Day_1km")
        .mean()
        .multiply(0.02)
        .clip(aoi)
    )


def dem(aoi: ee.FeatureCollection) -> ee.Image:
    return ee.ImageCollection(config.COLLECTIONS["dem"]).select("DEM").mosaic().clip(aoi)


def chirps_total(aoi: ee.FeatureCollection, start: str, end: str) -> ee.Image:
    """Antecedent-rainfall covariate: summed daily precipitation."""
    return (
        ee.ImageCollection(config.COLLECTIONS["chirps"])
        .filterBounds(aoi)
        .filterDate(start, end)
        .select("precipitation")
        .sum()
        .clip(aoi)
    )
