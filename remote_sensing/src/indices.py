"""Stage 3 — Index computation.

Every function takes a harmonized optical image (bands: blue, green, red,
nir, swir1, swir2) and returns a single-band index image, so the same code
runs on a Landsat or a Sentinel-2 composite. Coefficients for SI/VSSI/CRSI
follow Douaoui (2006), Allbed & Kumar (2013), and Deng et al. (2015) —
recalibrate against field EC samples before treating outputs as absolute.
"""
import ee


def ndvi(img: ee.Image) -> ee.Image:
    return img.normalizedDifference(["nir", "red"]).rename("NDVI")


def savi(img: ee.Image, l: float = 0.5) -> ee.Image:
    return (
        img.expression(
            "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
            {"NIR": img.select("nir"), "RED": img.select("red"), "L": l},
        ).rename("SAVI")
    )


def ndwi(img: ee.Image) -> ee.Image:
    return img.normalizedDifference(["green", "nir"]).rename("NDWI")


def mndwi(img: ee.Image) -> ee.Image:
    return img.normalizedDifference(["green", "swir1"]).rename("MNDWI")


def si1(img: ee.Image) -> ee.Image:
    return img.expression(
        "sqrt(GREEN * RED)", {"GREEN": img.select("green"), "RED": img.select("red")}
    ).rename("SI1")


def si2(img: ee.Image) -> ee.Image:
    return img.expression(
        "sqrt(GREEN**2 + RED**2 + NIR**2)",
        {"GREEN": img.select("green"), "RED": img.select("red"), "NIR": img.select("nir")},
    ).rename("SI2")


def si3(img: ee.Image) -> ee.Image:
    return img.expression(
        "sqrt(GREEN**2 * RED**2)", {"GREEN": img.select("green"), "RED": img.select("red")}
    ).rename("SI3")


def si_t(img: ee.Image) -> ee.Image:
    return img.select("red").divide(img.select("nir")).rename("SI_T")


def brightness_index(img: ee.Image) -> ee.Image:
    return img.expression(
        "sqrt(RED**2 + NIR**2)", {"RED": img.select("red"), "NIR": img.select("nir")}
    ).rename("BI")


def ndsi(img: ee.Image) -> ee.Image:
    return img.normalizedDifference(["red", "nir"]).rename("NDSI")


def vssi(img: ee.Image) -> ee.Image:
    return img.expression(
        "2 * GREEN - 5 * (RED + NIR)",
        {"GREEN": img.select("green"), "RED": img.select("red"), "NIR": img.select("nir")},
    ).rename("VSSI")


def crsi(img: ee.Image) -> ee.Image:
    return img.expression(
        "sqrt(((NIR * RED) - (GREEN * BLUE)) / ((NIR * RED) + (GREEN * BLUE)))",
        {
            "NIR": img.select("nir"),
            "RED": img.select("red"),
            "GREEN": img.select("green"),
            "BLUE": img.select("blue"),
        },
    ).rename("CRSI")


def sar_ratio(s1_img: ee.Image) -> ee.Image:
    """VH/VV backscatter ratio — bare/stressed soil vs. dense canopy."""
    return s1_img.select("VH").divide(s1_img.select("VV")).rename("VH_VV")


def sar_delta_vv(baseline_s1: ee.Image, event_s1: ee.Image) -> ee.Image:
    """Event-window VV change — storm-surge / flood inundation footprint."""
    return event_s1.select("VV").subtract(baseline_s1.select("VV")).rename("dVV")


ALL_OPTICAL_INDICES = [ndvi, savi, ndwi, mndwi, si1, si2, si3, si_t, brightness_index, ndsi, vssi, crsi]


def optical_index_stack(img: ee.Image) -> ee.Image:
    """Every optical index in ALL_OPTICAL_INDICES, stacked into one image."""
    bands = [fn(img) for fn in ALL_OPTICAL_INDICES]
    stack = bands[0]
    for band in bands[1:]:
        stack = stack.addBands(band)
    return stack


def feature_stack(
    optical_img: ee.Image,
    s1_img: ee.Image,
    dem_img: ee.Image,
    lst_img: ee.Image,
    precip_img: ee.Image,
) -> ee.Image:
    """The full per-pixel feature stack handed to the classifier in stage 5:
    optical bands + all indices + SAR ratio + elevation + LST + antecedent
    precipitation. Distance-to-shoreline is intentionally left to be joined
    in from your own coastline vector, since it depends on the AOI source.
    """
    return (
        optical_img
        .addBands(optical_index_stack(optical_img))
        .addBands(sar_ratio(s1_img))
        .addBands(dem_img.rename("elevation"))
        .addBands(lst_img.rename("LST"))
        .addBands(precip_img.rename("precip_total"))
    )
