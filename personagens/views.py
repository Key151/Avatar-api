"""Views do app personagens: consome a API e traduz os atributos."""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator
from django.shortcuts import render

API_URL = "https://last-airbender-api.fly.dev/api/v1/characters"
LIMITE = 10  # quantos personagens vamos traduzir por página


@lru_cache(maxsize=1024)
def traduzir(texto):
    """Traduz um texto para o português (Google, com reserva no MyMemory).

    O cache evita traduzir o mesmo texto de novo em próximas cargas da página.
    """
    if not texto or not texto.strip():
        return ""
    try:
        return GoogleTranslator(source="auto", target="pt").translate(texto)
    except Exception:
        return MyMemoryTranslator(source="en-US", target="pt-BR").translate(texto)


def traduzir_lista(itens):
    """Traduz cada item de uma lista e junta com vírgula."""
    return ", ".join(traduzir(item) for item in itens)


def lista_personagens(request):
    """Busca os personagens na API, traduz e mostra na página."""
    resposta = requests.get(API_URL, timeout=10)
    personagens_api = resposta.json()[:LIMITE]

    # Reúne todos os textos únicos e traduz vários ao mesmo tempo
    textos = set()
    for item in personagens_api:
        textos.add(item["name"])
        textos.add(item.get("affiliation", ""))
        textos.update(item.get("allies", []))
        textos.update(item.get("enemies", []))

    textos_para_traduzir = [t for t in textos if t and t.strip()]
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(traduzir, textos_para_traduzir))

    personagens = []
    for item in personagens_api:
        personagens.append({
            "nome": traduzir(item["name"]),
            "afiliacao": traduzir(item.get("affiliation", "")),
            "aliados": traduzir_lista(item.get("allies", [])),
            "inimigos": traduzir_lista(item.get("enemies", [])),
            "foto": item.get("photoUrl", ""),
        })

    return render(request, "personagens/lista.html", {"personagens": personagens})
