"""Constants for the health (salud) module.

All salud data is CKAN-backed by the national open-data portal
(catalogodatos.gub.uy, run by AGESIC, CKAN 2.10.6). This module implements its
own tiny CKAN client (mirroring the catalogodatos ``_action`` pattern) so it
stays self-contained — no cross-module imports.

Discovery defaults to ``groups:salud`` (276 datasets, broad: MSP, FNR, ASSE,
intendencias…) rather than ``organization:msp`` (only 7 datasets).
"""

from __future__ import annotations

API_NAME = "catalogodatos.gub.uy"
BASE_URL = "https://catalogodatos.gub.uy"
ACTION_URL = f"{BASE_URL}/api/3/action"
MODULE = "salud"

# Primary discovery surface for health data.
SALUD_GROUP = "salud"
# Recognized organizations that can be used as an extra filter on salud_buscar.
SALUD_ORGS = ("msp", "fondo-nacional-de-recursos")

# Policlínicas (ubicacion-de-policlinicas): its CSV is NOT datastore-active,
# so the tool resolves the dataset and returns the CSV download URL.
POLICLINICAS_DATASET = "ubicacion-de-policlinicas"

# FNR medication/treatment spending — its per-year CSV resources ARE
# datastore-active. There is NO "Formulario Terapéutico de Medicamentos" in
# this CKAN (see gotchas), so salud_medicamentos targets this dataset.
MEDICAMENTOS_DATASET = (
    "fondo-nacional-de-recursos-gasto-por-tratamientos-fondo-nacional-de-recursos"
)

# Cap CKAN page/row sizes so a single call never returns a megabyte blob.
MAX_ROWS = 100
DEFAULT_ROWS = 20
# Cap rows parsed from a downloaded CSV (policlínicas) client-side.
MAX_CSV_ROWS = 500
