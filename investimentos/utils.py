import requests, pymongo
from decimal import Decimal
from django.utils import timezone
from .models import Ativos, Cotacao, ConfiguracaoAtivo
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime


def conexao_db():
    client = pymongo.MongoClient("localhost", 27017)
    database = client["INOAinvestimentos"]

    return client


def obter_dados_ativos(codigo):
    url = "https://brapi.dev/api/quote/{}?range=1d&interval=1d&fundamental=true&dividends=false".format(
        codigo
    )
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        return dados
    else:
        return None


def salvar_dados_BD(dados, user):
    # Obter os dados do primeiro resultado
    resultado = dados["results"][0]
    symbol = resultado["symbol"]
    longName = resultado["longName"]
    currency = resultado["currency"]
    regularMarketPrice = Decimal(resultado["regularMarketPrice"])
    regularMarketDayHigh = Decimal(resultado["regularMarketDayHigh"])
    regularMarketDayLow = Decimal(resultado["regularMarketDayLow"])
    regularMarketTime = timezone.now()

    # Criar ou atualizar o objeto Ativos
    ativo, created = Ativos.objects.update_or_create(
        symbol=symbol,
        defaults={
            "symbol": symbol,
            "nome": longName,
            "moeda": currency,
            "data_atualizacao": regularMarketTime,
        },
    )

    # Criar a instância de Cotacao
    cotacao = Cotacao.objects.create(
        user=user,
        ativo=ativo,
        symbol=symbol,
        currency=currency,
        regularMarketPrice=regularMarketPrice,
        regularMarketDayHigh=regularMarketDayHigh,
        regularMarketDayLow=regularMarketDayLow,
        regularMarketTime=regularMarketTime,
    )


def configuracao_ativo(user, codigo, limite_inferior, limite_superior):
    try:
        # Tenta obter a configuração existente com o mesmo símbolo e usuário
        configuracao = ConfiguracaoAtivo.objects.get(user=user, symbol=codigo)
        # Atualiza os limites inferiores e superiores da configuração existente
        configuracao.limite_inferior = limite_inferior
        configuracao.limite_superior = limite_superior
        configuracao.save()
    except ConfiguracaoAtivo.DoesNotExist:
        # Se não existir uma configuração com o mesmo símbolo e usuário, cria uma nova configuração
        configuracao = ConfiguracaoAtivo.objects.create(
            user=user,
            symbol=codigo,
            limite_inferior=limite_inferior,
            limite_superior=limite_superior,
        )


def salvando_codigos_ativos():
    api_url = "https://brapi.dev/api/available"
    response = requests.get(api_url)
    data = response.json()

    indices = data["indexes"]
    stocks = data["stocks"]

    codigos = indices + stocks
    return codigos