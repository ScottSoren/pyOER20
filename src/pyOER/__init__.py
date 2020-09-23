__version__ = "0.0.1"

# Module utilizes internal functions only available from V3.6+
import sys

major, minor = sys.version_info.major, sys.version_info.minor
if major < 3 or (major > 2 and minor < 6):
    raise SystemError(
        "This module requires python3.6 or newer. You are using {}.{}".format(
            major, minor
        )
    )
else:
    print("Python version check: ok")

# Use old formatting syntax to prevent a SyntaxError from running above version check
print("importing pyOER v{} from {}".format(__version__, __file__))

from .measurement import Measurement, MeasurementCounter, all_measurements
from .calibration import Calibration, CalibrationCounter, all_calibrations
from .icpms import (
    ICPMSPoint,
    ICPMSCalibration,
    ICPMSCounter,
    ICPMSCalCounter,
    all_icpms_points,
)
from .iss import ISS
