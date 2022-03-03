import json
import numpy as np
from matplotlib import pyplot as plt
from ixdat.constants import FARADAY_CONSTANT, STANDARD_PRESSURE, STANDARD_TEMPERATURE, R
from pyOER.constants import STANDARD_SITE_DENSITY, STANDARD_SPECIFIC_CAPACITANCE
from paper_I_v6_fig3 import plot_all_activity_results
from paper_I_v6_fig5 import get_model_j_norm

if True:  # equilibrium shift calculation.

    p0 = STANDARD_PRESSURE  # standard pressure of 1 bar / [Pa]
    K_H = 76923  # O2 henry's-law constant / [Pa/(mol/m^3)]
    c_sat = p0 / K_H
    print(f"concentration at surfaces in eq with 1 bar O2: {c_sat} mM")

    D = 2.1e-5  # O2 diffusion constant in water / [m^2/s]
    L = 100e-6   # working distance / [m]
    A_el = 0.196e-4  # Area of electrode / [m^2]
    n_dot_lim = 2e-13  # limiting O2 flux of 0.2 pmol/s / [mol/s]
    c_lim = n_dot_lim / A_el * L / D
    print(f"concentration at surface with {n_dot_lim} mol/s O2 generation: {c_lim} mM")

    act_lim = c_lim / c_sat
    print(f"O2 activity at surface with {n_dot_lim} mol/s O2 generation: {act_lim}")

    E0 = 1.23   # Standard potential (saturated O2) in V vs RHE
    E0_lim = E0 + R * STANDARD_TEMPERATURE / (4 * FARADAY_CONSTANT) * np.log(act_lim)
    print(f"equilibrium potential with {n_dot_lim} mol/s O2 gen.: {E0_lim} V vs RHE")

with open("fit_results.json", "r") as f:
    fit_results = json.load(f)

eta_max = 0.275
u = np.linspace(E0 - eta_max, E0 + eta_max, 500)
tof_to_j_norm = STANDARD_SITE_DENSITY * (4 * FARADAY_CONSTANT) / STANDARD_SPECIFIC_CAPACITANCE

j_norm_OER = get_model_j_norm(G1=fit_results["G1"], G2=fit_results["G2"], j_norm_0=fit_results["j_norm_0"], u=u)
j_norm_ORR = - get_model_j_norm(G1=fit_results["G1"], G2=fit_results["G2"], j_norm_0=fit_results["j_norm_0"], u=2 * E0 - u)

j_total = j_norm_OER + j_norm_ORR

fig_lin, ax_lin = plt.subplots()

ax_lin.plot(u, j_norm_OER, "g")
ax_lin.plot(u, j_norm_ORR, "r--")
ax_lin.plot(u, j_total, "k:")
ax_lin.plot([E0, E0], [min(j_total), max(j_total)], "0.5")

plot_all_activity_results(ax=ax_lin, result="tof", factor=tof_to_j_norm)

ax_lin_tof = ax_lin.twinx()
ax_lin_tof.set_ylim([lim / tof_to_j_norm for lim in ax_lin.get_ylim()])

ax_lin.set_xlabel("E vs RHE (V)")
ax_lin.set_ylabel("j$_{norm}$ / (A F$^{-1}$)")
ax_lin_tof.set_ylabel("TOF / (s$^{-1}$)")
fig_lin.savefig("SI_paper_I_v6_figSX_lin.svg")

fig_log, ax_log = plt.subplots()
ax_log.set_yscale("log")

ax_log.plot(u, j_norm_OER, "g")
ax_log.plot(u, - j_norm_ORR, "r--")
j_total_abs = np.abs(j_total)

mask = j_total_abs > 1e-18
ax_log.plot(u[mask], j_total_abs[mask], "k:")
ax_log.plot([E0, E0], [min(j_total_abs[mask]), max(j_total_abs[mask])], "0.5")

plot_all_activity_results(ax=ax_log, result="tof", factor=tof_to_j_norm)

ax_log_tof = ax_log.twinx()
ax_log_tof.set_yscale("log")
ax_log_tof.set_ylim([lim / tof_to_j_norm for lim in ax_log.get_ylim()])

ax_log.set_xlabel("E vs RHE (V)")
ax_log.set_ylabel("abs(j$_{norm})$ / (A F$^{-1}$)")
ax_log_tof.set_ylabel("abs(TOF) / (s$^{-1}$)")
fig_log.savefig("SI_paper_I_v6_figSX_log.svg")

ax_log.set_xlim([E0 - eta_max / 15, E0 + eta_max / 15])
ax_log.set_ylim([1e-10, 1e-7])
fig_log.set_figwidth(fig_log.get_figwidth()/3)
fig_log.set_figheight(fig_log.get_figheight()/3)
ax_log.set_xlabel("")
ax_log.set_ylabel("")
fig_log.savefig("SI_paper_I_v6_figSX_log_inset.svg")