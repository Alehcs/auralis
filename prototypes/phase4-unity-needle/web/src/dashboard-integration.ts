// Hosting/container adapter only. No render, scientific or temporal controller imports.
import QRCode from 'qrcode';
const states = ['24','25','28','29','30'].map(day => 'hmi-2022-03-' + day);
const requested = new URL(location.href).searchParams.get('state');
let applied = !states.includes(requested ?? ''), shared = '', last = '';
const embedded = parent !== window;
// Only the configured dashboard (or this same origin locally) receives metadata.
const dashboardOrigin = import.meta.env.VITE_DASHBOARD_ORIGIN;
const referringOrigin = document.referrer ? new URL(document.referrer).origin : location.origin;
const parentTarget = referringOrigin === location.origin || referringOrigin === dashboardOrigin ? referringOrigin : null;
function publish() {
  const diagnostic = document.getElementById('diagnostics');
  let data: Record<string, any>;
  try { data = JSON.parse(diagnostic?.textContent ?? ''); } catch { return; }
  const ready = document.getElementById('load-status')?.textContent === 'Unity → Needle · escena y recursos verificados' && data.status !== 'disposed' && data.status !== 'failed';
  if (ready && !applied) {
    applied = true;
    document.querySelector<HTMLButtonElement>(`#timeline [data-state-index="${states.indexOf(requested!)}"]`)?.click();
    return;
  }
  if (ready && !data.transitioning && states.includes(data.stateId) && shared !== data.stateId) {
    shared = data.stateId;
    const url = new URL(location.href); url.search = ''; url.hash = ''; url.searchParams.set('state', shared);
    // QR and the top-level AR launch always target this same local/deployed build.
    const share = document.getElementById('share-url') as HTMLAnchorElement;
    share.href = url.href; share.textContent = url.href;
    const launch = document.getElementById('ios-launch') as HTMLAnchorElement;
    const clip = new URL('https://appclip.needle.tools/ar'); clip.searchParams.set('url', url.href); launch.href = clip.href;
    void QRCode.toCanvas(document.getElementById('qr') as HTMLCanvasElement, url.href, {width:200,margin:2,errorCorrectionLevel:'M'}).catch(()=>{});
  }
  if (!embedded || !parentTarget) return;
  const message = { type:'auralis-viewer', status:data.status === 'failed' || data.status === 'disposed' ? 'error' : ready ? 'ready' : 'loading', state:states.includes(data.stateId) ? data.stateId : null, height:Math.ceil(document.body.getBoundingClientRect().height) };
  const serialized = JSON.stringify(message);
  if (serialized !== last) { last = serialized; parent.postMessage(message, parentTarget); }
}
const observer = new MutationObserver(publish);
for (const id of ['diagnostics','load-status']) observer.observe(document.getElementById(id)!, {childList:true,subtree:true,characterData:true});
const size = new ResizeObserver(publish); size.observe(document.body);
window.addEventListener('pagehide',()=>{observer.disconnect();size.disconnect();},{once:true});
publish();
