# Teste de carga do site

Teste de carga em estágios (sobe a carga aos poucos) para descobrir em que ponto o seu site começa a degradar. Mostra RPS, % de falhas e tempos p50/p95/p99.

Use só no seu próprio site.

## Instalar (um comando só)

Cole no Termux:

```
curl -sL https://raw.githubusercontent.com/daniel810e-hue/teste-carga-site/main/install.sh | bash
```

## Rodar

```
carga
```

O resultado também é salvo em `resultado_teste_carga.csv` na pasta onde você rodou o comando.

## Configurar

Para mudar o site, os estágios ou os limites:

```
nano ~/teste-carga-site/teste_carga_site.py
```

Procure as variáveis `URLS` e `ESTAGIOS` no começo do arquivo.

## Atualizar

Rode o comando de instalação de novo.

## Desinstalar

```
rm -rf ~/teste-carga-site $PREFIX/bin/carga
```
