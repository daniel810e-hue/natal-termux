import os
import csv
import ssl
import json
import time
import socket
import platform
from urllib.parse import urlsplit
from datetime import datetime

# GAMKERS SITE MONITOR 6.0
# Termux, Android, Linux e Windows
# Use somente em sites seus ou que voce tenha autorizacao para monitorar.

VERSAO = "6.0"
ARQUIVO_CONFIG = "monitor_config.json"
ARQUIVO_SITES = "sites.txt"
TAMANHO_MAXIMO_CSV = 5 * 1024 * 1024
MAX_INTERVALO = 10.0
MIN_INTERVALO = 0.1

CONFIG = {
    "intervalo": 1.0,
    "timeout": 8.0,
    "historico": "monitor_historico.csv"
}

RESET = "\033[0m"
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
CIANO = "\033[96m"
AZUL = "\033[94m"
BRANCO = "\033[97m"
NEGRITO = "\033[1m"

CAMPOS = [
    "Data", "Site", "HTTP", "Tempo_ms",
    "DNS_ms", "Conexao_ms", "Resposta_ms",
    "SSL_dias", "Resultado"
]


def limpar():
    os.system("cls" if os.name == "nt" else "clear")


def titulo():
    print(CIANO + "=" * 58 + RESET)
    print(VERDE + NEGRITO + "             GAMKERS SITE MONITOR" + RESET)
    print(CIANO + "                    VERSION " + VERSAO + RESET)
    print(CIANO + "=" * 58 + RESET)


def pausa():
    input("\nPressione ENTER para continuar...")


def beep():
    """Emite um alerta sonoro quando possivel."""
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.MessageBeep()
        else:
            print("\a", end="", flush=True)
    except Exception:
        print("\a", end="", flush=True)


def formatar_tempo(valor):
    return "--" if valor is None else f"{valor:.2f} ms"


def porcentagem(valor, total):
    return round(valor * 100 / total, 2) if total else 0.0


def normalizar_url(url):
    url = url.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        partes = urlsplit(url)
        if partes.scheme not in ("http", "https") or not partes.hostname:
            return None
        if partes.port is not None and not 1 <= partes.port <= 65535:
            return None
        return url
    except ValueError:
        return None


# ---------------- CONFIGURACOES ----------------

def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            CONFIG.update(dados)
        except (OSError, ValueError, TypeError):
            print(AMARELO + "Configuracao invalida. Usando padroes." + RESET)

    try:
        CONFIG["intervalo"] = max(
            MIN_INTERVALO, min(float(CONFIG["intervalo"]), MAX_INTERVALO)
        )
        CONFIG["timeout"] = max(1.0, min(float(CONFIG["timeout"]), 120.0))
        CONFIG["historico"] = str(CONFIG["historico"]).strip()
        if not CONFIG["historico"]:
            CONFIG["historico"] = "monitor_historico.csv"
    except (ValueError, TypeError, KeyError):
        CONFIG.update({
            "intervalo": 1.0,
            "timeout": 8.0,
            "historico": "monitor_historico.csv"
        })


def salvar_config():
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        json.dump(CONFIG, arquivo, indent=4, ensure_ascii=False)


def ler_numero(texto, padrao, minimo, maximo):
    while True:
        valor = input(texto).strip().replace(",", ".")
        if not valor:
            return padrao
        try:
            numero = float(valor)
            if minimo <= numero <= maximo:
                return numero
            print(AMARELO + f"Digite um valor entre {minimo} e {maximo}." + RESET)
        except ValueError:
            print(VERMELHO + "Numero invalido." + RESET)


def configuracoes():
    limpar()
    titulo()
    print(NEGRITO + "CONFIGURACOES DO MONITOR" + RESET)

    CONFIG["intervalo"] = ler_numero(
        f"Intervalo atual {CONFIG['intervalo']}s (0.1 a 10): ",
        CONFIG["intervalo"], 0.1, 10.0
    )
    CONFIG["timeout"] = ler_numero(
        f"Timeout atual {CONFIG['timeout']}s (1 a 120): ",
        CONFIG["timeout"], 1.0, 120.0
    )

    print("Historico atual:", CONFIG["historico"])
    novo = input("Novo arquivo CSV (ENTER mantem): ").strip()
    if novo:
        CONFIG["historico"] = novo

    salvar_config()
    print(VERDE + "\nConfiguracoes salvas!" + RESET)
    pausa()


# ---------------- HISTORICO E CSV ----------------

