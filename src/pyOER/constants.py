from pathlib import Path

# -------------- natural constants -------------- #
STANDARD_ALPHA = 0.9980  # the natural ratio ^{16}O/(^{16}O + ^{18}O) of oxygen atoms


# -------------- project-specific constants -------------- #
PROJECT_START_TIMESTAMP = 1533502800  # August 25, 2018 in unix time


# -------------- table stuff (directories and counter files) -------------- #
PROJECT_DIR = Path(__file__).absolute().parent.parent.parent

ELOG_DIR = PROJECT_DIR / "tables/elog"

SAMPLE_DIR = PROJECT_DIR / "tables/samples"

MEASUREMENT_DIR = PROJECT_DIR / "tables/measurements"
MEASUREMENT_ID_FILE = MEASUREMENT_DIR / "LAST_MEASUREMENT_ID.pyoer20"

CALIBRATION_DIR = PROJECT_DIR / "tables/calibrations"
CALIBRATION_ID_FILE = CALIBRATION_DIR / "LAST_CALIBRATION_ID.pyoer20"

ICPMS_DIR = PROJECT_DIR / "tables/icpms"
ICPMS_ID_FILE = ICPMS_DIR / "LAST_ICPMS_ID.pyoer20"
ICPMS_CALIBRATION_ID_FILE = ICPMS_DIR / "LAST_ICPMS_CALIBRATION_ID.pyoer20"

EXPERIMENT_DIR = PROJECT_DIR / "tables/experiments"
EXPERIMENT_ID_FILE = (
        EXPERIMENT_DIR / "LAST_EXPERIMENT_ID.pyOER20"
)
