"""Comando `manage.py iniciar`: sobe o servidor para toda a rede e abre o navegador."""

import socket
import threading
import webbrowser

from django.core.management.commands.runserver import Command as RunServerCommand


def ip_local():
    """Descobre o IP da máquina na rede local."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class Command(RunServerCommand):
    help = "Igual ao runserver, mas sobe em 0.0.0.0:8000 e abre o navegador"

    def handle(self, *args, **options):
        # Se não passar endereço, fica aberto para qualquer PC da rede
        if not options.get("addrport"):
            options["addrport"] = "0.0.0.0:8000"
        super().handle(*args, **options)

    def inner_run(self, *args, **options):
        ip = ip_local()

        def ao_iniciar():
            webbrowser.open("http://127.0.0.1:8000/")

        threading.Timer(1.5, ao_iniciar).start()
        self.stdout.write(self.style.SUCCESS(
            f"\nNeste PC:     http://127.0.0.1:8000/\n"
            f"Outro PC:     http://{ip}:8000/\n"
        ))
        super().inner_run(*args, **options)
