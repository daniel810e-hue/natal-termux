# GAMKERS Site Monitor

Monitor de sites para Termux, Android, Linux e Windows. Mostra status HTTP, tempo de resposta, DNS, conexão, validade do SSL e salva um histórico em CSV.

Use somente em sites seus ou que você tenha autorização para monitorar.

## Instalar (um comando só)

Cole no Termux:

```
curl -sL https://raw.githubusercontent.com/daniel810e-hue/gamkers-monitor/main/install.sh | bash
```

## Rodar

```
monitor
```

Os arquivos `monitor_config.json`, `sites.txt` e o histórico CSV ficam em `~/gamkers-monitor`.

## Atualizar

Rode o comando de instalação de novo. Suas configurações e sites salvos não são apagados.

## Desinstalar

```
rm -rf ~/gamkers-monitor $PREFIX/bin/monitor
```
