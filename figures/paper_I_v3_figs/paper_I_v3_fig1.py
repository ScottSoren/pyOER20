from matplotlib import pyplot as plt
import numpy as np

from pyOER import Measurement
from EC_MS import CyclicVoltammagram, Chem


plt.close("all")

T = 298.15
A_el = 0.196

measurement = Measurement.open(10)

dataset = measurement.dataset

dataset.plot_experiment()

V_str, J_str = dataset.sync_metadata(RE_vs_RHE=0.715, A_el=0.196)

O2 = dataset.point_calibration(mol="O2", mass="M32", tspan=[300, 350], n_el=4)

cv = CyclicVoltammagram(dataset=dataset, tspan=[6370, 6700], t_zero="start")

ax = cv.plot_experiment(
    mols=[O2],
    logplot=False,
    t_bg=[0, 20],
    # J_str="cycle"
)
ax[0].get_figure().savefig("Reshma1A cv vs time.png")
ax[0].get_figure().savefig("Reshma1A cv vs time.svg")


cv1 = cv.cut(tspan=[86, 172])

v, j = cv1[V_str], cv1[J_str]

fig, ax = plt.subplots()
ax.plot(v, j, "b")

x, y = cv1.get_flux(O2, unit="mol/s", t_bg=[90, 100])
n_dot_O2 = np.trapz(y, x)  # in mol

Q_O2 = n_dot_O2 * 4 * Chem.Far  # in C
q_O2 = Q_O2 * 1e3 / A_el  # in mC/cm^2

V_times_J_O2 = 20e-3 * q_O2 / 2  # in V/s * mC/cm^2 = V * mA/cm^2

v_max = max(v)

nernst = Chem.R * T / Chem.Far  # 26 mV per factor e  (60 mV per decade)

v_O2_model = np.linspace(1.23, v_max, 100)
j_O2_model = V_times_J_O2 / nernst * np.exp((v_O2_model - v_max) / nernst)
zero_O2_model = np.zeros(v_O2_model.shape)

ax.fill_between(v_O2_model, j_O2_model, zero_O2_model, color="k", alpha=0.5)
ax.set_xlabel(V_str)
ax.set_ylabel(J_str)
ax.get_figure().savefig("Reshma1A cv with J_O2.png")
ax.get_figure().savefig("Reshma1A cv with J_O2.svg")