def preparar_historico():
    caminho = CONFIG["historico"]
    if not os.path.exists(caminho):
        with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
            csv.writer(arquivo).writerow(CAMPOS)


def rotacionar_csv():
    caminho = CONFIG["historico"]
    if not os.path.exists(caminho):
        preparar_historico()
        return
    try:
        if os.path.getsize(caminho) >= TAMANHO_MAXIMO_CSV:
            antigo = caminho + ".1"
            if os.path.exists(antigo):
                os.remove(antigo)
            os.replace(caminho, antigo)
            preparar_historico()
    except OSError as erro:
        print(VERMELHO + "Erro na rotacao do CSV: " + str(erro) + RESET)


def salvar(url, dados):
    rotacionar_csv()
    preparar_historico()
    try:
        with open(CONFIG["historico"], "a", newline="", encoding="utf-8") as arquivo:
            csv.writer(arquivo).writerow([
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                url,
                dados["status"] if dados["status"] is not None else "",
                dados["tempo"],
                dados["dns"],
                dados["conexao"],
                dados["resposta"],
                dados["ssl_dias"] if dados["ssl_dias"] is not None else "",
                dados["resultado"]
            ])
    except OSError as erro:
        print(VERMELHO + "Erro ao salvar historico: " + str(erro) + RESET)


def ler_todos_registros():
    registros = []
    for caminho in (CONFIG["historico"] + ".1", CONFIG["historico"]):
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    leitor = csv.DictReader(arquivo)
                    registros.extend(list(leitor))
            except (OSError, csv.Error):
                pass
    return registros


def consultar_historico():
    limpar()
    titulo()
    preparar_historico()
    registros = ler_todos_registros()

    print(NEGRITO + "ULTIMAS VERIFICACOES" + RESET)
    for linha in registros[-15:]:
        print(" | ".join(str(linha.get(campo, "")) for campo in CAMPOS))

    print("\nTotal de registros:", len(registros))
    print("Arquivo:", CONFIG["historico"])
    pausa()


def exportar_historico():
    limpar()
    titulo()
    print(NEGRITO + "EXPORTAR HISTORICO FILTRADO" + RESET)
    print("1 - Todos os registros")
    print("2 - Filtrar por site")
    print("3 - Filtrar por data")
    print("4 - Filtrar por site e data")

    opcao = input("\nEscolha: ").strip()
    if opcao not in ("1", "2", "3", "4"):
        print(VERMELHO + "Opcao invalida." + RESET)
        pausa()
        return

    site = input("Endereco do site: ").strip().lower() if opcao in ("2", "4") else ""
    data = input("Data (DD/MM/AAAA): ").strip() if opcao in ("3", "4") else ""

    if data:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            print(VERMELHO + "Data invalida." + RESET)
            pausa()
            return

    nome = input("Nome do arquivo (ENTER = exportacao.csv): ").strip()
    if not nome:
        nome = "exportacao.csv"
    if not nome.lower().endswith(".csv"):
        nome += ".csv"

    total = 0
    try:
        with open(nome, "w", newline="", encoding="utf-8") as saida:
            escritor = csv.DictWriter(saida, fieldnames=CAMPOS)
            escritor.writeheader()
            for linha in ler_todos_registros():
                if site and site not in linha.get("Site", "").lower():
                    continue
                if data and not linha.get("Data", "").startswith(data):
                    continue
                escritor.writerow({campo: linha.get(campo, "") for campo in CAMPOS})
                total += 1
        print(VERDE + f"\nExportacao concluida: {total} registros." + RESET)
        print("Arquivo:", nome)
    except (OSError, csv.Error) as erro:
        print(VERMELHO + "Erro na exportacao: " + str(erro) + RESET)
    pausa()


# ---------------- LISTA DE SITES ----------------

def carregar_sites():
    sites = []
    if os.path.exists(ARQUIVO_SITES):
        try:
            with open(ARQUIVO_SITES, "r", encoding="utf-8") as arquivo:
                for linha in arquivo:
                    url = normalizar_url(linha)
                    if url and url not in sites:
                        sites.append(url)
        except OSError:
            pass
    return sites


def salvar_sites(sites):
    try:
        with open(ARQUIVO_SITES, "w", encoding="utf-8") as arquivo:
            for site in sites:
                arquivo.write(site + "\n")
    except OSError as erro:
        print(VERMELHO + "Erro ao salvar sites: " + str(erro) + RESET)


