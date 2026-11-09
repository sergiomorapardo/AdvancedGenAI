"""Servidores MCP del curso: la cartera de créditos y las políticas de ACME."""

import os
import sys


def prepare_stderr() -> None:
    """Da a Jupyter en Windows el descriptor de stderr que ya tiene en Linux y macOS.

    En Windows, el sys.stderr de ipykernel no tiene fileno() y los clientes MCP por
    stdio no pueden arrancar el servidor como subproceso. Con el descriptor, el stderr
    del servidor va a la consola de Jupyter, como en macOS. Fuera de ese caso no hace nada.
    """
    if sys.platform != "win32" or "ipykernel" not in sys.modules:
        return
    from ipykernel.iostream import OutStream

    if not isinstance(sys.stderr, OutStream):
        return
    try:
        sys.stderr.fileno()
    except OSError:  # io.UnsupportedOperation
        try:
            descriptor = os.dup(2)
        except OSError:  # el kernel arrancó sin consola
            descriptor = os.open(os.devnull, os.O_WRONLY)
        sys.stderr._original_stdstream_copy = descriptor
