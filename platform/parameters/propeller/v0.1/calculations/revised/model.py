"""Independent axial propeller BEMT using a bracketed inflow-angle residual."""
from dataclasses import dataclass, asdict
import math

import numpy as np
from scipy.special import roots_legendre

BASELINE = "544da4e0ad59d8cbe0bf4f2a6f749fc26df0bbcf"
REF = (20.0, 1.10, 278.0)  # rev/s, kg/m³, K
TIP_SCREEN = 0.70
AIR = 287.05287


@dataclass(frozen=True)
class Geometry:
    id: str
    D: float
    blades: int
    pitch_ratio: float
    root_chord_ratio: float
    outer_chord_ratio: float
    rpm_min: float
    rpm_max: float
    hub_mass: float
    hub: float = .22
    outer_station: float = .97
    areal_mass: float = 10.0
    install: float = 2.0

    def chord_ratio(self, x):
        f = np.minimum((x - self.hub) / (self.outer_station - self.hub), 1.0)
        return self.root_chord_ratio + (self.outer_chord_ratio - self.root_chord_ratio) * f

    def mass(self, extend=True):
        x, weights = radial(self, 16, extend=extend)
        radius = self.D / 2
        dm = self.blades * self.areal_mass * self.D * self.chord_ratio(x) * radius * weights
        jb = float(dm @ (radius*x)**2)
        jh = .5*self.hub_mass*(radius*self.hub)**2
        mass = float(dm.sum()) + self.hub_mass
        return dict(**asdict(self), pitch_m=self.pitch_ratio*self.D, disk_area_m2=math.pi*radius**2,
                    blades_kg=float(dm.sum()), prop_kg=mass, blade_J_kg_m2=jb, hub_J_kg_m2=jh,
                    J_prop_kg_m2=jb+jh, gyration_radius_m=math.sqrt((jb+jh)/mass),
                    drive_remaining_kg=22-mass-self.install)


GEOMETRIES = (
    Geometry("PROP-A", 2.5, 3, .95, .080, .035, 650, 1750, 1.8),
    Geometry("PROP-B", 2.2, 3, 1.05, .075, .032, 750, 1950, 1.5),
    Geometry("PROP-C", 1.8, 4, 1.15, .070, .030, 850, 2350, 1.25),
)


def radial(g, stations, extend=True):
    nodes, weights = roots_legendre(stations)
    intervals = [(g.hub, g.outer_station)]
    if extend:
        intervals.append((g.outer_station, 1.0))
    return tuple(np.concatenate([func(l, r) for l, r in intervals]) for func in (
        lambda l, r: (l+r)/2 + (r-l)/2*nodes, lambda l, r: (r-l)/2*weights))


def temperature(height):
    return max(216.65, 288.15-.0065*height)


def viscosity(T):
    return 1.716e-5*(T/273.15)**1.5*(273.15+110.4)/(T+110.4)


