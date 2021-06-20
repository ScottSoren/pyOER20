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
    error = np.log10(tof_model) - np.log10(tof_exp)
    return error.dot(error)


result = minimize(square_error, np.array([-0.2, -0.5, 3e-3]))

G1, G2, tof0 = result.x

u = np.linspace(1.23, 1.55, 100)
j_over_j0 = get_j_over_j0(G1, G2, u)


ax1, ax2, ax3 = MPLPlotter().new_two_panel_axes(n_bottom=2, emphasis="top")

ax1.plot(u, np.log10(j_over_j0), "k")

if True:  # plot the experimental results with the colors:
    plot_all_activity_results(ax=ax1, result="tof", factor=1 / tof0, takelog=True)
elif True:  # plot all the experimental results black and white:
    ax1.plot(
        u_exp,
        np.log10(tof_exp / tof_0),
        "k",
        marker="o",
        linestyle="none",
        fillstyle="none",
    )

ax1.set_xlabel("U$_{RHE}$ / [V]")
ax1.set_ylabel("log(j / j$_{0, i}$)")
plt.savefig("model.png")
plt.savefig("model.svg")


if True:  # explanatory fig

    states = get_states(G1, G2)
    theta_over_theta_i = np.array(
        [
            1 / state.K_rds * np.exp(-state.n_to_rds * F * (u - U0) / (R * T0))
            for state in states
        ]
    )
    # ... and this matrix is the coverage of each individual state:
    thetas = theta_over_theta_i / np.sum(theta_over_theta_i, axis=0)

    # ...and also the average number of electron transfers to get to the RDS:
    n_to_rds_vec = np.sum(
        [thetas[j] * state.n_to_rds for j, state in enumerate(states)], axis=0
    )

    for j, state in enumerate(states):
        ax2.plot(u, thetas[j], state.color)
    ax3.plot(u, n_to_rds_vec, "r--")

    ax2.set_xlabel("U$_{RHE}$ / [V]")
    ax2.set_ylabel("coverage")
    ax3.set_ylabel("<n> before RDS")

ax1.get_figure().set_figheight(ax1.get_figure().get_figwidth() * 1.25)
plt.savefig("fitted_model_combined.png")
plt.savefig("fitted_model_combined.svg")


if True:
    # delta G plot
    fig, ax = plt.subplots()

    u_vec = np.array([1.23, 1.55])
    for state in states:
        n = state.n_to_rds
        G0 = state.eV_1p23_vs_rds
        G_vec = G0 + (u_vec - U0) * n
        ax.plot(u_vec, G_vec, state.color)

    ax.set_xlabel("U vs RHE / [V]")
    ax.set_ylabel("$\Delta_fG_0 - \Delta_fG_0(S_{RDS})$ / [eV]")
    ax.set_title("$\Delta_f$G_0 relative to active state")

    fig = ax.get_figure()
    fig.savefig("dG_vs_U.png")
    fig.savefig("dG_vs_U.svg")