def selecionar_sites():
    existentes = carregar_sites()
    print("\n" + NEGRITO + "LISTA DE SITES" + RESET)

    if existentes:
        for i, site in enumerate(existentes, 1):
            print(f"{i} - {site}")
        print("\nENTER - Usar lista salva")
        print("N - Cadastrar nova lista")
        escolha = input("\nEscolha: ").strip().lower()
        if not escolha:
            return existentes
    else:
        escolha = "n"

    if escolha == "n":
        print("\nDigite os enderecos separados por virgula.")
        entrada = input("Sites: ").strip()
        sites = []
        for item in entrada.split(","):
            url = normalizar_url(item)
            if url and url not in sites:
                sites.append(url)
        if not sites:
            print(VERMELHO + "Nenhum site valido." + RESET)
            pausa()
            return []
        salvar_sites(sites)
        print(VERDE + f"{len(sites)} site(s) salvos em {ARQUIVO_SITES}." + RESET)
        return sites

    print(VERMELHO + "Escolha invalida." + RESET)
    pausa()
    return []


# ---------------- TESTE DE REDE ----------------

def verificar(url):
    inicio = time.perf_counter()
    dados = {
        "status": None, "tempo": 0, "dns": None,
        "conexao": None, "resposta": None,
        "ssl_dias": None, "resultado": "SEM RESPOSTA",
        "ok": False
    }
    sock = None
    arquivo_socket = None

    try:
        partes = urlsplit(url)
        host = partes.hostname
        porta = partes.port or (443 if partes.scheme == "https" else 80)
        caminho = partes.path or "/"
        if partes.query:
            caminho += "?" + partes.query

        # DNS
        inicio_dns = time.perf_counter()
        enderecos = socket.getaddrinfo(host, porta, type=socket.SOCK_STREAM)
        dados["dns"] = (time.perf_counter() - inicio_dns) * 1000
        if not enderecos:
            raise socket.gaierror("Nenhum endereco DNS encontrado")

        familia, tipo, protocolo, _, endereco = enderecos[0]

        # Conexao TCP
        inicio_conexao = time.perf_counter()
        sock = socket.socket(familia, tipo, protocolo)
        sock.settimeout(CONFIG["timeout"])
        sock.connect(endereco)

        # Certificado SSL
        if partes.scheme == "https":
            contexto = ssl.create_default_context()
            sock = contexto.wrap_socket(sock, server_hostname=host)
            certificado = sock.getpeercert()
            validade = certificado.get("notAfter")
            if validade:
                vencimento = datetime.strptime(validade, "%b %d %H:%M:%S %Y %Z")
                dados["ssl_dias"] = (vencimento - datetime.utcnow()).days

        dados["conexao"] = (time.perf_counter() - inicio_conexao) * 1000

        host_header = f"[{host}]" if ":" in host and not host.startswith("[") else host
        if porta not in (80, 443):
            host_header += ":" + str(porta)

        requisicao = (
            f"GET {caminho} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "User-Agent: GAMKERS-MONITOR/6.0\r\n"
            "Connection: close\r\n"
            "Accept: */*\r\n\r\n"
        )

        # Tempo ate receber a primeira linha da resposta
        inicio_resposta = time.perf_counter()
        sock.sendall(requisicao.encode("ascii"))
        arquivo_socket = sock.makefile("rb")
        linha = arquivo_socket.readline(4096)
        dados["resposta"] = (time.perf_counter() - inicio_resposta) * 1000

        if not linha:
            raise OSError("Servidor nao enviou resposta HTTP")

        partes_status = linha.decode("iso-8859-1").strip().split()
        status = int(partes_status[1])
        dados["status"] = status

        # Consumir cabecalhos HTTP
        while True:
            cabecalho = arquivo_socket.readline(8192)
            if not cabecalho or cabecalho in (b"\r\n", b"\n"):
                break

        if 200 <= status < 400:
            dados["resultado"] = "ACESSO OK"
            dados["ok"] = True
        elif status == 403:
            dados["resultado"] = "ONLINE - ACESSO NEGADO"
        elif status == 404:
            dados["resultado"] = "ONLINE - PAGINA NAO ENCONTRADA"
        elif status == 429:
            dados["resultado"] = "HTTP 429 - LIMITE DE REQUISICOES"
        elif status >= 500:
            dados["resultado"] = "ERRO 5XX - SERVIDOR"
        else:
            dados["resultado"] = "ONLINE - ERRO HTTP"

    except socket.timeout:
        dados["resultado"] = "TIMEOUT"
    except ConnectionRefusedError:
        dados["resultado"] = "CONEXAO RECUSADA"
    except ssl.SSLCertVerificationError:
        dados["resultado"] = "ERRO SSL - CERTIFICADO INVALIDO"
    except ssl.SSLError as erro:
        dados["resultado"] = "ERRO SSL: " + str(erro)
    except socket.gaierror:
        dados["resultado"] = "FALHA NO DNS"
    except OSError as erro:
        if isinstance(erro, ConnectionRefusedError):
            dados["resultado"] = "CONEXAO RECUSADA"
        elif isinstance(erro, socket.timeout):
            dados["resultado"] = "TIMEOUT"
        else:
            dados["resultado"] = "ERRO DE REDE: " + str(erro)
    except (ValueError, IndexError, UnicodeError) as erro:
        dados["resultado"] = "RESPOSTA INVALIDA: " + str(erro)
    except Exception as erro:
        dados["resultado"] = "ERRO: " + str(erro)
    finally:
        if arquivo_socket:
            try:
                arquivo_socket.close()
            except OSError:
                pass
        if sock:
            try:
                sock.close()
            except OSError:
                pass

    dados["tempo"] = round((time.perf_counter() - inicio) * 1000, 2)
    for campo in ("dns", "conexao", "resposta"):
        if dados[campo] is not None:
            dados[campo] = round(dados[campo], 2)
    return dados


