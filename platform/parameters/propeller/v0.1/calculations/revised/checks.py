"""Independent checks on representative points, map cells, and mission uncertainty."""
import math
from collections import Counter

import numpy as np
from scipy.optimize import brentq

from model import GEOMETRIES, forward_state_status, solve, temperature
from review import GRID, Map, csv_out, combine, energy, inputs


def investigate(out, source, matches, models, old_map, old_matches, old_energy):
    old_index = {(r["candidate_id"],r["source_point_id"]):r for r in old_matches}
    source_index = {r["point_id"]:r for r in source}
    refined = []
    interpolation = {}
    legacy_bounds = []
    for g in GEOMETRIES:
        model = models[g.id]
        centers = (model.left+model.right)/2
        direct = solve(g,centers)
        approximation = model.offset+model.slopes*centers
        interpolation[g.id] = {
            "cell_midpoints":len(centers), "all_valid":bool(direct["valid"].all()),
            "max_abs_CT":float(np.max(abs(direct["CT"]-approximation[0]))),
            "max_abs_CQ":float(np.max(abs(direct["CQ"]-approximation[1]))),
            "max_abs_eta":float(np.max(abs(direct["eta"]-centers*approximation[0]/(2*np.pi*approximation[1]))))}
        assert direct["valid"].all()
        assert interpolation[g.id]["max_abs_CT"]<2e-6 and interpolation[g.id]["max_abs_CQ"]<2e-6

        old = [r for r in old_map if r["candidate_id"]==g.id and r["map_valid"]=="True"]
        old_j = np.array([float(r["J"]) for r in old])
        old_ct = np.array([float(r["CT"]) for r in old])
        for point in ("X01-MAX-THRUST","X03-LOW-LOAD"):
            demand,V,rho,h = inputs(source_index[point])
            k=60*V/g.D
            lo,hi=max(g.rpm_min,k/old_j[-1]),min(g.rpm_max,k/old_j[0])
            assert lo<=hi
            rpm=np.sort(np.array([lo,*[k/j for j in old_j if lo<k/j<hi],hi]))
            thrust=rho*(rpm/60)**2*g.D**4*np.interp(k/rpm,old_j,old_ct)
            assert np.all(np.diff(thrust)>0)  # monotonic on each piece is checked below
            jmid=k/((rpm[:-1]+rpm[1:])/2)
            seg=np.searchsorted(old_j,jmid)-1
            slopes=np.diff(old_ct)[seg]/np.diff(old_j)[seg]
            offsets=old_ct[seg]-slopes*old_j[seg]
            assert np.all(2*offsets*rpm[:-1]+slopes*k>0) and np.all(2*offsets*rpm[1:]+slopes*k>0)
            exact_old_rpm=None
            if thrust[0]<=demand<=thrust[-1]:
                exact_old_rpm=brentq(lambda r:rho*(r/60)**2*g.D**4*np.interp(k/r,old_j,old_ct)-demand,lo,hi)
            relaxed=model.match(g,demand,V,rho,h,rpm_min=1)
            legacy_bounds.append(dict(candidate_id=g.id,point_id=point,request_N=demand,old_rpm_floor=lo,
                                      old_rpm_ceiling=hi,old_min_N=thrust[0],old_max_N=thrust[-1],
                                      old_exact_rpm=exact_old_rpm,old_status=old_index[g.id,point]["status"],
                                      relaxed_floor_status=relaxed["status"],relaxed_floor_rpm=relaxed.get("rpm")))
        selected = [next(r for r in matches if r["candidate_id"]==g.id and r["source_point_id"]==key)
                    for key in ("M02-cruise-20","M02-climb-00","M02-descent-20","M03-300-climb-00","X02-MAX-EFFECTIVE-POWER")]
        if g.id=="PROP-A":
            selected.extend(r for r in matches if r["candidate_id"]==g.id and r["source_point_id"] in ("X01-MAX-THRUST","X03-LOW-LOAD"))
        for r in selected:
            if r["status"]!="MATCHED":
                continue
            j=r["J"]
            variants=(
                ("radial_16",dict(stations=16)),("radial_32",dict(stations=32)),
                ("base_64",{}),("radial_128",dict(stations=128)),("radial_256",dict(stations=256)),
                ("bisection_20",dict(iterations=20)),("bisection_28",dict(iterations=28)),
                ("bisection_46",dict(iterations=46)),("no_hub_loss",dict(hub_loss=False)),
                ("span_to_0p97",dict(extend=False)),("legacy_stations_tip_only",dict(legacy=True)),
                ("actual_Re",dict(condition=(r["rpm"]/60,float(r["rho_kg_m3"]),temperature(float(r["z_m"]))))),
            )
            for case, kwargs in variants:
                p={k:v[0] for k,v in solve(g,j,**kwargs).items()}
                direct_thrust=float(r["rho_kg_m3"])*(r["rpm"]/60)**2*g.D**4*p["CT"]
                refined.append(dict(candidate_id=g.id,point_id=r["source_point_id"],case=case,J=j,
                                    CT=p["CT"],CQ=p["CQ"],eta=p["eta"],max_annular_residual=p["balance"],
                                    a_interior_max=p["a_max_interior"],a_interior_min=p["a_min_interior"],
                                    relative_CT_error_vs_map=(p["CT"]-r["CT"])/r["CT"],direct_thrust_delta_N=direct_thrust-r["thrust_N"],
                                    relative_CQ_error_vs_map=(p["CQ"]-r["CQ"])/r["CQ"],map_valid=p["valid"]))
    csv_out(out/"independent_recalculation.csv",refined)
    csv_out(out/"stress_boundary_diagnostics.csv",legacy_bounds)

    def max_difference(a,b,field):
        left={(r["candidate_id"],r["point_id"]):r[field] for r in refined if r["case"]==a}
        right={(r["candidate_id"],r["point_id"]):r[field] for r in refined if r["case"]==b}
        return max(abs(left[k]-right[k]) for k in left)
    numerical = {f"{a}_vs_{b}":{k:max_difference(a,b,k) for k in ("CT","CQ","eta")}
                 for a,b in (("radial_16","radial_256"),("radial_32","radial_256"),("base_64","radial_256"),
                             ("bisection_20","bisection_46"),("bisection_28","bisection_46"),
                             ("base_64","bisection_46"),("base_64","actual_Re"),
                             ("base_64","no_hub_loss"),("base_64","span_to_0p97"))}
    assert numerical["base_64_vs_radial_256"]["CT"]<1e-5
    assert numerical["base_64_vs_bisection_46"]["CQ"]<1e-9

    max_direct_thrust = max(abs(r["direct_thrust_delta_N"]) for r in refined if r["case"]=="base_64")
    assert max_direct_thrust < .01

    # Independently integrate the mass moments of c(x)/D = b + m*x.
    for g in GEOMETRIES:
        m = (g.outer_chord_ratio-g.root_chord_ratio)/(g.outer_station-g.hub)
        b = g.root_chord_ratio-m*g.hub
        j_dimensionless = (b*(g.outer_station**3-g.hub**3)/3 + m*(g.outer_station**4-g.hub**4)/4
                           + g.outer_chord_ratio*(1-g.outer_station**3)/3)
        analytical = g.blades*g.areal_mass*g.D**4/8*j_dimensionless
        assert abs(analytical-g.mass()["blade_J_kg_m2"])<1e-12
        assert 0 < g.mass()["gyration_radius_m"] < g.D/2

    # Explicit boundary cases: invalid endpoints cannot be crossed, and fallback is a status.
    probe_g=GEOMETRIES[1]
    probe_model=models[probe_g.id]
    assert probe_model.match(probe_g,100,0,1.2,0)["status"]=="OUTSIDE_FORWARD_DOMAIN"
    assert probe_model.match(probe_g,-100,35,1.2,0)["status"]=="OUTSIDE_FORWARD_DOMAIN"
    assert probe_model.match(probe_g,100,35,1.2,0,mach_limit=.1)["status"]=="MACH_SCREEN"
    assert probe_model.match(probe_g,100,35,1.2,0,rpm_min=0+probe_g.rpm_max+1)["status"]=="OUTSIDE_RPM_J_DOMAIN"
    toy=solve(probe_g,[.65,.70,.75,.80,.85])
    toy["valid"][2]=False
    assert Map(toy).validity==[[.65,.70],[.80,.85]]
    intervals=probe_model.validity
    for rpm,V,expected in (
        (0,35,"PARKED_UNKNOWN"),(-5,35,"OUTSIDE_FORWARD_DOMAIN"),
        (80,35,"OUTSIDE_RPM_SCREEN"),(950,0,"OUTSIDE_FORWARD_DOMAIN"),
        (750,40,"OUTSIDE_J_DOMAIN"),(1200,37,"INSIDE_LOOKUP_DOMAIN_CHECK_MACH")):
        assert forward_state_status(rpm,V,1.1,probe_g,intervals)==expected
    valid_a_max=max(float(max(m.table["a_max_interior"][m.table["valid"]])) for m in models.values())
    valid_a_min=min(float(min(m.table["a_min_interior"][m.table["valid"]])) for m in models.values())

    g=GEOMETRIES[1]
    candidate_source=[r for r in source if r["mission"] in ("M01","M02","M03-300")]
    sensitivity=[]
    for case,settings,screen in (
        ("base",{},.70),("profile_drag_plus25",{"drag":1.25},.70),
        ("profile_drag_minus25",{"drag":.75},.70),("lift_slope_plus8",{"lift":1.08},.70),
        ("lift_slope_minus8",{"lift":.92},.70),("no_hub_loss",{"hub_loss":False},.70),
        ("span_to_0p97",{"extend":False},.70),("screen_M0p45",{},.45),
        ("screen_M0p40",{},.40),("screen_M0p38",{},.38)):
        m=models[g.id] if not settings else Map(solve(g,GRID,**settings))
        result=[]
        for r in candidate_source:
            row=combine(r,g,m)
            if screen!=.70:
                row={k:v for k,v in row.items() if k not in m.match(g,*inputs(r))}
                row.update(m.match(g,*inputs(r),mach_limit=screen))
            result.append(row)
        regrouped=energy(result)[g.id]
        for mission,entry in regrouped.items():
            ok=[r for r in result if r["mission"]==mission and r["status"]=="MATCHED"]
            sensitivity.append(dict(case=case,mission=mission,valid_count=len(ok),n=123,
                                    shaft_kWh=entry["P_shaft_kWh"],eta_energy=entry["eta_energy"],
                                    max_shaft_W=max((r["P_shaft_W"] for r in ok),default=None),
                                    max_rpm=max((r["rpm"] for r in ok),default=None),
                                    max_Q_Nm=max((r["Q_prop_Nm"] for r in ok),default=None)))
    csv_out(out/"sensitivity_results.csv",sensitivity)

    m02=[r for r in matches if r["candidate_id"]==g.id and r["mission"]=="M02" and r["status"]=="MATCHED"]
    historic_useful=sum(float(source_index[r["source_point_id"]]["effective_W"])*float(r["quadrature_weight_s"]) for r in m02)/3.6e6
    independence_check=sum(r["useful_W"]*float(r["quadrature_weight_s"]) for r in m02)/3.6e6
    assert abs(historic_useful-independence_check)<1e-10
    archived_old_shaft=old_energy[g.id]["M02"]["shaft_energy_kWh"]
    m07=[r for r in source if r["mission"].startswith("M07")]
    physical_points={inputs(r) for r in source if r["trim_status"]=="FEASIBLE"}
    return dict(midcell_interpolation=interpolation,numerical_convergence=numerical, max_direct_thrust_delta_N=max_direct_thrust, analytic_mass_moment_check="PASS", boundary_guard_checks="PASS", valid_map_interior_a_range=[valid_a_min,valid_a_max],
                M02_original_effective_over_shaft=historic_useful/archived_old_shaft,
                M02_archived_effective_kWh=historic_useful,
                source_unique_physical_tuples=len(physical_points),
                M07_source_count=len(m07),M07_original_static_cap_states=dict(Counter(r["static_cap_status"] for r in m07)),
                matlab_simulink="NOT RUN")
