// Presentation-only detail on the real Unity sphere. HMI atlas and guide UVs
// remain fixed; no displacement of observations, vertices or magnetic regions.
export const surfaceUniforms = /* glsl */`
uniform float uSurfaceSeed;
uniform sampler2D uGuidePlus;
uniform sampler2D uGuideMinus;
uniform sampler2D uDecoration;
uniform vec3 uGuideDisk;
varying vec3 vSolarLocal;
float solarHash(vec3 p) {
  p=fract(p*.1031); p+=dot(p,p.yzx+33.33);
  return fract((p.x+p.y)*p.z);
}
float solarNoise(vec3 p) {
  vec3 i=floor(p), f=fract(p);
  f=f*f*f*(f*(f*6.0-15.0)+10.0);
  return mix(mix(mix(solarHash(i),solarHash(i+vec3(1,0,0)),f.x),
                 mix(solarHash(i+vec3(0,1,0)),solarHash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(solarHash(i+vec3(0,0,1)),solarHash(i+vec3(1,0,1)),f.x),
                 mix(solarHash(i+vec3(0,1,1)),solarHash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
vec3 solarHash3(vec3 p) {
  return vec3(solarHash(p),solarHash(p+vec3(19.7,3.1,7.9)),solarHash(p+vec3(3.7,31.1,13.3)));
}
// Continuous cellular detail: per-cell radii vary, but brightness never switches
// abruptly to a nearest cell's ID. Smooth domain warping supplies larger clusters.
// Filtering is applied after the nonlinear palette below, not just to the noise.
float solarGranules(vec3 p,float time) {
  vec3 tile=floor(p),f=fract(p);float nearest=9.0,second=9.0;
  for(int z=-1;z<=1;z++)for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
    vec3 offset=vec3(float(x),float(y),float(z));
    vec3 h=solarHash3(tile+offset+vec3(uSurfaceSeed));
    vec3 center=.5+(h-.5)*.82+.045*sin(time*mix(.11,.23,h.z)+h*6.2831853);
    vec3 r=offset+center-f;float d=dot(r,r)/mix(.80,1.20,h.y);
    second=min(second,max(nearest,d));nearest=min(nearest,d);
  }
  float lane=smoothstep(.0,.48,second-nearest);
  float interior=exp(-2.8*nearest);
  return (.90*interior+.10*lane)*mix(.90,1.10,solarNoise(p*.43));
}
vec3 solarPalette(float level) {
  vec3 color=mix(vec3(.29,.039,.0025),vec3(1.0,.36,.024),smoothstep(.04,.57,level));
  return mix(color,vec3(1.0,.79,.31),smoothstep(.54,.92,level));
}
// Cached sRGB textures encode nonnegative, linear channel magnitudes.
float guideMagnitude(float c) { return c<=.0031308 ? c*12.92 : 1.055*pow(c,1.0/2.4)-.055; }
`;
export const surfaceTransfer = /* glsl */`
  vec3 n=normalize(vSolarLocal);
  vec2 guideUv=(uGuideDisk.xy+vec2(-n.x,-n.y)*uGuideDisk.z+.5)/512.0;
  float plus=guideMagnitude(texture2D(uGuidePlus,guideUv).r);
  float minus=guideMagnitude(texture2D(uGuideMinus,guideUv).r);
  float guide=smoothstep(.02,.30,plus+minus)*smoothstep(0.0,.095,-n.z);
  vec3 original=texture2D(uDecoration,vMapUv).rgb;
  // The ratio retains the baked, anchored HMI transfer while reducing the coarse
  // decorative filaments shared by the original and all five activity atlases.
  vec3 anchoredRatio=clamp((diffuseColor.rgb+.002)/(original+.002),vec3(.018),vec3(2.3));
  float dark=1.0-smoothstep(.15,.9,dot(anchoredRatio,vec3(.2126,.7152,.0722)));
  float rate=mix(.10,.19,solarNoise(n.yzx*11.0+vec3(uSurfaceSeed)));
  float t=uIllustrationTime*rate;
  vec2 flow=vec2(solarNoise(n*19.0+vec3(t,7.3,3.1)),
                 solarNoise(n.yzx*17.0+vec3(5.7,t*.81,19.1)))-.5;
  float pole=sin(clamp(vMapUv.y,0.0,1.0)*3.14159265);
  vec3 transported=texture2D(uDecoration,vMapUv+flow*vec2(.0018,.0028)*pole*pole).rgb;
  float decorationLuma=dot(transported,vec3(.2126,.7152,.0722));
  float broad=solarNoise(n*13.0+vec3(3.1,7.9,uSurfaceSeed));
  vec3 p=n*88.0+vec3(flow*.45,uSurfaceSeed*.17);
  p+=.95*vec3(solarNoise(n*23.0),solarNoise(n.yzx*29.0+vec3(7.1)),solarNoise(n.zxy*19.0+vec3(19.3)));
  float granules=solarGranules(p,uIllustrationTime);
  vec3 q=n.yzx*410.0+vec3(-flow.yx*.6,t*.10);
  float fine=(solarNoise(q)-.5)*(1.0-smoothstep(.35,1.15,length(fwidth(q))));
  // Three display scales: fine granules, intermediate mottling and restrained
  // original Unity decoration. No broad bright veins or global brightness pulse.
  float meso=solarNoise(n*33.0+vec3(flow*.35,11.7));
  vec3 detailP=n.zxy*203.0+vec3(7.1,flow*.35);
  float detail=(solarNoise(detailP)-.5)*(1.0-smoothstep(.35,1.15,length(fwidth(detailP))));
  // Lower contrast at HMI cores/shoulders integrates decoration without changing
  // the anchored attenuation or sampling neighboring observations.
  float baseLevel=.50+.20*(meso-.5);
  float level=clamp(baseLevel+.70*(granules-.46)*(1.0-.45*dark)+.09*detail+.05*fine,0.0,1.0);
  // Preserve the exact gold/amber Phase 7.3 palette. Estimate the unresolved
  // color average before blending out subpixel structure; no beige LOD fallback.
  vec3 averageColor=.25*solarPalette(baseLevel-.12)+.50*solarPalette(baseLevel)+.25*solarPalette(baseLevel+.12);
  float resolved=1.0-smoothstep(.38,1.20,length(fwidth(p)));
  vec3 photosphere=mix(averageColor,solarPalette(level),resolved);
  float originalDetail=clamp(log2(max(.04,decorationLuma)/.34),-1.4,1.4);
  photosphere*=.94+.19*(broad-.5)+.07*originalDetail;
  // Volume comes from the continuous limb law, not screen-pixel slope lighting.
  // No normals, vertices or reconstructed surface heights are introduced.
  // Keep exactly the same scalar HMI attenuation as Phase 7.2. Warming the
  // shoulders improves integration without moving, enlarging or lifting cores.
  float attenuation=pow(clamp(anchoredRatio.r,.018,1.35),.96);
  float shoulder=smoothstep(.13,.48,attenuation)*(1.0-smoothstep(.68,.98,attenuation));
  vec3 polarityTint=mix(vec3(1.0,.19,.012),vec3(1.0,.55,.095),plus/max(.0001,plus+minus));
  photosphere=mix(photosphere,polarityTint,guide*.13);
  photosphere+=vec3(.15,.055,.003)*shoulder*(.75+.25*meso);
  diffuseColor.rgb=photosphere*attenuation;
  diffuseColor.rgb*=1.0+.04*detail*(1.0-.75*dark)*(1.0-.5*guide);
`;
