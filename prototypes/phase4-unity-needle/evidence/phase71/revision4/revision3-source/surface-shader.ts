// Evolving illustrative microstructure on the actual Unity sphere. No advection
// of the atlas, HMI guides, or vertices; no measured velocities or new regions.
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
// Each fixed lattice corner has its own lifetime and phase. Adjacent corners
// change independently, so interpolated structures reshape, emerge and dissolve
// locally instead of following a persistent circular path or sliding UVs.
float solarLife(vec3 corner, float time) {
  float h = solarHash(corner + vec3(19.7, 4.3, 11.9));
  float age = time / mix(3.5, 8.5, h) + h * 23.0;
  float generation = floor(age), f = fract(age);
  f = f*f*f*(f*(f*6.0-15.0)+10.0);
  vec3 offset = vec3(17.13, 31.71, 7.93);
  return mix(solarHash(corner + generation*offset),
             solarHash(corner + (generation+1.0)*offset), f);
}
float solarNoise(vec3 p, float time) {
  vec3 i = floor(p), f = fract(p);
  f = f*f*f*(f*(f*6.0-15.0)+10.0);
  return mix(mix(mix(solarLife(i,time),solarLife(i+vec3(1,0,0),time),f.x),
                 mix(solarLife(i+vec3(0,1,0),time),solarLife(i+vec3(1,1,0),time),f.x),f.y),
             mix(mix(solarLife(i+vec3(0,0,1),time),solarLife(i+vec3(1,0,1),time),f.x),
                 mix(solarLife(i+vec3(0,1,1),time),solarLife(i+vec3(1,1,1),time),f.x),f.y),f.z);
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
  vec3 p = n*105.0 + vec3(uSurfaceSeed*.17);
  vec3 detail = n.yzx*181.0 + vec3(43.7,17.2,uSurfaceSeed);
  float cells = solarNoise(p,uIllustrationTime);
  float fine = solarNoise(detail,uIllustrationTime*1.31);
  float localLight = solarNoise(n*27.0+vec3(8.3),uIllustrationTime*.38);
  // Filter unresolved detail at the limb and when zoomed out. Frequencies are
  // fixed on the sphere; zoom reveals detail rather than enlarging cell sizes.
  float cellVisibility = 1.0-smoothstep(.65,1.8,length(fwidth(p)));
  float fineVisibility = 1.0-smoothstep(.65,1.8,length(fwidth(detail)));
  float granulation = ((cells-.5)*.65*cellVisibility+(fine-.5)*.18*fineVisibility)*(1.0-.9*guide);
  float magneticLight = guide*(localLight-.5)*.035;
  diffuseColor.rgb *= 1.0 + granulation + magneticLight;
`;
