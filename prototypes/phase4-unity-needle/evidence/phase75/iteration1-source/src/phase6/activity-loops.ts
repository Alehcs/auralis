import {BufferGeometry,Float32BufferAttribute,Mesh,ShaderMaterial,DoubleSide,AdditiveBlending,Vector3,type Texture} from 'three';
import type {polishMaterials} from '../phase5/visual-materials';

type Bundle={entry:any;activity:any;textures:Map<string,Texture>};
type Peak={x:number;y:number;value:number};
// This is an aesthetic construction, not a magnetic extrapolation. Its two
// anchors are sampled from opposite signed HMI concentrations, but connections,
// heights, strand counts and speeds are deliberately illustrative.
function channels(texture:Texture){
  const c=document.createElement('canvas');c.width=c.height=512;
  const ctx=c.getContext('2d',{willReadFrequently:true})!;
  ctx.drawImage(texture.image,0,0);return ctx.getImageData(0,0,512,512).data;
}
function peaks(pixels:Uint8ClampedArray,disk:{cx:number;cy:number;radius:number}){
  const candidates:Peak[]=[];
  for(let y=8;y<504;y+=3)for(let x=8;x<504;x+=3){
    if(Math.hypot(x-disk.cx,y-disk.cy)>disk.radius*.985)continue;
    let v=0;for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++)v+=pixels[((y+dy)*512+x+dx)*4]/255;
    v/=25;if(v>.065)candidates.push({x,y,value:v});
  }
  candidates.sort((a,b)=>b.value-a.value||a.y-b.y||a.x-b.x);
  const selected:Peak[]=[];
  for(const p of candidates){if(selected.every(q=>Math.hypot(p.x-q.x,p.y-q.y)>15))selected.push(p);if(selected.length===32)break;}
  return selected;
}
function geometryFor(bundle:Bundle){
  const disk=bundle.activity.disk;
  const positive=peaks(channels(bundle.textures.get('bplus')!),disk);
  const negative=peaks(channels(bundle.textures.get('bminus')!),disk);
  const positions:number[]=[],tangents:number[]=[],uv:number[]=[],phases:number[]=[],indices:number[]=[];
  const anchors:{positive:Peak;negative:Peak}[]=[];
  const direction=(p:Peak)=>{const x=-(p.x-disk.cx)/disk.radius,y=-(p.y-disk.cy)/disk.radius;return new Vector3(x,y,-Math.sqrt(Math.max(.001,1-x*x-y*y))).normalize();};
  for(const p of positive){
    const options=negative.filter(q=>{const d=Math.hypot(p.x-q.x,p.y-q.y);return d>=7&&d<72;});
    options.sort((a,b)=>b.value/(8+Math.hypot(p.x-b.x,p.y-b.y))-a.value/(8+Math.hypot(p.x-a.x,p.y-a.y)));
    const q=options[0];if(!q||anchors.some(a=>Math.hypot(a.positive.x-p.x,a.positive.y-p.y)<22))continue;
    anchors.push({positive:p,negative:q});if(anchors.length>=16)break;
  }
  for(const [region,pair] of anchors.entries()){
    const a=direction(pair.positive),b=direction(pair.negative),span=a.distanceTo(b),side=new Vector3().crossVectors(a,b).normalize();
    for(let strand=0;strand<14;strand++){
      const seed=region*17+strand*2.39996323;
      const height=Math.min(.17,span*.36)*(.50+strand/14*.85);
      const spread=(strand/13-.5)*Math.min(.065,span*.25);
      const curve=(t:number)=>{
        const arc=Math.sin(Math.PI*t);
        const n=a.clone().lerp(b,t).normalize().addScaledVector(side,spread*arc).normalize();
        return n.multiplyScalar(.421+height*Math.pow(arc,.85));
      };
      const start=positions.length/3;
      for(let i=0;i<=56;i++){
        const t=i/56,pos=curve(t),tangent=curve(Math.min(1,t+.001)).sub(curve(Math.max(0,t-.001))).normalize();
        for(const edge of [-1,1]){positions.push(...pos.toArray());tangents.push(...tangent.toArray());uv.push(t,edge);phases.push(seed);}
        if(i<56){const k=start+i*2;indices.push(k,k+1,k+2,k+1,k+3,k+2);}
      }
    }
  }
  const geometry=new BufferGeometry();
  geometry.setAttribute('position',new Float32BufferAttribute(positions,3));geometry.setAttribute('aTangent',new Float32BufferAttribute(tangents,3));
  geometry.setAttribute('uv',new Float32BufferAttribute(uv,2));geometry.setAttribute('aPhase',new Float32BufferAttribute(phases,1));geometry.setIndex(indices);
  return {geometry,anchors};
}
export function createActivityLoops(sphere:Mesh,visual:ReturnType<typeof polishMaterials>,bundles:Bundle[]){
  const cache=new Map(bundles.map(b=>[b.entry.state.id,geometryFor(b)]));
  const material=new ShaderMaterial({transparent:true,depthWrite:false,depthTest:true,side:DoubleSide,blending:AdditiveBlending,toneMapped:false,
    uniforms:{uTime:visual.time,uFade:visual.fade},
    vertexShader:/* glsl */`
      attribute vec3 aTangent; attribute float aPhase;
      uniform float uTime; varying vec2 vUv; varying float vPhase;
      void main(){
        vUv=uv;vPhase=aPhase;
        float arc=sin(uv.x*3.14159265);
        vec3 n=normalize(position);
        // Bounded sub-strand sway vanishes at both fixed HMI anchors.
        vec3 pos=position+n*(.00065*arc*sin(uv.x*9.0-uTime*.38+aPhase));
        vec4 mv=modelViewMatrix*vec4(pos,1.0);
        vec3 tangent=normalize(mat3(modelViewMatrix)*aTangent);
        vec3 across=normalize(cross(tangent,normalize(-mv.xyz)));
        float width=.00063*(.65+.35*sin(aPhase*1.7)*sin(aPhase*1.7));
        mv.xyz+=across*uv.y*width*length(modelViewMatrix[0].xyz);
        gl_Position=projectionMatrix*mv;
      }`,
    fragmentShader:/* glsl */`
      uniform float uTime; uniform float uFade; varying vec2 vUv; varying float vPhase;
      void main(){
        float crossSection=exp(-vUv.y*vUv.y*4.0);
        float ends=.35+.65*pow(sin(vUv.x*3.14159265),.32);
        float flow=.64+.36*sin(vUv.x*16.0-uTime*.9+vPhase);
        float fine=.85+.15*sin(vUv.x*43.0-uTime*.6+vPhase*2.0);
        float alpha=crossSection*ends*flow*fine*.30*uFade;
        gl_FragColor=vec4(mix(vec3(1.0,.48,.09),vec3(1.0,.91,.50),flow),alpha);
      }`});
  const mesh=new Mesh(cache.values().next().value!.geometry,material);mesh.name='IllustrativeHmiArcades';mesh.frustumCulled=false;mesh.renderOrder=2;sphere.add(mesh);
  return {mesh,select(id:string){const entry=cache.get(id);if(!entry)throw Error('Missing HMI arcade state: '+id);mesh.geometry=entry.geometry;return {state:id,regions:entry.anchors.length,strands:entry.anchors.length*14,anchors:entry.anchors};},
    dispose(){mesh.removeFromParent();material.dispose();for(const e of cache.values())e.geometry.dispose();cache.clear();}};
}
