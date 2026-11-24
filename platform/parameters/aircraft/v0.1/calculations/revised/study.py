"""A-V3-03AR mission supplement. Reuses the original 03A load equations."""
import argparse
import csv
import json
import importlib.util
from pathlib import Path

import numpy as np
from scipy.integrate import simpson
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent
original_spec = importlib.util.spec_from_file_location("study_03a", ROOT / "source_03a" / "study.py")
original = importlib.util.module_from_spec(original_spec)
original_spec.loader.exec_module(original)

CONFIG = json.loads((ROOT / "mission_profiles.json").read_text())
COMMON = CONFIG["common"]
CANDIDATE = original.cfg["candidates"]["P-B"]
G = original.g
MAC = original.geometry(CANDIDATE)[2]
EFFICIENCY = original.eta


def properties(payload, fuel, ballast):
    entries = np.array(original.cfg["mass_rows"], dtype=float)
    entries[1, 0], entries[-1, 0] = payload, fuel
    if ballast:
        nominal_cg, _ = original.mass(CANDIDATE, 471)
        entries = np.vstack((entries, [ballast, -nominal_cg[0]/MAC, nominal_cg[1]/MAC, 0]))
    weights = entries[:, 0]
    stations = entries[:, 1:3] * [-MAC, MAC]
    center = np.average(stations, axis=0, weights=weights)
    inertia = sum(weights*((entries[:, 3]*MAC)**2 + ((stations-center)**2).sum(axis=1)))
    return weights.sum(), center, inertia


def power_bounds(useful_w):
    if useful_w < COMMON["electrical_conversion_screen_min_effective_W"]:
        return [None] * 6
    return [
        useful_w / EFFICIENCY[:level, j].prod()
        for level in (1, 2, 3) for j in (1, 0)
    ]


def solve(tas, height, rate, wind, payload, fuel, ballast):
    mass, cg, inertia = properties(payload, fuel, ballast)
    density = original.density(height)
    gamma = np.arcsin(rate/tas)

    def residual(y):
        alpha, elevator, thrust_fraction = y
        force, moment, _ = original.loads(CANDIDATE, density, tas, alpha, 0, elevator,
                                           thrust_fraction*mass*G, cg, (1,1,1))
        inertial_force = original.rot(alpha+gamma)@force
        return np.r_[(inertial_force-[0, mass*G])/(mass*G), moment/(mass*G*MAC)]

    result = least_squares(residual, [0.07, -0.06, 0.12],
                           bounds=([-np.pi/36, -np.pi/9, 0.0],
                                   [np.radians(11), np.pi/9, np.inf]),
                           xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=250)
    alpha, elevator, thrust_fraction = result.x
    thrust = thrust_fraction*mass*G
    _, net_moment, diagnostics = original.loads(CANDIDATE, density, tas, alpha, 0, elevator,
                                                 thrust, cg, (1,1,1))
    lift, drag, cl, _, aero_moment, prop_moment, moment_o = diagnostics
    scaled = residual(result.x)
    stall = np.sqrt(2*mass*G/(density*CANDIDATE[0]*CANDIDATE[6]))
    status = "FEASIBLE"
    if not result.success:
        status = "NUMERICAL_FAILURE"
    elif max(abs(scaled)) > 1e-8:
        status = "NO_TRIM_FOUND"
    elif cl > .85*CANDIDATE[6] or tas < 1.30*stall:
        status = "OUTSIDE_SCREEN"
    elif mass > COMMON["maximum_mass_kg"] or fuel < COMMON["unusable_fuel_kg"]:
        status = "OUTSIDE_MASS_BUDGET"
    axial = tas*np.cos(alpha+original.axis)
    power = thrust*axial
    bounds = power_bounds(power) if status=="FEASIBLE" else [None]*6
    return dict(mass_kg=mass, total_fuel_kg=fuel, payload_kg=payload, cg_x_b_m=cg[0],
                cg_z_b_m=cg[1], Iy_kg_m2=inertia, z_m=height, rho_kg_m3=density,
                tas_mps=tas, ground_speed_x_mps=np.sqrt(tas**2-rate**2)+wind,
                wind_x_mps=wind, vertical_rate_mps=rate, alpha_deg=np.degrees(alpha),
                theta_deg=np.degrees(alpha+gamma), elevator_deg=np.degrees(elevator),
                axis_deg=np.degrees(original.axis), prop_axial_inflow_mps=axial,
                thrust_N=thrust, effective_W=power, prop_shaft_min_W=bounds[0],
                prop_shaft_max_W=bounds[1], motor_mech_min_W=bounds[2],
                motor_mech_max_W=bounds[3], drive_in_min_W=bounds[4],
                drive_in_max_W=bounds[5], stall_tas_mps=stall, speed_margin_ratio=tas/stall,
                lift_N=lift, drag_N=drag, CL=cl, moment_aero_CG_Nm=aero_moment,
                moment_prop_CG_Nm=prop_moment, moment_prop_O_Nm=moment_o, net_moment_Nm=net_moment,
                residual_x_N=scaled[0]*mass*G, residual_z_N=scaled[1]*mass*G,
                residual_M_Nm=scaled[2]*mass*G*MAC, max_scaled_residual=max(abs(scaled)),
                nfev=result.nfev, solver_status=result.status, trim_status=status,
                conditional_power=("03A efficiency envelope; shaft loss counted once"
                                   if bounds[0] is not None else "UNAVAILABLE"))


