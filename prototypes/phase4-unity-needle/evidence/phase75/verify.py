#!/usr/bin/env python3
"""Read-only science/render evidence verification; writes only its result JSON."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
ROOT=P.parents[3]
WEB=ROOT/'prototypes/phase4-unity-needle/web'
def read(n):return json.loads((P/n).read_text())
def science(n):
 d=read(n+'.json');return d.get('science',d.get('before',d))
def pixels(n):return np.array(Image.open(P/(n+'.png')))
def equal(a,b):
 assert np.array_equal(pixels(a),pixels(b)),(a,b)
 return True
protected=read('protected-before.json')
changed=[n for n,h in protected.items() if not (ROOT/n).is_file() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
assert not changed,changed
checks={'protected_files_unchanged':len(protected),'pairs':{},'exact_pixels':{},'physical_ar':'not_tested','visual_acceptance':'user_review'}
keys=['stateId','recordUTC','SI','prediction','protocol','contractSha256','activeMaps','scale','layer']
for view in ['full','close','motion']:
 a,b=[science(s+'-'+view) for s in ['before','after']]
 for k in keys:assert a[k]==b[k],(view,k)
 assert a['stateId']=='hmi-2022-03-29' and a['pixelRatio']==b['pixelRatio']==1.5
 assert np.allclose(a['cameraPosition'],b['cameraPosition'],rtol=0,atol=1e-12)
 if view!='motion':
  assert a['illustrativeTime']==b['illustrativeTime']==0
  assert pixels('before-'+view).shape==pixels('after-'+view).shape
  assert not np.array_equal(pixels('before-'+view),pixels('after-'+view))
 checks['pairs'][view]='same HMI29, camera, scale, scientific values, DPR and presentation clock'
checks['exact_pixels']['baseline identity']=equal('before-full','before-check')
checks['exact_pixels']['final identity after restoration']=equal('after-full','final-identity')
seq=json.loads((WEB/'public/phase6/sequence.json').read_text())
counts={}
for entry in seq['entries']:
 state=entry['state'];day=int(state['id'][-2:]);obs=state['observation'];coro=state['coronium_results']
 checks['exact_pixels'][f'return {day}']=equal(f'forward-{day}',f'reverse-{day}')
 for direction in ['forward','reverse']:
  d=science(f'{direction}-{day}');arc=d['illustrativeArcades']
  assert d['stateId']==d['surfaceGuideState']==d['contextStateId']==arc['state']==state['id']
  assert d['recordUTC']==obs['time']['record_utc'] and d['SI']==obs['target_si']['value'] and d['prediction']==coro['prediction_si']
  assert d['protocol']==coro['protocol'] and d['contractSha256']==seq['contract_sha256']
  assert d['cachedTextures']==20 and not d['errors']
  assert 0<arc['regions']<=12 and arc['strands']==arc['regions']*14
  for layer,asset in entry['layers'].items():assert d['activeMaps'][layer]['sha256']==asset['sha256']
 # Check each recorded signed support against actual verified PNG channel bytes.
 channels={k:np.array(Image.open(WEB/'public'/entry['layers'][k]['url'].lstrip('/')))/255. for k in ['bplus','bminus']}
 for pair in arc['anchors']:
  for sign,channel in [('positive','bplus'),('negative','bminus')]:
   p=pair[sign];x,y=p['x'],p['y'];a=channels[channel]
   if a.ndim==3:a=a[:,:,0]
   mean=a[y-2:y+3,x-2:x+3].mean();assert abs(mean-p['value'])<1e-12
   assert mean>.065
  assert pair['positive']['value']>=.15
 counts[day]={'regions':arc['regions'],'strands':arc['strands'],'triangles':d['triangles'],'draw_calls':d['drawCalls']}
checks['HMI_signed_supports']=counts
for layer in ['magnetogram','bplus','bminus']:
 checks['exact_pixels'][layer+' frozen']=equal(layer+'-a',layer+'-b')
 checks['exact_pixels'][layer+' unchanged from 7.4']=equal('before-'+layer,layer+'-a')
for side in ['before','after']:
 m=read(side+'-motion.json');assert m['before']['illustrativeTime']==0 and m['after']['illustrativeTime']==8
 for s in m['snapshots']:
  for k in keys:assert s[k]==m['before'][k],(side,k)
 checks['exact_pixels'][side+' motion pause']=equal(side+'-motion-frozen-0',side+'-motion-frozen-1')
c=read('controls.json')
assert c['forward']['stateId']=='hmi-2022-03-30' and not c['forward']['playing']
assert c['reverse']['stateId']=='hmi-2022-03-24' and not c['reverse']['playing']
assert c['externalEvent']['stateId']=='hmi-2022-03-29' and c['externalEvent']['selectedEventId']=='20220330_4220' and not c['externalEvent']['playing']
assert c['surfaceRunning']['illustrativeTime']>0 and not c['surfacePaused']['illustrativeMotion']
assert c['scale']['scale']>1 and c['zoom']['cameraDistance']<2
assert c['orbit']['stateId']=='hmi-2022-03-29' and abs(c['orbit']['cameraPosition'][0])>.1
assert c['release']['status']=='disposed' and not c['release']['canvasAttached']
assert c['retry']['status']=='ready' and c['retry']['cachedTextures']==20 and c['retry']['illustrativeArcades']['state']=='hmi-2022-03-29'
checks['exact_pixels']['surface paused']=equal('paused-a','paused-b')
checks['controls']='forward/back, event, surface pause, zoom, scale, orbit, release/retry passed'
r=read('responsive.json');assert r['actual']['width']==r['actual']['scrollWidth']==393 and r['actual']['height']==852
assert len(r['states'])==5 and all(x['state']==x['arcades'] and x['cache']==20 and not x['errors'] for x in r['states'])
checks['responsive']=r
ar=read('ar-dom.json');assert len(ar['states'])==5 and all(x['id']==x['arcades'] for x in ar['states'])
assert ar['scale']==1.1 and ar['scientific']['layer']=='bplus' and ar['scientific']['drawCalls']==1
checks['AR_DOM']='real shared controls exercised in desktop DOM; not a physical XR session'
for side in ['before','after']:
 perf=read(side+'-performance.json');assert perf['status']=='completed' and perf['stateId']=='hmi-2022-03-29'
 checks[side+'_performance']=perf
checks['unchanged_shaders']=read('unchanged-shaders.json');assert all(checks['unchanged_shaders'].values())
assert (WEB/'dev/phase72-capture.mjs').read_bytes()==(P/'baseline/dev/phase72-capture.mjs').read_bytes()
assert not any('auralis-capture-time' in f.read_text() or 'Ver controles AR · prueba DOM' in f.read_text() for f in (WEB/'dist/assets').glob('*.js'))
checks['temporary_instrumentation_removed']=True
checks['video']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-of','json',str(P/'comparison-motion.mp4')]))['format']
assert abs(float(checks['video']['duration'])-9)<.05
assert '# pass 26' in (P/'tests.log').read_text() and 'built in' in (P/'build.log').read_text()
checks['after_performance_additional']=read('after-performance-clean.json')
checks['video_playback']=read('video-playback.json');assert checks['video_playback']['ended'] and checks['video_playback']['error'] is None
checks['final_browser_errors']=[x for x in read('browser-final-logs.json') if x['level']=='error'];assert not checks['final_browser_errors']
checks['tests']=26;checks['build']='passed'
checks['passed']=True
(P/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
