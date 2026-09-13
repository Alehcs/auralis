import {surfaceUniforms,surfaceTransfer} from '../phase6/surface-shader';
import {SURFACE_SEED} from '../phase6/surface-motion.mjs';
import { Mesh, Object3D, Vector3, Vector4, type Material, type Texture } from 'three';

// Extend the materials of the Unity GLB; geometry and baked assets stay in Unity.
// Quick Look keeps the baked material and the original linear scientific maps.
export function polishMaterials(root:Object3D, temporal=false) {
  const guidePlus={value:null as Texture|null},guideMinus={value:null as Texture|null},guideDisk={value:new Vector3()},seed={value:SURFACE_SEED};
  const arcadeAnchors={value:Array.from({length:12},()=>new Vector4())},arcadeCount={value:0};
  const time={value:0}, gain={value:1},fade={value:1};
  // Original observation-free Unity illustration; HMI atlases retain their UVs.
  const decoration={value:null as Texture|null};
  const solarFrom={value:null as Texture|null},solarTo={value:null as Texture|null},solarMix={value:1};
  root.traverse(o=>{
    if(!(o instanceof Mesh))return;
    const solar=o.name==='IllustrativeSphere', scientific=o.name.startsWith('Layer_');
    if(temporal&&o.name==='SubtleCorona'){
      for(const material of Array.isArray(o.material)?o.material:[o.material]){
        material.customProgramCacheKey=()=> 'auralis-corona-v75';
        material.onBeforeCompile=(shader:Parameters<Material['onBeforeCompile']>[0])=>{
          shader.uniforms.uStateFade=fade;
          shader.fragmentShader='uniform float uStateFade;\n'+shader.fragmentShader;
          shader.uniforms.uIllustrationTime=time;
          shader.fragmentShader='uniform float uIllustrationTime;\n'+shader.fragmentShader;
          // Nested irregular falloffs on the original Unity plane. Presentation
          // rays are not reconstructed field lines or inferred coronal heights.
          shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#ifdef USE_MAP
            vec2 p=vMapUv*2.0-1.0;
            float radius=length(p);
            float angle=atan(p.y,p.x);
            float edge=max(0.0,radius-.70);
            float outside=smoothstep(.697,.707,radius);
            float cutoff=1.0-smoothstep(.93,1.0,radius);
            float t=uIllustrationTime*.045;
            float fan=.5+.5*sin(angle*11.0+1.4*sin(angle*5.0)+t);
            float rays=pow(.5+.5*sin(angle*59.0+3.0*sin(angle*13.0)+edge*47.0*sin(angle*7.0)-t),5.0);
            float fine=pow(.5+.5*sin(angle*113.0+2.0*sin(angle*23.0)+edge*63.0*sin(angle*9.0)+t*.7),9.0);
            float innerGlow=exp(-edge*125.0);
            float diffuseGlow=exp(-edge*mix(17.0,32.0,fan));
            diffuseColor.rgb=vec3(1.0,.65,.19);
            diffuseColor.a*=(.52*innerGlow+diffuseGlow*(.11+.19*fan+.09*rays+.035*fine))*outside*cutoff;
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
      material.customProgramCacheKey=()=>solar?(temporal?'auralis-solar-motion-v75':'auralis-solar-polish-v1'):'auralis-data-display-'+o.name;
      material.onBeforeCompile=(shader:Parameters<Material['onBeforeCompile']>[0])=>{
        shader.uniforms.uIllustrationTime=time;shader.uniforms.uDisplayGain=gain;shader.uniforms.uStateFade=fade;
        shader.fragmentShader='uniform float uStateFade;\n'+shader.fragmentShader;
        if(solar){
          shader.uniforms.uSolarFrom=solarFrom;shader.uniforms.uSolarTo=solarTo;shader.uniforms.uSolarMix=solarMix;
          if(temporal){
            shader.uniforms.uDecoration=decoration;shader.uniforms.uArcadeAnchors=arcadeAnchors;shader.uniforms.uArcadeCount=arcadeCount;
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
            float limb=${temporal?'.50+.50*pow(mu,.40)':'.53+.47*pow(mu,.40)'};
            gl_FragColor.rgb*=limb;
            gl_FragColor.rgb+=${temporal?'vec3(.24,.16,.035)*pow(1.0-mu,28.0)':'vec3(.09,.035,.006)*pow(1.0-mu,9.0)'};
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
  return {time,gain,fade,solarFrom,solarTo,solarMix,guidePlus,guideMinus,guideDisk,seed,decoration,arcadeAnchors,arcadeCount,
    dispose(){decoration.value?.dispose();decoration.value=null;}};
}
