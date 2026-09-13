export const LAYERS = ['solar', 'magnetogram', 'bplus', 'bminus'];
export function validateState(data) {
  if (data?.schema_version !== 'auralis.phase5.v1' || data.contract_schema_version !== '1.0.0') throw new Error('Versión de datos no compatible.');
  const s = data.state;
  if (s?.id !== 'hmi-2022-03-24' || s.order !== 1 || s.observation?.id !== s.id+'-observation') throw new Error('La publicación no contiene el primer estado autorizado.');
  if (s.observation.time.record_utc !== '2022-03-24T00:00:53.000Z') throw new Error('Tiempo de observación inesperado.');
  if (!Number.isFinite(s.observation.target_si.value) || !Number.isFinite(s.coronium_results.prediction_si)) throw new Error('SI ausente o inválido.');
  if (s.coronium_results.protocol !== 'deterministic_onnx_cpu_eval_batch1_threads4_no_noise_no_mc') throw new Error('Protocolo de predicción inesperado.');
  if (s.coronium_results.grad_cam.status !== 'not_available' || s.observation.region_context.wcs !== null || s.observation.region_context.region_mask !== null || s.observation.region_context.magnetic_field_3d !== null || data.visual.data_projection !== 'none') throw new Error('El contrato espacial de esta fase cambió.');
  const p = s.derived.polarity;
  if (p.channel_order.join(',') !== 'B_plus,B_minus_magnitude' || p.b_plus_mean < 0 || p.b_minus_magnitude_mean < 0) throw new Error('Canales de polaridad inválidos.');
  for (const name of LAYERS.slice(1)) {
    const layer = data.layers?.[name];
    if (layer?.url !== `./assets/${name}.png` || !/^[0-9a-f]{64}$/.test(layer.sha256) || layer.origin !== 'upper_left_array_row0' || layer.width !== 512 || layer.height !== 512) throw new Error('Referencia 2D inválida.');
  }
  return data;
}
export function checkedLayer(name) { if (!LAYERS.includes(name)) throw new Error('Capa desconocida.'); return name; }
export function clampScale(value) { if (!Number.isFinite(value)) throw new Error('Escala inválida.'); return Math.min(1.5,Math.max(.4,value)); }
export async function digest(bytes) { return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join(''); }
export async function verifyExport(bytes, evidence, stateBytes) {
  const view = new DataView(bytes);
  if (bytes.byteLength < 20 || view.getUint32(0,true)!==0x46546c67 || view.getUint32(4,true)!==2 || view.getUint32(8,true)!==bytes.byteLength) throw new Error('No se recibió un GLB válido.');
  if (evidence.scene !== 'Assets/Scenes/Phase5Solar.unity' || evidence.unityVersion !== '6000.3.17f1' || evidence.exporterVersion !== '5.1.12' || evidence.bytes !== bytes.byteLength || await digest(bytes)!==evidence.sha256 || await digest(stateBytes)!==evidence.stateSha256) throw new Error('La escena, sus datos y la evidencia Unity no coinciden.');
}
