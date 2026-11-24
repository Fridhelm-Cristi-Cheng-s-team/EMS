"""Generate and verify the A-V3-05AR datasets from archived aircraft requirements."""
import argparse
from collections import Counter, defaultdict
import csv
from functools import lru_cache
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from model import AIR, BASELINE, GEOMETRIES, REF, TIP_SCREEN, solve, temperature, viscosity

HERE = Path(__file__).resolve().parent
GRID = np.linspace(.20, 1.30, 441)
PROP_B = GEOMETRIES[1]


def read(path):
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def csv_out(path, records):
    fields = list(dict.fromkeys(key for record in records for key in record))
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def json_out(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n")


def rows(table, **labels):
    for index in range(len(table["J"])):
        yield {**labels, **{k: a[index].item() if isinstance(a[index], np.generic) else a[index] for k, a in table.items()}}


class Map:
    fields = ("CT", "CQ", "W75_nd", "W_outer_nd", "W_max_nd", "profile_CP")

    def __init__(self, table):
        self.table = table
        self.J = table["J"]
        self.valid_pairs = table["valid"][:-1] & table["valid"][1:]
        idx = np.flatnonzero(self.valid_pairs)
        self.left, self.right = self.J[idx], self.J[idx+1]
        self.left_values = np.array([table[k][idx] for k in self.fields])
        self.slopes = (np.array([table[k][idx+1] for k in self.fields])-self.left_values)/(self.right-self.left)
        self.offset = self.left_values-self.slopes*self.left

    @property
    def validity(self):
        return [[float(self.left[part[0]]), float(self.right[part[-1]])]
                for part in np.split(np.arange(len(self.left)), np.flatnonzero(self.left[1:] != self.right[:-1])+1)
                if len(part)]

    @lru_cache(maxsize=None)
    def match(self, g, T, V, rho, h, rpm_min=None, mach_limit=TIP_SCREEN):
        D = g.D
        rpm_min = g.rpm_min if rpm_min is None else rpm_min
        if not all(math.isfinite(v) for v in (T,V,rho,h)) or V <= 0 or rho <= 0 or T <= 0:
            return dict(status="OUTSIDE_FORWARD_DOMAIN")
        temp = temperature(h)
        sound = math.sqrt(1.4*AIR*temp)
        k = 60*V/D
        scale = rho*D**4/3600
        low = np.maximum(rpm_min, k/self.right)
        high = np.minimum(g.rpm_max, k/self.left)
        active = low <= high
        if not any(active):
            return dict(status="OUTSIDE_RPM_J_DOMAIN")
        low_raw, high_raw = low.copy(), high.copy()
        # Both the geometric tip speed and the interpolated maximum local speed are screened.
        if V >= mach_limit*sound:
            return dict(status="MACH_SCREEN")
        high = np.minimum(high, 60*math.sqrt((mach_limit*sound)**2-V**2)/(math.pi*D))
        max_speed_slope = self.offset[4]*D/60
        max_speed_intercept = self.slopes[4]*V
        crossing = np.divide(mach_limit*sound-max_speed_intercept, max_speed_slope,
                             out=np.zeros_like(low), where=max_speed_slope!=0)
        high = np.where(max_speed_slope>0, np.minimum(high,crossing), high)
        low = np.where(max_speed_slope<0, np.maximum(low,crossing), low)
        active &= (low <= high) & ((max_speed_slope!=0) | (max_speed_intercept <= mach_limit*sound))
        if not any(active):
            return dict(status="MACH_SCREEN")

        # In one valid J cell CT=b+mJ means T(rpm)=scale*(b*rpm²+m*k*rpm).
        p, q = self.offset[0], self.slopes[0]*k
        vertex = np.divide(-q, 2*p, out=low.copy(), where=p!=0)
        mid = np.clip(vertex, np.minimum(low, high), np.maximum(low, high))
        def thrust(speed):
            return scale*speed*(p*speed+q)
        ta, tm, tb = thrust(low), thrust(mid), thrust(high)
        range_data = dict(
            allowed_min_thrust_N=float(np.min(np.minimum.reduce([ta,tm,tb])[active])),
            allowed_max_thrust_N=float(np.max(np.maximum.reduce([ta,tm,tb])[active])),
            allowed_min_rpm=float(low[active].min()), allowed_max_rpm=float(high[active].max()),
            rpm_map_lower_bound=float(low_raw[low_raw<=high_raw].min()),
            rpm_map_upper_bound=float(high_raw[low_raw<=high_raw].max()))
        roots = []
        for a, b, fa, fb in ((low,mid,ta,tm), (mid,high,tm,tb)):
            for idx in np.flatnonzero(active & (np.minimum(fa,fb)-1e-9 <= T) & (T <= np.maximum(fa,fb)+1e-9)):
                if abs(fa[idx]-T)<1e-9:
                    rpm = a[idx]
                elif abs(fb[idx]-T)<1e-9:
                    rpm = b[idx]
                else:
                    rpm = brentq(lambda r: scale*r*(p[idx]*r+q[idx])-T, a[idx], b[idx],
                                  xtol=1e-10, rtol=1e-14)
                if any(abs(rpm-r["rpm"])<1e-7 for r in roots):
                    continue
                j = k/rpm
                ct,cq,w75,wo,wm,profile_cp = self.offset[:,idx]+self.slopes[:,idx]*j
                n = rpm/60
                thrust_N = rho*n*n*D**4*ct
                torque = rho*n*n*D**5*cq
                power = torque*2*math.pi*n
                useful = thrust_N*V
                vi = (math.sqrt(V*V+2*thrust_N/(rho*math.pi*(D/2)**2))-V)/2
                ideal = thrust_N*(V+vi)
                if power < ideal:
                    continue
                run = next((v for v in self.validity if v[0]-1e-10 <= j <= v[1]+1e-10))
                mach_geom = math.hypot(math.pi*D*n,V)/sound
                mach_solved = wm*n*D/sound
                roots.append(dict(rpm=float(rpm), omega_rad_s=2*math.pi*n, J=j, CT=ct, CQ=cq, CP=2*math.pi*cq,
                                  thrust_N=thrust_N, Q_prop_Nm=torque, P_shaft_W=power, eta=useful/power,
                                  useful_W=useful, ideal_W=ideal, profile_W=rho*n**3*D**5*profile_cp,
                                  M_tip_geometric=mach_geom, M_outer_solved=wo*n*D/sound,
                                  M_local_max=mach_solved, Re75=rho*w75*n*D*g.D*g.chord_ratio(.75)/viscosity(temp),
                                  J_clearance=min(j-run[0],run[1]-j), RPM_upper_margin=g.rpm_max-rpm,
                                  thrust_residual_N=thrust_N-T))
        if not roots:
            if T > range_data["allowed_max_thrust_N"]:
                code = "THRUST_ABOVE_SCREENED_RANGE"
            elif T < range_data["allowed_min_thrust_N"]:
                code = "THRUST_BELOW_SCREENED_RANGE"
            else:
                code = "NO_VALID_ROOT"
            return dict(status=code, **range_data)
        best = min(roots,key=lambda r:(-r["eta"],r["rpm"]))
        alternatives = [{"rpm":r["rpm"], "eta":r["eta"], "J":r["J"]} for r in roots] if len(roots)>1 else []
        return dict(status="MATCHED", **range_data, **best, root_count=len(roots), alternatives=json.dumps(alternatives))


def inputs(row):
    return tuple(float(row[key]) for key in ("thrust_N","prop_axial_inflow_mps","rho_kg_m3","z_m"))


def classification(r):
    if r["mission"].startswith("M07"):
        return "M07_CAP_REFERENCE_UNFLOWN"
    if r["tier"]=="3":
        return "TIER3_STRESS_NO_DURATION"
    if float(r["vertical_rate_mps"]) == 5 and r["phase"]=="climb":
        return "HIGH_CLIMB_240S"
    if r["phase"]=="climb":
        return "NORMAL_CLIMB_480S"
    if r["phase"]=="cruise":
        return "CRUISE_RECORDED_DUTY"
    return "DESCENT_RECORDED_DUTY"


def combine(r, g, model):
    result = dict(source_point_id=r["point_id"], candidate_id=g.id, mission=r["mission"], phase=r["phase"],
                  tier=int(r["tier"]), duty=classification(r), trim_status=r["trim_status"],
                  repeated_scenario_note=r["occurrence"], weight_applicable=(r["tier"]!="3" and not r["mission"].startswith("M07")),
                  thrust_request_N=r["thrust_N"], V_ax_mps=r["prop_axial_inflow_mps"],
                  **{key:r[key] for key in ("phase_duration_s","quadrature_weight_s","time_s","mass_kg","z_m","rho_kg_m3",
                                            "assumed_thrust_cap_N","thrust_cap_deficit_N","static_cap_status","source")})
    if r["trim_status"]!="FEASIBLE":
        return dict(**result,status="EXCLUDED_"+r["trim_status"])
    return dict(**result,**model.match(g,*inputs(r)))


def energy(records):
    grouped = defaultdict(list)
    for r in records:
        if r["weight_applicable"]:
            grouped[r["candidate_id"], r["mission"], r["phase"]].append(r)
    missions = defaultdict(dict)
    for (candidate, mission, phase), rr in sorted(grouped.items()):
        ok = [r for r in rr if r["status"]=="MATCHED"]
        duration = float(rr[0]["phase_duration_s"])
        dt = sum(float(r["quadrature_weight_s"]) for r in rr)
        assert abs(dt-duration)<1e-8 and all(float(r["phase_duration_s"])==duration for r in rr)
        result = dict(rows=len(rr), matched=len(ok), phase_s=duration, weight_sum_s=dt, complete=len(rr)==len(ok))
        for key in ("P_shaft_W","useful_W","ideal_W","profile_W"):
            result[key.replace("_W","_kWh")] = (
                sum(r[key]*float(r["quadrature_weight_s"]) for r in ok)/3.6e6 if result["complete"] else None)
        for key in ("rpm","Q_prop_Nm","P_shaft_W"):
            result[key+"_range"]=[min(r[key] for r in ok),max(r[key] for r in ok)] if ok else None
        missions[candidate].setdefault(mission,{"phases":{}})["phases"][phase]=result
    for candidate in missions.values():
        for entry in candidate.values():
            phases = list(entry["phases"].values())
            entry["complete"] = all(p["complete"] for p in phases)
            for key in ("P_shaft_kWh","useful_kWh","ideal_kWh","profile_kWh"):
                entry[key]=sum(p[key] for p in phases) if entry["complete"] else None
            entry["eta_energy"]=entry["useful_kWh"]/entry["P_shaft_kWh"] if entry["complete"] else None
    return dict(missions)


def original_audit(original, source):
    original_map = read(original/"propeller_map.csv")
    original_matches = read(original/"propulsion_matching_results.csv")
    original_motor = read(original/"motor_requirements.csv")
    old = json.loads((original/"propeller_parameters.json").read_text())
    old_energy = json.loads((original/"mission_shaft_energy.json").read_text())
    input_snap = read(original/"inputs/propulsion_requirements.csv")
    assert input_snap==source
    index = {(r["candidate_id"],r["source_point_id"]):r for r in original_matches}
    assert len(index)==len(original_matches)==3*len(source)
    assert len(original_motor)==11567
    original_counts = Counter((r["candidate_id"],r["tier"],r["status"]) for r in original_matches)
    keys = {(r["candidate_id"],r["source_point_id"]) for r in original_motor}
    assert len(keys)==len(original_motor)
    assert keys == {k for k,r in index.items() if r["status"]=="MATCHED"}
    cross_fields=("rpm","torque_Nm","shaft_power_W","eta_prop","phase_duration_s","quadrature_weight_s","Vax_mps","T_request_N")
    assert all(all(r[k]==index[r["candidate_id"],r["source_point_id"]][k] for k in cross_fields) for r in original_motor)
    assert len(original_map)==273
    return original_map, old, old_energy, original_counts, original_matches


def compare(out, old_map, old, new_models, old_matches, matched):
    maps = []
    parity = {}
    parameter_rows = []
    points = []
    index = {(r["candidate_id"],r["source_point_id"]):r for r in old_matches}
    for g, old_g in zip(GEOMETRIES, old["candidates"], strict=True):
        ref = [r for r in old_map if r["candidate_id"]==g.id]
        j = np.array([float(r["J"]) for r in ref])
        parity_calc = solve(g,j,legacy=True)
        revised = solve(g,j)
        valid = np.array([r["map_valid"]=="True" for r in ref])
        parity[g.id]={k:float(np.max(np.abs(parity_calc[k][valid]-[float(r[k]) for r in ref if r["map_valid"]=="True"]))) for k in ("CT","CQ")}
        for i,r in enumerate(ref):
            maps.append(dict(candidate_id=g.id,J=j[i],old_valid=valid[i],revised_direct_valid=revised["valid"][i],
                             **{f"{k}_05A":r[k] for k in ("CT","CQ","CP","eta_prop")},
                             **{f"{k}_05AR":revised[k][i] for k in ("CT","CQ","CP","eta")}))
        m=g.mass()
        for name,before,after,unit in (
            ("diameter",old_g["D_m"]["value"],g.D,"m"),("pitch",old_g["pitch_m"]["value"],m["pitch_m"],"m"),
            ("blades",old_g["blade_count"],g.blades,"1"),("rpm_min",old_g["rpm_candidate_range"][0],g.rpm_min,"rpm"),
            ("rpm_max",old_g["rpm_candidate_range"][1],g.rpm_max,"rpm"),
            ("prop_mass",old_g["propeller_mass_kg"]["value"],m["prop_kg"],"kg"),
            ("install_mass",old_g["installation_mass_kg"]["value"],g.install,"kg"),
            ("J_prop",old_g["J_prop_kg_m2"]["value"],m["J_prop_kg_m2"],"kg m²"),
            ("drive_remaining",old_g["mass_budget"]["remaining_for_motor_and_other_drive_kg"],m["drive_remaining_kg"],"kg"),
            ("gyration_radius",math.sqrt(old_g["J_prop_kg_m2"]["value"]/old_g["propeller_mass_kg"]["value"]),m["gyration_radius_m"],"m"),
            ("valid_J_cells",old_g["valid_J_range"],new_models[g.id].validity,"1")):
            parameter_rows.append(dict(candidate_id=g.id,parameter=name,unit=unit,before=before,after=after))
    for r in matched:
        before = index[r["candidate_id"],r["source_point_id"]]
        points.append(dict(candidate_id=r["candidate_id"],point_id=r["source_point_id"],old_status=before["status"],
                           new_status=r["status"],old_rpm=before["rpm"],new_rpm=r.get("rpm"),
                           old_shaft_W=before["shaft_power_W"],new_shaft_W=r.get("P_shaft_W"),
                           old_tip_mach=before["tip_mach"],new_tip_mach=r.get("M_tip_geometric")))
    csv_out(out/"map_comparison.csv",maps)
    csv_out(out/"parameter_comparison.csv",parameter_rows)
    csv_out(out/"match_comparison.csv",points)
    return parity


def main(original, out):
    out.mkdir(parents=True,exist_ok=True)
    source = read(HERE/"inputs/propulsion_requirements.csv")
    assert len(source)==len({r["point_id"] for r in source})==3859
    counts=Counter((r["tier"],r["trim_status"]) for r in source)
    assert counts=={("1","FEASIBLE"):246,("2","FEASIBLE"):3608,("3","FEASIBLE"):3,
                    ("3","OUTSIDE_SCREEN"):1,("3","NO_TRIM_FOUND"):1}
    old_map, old_g, old_energy, old_counts, old_matches=original_audit(original,source)
    models = {g.id:Map(solve(g,GRID)) for g in GEOMETRIES}
    for m in models.values():
        assert m.validity
    csv_out(out/"propeller_map.csv",list(row for g in GEOMETRIES for row in rows(models[g.id].table,candidate_id=g.id)))

    matches = [combine(r,g,models[g.id]) for g in GEOMETRIES for r in source]
    ok = [r for r in matches if r["status"]=="MATCHED"]
    for r in ok:
        assert abs(r["CP"]-2*math.pi*r["CQ"])<1e-13
        assert abs(r["P_shaft_W"]-r["Q_prop_Nm"]*r["omega_rad_s"])<1e-8
        assert abs(r["thrust_residual_N"])<1e-6 and r["P_shaft_W"]>=r["ideal_W"]>r["useful_W"]>0
        assert max(r["M_tip_geometric"],r["M_local_max"])<=TIP_SCREEN+1e-10
    assert len(matches)==11577
    assert all(r["status"]=="MATCHED" for r in matches if r["tier"] in (1,2))
    assert sum(r["status"].startswith("EXCLUDED") for r in matches)==6
    csv_out(out/"propulsion_matching_results.csv",matches)
    csv_out(out/"motor_requirements_all_candidates.csv",ok)
    motor = [r for r in ok if r["candidate_id"]==PROP_B.id and not r["mission"].startswith("M07")]
    motor_fields = dict(prop_J_kg_m2=PROP_B.mass()["J_prop_kg_m2"], drive_mass_remaining_kg=PROP_B.mass()["drive_remaining_kg"],
                        acceleration_torque_status="TBD", mechanical_losses="Add separately at motor/shaft boundary; no 03AR efficiency factor",
                        load_uncertainty="SYNTHETIC_BEMT; see sensitivity_results.csv; not a confidence interval")
    csv_out(out/"motor_requirements_PROP-B.csv",[dict(**r,**motor_fields) for r in motor])
    e=energy(matches)
    assert all(len(missions)==30 and all(v["complete"] for v in missions.values()) for missions in e.values())
    json_out(out/"mission_shaft_energy.json",e)
    csv_out(out/"mission_comparison.csv",[
        dict(candidate_id=g.id,mission=mission,shaft_kWh_05A=old_energy[g.id][mission]["shaft_energy_kWh"],
             shaft_kWh_05AR=v["P_shaft_kWh"],useful_kWh=v["useful_kWh"],ideal_lower_kWh=v["ideal_kWh"],eta_05AR=v["eta_energy"])
        for g in GEOMETRIES for mission,v in e[g.id].items()])
    parity=compare(out,old_map,old_g,models,old_matches,matches)
    from checks import investigate
    evidence=investigate(out,source,matches,models,old_map,old_matches,old_energy)
    scored=Counter((r["candidate_id"],r["tier"],r["status"]) for r in matches)
    archive = json.loads((HERE/"inputs/aircraft_parameters.json").read_text())
    params = dict(baseline=BASELINE,status="PROPOSED / NOT FROZEN",recommended="PROP-B",
                  reference_conditions={"rev_per_s":REF[0],"density_kg_m3":REF[1],"temperature_K":REF[2]},
                  candidates=[dict(**g.mass(), modeled_span=[g.hub,1.], valid_J_cells=models[g.id].validity,
                                   installation_clearance="TBD", mechanical_rpm_limit="TBD") for g in GEOMETRIES],
                  installation=archive["candidates"]["P-B"]["geometry"]["prop_application_O_relative"],
                  theta_shaft_deg=1., mach_screen=TIP_SCREEN)
    json_out(out/"propeller_parameters.json",params)
    json_out(out/"results.json",dict(
        baseline=BASELINE, revised_rows=len(matches), revised_matched=len(ok), motor_PROP_B_rows=len(motor),
        original_counts=[[*k,v] for k,v in sorted(old_counts.items())],
        revised_counts=[[*k,v] for k,v in sorted(scored.items())],
        legacy_independent_max_absolute_map_delta=parity, max_residual_N=max(abs(r["thrust_residual_N"]) for r in ok),
        max_Mach=max(max(r["M_tip_geometric"],r["M_local_max"]) for r in ok),
        max_eta=max(r["eta"] for r in ok), max_root_count=max(r["root_count"] for r in ok), **evidence))
    json_out(out/"motor_duty_PROP-B.json",dict(
        status="PROPOSED / NOT FROZEN", candidate=PROP_B.id, **motor_fields,
        baseline_duty={m:e[PROP_B.id][m] for m in ("M01","M02","M03-120","M03-300")},
        stress_evidence=[r for r in matches if r["candidate_id"]==PROP_B.id and r["tier"]==3],
        mission_row_count=len(motor), duty_interpretation="Cruise dwell and 480 s/240 s climb are aircraft task loads. Thermal capability TBD; no rating."))


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--original",type=Path,default=HERE/"original_replay")
    cli.add_argument("--out",type=Path,default=HERE/"outputs")
    args=cli.parse_args()
    main(args.original,args.out)
