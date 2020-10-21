from pathlib import Path
import json

from pyOER.experiment import StandardExperiment

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
    99: dict(tspan_plot=[-50, 360]),
    102: dict(tspan_plot=[-50, 360]),
    103: dict(tspan_plot=[-50, 360]),
    104: dict(tspan_plot=[-50, 360]),
    148: dict(
        tspan_bg=[-20, -10],
        tspan_plot=[-50, 1350],
        plot_specs={"ylims": {0: [-0.2, 2]}},
    ),
    149: dict(
        tspan_bg=[-20, -10],
        tspan_plot=[-50, 2000],
        plot_specs={"ylims": {0: [-0.2, 2]}},
    ),
    150: dict(
        tspan_bg=[-30, 0], tspan_plot=[-50, 3800], plot_specs={"ylims": {0: [-0.2, 2]}}
    ),
    155: dict(
        tspan_bg=[-10, 0],
        tspan_plot=[-50, 1300],
        plot_specs={"ylims": {0: [-0.2, 2]}},
        fix_U=True,
    ),
    157: dict(tspan_bg=[-10, 0], tspan_plot=[-50, 1300], fix_U=True),
    159: dict(tspan_bg=[-10, 0], tspan_plot=[-30, 800]),
    160: dict(tspan_plot=[-30, 1600]),
    161: dict(tspan_plot=[-50, 2110]),
    163: dict(tspan_plot=[-50, 2050], plot_specs={"ylims": {0: [-0.2, 2]}}),
    165: dict(tspan_plot=[-50, 2000], plot_specs={"ylims": {0: [-0.2, 2]}}),
    171: dict(
        tspan_plot=[-50, 1650], plot_specs={"ylims": {0: [-0.2, 2], 1: [1.1, 1.8]}}
    ),
    175: dict(tspan_plot=[0, 600]),
    180: dict(tspan_plot=[0, 400]),
    182: dict(plot_specs={"ylims": {0: [-0.2, 2], 1: [0.9, 1.6]}}),
    184: dict(
        tspan_plot=[0, 2010], plot_specs={"ylims": {0: [-0.2, 2], 1: [0.6, 1.6]}}
    ),
    185: dict(tspan_bg=[250, 300], fix_U=True),
    187: dict(tspan_bg=[500, 550], plot_specs={"ylims": {0: [-0.2, 2]}}),
    192: dict(plot_specs={"ylims": {0: [-0.2, 2], 1: [0.6, 1.6]}}),
    193: dict(plot_specs={"ylims": {0: [-0.06, 0.6],}}),
    196: dict(
        tspan_bg=[150, 175], tspan_plot=[0, 5800], plot_specs={"ylims": {0: [-0.2, 2],}}
    ),
    # ^ missing ICPMS, should have it!
    197: dict(plot_specs={"ylims": {0: [-0.1, 1], 1: [0.6, 1.6]}}),
    198: dict(plot_specs={"ylims": {0: [-0.3, 3], 1: [0.5, 1.6]}}),
    203: dict(plot_specs={"ylims": {0: [-0.3, 3]}}),
    204: dict(plot_specs={"ylims": {0: [-0.3, 3]}}),
    205: dict(tspan_bg=[275, 300], plot_specs={"ylims": {0: [-0.2, 2]}}),
    209: dict(plot_specs={"ylims": {0: [-0.3, 3]}}),
    217: dict(tspan_bg=[350, 400], plot_specs={"ylims": {1: [0.8, 1.6]}}),
    222: dict(plot_specs={"ylims": {0: [-0.2, 2]}}),  # looks failed
    223: dict(
        tspan_bg=[350, 400], plot_specs={"ylims": {0: [-0.02, 0.2]}}
    ),  # looks failed
    224: dict(tspan_bg=[300, 350], plot_specs={"ylims": {0: [-0.2, 2]}}),
    231: dict(plot_specs={"ylims": {0: [-0.2, 2], 1: [0.7, 1.7]}}),
    232: dict(plot_specs={"ylims": {0: [-0.2, 2],}}),
    233: dict(
        tspan_plot=[0, 2350], plot_specs={"ylims": {0: [-0.2, 2], 1: [0.7, 1.7]}}
    ),
    234: dict(plot_specs={"ylims": {0: [-0.2, 2],}}),
    235: dict(plot_specs={"ylims": {0: [-0.06, 0.6],}}),
    236: dict(tspan_bg=[310, 340], plot_specs={"ylims": {0: [-0.02, 0.2]}}),
}

working_range = [0, 250]
if False:  # go through and save them all
    for m_id_str in systematic_mids:
        m_id = int(m_id_str)
        if m_id < working_range[0]:
            continue
        elif m_id > working_range[-1]:
            break
        spec = specs.get(m_id, {})
        if "tspan_bg" not in spec:
            spec["tspan_bg"] = [0, 10]

        se = StandardExperiment(
            m_id=m_id,
            experiment_type=standard_measurements[m_id_str],
            # se_id = StandardExperimentCounter.id
            **spec
        )

        if False:  # plot them all!
            ax = se.plot_EC_MS_ICPMS()
            ax[1].set_title(str(se.measurement))

        se.save()


if False:  # change prefix 'se' to 'e'
    from pyOER.constants import EXPERIMENT_DIR
    for file in EXPERIMENT_DIR.iterdir():
        if not file.suffix == ".json":
            continue
        with open(file, "r") as f:
            e_as_dict = json.load(f)
        e_as_dict["e_id"] = e_as_dict.pop("se_id")
        e = StandardExperiment(**e_as_dict)
        e.save()
        file.unlink()