def summarize_phase(rows, seconds):
    summary = dict(t_s=seconds, distance_m=rows[-1]["ground_x_m"]-rows[0]["ground_x_m"])
    for key in ("mass_kg", "z_m", "rho_kg_m3", "tas_mps", "ground_speed_x_mps", "vertical_rate_mps",
                "thrust_N", "alpha_deg", "elevator_deg",
                "effective_W", "prop_shaft_min_W", "prop_shaft_max_W",
                "motor_mech_min_W", "motor_mech_max_W", "drive_in_min_W", "drive_in_max_W",
                "stall_tas_mps", "speed_margin_ratio", "prop_axial_inflow_mps",
                "cg_x_b_m", "cg_z_b_m", "Iy_kg_m2"):
        values = [r[key] for r in rows]
        summary[key] = None if None in values else [min(values), max(values)]
    for key in ("effective_W", "prop_shaft_min_W", "prop_shaft_max_W",
                "motor_mech_min_W", "motor_mech_max_W", "drive_in_min_W", "drive_in_max_W"):
        values = [r[key] for r in rows]
        summary[key.replace("_W", "_kWh")] = (
            simpson(values, x=[r["time_s"] for r in rows])/3.6e6
            if None not in values and all(r["trim_status"]=="FEASIBLE" for r in rows) else None
        )
    return summary


