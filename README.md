### Holosophos

Autonomous research assistant composed of specialized agents for literature discovery, experiment execution on remote GPUs, technical writing, idea generation, and paper review. Also includes ERC3 competition agents for benchmarks.

Built on top of:
- [CodeArkt agentic framework](https://github.com/IlyaGusev/codearkt)
- [Academia MCP server](https://github.com/IlyaGusev/academia_mcp)
- [MLE kit MCP server](https://github.com/IlyaGusev/mle_kit_mcp)
- [ERC3 SDK](https://erc.timetoact-group.at/) - for AI Agents in Action competition


### Features
- **Manager agent**: Orchestrates task flow across specialized agents.
- **Librarian**: Searches papers (ArXiv, ACL Anthology, Semantic Scholar), reads webpages, and analyzes documents.
- **MLE Solver**: Writes and runs code on remote GPUs via MLE Kit MCP tools.
- **Writer**: Composes LaTeX reports/papers and compiles them to PDF.
- **Proposer**: Generates and scores research ideas given context and a baseline paper.
- **Reviewer**: Reviews papers with venue-grade criteria.
- **ERC3 Agents**: Competition agents using Schema-Guided Reasoning for store and corporate benchmarks.

### Architecture at a glance
- Server entrypoint: `holosophos_erc.server` (starts a CodeArkt server with the composed agent team)
- Agent composition: `holosophos_erc.holosophos_main_agent.compose_holosophos_main_agent`
- Agent prompts: `holosophos_erc/prompts/*.yaml`
- Settings: `holosophos_erc/settings.py` (env-driven via `pydantic-settings`)
- External MCPs:
  - `academia_mcp` (papers/search)
  - `mle_kit_mcp` (remote GPU execution, file ops)
- Optional tracing/observability: Phoenix (OTLP)

### Requirements
- Python 3.12+
- Docker
- `uv` (recommended for fast Python environment management)

### Installation
```bash
uv venv .venv
source .venv/bin/activate
make install

# Note: If using ERC3 agents, you'll need the custom package index:
pip install --extra-index-url https://erc.timetoact-group.at/ -e .
```

### Environment configuration
Create a `.env` file at the project root. Typical entries:
```bash
# LLM provider keys (use what you need)
OPENROUTER_API_KEY=...

# Tooling keys
TAVILY_API_KEY=...
VAST_AI_KEY=...

# Optional observability
PHOENIX_URL=http://localhost:6006
PHOENIX_PROJECT_NAME=holosophos_erc

# MCP endpoints when running locally
ACADEMIA_MCP_URL=http://0.0.0.0:5056/mcp
MLE_KIT_MCP_URL=http://0.0.0.0:5057/mcp

# App options
MODEL_NAME=deepseek/deepseek-chat-v3.1
PORT=5055
```

Holosophos reads configuration from `holosophos_erc/settings.py`. You can override any setting via environment variables (case-insensitive), for example `MODEL_NAME`, `MAX_COMPLETION_TOKENS`, `ENABLE_PHOENIX=true`, or custom `PHOENIX_ENDPOINT`.

### Quickstart: Local (multi-process)
Open separate terminals and run:

1) Phoenix (optional, for traces)
```bash
docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix
```

2) Academia MCP (papers)
```bash
uv run python -m academia_mcp --port 5056
```

3) MLE Kit MCP (GPU exec; with local workspace bind)
```bash
uv run python -m mle_kit_mcp --port 5057 --workspace workdir
```

4) Holosophos server
```bash
uv run python -m holosophos_erc.server --port 5055 --enable-phoenix
```

5) Client UI (choose one)
```bash
# Gradio UI
uv run python -m codearkt.gradio

# Terminal client
uv run python -m codearkt.terminal
```

The server listens on `http://localhost:5055`. The manager agent will call into MCP tools from Academia and MLE Kit as needed.

### Quickstart: Docker Compose
Holosophos ships with a `docker-compose.yml` that brings up:
- `app` (Holosophos server)
- `executor` (CodeArkt executor)
- `phoenix` (optional tracing UI and OTLP collector)
- `academia` (Academia MCP)
- `mle_kit` (MLE Kit MCP, with `./workdir` mounted and Docker socket pass-through)

Steps:
```bash
# 1) Ensure you have a .env at project root (see above)
# 2) Start the stack
docker compose up --build
```

Default ports:
- App: `http://localhost:5055`
- Phoenix UI: `http://localhost:6006`
- Academia MCP: `http://localhost:5056`
- MLE Kit MCP: `http://localhost:5057`

