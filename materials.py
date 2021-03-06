import numpy as np
from sys import exit

class Materials:
    def __init__(self, rp):
        self.rp = rp
        self.input = rp.input
        self.geo = rp.geo
        self.N = rp.geo.N

        # Specific energy density (constant)
        self.C_v = self.input.C_v
        # Compressability coefficient (constant)
        self.gamma = self.input.gamma
        # Kappa function (bottom of page 1 in codespec)
        k1, k2, k3, n = self.input.kappa
        self.kappa_func = lambda T: k1 / (k2 * T**n + k3)
        # Absorption opacity (defined on spatial cells)
        self.kappa_a = np.zeros(self.N)
        # Scattering opacity (constant)
        self.kappa_s = self.input.kappa_s
        # Total opacity defined on cell edges (Eq. 19)
        self.kappa_t = np.zeros(self.N + 1)
        # Container for masses
        self.m = np.zeros(self.N)
        self.m_half = np.zeros(self.N + 1)

    # Initialize materials that require field variables to be initialized first
    def initFromFields(self, fields):
        rho_old = fields.rho_old
        V_old = self.geo.V_old

        # Initialize masses now that rho has been computed
        self.m = V_old * rho_old

        self.m_half[0] = self.m[0] / 2 # see below Eq. 38
        self.m_half[-1] = self.m[-1] / 2 # see below Eq. 38
        for i in range(1, self.N):
            self.m_half[i] = (V_old[i - 1] * rho_old[i - 1] + V_old[i] * rho_old[i]) / 2

    # Recompute kappa_a with a new temperature T (bottom of page 1 in codespec)
    def recomputeKappa_a(self, T):
        for i in range(self.N):
            self.kappa_a[i] = self.kappa_func(T[i])

    # Recompute kappa with a new temperature T (Eq. 19)
    def recomputeKappa_t(self, T):
        a = self.input.a
        # Left system boundary
        if self.input.rad_L is 'source':
            E_bL = self.input.rad_L_val
            T_L = ((E_bL / a + T[0]**4) / 2)**(1/4)
            self.kappa_t[0] = self.kappa_func(T_L) + self.kappa_s
        else:
            self.kappa_t[0] = self.kappa_func(T[0]) + self.kappa_s
        # Right system boundary
        if self.input.rad_R is 'source':
            E_bR = self.input.rad_R_val
            T_R = ((E_bR / a + T[-1]**4) / 2)**(1/4)
            self.kappa_t[-1] = self.kappa_func(T_R) + self.kappa_s
        else:
            self.kappa_t[-1] = self.kappa_func(T[-1]) + self.kappa_s
        # Interior cells
        for i in range(1, self.N):
            Tedge = ((T[i - 1]**4 + T[i]**4) / 2)**(1 / 4)
            self.kappa_t[i] = self.kappa_func(Tedge) + self.kappa_s