# ---------------- EXIBICAO E ESTATISTICAS ----------------

def mostrar_resultado(url, dados):
    print(CIANO + "-" * 58 + RESET)
    print(BRANCO + "SITE: " + url + RESET)
    status = dados["status"]
    if status is None:
        print(VERMELHO + "HTTP: SEM RESPOSTA" + RESET)
    else:
        cor = VERDE if dados["ok"] else AMARELO
        print(cor + "HTTP: " + str(status) + RESET)

    print("TEMPO TOTAL:", formatar_tempo(dados["tempo"]))
    print("DNS:", formatar_tempo(dados["dns"]))
    print("CONEXAO:", formatar_tempo(dados["conexao"]))
    print("RESPOSTA:", formatar_tempo(dados["resposta"]))

    if dados["ssl_dias"] is not None:
        dias = dados["ssl_dias"]
        if dias < 0:
            print(VERMELHO + "SSL: CERTIFICADO VENCIDO" + RESET)
        elif dias <= 15:
            print(AMARELO + f"SSL: VENCE EM {dias} DIAS" + RESET)
        else:
            print(VERDE + f"SSL: VALIDO - {dias} DIAS RESTANTES" + RESET)

    cor = VERDE if dados["ok"] else VERMELHO
    print(cor + NEGRITO + "STATUS: " + dados["resultado"] + RESET)
    print(CIANO + "-" * 58 + RESET)


def mostrar_estatisticas(stats):
    total = stats["total"]
    print(NEGRITO + "\nESTATISTICAS" + RESET)
    print("VERIFICACOES:", total)
    print("UPTIME:", porcentagem(stats["ok"], total), "%")
    print("RESPOSTAS RECEBIDAS:", porcentagem(stats["respostas"], total), "%")

    tempos = stats["tempos"]
    if tempos:
        print("TEMPO MINIMO:", round(min(tempos), 2), "ms")
        print("TEMPO MEDIO:", round(sum(tempos) / len(tempos), 2), "ms")
        print("TEMPO MAXIMO:", round(max(tempos), 2), "ms")
    else:
        print("TEMPOS: Nenhuma resposta HTTP bem-sucedida registrada.")


# ---------------- MONITORAMENTO ----------------

