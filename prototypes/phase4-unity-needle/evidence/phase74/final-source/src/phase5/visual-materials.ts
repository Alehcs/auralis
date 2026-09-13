import {surfaceUniforms,surfaceTransfer} from '../phase6/surface-shader';
import {SURFACE_SEED} from '../phase6/surface-motion.mjs';
import { Mesh, Object3D, Vector3, type Material, type Texture } from 'three';

// Extend the materials of the Unity GLB; geometry and baked assets stay in Unity.
// Quick Look keeps the baked material and the original linear scientific maps.
export function polishMaterials(root:Object3D, temporal=false) {
  const guidePlus={value:null as Texture|null},guideMinus={value:null as Texture|null},guideDisk={value:new Vector3()},seed={value:SURFACE_SEED};
  const time={value:0}, gain={value:1},fade={value:1};
  // Original observation-free Unity illustration; HMI atlases retain their UVs.
  const decoration={value:null as Texture|null};
  const solarFrom={value:null as Texture|null},solarTo={value:null as Texture|null},solarMix={value:1};
  root.traverse(o=>{
    if(!(o instanceof Mesh))return;
    const solar=o.name==='IllustrativeSphere', scientific=o.name.startsWith('Layer_');
    if(temporal&&o.name==='SubtleCorona'){
      for(const material of Array.isArray(o.material)?o.material:[o.material]){
        material.customProgramCacheKey=()=> 'auralis-corona-v74';
        material.onBeforeCompile=(shader:Parameters<Material['onBeforeCompile']>[0])=>{
          shader.uniforms.uStateFade=fade;
          shader.fragmentShader='uniform float uStateFade;\n'+shader.fragmentShader;
          // Same Unity plane/texture, with a thinner falloff and broad irregularity.
          // Decorative halo only; no atmospheric structure reconstructed from HMI.
          shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#ifdef USE_MAP
            vec4 bakedCorona=texture2D(map,vMapUv);
            float radius=length(vMapUv*2.0-1.0);
            float edge=max(0.0,radius-.70);
            float outside=smoothstep(.700,.716,radius);
            float cutoff=1.0-smoothstep(.94,1.0,radius);
            float innerGlow=exp(-edge*95.0);
            float diffuseGlow=exp(-edge*14.0);
            diffuseColor.rgb*=mix(vec3(1.0,.17,.009),vec3(1.0,.52,.085),innerGlow);
            float angle=atan(vMapUv.y-.5,vMapUv.x-.5);
            float irregular=.88+.07*sin(3.0*angle+.4)+.05*sin(5.0*angle-1.7);
            diffuseColor.a*=(.42*innerGlow+.14*diffuseGlow+.12*bakedCorona.a)*outside*cutoff*irregular;
          #endif`);
          shader.fragmentShader=shader.fragmentShader.replace('#include <colorspace_fragment>','#include <colorspace_fragment>\ngl_FragColor.a*=uStateFade;');
        };
        material.needsUpdate=true;
      }
    }
    if(!solar&&!scientific)return;
    for(const material of Array.isArray(o.material)?o.material:[o.material]) {
      if(solar&&temporal)decoration.value=(material as Material&{map:Texture}).map;
      material.toneMapped=false;
      material.customProgramCacheKey=()=>solar?(temporal?'auralis-solar-motion-v74':'auralis-solar-polish-v1'):'auralis-data-display-'+o.name;
      material.onBeforeCompile=(shader:Parameters<Material['onBeforeCompile']>[0])=>{
        shader.uniforms.uIllustrationTime=time;shader.uniforms.uDisplayGain=gain;shader.uniforms.uStateFade=fade;
        shader.fragmentShader='uniform float uStateFade;\n'+shader.fragmentShader;
        if(solar){
          shader.uniforms.uSolarFrom=solarFrom;shader.uniforms.uSolarTo=solarTo;shader.uniforms.uSolarMix=solarMix;
          if(temporal){
            shader.uniforms.uDecoration=decoration;
            shader.uniforms.uGuidePlus=guidePlus;shader.uniforms.uGuideMinus=guideMinus;shader.uniforms.uGuideDisk=guideDisk;shader.uniforms.uSurfaceSeed=seed;
            shader.fragmentShader=surfaceUniforms+shader.fragmentShader;
            shader.vertexShader='varying vec3 vSolarLocal;\n'+shader.vertexShader;
            shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvSolarLocal=position;');
          }
          if(temporal)shader.fragmentShader='uniform sampler2D uSolarFrom; uniform sampler2D uSolarTo; uniform float uSolarMix;\n'+shader.fragmentShader;
          shader.vertexShader='varying vec3 vSolarNormal; varying vec3 vSolarView;\n'+shader.vertexShader;
          shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nvSolarNormal = normalize(normalMatrix * normal); vSolarView = -mvPosition.xyz;');
          shader.fragmentShader='uniform float uIllustrationTime; varying vec3 vSolarNormal; varying vec3 vSolarView;\n'+shader.fragmentShader;
          shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',temporal?`#ifdef USE_MAP
            diffuseColor *= texture2D(map,vMapUv);
            ${surfaceTransfer}
          #endif`:`#ifdef USE_MAP
            vec2 flowUv=vMapUv;
            float pole=sin(clamp(flowUv.y,0.0,1.0)*3.14159265);
            flowUv.x+=uIllustrationTime*.00010;
            flowUv.y+=pole*pole*.00065*sin(flowUv.x*31.4159265+uIllustrationTime*.12);
            diffuseColor*=texture2D(map,flowUv);
          #endif`);
          shader.fragmentShader=shader.fragmentShader.replace('#include <colorspace_fragment>',`#include <colorspace_fragment>
            float mu=clamp(dot(normalize(vSolarNormal),normalize(vSolarView)),0.0,1.0);
            float limb=${temporal?'.30+.70*pow(mu,.52)':'.53+.47*pow(mu,.40)'};
            gl_FragColor.rgb*=limb;
            gl_FragColor.rgb+=${temporal?'vec3(.10,.028,.002)*pow(1.0-mu,18.0)':'vec3(.09,.035,.006)*pow(1.0-mu,9.0)'};
            gl_FragColor.rgb*=uStateFade;
          `);
        }else{
          // Apply display transfer in sRGB after output conversion, matching CSS
          // contrast/brightness on the reference PNG. No source pixels change.
          shader.fragmentShader='uniform float uDisplayGain;\n'+shader.fragmentShader;
          const center=o.name==='Layer_magnetogram'?'.5':'0.0';
          shader.fragmentShader=shader.fragmentShader.replace('#include <colorspace_fragment>',`#include <colorspace_fragment>\ngl_FragColor.rgb=clamp((gl_FragColor.rgb-${center})*uDisplayGain+${center},0.0,1.0)*uStateFade;`);
        }
      };
      material.needsUpdate=true;
    }
  });
  return {time,gain,fade,solarFrom,solarTo,solarMix,guidePlus,guideMinus,guideDisk,seed,decoration,
    dispose(){decoration.value?.dispose();decoration.value=null;}};
}
