// Local illustrative transport. Only the original observation-free Unity texture
// is displaced. The selected activity atlas, guide UVs and vertices stay fixed.
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
// Cached sRGB textures encode linear, nonnegative channel magnitudes.
float guideMagnitude(float c) { return c<=.0031308 ? c*12.92 : 1.055*pow(c,1.0/2.4)-.055; }
`;
export const surfaceTransfer = /* glsl */`
  vec3 n=normalize(vSolarLocal);
  vec2 guideUv=(uGuideDisk.xy+vec2(-n.x,-n.y)*uGuideDisk.z+.5)/512.0;
  float plus=guideMagnitude(texture2D(uGuidePlus,guideUv).r);
  float minus=guideMagnitude(texture2D(uGuideMinus,guideUv).r);
  float guide=smoothstep(.02,.30,plus+minus)*smoothstep(0.0,.095,-n.z);

  // Bounded, non-periodic local displacement, with independently varying rates.
  // Noise is continuous in object space: no seam, whole-sphere spin or UV scroll.
  float rate=mix(.10,.24,solarNoise(n.yzx*11.0+vec3(uSurfaceSeed)));
  float t=uIllustrationTime*rate;
  vec2 flow=vec2(solarNoise(n*19.0+vec3(t,7.3,3.1)),
                 solarNoise(n.yzx*17.0+vec3(5.7,t*.81,19.1)))-.5;
  float pole=sin(clamp(vMapUv.y,0.0,1.0)*3.14159265);
  vec2 decorativeUv=vMapUv+flow*vec2(.009,.014)*pole*pole;
  vec3 original=texture2D(uDecoration,vMapUv).rgb;
  vec3 transported=texture2D(uDecoration,decorativeUv).rgb;
  // Suppress transport in anchored magnetic concentrations. No displaced atlas
  // sample is ever taken, so HMI-derived dark regions cannot travel with flow.
  vec3 detailRatio=clamp((transported+.018)/(original+.018),vec3(.40),vec3(2.4));
  diffuseColor.rgb*=mix(vec3(1.0),detailRatio,.82*(1.0-guide));

  // Fine structures reshape as well as move, at two resolved scales. The source
  // texture supplies persistent structure; this small modulation supplies life.
  vec3 p=n*140.0+vec3(flow*3.0,uSurfaceSeed*.17);
  vec3 q=n.yzx*231.0+vec3(-flow.yx*2.0,t*.21);
  float cells=solarNoise(p),fine=solarNoise(q);
  float visible=1.0-smoothstep(.65,1.8,length(fwidth(p)));
  float fineVisible=1.0-smoothstep(.65,1.8,length(fwidth(q)));
  float localLight=solarNoise(n*25.0+vec3(t*.19,7.1,-t*.13));
  diffuseColor.rgb*=1.0+((cells-.5)*.24*visible+(fine-.5)*.10*fineVisible)*(1.0-.9*guide)+guide*(localLight-.5)*.025;
  // Leave room between the quiet network and bright knots in the golden palette.
  diffuseColor.rgb*=.94/(1.0+.12*dot(diffuseColor.rgb,vec3(.2126,.7152,.0722)));
`;
