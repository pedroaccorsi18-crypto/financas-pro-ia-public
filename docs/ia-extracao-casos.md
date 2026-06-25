# Casos anonimizados para extracao por IA

## Objetivo

Manter uma pequena suite de exemplos sinteticos para avaliar se a saida esperada
do Gemini continua compativel com o fluxo de homologacao do app.

Esses casos nao substituem testes com PDFs reais em ambiente controlado. Eles
servem como contrato publico e seguro para:

- formato do JSON retornado pela IA;
- tipos e categorias aceitos pelo app;
- mes de referencia no formato `MM/AAAA`;
- ausencia de identificadores pessoais obvios;
- compatibilidade com `preparar_transacoes_importadas`.

## Local dos casos

Os exemplos ficam em:

```text
tests/fixtures/ia_extracao/
```

Cada arquivo possui:

- `case_id`;
- `source_summary`, com descricao sintetica do documento;
- `expected_output`, simulando a resposta estruturada esperada da IA.

## Casos atuais

| Caso | Cobertura |
| --- | --- |
| `fatura_cartao_basica` | Despesas de cartao, assinatura, alimentacao fora e pagamento. |
| `extrato_bancario_misto` | Receita, transporte, moradia e saude em extrato. |
| `comprovante_reembolso` | Comprovante simples com receita de reembolso. |

## Como validar

```powershell
.\scripts\check.ps1
```

Ou, para rodar apenas essa suite:

```powershell
python -m unittest tests.test_ia_extraction_cases -v
```

## Regras para novos casos

- Usar apenas dados sinteticos.
- Nao incluir e-mail real, CPF, telefone, endereco, numero de cartao, agencia ou conta.
- Preferir nomes genericos como `Banco Exemplo`, `Empresa Exemplo` e `Mercado Bairro`.
- Manter categorias dentro de `CATEGORIAS_VALIDAS`.
- Manter tipos dentro de `Despesa` ou `Receita`.
- Manter `mes_fatura` no formato `MM/AAAA`.