def mission(case, distance_km, n=None):
    opt = COMMON | case
    limit = distance_km*1000
    wind = opt["wind_x_mps"]
    count = n or opt["quadrature_nodes_per_phase"]
    begin, top, end = opt["altitudes_m"]
    up, down = opt["climb_rate_mps"], opt["descent_rate_mps"]
    vu, vc, vd = opt["climb_tas_mps"], opt["cruise_tas_mps"], opt["descent_tas_mps"]
    climb_time, descent_time = (top-begin)/up, (end-top)/down
    ground_x = lambda v,r: np.sqrt(v*v-r*r)+wind
    cruise_dist = limit-ground_x(vu,up)*climb_time-ground_x(vd,down)*descent_time
    assert cruise_dist > 0 and all(ground_x(v,r)>0 for v,r in ((vu,up),(vc,0),(vd,down)))
    phases = (("climb",begin,top,vu,up,climb_time),
              ("cruise",top,top,vc,0,cruise_dist/ground_x(vc,0)),
              ("descent",top,end,vd,down,descent_time))
    t0, x0 = 0.0, 0.0
    rows, summaries = [], {}
    start_fuel = opt["initial_total_fuel_kg"]
    finish_fuel = opt.get("final_total_fuel_kg",start_fuel)
    case_id = case["id"] + (f"-{distance_km}" if "distances_km" in case else "")
    for name,z0,z1,tas,rate,duration in phases:
        samples = []
        for i, fraction in enumerate(np.linspace(0,1,count)):
            x = x0+duration*fraction*ground_x(tas,rate)
            fuel = start_fuel+(finish_fuel-start_fuel)*np.clip(x/limit,0,1)
            point = solve(tas,z0+(z1-z0)*fraction,rate,wind,opt["payload_kg"],fuel,opt["ballast_kg"])
            step = duration/(count-1)
            weight = step/3 if i in (0,count-1) else (4 if i%2 else 2)*step/3
            samples.append(dict(point_id=f"{case_id}-{name}-{i:02d}", mission=case_id,
                                tier=case["tier"], phase=name, phase_duration_s=duration,
                                quadrature_weight_s=weight, time_s=t0+duration*fraction,
                                ground_x_m=x, occurrence="one phase per named scenario",
                                continuous_design=case["tier"]==1,
                                short_extension=case["id"].startswith("M03") and name=="climb",
                                extreme_stress=False, source="03A/P-B equations; 03AR scenario",
                                domain="25-49 m/s TAS; alpha -5..11 deg; CL<=0.85 CLmax; TAS>=1.30 Vs",
                                **point))
        rows.extend(samples)
        summaries[name] = summarize_phase(samples,duration)
        x0,t0 = samples[-1]["ground_x_m"], samples[-1]["time_s"]
    total = dict(distance_m=x0, time_s=t0, initial_mass_kg=rows[0]["mass_kg"],
                 final_mass_kg=rows[-1]["mass_kg"], max_scaled_residual=max(r["max_scaled_residual"] for r in rows),
                 statuses={status:sum(r["trim_status"]==status for r in rows)
                           for status in sorted({r["trim_status"] for r in rows})})
    for key in summaries["cruise"]:
        if key.endswith("_kWh"):
            values = [p[key] for p in summaries.values()]
            total[key] = sum(values) if None not in values else None
    return case_id, rows, dict(phases=summaries, total=total)


def isolated(label, tas, z, rate, fuel=40, ballast=0):
    return dict(point_id=label, mission="03A scan replay", tier=3, phase="isolated",
                phase_duration_s=None, quadrature_weight_s=None, time_s=None, ground_x_m=None,
                occurrence="no operational duration or frequency", continuous_design=False,
                short_extension=False, extreme_stress=True, source="03A/P-B point; 03AR solver",
                domain="25-49 m/s TAS; alpha -5..11 deg; CL<=0.85 CLmax; TAS>=1.30 Vs",
                **solve(tas,z,rate,0,48,fuel,ballast))


def static_limits(scenarios):
    output, cases = {}, []
    for spec in CONFIG["thrust_limits"]:
        rows = [r for r in scenarios[spec["reference"]] if r["phase"]==spec["phase"]]
        t0 = rows[0]["time_s"]
        def cap(t):
            if "cap_N" in spec:
                return spec["cap_N"]
            return spec["cap_initial_N"] + (spec["cap_final_N"]-spec["cap_initial_N"])*min(t/spec["cap_ramp_s"],1)
        deficit = [(r["time_s"]-t0,r["thrust_N"]-cap(r["time_s"]-t0)) for r in rows]
        first = next((t for t,d in deficit if d>0),None)
        for i, (sample, (elapsed, delta)) in enumerate(zip(rows,deficit)):
            cases.append(sample | dict(point_id=f"{spec['id']}-{i:02d}",mission=spec["id"],tier=2,
                                       continuous_design=False,short_extension=spec["id"]=="M07-HI",
                                       occurrence="static demand comparison; unflown",
                                       assumed_thrust_cap_N=cap(elapsed),thrust_cap_deficit_N=max(0,delta),
                                       static_cap_status="EXCEEDS_CAP" if delta>0 else "WITHIN_CAP"))
        exact = None
        if "cap_ramp_s" in spec:
            exact = (spec["cap_initial_N"]-rows[0]["thrust_N"])*spec["cap_ramp_s"]/(spec["cap_initial_N"]-spec["cap_final_N"])
        output[spec["id"]] = dict(phase=spec["phase"], baseline=spec["reference"],
                                   required_N=[min(r["thrust_N"] for r in rows),max(r["thrust_N"] for r in rows)],
                                   max_deficit_N=max(d for _,d in deficit),
                                   first_infeasible_sample_s=first, continuous_crossing_s=exact,
                                   status="REQUEST_STATIC_INFEASIBLE_UNDER_CAP" if first is not None else "WITHIN_CAP",
                                   dynamics="NOT RUN")
    return output, cases