def solve(g, advance, stations=64, iterations=38, condition=REF,
          drag=1., lift=1., hub_loss=True, extend=True, legacy=False):
    """Solve for phi, then integrate each strip with the dimensional blade forces.

    `legacy` reproduces the original integration stations/weights, tip-only loss.
    It is diagnostic only. The performance branch uses independent Gauss quadrature.
    """
    J = np.atleast_1d(advance).astype(float)[:, None]
    if np.any(J <= 0):
        raise ValueError("Positive axial forward flight only")
    if legacy:
        x = np.linspace(g.hub+.012, .97, 34)
        weights = np.full_like(x, x[1]-x[0])
    else:
        x, weights = radial(g, stations, extend)
    n, rho, T = condition
    chord = g.D*g.chord_ratio(x)
    beta = np.arctan(g.pitch_ratio/(np.pi*x))
    sigma = g.blades*chord/(np.pi*g.D*x)
    tang = np.pi*x
    re_factor = rho*n*g.D*chord/viscosity(T)

    def state(phi):
        s, c = np.sin(phi), np.cos(phi)
        cl_linear = lift*5.7*(beta-phi)
        cl = np.clip(cl_linear, -1.2, 1.2)
        def prandtl(exponent):
            return 2/np.pi*np.arccos(np.exp(-exponent))
        F = prandtl(g.blades/2*(1-x)/(x*s))
        if legacy:
            F = np.maximum(F, .025)
        elif hub_loss:
            F *= prandtl(g.blades/2*(x-g.hub)/(g.hub*s))
        tang_factor = sigma/(4*F*s*c)
        W = np.hypot(J, tang)
        # Iterate the weak Reynolds dependence at fixed phi with the tangential velocity relation.
        for _ in range(7):
            cd = drag*(np.clip(.012*np.maximum(re_factor*W/5e5, .05)**(-.2), .008, .020)
                       + .015*cl**2)
            ctan = cl*s+cd*c
            kq = tang_factor*ctan
            W = tang/(c*np.maximum(1+kq, .01))
        cax = cl*c-cd*s
        kx = sigma*cax/(4*F*s**2)
        error = J*c*(1+kq)-tang*s*(1-kx)
        return error, W, cax, ctan, kx, kq, cl_linear, cd, F

    shape = (len(J), len(x))
    lo, hi = np.full(shape, .025), np.full(shape, 1.545)
    bracket = (state(lo)[0] >= 0) & (state(hi)[0] <= 0)
    for _ in range(iterations):
        mid = (lo+hi)/2
        lower_half = state(mid)[0] <= 0
        hi = np.where(lower_half, mid, hi)
        lo = np.where(lower_half, lo, mid)
    phi = (lo+hi)/2
    err, W, cax, ctan, kx, kq, cl, cd, F = state(phi)
    a = W*np.sin(phi)/J-1
    ap = 1-W*np.cos(phi)/tang
    strip_t = .25*g.blades*(chord/g.D)*W**2*cax*weights
    strip_q = .125*g.blades*(chord/g.D)*x*W**2*ctan*weights
    ct, cq = strip_t.sum(axis=1), strip_q.sum(axis=1)
    cp = 2*np.pi*cq
    eta = np.divide(J[:, 0]*ct, cp, out=np.full_like(cp, np.nan), where=cp > 0)
    alpha = np.degrees(beta-phi)
    q_profile = (.125*g.blades*(chord/g.D)*x*W**2*cd*np.cos(phi)*weights).sum(axis=1)
    # Recover the balance directly from independent kinematic velocities.
    balance = np.maximum(abs(a/(1+a)-kx), abs(ap/(1-ap)-kq)).max(axis=1)
    # Edge cells have small circulation. Retain their induction diagnostics and screen strong axial
    # induction over the lifting annulus away from the first and last 3% of radius.
    interior = (x >= g.hub+.03) & (x <= .97)
    amax = a[:, interior].max(axis=1)
    amin = a[:, interior].min(axis=1)
    adi = (np.sqrt(1+8*np.maximum(ct,0)/(np.pi*J[:,0]**2))-1)/2
    ideal_cp = J[:,0]*ct*(1+adi)
    reasons = np.full(len(J), "VALID", dtype=object)
    conditions = (
        ((ct <= 0) | (cq <= 0) | ~np.isfinite(eta) | (cp < ideal_cp), "NONPROPELLING_OR_IDEAL_LIMIT"),
        ((amax > .50) | (amin < -.30), "INDUCTION_GUARD"),
        ((alpha.min(axis=1) < -8) | (alpha.max(axis=1) > 12) | (abs(cl).max(axis=1) >= 1.2), "POLAR_DOMAIN"),
        (~bracket.all(axis=1) | (balance > 2e-6), "ANNULUS_SOLVE"),
    )
    for mask, code in conditions:
        reasons[mask] = code
    return dict(J=J[:,0], CT=ct, CQ=cq, CP=cp, eta=eta, reason=reasons, valid=reasons=="VALID",
                ideal_CP=ideal_cp, profile_CP=2*np.pi*q_profile,
                alpha_min_deg=alpha.min(axis=1), alpha_max_deg=alpha.max(axis=1),
                a_max_interior=amax, a_min_interior=amin, balance=balance,
                a_outer=a[:,-1], ap_outer=ap[:,-1], outer_x=np.full(len(J),x[-1]),
                W_outer_nd=W[:,-1], W75_nd=np.array([np.interp(.75,x,row) for row in W]),
                W_max_nd=W.max(axis=1))


def forward_state_status(rpm, V_ax, rho, g, valid_j_intervals):
    """Quasisteady software dispatch. Invalid means loads are unavailable."""
    if not all(math.isfinite(v) for v in (rpm,V_ax,rho)) or rho <= 0:
        return "INVALID_INPUT"
    if rpm == 0:
        return "PARKED_UNKNOWN"
    if rpm < 0 or V_ax <= 0:
        return "OUTSIDE_FORWARD_DOMAIN"
    if not g.rpm_min <= rpm <= g.rpm_max:
        return "OUTSIDE_RPM_SCREEN"
    advance = 60*V_ax/(rpm*g.D)
    if not any(lo <= advance <= hi for lo,hi in valid_j_intervals):
        return "OUTSIDE_J_DOMAIN"
    return "INSIDE_LOOKUP_DOMAIN_CHECK_MACH"