You can change ports via environment variables in `docker-compose.yml` (`APP_PORT`, `PHOENIX_UI_PORT`, `PHOENIX_OTLP_PORT`, `ACADEMIA_PORT`, `MLE_KIT_PORT`).

#### Compose commands and tips
```bash
# Start everything in the background
docker compose up -d --build

# Tail logs for a service
docker compose logs -f app
docker compose logs -f phoenix
docker compose logs -f academia
docker compose logs -f mle_kit
docker compose logs -f executor

# Restart or rebuild a single service
docker compose restart app
docker compose build app --no-cache && docker compose up -d app

# Stop and remove (including named volumes, if any)
docker compose down -v
```

#### Override ports and options at runtime
```bash
# Example: change app and Phoenix UI ports for this run only
APP_PORT=8055 PHOENIX_UI_PORT=6606 docker compose up -d --build
```

#### Workspace and persistence
- `./workdir` is bind-mounted into both `academia` and `mle_kit` containers at `/workdir`.
- Use `workdir/` for inputs and outputs you want to inspect or edit from the host.
- The `mle_kit` service has `/var/run/docker.sock` mounted to orchestrate jobs; see the security note below.

#### Interacting with the stack
Run a client in a separate terminal to talk to the app at `http://localhost:${APP_PORT:-5055}`:
```bash
# Gradio UI
uv run python -m codearkt.gradio

# or terminal client
uv run python -m codearkt.terminal
```

#### Customizing the model and tracing
- Set `MODEL_NAME` in `.env` (or export it) to change the model (default comes from `holosophos_erc/settings.py`).
- Enable tracing by setting `ENABLE_PHOENIX=true` and ensuring Phoenix is up. The app will send OTLP traces to `${PHOENIX_URL}/v1/traces` unless `PHOENIX_ENDPOINT` is provided.

#### Security note
Mounting `/var/run/docker.sock` into `mle_kit` grants it control over the host Docker daemon. Only run this stack on a trusted machine and network.

### Using the agents
The server composes a manager agent with five specialists:
- **librarian**: queries literature and the web (no file system access)
- **mle_solver**: executes code on remote GPUs (remote tools)
- **writer**: creates LaTeX PDFs (templates, compile)
- **proposer**: ideates and scores research proposals
- **reviewer**: reviews papers using venue-style rubrics

Prompts live under `holosophos_erc/prompts/` and can be customized per agent (`*.yaml`). Tool sets and iteration limits are configured in `holosophos_erc/settings.py` and can be overridden via environment variables.

### Development
- Install dev tools: `make install`
- Format: `make black`
- Lint & type-check: `make validate`
- Tests: `make test`

### ERC3 Competition Agents

The project includes agents for the [ERC3: AI Agents in Action](https://www.timetoact-group.at/events/enterprise-rag-challenge-part-3) competition. These agents use Schema-Guided Reasoning to solve benchmark tasks.

#### Getting Your ERC3 API Key

1. Visit https://erc.timetoact-group.at/
2. Enter the email address you used during registration
3. Your API key will be displayed

Note: If you haven't registered yet, visit the competition page and allow 24 hours for your registration to be processed.

#### Running ERC3 Agents

The ERC3 agents are located in `holosophos_erc/agents/` and can be run using the `main.py` script at the project root:

```bash
# Set up your environment variables
export OPENAI_API_KEY=sk-...
export ERC3_API_KEY=key-...

# Run with default settings (store benchmark, gpt-4o)
python main.py

# Or specify custom settings
python main.py --benchmark corporate --model gpt-4o-mini --workspace my-workspace
```

#### Available ERC3 Agents

- **store_agent**: Agent for the store benchmark (product listings, basket management, coupons, checkout)
- **corporate_agent**: Agent for the corporate benchmark (employee management, projects, task assignments, budget reports)

Both agents use Schema-Guided Reasoning with recursive prompts for adaptive thinking capabilities.

#### ERC3 Resources

- Competition page: https://www.timetoact-group.at/events/enterprise-rag-challenge-part-3
- ERC3 Platform: https://erc.timetoact-group.at/
- Discord support: Available via registration email

### Troubleshooting
- If the manager cannot reach MCP servers, verify `ACADEMIA_MCP_URL` and `MLE_KIT_MCP_URL` match the ports you started.
- For tracing, ensure Phoenix is running and `ENABLE_PHOENIX=true` (or pass `--enable-phoenix`).
- Ensure LLM credentials are present in `.env` for your chosen provider(s).
