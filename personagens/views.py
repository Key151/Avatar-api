"""Views do app personagens: consome a API e traduz os atributos."""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator
from django.shortcuts import render

API = "https://last-airbender-api.fly.dev/api/v1/characters"
POR_PAGINA = 20      # a API devolve 20 personagens por página
TOTAL_PAGINAS = 25   # a API tem 497 personagens no total


@lru_cache(maxsize=1024)
def traduzir(texto):
    """Traduz para português. O cache evita traduzir o mesmo texto duas vezes.

    Se os dois tradutores falharem, devolve o texto original em vez de quebrar.
    """
    if not texto or not texto.strip():
        return ""
    try:
        return GoogleTranslator(source="auto", target="pt").translate(texto)
    except Exception:
        pass
    try:
        return MyMemoryTranslator(source="en-US", target="pt-BR").translate(texto)
    except Exception:
        return texto


def traduzir_em_paralelo(personagens_api):
    """Pega todos os textos dos personagens e traduz vários ao mesmo tempo."""
    textos = set()
    for p in personagens_api:
        textos.update([p["name"], p.get("affiliation", "")])
        textos.update(p.get("allies", []))
        textos.update(p.get("enemies", []))

    com_texto = [t for t in textos if t and t.strip()]
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(traduzir, com_texto))


def pagina_na_url(request):
    """Lê o número da página na URL (ex: /?pagina=3), com segurança."""
    try:
        pagina = int(request.GET.get("pagina", 1))
    except ValueError:
        pagina = 1
    return max(1, min(pagina, TOTAL_PAGINAS))


def lista_personagens(request):
    pagina = pagina_na_url(request)

    personagens_api = requests.get(API, params={"page": pagina}, timeout=10).json()
    traduzir_em_paralelo(personagens_api)

    personagens = [{
        "nome": traduzir(p["name"]),
        "afiliacao": traduzir(p.get("affiliation", "")),
        "aliados": ", ".join(traduzir(a) for a in p.get("allies", [])),
        "inimigos": ", ".join(traduzir(e) for e in p.get("enemies", [])),
        "foto": p.get("photoUrl") or "",
    } for p in personagens_api]

    # Janela de 5 páginas ao redor da atual para o menu de paginação
    paginas = range(max(1, pagina - 2), min(TOTAL_PAGINAS, pagina + 2) + 1)

    return render(request, "personagens/lista.html", {
        "personagens": personagens,
        "pagina": pagina,
        "total_paginas": TOTAL_PAGINAS,
        "paginas": paginas,
        "tem_anterior": pagina > 1,
        "tem_proxima": pagina < TOTAL_PAGINAS,
        "offset": (pagina - 1) * POR_PAGINA,
    })
