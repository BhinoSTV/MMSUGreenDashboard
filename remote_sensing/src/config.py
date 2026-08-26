"""Study-area, time-window, and sensor parameters for the coastal Ilocos Norte
salinity assessment. Edit this file to change the AOI or seasons — nothing
else in the pipeline should need touching for that.
"""

# --- Study area -------------------------------------------------------------
# Coastal municipalities of Ilocos Norte (verify against PSGC/NAMRIA before
# publication; Vintar and San Nicolas are inland and deliberately excluded).
COASTAL_MUNICIPALITIES = [
    "Dumalneg",
    "Bangui",
    "Pagudpud",
    "Burgos",
    "Pasuquin",
    "Bacarra",
    "Laoag City",
    "Paoay",
    "Currimao",
    "Badoc",
]
ADM1_NAME = "Ilocos Norte"

# Inland buffer distance from the coastline used to scope the AOI, in meters.
COASTAL_BUFFER_M = 5000

# --- Grid / projection --------------------------------------------------
OUTPUT_CRS = "EPSG:32651"  # UTM Zone 51N
OUTPUT_SCALE_M = 10

# --- Temporal domain ------------------------------------------------------
BASELINE_YEAR = 1990          # earliest usable Landsat 5 epoch
CURRENT_YEAR = 2025

# Seasonal composite windows (month-day), tied to the salinity signal, not
# the calendar year.
DRY_SEASON = ("02-01", "04-30")   # peak evapotranspiration / salinity signal
WET_SEASON = ("07-01", "09-30")   # leaching / dilution signal

# --- Cloud / quality filters ---------------------------------------------
MAX_CLOUD_COVER_LANDSAT = 20     # percent
MAX_CLOUD_COVER_S2 = 20          # percent
S2_CLOUD_PROB_THRESHOLD = 40     # s2cloudless probability cutoff

# --- Earth Engine collection IDs ------------------------------------------
COLLECTIONS = {
    "l5": "LANDSAT/LT05/C02/T1_L2",
    "l8": "LANDSAT/LC08/C02/T1_L2",
    "l9": "LANDSAT/LC09/C02/T1_L2",
    "s2_sr": "COPERNICUS/S2_SR_HARMONIZED",
    "s2_clouds": "COPERNICUS/S2_CLOUD_PROBABILITY",
    "s1_grd": "COPERNICUS/S1_GRD",
    "modis_ndvi": "MODIS/061/MOD13Q1",
    "modis_lst": "MODIS/061/MOD11A2",
    "dem": "COPERNICUS/DEM/GLO30",
    "chirps": "UCSB-CHG/CHIRPS/DAILY",
    "admin2": "FAO/GAUL/2015/level2",
}

# --- Band correspondence (role -> band name per sensor) --------------------
BANDS_L8 = {"blue": "SR_B2", "green": "SR_B3", "red": "SR_B4",
            "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7",
            "thermal": "ST_B10"}
BANDS_L5 = {"blue": "SR_B1", "green": "SR_B2", "red": "SR_B3",
            "nir": "SR_B4", "swir1": "SR_B5", "swir2": "SR_B7"}
BANDS_S2 = {"blue": "B2", "green": "B3", "red": "B4", "nir": "B8",
            "swir1": "B11", "swir2": "B12"}
