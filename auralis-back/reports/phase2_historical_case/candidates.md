# Candidatos locales auditados — Fase 2

SI real = etiqueta original guardada; predicción = ONNX V3.1 determinista CPU.
UTC convierte el tiempo de registro TAI; no sustituye T_OBS. NOAA y HARP son contexto externo, no una máscara del archivo.
Las posiciones SRS son válidas a las 00:00 UTC del día. Ausente = no figura en la tabla I del boletín, no prueba de ausencia física absoluta.
HARP es una asociación de catálogo a lo largo de su vida y puede incluir varias regiones.

## 2017_sep: NOAA 12673; evento de contexto X9.3, 2017-09-06T12:02:00Z

| Archivo local | Registro UTC | SI real | V3.1 ONNX | NOAA en SRS / posición | Tipo magnético | HARP | Split |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| [hmi.m_45s.2017.08.23_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.08.23_00_01_30_TAI.magnetogram_processed.npy) | 2017-08-23T00:00:53.000Z | 1.560092 | 1.490665 | [12673: Ausente en tabla I](sources/20170823SRS.txt) | unknown | 7115 | train |
| [hmi.m_45s.2017.08.28_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.08.28_00_01_30_TAI.magnetogram_processed.npy) | 2017-08-28T00:00:53.000Z | 1.479721 | 1.414902 | [12673: Ausente en tabla I](sources/20170828SRS.txt) | unknown | 7115 | selection_validation |
| [hmi.m_45s.2017.08.30_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.08.30_00_01_30_TAI.magnetogram_processed.npy) | 2017-08-30T00:00:53.000Z | 1.473784 | 1.432392 | [12673: S08E62](sources/20170830SRS.txt) | Alpha | 7115 | selection_validation |
| [hmi.m_45s.2017.08.31_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.08.31_00_01_30_TAI.magnetogram_processed.npy) | 2017-08-31T00:00:53.000Z | 1.508963 | 1.439879 | [12673: S08E48](sources/20170831SRS.txt) | Alpha | 7115 | train |
| [hmi.m_45s.2017.09.03_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.09.03_00_01_30_TAI.magnetogram_processed.npy) | 2017-09-03T00:00:53.000Z | 1.648891 | 1.528312 | [12673: S10E09](sources/20170903SRS.txt) | Beta | 7115 | train |
| [hmi.m_45s.2017.09.13_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.09.13_00_01_30_TAI.magnetogram_processed.npy) | 2017-09-13T00:00:53.000Z | 1.450807 | 1.381470 | [12673: Ausente en tabla I](sources/20170913SRS.txt) | unknown | 7115 | selection_validation |
| [hmi.m_45s.2017.09.14_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2017.09.14_00_01_30_TAI.magnetogram_processed.npy) | 2017-09-14T00:00:53.000Z | 1.421493 | 1.373340 | [12673: Ausente en tabla I](sources/20170914SRS.txt) | unknown | 7115 | selection_validation |

## 2022_mar: NOAA 12975; evento de contexto X1.3, 2022-03-30T17:37:00Z

