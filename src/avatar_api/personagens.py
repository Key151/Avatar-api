"""Traduz os atributos name e affiliation da Last Airbender API."""

import sys

import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator

# Evita erro de codificação no console do Windows
sys.stdout.reconfigure(encoding="utf-8")

URL = "https://last-airbender-api.fly.dev/api/v1/characters"


def buscar_personagens():
    """Faz uma requisição GET e devolve a lista de personagens."""
    resposta = requests.get(URL)
    return resposta.json()


def traduzir(texto):
    """Traduz um texto para o português (Google, com reserva no MyMemory)."""
    if not texto or not texto.strip():
        return texto
    try:
        return GoogleTranslator(source="auto", target="pt").translate(texto)
    except Exception:
        return MyMemoryTranslator(source="en-US", target="pt-BR").translate(texto)


def main():
    personagens = buscar_personagens()

    # Mostra os 3 primeiros personagens traduzidos
    for personagem in personagens[:3]:
        nome = personagem["name"]              # ex: Aang
        afiliacao = personagem["affiliation"]  # ex: Air Nomads, Team Avatar...

        print(f"Original  -> Nome: {nome} | Afiliação: {afiliacao.strip()}")
        print(f"Traduzido -> Nome: {traduzir(nome)} | Afiliação: {traduzir(afiliacao)}")
        print("-" * 60)


if __name__ == "__main__":
    main()
