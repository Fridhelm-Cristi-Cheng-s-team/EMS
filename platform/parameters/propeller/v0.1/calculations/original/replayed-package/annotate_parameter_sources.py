#!/usr/bin/env python3
"""Add explicit A-side source classes and status labels to generated parameter JSON."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'propeller_parameters.json')
j=json.loads(p.read_text())
classes={
 'D_m':'SYNTHETIC','P_over_D':'SYNTHETIC','blade_count':'SYNTHETIC','hub_radius_ratio':'SYNTHETIC',
 'chord_root_m':'SYNTHETIC','chord_tip_m':'SYNTHETIC','pitch_model':'SYNTHETIC',
 'rpm_candidate_range':'ASSUMED','blade_areal_mass_kg_m2':'ASSUMED','hub_mass_kg':'ASSUMED','installation_mass_kg':'ASSUMED',
 'R_m':'CALCULATED','pitch_m':'CALCULATED','hub_diameter_m':'CALCULATED','disk_area_m2':'CALCULATED',
 'blade_mass_kg':'CALCULATED','propeller_mass_kg':'CALCULATED','J_prop_kg_m2':'CALCULATED',
 'installation.application_point_O_relative_m':'REFERENCE-DERIVED','installation.aircraft_axis_installation_angle_deg':'REFERENCE-DERIVED',
 'mechanical_rpm_limit':'TBD','clearance':'TBD','full_scale_performance_map':'TBD','windmill_map':'TBD','J_motor':'TBD','J_other':'TBD'
}
for c in j['candidates']:
 for key in ('source_class_by_parameter','status_by_parameter','derivation_basis'): c.pop(key,None)
 c['source_class_by_parameter']=classes
 c['derivation_basis']={'pitch_m':'D_m × P_over_D','blade_mass_kg':'assumed 10 kg/m² × computed planform','propeller_mass_kg':'blade mass + assumed hub mass','J_prop_kg_m2':'integrated assumed blade areal mass and solid-disk assumed hub'}
 c['status_by_parameter']={k:('TBD' if v=='TBD' else 'PROPOSED / NOT FROZEN') for k,v in classes.items()}
p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
