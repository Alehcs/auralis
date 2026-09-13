#!/usr/bin/env python3
"""Read-only integrity and rendered-evidence checks for Phase 7.3."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
ROOT=P.parents[3]
def read(n):return json.loads((P/n).read_text())
def science(n):
 d=read(n+'.json');return d.get('science',d.get('before',d))
baseline=read('protected-before.json')
changed=[n for n,h in baseline.items() if not (ROOT/n).is_file() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
assert not changed,changed
checks={'protected_files_unchanged':len(baseline),'pairs':{},'exact_pixels':{},'physical_ar':'not_tested','visual_acceptance':'pending_user_review'}
keys=['stateId','recordUTC','SI','prediction','protocol','contractSha256','activeMaps','scale','layer']
for view in ['full','close','motion']:
 a,b=[science(s+'-'+view) for s in ['before','after']]
 for k in keys:assert a[k]==b[k],(view,k,a[k],b[k])
 assert a['stateId']=='hmi-2022-03-29'
 assert abs(a['cameraDistance']-b['cameraDistance'])<1e-12
 assert np.allclose(a['cameraPosition'],b['cameraPosition'],rtol=0,atol=1e-12)
 checks['pairs'][view]={'same_science_camera_scale':True,'state':a['stateId'],'camera_distance':a['cameraDistance']}
 if view!='motion':
  x,y=[np.array(Image.open(P/f'{s}-{view}.png')) for s in ['before','after']]
  assert x.shape==y.shape and x[:,:,:3].std()>10 and y[:,:,:3].std()>10
  assert not np.array_equal(x,y)
for n in ['before-motion','after-motion']:
 d=read(n+'.json');a=d['before'];assert 7.6<d['after']['illustrativeTime']-a['illustrativeTime']<8.3
 for s in d['snapshots']:
  for k in keys:assert s[k]==a[k],(n,k)
  assert np.allclose(s['cameraPosition'],a['cameraPosition'],rtol=0,atol=1e-12)
 x,y=[np.array(Image.open(P/f'{n}-frozen-{i}.png')) for i in range(2)]
 assert np.array_equal(x,y),n
 checks['exact_pixels'][n+' paused']=True
for day in [24,25,28,29,30]:
 names=[f'{order}-{day}' for order in ['forward','reverse']]
 assert all((P/(n+'.png')).exists() for n in names),names
 x,y=[np.array(Image.open(P/(n+'.png'))) for n in names]
 assert np.array_equal(x,y),day
 checks['exact_pixels'][f'date return {day}']=True
for layer in ['magnetogram','bplus','bminus']:
 names=[f'{layer}-{suffix}' for suffix in ['a','b']]
 assert all((P/(n+'.png')).exists() for n in names),names
 x,y=[np.array(Image.open(P/(n+'.png'))) for n in names]
 assert np.array_equal(x,y),layer
 checks['exact_pixels'][layer+' frozen']=True
for key in ['performance-before','performance-after']:
 if (P/(key+'.json')).exists():checks[key]=read(key+'.json')
c=read('controls.json')
assert c['forward']['stateId']=='hmi-2022-03-30' and not c['forward']['playing']
assert c['reverse']['stateId']=='hmi-2022-03-24' and not c['reverse']['playing']
assert c['externalEvent']['stateId']=='hmi-2022-03-29' and not c['externalEvent']['playing']
assert c['externalEvent']['selectedEventId']=='20220330_4220'
assert c['scale']['scale']>1 and c['scale']['stateId']=='hmi-2022-03-29'
assert c['release']['status']=='disposed' and not c['release']['canvasAttached']
assert c['retry']['status']=='ready' and c['retry']['stateId']=='hmi-2022-03-29' and c['retry']['cachedTextures']==20
assert c['surfacePaused']['illustrativeTime']>=c['surfaceRunning']['illustrativeTime']>0
assert np.array_equal(np.array(Image.open(P/'paused-a.png')),np.array(Image.open(P/'paused-b.png')))
checks['controls']='passed'
checks['responsive']=read('responsive.json')
assert checks['responsive']['actual']['width']==393 and checks['responsive']['actual']['scrollWidth']==393
checks['video']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-of','json',str(P/'comparison-motion.mp4')]))['format']
assert abs(float(checks['video']['duration'])-9)<.05
checks['passed']=True
(P/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
