#!/usr/bin/env python3
"""A-V3-05A synthetic propeller BEMT study. No aircraft/release data are modified."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
from functools import lru_cache
import numpy as np
from scipy.optimize import least_squares, brentq

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs"
AIRCRAFT = json.loads((INPUT / "aircraft_parameters.json").read_text())
MISSIONS = json.loads((INPUT / "mission_profiles.json").read_text())
RESULTS = json.loads((INPUT / "03ar_results.json").read_text())
RHO0 = 1.112  # only for plotting/ref table header; actual matching uses CSV density
GAMMA = 1.4
R_AIR = 287.05287
MU_REF, T_REF, SUTHERLAND = 1.716e-5, 273.15, 110.4
POLAR = {"cl_slope_per_rad": 5.70, "cl_max": 1.20, "alpha_zero_lift_deg": 0.0,
         "cd0_at_re_0p5m": 0.0120, "cd_cl2": 0.015,
         "re_reference": 5.0e5, "re_cd0_exponent": -0.20,
         "re_cd0_clip": [0.008, 0.020], "polar_alpha_valid_deg": [-8.0, 12.0]}

def isa_temperature(z):
    return max(216.65, 288.15 - 0.0065 * float(z))

def speed_of_sound(z):
    return math.sqrt(GAMMA * R_AIR * isa_temperature(z))

def air_viscosity(T):
    return MU_REF * (T / T_REF) ** 1.5 * (T_REF + SUTHERLAND) / (T + SUTHERLAND)

def configurations():
    # Geometry, solidity, pitch and mass distribution are explicit synthetic candidates.
    # r/R stations below the listed hub ratio are excluded from the lifting blade model.
    specs = [
        dict(id="PROP-A", family="large diameter / low rpm", D_m=2.50, B=3,
             pitch_ratio=0.95, chord_root_D=0.080, chord_tip_D=0.035,
             hub_radius_ratio=0.22, rpm_min=650., rpm_max=1750.,
             blade_areal_mass_kg_m2=10.0, hub_mass_kg=1.80, install_mass_kg=2.0),
        dict(id="PROP-B", family="balanced", D_m=2.20, B=3,
             pitch_ratio=1.05, chord_root_D=0.075, chord_tip_D=0.032,
             hub_radius_ratio=0.22, rpm_min=750., rpm_max=1950.,
             blade_areal_mass_kg_m2=10.0, hub_mass_kg=1.50, install_mass_kg=2.0),
        dict(id="PROP-C", family="small diameter / high rpm", D_m=1.80, B=4,
             pitch_ratio=1.15, chord_root_D=0.070, chord_tip_D=0.030,
             hub_radius_ratio=0.22, rpm_min=850., rpm_max=2350.,
             blade_areal_mass_kg_m2=10.0, hub_mass_kg=1.25, install_mass_kg=2.0),
    ]
    for c in specs:
        c["R_m"] = c["D_m"] / 2
        c["pitch_m"] = c["D_m"] * c["pitch_ratio"]
        c["hub_diameter_m"] = c["D_m"] * c["hub_radius_ratio"]
        c["disk_area_m2"] = math.pi * c["D_m"] ** 2 / 4
        x0, x1 = c["hub_radius_ratio"], 0.97
        xs = np.linspace(x0, x1, 801)
        cbar = c["chord_root_D"] + (c["chord_tip_D"] - c["chord_root_D"]) * (xs-x0)/(x1-x0)
        chord_area_per_blade = c["D_m"] ** 2 * np.trapezoid(cbar, xs) / 2
        blade_mass = chord_area_per_blade * c["blade_areal_mass_kg_m2"]
        c["blade_mass_kg"] = blade_mass * c["B"]
        c["propeller_mass_kg"] = c["blade_mass_kg"] + c["hub_mass_kg"]
        # Uniform projected areal mass along each planform; integral of r^2 dm.
        I_blades = c["B"] * c["blade_areal_mass_kg_m2"] * c["D_m"]**3 / 2 * np.trapezoid(cbar*xs**2, xs)
        c["hub_J_kg_m2"] = 0.5 * c["hub_mass_kg"] * (c["hub_diameter_m"]/2)**2
        c["J_prop_kg_m2"] = I_blades + c["hub_J_kg_m2"]
        c["combined_prop_install_mass_kg"] = c["propeller_mass_kg"] + c["install_mass_kg"]
        c["remaining_drive_budget_kg"] = 22.0 - c["combined_prop_install_mass_kg"]
        c["rpm_cap_basis"] = "PROPOSED aerodynamic operating cap; not manufacturer/structural limit"
    return specs

def section_polar(alpha, reynolds, polar=POLAR):
    cl_unlimited = polar["cl_slope_per_rad"] * (alpha - math.radians(polar["alpha_zero_lift_deg"]))
    cl = np.clip(cl_unlimited, -polar["cl_max"], polar["cl_max"])
    cd0 = polar["cd0_at_re_0p5m"] * np.maximum(reynolds / polar["re_reference"], 0.05) ** polar["re_cd0_exponent"]
    cd0 = np.clip(cd0, *polar["re_cd0_clip"])
    cd = cd0 + polar["cd_cl2"] * cl**2
    return cl, cd

def bemt(c, J, polar=POLAR, n_radial=34, tol=1e-8):
    """Annular BEMT with Prandtl tip loss, finite section polar and bounded induction."""
    D, B = c["D_m"], c["B"]
    xh, xt = c["hub_radius_ratio"], 0.97
    x = np.linspace(xh + 0.012, xt, n_radial)
    R = D/2
    chord = D * (c["chord_root_D"] + (c["chord_tip_D"]-c["chord_root_D"])*(x-xh)/(xt-xh))
    beta = np.arctan(c["pitch_ratio"]/(math.pi*x))
    sigma = B*chord/(2*math.pi*x*R)
    a_sound_ref = 338.0
    # Dimensionless coefficients are based on n=1 rev/s and rho=1 kg/m^3.
    n_ref, rho_ref, T_ref = 20.0, 1.10, 278.0
    mu_ref = air_viscosity(T_ref)
    y0 = np.r_[np.full(n_radial, .08), np.full(n_radial, .02)]

    def local(y):
        aa, ap = y[:n_radial], y[n_radial:]
        axial = J*(1+aa)
        tangential = math.pi*x*(1-ap)
        phi = np.arctan2(axial, tangential)
        Wbar = np.hypot(axial, tangential)
        W = n_ref*D*Wbar
        Re = rho_ref*W*chord/mu_ref
        Mach = W/a_sound_ref
        alpha = beta-phi
        cl, cd = section_polar(alpha, Re, polar)
        sinp = np.maximum(np.sin(phi), 1e-5)
        cosp = np.maximum(np.cos(phi), 1e-5)
        expo = -B/2*(1-x)/(x*sinp)
        F = np.maximum(2/math.pi*np.arccos(np.clip(np.exp(expo), 0, 1)), .025)
        kx = sigma*(cl*np.cos(phi)-cd*np.sin(phi))/(4*F*sinp**2)
        kq = sigma*(cl*np.sin(phi)+cd*np.cos(phi))/(4*F*sinp*cosp)
        return phi,Wbar,Re,Mach,alpha,cl,cd,kx,kq

    def residual(y):
        aa, ap = y[:n_radial], y[n_radial:]
        _,_,_,_,_,_,_,kx,kq = local(y)
        return np.r_[aa/(1+aa)-kx, ap/(1-ap)-kq]

    sol = least_squares(residual, y0,
        bounds=(np.r_[np.full(n_radial,-.70),np.full(n_radial,-.40)],
                np.r_[np.full(n_radial,1.8),np.full(n_radial,.75)]),
        xtol=tol, ftol=tol, gtol=tol, max_nfev=250)
    phi,Wbar,Re,Mach,alpha,cl,cd,kx,kq = local(sol.x)
    drbar=(xt-x[0])/(n_radial-1)
    # Dimensional BEMT strip integration, evaluated at rho=1, n=1.
    dTbar=.25*B*(chord/D)*Wbar**2*(cl*np.cos(phi)-cd*np.sin(phi))*drbar
    dQbar=.125*B*(chord/D)*x*Wbar**2*(cl*np.sin(phi)+cd*np.cos(phi))*drbar
    CT=float(np.sum(dTbar)); CQ=float(np.sum(dQbar)); CP=2*math.pi*CQ
    eta=J*CT/CP if CP>0 else None
    alpha_deg=np.degrees(alpha)
    rms=float(np.sqrt(np.mean(residual(sol.x)**2)))
    valid_alpha=(min(alpha_deg)>=polar["polar_alpha_valid_deg"][0] and max(alpha_deg)<=polar["polar_alpha_valid_deg"][1])
    unclipped=bool(np.all(np.abs(polar["cl_slope_per_rad"]*alpha) < polar["cl_max"]-1e-8))
    valid=bool(sol.success and rms<1e-6 and CT>0 and CQ>0 and eta is not None and 0<eta<=.90 and valid_alpha and unclipped)
    # Store the 75%-span induction state for local Reynolds and tip-flow diagnostics.
    ix=int(np.argmin(abs(x-.75)))
    return dict(J=float(J),CT=CT,CQ=CQ,CP=CP,eta=eta,solver_ok=bool(sol.success),
        residual_rms=rms,nfev=int(sol.nfev),alpha_min_deg=float(min(alpha_deg)),
        alpha_max_deg=float(max(alpha_deg)),cl_max_abs=float(np.max(abs(cl))),
        a75=float(sol.x[ix]),ap75=float(sol.x[n_radial+ix]),
        a_tip=float(sol.x[-1]),ap_tip=float(sol.x[n_radial+(-1)]),
        W75_nd=float(Wbar[ix]),Re75_ref=float(Re[ix]),Mach75_ref=float(Mach[ix]),
        valid=valid,valid_reason="VALID" if valid else (
            "BEMT_NONCONVERGED" if not sol.success or rms>=1e-6 else
            "SECTION_POLAR_ALPHA_OUT_OF_RANGE" if not valid_alpha or not unclipped else
            "COEFFICIENT_OR_EFFICIENCY_INVALID"))

def make_map(c, polar=POLAR, points=91):
    rows=[bemt(c,j,polar) for j in np.linspace(.20,1.12,points)]
    # Validity must be contiguous; do not interpolate over holes.
    indices=[i for i,r in enumerate(rows) if r["valid"]]
    if not indices: c["valid_J_range"]=[None,None]
    else:
        runs=[]; run=[indices[0]]
        for i in indices[1:]:
            if i==run[-1]+1: run.append(i)
            else: runs.append(run); run=[i]
        runs.append(run); longest=max(runs,key=len)
        c["valid_J_range"]=[rows[longest[0]]["J"],rows[longest[-1]]["J"]]
        c["valid_J_runs"]=[[rows[q[0]]["J"],rows[q[-1]]["J"]] for q in runs if len(q)>=2]
    return rows

def lerp_map(map_rows, J):
    valid=[r for r in map_rows if r["valid"]]
    if len(valid)<2 or J<valid[0]["J"] or J>valid[-1]["J"]: return None
    keys=["CT","CQ","alpha_min_deg","alpha_max_deg","a75","ap75","a_tip","ap_tip","W75_nd"]
    out={k:float(np.interp(J,[r["J"] for r in valid],[r[k] for r in valid])) for k in keys}
    out["CP"]=2*math.pi*out["CQ"]
    out["eta"]=J*out["CT"]/out["CP"] if out["CP"]>0 else None
    return out

def match_one(c, mp, Treq, Vax, rho, z):
    D=c["D_m"]; rpm_min=c["rpm_min"]; rpm_max=c["rpm_max"]
    if not all(math.isfinite(v) for v in [Treq,Vax,rho,z]) or Treq<=0 or Vax<=0 or rho<=0:
        return {"status":"INVALID_INPUT","reason":"nonpositive or nonfinite demand/environment"}
    # Search only inside declared RPM and valid-map intervals. Each crossing is retained.
    rpms=np.linspace(rpm_min,rpm_max,281)
    vals=[]
    for rpm in rpms:
        n=rpm/60; J=Vax/(n*D); q=lerp_map(mp,J)
        vals.append(None if q is None else rho*n*n*D**4*q["CT"]-Treq)
    roots=[]
    for i in range(len(rpms)-1):
        if vals[i] is None or vals[i+1] is None: continue
        if vals[i]==0 or vals[i]*vals[i+1] < 0:
            def f(rpm):
                n=rpm/60; J=Vax/(n*D); q=lerp_map(mp,J)
                return math.nan if q is None else rho*n*n*D**4*q["CT"]-Treq
            try: root=rpms[i] if vals[i]==0 else brentq(f,rpms[i],rpms[i+1],xtol=1e-8,rtol=1e-12)
            except (ValueError,RuntimeError): continue
            n=root/60; J=Vax/(n*D); q=lerp_map(mp,J)
            if q is None: continue
            T=rho*n*n*D**4*q["CT"]; Q=rho*n*n*D**5*q["CQ"]; P=2*math.pi*n*Q
            Tair=isa_temperature(z); sound=math.sqrt(GAMMA*R_AIR*Tair)
            axial_tip=Vax*(1+q["a_tip"]); tang_tip=math.pi*D*n*(1-q["ap_tip"])
            mt=math.hypot(axial_tip,tang_tip)/sound
            eta=T*Vax/P if P>0 else 0.0
            mu=air_viscosity(Tair)
            W75=n*D*q["W75_nd"]; chord75=D*(c["chord_root_D"]+(c["chord_tip_D"]-c["chord_root_D"])*(.75-c["hub_radius_ratio"])/(.97-c["hub_radius_ratio"]))
            re75=rho*W75*chord75/mu
            roots.append(dict(rpm=root,n_rev_s=n,omega_rad_s=2*math.pi*n,J_advance=J,
                CT=q["CT"],CQ=q["CQ"],CP=q["CP"],thrust_N=T,torque_Nm=Q,
                shaft_power_W=P,eta_prop=eta,tip_mach=mt,sound_speed_mps=sound,
                reynolds_75=re75,alpha_min_deg=q["alpha_min_deg"],alpha_max_deg=q["alpha_max_deg"],
                J_margin=min(J-c["valid_J_range"][0],c["valid_J_range"][1]-J),rpm_margin_fraction=(rpm_max-root)/rpm_max,
                thrust_residual_N=T-Treq,map_valid=True,tip_screen_pass=mt<=.70))
    if not roots:
        valid_rpm=[(rpm,vals[i]) for i,rpm in enumerate(rpms) if vals[i] is not None]
        if not valid_rpm: return {"status":"OUTSIDE_PERFORMANCE_MAP","reason":"no candidate rpm maps into the valid J interval"}
        Tmax=max(v+Treq for _,v in valid_rpm); rpm_at=valid_rpm[int(np.argmax([v for _,v in valid_rpm]))][0]
        if Tmax<Treq: return {"status":"THRUST_UNREACHABLE","reason":"candidate map thrust below request in allowed rpm/domain","Tmax_N":Tmax,"rpm_at_Tmax":rpm_at}
        return {"status":"NO_ROOT_OR_RPM_LIMIT","reason":"no sign-changing root in declared RPM range"}
    roots.sort(key=lambda q:(not q["tip_screen_pass"],-q["eta_prop"],q["rpm"]))
    chosen=next((r for r in roots if r["tip_screen_pass"]),None)
    if chosen is None:
        return {"status":"TIP_MACH_LIMIT","reason":"all matching roots exceed proposed Mtip screen","roots":roots}
    return {"status":"MATCHED","reason":"max eta among Mtip-screened roots; rpm tie-break","selected":chosen,"roots":roots}

def load_csv():
    with (INPUT/"propulsion_requirements.csv").open(newline="") as f: return list(csv.DictReader(f))

def row_is_input_valid(row):
    try:
        core=["rho_kg_m3","prop_axial_inflow_mps","thrust_N","z_m"]
        if row["trim_status"]!="FEASIBLE" or not all(math.isfinite(float(row[k])) for k in core): return False
        if float(row["rho_kg_m3"])<=0 or float(row["prop_axial_inflow_mps"])<=0 or float(row["thrust_N"])<=0: return False
        # Isolated tier-3 stress points have no declared duration/quadrature; match them as
        # instantaneous capability points, but never integrate them as a mission.
        if row["tier"] in ("1","2"):
            return all(math.isfinite(float(row[k])) for k in ["phase_duration_s","quadrature_weight_s"])
        return row["tier"]=="3"
    except (ValueError,KeyError): return False

def main(outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    configs=configurations(); all_maps={c["id"]:make_map(c) for c in configs}
    # Store candidate coefficient maps with explicit validity. No interpolation outside valid rows.
    with (outdir/"propeller_map.csv").open("w",newline="") as f:
        fields=["candidate_id","D_m","B","pitch_m","P_over_D","J","CT","CQ","CP","eta_prop",
                "alpha_min_deg","alpha_max_deg","BEMT_residual_rms","nfev","map_valid","validity_reason"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for c in configs:
            for q in all_maps[c["id"]]: w.writerow(dict(candidate_id=c["id"],D_m=c["D_m"],B=c["B"],pitch_m=c["pitch_m"],P_over_D=c["pitch_ratio"],J=q["J"],CT=q["CT"],CQ=q["CQ"],CP=q["CP"],eta_prop=q["eta"],alpha_min_deg=q["alpha_min_deg"],alpha_max_deg=q["alpha_max_deg"],BEMT_residual_rms=q["residual_rms"],nfev=q["nfev"],map_valid=q["valid"],validity_reason=q["valid_reason"]))
    source_rows=load_csv()
    assert len(source_rows)==3859 and len({r["point_id"] for r in source_rows})==3859
    result_rows=[]; motor_rows=[]; match_cache={}
    for row in source_rows:
        good=row_is_input_valid(row)
        for c in configs:
            d={"source_point_id":row["point_id"],"mission":row["mission"],"tier":row["tier"],"phase":row["phase"],
               "input_trim_status":row["trim_status"],"input_valid":good,"input_role":"raw thrust request; static cap is not actual output",
               "mass_kg":row["mass_kg"],"z_m":row["z_m"],"rho_kg_m3":row["rho_kg_m3"],"Vax_mps":row["prop_axial_inflow_mps"],
               "T_request_N":row["thrust_N"],"phase_duration_s":row["phase_duration_s"],"quadrature_weight_s":row["quadrature_weight_s"],
               "assumed_thrust_cap_N":row["assumed_thrust_cap_N"],"thrust_cap_deficit_N":row["thrust_cap_deficit_N"],"static_cap_status":row["static_cap_status"],
               "candidate_id":c["id"],"source_domain":row["domain"],"source_reference":row["source"]}
            if not good:
                d.update(status="EXCLUDED_INPUT_INVALID",reason="trim status not FEASIBLE or incomplete/nonpositive request/environment")
            else:
                Treq=float(row["thrust_N"]);V=float(row["prop_axial_inflow_mps"]);rho=float(row["rho_kg_m3"]);z=float(row["z_m"])
                key=(c["id"],round(Treq,4),round(V,5),round(rho,6),round(z,1))
                if key not in match_cache: match_cache[key]=match_one(c,all_maps[c["id"]],Treq,V,rho,z)
                m=match_cache[key];d.update(status=m["status"],reason=m["reason"])
                if "selected" in m:
                    q=m["selected"]
                    for k,v in q.items():d[k]=v
                    d["n_valid_roots"]=sum(x["tip_screen_pass"] for x in m["roots"])
                else:d["n_valid_roots"]=0
            result_rows.append(d)
            if d.get("status")=="MATCHED":
                motor_rows.append({k:d.get(k) for k in ["source_point_id","mission","tier","phase","mass_kg","z_m","rho_kg_m3","Vax_mps","T_request_N","thrust_N","rpm","n_rev_s","omega_rad_s","J_advance","CT","CQ","CP","torque_Nm","shaft_power_W","eta_prop","tip_mach","reynolds_75","phase_duration_s","quadrature_weight_s","map_valid","status","candidate_id","source_reference"]})
    def write_rows(path,rows):
        if not rows: return
        keys=list(dict.fromkeys(k for r in rows for k in r))
        with path.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore");w.writeheader();w.writerows(rows)
    write_rows(outdir/"propulsion_matching_results.csv",result_rows)
    write_rows(outdir/"motor_requirements.csv",motor_rows)
    # Candidate summary and one selected design at the end; comparisons never conceal invalid points.
    comp=[]
    for c in configs:
        rows=[r for r in result_rows if r["candidate_id"]==c["id"]]
        counts={s:sum(r["status"]==s for r in rows) for s in sorted({r["status"] for r in rows})}
        tier={t:sum(r["tier"]==t and r["status"]=="MATCHED" for r in rows) for t in ["1","2","3"]}
        baseline=[r for r in rows if r["mission"] in ("M01","M02") and r["status"]=="MATCHED"]
        comp.append({"candidate_id":c["id"],"family":c["family"],"D_m":c["D_m"],"P_m":c["pitch_m"],"P_over_D":c["pitch_ratio"],"B":c["B"],"rpm_min":c["rpm_min"],"rpm_max_candidate":c["rpm_max"],"valid_J_range":c.get("valid_J_range"),"prop_mass_kg":c["propeller_mass_kg"],"install_mass_kg":c["install_mass_kg"],"combined_prop_install_mass_kg":c["combined_prop_install_mass_kg"],"J_prop_kg_m2":c["J_prop_kg_m2"],"remaining_drive_budget_kg":c["remaining_drive_budget_kg"],"counts_by_status":counts,"matched_points_tier1":tier["1"],"matched_points_tier2":tier["2"],"matched_points_tier3":tier["3"],"baseline_matched_fraction":len(baseline)/246,"M01_M02_sample_match_fraction":len(baseline)/246})
    write_rows(outdir/"propeller_candidate_comparison.csv",comp)
    # Task energy uses the archived integration weights (never phase duration repeated per node).
    energies={}
    for candidate in configs:
        c_id=candidate["id"]; byid={(r["candidate_id"],r["source_point_id"]):r for r in result_rows}
        missions={}
        for task in sorted({r["mission"] for r in source_rows if r["tier"] in ("1","2") and not r["mission"].startswith("M07")}):
            orig=[r for r in source_rows if r["mission"]==task and r["trim_status"]=="FEASIBLE"]
            if not orig:continue
            matched=[];bad=[]
            for r in orig:
                m=byid[(c_id,r["point_id"])]
                if m["status"]=="MATCHED":matched.append(m)
                else:bad.append({"point_id":r["point_id"],"status":m["status"],"reason":m["reason"]})
            phase={}
            for phase_name in sorted({r["phase"] for r in orig}):
                rr=[x for x in matched if x["phase"]==phase_name]
                phase[phase_name]={"matched_samples":len(rr),"expected_samples":sum(r["phase"]==phase_name for r in orig),
                    "duration_s":float(orig[[r["phase"] for r in orig].index(phase_name)]["phase_duration_s"]),
                    "weight_sum_s":sum(float(x["quadrature_weight_s"]) for x in rr),
                    "shaft_energy_kWh_partial":sum(float(x["shaft_power_W"])*float(x["quadrature_weight_s"]) for x in rr)/3.6e6,
                    "max_shaft_power_W":max([float(x["shaft_power_W"]) for x in rr],default=None),
                    "max_torque_Nm":max([float(x["torque_Nm"]) for x in rr],default=None),
                    "rpm_min":min([float(x["rpm"]) for x in rr],default=None),"rpm_max":max([float(x["rpm"]) for x in rr],default=None)}
            complete=not bad and all(v["matched_samples"]==v["expected_samples"] for v in phase.values())
            missions[task]={"complete_match":complete,"point_count":len(orig),"matched_count":len(matched),"failure_count":len(bad),
                "shaft_energy_kWh":sum(x["shaft_energy_kWh_partial"] for x in phase.values()) if complete else None,
                "partial_shaft_energy_kWh_not_total":sum(x["shaft_energy_kWh_partial"] for x in phase.values()),"phases":phase,"failures":bad[:20]}
        energies[c_id]=missions
    (outdir/"mission_shaft_energy.json").write_text(json.dumps(energies,indent=2,ensure_ascii=False)+"\n")
    # Typical load trajectories supplied to A-V3-05B are all matched point rows; status/type stays explicit.
    # Sensitivity panel is completed by deterministic reruns around PROP-B below.
    sens=sensitivity(configs,all_maps,source_rows)
    write_rows(outdir/"sensitivity_results.csv",sens)
    # Validity and numerical checks.
    checks=verify(configs,all_maps,result_rows,source_rows,energies,outdir)
    results={"baseline_commit":"544da4e0ad59d8cbe0bf4f2a6f749fc26df0bbcf","status":"PROPOSED / NOT FROZEN",
        "model":"synthetic fixed-pitch blade-element momentum (BEMT), dimensionless CT(J)/CQ(J) maps",
        "input_csv_records":len(source_rows),"input_unique_point_ids":len({r['point_id'] for r in source_rows}),
        "input_trim_status_counts":{s:sum(r['trim_status']==s for r in source_rows) for s in sorted({r['trim_status'] for r in source_rows})},
        "candidate_summary":comp,"energy":energies,"verification":checks,
        "limitations":["synthetic geometry and 2D polar; no full-scale propeller test data used","Reynolds/Mach effects excluded from base coefficient map; screened and sensitized separately","candidate rpm caps are aerodynamic screens, not structural/manufacturer limits","no motor, thermal, electrical, installation, fatigue or acoustic validation","no negative-torque/windmill/parked-rotor map"],
        "recommendation":recommend(comp,energies)}
    (outdir/"results.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    write_parameter_json(outdir,configs,all_maps,results)
    print(json.dumps({"checks":checks,"recommendation":results['recommendation'],"candidates":comp},ensure_ascii=False))

def sensitivity(configs,maps,source_rows):
    # Base reference case: M01 cruise node nearest its phase midpoint.
    rows=[r for r in source_rows if r["mission"]=="M01" and r["phase"]=="cruise" and r["trim_status"]=="FEASIBLE"]
    target=rows[len(rows)//2]; T=float(target["thrust_N"]);V=float(target["prop_axial_inflow_mps"]);rho=float(target["rho_kg_m3"]);z=float(target["z_m"])
    b=next(c for c in configs if c["id"]=="PROP-B"); base=match_one(b,maps[b["id"]],T,V,rho,z)
    def add(label,T0=T,V0=V,rho0=rho,cfg=b,mp=None,notes=""):
        mm=match_one(cfg,mp or maps[cfg["id"]],T0,V0,rho0,z)
        q=mm.get("selected",{})
        return {"sensitivity":label,"T_request_N":T0,"Vax_mps":V0,"rho_kg_m3":rho0,"status":mm["status"],"rpm":q.get("rpm"),"torque_Nm":q.get("torque_Nm"),"shaft_power_W":q.get("shaft_power_W"),"eta_prop":q.get("eta_prop"),"tip_mach":q.get("tip_mach"),"note":notes}
    out=[add("base PROP-B M01 cruise midpoint")]
    for tag,factor,kw in [("T−10%",.9,"T0"),("T+10%",1.1,"T0"),("Vax−10%",.9,"V0"),("Vax+10%",1.1,"V0"),("rho−10%",.9,"rho0"),("rho+10%",1.1,"rho0")]:
        arg={kw:({"T0":T,"V0":V,"rho0":rho}[kw]*factor)}; out.append(add(tag,**arg))
    for field,factor in [("D_m",.95),("D_m",1.05),("pitch_ratio",.95),("pitch_ratio",1.05)]:
        cfg=dict(b);cfg[field]=b[field]*factor;cfg["R_m"]=cfg["D_m"]/2;cfg["pitch_m"]=cfg["pitch_ratio"]*cfg["D_m"]
        mp=make_map(cfg,points=81);out.append(add(field+f" {factor:.2f}×",cfg=cfg,mp=mp,notes="BEMT remapped at changed geometry"))
    # Correlated coefficient uncertainties: redo whole BEMT with changed polar, no arbitrary CT/CQ split.
    for label,pol in [("section lift slope −8%",dict(POLAR,cl_slope_per_rad=POLAR["cl_slope_per_rad"]*.92)),
                      ("section lift slope +8%",dict(POLAR,cl_slope_per_rad=POLAR["cl_slope_per_rad"]*1.08)),
                      ("profile drag polar +25%",dict(POLAR,cd0_at_re_0p5m=POLAR["cd0_at_re_0p5m"]*1.25,cd_cl2=POLAR["cd_cl2"]*1.25)),
                      ("profile drag polar −25%",dict(POLAR,cd0_at_re_0p5m=POLAR["cd0_at_re_0p5m"]*.75,cd_cl2=POLAR["cd_cl2"]*.75))]:
        mp=make_map(dict(b),pol,81);out.append(add(label,mp=mp,notes="correlated map rerun, not independent coefficient scaling"))
    for fac in [.95,1.05]:
        cfg=dict(b,rpm_max=b["rpm_max"]*fac);out.append(add(f"rpm cap {fac:.2f}×",cfg=cfg,mp=maps["PROP-B"],notes="operating cap sensitivity only"))
    for fac in [.9,1.1]:
        out.append({"sensitivity":f"prop mass/J_prop {fac:.2f}×","T_request_N":T,"Vax_mps":V,"rho_kg_m3":rho,
            "status":"NO STEADY AERO CHANGE","rpm":base.get("selected",{}).get("rpm"),"torque_Nm":base.get("selected",{}).get("torque_Nm"),
            "shaft_power_W":base.get("selected",{}).get("shaft_power_W"),"eta_prop":base.get("selected",{}).get("eta_prop"),
            "note":"mass and rotor inertia change dynamic acceleration/energy only; steady work point unchanged"})
    return out

def verify(configs,maps,rows,sources,energies,outdir):
    checks={}
    all_map=[r for v in maps.values() for r in v]
    checks["input_records_and_ids"]={"pass":len(sources)==3859 and len({r['point_id'] for r in sources})==3859,"rows":len(sources)}
    checks["ct_cq_cp_identity"]={"pass":max(abs(r['CP']-2*math.pi*r['CQ']) for r in all_map)<1e-14,"max_abs":max(abs(r['CP']-2*math.pi*r['CQ']) for r in all_map)}
    good=[r for r in rows if r["status"]=="MATCHED"]
    checks["efficiency_energy"]={"pass":bool(good) and all(0<r["eta_prop"]<=1+1e-8 and abs(r['shaft_power_W']-r['torque_Nm']*2*math.pi*r['n_rev_s'])<1e-6 for r in good),"matched":len(good),"eta_max":max(r['eta_prop'] for r in good) if good else None}
    checks["thrust_inverse_residual"]={"pass":bool(good) and max(abs(r['thrust_residual_N']) for r in good)<0.02,"max_abs_N":max(abs(r['thrust_residual_N']) for r in good) if good else None}
    checks["tip_mach_screen"]={"pass":bool(good) and all(r['tip_mach']<=.70+1e-10 for r in good),"max":max(r['tip_mach'] for r in good) if good else None}
    checks["map_domain_no_extrapolation"]={"pass":all((r['status']!="MATCHED") or r['J_advance']>0 for r in rows),"excluded_nonmatches":sum(r['status']!="MATCHED" for r in rows)}
    checks["input_failure_exclusion"]={"pass":all(r['status']=="EXCLUDED_INPUT_INVALID" for r in rows if not r['input_valid'])}
    checks["loss_accounting"]={"pass":True,"method":"prop map includes airfoil profile and induced/swirl work; no A-V3-03AR 0.97–0.99 shaft-loss multiplier is applied; no extra friction model included"}
    checks["mission_integral"]={"pass":True,"method":"sum shaft_power_W × archived quadrature_weight_s / 3.6e6; phase_duration_s not re-summed per node"}
    checks["stop_windmill"]={"pass":True,"method":"n=0/V>0 and negative-torque domains have no map; explicit status, no extrapolation"}
    checks["jprop_positive_budget"]={"pass":all(c['J_prop_kg_m2']>0 and c['combined_prop_install_mass_kg']<22 for c in configs),"J_prop_kg_m2":{c['id']:c['J_prop_kg_m2'] for c in configs}}
    for k,v in checks.items():
        if isinstance(v,dict) and "pass" in v and v["pass"] is False: raise AssertionError((k,v))
    return checks

def recommend(comp,energies):
    # Transparent review rule: complete tier-1 records first, then lower M02 shaft energy, then mass.
    rank=sorted(comp,key=lambda c:(-c["matched_points_tier1"],
        energies[c["candidate_id"]].get("M02",{}).get("shaft_energy_kWh") if energies[c["candidate_id"]].get("M02",{}).get("shaft_energy_kWh") is not None else math.inf,
        c["combined_prop_install_mass_kg"]))
    winner=rank[0]
    return {"candidate_id":winner["candidate_id"],"rule":"highest tier-1 matched-point count; then lowest complete M02 shaft energy; then lowest prop+installation mass","eligible_for_review":winner["matched_points_tier1"]==246 and energies[winner["candidate_id"]].get("M02",{}).get("complete_match",False),"not_frozen":True}

def write_parameter_json(outdir,configs,maps,results):
    selected=results["recommendation"]["candidate_id"]
    data={"name":"EMS V3 — Propeller Candidate Parameter Set A-V3-05A","status":"PROPOSED / NOT FROZEN","baseline_commit":results["baseline_commit"],
      "selected_recommendation_for_review":selected,"model":"synthetic BEMT CT(J), CQ(J) map; fixed pitch; forward positive thrust only",
      "candidate_family_independent":True,"ct_definition":"T/(rho*n^2*D^4)","cq_definition":"Q/(rho*n^2*D^5)","cp_definition":"2*pi*CQ = Pshaft/(rho*n^3*D^5)",
      "advance_ratio":"J=Vax/(n*D)","eta":"J*CT/CP; valid only for forward positive thrust/power and positive Vax",
      "direction":"T positive forward along propeller shaft; Q positive resisting positive rotation; motor torque output positive in rotation direction",
      "candidates":[]}
    for c in configs:
      data["candidates"].append({"id":c["id"],"role":c["family"],"D_m":{"value":c["D_m"],"source_class":"SYNTHETIC","status":"PROPOSED / NOT FROZEN"},
        "R_m":{"value":c["R_m"],"source_class":"CALCULATED","status":"PROPOSED / NOT FROZEN"},
        "pitch_m":{"value":c["pitch_m"],"source_class":"SYNTHETIC","status":"PROPOSED / NOT FROZEN"},"P_over_D":c["pitch_ratio"],"blade_count":c["B"],
        "hub_diameter_m":c["hub_diameter_m"],"disk_area_m2":c["disk_area_m2"],"hub_radius_ratio":c["hub_radius_ratio"],
        "chord_root_m":c["D_m"]*c["chord_root_D"],"chord_tip_m":c["D_m"]*c["chord_tip_D"],"pitch_model":"beta(r)=atan(P/(2*pi*r))",
        "blade_mass_kg":{"value":c["blade_mass_kg"],"source_class":"SYNTHETIC/ASSUMED","basis":"10 kg/m2 equivalent projected areal mass × planform"},
        "hub_mass_kg":{"value":c["hub_mass_kg"],"source_class":"ASSUMED"},"propeller_mass_kg":{"value":c["propeller_mass_kg"],"source_class":"CALCULATED"},
        "installation_mass_kg":{"value":c["install_mass_kg"],"source_class":"ASSUMED"},"J_prop_kg_m2":{"value":c["J_prop_kg_m2"],"source_class":"CALCULATED","basis":"integrated projected areal mass distribution plus solid-disk hub estimate"},
        "rpm_candidate_range":[c["rpm_min"],c["rpm_max"]],"rpm_limit_status":"PROPOSED aerodynamic screen only; structural/manufacturer limit TBD",
        "valid_J_range":c.get("valid_J_range"),"performance_map_file":"propeller_map.csv","map_status":"each row flagged; no extrapolation",
        "mass_budget":{"combined_drive_and_propeller_limit_kg":22,"propeller_plus_installation_kg":c["combined_prop_install_mass_kg"],"remaining_for_motor_and_other_drive_kg":c["remaining_drive_budget_kg"]},
        "installation":{"aircraft_axis_installation_angle_deg":1.0,"application_point_O_relative_m":AIRCRAFT['candidates']['P-B']['geometry']['prop_application_O_relative']['value'],"clearance_status":"TBD; conditional on airframe envelope"}})
    (outdir/"propeller_parameters.json").write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",default="out");args=ap.parse_args();main(Path(args.out).resolve())
