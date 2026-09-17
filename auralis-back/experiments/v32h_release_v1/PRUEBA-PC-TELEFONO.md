> **Closure addendum — 2026-09-17:** the user confirmed that the mobile review after the coherence correction is resolved. Source: user confirmation; device/browser/version, test date, recordings and measurements not recorded. The subsequent [TypeScript closure](typescript/REPORT.md) resolves the 15 source diagnostics and the compiler-option incompatibility. Earlier results and pending statements below are historical, preserved unchanged. No new physical AR session or publication is claimed.

> **Final status — 2026-09-17:** the user confirmed successful PC and phone/AR tests, including active version, predictions, metrics, Agent Lab, Grad-CAM, five states, layers, timeline and AR, with no reported visual regressions. Source: user confirmation; device/browser versions, execution dates, recordings and performance measurements were not recorded. See [final closure](closure/REPORT.md). Earlier pending statements below describe the original test stage and are preserved as history. Local promotion and the subsequently refreshed temporary Sites are distinct from a definitive publication, which is not performed here.

# Prueba humana breve — pendiente

No se ha realizado una validación física de PC/teléfono o AR. Los servidores de QA se cierran al terminar; usa RUNBOOK.md para iniciar la instancia explícita del release sin cambiar el valor predeterminado.

1. PC: abre el dashboard de la instancia de prueba. Confirma Coronium V3.2, MAE determinista0.0483 y Agent Lab sin errores; navega por todas las pestañas.
2. Monitoring: selecciona un magnetograma, comprueba respuesta y Grad-CAM. El diagnóstico de ruido sigue separado y no es una probabilidad calibrada.
3. Simulation: recorre24,25,28,29,30 y regresa a29. Deben conservarse fechas, mapas, cámara y comportamiento de capas/timeline. Solo cambia la identidad y el resultado Coronium. HMI29: SI2.057672 y resultado2.049826.
4. PC: congela superficie en t=0, misma fecha/cámara; compara el Sol con tu referencia aprobada. Prueba Play/Pause, zoom y cambio de pestaña/retorno.
5. Teléfono: una URL127.0.0.1 del Mac no es accesible desde el teléfono. Para prueba LAN utiliza explícitamente IP del Mac, frontend host0.0.0.0, backend host0.0.0.0, VITE_API_URL y CORS_ORIGINS correspondientes a esa IP/puertos. No se ha abierto esa exposición ni publicado nada en H. Comprueba navegación táctil, cinco fechas, capas, zoom y que no se recorten controles.
6. AR físico requiere la ruta segura compatible ya documentada (iPhone Safari→Needle Go); localhost/LAN HTTP no acredita AR. El Site público conserva V3.1 y no sirve como prueba física del release V3.2. No publicar para resolverlo sin autorización específica.

Devuelve dispositivo/navegador, resultado de cada paso y cualquier captura/error. No interpretar esta lista como prueba ya aprobada ni inferir rendimiento móvil a partir del Mac.
