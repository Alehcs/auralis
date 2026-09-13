export function describeAR({ secure, immersiveAR, ios, error }) {
  if (!secure) return 'AR requiere HTTPS. Puedes seguir usando los controles 3D.';
  if (error) return 'No se pudo comprobar WebXR. El modo 3D sigue disponible; revisa permisos y navegador.';
  if (immersiveAR) return 'WebXR AR disponible según el navegador. La sesión y la colocación aún deben probarse.';
  if (ios) return 'Safari/iOS: AR mediante Needle Go (App Clip), o Quick Look. No es WebXR nativo de Safari.';
  return 'Este navegador no ofrece AR inmersiva. Puedes explorar el objeto en 3D.';
}
export function shareable(url) {
  const u = new URL(url);
  return u.protocol === 'https:' && !['localhost','127.0.0.1','[::1]'].includes(u.hostname);
}
