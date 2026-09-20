"""Freno de fuerza bruta para el login, contado por email.

Por que no alcanza con limitar por IP: quien ataca puede rotar de IP
(una red movil, una VPN), y el limite por IP de slowapi es holgado a
proposito. El freno por email en cambio sigue a la cuenta atacada, sin
importar desde donde lleguen los intentos. Cada cuenta tiene su ventana
y el limite por IP queda como freno grueso de respaldo.

Vive en memoria a proposito, y eso tiene un costo conocido: en Vercel
puede haber varias instancias de la funcion a la vez y cada una lleva su
propia cuenta, que ademas se pierde cuando la instancia se apaga. El
freno sigue cortando rafagas, pero es aproximado. Si hiciera falta uno
exacto, esto va a la base o a Redis.
"""

from datetime import UTC, datetime, timedelta

VENTANA = timedelta(minutes=15)
MAX_INTENTOS = 8
# Tope de cuentas vigiladas a la vez. Sin esto, alguien podria hacer
# crecer el diccionario probando un email distinto cada vez.
MAX_EMAILS = 1000

_fallos: dict[str, list[datetime]] = {}


def _vigentes(email: str, ahora: datetime) -> list[datetime]:
    """Fallos de esa cuenta dentro de la ventana, descartando los viejos."""
    recientes = [t for t in _fallos.get(email, []) if ahora - t < VENTANA]
    if recientes:
        _fallos[email] = recientes
    else:
        _fallos.pop(email, None)
    return recientes


def _purgar(ahora: datetime) -> None:
    for email in list(_fallos):
        _vigentes(email, ahora)


def esta_bloqueado(email: str) -> bool:
    return len(_vigentes(email, datetime.now(UTC))) >= MAX_INTENTOS


def registrar_fallo(email: str) -> None:
    ahora = datetime.now(UTC)
    if len(_fallos) >= MAX_EMAILS:
        _purgar(ahora)
    _fallos.setdefault(email, []).append(ahora)


def limpiar(email: str) -> None:
    """Un login exitoso borra el historial: la cuenta no arrastra fallos."""
    _fallos.pop(email, None)


def reiniciar() -> None:
    """Solo para los tests, que necesitan arrancar de cero."""
    _fallos.clear()
