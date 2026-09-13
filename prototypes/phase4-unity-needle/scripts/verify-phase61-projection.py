#!/usr/bin/env python3
"""Independent orientation/polarity probe, without scientific source writes."""
import importlib.util, json
from pathlib import Path
import numpy as np

P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('phase61',P/'scripts/build-phase61-assets.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base=np.full((512,1024,3),180,dtype='uint8')
disk={'cx':255.5,'cy':255.5,'radius':250.0}
x=np.zeros((512,512));x[166:175,376:385]=.8
atlas,_=m.render(x,disk,base)
opposite,_=m.render(-x,disk,base)
mirrored,_=m.render(x[:,::-1],disk,base)
right=(380-255.5)/250;up=(255.5-170)/250
z=-np.sqrt(1-right*right-up*up)
col=int((np.arctan2(z,right)%(2*np.pi))/(2*np.pi)*1024)
row=int(np.arccos(up)/np.pi*512)
assert np.linalg.norm(atlas[row,col].astype(float)-180)>100
assert np.array_equal(atlas[:,:512],base[:,:512])
assert not np.array_equal(atlas,opposite)
assert not np.array_equal(atlas,mirrored)
report={'passed':True,'known_upper_right_source':[380,170],
        'projected_uv_pixel':[col,row],'front_detected':True,
        'back_unchanged':True,'sign_changes_visual_at_same_magnitude':True,
        'spatial_mirror_changes_visual_at_same_global_magnitude':True}
(P/'evidence/phase61/spatial-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
