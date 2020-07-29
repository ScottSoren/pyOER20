from pyOER import Measurement

measurement = Measurement.open(125)

measurement.plot_experiment()

measurement.print_notes()
