"""This module plots stuff from 21F10 in Spectro Inlets notebook."""

import numpy as np
from matplotlib import pyplot as plt

from ixdat.constants import FARADAY_CONSTANT as F, STANDARD_TEMPERATURE as T0, R

n_points = 100

u = np.linspace(1.23, 1.6, n_points)  # vector describing potential vs RHE in [V]
U0 = 1.23  # sort of arbitrary reference potential vs RHE in [V]

alpha_rds = 0.5  # symmetry factor for the rate-determining step

# if there was constant coverage of the RDS state,
#   the current relative to j0 would simply be:
j_over_j0_simple = np.exp(alpha_rds * F * (u - U0) / (R * T0))

# if there were two sites with different symmetry factors, we might get something like:
j_over_j0_early_site = 0.99 * np.exp(0.1 * F * (u - U0) / (R * T0)) * 1e-6
j_over_j0_late_site = 0.01 * np.exp(0.9 * F * (u - U0) / (R * T0)) * 1e-6
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
    State(1, -0.3, "b"),  # the state one electron transfer behind the RDS state
    State(2, -0.4, "g"),  # the state two electron transfers behind the RDS state
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

fig, ax = plt.subplots()
ax.plot(u, np.log10(j_over_j0), "k")

# lets plot the other two models:
ax.plot(u, np.log10(j_over_j0_simple), "k--")
ax.plot(u, np.log10(j_over_j0_2_simple), "r--")

ax.set_xlabel("U$_{RHE}$ / [V]")
ax.set_ylabel("log(j / j$_{0, i}$)")

fig2, ax2 = plt.subplots()

for j, state in enumerate(states):
    ax2.plot(u, thetas[j], state.color)

ax3 = ax2.twinx()
ax3.plot(u, n_to_rds_vec, "r--")

ax2.set_xlabel("U$_{RHE}$ / [V]")
ax2.set_ylabel("coverage")
ax3.set_ylabel("<n> before RDS")