def main(out):
    out.mkdir(parents=True,exist_ok=True)
    traces, summary = {}, {}
    for case in CONFIG["scenarios"]:
        for length in (case.get("distances_km") or [case["distance_km"]]):
            key, rows, report = mission(case,length)
            traces[key], summary[key] = rows, report
    extreme = [isolated("X01-MAX-THRUST",26,0,5,ballast=29),
               isolated("X02-MAX-EFFECTIVE-POWER",49,0,5,ballast=29),
               isolated("X03-LOW-LOAD",25,0,-1.4,fuel=4),
               isolated("X04-SCREEN-REJECT",25,2500,5,ballast=29),
               isolated("X05-STEEP-DESCENT",36,1000,-8)]
    baseline = original.trim(CANDIDATE,37,1500,0,471)
    cross = abs(baseline["thrust"]-summary["M01"]["phases"]["cruise"]["thrust_N"][0])
    original_mission = original.mission(CANDIDATE,471)
    base_error = abs(original_mission["totals"][2]-summary["M01"]["total"]["effective_kWh"])
    refined = [mission(CONFIG["scenarios"][i],length,n=81)[2]["total"]["effective_kWh"]
               for i,length in ((0,120),(1,300))]
    checks = dict(cross_trim_thrust_error_N=cross, original_M01_effective_kWh_error=base_error,
                  integration_41_vs_81_kWh=[abs(refined[i]-summary[key]["total"]["effective_kWh"])
                                            for i,key in enumerate(("M01","M02"))],
                  max_scaled_residual_all_missions=max(r["max_scaled_residual"] for rs in traces.values() for r in rs),
                  mission_points=sum(len(rs) for rs in traces.values()))
    assert cross<1e-8 and base_error<1e-8 and max(checks["integration_41_vs_81_kWh"])<1e-6
    assert all(r["trim_status"]=="FEASIBLE" for rs in traces.values() for r in rs)
    assert all(abs(summary[k]["total"]["distance_m"]-(300000 if k.endswith("-300") or k=="M02" else 120000))<1e-7 for k in summary)
    assert all(t["total"]["effective_kWh"] is not None for t in summary.values())
    assert [r["trim_status"] for r in extreme[-2:]]==["OUTSIDE_SCREEN","NO_TRIM_FOUND"]
    limits, limited_traces = static_limits(traces)
    assert all(r["max_deficit_N"]>0 for r in limits.values())
    with (out/"propulsion_requirements.csv").open("w",newline="",encoding="utf-8") as stream:
        fields = [*traces["M01"][0], "assumed_thrust_cap_N", "thrust_cap_deficit_N", "static_cap_status"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(r for rows in traces.values() for r in rows)
        writer.writerows(limited_traces)
        writer.writerows(extreme)
    report=dict(baseline=CONFIG["main"], version=CONFIG["status"], missions=summary,
                extremes=extreme, static_thrust_limits=limits, gust=CONFIG["gust_candidate"],
                checks=checks)
    (out/"results.json").write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
                                    encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=ROOT/"reproduced")
    main(parser.parse_args().out)
