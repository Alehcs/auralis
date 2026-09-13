# Fase 4.2 — única validación manual pendiente

Usar el GLB real, build `phase4.2-20260909-b`:
https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/?scene=unity

QR: `qr-unity-public.png`. SHA-256 del GLB:
`92ce99f4e279eaf47110ddaee595e0c52daa566d806bb05204f9e458fe9d413b`.

No hace falta crear la escena ni exportar manualmente en Unity: ya se hizo.

1. **Android:** escanear QR y abrir en Chrome sobre un dispositivo compatible
   ARCore. **iPhone:** abrir en Safari. Confirmar «Escena real Unity» y probar
   arrastre/pellizco, color, giro, escala y restablecer.
2. Pulsar **Medir 30 s de render**. Mantener el cubo visible. Descargar diagnóstico
   antes de pasar a Needle Go, porque Safari y App Clip no comparten el registro.
3. Pulsar la entrada AR de Needle. Android: cámara → retícula → tocar para colocar.
   iPhone: abrir Needle Go → cámara → retícula → tocar. Si no aparece la tarjeta,
   usar «abrir Needle Go» o `qr-unity-ios.png`. Confirmar cubo de 20 cm, ajuste por
   gestos, estabilidad al caminar 60 s y salida/reentrada. La colocación dispara
   automáticamente una muestra XR de 30 s. Quick Look se prueba aparte en Safari;
   no ejecuta los controles HTML/TypeScript.
4. Tras 5 minutos, anotar calor, cierres, pérdida de tracking y deriva. Rellenar
   dispositivo/OS/navegador, red/caché y observaciones; descargar JSON. Si Needle Go
   no permite descargar, conservar captura del resultado y foto/vídeo externo de
   colocación. Repetir 3 aperturas frías con red/caché declaradas.

Marcar aprobado/falló/no probado. Un evento `onPlaced`, un viewport estrecho o
HTTP 200 no demuestra calidad de tracking. Cadencia de render no es tiempo GPU.
Presupuestos propuestos: interacción ≤5 s, cadencia ≥30 Hz, p95 ≤50 ms y sin
cierres en 5 min. Son criterios, no resultados ya obtenidos. Probar también
permiso denegado/recuperado y bloqueo/reanudación; iOS tiene limitaciones de anclas.
