# API Covid-19

Este é um guia rápido para usar o código fornecido para criar uma API de consulta de dados a partir de um banco de dados SQLite.

## Requisitos

Certifique-se de ter os seguintes requisitos instalados:

- Python 3.x
- Flask (instale com `pip install Flask`)
- SQLite3 (já integrado ao Python)

## Uso

**Configuração Inicial**:
- Certifique-se de ter um banco de dados SQLite chamado `latest.db` na mesma pasta onde este código está localizado. Esse banco de dados deve conter as tabelas `location` e `timeseries`.
- Defina as variáveis `gz_file`, e `db_file` de acordo com os nomes de seus arquivos e caminhos.

**Execução do Servidor**:
- Execute o servidor Flask com o seguinte comando:

```bash
$ python api.py
```

**Download e Extração de Dados**:
- Quando você acessa a raiz (`/`) no navegador, o código verifica se um download está em andamento. Se estiver, você verá "Download em andamento...". Se não, ele iniciará o download do arquivo, extrairá o banco de dados e retornará "Download concluído!" ou "Falha no download!".

**Consulta de Dados**:
- Para consultar dados, acesse `/api/consultar` com os seguintes parâmetros na URL:
- `level`: Nível administrativo (1, 2 ou 3).
- `location`: Nome da localização.
- `start_date`: Data de início no formato YYYY-MM-DD.
- `end_date`: Data de término no formato YYYY-MM-DD.
- `campos[]`: Uma lista de campos que você deseja retornar na consulta.

Exemplo de consulta:

```
suaurl.com/api/consultar?level=1&location=Brasil&start_date=2023-01-01&end_date=2023-12-31&campos[]=confirmed&campos[]=deaths
```

Isso retornará um JSON com os resultados da consulta:

```json
[
    {
    "confirmed": 1,
    "date": "2020-02-25",
    "id": "59d3b85f",
    "people_fully_vaccinated": null,
    "school_closing": 0
    },
    ...
]
```

**Notas Importantes**:
- O código suporta downloads assíncronos, para que outros clientes vejam "Download em andamento..." se o download estiver em andamento.

## Créditos

API desenvolvida para o trabalho final da disciplina de Séries Temporais. O projeto completo pode ser encontrado em [time-series](https://github.com/heitortanoue/time-series).

👤 **Heitor Tanoue de Mello**
