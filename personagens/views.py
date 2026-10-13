"""Views do app personagens: consome a API e traduz os atributos."""

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, wait

import requests
from deep_translator import GoogleTranslator
from django.core.cache import cache
from django.shortcuts import render

from .nomes_oficiais import NOMES_OFICIAIS

API = "https://last-airbender-api.fly.dev/api/v1/characters"
POR_PAGINA = 20      # a API devolve 20 personagens por página
TOTAL_PAGINAS = 25   # a API tem 497 personagens no total
CHAVE = "trad:"      # prefixo das chaves no cache
TEMPO_MAX_TRADUCAO = 3   # segundos: depois disso a página segue sem esperar

# Dicionário local: termos do universo Avatar + palavras comuns das afiliações.
# Serve de reserva quando o Google/MyMemory estão bloqueados.
Dicionario = [
    # --- frases longas (substituídas primeiro) ---
    ("Order of the White Lotus", "Ordem do Lótus Branco"),
    ("Military of the Fire Nation", "Exército da Nação do Fogo"),
    ("Military of the Earth Empire", "Exército do Império da Terra"),
    ("Fire Nation Royal Family", "Família Real da Nação do Fogo"),
    ("Earth Kingdom Air Force", "Força Aérea do Reino da Terra"),
    ("Metalbending Police Force", "Polícia de Metalmancança"),
    ("Metalbending Academy", "Academia de Metalmancança"),
    ("Northern Water Tribe", "Tribo da Água do Norte"),
    ("Southern Water Tribe", "Tribo da Água do Sul"),
    ("Foggy Swamp Tribe", "Tribo da Charco Nebuloso"),
    ("Triple Threat Triad", "Tríade Tripla Ameaça"),
    ("Council of Elders", "Conselho de Anciãos"),
    ("Earth Kingdom military", "Exército do Reino da Terra"),
    ("Earth Kingdom government", "Governo do Reino da Terra"),
    ("Fire Nation military", "Exército da Nação do Fogo"),
    ("Fire Nation Navy", "Marinha da Nação do Fogo"),
    ("Fire Nation school", "Escola da Nação do Fogo"),
    ("Air Acolytes", "Acólitos do Ar"),
    ("Air Scouts", "Batedores do Ar"),
    ("Air Temples", "Templos do Ar"),
    ("Air Temple", "Templo do Ar"),
    ("Rough Rhinos", "Rinocerontes Selvagens"),
    ("Sun Warriors", "Guerreiros do Sol"),
    ("Metal Clan", "Clã do Metal"),
    ("Sato family", "Família Sato"),
    ("Beifong family", "Família Beifong"),
    ("Red Lotus", "Lótus Vermelho"),
    ("Team Avatar", "Equipe Avatar"),
    ("White Lotus", "Lótus Branco"),
    ("Republic City", "Cidade da República"),
    ("Air Temple Island", "Ilha do Templo do Ar"),
    ("Earth Rumble", "Abalo Terrestre"),
    ("Fire Nation", "Nação do Fogo"),
    ("Earth Kingdom", "Reino da Terra"),
    ("Air Nomads", "Nômades do Ar"),
    ("Air Nation", "Nação do Ar"),
    ("Water Tribe", "Tribo da Água"),
    ("Spirit World", "Mundo Espiritual"),
    ("Equalists", "Equalistas"),
    ("Earth Empire", "Império da Terra"),
    # --- palavras soltas ---
    ("(formerly)", "(anteriormente)"),
    ("formerly", "anteriormente"),
    ("Royal Family", "Família Real"),
    ("Air Force", "Força Aérea"),
    ("government", "governo"),
    ("military", "exército"),
    ("academy", "academia"),
    ("school", "escola"),
    ("police", "polícia"),
    ("deserted", "desertou"),
    ("family", "família"),
    ("captain", "capitão"),
    ("leader", "líder"),
    ("teacher", "professor"),
    ("island", "ilha"),
    ("temple", "templo"),
    ("clan", "clã"),
    ("tribe", "tribo"),
    ("nation", "nação"),
    ("kingdom", "reino"),
    ("empire", "império"),
    ("city", "cidade"),
    ("navy", "marinha"),
    ("army", "exército"),
    ("world", "mundo"),
    ("lotus", "lótus"),
    ("fire", "fogo"),
    ("earth", "terra"),
    ("water", "água"),
    ("air", "ar"),
    ("man", "homem"),
    ("men", "homens"),
    ("woman", "mulher"),
    ("king", "rei"),
    ("queen", "rainha"),
    ("prince", "príncipe"),
    ("princess", "princesa"),
    ("general", "general"),
    ("soldier", "soldado"),
    ("guard", "guarda"),
    ("spirit", "espírito"),
    ("spirits", "espíritos"),
    ("swamp", "pântano"),
    ("academy", "academia"),
]


