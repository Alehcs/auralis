# Prueba aislada Unity + Needle + WebAR

**Fase 4.2: Unity → Needle → Web demostrado. AR móvil pendiente de prueba física.**

Unity 6000.3.17f1 y Needle 5.1.12 exportaron el cubo mínimo real. El visor público
lo carga por defecto, verifica SHA-256 y conserva cámara, material, órbita y raíz AR.
No es el gemelo solar ni modifica la simulación Three.js de Auralis.

https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/?scene=unity

## Ejecutar

Desde esta carpeta, con Unity cerrado y licencia activa:

```sh
sh scripts/prepare-phase42.sh
cd web
npm run dev
```

Abrir `http://localhost:5184/?scene=unity`. La ruta `/` también carga el GLB real;
`?scene=provisional` permite consultar el cubo TS histórico, etiquetado como tal.
La exportación escribe `web/public/unity/Phase4Probe.glb` y `export-evidence.json`.
El build Vite queda en `web/dist`. El comando no publica por sí mismo.

Para abrir la escena en el editor: añadir `unity/` a Unity Hub, abrir
`Assets/Scenes/Phase4Probe.unity`. Menú `Auralis > Phase 4 > 2 - Export with Needle`.
No ejecutar el menú de creación si la escena ya existe; el script no la sobrescribe.

## Verificación y móviles

- [Informe Fase 4.2](../../docs/phase42.md)
- [Pasos mínimos de prueba física](evidence/phase42/PRUEBA-MOVIL.md)
- [QR público Unity](evidence/phase42/qr-unity-public.png)
- [QR iOS / Needle Go](evidence/phase42/qr-unity-ios.png)
- Histórico: [Fase 4](../../docs/phase4.md), [Fase 4.1](../../docs/phase41.md)

Tests: `cd web && npm test`; build: `npm run build`. Auditoría pública desde
esta carpeta: `python3 scripts/audit-phase41-public.py --phase phase42`.
Los ~60 renders/s medidos corresponden al Mac, no a teléfonos ni tiempo GPU.
