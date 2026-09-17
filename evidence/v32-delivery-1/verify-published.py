"""Non-browser HTTP checks; optional private access token is supplied only in memory."""
import hashlib,json,re,subprocess
from pathlib import Path
from urllib.parse import urljoin,urlparse
R=Path(__file__).resolve().parents[2]
SOLAR='https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site'
DASH='https://auralis-dashboard.alejandro-cornejog4.chatgpt.site'
def fetch(url,token=None):
 args=['curl','-sS','-L','--max-time','90','--write-out','\n%{http_code}\n%{url_effective}','-H','Cache-Control: no-cache']
 if token:args+=['-H','OAI-Sites-Authorization: Bearer '+token]
 res=subprocess.run(args+[url],capture_output=True)
 if res.returncode:raise RuntimeError('HTTPS probe failed with curl exit '+str(res.returncode))
 body,code,final=res.stdout.rsplit(b'\n',2)
 return int(code),final.decode(),body
def check(solar=True,token=None):
 base=SOLAR if solar else DASH
 local=R/('prototypes/phase4-unity-needle/web/dist' if solar else 'deployments/dashboard-sites/dist')
 routes=['/','/phase6/','/phase6/releases/coronium-v3.2-r1.json','/phase6/sequence.json','/phase6/activity.json'] if solar else ['/','/dashboard/','/demo/responses.json','/demo/manifest.json','/demo/predictions-v32.json']
 results=[];assets=set()
 for route in routes:
  code,url,data=fetch(base+route,token)
  assert code==200 and url.startswith(base), (route,code,url)
  html=route.endswith('/')
  if html:
   text=data.decode();assert '<!doctype html' in text.lower()
   assets.update(urlparse(urljoin(base+route,ref)).path for ref in re.findall(r'(?:src|href)="([^" ]+)"',text) if '/assets/' in urljoin(base+route,ref))
  else:
   expected=(local/route.lstrip('/')).read_bytes();assert data==expected,route
  results.append({'path':route,'status':code,'sha256':hashlib.sha256(data).hexdigest(),'exact_static_bytes':not html})
 for route in sorted(assets):
  code,url,data=fetch(base+route,token);assert data==(local/route.lstrip('/')).read_bytes(),route
  results.append({'path':route,'status':code,'sha256':hashlib.sha256(data).hexdigest(),'exact_static_bytes':True})
 out=R/'evidence/v32-delivery-1'/('public-solar-http.json' if solar else 'private-dashboard-http.json');out.write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps({'site':'solar' if solar else 'dashboard','checked':len(results),'passed':True}))
def check_assets(solar=True,token=None):
 from concurrent.futures import ThreadPoolExecutor
 base=SOLAR if solar else DASH
 local=R/('prototypes/phase4-unity-needle/web/dist' if solar else 'deployments/dashboard-sites/dist')
 files=sorted(p for p in local.rglob('*') if p.is_file() and p.suffix!='.html')
 def one(p):
  route='/'+p.relative_to(local).as_posix()
  code,url,data=fetch(base+route,token)
  assert code==200 and data==p.read_bytes(),route
  return {'path':route,'sha256':hashlib.sha256(data).hexdigest(),'status':code}
 with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(one,files))
 (R/'evidence/v32-delivery-1'/('solar-assets.json' if solar else 'dashboard-assets.json')).write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps({'site':'solar' if solar else 'dashboard','exact_assets':len(results)}))
if __name__=='__main__':
 import os
 check()
 check(False,os.environ['SITES_VERIFY_TOKEN'])

 check_assets()
 check_assets(False,os.environ['SITES_VERIFY_TOKEN'])
