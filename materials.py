import numpy as np
from sys import exit

class Materials:
    def __init__(self, rp):
        self.rp = rp
        self.input = rp.input
        self.geo = rp.geo
        self.N = rp.geo.N
        self.fields = None

        # Specific energy density (constant)
        self.C_v = self.input.C_v
        # Compressability coefficient (constant)
        self.gamma = self.input.gamma
        # Kappa function (bottom of page 1 in codespec)
        k1, k2, k3, n = self.input.kappa
        self.kappa_func = lambda T: k1 / (k2 * T**n + k3)
        # Absorption opacity (defined on spatial cells)
        self.kappa_a = np.zeros(self.N)
        self.kappa_a_old = np.zeros(self.N)
        # Absorption opacity at T_1/2 (defined on cell edges, Eq. 19)
        self.kappa_t = np.zeros(self.N)
        self.kappa_t_old = np.zeros(self.N)
        # Container for masses
        self.m = np.zeros(self.N)
        self.m_half = np.zeros(self.N + 1)

    # Initialize materials that require field variables to be initialized first
    def initFromFields(self, fields):
        self.fields = fields

        # Initialize masses now that rho has been computed
        self.m = self.geo.V * fields.rho_old
        self.m_half[0] = self.m[0] / 2 # see below Eq. 38
        self.m_half[-1] = self.m[-1] / 2 # see below Eq. 38
        for i in range(1, self.N - 1):
            self.m_half[i] = self.geo.V[i - 1] * fields.rho_old[i - 1]
            self.m_half[i] += self.geo.V[i] * fields.rho_old[i]

        # Initialize kappas
        self.recomputeKappa_a(fields.T_old)
        self.recomputeKappa_t(fields.T_old)

    # Recompute kappa_a with a new temperature T (bottom of page 1 in codespec)
    def recomputeKappa_a(self, T):
        np.copyto(self.kappa_a_old, self.kappa_a)
        for i in range(self.N):
            self.kappa_a = self.kappa_func(T[i])

    # Recompute kappa_t with a new temperature T (Eq. 19)
    def recomputeKappa_t(self, T):
        np.copyto(self.kappa_t_old, self.kappa_t)
        # Left cell (use T_1)
        self.kappa_t[0] = self.kappa_func(T[0])
        # Right cell (use T_N)
        self.kappa_t[-1] = self.kappa_func(T[-1])
        # Interior cells
        for i in range(1, self.N - 2):
            Tedge = ((T[i]**4 + T[i + 1]**4) / 2)**(1 / 4)
            self.kappa_t[i] = self.kappa_func(Tedge)