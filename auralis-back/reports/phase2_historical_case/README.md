# Selección histórica — Fase 2

Informe: [docs/phase2.md](../../../docs/phase2.md).

Secuencia seleccionada: cinco archivos locales de disco completo, 24/25/28/29/30 de marzo de 2022, con NOAA 12975 presente en los boletines SRS. El SI es global; la asociación regional no es una máscara ni un registro espacial. La llamarada X1.3 del 30-mar sucede después de la última imagen.

- `recommended_sequence.csv`: los cinco estados con fechas TAI/UTC, etiquetas SI originales, predicciones deterministas V3.1, hashes, partición y contexto NOAA/HARP.
- `candidates.md` / `candidates.csv`: los 35 candidatos de cinco episodios históricos.
- `local_inventory.csv`: 1.314 observaciones locales únicas; no son imágenes nuevas.
- `five_state_windows_up_to_10_days.csv`: 953 ventanas de cinco observaciones consecutivas, sin reordenar por SI.
- `cataloged_mx_events.csv`: filas M/X de los boletines consultados; no es un catálogo exhaustivo ni deduplicado de todos los eventos.
- `sources/`: sólo metadatos de texto NOAA/JSOC y manifiesto de consultas, con URLs, hashes, tiempos y errores. Los datos oficiales se conservan sin corregir silenciosamente discrepancias de catálogo.
- `selected_magnetograms.png`: lámina derivada de matrices existentes, sin certificar orientación WCS.
- `activity_evolution.png` / `.svg`: SI real y estimado con tiempos reales; líneas de conexión sin reconstrucción física de intervalos.
- `verification.json` / `manifest.json`: verificaciones y hashes reproducibles.

Reproducir desde la raíz de Auralis:

```bash
/Users/alejandro/.pyenv/versions/3.12.7/bin/python3 auralis-back/scripts/select_phase2_history.py
```

La ejecución es offline, consume los snapshots ya archivados y regenera los resultados derivados. No cambia modelos, datos originales, API ni frontend. No desarrolla el gemelo ni inicia fases posteriores.
