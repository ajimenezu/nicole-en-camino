import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def ip_del_cliente(request: Request) -> str:
    """IP de quien hace el pedido, para contar los límites por persona.

    En Vercel la conexión llega desde su proxy, así que la IP del socket es
    la misma para todos: contar por ella convertía cada límite en un balde
    único compartido por todos los invitados, y abrir la invitación desde
    un grupo de WhatsApp agotaba el cupo de todos a la vez. Vercel pone la
    IP real en `x-real-ip` y la sobrescribe siempre, así que ahí el cliente
    no la puede falsear.

    Fuera de Vercel (local, tests) ese header lo escribe quien quiera, así
    que no se le cree y se usa la IP de la conexión.
    """
    if os.environ.get("VERCEL"):
        ip = request.headers.get("x-real-ip", "").strip()
        if ip:
            return ip
    return get_remote_address(request)


limiter = Limiter(key_func=ip_del_cliente)
