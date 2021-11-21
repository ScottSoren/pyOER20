from pyOER import all_measurements

ms = [m for m in all_measurements() if m.sample_name and "Evans" in m.sample_name]

good_ones = [1, 9, 10, 16, 25, 27, 28, 31, 32, 33, 34]

for i in good_ones:
    m = ms[i - 1]
    m.meas.sync_metadata(RE_vs_RHE=m.RE_vs_RHE, A_el=0.196)
    axes = m.plot(tspan="all", masses=["M32", "M34", "M36"], unit="pmol/s/cm^2")
    axes[2].set_ylabel("J / (mA cm$^{-2}_{geo}$)")
    axes[1].set_title(str(m))
    fig = axes[0].get_figure()
    fig.savefig(str(m))
