"""Constants for the BCU exchange-rate web services (cotizaciones.bcu.gub.uy).

The Banco Central del Uruguay publishes daily closing exchange rates over three
public SOAP 1.1 services (no auth). There is no REST equivalent, so the client
wraps the synchronous ``zeep`` library in threads.
"""

from __future__ import annotations

API_NAME = "bcu.gub.uy / cotizaciones"
MODULE = "bcu"

# The three public WSDLs (anonymous, no credentials required).
WSDL_COTIZACIONES = (
    "https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcucotizaciones?wsdl"
)
WSDL_MONEDAS = "https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcumonedas?wsdl"
WSDL_ULTIMO_CIERRE = (
    "https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsultimocierre?wsdl"
)

# Currency groups understood by the services.
GROUP_DIVISAS = 2  # foreign currencies / banknotes (USD, ARS, BRL, ...)
GROUP_LOCAL = 0  # local indexed units (UI, UR, UP) — Fecha may be empty (see gotchas)

# Canonical USD code (DLS. USA BILLETE) — the rate users mean by "el dólar".
USD_CODE = 2225
