// Presentation-only detail on the real Unity sphere. HMI atlas and guide UVs
// remain fixed; no displacement of observations, vertices or magnetic regions.
export const surfaceUniforms = /* glsl */`
uniform float uSurfaceSeed;
uniform vec4 uArcadeAnchors[12];
uniform int uArcadeCount;
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
// Smooth, anisotropic emissive threads, filtered at the screen footprint.
// All transport is decorative object-space detail. HMI UVs remain stationary.
float solarFbm(vec3 p) {
  return .53*solarNoise(p)+.27*solarNoise(p*2.03+7.1)+.13*solarNoise(p*4.11+19.3)+.07*solarNoise(p*8.23);
}
float solarThreads(vec3 p) {
  float warp=solarNoise(p*.37+3.1);
  float phase=(p.x+1.8*solarNoise(p*.61)+warp*2.7)*6.2831853;
  float ridge=pow(.5+.5*sin(phase),7.0);
  float resolved=1.0-smoothstep(.65,2.7,fwidth(phase));
  return mix(.21,ridge,resolved);
}
vec3 solarPalette(float level) {
  vec3 color=mix(vec3(.035,.012,.0015),vec3(.27,.12,.012),smoothstep(.04,.49,level));
  color=mix(color,vec3(.80,.53,.095),smoothstep(.39,.78,level));
  return mix(color,vec3(1.0,.93,.60),smoothstep(.72,1.10,level));
}
// Cached sRGB textures encode nonnegative, linear channel magnitudes.
float guideMagnitude(float c) { return c<=.0031308 ? c*12.92 : 1.055*pow(c,1.0/2.4)-.055; }
`;
export const surfaceTransfer = /* glsl */`
  vec3 n=normalize(vSolarLocal);
  vec2 guideUv=(uGuideDisk.xy+vec2(-n.x,-n.y)*uGuideDisk.z+.5)/512.0;
  float plus=guideMagnitude(texture2D(uGuidePlus,guideUv).r);
  float minus=guideMagnitude(texture2D(uGuideMinus,guideUv).r);
  float front=smoothstep(0.0,.095,-n.z);
  float guide=smoothstep(.02,.30,plus+minus)*front;
  // Mip levels are a display envelope over the same selected HMI channels.
  // They neither alter the source maps nor introduce a new observation.
  float envelope=guideMagnitude(textureLod(uGuidePlus,guideUv,3.5).r)+guideMagnitude(textureLod(uGuideMinus,guideUv,3.5).r);
  float broadField=guideMagnitude(textureLod(uGuidePlus,guideUv,5.0).r)+guideMagnitude(textureLod(uGuideMinus,guideUv,5.0).r);
  float activityGlow=smoothstep(.018,.19,envelope)*front;
  float aura=smoothstep(.012,.10,broadField)*front;
  vec3 original=texture2D(uDecoration,vMapUv).rgb;
  vec3 anchoredRatio=clamp((diffuseColor.rgb+.002)/(original+.002),vec3(.018),vec3(2.3));
  float dark=1.0-smoothstep(.15,.9,dot(anchoredRatio,vec3(.2126,.7152,.0722)));
  float rate=mix(.09,.16,solarNoise(n.yzx*11.0+vec3(uSurfaceSeed)));
  // Only the presentation rate changes; t=0 and all spatial formulas stay exact.
  float motionTime=uIllustrationTime*1.65;
  float t=motionTime*rate;
  vec3 flow=vec3(solarNoise(n*9.0+vec3(t,7.3,3.1)),solarNoise(n.yzx*11.0+vec3(5.7,t*.81,19.1)),solarNoise(n.zxy*8.0+vec3(3.1,1.7,t*.73)))-.5;
  vec3 p=n*28.0+flow*.85;
  vec3 warp=vec3(solarFbm(p),solarFbm(p.yzx+13.1),solarNoise(p.zxy+8.7));
  float cloud=solarFbm(p+warp*1.8);
  float meso=solarFbm(n*63.0+warp*4.0+flow);
  float threads=solarThreads(n.yxz*vec3(91.,23.,27.)+warp*5.0+flow*.6);
  float fine=solarThreads(n.zxy*vec3(177.,53.,37.)+warp*7.0-flow*.8);
  float veil=solarNoise(n*8.0+vec3(17.1,uSurfaceSeed,3.7));
  float level=.34+.66*(cloud-.48)+.26*(meso-.5)+.13*threads+.06*fine;
  // Quiet channels are darker; bright woven shoulders follow the HMI envelope.
  level+=.075*aura+.14*activityGlow;
  level-=.07*smoothstep(.54,.75,veil)*(1.0-.7*aura);
  // Schematic circular filament contours through the same opposite-polarity
  // anchors as the raised arcades. This is an illustrative weave, not a field
  // solver. Contours and envelopes are fixed; only emissive texture travels.
  float arcadeLight=0.0;
  for(int i=0;i<12;i++){
    if(i>=uArcadeCount)break;
    vec4 anchor=uArcadeAnchors[i];
    vec2 pa=guideUv-anchor.xy,pb=guideUv-anchor.zw;
    float span=max(.014,length(anchor.xy-anchor.zw));
    float distanceToFeet=min(length(pa),length(pb));
    float mask=exp(-2.1*distanceToFeet/span)*(1.0-smoothstep(span*1.9,span*3.3,distanceToFeet));
    float angle=atan(pa.x*pb.y-pa.y*pb.x,dot(pa,pb));
    float phase=angle*23.0+solarNoise(n*45.0)*1.9;
    float ridge=pow(.5+.5*sin(phase),10.0);
    ridge=mix(.15,ridge,1.0-smoothstep(.8,3.5,fwidth(phase)));
    float current=.65+.35*solarNoise(n*84.0+vec3(motionTime*.20,float(i),0));
    arcadeLight+=mask*ridge*current;
  }
  arcadeLight=min(1.6,arcadeLight)*front;
  vec3 atmosphere=solarPalette(level);
  float attenuation=pow(clamp(anchoredRatio.r,.018,1.35),.96);
  float shoulder=smoothstep(.13,.48,attenuation)*(1.0-smoothstep(.68,.98,attenuation));
  vec3 polarityTint=mix(vec3(1.0,.30,.065),vec3(1.0,.76,.27),plus/max(.0001,plus+minus));
  atmosphere=mix(atmosphere,polarityTint,guide*.09);
  atmosphere+=vec3(.25,.14,.025)*shoulder*(.6+.7*meso);
  diffuseColor.rgb=atmosphere*attenuation;
  // HMI anchors remain dark; emissive filaments gather on their shoulders.
  diffuseColor.rgb+=vec3(.42,.28,.055)*arcadeLight*smoothstep(.06,.36,attenuation);
  diffuseColor.rgb+=vec3(.70,.43,.085)*activityGlow*(.065+.30*threads)*smoothstep(.035,.24,attenuation);
`;
