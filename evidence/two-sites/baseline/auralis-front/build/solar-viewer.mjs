import { readdir, readFile, copyFile, mkdir } from 'node:fs/promises';
import { constants } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const viewerRoot = fileURLToPath(new URL('../../prototypes/phase4-unity-needle/web/', import.meta.url));
const directories = ['phase5', 'phase6', 'phase7', 'assets', 'unity'];
const mime = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.json':'application/json', '.png':'image/png', '.glb':'model/gltf-binary', '.wasm':'application/wasm', '.txt':'text/plain', '.svg':'image/svg+xml' };
export async function viewerFiles(root = path.join(viewerRoot, 'dist')) {
  const files = new Map();
  async function walk(relative) {
    for (const entry of await readdir(path.join(root, relative), { withFileTypes: true })) {
      const name = path.posix.join(relative, entry.name);
      if (entry.isDirectory()) await walk(name);
      else if (entry.isFile()) files.set('/' + name, path.join(root, name));
    }
  }
  for (const dir of directories) await walk(dir);
  return files;
}
export function solarViewer() {
  let files, output, building = false;
  return {
    name: 'auralis-existing-solar-viewer',
    configResolved(config) { building = config.command === 'build'; output = path.resolve(config.root, config.build.outDir); },
    async configureServer(server) {
      files = await viewerFiles();
      server.middlewares.use(async (req, res, next) => {
        const pathname = new URL(req.url, 'http://localhost').pathname;
        const key = pathname.endsWith('/') ? pathname + 'index.html' : pathname;
        const file = files.get(key);
        if (!file) {
          if (/^\/phase[567](\/|$)|^\/unity\//.test(pathname)) { res.statusCode=404; res.end('Viewer resource not found'); }
          else next();
          return;
        }
        try {
          res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
          res.setHeader('Cache-Control', 'no-cache');
          res.end(await readFile(file));
        } catch { res.statusCode=503; res.end('Viewer unavailable; rebuild resources'); }
      });
    },
    async closeBundle() {
      if (!building) return;
      // Generated deployment artifacts, never an independently maintained viewer source.
      for (const [url, source] of await viewerFiles()) {
        const destination = path.join(output, url.slice(1));
        await mkdir(path.dirname(destination), { recursive: true });
        // Fail on any collision instead of replacing frontend assets.
        await copyFile(source, destination, constants.COPYFILE_EXCL);
      }
    },
  };
}
