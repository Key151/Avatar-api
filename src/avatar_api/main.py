"""Cliente HTTP inicial do projeto Avatar API."""

import json

import requests

# API de personagens de Avatar: A Lenda de Aang
URL = "https://last-airbender-api.fly.dev/api/v1/characters"


def main():
    # 1. Faz a requisição GET
    resposta = requests.get(URL)

    # 2. Pega a resposta em JSON (vira uma lista de dicionários no Python)
    dados = resposta.json()

    # 3. Imprime o conteúdo formatado
    print(json.dumps(dados, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
