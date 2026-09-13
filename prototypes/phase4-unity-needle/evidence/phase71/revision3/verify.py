#!/usr/bin/env python3
"""Verify captured evidence; reject blank frames and inconsistent science/cameras."""
from pathlib import Path
from PIL import Image,ImageChops
import json,subprocess,hashlib
P=Path(__file__).resolve().parent
read=lambda n:json.loads((P/n).read_text())
result={'protected':json.loads(subprocess.check_output(['python3',str(P.parents[2]/'scripts/verify-phase71.py')],text=True))}
keys=['stateId','recordUTC','SI','prediction','protocol','contractSha256','activeMaps','solarActivity','surfaceGuideMaps','cameraPosition','scale','layer']
for view in ['full','close']:
 before=read(f'before-{view}.json');after=read(f'after-{view}.json')
 for k in keys:assert before['after'][k]==after['after'][k],(view,k)
 for c in [before,after]:
  for snap in c['snapshots']:
   for k in keys:assert snap[k]==c['after'][k],(view,k)
  assert c['after']['errors']==[]
 probes=[]
 for prefix in ['before','after']:
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate','-of','json',str(P/f'{prefix}-{view}.webm')],text=True))['streams'][0];probes.append(probe)
 assert probes[0]==probes[1]
 result[view]={'sameScienceAndCamera':True,'video':probes[0],'distance':after['after']['cameraDistance'],'recordedSecondsOfSurfaceTime':after['after']['illustrativeTime']}
result['exactPixels']={}
for a,b in [(f'forward-{d}',f'reverse-{d}')for d in ['24','25','28','29','30']]+[(n+'-a',n+'-b')for n in ['paused','magnetogram','bplus','bminus']]:
 im1=Image.open(P/(a+'.png'));im2=Image.open(P/(b+'.png'))
 assert im1.getbbox() is not None and im2.getbbox() is not None, 'Blank frame'
 maximum=max(hi for lo,hi in ImageChops.difference(im1,im2).getextrema());assert maximum==0,(a,b,maximum)
 result['exactPixels'][a+' / '+b]=maximum
for name in ['before','after']:
 d=read('performance-'+name+'.json');assert d['sample']['status']=='completed';result['performance-'+name]=d['sample']
assert read('performance-before.json')['sample']['cameraPosition']==read('performance-after.json')['sample']['cameraPosition']
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-of','json',str(P/'comparison-18s.mp4')],text=True))
assert float(probe['format']['duration'])==18.0
result['comparison']=probe['format'];result['comparison']['sha256']=hashlib.sha256((P/'comparison-18s.mp4').read_bytes()).hexdigest()
result['physicalAR']='not_tested';result['visualAcceptance']='pending_user_review'
(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
