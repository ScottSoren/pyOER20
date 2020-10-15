from pyOER.extraction import StandardExperiment

e1 = StandardExperiment(m_id=217, tspan_bg=[350, 400])

ax = e1.plot_EC_MS_ICPMS(ylims={1: [0.8, 1.6]})
