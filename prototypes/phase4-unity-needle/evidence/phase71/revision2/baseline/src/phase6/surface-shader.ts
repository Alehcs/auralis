// Small-scale, seeded Eulerian granulation on the actual Unity sphere.
// The atlas and HMI guide coordinates are NEVER advected. Only decorative
// noise moves. No SI, event input, geometry deformation or new regions.
export const surfaceUniforms = /* glsl */`
uniform float uSurfaceSeed;
uniform sampler2D uGuidePlus;
uniform sampler2D uGuideMinus;
uniform vec3 uGuideDisk;
varying vec3 vSolarLocal;
float solarHash(vec3 p) {
  p = fract(p * .1031);
  p += dot(p, p.yzx + 33.33);
  return fract((p.x + p.y) * p.z);
}
float solarNoise(vec3 p) {
  vec3 i = floor(p), f = fract(p);
  f = f*f*f*(f*(f*6.0-15.0)+10.0);
  return mix(mix(mix(solarHash(i),solarHash(i+vec3(1,0,0)),f.x),
                 mix(solarHash(i+vec3(0,1,0)),solarHash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(solarHash(i+vec3(0,0,1)),solarHash(i+vec3(1,0,1)),f.x),
                 mix(solarHash(i+vec3(0,1,1)),solarHash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
// The cached PNGs have sRGB GPU storage, but encode linear channel magnitudes.
float guideMagnitude(float c) { return c <= .0031308 ? c*12.92 : 1.055*pow(c,1.0/2.4)-.055; }
`;
export const surfaceTransfer = /* glsl */`
  vec3 n = normalize(vSolarLocal);
  // Same array-right=-X, up=+Y and front=-Z as the verified Phase6.1 atlas.
  vec2 guideUv = (uGuideDisk.xy + vec2(-n.x,-n.y)*uGuideDisk.z + .5)/512.0;
  float plus = guideMagnitude(texture2D(uGuidePlus,guideUv).r);
  float minus = guideMagnitude(texture2D(uGuideMinus,guideUv).r);
  float guide = smoothstep(.02,.30,plus+minus)*smoothstep(0.0,.095,-n.z);
  vec3 p = n*92.0 + vec3(uSurfaceSeed*.17);
  // Bounded local circulation, not global UV rotation. Quintic noise yields
  // continuous translation and evolution, including the illustrative back.
  vec3 flow = vec3(sin(n.y*9.0+uIllustrationTime*.21),
                   cos(n.z*8.0+uIllustrationTime*.17),
                   sin(n.x*7.0-uIllustrationTime*.19)) * 1.25;
  float cells = solarNoise(p+flow);
  float fine = solarNoise(p*1.87-flow*.6+vec3(0,uIllustrationTime*.11,0));
  float localLight = solarNoise(n*18.0+vec3(uIllustrationTime*.09,0,-uIllustrationTime*.07));
  // Attenuate granulation at strong HMI concentrations; their cores stay fixed.
  float granulation = ((cells-.5)*.42+(fine-.5)*.12)*(1.0-.8*guide);
  float magneticLight = guide*(localLight-.5)*.065;
  diffuseColor.rgb *= 1.0 + granulation + magneticLight;
`;
