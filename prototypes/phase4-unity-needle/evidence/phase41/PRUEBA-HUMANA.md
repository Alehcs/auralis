# Fase 4.1 — pasos mínimos y registro físico

Fecha: 2026-09-09. Build: `phase4.1-20260909-a`. No iniciar otra fase.

## Qué se puede probar ahora

URL pública (sin cuenta):
https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/

QR: `qr-public.png`. La página también genera un QR de su URL exacta.
**Esta publicación contiene el cubo provisional TypeScript.** Sirve para validar
Needle, el acceso móvil y la ruta AR, pero no acredita Unity. Registrar su fuente.
No usar un resultado provisional como aprobación del futuro GLB Unity.

## Primero: desbloquear la exportación Unity real

1. Instalar Unity Hub desde https://unity.com/download. Iniciar sesión y activar
   una licencia que corresponda al usuario. Instalar Unity 6.3 LTS para Apple
   Silicon; el proyecto propone 6000.3.0f1. No hace falta módulo Android/iOS ni
   Unity WebGL: Needle exporta glTF y la web se construye con Vite.
2. Desde la raíz `prototypes/phase4-unity-needle`, ejecutar:

   ```sh
   UNITY_EDITOR='/Applications/Unity/Hub/Editor/6000.3.0f1/Unity.app/Contents/MacOS/Unity' sh scripts/prepare-phase41.sh
   ```

   Ajustar únicamente la ruta si se instaló otro parche 6000.3. El proceso debe
   compilar C#, crear la escena, exportar mediante Needle 5.1.12, comprobar el
   SHA-256 y compilar la web. Si falla, conservar `evidence/unity-export.log`;
   **no continuar como si hubiese exportado**.
3. Abrir `unity/` en Unity, luego `Assets/Scenes/Phase4Probe.unity`. Comparar el
   cubo de 20 cm, material verde, cámara, luz, pivote al suelo y orientación con
   `http://localhost:5184/?scene=unity` después de `cd web && npm run dev`.
   Conservar captura del editor y navegador; el verificador no certifica paridad.
4. Publicar el nuevo `web/dist` en el MISMO sitio y abrir `/?scene=unity`.
   Debe indicar GLB cargado, nunca escena provisional. El QR debe conservar
   `?scene=unity`. Entregar el log y el GLB/evidencia a Codex para esta publicación
   y revisión; el comando local no publica ni cambia la audiencia.

## Android — unos 5 minutos, dispositivo real

1. Android compatible ARCore, Chrome y Google Play Services for AR disponibles.
   Anotar modelo, versión Android/Chrome y red. Escanear `qr-public.png` con la
   cámara, abrir en Chrome y confirmar que no exige cuenta.
2. Confirmar cubo 3D; arrastrar, pellizcar, cambiar color, girar, escalar y reset.
   Pulsar **Medir 30 s de render**: la página vuelve al cubo. Mantenerlo visible
   y mover lentamente la cámara. Después consultar el resultado más abajo.
3. Usar el botón AR de Needle. Probar denegar cámara una vez y luego habilitar
   permiso y reintentar. Con luz y superficie texturada, mover el teléfono hasta
   ver retícula y tocar para colocar. Verificar cubo de ~20 cm y apoyo en suelo.
4. Al colocar se inicia una muestra XR de 30 s automáticamente. Caminar alrededor
   durante 60 s; comprobar deriva, posición, giro y escala con gestos. Salir y
   reentrar. Bloquear/desbloquear y anotar si se pierde la sesión o colocación.
5. Salir a 3D, rellenar los tres campos y **Diagnóstico técnico → Descargar
   diagnóstico**. Adjuntar una foto/vídeo externo que muestre objeto y superficie.
   Dejar activo 5 min y anotar calor, cierre, congelamiento o degradación; repetir
   muestra de 30 s al final. Esto es una prueba básica, no un perfil GPU.

## iPhone — Safari → Needle Go; Quick Look por separado

1. Escanear el mismo QR con Cámara y abrir en Safari. Repetir los controles 3D
   y la muestra de 30 s. Descargar este primer diagnóstico **antes** de salir a
   Needle Go: Safari y App Clip son procesos distintos y no comparten memoria.
2. Pulsar AR; aceptar abrir Needle Go. Si no aparece la tarjeta, usar **abrir
   Needle Go** en la página. No aprobar si solo se muestra la ficha o App Store.
   El destino preparado es:
   https://appclip.needle.tools/ar?url=https%3A%2F%2Fauralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site%2F
3. En Needle Go, cámara, retícula, toque, ajuste, 60 s caminando, salida/reentrada
   y 5 min de observación como Android. La muestra XR comienza tras `onPlaced`.
   Las anclas de esta ruta tienen limitaciones: anotar deriva real, no asumir
   persistencia espacial. Si la descarga no está disponible dentro del App Clip,
   guardar captura del resultado y escribir las observaciones en el registro.
4. Volver a Safari y probar **Ver con Quick Look (iOS)** por separado. Comprobar
   que genera/abre USDZ, coloca el cubo y conserva el color/escala exportados.
   Los controles HTML/TypeScript no se ejecutan dentro de Quick Look.
5. Guardar vídeo/foto externa de la colocación. La captura interna del App Clip
   puede no incluir el fondo de cámara; ese límite no demuestra fallo de tracking.

## Registro y criterios

Por dispositivo anotar: fecha, build/hash, fuente provisional/Unity, URL, modelo,
SO/navegador, red, caché, QR, tiempo hasta poder interactuar (cronómetro), controles,
permiso denegado/recuperado, retícula, colocación, ajuste, escala, deriva estimada,
salida/reentrada, bloqueo/reanudación, calor tras 5 min, fallos, JSON y vídeo.
Cada casilla: **aprobado / falló / no probado**, nunca completar por inferencia.

Hacer 3 aperturas frías (borrar los datos del sitio/caché entre ellas, declarar
red). Presupuesto propuesto: interacción ≤5 s; muestra completa de render ≥30 Hz,
objetivo p95 ≤50 ms; sin cierres ni pérdida de uso durante 5 min. Los presupuestos
son criterios de aceptación, no resultados. Si falla, conservar el resultado.
Una cadencia suficiente no certifica buen tracking ni una carga futura del Sol.
La medida cuenta callbacks de render, no tiempo GPU. `onPlaced` solo es un evento
software; la calidad de colocación requiere observación física. Samples marcadas
`interrupted-*`, sin cuadros o de otra fuente no sirven para aprobar el requisito.
