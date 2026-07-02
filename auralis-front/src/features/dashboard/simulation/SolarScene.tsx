/**
 * Interactive 3D Sun — procedural, educational rendering only.
 *
 * A plain Three.js engine (no react-three-fiber) wrapped in a React component.
 * Everything painted here (surface convection, sunspots, active regions,
 * flare-like arcs, B+/B− magnetogram patches) is procedurally generated for
 * visual explanation. It is NOT a plasma simulation, an SDO/HMI frame, or any
 * kind of forecast, and it never reads Coronium model output.
 *
 * Region/spot placement lives in the sphere's object space so features rotate
 * with the mesh. Activity class only changes visual density/intensity presets.
 *
 * Rendering notes: the surface uses domain-warped FBM for plasma-like flow;
 * per-region effects reuse noise fields precomputed once per fragment so the
 * region loop stays cheap. The corona is a camera-facing plane with animated
 * radial wisps plus a fresnel rim shell. Flare-like events combine an arc
 * (bright at the footpoints), a short-lived spark burst, and a localized
 * surface brightening fed to the sun shader through the uFlares uniform.
 */

import {
  forwardRef, useEffect, useImperativeHandle, useRef, useState,
} from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { useLanguage } from '@/lib/i18n/language-context';
import {
  ACTIVITY_PROFILES, type ActivityClass, type ActivityProfile,
} from './solarSimulationTypes';

// ---------------------------------------------------------------------------
// GLSL — Ashima 3D simplex noise (public domain) + fbm
// ---------------------------------------------------------------------------

const NOISE_GLSL = /* glsl */ `
vec3 mod289(vec3 x){ return x - floor(x * (1.0/289.0)) * 289.0; }
vec4 mod289(vec4 x){ return x - floor(x * (1.0/289.0)) * 289.0; }
vec4 permute(vec4 x){ return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v){
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
            i.z + vec4(0.0, i1.z, i2.z, 1.0))
          + i.y + vec4(0.0, i1.y, i2.y, 1.0))
          + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}

float fbm(vec3 p){
  float f = 0.0;
  float a = 0.5;
  for (int i = 0; i < 5; i++) {
    f += a * snoise(p);
    p *= 2.02;
    a *= 0.5;
  }
  return f;
}
`;

const MAX_REGIONS = 16;
const MAX_FLARES = 4;

const SUN_VERTEX = /* glsl */ `
varying vec3 vLocal;
varying vec3 vViewN;
void main(){
  vLocal = position;
  vViewN = normalMatrix * normal;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const SUN_FRAGMENT = /* glsl */ `
uniform float uTime;
uniform float uTurbulence;
uniform float uMagnetogram;
uniform float uShowSpots;
uniform float uShowRegions;
uniform float uSpotScale;
uniform float uBrightness;
uniform int uRegionCount;
uniform vec4 uRegions[${MAX_REGIONS}];   // xyz: region center (object space), w: angular radius
uniform vec4 uRegionAux[${MAX_REGIONS}]; // xyz: east tangent, w: strength
uniform vec4 uFlares[${MAX_FLARES}];     // xyz: event center, w: surface-brightening envelope

varying vec3 vLocal;
varying vec3 vViewN;

${NOISE_GLSL}

