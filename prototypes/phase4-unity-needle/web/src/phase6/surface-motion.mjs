// Presentation seconds only. Never reads/writes observation dates or SI.
export const SURFACE_SEED = 71;
export class SurfaceClock {
  time = 0;
  last = null;
  running;
  constructor(running = true) { this.running = running; }
  sync(now) { this.last = now; }
  tick(now, visible) {
    if (!Number.isFinite(now)) return this.time;
    const dt = this.last === null ? 0 : Math.max(0, Math.min((now - this.last) / 1000, .1));
    this.last = now;
    if (this.running && visible) this.time += dt;
    return this.time;
  }
  reset(now) { this.running = false; this.time = 0; this.sync(now); }
}
