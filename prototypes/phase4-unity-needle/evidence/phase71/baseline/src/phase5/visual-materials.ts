import { Mesh, Object3D, type Material, type Texture } from 'three';

// Extend the materials of the Unity GLB; geometry and baked assets stay in Unity.
// Quick Look keeps the baked material and the original linear scientific maps.
export function polishMaterials(root:Object3D, temporal=false) {
  const time={value:0}, gain={value:1},fade={value:1};
  const solarFrom={value:null as Texture|null},solarTo={value:null as Texture|null},solarMix={value:1};
  root.traverse(o=>{
    if(!(o instanceof Mesh))return;
    const solar=o.name==='IllustrativeSphere', scientific=o.name.startsWith('Layer_');
    if(!solar&&!scientific)return;
    for(const material of Array.isArray(o.material)?o.material:[o.material]) {
      material.toneMapped=false;
      material.customProgramCacheKey=()=>solar?(temporal?'auralis-solar-activity-v1':'auralis-solar-polish-v1'):'auralis-data-display-'+o.name;
      material.onBeforeCompile=(shader:Parameters<Material['onBeforeCompile']>[0])=>{
        shader.uniforms.uIllustrationTime=time;shader.uniforms.uDisplayGain=gain;shader.uniforms.uStateFade=fade;
        shader.fragmentShader='uniform float uStateFade;\n'+shader.fragmentShader;
        if(solar){
          shader.uniforms.uSolarFrom=solarFrom;shader.uniforms.uSolarTo=solarTo;shader.uniforms.uSolarMix=solarMix;
          if(temporal)shader.fragmentShader='uniform sampler2D uSolarFrom; uniform sampler2D uSolarTo; uniform float uSolarMix;\n'+shader.fragmentShader;
          shader.vertexShader='varying vec3 vSolarNormal; varying vec3 vSolarView;\n'+shader.vertexShader;
          shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nvSolarNormal = normalize(normalMatrix * normal); vSolarView = -mvPosition.xyz;');
          shader.fragmentShader='uniform float uIllustrationTime; varying vec3 vSolarNormal; varying vec3 vSolarView;\n'+shader.fragmentShader;
          shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',temporal?`#ifdef USE_MAP
            diffuseColor *= mix(texture2D(uSolarFrom,vMapUv),texture2D(uSolarTo,vMapUv),uSolarMix);
          #endif`:`#ifdef USE_MAP
            vec2 flowUv=vMapUv;
            float pole=sin(clamp(flowUv.y,0.0,1.0)*3.14159265);
            flowUv.x+=uIllustrationTime*.00010;
            flowUv.y+=pole*pole*.00065*sin(flowUv.x*31.4159265+uIllustrationTime*.12);
            diffuseColor*=texture2D(map,flowUv);
          #endif`);
          shader.fragmentShader=shader.fragmentShader.replace('#include <colorspace_fragment>',`#include <colorspace_fragment>
            float mu=clamp(dot(normalize(vSolarNormal),normalize(vSolarView)),0.0,1.0);
            float limb=.53+.47*pow(mu,.40);
            gl_FragColor.rgb*=limb;
            gl_FragColor.rgb+=vec3(.09,.035,.006)*pow(1.0-mu,9.0);
            ${temporal?'':'gl_FragColor.rgb*=uStateFade;'}
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
  return {time,gain,fade,solarFrom,solarTo,solarMix};
}