void main(){
  vec3 n = normalize(vLocal);
  float t = uTime * 0.025 * uTurbulence;
  float mu = clamp(dot(normalize(vViewN), vec3(0.0, 0.0, 1.0)), 0.0, 1.0);

  // ── Magnetogram mode: grayscale B+/B− polarity patches ──────────
  if (uMagnetogram > 0.5) {
    // Quiet-sun granular speckle (multi-scale, salt-and-pepper look)
    float g = 0.5
      + 0.055 * snoise(n * 90.0)
      + 0.040 * snoise(n * 45.0)
      + 0.025 * snoise(n * 180.0);

    // Shared noise fields for irregular, fragmented patch interiors
    float s32 = snoise(n * 32.0);
    float s50 = snoise(n * 50.0);

    for (int i = 0; i < ${MAX_REGIONS}; i++) {
      if (i >= uRegionCount) break;
      vec4 R = uRegions[i];
      vec4 A = uRegionAux[i];
      vec3 tp = normalize(R.xyz + A.xyz * R.w * 0.55);
      vec3 tm = normalize(R.xyz - A.xyz * R.w * 0.55);
      float s  = R.w * 0.40;
      float dp = acos(clamp(dot(n, tp), -1.0, 1.0));
      float dm = acos(clamp(dot(n, tm), -1.0, 1.0));
      float shapeP = 1.0 + 0.5 * s32;
      float shapeM = 1.0 - 0.5 * s32;
      float lp = exp(-pow(dp * shapeP / s, 2.4)) * (0.65 + 0.55 * s50);
      float lm = exp(-pow(dm * shapeM / s, 2.4)) * (0.65 - 0.55 * s50 * 0.4);
      g += A.w * 1.35 * (lp - lm);
    }
    g = clamp(g, 0.0, 1.0);
    g *= 0.30 + 0.70 * pow(mu, 0.8);
    gl_FragColor = vec4(vec3(g), 1.0);
    return;
  }

  // ── Visual mode: domain-warped convection + granulation ─────────
  vec3 p = n * 3.0;
  vec2 warp = vec2(
    fbm(p + vec3(0.0, t, t * 0.7)),
    fbm(p + vec3(5.2, t * 0.8, 1.3))
  );
  float cells = fbm(p * 1.4 + vec3(warp * 0.85, t * 0.5));
  float gran  = fbm(n * 16.0 + vec3(warp * 0.4, -t * 2.2));
  float grain = snoise(n * 55.0 + vec3(0.0, 0.0, t * 4.0));
  float v = 0.52 + 0.40 * cells + 0.22 * gran + 0.06 * grain;

  // Layered color ramp: dark red-brown → red → orange → yellow → near-white
  vec3 cDark = vec3(0.28, 0.05, 0.01);
  vec3 cRed  = vec3(0.62, 0.13, 0.01);
  vec3 cOr   = vec3(0.98, 0.42, 0.05);
  vec3 cYel  = vec3(1.00, 0.83, 0.44);
  vec3 cHot  = vec3(1.00, 0.96, 0.82);
  vec3 col = mix(cDark, cRed, smoothstep(0.05, 0.42, v));
  col = mix(col, cOr,  smoothstep(0.40, 0.72, v));
  col = mix(col, cYel, smoothstep(0.72, 0.98, v));
  col = mix(col, cHot, smoothstep(0.98, 1.22, v));

  // Shared noise fields, computed once and reused by every region below
  float nz26  = snoise(n * 26.0);
  float tex30 = 0.6 * snoise(n * 30.0) + 0.3 * snoise(n * 61.0);
  float wob = 1.0 + 0.42 * nz26; // irregular (non-circular) spot boundaries

  for (int i = 0; i < ${MAX_REGIONS}; i++) {
    if (i >= uRegionCount) break;
    vec4 R = uRegions[i];
    vec4 A = uRegionAux[i];
    vec3 tp = normalize(R.xyz + A.xyz * R.w * 0.55);
    vec3 tm = normalize(R.xyz - A.xyz * R.w * 0.55);
    float dp = acos(clamp(dot(n, tp), -1.0, 1.0));
    float dm = acos(clamp(dot(n, tm), -1.0, 1.0));
    float dc = acos(clamp(dot(n, R.xyz), -1.0, 1.0));

    // Slightly darker, redder shading across the whole active zone
    float zone = exp(-pow(dc / (R.w * 1.6), 2.0));
    col = mix(col, col * vec3(0.92, 0.74, 0.62), zone * 0.35 * A.w);

    if (uShowRegions > 0.5) {
      // Plage / faculae: noise-gated mottled brightening hugging the
      // footpoints instead of a smooth glowing blob
      float mask = exp(-pow(min(dp, dm) / (R.w * 0.9), 2.0))
                 + 0.6 * exp(-pow(dc / (R.w * 1.3), 2.0));
      float plage = mask * smoothstep(0.05, 0.55, tex30) * A.w;
      col += vec3(1.0, 0.78, 0.42) * plage * 0.5;
    }

    if (uShowSpots > 0.5) {
      float sr = R.w * 0.30 * uSpotScale;
      float du = min(dp, dm) * wob;
      float umbra = exp(-pow(du / (sr * 0.55), 2.6));
      float penum = exp(-pow(du / (sr * 1.25), 2.2));
      // Occasional satellite pore beside the leading spot
      vec3 bt = normalize(cross(R.xyz, A.xyz));
      vec3 sat = normalize(tp + bt * R.w * 0.5);
      float dsat = acos(clamp(dot(n, sat), -1.0, 1.0)) * wob;
      float pore = exp(-pow(dsat / (sr * 0.32), 2.6)) * step(0.35, fract(A.w * 7.31));
      umbra = max(umbra, pore * 0.9);
      col = mix(col, col * vec3(0.62, 0.50, 0.42), clamp(penum, 0.0, 1.0) * 0.85);
      col = mix(col, vec3(0.02, 0.008, 0.002), clamp(umbra, 0.0, 1.0) * 0.97);
    }
  }

  // Localized surface brightening while a flare-like event is active
  for (int i = 0; i < ${MAX_FLARES}; i++) {
    vec4 F = uFlares[i];
    if (F.w <= 0.001) continue;
    float df = acos(clamp(dot(n, F.xyz), -1.0, 1.0));
    col += vec3(1.0, 0.85, 0.6) * exp(-pow(df / 0.13, 2.0)) * F.w;
  }

  // Limb darkening + red-shifted limb + thin warm rim
  col *= 0.32 + 0.68 * pow(mu, 0.7);
  col = mix(col, col * vec3(1.0, 0.60, 0.35), pow(1.0 - mu, 2.0) * 0.5);
  col += vec3(1.0, 0.50, 0.15) * pow(1.0 - mu, 3.0) * 0.4;
  col *= uBrightness;
  gl_FragColor = vec4(col, 1.0);
}
`;

const GLOW_VERTEX = /* glsl */ `
varying float vIntensity;
void main(){
  vec3 vn = normalize(normalMatrix * normal);
  vIntensity = pow(0.72 - dot(vn, vec3(0.0, 0.0, 1.0)), 2.4);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const GLOW_FRAGMENT = /* glsl */ `
uniform vec3 uColor;
uniform float uStrength;
varying float vIntensity;
void main(){
  gl_FragColor = vec4(uColor * vIntensity * uStrength, vIntensity * uStrength);
}
`;

// Camera-facing corona plane: uneven radial falloff with slow animated wisps.
const CORONA_VERTEX = /* glsl */ `
varying vec2 vUv;
void main(){
  vUv = uv * 2.0 - 1.0;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const CORONA_FRAGMENT = /* glsl */ `
uniform float uTime;
uniform float uStrength;
varying vec2 vUv;

${NOISE_GLSL}

// Solar disc radius in plane units (sphere r=1 on a 7×7 plane → 1/3.5)
const float RD = 0.2857;

void main(){
  float r = length(vUv);
  if (r < RD * 0.85) discard;
  float ang = atan(vUv.y, vUv.x) + uTime * 0.015;
  float streak = fbm(vec3(cos(ang) * 2.4, sin(ang) * 2.4, r * 2.0 - uTime * 0.05));
  float fall = exp(-(r - RD) * 6.5);
  float ring = smoothstep(RD * 0.88, RD * 1.02, r);
  float a = clamp(ring * fall * (0.5 + 0.5 * streak) * uStrength, 0.0, 1.0);
  vec3 col = mix(vec3(1.0, 0.88, 0.60), vec3(1.0, 0.45, 0.12), clamp((r - RD) * 2.6, 0.0, 1.0));
  gl_FragColor = vec4(col * a, a);
}
`;

// Shared arc shader for loops and flare arcs: brighter and whiter toward the
// footpoints, dimmer along the apex, so arcs read as anchored to the surface.
const ARC_VERTEX = /* glsl */ `
varying vec2 vUv;
void main(){
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const ARC_FRAGMENT = /* glsl */ `
uniform vec3 uColor;
uniform float uOpacity;
varying vec2 vUv;
void main(){
  float ends = pow(abs(vUv.x - 0.5) * 2.0, 1.5);
  float foot = mix(0.35, 1.0, ends);
  vec3 col = mix(uColor, vec3(1.0, 0.97, 0.90), ends * 0.55);
  gl_FragColor = vec4(col, uOpacity * foot);
}
`;

function makeArcMaterial(color: number, opacity: number): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    vertexShader: ARC_VERTEX,
    fragmentShader: ARC_FRAGMENT,
    uniforms: {
      uColor:   { value: new THREE.Color(color) },
      uOpacity: { value: opacity },
    },
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
}

// ---------------------------------------------------------------------------
// Engine
// ---------------------------------------------------------------------------

interface Region {
  dir: THREE.Vector3;     // unit vector, object space
  tangent: THREE.Vector3; // east-west unit tangent (bipolar axis)
  radius: number;         // angular radius (rad)
  strength: number;
}

type ArcMesh = THREE.Mesh<THREE.TubeGeometry, THREE.ShaderMaterial>;

interface FlareArc {
  mesh: ArcMesh;
  dir: THREE.Vector3;
  born: number;
  life: number;
  strength: number;
}

interface SparkBurst {
  points: THREE.Points<THREE.BufferGeometry, THREE.PointsMaterial>;
  vel: Float32Array;
  born: number;
  life: number;
}

interface EngineState {
  activity: ActivityClass;
  sunspots: boolean;
  magneticRegions: boolean;
  magnetogram: boolean;
  autoRotate: boolean;
}

const CAMERA_HOME = new THREE.Vector3(0, 0.35, 3.3);

class SolarEngine {
  private container: HTMLDivElement;
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private sunGroup = new THREE.Group();
  private sunMaterial: THREE.ShaderMaterial;
  private glowMaterial: THREE.ShaderMaterial;
  private glowMesh: THREE.Mesh;
  private coronaMaterial: THREE.ShaderMaterial;
  private coronaPlane: THREE.Mesh;
  private loopsGroup = new THREE.Group();
  private flaresGroup = new THREE.Group();
  private regions: Region[] = [];
  private flares: FlareArc[] = [];
  private sparks: SparkBurst[] = [];
  private state: EngineState;
  private profile: ActivityProfile;
  private rafId: number | null = null;
  private lastFrame = performance.now();
  private elapsed = 0;
  private nextAutoFlareAt = 0;
  private resizeObserver: ResizeObserver;
  private disposed = false;
  private onVisibility = () => {
    if (document.hidden) this.stopLoop();
    else this.startLoop();
  };

  constructor(container: HTMLDivElement, initial: EngineState) {
    this.container = container;
    this.state = { ...initial };
    this.profile = ACTIVITY_PROFILES[initial.activity];

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.domElement.style.display = 'block';
    container.appendChild(this.renderer.domElement);

    this.camera = new THREE.PerspectiveCamera(
      40, container.clientWidth / Math.max(container.clientHeight, 1), 0.1, 100,
    );
    this.camera.position.copy(CAMERA_HOME);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.rotateSpeed = 0.8;
    this.controls.zoomSpeed = 0.7;
    this.controls.enablePan = false;
    this.controls.minDistance = 1.7;
    this.controls.maxDistance = 7;
    this.controls.autoRotate = initial.autoRotate;
    this.controls.autoRotateSpeed = 0.5;

    // Sun sphere
    const regionsInit = Array.from({ length: MAX_REGIONS }, () => new THREE.Vector4());
    const auxInit = Array.from({ length: MAX_REGIONS }, () => new THREE.Vector4());
    const flaresInit = Array.from({ length: MAX_FLARES }, () => new THREE.Vector4());
    this.sunMaterial = new THREE.ShaderMaterial({
      vertexShader: SUN_VERTEX,
      fragmentShader: SUN_FRAGMENT,
      uniforms: {
        uTime:        { value: 0 },
        uTurbulence:  { value: this.profile.turbulence },
        uMagnetogram: { value: initial.magnetogram ? 1 : 0 },
        uShowSpots:   { value: initial.sunspots ? 1 : 0 },
        uShowRegions: { value: initial.magneticRegions ? 1 : 0 },
        uSpotScale:   { value: this.profile.spotScale },
        uBrightness:  { value: 0.92 + 0.12 * this.profile.glowIntensity },
        uRegionCount: { value: 0 },
        uRegions:     { value: regionsInit },
        uRegionAux:   { value: auxInit },
        uFlares:      { value: flaresInit },
      },
    });
    const sunMesh = new THREE.Mesh(new THREE.SphereGeometry(1, 96, 96), this.sunMaterial);
    this.sunGroup.add(sunMesh);
    this.sunGroup.add(this.loopsGroup);
    this.sunGroup.add(this.flaresGroup);
    this.scene.add(this.sunGroup);

    // Corona: fresnel rim shell + camera-facing wispy plane
    this.glowMaterial = new THREE.ShaderMaterial({
      vertexShader: GLOW_VERTEX,
      fragmentShader: GLOW_FRAGMENT,
      uniforms: {
        uColor:    { value: new THREE.Color(1.0, 0.52, 0.16) },
        uStrength: { value: this.profile.glowIntensity },
      },
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false,
    });
    this.glowMesh = new THREE.Mesh(new THREE.SphereGeometry(1.28, 48, 48), this.glowMaterial);
    this.scene.add(this.glowMesh);

    this.coronaMaterial = new THREE.ShaderMaterial({
      vertexShader: CORONA_VERTEX,
      fragmentShader: CORONA_FRAGMENT,
      uniforms: {
        uTime:     { value: 0 },
        uStrength: { value: this.profile.glowIntensity },
      },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      depthTest: false,
    });
    this.coronaPlane = new THREE.Mesh(new THREE.PlaneGeometry(7, 7), this.coronaMaterial);
    this.coronaPlane.renderOrder = -1; // always behind the sun disc
    this.scene.add(this.coronaPlane);

    // Faint starfield backdrop
    const starCount = 450;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const v = new THREE.Vector3().randomDirection().multiplyScalar(30 + Math.random() * 25);
      starPos.set([v.x, v.y, v.z], i * 3);
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({
      color: 0x9a9a9a, size: 0.07, transparent: true, opacity: 0.55, depthWrite: false,
    }));
    this.scene.add(stars);

    this.regenerateRegions();
    this.applyMagnetogramLook();
    this.scheduleNextAutoFlare();

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    document.addEventListener('visibilitychange', this.onVisibility);

    this.startLoop();
  }

  // ── Regions / loops ───────────────────────────────────────────────

  private regenerateRegions() {
    const { regionCount, regionRadius } = this.profile;
    this.regions = [];
    for (let i = 0; i < Math.min(regionCount, MAX_REGIONS); i++) {
      // Mid-latitude bands (±10°–35°), the belt where real active regions
      // cluster — placement itself is random, purely illustrative.
      const lon = Math.random() * Math.PI * 2;
      const latDeg = (10 + 25 * Math.random()) * (Math.random() < 0.5 ? -1 : 1);
      const lat = (latDeg * Math.PI) / 180;
      const dir = new THREE.Vector3(
        Math.cos(lat) * Math.cos(lon),
        Math.sin(lat),
        Math.cos(lat) * Math.sin(lon),
      );
      const tangent = new THREE.Vector3(0, 1, 0).cross(dir).normalize();
      this.regions.push({
        dir,
        tangent,
        radius: regionRadius[0] + (regionRadius[1] - regionRadius[0]) * Math.random(),
        strength: 0.7 + 0.6 * Math.random(),
      });
    }

    const u = this.sunMaterial.uniforms;
    const regs = u.uRegions.value as THREE.Vector4[];
    const aux = u.uRegionAux.value as THREE.Vector4[];
    this.regions.forEach((r, i) => {
      regs[i].set(r.dir.x, r.dir.y, r.dir.z, r.radius);
      aux[i].set(r.tangent.x, r.tangent.y, r.tangent.z, r.strength);
    });
    u.uRegionCount.value = this.regions.length;

    this.rebuildLoops();
  }

  private rebuildLoops() {
    for (const child of [...this.loopsGroup.children]) {
      const mesh = child as ArcMesh;
      mesh.geometry.dispose();
      mesh.material.dispose();
      this.loopsGroup.remove(mesh);
    }
    const loopColor = this.state.magnetogram ? 0xd8d8d8 : 0xff9c4a;
    for (const r of this.regions) {
      const binormal = r.dir.clone().cross(r.tangent).normalize();
      const arcCount = 3;
      for (let k = 0; k < arcCount; k++) {
        const spread = 0.45 + k * 0.3;
        const tilt = (k - 1) * 0.35;
        const tp = r.dir.clone().addScaledVector(r.tangent, r.radius * spread).normalize();
        const tm = r.dir.clone().addScaledVector(r.tangent, -r.radius * spread).normalize();
        const apex = r.dir.clone()
          .multiplyScalar(1 + r.radius * (1.0 + k * 0.7) * r.strength)
          .addScaledVector(binormal, r.radius * tilt);
        const curve = new THREE.QuadraticBezierCurve3(tp, apex, tm);
        const geo = new THREE.TubeGeometry(curve, 24, 0.0038, 6);
        this.loopsGroup.add(new THREE.Mesh(geo, makeArcMaterial(loopColor, 0.5)));
      }
    }
    this.loopsGroup.visible = this.state.magneticRegions;
  }

  // ── Flare-like visual events (educational, not physical) ─────────

  triggerFlare(manual = false) {
    if (this.disposed || this.regions.length === 0) return;
    const r = this.regions[Math.floor(Math.random() * this.regions.length)];
    const mul = this.profile.flareStrength * (manual ? 1.25 : 0.7 + 0.6 * Math.random());
    const tp = r.dir.clone().addScaledVector(r.tangent, r.radius * 0.55).normalize();
    const tm = r.dir.clone().addScaledVector(r.tangent, -r.radius * 0.55).normalize();
    const apex = r.dir.clone().multiplyScalar(1 + (0.3 + Math.random() * 0.3) * mul);
    const curve = new THREE.QuadraticBezierCurve3(tp, apex, tm);
    const geo = new THREE.TubeGeometry(curve, 32, 0.010 * Math.max(mul, 0.5), 8);
    const mat = makeArcMaterial(this.state.magnetogram ? 0xffffff : 0xffb066, 0);
    const mesh = new THREE.Mesh(geo, mat);
    this.flaresGroup.add(mesh);
    this.flares.push({
      mesh, dir: r.dir.clone(), born: this.elapsed, life: 1.8 + 0.6 * mul, strength: mul,
    });
    this.spawnSparks(curve.getPoint(0.5), r.dir, mul);
  }

  private spawnSparks(origin: THREE.Vector3, dir: THREE.Vector3, mul: number) {
    const count = Math.round(20 + 28 * Math.min(mul, 2));
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos.set([origin.x, origin.y, origin.z], i * 3);
      const v = new THREE.Vector3()
        .randomDirection()
        .multiplyScalar(0.8)
        .addScaledVector(dir, 0.6)
        .normalize()
        .multiplyScalar((0.15 + 0.3 * Math.random()) * Math.max(mul, 0.6));
      vel.set([v.x, v.y, v.z], i * 3);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({
      color: this.state.magnetogram ? 0xffffff : 0xffe0b0,
      size: 0.018,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const points = new THREE.Points(geo, mat);
    this.flaresGroup.add(points);
    this.sparks.push({ points, vel, born: this.elapsed, life: 1.1 + 0.4 * Math.min(mul, 2) });
  }

  private scheduleNextAutoFlare() {
    const [min, max] = this.profile.flareIntervalMs;
    this.nextAutoFlareAt = this.elapsed + (min + Math.random() * (max - min)) / 1000;
  }

  private updateEvents(dt: number) {
    // Arcs: sine envelope on opacity, slight outward growth, footpoint
    // brightening on the surface via the uFlares uniform.
    const flareUniform = this.sunMaterial.uniforms.uFlares.value as THREE.Vector4[];
    for (let i = 0; i < MAX_FLARES; i++) flareUniform[i].set(0, 0, 0, 0);

    let pulse = 0;
    let uniformSlot = 0;
    for (let i = this.flares.length - 1; i >= 0; i--) {
      const f = this.flares[i];
      const t = (this.elapsed - f.born) / f.life;
      if (t >= 1) {
        f.mesh.geometry.dispose();
        f.mesh.material.dispose();
        this.flaresGroup.remove(f.mesh);
        this.flares.splice(i, 1);
        continue;
      }
      const env = Math.sin(Math.PI * t);
      f.mesh.material.uniforms.uOpacity.value = env * Math.min(1.0, 0.6 + 0.35 * f.strength);
      f.mesh.scale.setScalar(1 + 0.08 * t);
      if (uniformSlot < MAX_FLARES) {
        flareUniform[uniformSlot++].set(f.dir.x, f.dir.y, f.dir.z, env * 0.55 * f.strength);
      }
      pulse = Math.max(pulse, env * 0.4 * f.strength);
    }

    // Spark bursts: integrate simple ballistic motion with drag, fade out.
    for (let i = this.sparks.length - 1; i >= 0; i--) {
      const s = this.sparks[i];
      const t = (this.elapsed - s.born) / s.life;
      if (t >= 1) {
        s.points.geometry.dispose();
        s.points.material.dispose();
        this.flaresGroup.remove(s.points);
        this.sparks.splice(i, 1);
        continue;
      }
      const posAttr = s.points.geometry.getAttribute('position') as THREE.BufferAttribute;
      const arr = posAttr.array as Float32Array;
      const drag = 1 - 0.9 * dt;
      for (let j = 0; j < arr.length; j++) {
        arr[j] += s.vel[j] * dt;
        s.vel[j] *= drag;
      }
      posAttr.needsUpdate = true;
      s.points.material.opacity = Math.pow(1 - t, 1.5) * 0.85;
    }

    const base = this.state.magnetogram ? 0 : this.profile.glowIntensity;
    this.glowMaterial.uniforms.uStrength.value = base + (this.state.magnetogram ? 0 : pulse);
    this.coronaMaterial.uniforms.uStrength.value = base + (this.state.magnetogram ? 0 : pulse * 0.7);
  }

  // ── State setters (called from React effects) ────────────────────

  setActivity(cls: ActivityClass) {
    if (this.state.activity === cls) return;
    this.state.activity = cls;
    this.profile = ACTIVITY_PROFILES[cls];
    const u = this.sunMaterial.uniforms;
    u.uTurbulence.value = this.profile.turbulence;
    u.uSpotScale.value = this.profile.spotScale;
    u.uBrightness.value = 0.92 + 0.12 * this.profile.glowIntensity;
    this.regenerateRegions();
    this.applyMagnetogramLook();
    this.scheduleNextAutoFlare();
  }

  setSunspots(on: boolean) {
    this.state.sunspots = on;
    this.sunMaterial.uniforms.uShowSpots.value = on ? 1 : 0;
  }

  setMagneticRegions(on: boolean) {
    this.state.magneticRegions = on;
    this.sunMaterial.uniforms.uShowRegions.value = on ? 1 : 0;
    this.loopsGroup.visible = on;
  }

  setMagnetogram(on: boolean) {
    this.state.magnetogram = on;
    this.sunMaterial.uniforms.uMagnetogram.value = on ? 1 : 0;
    this.applyMagnetogramLook();
  }

  setAutoRotate(on: boolean) {
    this.state.autoRotate = on;
    this.controls.autoRotate = on;
  }

  resetView() {
    this.camera.position.copy(CAMERA_HOME);
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  private applyMagnetogramLook() {
    const mag = this.state.magnetogram;
    this.glowMesh.visible = !mag;
    this.coronaPlane.visible = !mag;
    const loopColor = mag ? 0xd8d8d8 : 0xff9c4a;
    for (const child of this.loopsGroup.children) {
      const mat = (child as ArcMesh).material;
      (mat.uniforms.uColor.value as THREE.Color).setHex(loopColor);
    }
  }

  // ── Loop / lifecycle ──────────────────────────────────────────────

  private startLoop() {
    if (this.rafId !== null || this.disposed) return;
    this.lastFrame = performance.now();
    const tick = () => {
      this.rafId = requestAnimationFrame(tick);
      const now = performance.now();
      const dt = Math.min((now - this.lastFrame) / 1000, 0.05);
      this.lastFrame = now;
      this.elapsed += dt;

      this.sunGroup.rotation.y += dt * 0.05;
      this.sunMaterial.uniforms.uTime.value = this.elapsed;
      this.coronaMaterial.uniforms.uTime.value = this.elapsed;
      this.coronaPlane.quaternion.copy(this.camera.quaternion);

      if (this.elapsed >= this.nextAutoFlareAt) {
        this.triggerFlare(false);
        this.scheduleNextAutoFlare();
      }
      this.updateEvents(dt);

      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    this.rafId = requestAnimationFrame(tick);
  }

  private stopLoop() {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  private resize() {
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    if (w === 0 || h === 0) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  dispose() {
    this.disposed = true;
    this.stopLoop();
    this.resizeObserver.disconnect();
    document.removeEventListener('visibilitychange', this.onVisibility);
    this.controls.dispose();
    this.scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (mesh.geometry) mesh.geometry.dispose();
      const material = (mesh as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
      if (Array.isArray(material)) material.forEach((m) => m.dispose());
      else if (material) material.dispose();
    });
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}

// ---------------------------------------------------------------------------
// React wrapper
// ---------------------------------------------------------------------------

export interface SolarSceneHandle {
  triggerFlare: () => void;
  resetView: () => void;
}

interface SolarSceneProps {
  activity: ActivityClass;
  sunspots: boolean;
  magneticRegions: boolean;
  magnetogram: boolean;
  autoRotate: boolean;
}

export const SolarScene = forwardRef<SolarSceneHandle, SolarSceneProps>(function SolarScene(
  { activity, sunspots, magneticRegions, magnetogram, autoRotate },
  ref,
) {
  const { t } = useLanguage();
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<SolarEngine | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let engine: SolarEngine | null = null;
    try {
      engine = new SolarEngine(container, {
        activity, sunspots, magneticRegions, magnetogram, autoRotate,
      });
      engineRef.current = engine;
    } catch {
      setWebglFailed(true);
    }
    return () => {
      engineRef.current = null;
      engine?.dispose();
    };
    // Initial state only — later prop changes go through the setter effects.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { engineRef.current?.setActivity(activity); }, [activity]);
  useEffect(() => { engineRef.current?.setSunspots(sunspots); }, [sunspots]);
  useEffect(() => { engineRef.current?.setMagneticRegions(magneticRegions); }, [magneticRegions]);
  useEffect(() => { engineRef.current?.setMagnetogram(magnetogram); }, [magnetogram]);
  useEffect(() => { engineRef.current?.setAutoRotate(autoRotate); }, [autoRotate]);

  useImperativeHandle(ref, () => ({
    triggerFlare: () => engineRef.current?.triggerFlare(true),
    resetView: () => engineRef.current?.resetView(),
  }), []);

  if (webglFailed) {
    return (
      <div className="w-full h-full flex items-center justify-center px-6 text-center">
        <p className="text-[13px] text-neutral-400">{t.simulation.webglFallback}</p>
      </div>
    );
  }

  return <div ref={containerRef} className="w-full h-full" />;
});
