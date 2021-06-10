"""This module plots stuff from 21F10 in Spectro Inlets notebook."""

import numpy as np
from matplotlib import pyplot as plt

from ixdat.constants import FARADAY_CONSTANT as F, STANDARD_TEMPERATURE as T0, R
from ixdat.plotters.base_mpl_plotter import MPLPlotter
from paper_I_v3_fig4 import plot_all_activity_results


n_points = 100

u = np.linspace(1.23, 1.6, n_points)  # vector describing potential vs RHE in [V]
U0 = 1.23  # sort of arbitrary reference potential vs RHE in [V]

alpha_rds = 0.5  # symmetry factor for the rate-determining step

# if there was constant coverage of the RDS state,
#   the current relative to j0 would simply be:
j_over_j0_simple = np.exp(alpha_rds * F * (u - U0) / (R * T0))

# if there were two sites with different symmetry factors, we might get something like:
j_over_j0_early_site = 0.99 * np.exp(0.1 * F * (u - U0) / (R * T0))
j_over_j0_late_site = 0.01 * np.exp(0.9 * F * (u - U0) / (R * T0))
j_over_j0_2_simple = j_over_j0_early_site + j_over_j0_late_site

# ---------- state definitions --------------- #
class State:
    def __init__(self, n_to_rds, eV_1p23_vs_rds, color):
        """Nice little class to represent a surface state

        States are described relative to the RDS state, which is the state from which
        the rate-limiting step of OER takes place.
        States are described with reference to a standard potential U0 = 1.23 V_RHE

        Args:
            n_to_rds (int): ox. state of RDS intermediate relative to self
            eV_1p23_vs_rds (float): energy relative to RDS at U0 / [eV]
            color (str): default color for plotting
        """
        self.n_to_rds = n_to_rds
        self.eV_1p23_vs_rds = eV_1p23_vs_rds
        self.color = color

    @property
    def G_1p23_vs_rds(self):
        """Energy relative to RDS at U0 / [J/mol]"""
        return self.eV_1p23_vs_rds * F

    @property
    def K_rds(self):
        """equilibrium constant = theta_i / theta_j"""
        return np.exp(self.G_1p23_vs_rds / (R * T0))


states = (
    State(0, 0, "k"),  # the RDS state
    State(1, -0.2, "b"),  # the state one electron transfer behind the RDS state
    State(2, -0.35, "g"),  # the state two electron transfers behind the RDS state
)

# ---- and lets do some math! :D

# This matrix is the coverage of each state (outer dimension) relative to the RDS state
#   as a function of potential (outer dimension):
theta_over_theta_i = np.array(
    [
        1 / state.K_rds * np.exp(-state.n_to_rds * F * (u - U0) / (R * T0))
        for state in states
    ]
)
# ... and this matrix is the coverage of each individual state:
thetas = theta_over_theta_i / np.sum(theta_over_theta_i, axis=0)

# The coverage of the RDS state is the first of these thetas:
theta_i = thetas[0]

# From here it is easy to calculate the current relative to j0 of the RDS
j_over_j0 = theta_i * np.exp(alpha_rds * F * (u - U0) / (R * T0))

# ...and also the average number of electron transfers to get to the RDS:
n_to_rds_vec = np.sum(
    [thetas[j] * state.n_to_rds for j, state in enumerate(states)], axis=0
)


if False:  # get activity results for fitting
    u_exp, tof_exp = plot_all_activity_results(ax=None, result="tof", takelog=False)
    np.save("u_exp", u_exp)
    np.save("tof_exp", tof_exp)
elif False:  # load the results for fitting:
    u_exp = np.load("u_exp.npy")
    tof_exp = np.load("tof_exp.npy")


ax1, ax2, ax3 = MPLPlotter().new_two_panel_axes(n_bottom=2, emphasis="top")

tof_0 = 1e-3

if True:  # plot the experimental results with the colors:
    plot_all_activity_results(ax=ax1, result="tof", factor=1 / tof_0, takelog=True)
elif True:  # plot all the experimental results black and white:
    ax.plot(
        u_exp,
        np.log10(tof_exp / tof_0),
        "k",
        marker="o",
        linestyle="none",
        fillstyle="none",
    )

ax1.plot(u, np.log10(j_over_j0), "k")

# lets plot the other two models:
ax1.plot(u, np.log10(j_over_j0_simple), "k--")
ax1.plot(u, np.log10(j_over_j0_2_simple * 1e-4), "k:")

ax1.set_xlabel("U$_{RHE}$ / [V]")
ax1.set_ylabel("log(j / j$_{0, i}$)")
plt.savefig("model.png")
plt.savefig("model.svg")


if True:  # explanatory fig

    for j, state in enumerate(states):
        ax2.plot(u, thetas[j], state.color)

    # ax3 = ax2.twinx()
    ax3.plot(u, n_to_rds_vec, "r--")

    ax2.set_xlabel("U$_{RHE}$ / [V]")
    ax2.set_ylabel("coverage")
    ax3.set_ylabel("<n> before RDS")

ax1.get_figure().set_figheight(ax1.get_figure().get_figwidth() * 1.25)
plt.savefig("model_combined.png")
plt.savefig("model_combined.svg")
