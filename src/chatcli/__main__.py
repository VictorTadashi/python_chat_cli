from google import genai
from google.genai import errors, types
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table

from chatcli import config, db

console = Console()


def gerar_resposta(client, historico):
    """Faz streaming da resposta. Retorna (texto, ultimo_chunk, modelo) ou (None, None, None)."""
    for modelo in (config.MODEL, config.MODEL_FALLBACK):
        status = console.status(
            f"[bold cyan]Aguardando resposta da IA ({modelo})...", spinner="dots"
        )
        status.start()
        live = None
        texto = ""
        ultimo_chunk = None

        try:
            stream = client.models.generate_content_stream(
                model=modelo,
                contents=historico,
                config=types.GenerateContentConfig(
                    max_output_tokens=config.MAX_OUTPUT_TOKENS,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
            for chunk in stream:
                if chunk.text:
                    if live is None:  # primeiro pedaço: troca o spinner pela área da resposta
                        status.stop()
                        console.print("\n[bold magenta]IA:[/]")
                        live = Live(
                            Markdown(""),
                            console=console,
                            refresh_per_second=10,
                            vertical_overflow="visible",
                        )
                        live.start()
                    texto += chunk.text
                    live.update(Markdown(texto))
                ultimo_chunk = chunk

            return texto, ultimo_chunk, modelo

        except errors.ServerError as e:
            if texto:  # caiu no meio da resposta: não faz sentido trocar de modelo
                console.print("\n[yellow]\\[aviso] A resposta foi interrompida no meio.[/]")
                return None, None, None
            console.print(
                f"[yellow]\\[aviso] {modelo} indisponível ({e.code}). Tentando o próximo...[/]"
            )
        finally:
            status.stop()
            if live:
                live.stop()
                console.print()  # linha em branco antes das métricas

    return None, None, None


def mostrar_uso(chunk, modelo):
    usage = chunk.usage_metadata
    finish = chunk.candidates[0].finish_reason
    console.print(
        f"[dim]\\[{modelo}] entrada: {usage.prompt_token_count} | "
        f"saída: {usage.candidates_token_count} | "
        f"raciocínio: {usage.thoughts_token_count or 0} | "
        f"total: {usage.total_token_count} | "
        f"parada: {finish}[/dim]\n"
    )


def mostrar_conversas(conn):
    conversas = db.listar_conversas(conn)
    if not conversas:
        console.print("[dim]Nenhuma conversa salva ainda.[/]\n")
        return

    tabela = Table(title="Conversas salvas")
    tabela.add_column("ID", justify="right", style="cyan")
    tabela.add_column("Título")
    tabela.add_column("Msgs", justify="right")
    tabela.add_column("Criada em", style="dim")

    for c in conversas:
        tabela.add_row(
            str(c["id"]),
            escape(c["titulo"]),
            str(c["total_mensagens"]),
            c["criada_em"].replace("T", " "),
        )

    console.print(tabela)
    console.print()


def mostrar_ajuda():
    console.print(
        "[bold green]Comandos:[/] "
        "\n[bold]/conversas[/] lista as conversas salvas | "
        "\n[bold]/abrir <id>[/] retoma uma conversa | "
        "\n[bold]/limpar[/] começa uma conversa nova | "
        "\n[bold]/historico[/] mostra a conversa atual | "
        "\n[bold]/sair[/] encerra\n"
    )


def main() -> None:
    client = genai.Client(
        api_key=config.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2, max_delay=30)
        ),
    )

    historico = []
    conn = db.conectar()
    conversa_id = None

    console.print("[bold green]Chat iniciado.[/]")
    mostrar_ajuda()

    try:
        while True:
            try:
                pergunta = input("Você: ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold]Até mais![/]")
                break

            if not pergunta:
                continue

            comando = pergunta.lower()

            # ---------- Comandos ----------
            if comando == "/sair":
                console.print("[bold]Até mais![/]")
                break

            if comando == "/conversas":
                mostrar_conversas(conn)
                continue

            if comando.startswith("/abrir"):
                partes = pergunta.split()
                if len(partes) != 2 or not partes[1].isdigit():
                    console.print("[yellow]Uso: /abrir <id>   (ex: /abrir 1)[/]\n")
                    continue

                id_escolhido = int(partes[1])
                historico_salvo = db.carregar_historico(conn, id_escolhido)
                if not historico_salvo:
                    console.print(f"[yellow]Conversa {id_escolhido} não encontrada.[/]\n")
                    continue

                historico = historico_salvo
                conversa_id = id_escolhido
                console.print(
                    f"[green]Conversa {id_escolhido} carregada "
                    f"({len(historico)} mensagens). Pode continuar de onde parou.[/]\n"
                )
                continue

            if comando == "/limpar":
                historico.clear()
                conversa_id = None
                console.print("[green]Histórico limpo. A próxima pergunta inicia uma conversa nova.[/]\n")
                continue

            if comando == "/historico":
                situacao = f"conversa {conversa_id}" if conversa_id else "conversa nova (ainda não salva)"
                console.print(f"[cyan]{situacao} | {len(historico)} mensagens no histórico[/]\n")
                continue

            if comando.startswith("/"):
                console.print(f"[yellow]Comando desconhecido: {escape(pergunta)}[/]")
                mostrar_ajuda()
                continue

            # ---------- Pergunta para a IA ----------
            historico.append({"role": "user", "parts": [{"text": pergunta}]})

            texto, ultimo_chunk, modelo = gerar_resposta(client, historico)

            if texto is None:
                historico.pop()  # remove a pergunta que ficou sem resposta
                console.print("[red]Não foi possível obter a resposta. Tente de novo.[/]\n")
                continue

            if not texto:
                historico.pop()  # evita guardar uma resposta vazia
                console.print("[yellow]A IA não retornou texto. Reformule a pergunta.[/]\n")
                if ultimo_chunk:
                    mostrar_uso(ultimo_chunk, modelo)
                continue

            historico.append({"role": "model", "parts": [{"text": texto}]})
            mostrar_uso(ultimo_chunk, modelo)

            # ---------- Persistência ----------
            if conversa_id is None:
                conversa_id = db.nova_conversa(conn, pergunta[:60])

            usage = ultimo_chunk.usage_metadata
            db.salvar_mensagem(conn, conversa_id, "user", pergunta)
            db.salvar_mensagem(
                conn, conversa_id, "model", texto,
                modelo=modelo,
                tokens_entrada=usage.prompt_token_count,
                tokens_saida=usage.candidates_token_count,
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()