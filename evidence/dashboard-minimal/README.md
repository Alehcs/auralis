# Ajuste minimalista del dashboard

- Retirada la franja superior de demo y el párrafo científico repetido antes de cada panel.
- Notas científicas completas y condición de resultados guardados accesibles en «Sobre los datos» al pie.
- Resumen de dataset y sistema plegables. Hero sin brillo decorativo ni badge redundante de inferencia inactiva.
- Textos breves en Monitoring, configuración, XAI y contenedor de Simulación. Ningún cambio dentro del visor.
- Preparación de entrega valida la ruta estable de respuestas congeladas en lugar de depender del texto de un aviso.

Archivos editados: dashboard-page.tsx, model-metrics.tsx, magnetogram-panel.tsx, simulation/SolarTwinPanel.tsx, components/config-panel.tsx y components/xai-faithfulness.tsx bajo auralis-front/src/features/dashboard; scripts/prepare-dashboard-site.mjs.

Validación: build Sites y build del visor aprobados (build.log; aviso existente de tamaño de chunks). Preparación de 31 archivos generados aprobada. Apertura/cierre de ambos desplegables y navegación a Monitoring comprobados en navegador de escritorio. Capturas before.png y after.png en el mismo viewport 1280x720. Los 64 archivos de src/public del visor conservan su SHA-256 (verification.json); no cambios de Sol, animación, timeline ni AR. No se repitió prueba física AR ni comparación animada en esta edición de textos; la publicación de la integración entre Sites sigue pendiente.

Los archivos originales, incluidos cambios locales anteriores, están en before/ con sus rutas completas relativas al proyecto. Para deshacer solo este ajuste, comparar cada archivo con su instantánea y revertir esos cambios; no usar git restore, porque perdería cambios anteriores. No se realizaron commits, push ni publicación en este ajuste.
