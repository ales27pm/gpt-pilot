# GPT Pilot

GPT Pilot is an open‑source, multi‑agent system that builds full‑stack
applications by writing, running and reviewing code. It powers the
[Pythagora VS Code extension](https://bit.ly/3IeZxp6) but can also be used
as a standalone command‑line tool.

## Features

- Multi‑agent architecture: architect, engineer and QA agents collaborate
  to design, implement and debug features step by step.
- Integrated execution environment so code is run and validated after each
  change.
- Supports multiple LLM providers (OpenAI, Anthropic, Groq, Azure and
  compatible APIs).
- State stored in PostgreSQL with pgvector extension for semantic context retrieval.
- Optional web frontend started alongside the backend.

## How it works

1. Describe the application you want to build.
2. The architect agent plans the required steps and creates the initial
   project structure.
3. The engineer agent writes or edits code.
4. Code is executed and tests are run to verify behaviour.
5. The process repeats until the feature is complete.

Generated applications live in `workspace/<app-name>` and progress is
saved so you can resume work later.

## Requirements

- Python 3.9+
- (Optional) Node.js 18+ and npm for the frontend
- (Optional) PostgreSQL

## Installation

```bash
git clone https://github.com/Pythagora-io/gpt-pilot.git
cd gpt-pilot
./setup.sh
```

The interactive `setup.sh` script checks your Python version, optionally
creates a virtual environment, installs Python dependencies, installs
frontend packages when a `frontend` directory exists and creates
`config.json` with your LLM credentials.

## Configuration

The generated `config.json` contains credentials and defaults for GPT
providers. Each provider entry has `api_key` and `base_url` fields. The
`agent.default.provider` value selects which provider to use at runtime.
Edit `config.json` to adjust timeouts or add new providers.

## Running

```bash
./run.sh
```

`run.sh` starts the backend and, if a frontend project is present,
launches the development server. Generated apps are placed under
`workspace/<app-name>`.

## CLI options

- `python main.py --list` – list existing projects
- `python main.py --project <app_id>` – resume a project
- `python main.py --project <app_id> --step <step>` – resume from a
  specific step (subsequent progress is discarded)
- `python main.py --delete <app_id>` – delete a project
- `python main.py --help` – show all options

## Telemetry

GPT Pilot collects anonymous usage metrics by default to improve the
project. See [docs/TELEMETRY.md](docs/TELEMETRY.md) for what is collected
and how to opt out.

## Contributing

Contributions are welcome! After installing dependencies run the
following checks before submitting a pull request:

```bash
python3 -m pre_commit run --files README.md setup.sh
pytest
```

Join our [Discord community](https://discord.gg/HaqXugmxr9) to discuss
ideas and development.

## License

Released under the [FSL-1.1-MIT license](LICENSE).
