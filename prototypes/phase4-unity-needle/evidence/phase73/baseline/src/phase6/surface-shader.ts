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
// Irregular cell interiors and narrow, filtered lanes. Object-space evaluation
// has no UV seam or polar stretching. Sizes and motion are decorative, not km/s.
float solarGranules(vec3 p,float time) {
  vec3 tile=floor(p),f=fract(p);float nearest=9.0,second=9.0;
  for(int z=-1;z<=1;z++)for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
    vec3 offset=vec3(float(x),float(y),float(z));
    vec3 h=solarHash3(tile+offset+vec3(uSurfaceSeed));
    vec3 center=.5+(h-.5)*.82+.075*sin(time*mix(.16,.29,h.z)+h*6.2831853);
    vec3 r=offset+center-f;float d=dot(r,r);
    second=min(second,max(nearest,d));nearest=min(nearest,d);
  }
  float footprint=length(fwidth(p));
  float lane=smoothstep(.0,.34+footprint*.10,second-nearest);
  float interior=exp(-3.3*nearest);
  float cell=.78*interior+.22*lane;
  return mix(.46,cell,1.0-smoothstep(.65,1.65,footprint));
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
  vec3 p=n*78.0+vec3(flow*.45,uSurfaceSeed*.17);
  p+=.55*vec3(solarNoise(n*153.0),solarNoise(n.yzx*157.0+vec3(7.1)),solarNoise(n.zxy*149.0+vec3(19.3)));
  float granules=solarGranules(p,uIllustrationTime);
  vec3 q=n.yzx*410.0+vec3(-flow.yx*.6,t*.10);
  float fine=(solarNoise(q)-.5)*(1.0-smoothstep(.65,1.8,length(fwidth(q))));
  // Restrained large-scale contrast, resolved granular detail and quieter cores.
  float quiet=.88+.16*fine+.18*(broad-.5)
    +.075*log2(max(.04,decorationLuma)/.34);
  vec3 photosphere=mix(vec3(.53,.205,.047),vec3(1.0,.53,.18),granules)*quiet;
  // Scalar attenuation avoids spurious blue/green colors from dividing the
  // original golden RGB channels. Both shoulders retain their warm polarity cue.
  float attenuation=pow(clamp(anchoredRatio.r,.018,1.35),.96);
  vec3 polarityTint=mix(vec3(1.0,.30,.10),vec3(1.0,.63,.22),plus/max(.0001,plus+minus));
  photosphere=mix(photosphere,polarityTint*quiet,guide*.14);
  diffuseColor.rgb=photosphere*attenuation;
  // Preserve textured shoulders instead of flat black cut-outs. The same
  // bounded transfer is used for every date; it never reads SI or GOES events.
  diffuseColor.rgb*=1.0+.06*fine*(1.0-.75*dark)*(1.0-.5*guide);
`;
