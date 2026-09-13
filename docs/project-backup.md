# Respaldo del proyecto y del visor AR

El repositorio principal conserva el frontend, backend, modelos promovidos,
contratos, resultados guardados, figuras Grad-CAM y el visor aprobado completo.
El visor está en `prototypes/phase4-unity-needle/web/`: código, shaders, GLB,
texturas, datos temporales y configuración pública. El proyecto Unity editable
está en `prototypes/phase4-unity-needle/unity/`, con Assets, Packages y ProjectSettings.
Los archivos de ambos Sites se incorporan como archivos normales, no submódulos.

Los repositorios internos de entrega de Sites conservan su historial local por
separado. Sus directorios `.git` no forman parte del respaldo principal. Un clon
puede reconstruir los Sites desde el código y los recursos versionados siguiendo
`docs/two-sites-demo.md` y `deployments/dashboard-sites/README.md`.

Se omiten dependencias instaladas, cachés Unity, builds regenerables y archivos
comprimidos duplicados de entrega. El dataset completo local y los checkpoints
experimentales ignorados requieren un respaldo separado; el modelo promovido,
los recursos del visor y los resultados estáticos sí se incluyen. Se conservan
las capturas y vídeos de validación originales no comprimidos en archivos ZIP.

Un commit guarda el estado en Git local. Solo un push lo guarda también en GitHub.
El hosting de Sites es independiente de ambos y no sustituye este respaldo.
