# Pruebas físicas pendientes

Usar el MISMO build/export, guardar SHA-256, URL, fecha, modelo, SO y navegador.
No marcar una celda como aprobada por emulación de viewport ni por documentación.

| Prueba | Android Chrome + ARCore | iPhone Safari → Needle Go | iPhone Quick Look | Sin AR |
|---|---|---|---|---|
| Abrir HTTPS mediante QR | pendiente | pendiente | pendiente | pendiente móvil |
| Carga en red móvil, 3 intentos fríos | pendiente | pendiente | pendiente | pendiente |
| Orbitar, color, giro, escala y reset en web | pendiente | pendiente | antes del visor | aprobado escritorio |
| Denegar cámara y recuperar | pendiente | pendiente | pendiente | n/a |
| Iniciar sesión / salir y reentrar | pendiente | pendiente | pendiente | fallback aprobado escritorio |
| Retícula / tocar superficie | pendiente | pendiente | colocación nativa pendiente | n/a |
| Cubo a escala 20 cm, suelo correcto | pendiente | pendiente | pendiente | n/a |
| Ajustar posición / rotación / escala | pendiente | pendiente | pendiente | n/a |
| Caminar alrededor 60 s, medir deriva | pendiente | pendiente | pendiente | n/a |
| Pausa, bloqueo y reanudación | pendiente | pendiente | pendiente | n/a |
| Rendimiento 5 min y calentamiento | pendiente | pendiente | pendiente | pendiente |

Presupuestos de aceptación propuestos (no resultados): 3D/AR fluido ≥30 FPS
medido en render del dispositivo durante 5 minutos; tiempo a interacción ≤5 s
con red y caché declaradas. Describir iluminación, textura de superficie y
fallos de tracking. Registrar deriva en cm como observación, sin asumir anclas
persistentes. Guardar vídeo de colocación si el dispositivo lo permite.

El contador onPlaced es evidencia de un evento de software, no de buen tracking.
El diagnóstico requestAnimationFrame no sustituye un perfil XR/GPU. Quick Look
no conserva los controles HTML/TS; comprobar el estado antes de exportar y
los gestos del visor, no prometer equivalencia funcional.
