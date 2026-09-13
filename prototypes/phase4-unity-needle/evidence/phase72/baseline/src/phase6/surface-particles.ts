import {BufferGeometry,Float32BufferAttribute,Points,ShaderMaterial,NormalBlending,type Mesh} from 'three';
import type {polishMaterials} from '../phase5/visual-materials';

export const PARTICLE_COUNT=96;
export const TRAIL_SAMPLES=3;

// Uniform illustrative tracers, NOT newly generated magnetic regions.
// Fibonacci placement and bounded tangential paths are identical for all dates.
export function createSurfaceParticles(sphere:Mesh,visual:ReturnType<typeof polishMaterials>){
  const positions:number[]=[],phases:number[]=[],trails:number[]=[];
  for(let i=0;i<PARTICLE_COUNT;i++){
    const y=1-2*(i+.5)/PARTICLE_COUNT,r=Math.sqrt(1-y*y),angle=i*Math.PI*(3-Math.sqrt(5))+71;
    for(let j=0;j<TRAIL_SAMPLES;j++){
      positions.push(Math.cos(angle)*r,y,Math.sin(angle)*r);
      phases.push(i*2.39996323);trails.push(j);
    }
  }
  const geometry=new BufferGeometry();
  geometry.setAttribute('position',new Float32BufferAttribute(positions,3));
  geometry.setAttribute('aPhase',new Float32BufferAttribute(phases,1));
  geometry.setAttribute('aTrail',new Float32BufferAttribute(trails,1));
  const height={value:850};
  const material=new ShaderMaterial({
    transparent:true,depthWrite:false,depthTest:true,blending:NormalBlending,toneMapped:false,
    uniforms:{uTime:visual.time,uFade:visual.fade,uHeight:height,uPlus:visual.guidePlus,uMinus:visual.guideMinus,uDisk:visual.guideDisk},
    vertexShader:/* glsl */`
      attribute float aPhase; attribute float aTrail;
      uniform float uTime; uniform float uHeight;
      varying float vOpacity; varying vec3 vLocal;
      void main(){
        vec3 n=normalize(position);
        vec3 axis=abs(n.y)>.95?vec3(1,0,0):vec3(0,1,0);
        vec3 tangent=normalize(cross(axis,n)),bitangent=cross(n,tangent);
        float phase=fract(sin(aPhase*12.9898)*43758.5453);
        float speed=mix(.28,.63,phase);
        float t=uTime-aTrail*.045;
        float life=fract(uTime/mix(4.0,9.0,phase)+phase);
        float envelope=smoothstep(0.0,.25,life)*(1.0-smoothstep(.65,1.0,life));
        // Short closed circulation: no eruption, outward flight or rotation of HMI.
        vec3 drift=tangent*(.025*sin(t*speed+aPhase))
                  +bitangent*(.018*cos(t*speed*.71+aPhase*.71));
        vLocal=normalize(n+drift);
        vec4 mv=modelViewMatrix*vec4(vLocal*.4212,1.0);
        vec3 viewNormal=normalize(normalMatrix*vLocal);
        float facing=dot(viewNormal,normalize(-mv.xyz));
        vOpacity=envelope*exp(-aTrail*.85)*smoothstep(.15,.4,facing);
        gl_Position=projectionMatrix*mv;
        float objectScale=length(modelViewMatrix[0].xyz);
        gl_PointSize=clamp(.0032*objectScale*uHeight*projectionMatrix[1][1]/max(.1,-mv.z),.7,3.5);
      }`,
    fragmentShader:/* glsl */`
      uniform sampler2D uPlus; uniform sampler2D uMinus;
      uniform vec3 uDisk; uniform float uFade;
      varying float vOpacity; varying vec3 vLocal;
      float magnitude(float c){return c<=.0031308?c*12.92:1.055*pow(c,1.0/2.4)-.055;}
      void main(){
        float radius=length(gl_PointCoord-.5)*2.0;
        if(radius>1.0)discard;
        vec3 n=normalize(vLocal);
        vec2 uv=(uDisk.xy+vec2(-n.x,-n.y)*uDisk.z+.5)/512.0;
        float field=magnitude(texture2D(uPlus,uv).r)+magnitude(texture2D(uMinus,uv).r);
        float guide=smoothstep(.02,.3,field)*smoothstep(0.0,.095,-n.z);
        // Avoid painting over the anchored dark cores. Sparse tracers stay warm,
        // not neon; their position/count never depends on SI or GOES.
        float alpha=(1.0-smoothstep(.2,1.0,radius))*vOpacity*(.30-.25*guide)*uFade;
        gl_FragColor=vec4(vec3(1.0,.80,.43),alpha);
      }`,
  });
  const points=new Points(geometry,material);points.name='IllustrativeSurfaceTracers';
  points.frustumCulled=false;points.renderOrder=1;sphere.add(points);
  return {points,height,dispose(){points.removeFromParent();geometry.dispose();material.dispose();}};
}
