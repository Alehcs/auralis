# Limpieza solicitada del visor

Único archivo de implementación editado: prototypes/phase4-unity-needle/web/phase6/index.html.

Se retiraron de la interfaz el párrafo de movimiento ilustrativo, la nota dinámica de estimación, el desplegable de identidad/límites, las explicaciones y escala del bloque AR, los apartados de registro/prueba y diagnóstico, y el pie inferior. La sección AR contiene solo «Explora en AR», QR, «Continúa en tu teléfono» y enlace. El título reutiliza el enlace existente a Needle Go; el menú nativo de AR y el panel AR compacto permanecen intactos.

Los nodos internos que el controlador y el puente del dashboard necesitan se conservan vacíos bajo un contenedor hidden/inert, fuera de la interfaz y del árbol accesible. Así no se cambia la lógica de carga, animación, diagnóstico, escala en AR ni transición. Las etiquetas visibles que distinguen HMI, Coronium y recreación se conservan.

Build y 26 tests pasan. Verificados cinco estados y enlaces tras finalizar cada transición, cuatro capas, pausa/reanudación de superficie, sin errores de consola. Los 64 archivos src/public conservan hashes exactos. before.html permite revertir únicamente este ajuste; no usar git restore sobre trabajo anterior. Captura after.png tomada en preview local: su QR local no sirve para abrir el Mac desde un teléfono. Publicación y AR físico no realizados.
