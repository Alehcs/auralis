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

varying vec3 vLocal;
varying vec3 vViewN;

${NOISE_GLSL}

void main(){
  vec3 n = normalize(vLocal);
  float t = uTime * 0.03 * uTurbulence;
  float mu = clamp(dot(normalize(vViewN), vec3(0.0, 0.0, 1.0)), 0.0, 1.0);

  // ── Magnetogram mode: grayscale B+/B− polarity patches ──────────
  if (uMagnetogram > 0.5) {
    float g = 0.5 + 0.045 * snoise(n * 60.0);
    for (int i = 0; i < ${MAX_REGIONS}; i++) {
      if (i >= uRegionCount) break;
      vec4 R = uRegions[i];
      vec4 A = uRegionAux[i];
      vec3 tp = normalize(R.xyz + A.xyz * R.w * 0.55);
      vec3 tm = normalize(R.xyz - A.xyz * R.w * 0.55);
      float s  = R.w * 0.42;
      float dp = acos(clamp(dot(n, tp), -1.0, 1.0));
      float dm = acos(clamp(dot(n, tm), -1.0, 1.0));
      float lobe = exp(-pow(dp / s, 2.0)) - exp(-pow(dm / s, 2.0));
      lobe *= 0.75 + 0.35 * snoise(n * 24.0 + float(i) * 1.7);
      g += A.w * lobe * 0.9;
    }
    g = clamp(g, 0.0, 1.0);
    g *= 0.35 + 0.65 * mu;
    gl_FragColor = vec4(vec3(g), 1.0);
    return;
  }

  // ── Visual mode: procedural convection + granulation ────────────
  float cells = fbm(n * 3.5 + vec3(0.0, t, t * 0.6));
  float gran  = fbm(n * 14.0 - vec3(t * 1.8));
  float v = 0.55 + 0.45 * cells + 0.25 * gran;

  vec3 c1 = vec3(0.45, 0.08, 0.0);
  vec3 c2 = vec3(1.0, 0.42, 0.02);
  vec3 c3 = vec3(1.0, 0.85, 0.45);
  vec3 col = mix(c1, c2, smoothstep(0.15, 0.75, v));
  col = mix(col, c3, smoothstep(0.78, 1.15, v));

  for (int i = 0; i < ${MAX_REGIONS}; i++) {
    if (i >= uRegionCount) break;
    vec4 R = uRegions[i];
    vec4 A = uRegionAux[i];
    vec3 tp = normalize(R.xyz + A.xyz * R.w * 0.55);
    vec3 tm = normalize(R.xyz - A.xyz * R.w * 0.55);
    float dp = acos(clamp(dot(n, tp), -1.0, 1.0));
    float dm = acos(clamp(dot(n, tm), -1.0, 1.0));

    if (uShowRegions > 0.5) {
      float dc = acos(clamp(dot(n, R.xyz), -1.0, 1.0));
      float fac = exp(-pow(dc / (R.w * 1.1), 2.0))
                * (0.55 + 0.45 * snoise(n * 20.0 + float(i) * 3.7));
      col += vec3(1.0, 0.75, 0.35) * fac * 0.55 * A.w;
    }
    if (uShowSpots > 0.5) {
      float sr = R.w * 0.34 * uSpotScale;
      float umbra = max(exp(-pow(dp / sr, 3.0)), exp(-pow(dm / sr, 3.0)));
      float penum = max(exp(-pow(dp / (sr * 1.9), 3.0)), exp(-pow(dm / (sr * 1.9), 3.0)));
      col = mix(col, col * 0.5, clamp(penum, 0.0, 1.0));
      col = mix(col, vec3(0.05, 0.015, 0.0), clamp(umbra, 0.0, 1.0));
    }
  }

  col *= 0.35 + 0.75 * mu;                                // limb darkening
  col += vec3(1.0, 0.45, 0.1) * pow(1.0 - mu, 2.5) * 0.35; // warm rim
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

// ---------------------------------------------------------------------------
// Engine
// ---------------------------------------------------------------------------

interface Region {
  dir: THREE.Vector3;     // unit vector, object space
  tangent: THREE.Vector3; // east-west unit tangent (bipolar axis)
  radius: number;         // angular radius (rad)
  strength: number;
}

interface FlareArc {
  mesh: THREE.Mesh<THREE.TubeGeometry, THREE.MeshBasicMaterial>;
  born: number;
  life: number;
  strength: number;
}

interface EngineState {
  activity: ActivityClass;
  sunspots: boolean;
  magneticRegions: boolean;
  magnetogram: boolean;
}

function makeGlowSpriteTexture(): THREE.CanvasTexture {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d')!;
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0.0, 'rgba(255, 170, 60, 0.55)');
  grad.addColorStop(0.35, 'rgba(255, 120, 30, 0.22)');
  grad.addColorStop(1.0, 'rgba(255, 90, 20, 0.0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

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
  private glowSprite: THREE.Sprite;
  private loopsGroup = new THREE.Group();
  private flaresGroup = new THREE.Group();
  private regions: Region[] = [];
  private flares: FlareArc[] = [];
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
      42, container.clientWidth / Math.max(container.clientHeight, 1), 0.1, 100,
    );
    this.camera.position.set(0, 0.4, 3.1);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = false;
    this.controls.minDistance = 1.7;
    this.controls.maxDistance = 6.5;

    // Sun sphere
    const regionsInit = Array.from({ length: MAX_REGIONS }, () => new THREE.Vector4());
    const auxInit = Array.from({ length: MAX_REGIONS }, () => new THREE.Vector4());
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
        uBrightness:  { value: 0.95 + 0.1 * this.profile.glowIntensity },
        uRegionCount: { value: 0 },
        uRegions:     { value: regionsInit },
        uRegionAux:   { value: auxInit },
      },
    });
    const sunMesh = new THREE.Mesh(new THREE.SphereGeometry(1, 96, 96), this.sunMaterial);
    this.sunGroup.add(sunMesh);
    this.sunGroup.add(this.loopsGroup);
    this.sunGroup.add(this.flaresGroup);
    this.scene.add(this.sunGroup);

    // Corona: rim shell + soft radial sprite
    this.glowMaterial = new THREE.ShaderMaterial({
      vertexShader: GLOW_VERTEX,
      fragmentShader: GLOW_FRAGMENT,
      uniforms: {
        uColor:    { value: new THREE.Color(1.0, 0.55, 0.18) },
        uStrength: { value: this.profile.glowIntensity },
      },
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false,
    });
    this.glowMesh = new THREE.Mesh(new THREE.SphereGeometry(1.28, 48, 48), this.glowMaterial);
    this.scene.add(this.glowMesh);

    const spriteMat = new THREE.SpriteMaterial({
      map: makeGlowSpriteTexture(),
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      transparent: true,
      opacity: 0.6 * this.profile.glowIntensity,
    });
    this.glowSprite = new THREE.Sprite(spriteMat);
    this.glowSprite.scale.setScalar(4.6);
    this.scene.add(this.glowSprite);

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
      const mesh = child as THREE.Mesh<THREE.TubeGeometry, THREE.MeshBasicMaterial>;
      mesh.geometry.dispose();
      mesh.material.dispose();
      this.loopsGroup.remove(mesh);
    }
    const loopColor = this.state.magnetogram ? 0xd8d8d8 : 0xffa64d;
    for (const r of this.regions) {
      const arcCount = 2;
      for (let k = 0; k < arcCount; k++) {
        const spread = 0.55 + k * 0.35;
        const tp = r.dir.clone().addScaledVector(r.tangent, r.radius * spread).normalize();
        const tm = r.dir.clone().addScaledVector(r.tangent, -r.radius * spread).normalize();
        const apex = r.dir.clone().multiplyScalar(1 + r.radius * (1.2 + k * 0.8) * r.strength);
        const curve = new THREE.QuadraticBezierCurve3(tp, apex, tm);
        const geo = new THREE.TubeGeometry(curve, 24, 0.005, 6);
        const mat = new THREE.MeshBasicMaterial({
          color: loopColor,
          transparent: true,
          opacity: 0.4,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        this.loopsGroup.add(new THREE.Mesh(geo, mat));
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
    const geo = new THREE.TubeGeometry(curve, 32, 0.011 * Math.max(mul, 0.5), 8);
    const mat = new THREE.MeshBasicMaterial({
      color: this.state.magnetogram ? 0xffffff : 0xffd9a0,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    this.flaresGroup.add(mesh);
    this.flares.push({ mesh, born: this.elapsed, life: 1.6 + 0.5 * mul, strength: mul });
  }

  private scheduleNextAutoFlare() {
    const [min, max] = this.profile.flareIntervalMs;
    this.nextAutoFlareAt = this.elapsed + (min + Math.random() * (max - min)) / 1000;
  }

  private updateFlares() {
    let pulse = 0;
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
      f.mesh.material.opacity = env * Math.min(0.9, 0.55 + 0.3 * f.strength);
      f.mesh.scale.setScalar(1 + 0.08 * t);
      pulse = Math.max(pulse, env * 0.4 * f.strength);
    }
    const glowBase = this.state.magnetogram ? 0 : this.profile.glowIntensity;
    this.glowMaterial.uniforms.uStrength.value = glowBase + (this.state.magnetogram ? 0 : pulse);
  }

  // ── State setters (called from React effects) ────────────────────

  setActivity(cls: ActivityClass) {
    if (this.state.activity === cls) return;
    this.state.activity = cls;
    this.profile = ACTIVITY_PROFILES[cls];
    const u = this.sunMaterial.uniforms;
    u.uTurbulence.value = this.profile.turbulence;
    u.uSpotScale.value = this.profile.spotScale;
    u.uBrightness.value = 0.95 + 0.1 * this.profile.glowIntensity;
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

  private applyMagnetogramLook() {
    const mag = this.state.magnetogram;
    this.glowMesh.visible = !mag;
    this.glowSprite.visible = !mag;
    (this.glowSprite.material as THREE.SpriteMaterial).opacity = 0.6 * this.profile.glowIntensity;
    const loopColor = mag ? 0xd8d8d8 : 0xffa64d;
    for (const child of this.loopsGroup.children) {
      ((child as THREE.Mesh).material as THREE.MeshBasicMaterial).color.setHex(loopColor);
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

      this.sunGroup.rotation.y += dt * 0.07;
      this.sunMaterial.uniforms.uTime.value = this.elapsed;

      if (this.elapsed >= this.nextAutoFlareAt) {
        this.triggerFlare(false);
        this.scheduleNextAutoFlare();
      }
      this.updateFlares();

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
      else if (material) {
        const tex = (material as THREE.SpriteMaterial).map;
        if (tex) tex.dispose();
        material.dispose();
      }
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
}

interface SolarSceneProps {
  activity: ActivityClass;
  sunspots: boolean;
  magneticRegions: boolean;
  magnetogram: boolean;
}

export const SolarScene = forwardRef<SolarSceneHandle, SolarSceneProps>(function SolarScene(
  { activity, sunspots, magneticRegions, magnetogram },
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
        activity, sunspots, magneticRegions, magnetogram,
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

  useImperativeHandle(ref, () => ({
    triggerFlare: () => engineRef.current?.triggerFlare(true),
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