| Archivo local | Registro UTC | SI real | V3.1 ONNX | NOAA en SRS / posición | Tipo magnético | HARP | Split |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| [hmi.m_45s.2022.03.24_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.03.24_00_01_30_TAI.magnetogram_processed.npy) | 2022-03-24T00:00:53.000Z | 1.679617 | 1.470520 | [12975: N13E63](sources/20220324SRS.txt) | Beta | 8088 | train |
| [hmi.m_45s.2022.03.25_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.03.25_00_01_30_TAI.magnetogram_processed.npy) | 2022-03-25T00:00:53.000Z | 1.717091 | 1.477280 | [12975: N14E55](sources/20220325SRS.txt) | Beta | 8088 | train |
| [hmi.m_45s.2022.03.28_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.03.28_00_01_30_TAI.magnetogram_processed.npy) | 2022-03-28T00:00:53.000Z | 1.947987 | 1.656259 | [12975: N12E05](sources/20220328SRS.txt) | Beta | 8088 | selection_validation |
| [hmi.m_45s.2022.03.29_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.03.29_00_01_30_TAI.magnetogram_processed.npy) | 2022-03-29T00:00:53.000Z | 2.057672 | 1.683445 | [12975: N13W12](sources/20220329SRS.txt) | Beta-Gamma | 8088 | train |
| [hmi.m_45s.2022.03.30_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.03.30_00_01_30_TAI.magnetogram_processed.npy) | 2022-03-30T00:00:53.000Z | 2.050173 | 1.712676 | [12975: N13W25](sources/20220330SRS.txt) | Beta-Gamma-Delta | 8088 | train |
| [hmi.m_45s.2022.04.01_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.04.01_00_01_30_TAI.magnetogram_processed.npy) | 2022-04-01T00:00:53.000Z | 1.980442 | 1.698625 | [12975: N13W52](sources/20220401SRS.txt) | Beta-Gamma-Delta | 8088 | selection_validation |
| [hmi.m_45s.2022.04.03_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.04.03_00_01_30_TAI.magnetogram_processed.npy) | 2022-04-03T00:00:53.000Z | 2.009070 | 1.643563 | [12975: N15W78](sources/20220403SRS.txt) | Beta-Delta | 8088 | train |
| [hmi.m_45s.2022.04.05_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2022.04.05_00_01_30_TAI.magnetogram_processed.npy) | 2022-04-05T00:00:53.000Z | 1.930135 | 1.588688 | [12975: Ausente en tabla I](sources/20220405SRS.txt) | unknown | 8088 | selection_validation |

## 2023_dec: NOAA 13514; evento de contexto X2.8, 2023-12-14T17:02:00Z

| Archivo local | Registro UTC | SI real | V3.1 ONNX | NOAA en SRS / posición | Tipo magnético | HARP | Split |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| [hmi.m_45s.2023.12.08_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2023.12.08_00_01_30_TAI.magnetogram_processed.npy) | 2023-12-08T00:00:53.000Z | 1.818812 | 1.661302 | [13514: N09E51](sources/20231208SRS.txt) | Beta | 10489 | selection_validation |
| [hmi.m_45s.2023.12.11_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2023.12.11_00_01_30_TAI.magnetogram_processed.npy) | 2023-12-11T00:00:53.000Z | 1.694417 | 1.549359 | [13514: N10E07](sources/20231211SRS.txt) | Beta | 10489 | train |
| [hmi.m_45s.2023.12.13_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2023.12.13_00_01_30_TAI.magnetogram_processed.npy) | 2023-12-13T00:00:53.000Z | 1.688373 | 1.556627 | [13514: N10W22](sources/20231213SRS.txt) | Beta | 10489 | train |
| [hmi.m_45s.2023.12.16_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2023.12.16_00_01_30_TAI.magnetogram_processed.npy) | 2023-12-16T00:00:53.000Z | 1.778257 | 1.621051 | [13514: N05W68](sources/20231216SRS.txt) | Beta-Gamma-Delta | 10489 | selection_validation |
| [hmi.m_45s.2023.12.17_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2023.12.17_00_01_30_TAI.magnetogram_processed.npy) | 2023-12-17T00:00:53.000Z | 1.801836 | 1.622404 | [13514: N05W82](sources/20231217SRS.txt) | Beta-Gamma | 10489 | train |
| [hmi.m_45s.2023.12.18_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2023.12.18_00_01_30_TAI.magnetogram_processed.npy) | 2023-12-18T00:00:53.000Z | 1.845002 | 1.689409 | [13514: N05W94](sources/20231218SRS.txt) | Beta-Gamma | 10489 | train |

## 2024_may: NOAA 13664; evento de contexto X8.7, 2024-05-14T16:51:00Z

