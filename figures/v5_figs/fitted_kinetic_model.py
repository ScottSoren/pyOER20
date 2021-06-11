"""This module plots stuff from 21F10 in Spectro Inlets notebook."""

import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import minimize

from ixdat.constants import FARADAY_CONSTANT as F, STANDARD_TEMPERATURE as T0, R
from ixdat.plotters.base_mpl_plotter import MPLPlotter
from paper_I_v3_fig4 import plot_all_activity_results
from state_class import State

n_points = 100

U0 = 1.23  # sort of arbitrary reference potential vs RHE in [V]

alpha_rds = 0.5  # symmetry factor for the rate-determining step

u_exp = np.load("u_exp.npy")
tof_exp = np.load("tof_exp.npy")
mask = np.logical_not(np.logical_or(np.isnan(tof_exp), tof_exp < 0))
u_exp = u_exp[mask]
tof_exp = tof_exp[mask]


def get_states(G1, G2):
    # ---------- state definitions --------------- #
    return (
        State(0, 0, "k"),  # the RDS state
        State(1, G1, "b"),  # the state one electron transfer behind the RDS state
        State(2, G2, "g"),  # the state two electron transfers behind the RDS state
    )


def get_j_over_j0(G1, G2, u):

    # ---- and lets do some math! :D
    states = get_states(G1, G2)

    # This matrix is the coverage of each state (outer dimension) relative to the RDS state
    #   as a function of potential (outer dimension):
    theta_over_theta_i = np.array(
        [
            1 / state.K_rds * np.exp(-state.n_to_rds * F * (u - U0) / (R * T0))
            for state in states
        ]
    )
    # The coverage of the RDS state is the first of these over their sum:
    theta_i = theta_over_theta_i[0] / np.sum(theta_over_theta_i, axis=0)

    # From here it is easy to calculate the current relative to j0 of the RDS
    j_over_j0 = theta_i * np.exp(alpha_rds * F * (u - U0) / (R * T0))
    return j_over_j0


def get_tof_model(G1, G2, tof0):
    j_over_j0 = get_j_over_j0(G1, G2, u=u_exp)

    return j_over_j0 * tof0


def square_error(params):
    G1, G2, tof0 = params
    tof_model = get_tof_model(G1, G2, tof0)
    error = tof_model - tof_exp
    return error.dot(error)


result = minimize(square_error, np.array([-0.4, -0.1, 3e-3]))

G1, G2, tof0 = result.x

u = np.linspace(1.23, 1.6, 100)
j_over_j0 = get_j_over_j0(G1, G2, u)

fig, ax = plt.subplots()

tof_0 = 1e-3

# plot all the experimental results black and white:
ax.plot(
    u_exp,
    np.log10(tof_exp / tof_0),
    "k",
    marker="o",
    linestyle="none",
    fillstyle="none",
)

ax.plot(u, np.log10(j_over_j0), "k")

ax.set_xlabel("U$_{RHE}$ / [V]")
ax.set_ylabel("log(j / j$_{0, i}$)")
