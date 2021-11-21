from pyOER import Measurement

measurement = Measurement.open(125)

ax = measurement.plot()
ax[0].legend()

measurement.print_notes()