| Archivo local | Registro UTC | SI real | V3.1 ONNX | NOAA en SRS / posición | Tipo magnético | HARP | Split |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| [hmi.m_45s.2024.05.04_00_03_45_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.05.04_00_03_45_TAI.magnetogram_processed.npy) | 2024-05-04T00:03:08.000Z | 2.191842 | 1.712777 | [13664: S18E41](sources/20240504SRS.txt) | Beta-Gamma | 11149 | train |
| [hmi.m_45s.2024.05.05_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.05.05_00_01_30_TAI.magnetogram_processed.npy) | 2024-05-05T00:00:53.000Z | 2.019542 | 1.731662 | [13664: S19E28](sources/20240505SRS.txt) | Beta-Delta | 11149 | train |
| [hmi.m_45s.2024.05.08_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.05.08_00_01_30_TAI.magnetogram_processed.npy) | 2024-05-08T00:00:53.000Z | 2.118814 | 1.790458 | [13664: S20W09](sources/20240508SRS.txt) | Beta-Gamma-Delta | 11149 | train |
| [hmi.m_45s.2024.05.10_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.05.10_00_01_30_TAI.magnetogram_processed.npy) | 2024-05-10T00:00:53.000Z | 2.119255 | 1.755643 | [13664: S19W34](sources/20240510SRS.txt) | Beta-Gamma-Delta | 11149 | selection_validation |
| [hmi.m_45s.2024.05.11_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.05.11_00_01_30_TAI.magnetogram_processed.npy) | 2024-05-11T00:00:53.000Z | 2.062845 | 1.749627 | [13664: S17W48](sources/20240511SRS.txt) | Beta-Gamma-Delta | 11149 | selection_validation |
| [hmi.m_45s.2024.05.15_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.05.15_00_01_30_TAI.magnetogram_processed.npy) | 2024-05-15T00:00:53.000Z | 2.290875 | 1.954747 | [13664: Ausente en tabla I](sources/20240515SRS.txt) | unknown | 11149 | train |

## 2024_oct: NOAA 13842; evento de contexto X9.0, 2024-10-03T12:18:00Z

| Archivo local | Registro UTC | SI real | V3.1 ONNX | NOAA en SRS / posición | Tipo magnético | HARP | Split |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| [hmi.m_45s.2024.09.25_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.09.25_00_01_30_TAI.magnetogram_processed.npy) | 2024-09-25T00:00:53.000Z | 1.940441 | 1.721740 | [13842: Ausente en tabla I](sources/20240925SRS.txt) | unknown | 11930 | train |
| [hmi.m_45s.2024.09.26_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.09.26_00_01_30_TAI.magnetogram_processed.npy) | 2024-09-26T00:00:53.000Z | 1.966500 | 1.749103 | [13842: Ausente en tabla I](sources/20240926SRS.txt) | unknown | 11930 | train |
| [hmi.m_45s.2024.09.29_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.09.29_00_01_30_TAI.magnetogram_processed.npy) | 2024-09-29T00:00:53.000Z | 2.193981 | 1.897241 | [13842: S14E57](sources/20240929SRS.txt) | Beta-Gamma | 11930 | train |
| [hmi.m_45s.2024.10.03_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.10.03_00_01_30_TAI.magnetogram_processed.npy) | 2024-10-03T00:00:53.000Z | 2.502763 | 2.063811 | [13842: S15E06](sources/20241003SRS.txt) | Beta-Gamma-Delta | 11930 | selection_validation |
| [hmi.m_45s.2024.10.06_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.10.06_00_01_30_TAI.magnetogram_processed.npy) | 2024-10-06T00:00:53.000Z | 2.437609 | 2.018522 | [13842: S14W35](sources/20241006SRS.txt) | Beta-Gamma-Delta | 11930 | train |
| [hmi.m_45s.2024.10.07_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.10.07_00_01_30_TAI.magnetogram_processed.npy) | 2024-10-07T00:00:53.000Z | 2.344781 | 1.981516 | [13842: S16W50](sources/20241007SRS.txt) | Beta-Gamma-Delta | 11930 | selection_validation |
| [hmi.m_45s.2024.10.09_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.10.09_00_01_30_TAI.magnetogram_processed.npy) | 2024-10-09T00:00:53.000Z | 2.256125 | 1.884996 | [13842: S13W76](sources/20241009SRS.txt) | Beta-Gamma | 11930 | train |
| [hmi.m_45s.2024.10.10_00_01_30_TAI.magnetogram_processed.npy](../../data/processed/hmi.m_45s.2024.10.10_00_01_30_TAI.magnetogram_processed.npy) | 2024-10-10T00:00:53.000Z | 2.295727 | 1.924174 | [13842: S13W90](sources/20241010SRS.txt) | Beta-Gamma | 11930 | train |

Los CSV conservan precisión completa, hashes, filas originales, fecha CSV de escala desconocida, diferencias temporales al evento, otras regiones presentes y alcance de las asociaciones.
