#!/usr/bin/env python3
"""Independent direct-BEMT check at coefficient-map interpolation midpoints."""
import argparse,csv,json
from pathlib import Path
import study
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--map',default=str(ROOT/'propeller_map.csv'));ap.add_argument('--out',default=str(ROOT/'verification_interpolation.json'));args=ap.parse_args()
rows=list(csv.DictReader(Path(args.map).open(newline='')))
reports=[]
for c in study.configurations():
    q=[r for r in rows if r['candidate_id']==c['id'] and r['map_valid']=='True']
    mid=(float(q[len(q)//2]['J'])+float(q[len(q)//2+1]['J']))/2
    interp=study.lerp_map([dict(J=float(r['J']),CT=float(r['CT']),CQ=float(r['CQ']),CP=float(r['CP']),alpha_min_deg=float(r['alpha_min_deg']),alpha_max_deg=float(r['alpha_max_deg']),a75=0,ap75=0,a_tip=0,ap_tip=0,W75_nd=0,valid=True) for r in q],mid)
    direct=study.bemt(c,mid)
    reports.append({'candidate':c['id'],'J_midpoint':mid,'direct_valid':direct['valid'],
        'CT_abs_error':abs(interp['CT']-direct['CT']),'CQ_abs_error':abs(interp['CQ']-direct['CQ']),
        'eta_abs_error':abs(interp['eta']-direct['eta']), 'direct_CT':direct['CT'],'interpolated_CT':interp['CT'],
        'direct_CQ':direct['CQ'],'interpolated_CQ':interp['CQ']})
result={'checks':reports,'max_CT_abs_error':max(x['CT_abs_error'] for x in reports),'max_CQ_abs_error':max(x['CQ_abs_error'] for x in reports),'max_eta_abs_error':max(x['eta_abs_error'] for x in reports),'pass':all(x['direct_valid'] for x in reports)}
Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
