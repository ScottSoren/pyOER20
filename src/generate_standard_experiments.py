from pathlib import Path
import json

from pyOER.standard_experiments import StandardExperiment

DESCRIPTIONS_DIR = Path(__file__).parent.parent / "descriptions"

standard_measurements_file = DESCRIPTIONS_DIR / "systematic_measurements.json"

with open(standard_measurements_file, "r") as f:
    standard_measurements = json.load(f)

systematic_mids = list(
    [
        key
        for key, value in standard_measurements.items()
        if value in ["y", "s", "k", "c",]
    ]
)
# y: yes, fully systematic; s: starts systematic; k: short; c: composite

specs = {
    148: dict(tspan_bg=[-20, -10], tspan_plot=[-50, 1300]),
    149: dict(tspan_bg=[-20, -10], tspan_plot=[-50, 1300]),
    150: dict(tspan_bg=[-30, 0], tspan_plot=[-50, 2000]),
    155: dict(tspan_bg=[-10, 0], tspan_plot=[-50, 1300], fix_U=True),
    157: dict(tspan_bg=[-10, 0], tspan_plot=[-50, 1300], fix_U=True),
    159: dict(tspan_bg=[-10, 0], tspan_plot=[-30, 800]),
    160: dict(tspan_plot=[-30, 1600]),
    161: dict(tspan_plot=[-50, 2110]),
    163: dict(tspan_plot=[-50, 1300], plot_specs={"ylims": {0: [-0.2, 2]}}),
    165: dict(tspan_plot=[-50, 2000], plot_specs={"ylims": {0: [-0.2, 2]}}),
    171: dict(
        tspan_plot=[-50, 1650], plot_specs={"ylims": {0: [-0.2, 2]}, 1: [1.1, 1.8]}
    ),
    175: dict(tspan_plot=[0, 600]),
    217: dict(tspan_bg=[350, 400], plot_specs={"ylims": {1: [0.8, 1.6]}}),
}

# for m_id, spec in specs.items():
for m_id in systematic_mids:
    m_id = int(m_id)
    if m_id > 175:
        break
    spec = specs.get(m_id, {"tspan_bg": [0, 10]})

    se = StandardExperiment(
        m_id=m_id,
        # se_id = StandardExperimentCounter.id
        **spec
    )
    ax = se.plot_EC_MS_ICPMS()
    ax[1].set_title(str(se.measurement))

    # se.save()
