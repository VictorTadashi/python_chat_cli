# 💬 python_chat_cli

Chat com IA no terminal, construído em Python sobre a API do Google Gemini. As respostas chegam em streaming, as conversas ficam salvas em SQLite e o consumo de tokens é exibido a cada resposta.

Projeto de estudo em **Engenharia de IA**, construído em fases, cada uma cobrindo um conceito usado em aplicações reais com LLMs: streaming, gestão de histórico, resiliência a falhas da API, persistência e controle de custo.

<!-- Adicione aqui um print ou GIF do chat rodando no terminal -->
<!-- ![Demonstração](docs/demo.gif) -->

---

## ✨ Funcionalidades

- **Streaming de respostas:** o texto aparece conforme a IA gera, com Markdown renderizado no terminal (títulos, listas, negrito).
- **Conversa com contexto:** o histórico é enviado a cada pergunta, então a IA lembra do que foi dito antes.
- **Persistência em SQLite:** conversas e mensagens ficam salvas e podem ser retomadas depois.
- **Métricas por resposta:** tokens de entrada, saída e raciocínio, total e motivo da parada.
- **Resiliência:**
  - retry automático com backoff exponencial em falhas temporárias;
  - fallback para um modelo reserva quando o principal fica indisponível (erros 5xx);
  - tratamento de respostas vazias e de interrupção no meio do streaming.
- **Comandos de terminal** para listar, abrir e limpar conversas.

---

## 🛠️ Stack

| Tecnologia | Uso |
|---|---|
| Python 3.14 | Linguagem |
| [google-genai](https://pypi.org/project/google-genai/) | SDK oficial da API do Gemini |
| [rich](https://pypi.org/project/rich/) | Spinner, Markdown ao vivo, tabelas e cores no terminal |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Carregamento da chave da API a partir do `.env` |
| SQLite (`sqlite3`) | Banco local de conversas e mensagens |

---

## 📁 Estrutura

```
python_chat_cli/
├── src/
│   └── chatcli/
│       ├── __main__.py   # Loop do chat, comandos, streaming e exibição
│       ├── config.py     # Chave da API, modelos, limites e caminho do banco
│       └── db.py         # Conexão, criação de tabelas e consultas SQLite
├── ver_banco.py          # Script de depuração que imprime o conteúdo do banco
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🚀 Como rodar

### 1. Clonar o repositório

```bash
git clone https://github.com/VictorTadashi/python_chat_cli.git
cd python_chat_cli
```

### 2. Criar o ambiente virtual e instalar as dependências

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar a chave da API

Gere uma chave gratuita no [Google AI Studio](https://aistudio.google.com/) e crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=sua-chave-aqui
```

Em `src/chatcli/config.py`, defina os modelos principal e reserva, usando os nomes listados no AI Studio:

```python
MODEL = "nome-do-modelo-principal"
MODEL_FALLBACK = "nome-do-modelo-reserva"
```

### 4. Executar

```bash
cd src
python -m chatcli
```

O banco `chat.db` é criado automaticamente na raiz do projeto na primeira execução.

---

## ⌨️ Comandos

| Comando | Ação |
|---|---|
| `/conversas` | Lista as conversas salvas, com ID, título, número de mensagens e data |
| `/abrir <id>` | Carrega uma conversa salva e continua de onde parou |
| `/limpar` | Começa uma conversa nova (as anteriores continuam salvas) |
| `/historico` | Mostra a conversa atual e quantas mensagens ela tem |
| `/sair` | Encerra o chat (`Ctrl+C` também funciona) |

---

## 🗄️ Modelo de dados

```
conversas                     mensagens
├── id  ◄──────────────┐      ├── id
├── titulo             └───── ├── conversa_id
└── criada_em                 ├── role            (user | model)
                              ├── texto
                              ├── modelo
                              ├── tokens_entrada
                              ├── tokens_saida
                              └── criada_em
```

- O título da conversa é gerado a partir da primeira pergunta.
- Uma conversa só é criada no banco quando recebe a primeira resposta, então não ficam conversas vazias.
- A pergunta só é salva junto com a resposta. Se a API falhar, nada é gravado.
- Todas as consultas usam parâmetros (`?`), o que evita SQL injection.

---

## 🧠 Conceitos praticados

- **APIs de LLM são stateless:** a "memória" do chat é o histórico reenviado a cada chamada, e por isso o custo de entrada cresce a cada rodada.
- **Streaming:** consumo de respostas em chunks, com montagem do texto completo e leitura dos metadados de uso no último chunk.
- **Tratamento de erros por classe:** erros 5xx (temporários) recebem retry e fallback; erros 4xx (configuração) interrompem a execução, porque repetir não resolve.
- **Gerenciamento de recursos:** `try/finally` garante o fechamento do banco e do streaming em qualquer cenário.
- **Separação de responsabilidades:** configuração, acesso a dados e interface ficam em módulos distintos.

---

## 🗺️ Roadmap

- [x] Chamada à API com métricas de tokens
- [x] Retry com backoff e modelo reserva
- [x] Loop de conversa com histórico
- [x] Streaming com Markdown renderizado
- [x] Persistência em SQLite
- [x] Comandos para listar, abrir e limpar conversas
- [ ] Cálculo de custo em dinheiro por resposta e por conversa
- [ ] Gestão de contexto: truncamento e sumarização do histórico
- [ ] System instruction para idioma e tom das respostas
- [ ] Comando `chatcli` instalável via `pyproject.toml`

---

## 👤 Autor

**Victor Tadashi**: Software Developer | AI Engineering

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/victor-tadashi-saito-barra-578b7a308)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/VictorTadashi)
[![Portfólio](https://img.shields.io/badge/Portfólio-000000?style=flat&logo=vercel&logoColor=white)](https://victortadashi.com.br)