def monitorar(sites):
    if not sites:
        return

    intervalo_escolhido = CONFIG["intervalo"]
    intervalo_atual = intervalo_escolhido
    stats = {
        site: {
            "total": 0, "ok": 0, "respostas": 0,
            "tempos": [], "anterior": None
        }
        for site in sites
    }
    total_geral = 0

    limpar()
    titulo()
    print(VERDE + "MONITORAMENTO INICIADO" + RESET)
    print("Sites:", len(sites))
    print("Intervalo escolhido por site:", intervalo_escolhido, "segundos")
    print("Timeout:", CONFIG["timeout"], "segundos")
    print("Consultas teoricas por segundo e por site:",
          round(1 / intervalo_escolhido, 2))
    print("Consultas teoricas por hora e por site:",
          round(3600 / intervalo_escolhido, 2))
    print("CTRL + C para parar.")

    try:
        while True:
            for site in sites:
                dados = verificar(site)
                salvar(site, dados)
                total_geral += 1

                painel = stats[site]
                painel["total"] += 1
                if dados["status"] is not None:
                    painel["respostas"] += 1
                if dados["ok"]:
                    painel["ok"] += 1
                    painel["tempos"].append(dados["tempo"])

                anterior = painel["anterior"]
                caiu = anterior is True and not dados["ok"]
                voltou = anterior is False and dados["ok"]

                if caiu or voltou:
                    beep()
                painel["anterior"] = dados["ok"]

                # Freio: dobra para HTTP 429 ou 5xx, ate 10 segundos.
                status = dados["status"]
                limitou = status == 429 or (
                    status is not None and 500 <= status <= 599
                )
                if limitou:
                    novo = min(intervalo_atual * 2, MAX_INTERVALO)
                    if novo > intervalo_atual:
                        intervalo_atual = novo
                        print(AMARELO + "\n[FREIO AUTOMATICO] HTTP 429/5xx." + RESET)
                        print("Novo intervalo:", round(intervalo_atual, 2), "segundos")
                elif intervalo_atual > intervalo_escolhido:
                    intervalo_atual = max(intervalo_escolhido, intervalo_atual / 2)
                    print(VERDE + "\n[RECUPERACAO] Reduzindo intervalo." + RESET)

                limpar()
                titulo()
                print(VERDE + "MONITOR ATIVO" + RESET)
                print("DATA:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                print("SITE ATUAL:", site)
                mostrar_resultado(site, dados)

                if caiu:
                    print(VERMELHO + NEGRITO + "\n[ALERTA] SITE CAIU!" + RESET)
                elif voltou:
                    print(VERDE + NEGRITO + "\n[ALERTA] SITE VOLTOU!" + RESET)

                mostrar_estatisticas(painel)
                print("\n" + NEGRITO + "PAINEL GERAL" + RESET)
                print("TOTAL DE CONSULTAS:", total_geral)
                print("INTERVALO ATUAL:", round(intervalo_atual, 2), "segundos")
                print("CONSULTAS TEORICAS POR SEGUNDO (POR SITE):",
                      round(1 / intervalo_atual, 2))
                print("CONSULTAS TEORICAS POR HORA (POR SITE):",
                      round(3600 / intervalo_atual, 2))
                print("HISTORICO:", CONFIG["historico"])
                print(CIANO + "\nProxima verificacao em " +
                      str(round(intervalo_atual, 2)) + " segundos..." + RESET)
                time.sleep(intervalo_atual)

    except KeyboardInterrupt:
        print("\n\n" + AMARELO + "MONITORAMENTO ENCERRADO!" + RESET)
        print("TOTAL DE CONSULTAS:", total_geral)
        for site in sites:
            print("\nSITE:", site)
            mostrar_estatisticas(stats[site])
        print("\nHistorico salvo:", CONFIG["historico"])
        pausa()


def verificar_uma_vez(url):
    limpar()
    titulo()
    print("\nVerificando site...")
    dados = verificar(url)
    salvar(url, dados)
    mostrar_resultado(url, dados)
    pausa()


# ---------------- MENU PRINCIPAL ----------------

def main():
    carregar_config()
    preparar_historico()

    while True:
        limpar()
        titulo()
        print(AMARELO + "AVISO: Use somente em sites seus ou autorizados." + RESET)
        print("\n" + VERDE + "1" + RESET + " - Verificar site")
        print(VERDE + "2" + RESET + " - Monitoramento continuo")
        print(VERDE + "3" + RESET + " - Consultar historico / exportar")
        print(VERDE + "4" + RESET + " - Sair")
        print(VERDE + "5" + RESET + " - Configuracoes")
        print("\nIntervalo padrao:", CONFIG["intervalo"], "segundos")

        opcao = input("\nEscolha uma opcao: ").strip()

        if opcao == "1":
            url = normalizar_url(input("\nEndereco do site: "))
            if not url:
                print(VERMELHO + "Endereco invalido." + RESET)
                pausa()
                continue
            verificar_uma_vez(url)

        elif opcao == "2":
            sites = selecionar_sites()
            if sites:
                monitorar(sites)

        elif opcao == "3":
            consultar_historico()
            if input("\nDeseja exportar o historico? (S/N): ").strip().lower() == "s":
                exportar_historico()

        elif opcao == "4":
            print(VERDE + "\nGAMKERS SITE MONITOR ENCERRADO!" + RESET)
            break

        elif opcao == "5":
            configuracoes()

        else:
            print(VERMELHO + "Opcao invalida." + RESET)
            pausa()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + AMARELO + "Programa encerrado." + RESET)