def _chave_cache(texto):
    """Transforma o texto em uma chave segura (sem espaços)."""
    digesto = hashlib.md5(texto.encode("utf-8")).hexdigest()
    return CHAVE + digesto


def traduzir_dicionario(texto):
    """Traduz usando o dicionário local (frases longas primeiro)."""
    resultado = texto
    for ingles, portugues in Dicionario:
        padrao = r"(?<![A-Za-z])" + re.escape(ingles) + r"(?![A-Za-z])"
        resultado = re.sub(padrao, portugues, resultado, flags=re.IGNORECASE)
    return resultado


def traduzir(texto):
    """Traduz para português usando o cache em arquivo.

    Ordem: cache -> dicionário local (instantâneo) -> Google -> MyMemory.
    O dicionário resolve a maioria dos termos do Avatar sem depender da internet.
    """
    if not texto or not texto.strip():
        return ""

    salvo = cache.get(_chave_cache(texto))
    if salvo is not None:
        return salvo

    do_dicionario = traduzir_dicionario(texto)
    if do_dicionario != texto:
        cache.set(_chave_cache(texto), do_dicionario, timeout=None)
        return do_dicionario

    # Dicionário não conhece: tenta o Google uma vez
    try:
        resultado = GoogleTranslator(source="auto", target="pt").translate(texto)
    except Exception:
        # Falhou: guarda o original por 1 hora para a página não
        # tentar traduzir de novo a cada carregamento
        cache.set(_chave_cache(texto), texto, timeout=3600)
        return texto

    cache.set(_chave_cache(texto), resultado, timeout=None)
    return resultado


def nome_oficial(texto):
    """Aplica o nome oficial pt-BR da dublagem; se não achar, mantém o original."""
    if not texto:
        return ""
    return NOMES_OFICIAIS.get(texto.strip(), texto.strip())


def parece_nome(texto):
    """Nomes próprios de uma palavra (ex: Zuko) não mudam na tradução."""
    t = texto.strip()
    return bool(t) and " " not in t and t[0].isupper()


def traduzido_ou_original(texto):
    """Pega do cache; se ainda não tem, mostra o original (sem traduzir agora)."""
    if not texto or not texto.strip():
        return ""
    salvo = cache.get(_chave_cache(texto))
    return salvo if salvo is not None else texto


def traduzir_em_paralelo(personagens_api):
    """Traduz o que falta, em paralelo, sem travar a página.

    O dicionário local roda na hora. Só o que ele não souber vai para
    o tradutor externo, em segundo plano (sem travar o carregamento).
    """
    textos = set()
    for p in personagens_api:
        # Nome, aliados e inimigos usam nome_oficial (não precisam de tradução)
        textos.add(p.get("affiliation", ""))

    pendentes = []
    for t in textos:
        if not t or not t.strip() or cache.get(_chave_cache(t)) is not None:
            continue
        do_dicionario = traduzir_dicionario(t)
        if do_dicionario != t:
            cache.set(_chave_cache(t), do_dicionario, timeout=None)
        else:
            pendentes.append(t)

    if not pendentes:
        return

    # Sem "with" e sem cancelar: as que não caberem no tempo máximo
    # terminam em segundo plano e ficam no cache para a próxima carga
    executor = ThreadPoolExecutor(max_workers=6)
    futuros = [executor.submit(traduzir, t) for t in pendentes]
    wait(futuros, timeout=TEMPO_MAX_TRADUCAO)
    executor.shutdown(wait=False)


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
        "nome": nome_oficial(p["name"]),
        "afiliacao": traduzido_ou_original(p.get("affiliation", "")),
        "aliados": ", ".join(nome_oficial(a) for a in p.get("allies", [])),
        "inimigos": ", ".join(nome_oficial(e) for e in p.get("enemies", [])),
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
