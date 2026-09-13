// A separate display manifest extends, but never rewrites, the frozen Phase6 data.
export function validateActivity(a, sequence, sequenceHash, glbHash) {
  if(a?.schema_version!=='auralis.phase61.v1'||a.sequence_sha256!==sequenceHash||a.contract_sha256!==sequence.contract_sha256||a.glb?.sha256!==glbHash||a.entries?.length!==5)throw Error('Procedencia de la actividad 3D incorrecta.');
  for(const [i,e] of a.entries.entries()){
    const original=sequence.entries[i],s=e.solar,d=e.disk;
    if(e.id!==original.state.id||e.source_sha256!==original.source.sha256||s?.url!==`/phase6/assets/${e.id}/solar-activity.png`||!/^[a-f0-9]{64}$/.test(s.sha256)||s.width!==2048||s.height!==1024||s.origin!=='gltf_uv_top_left'||s.kind!=='magnetic_activity_recreation')throw Error('El estado solar no corresponde al magnetograma.');
    if(!d||![d.cx,d.cy,d.radius,d.edge_residual_p95_px,d.edge_residual_max_px].every(Number.isFinite)||d.radius<245||d.radius>256||d.edge_residual_max_px>=2)throw Error('Geometría del disco incorrecta.');
  }
  return a;
}
