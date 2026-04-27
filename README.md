# CLI-Copilot

[![Run Tests](https://github.com/djviodes/cli-copilot/actions/workflows/test.yml/badge.svg)](https://github.com/djviodes/cli-copilot/actions/workflows/test.yml)

A command line tool that generates bash commands by interpreting natural language requests, powered by a local LLM via Ollama.

---

## Features

- Converts natural language descriptions into shell commands using a local LLM
- The `--explain` flag provides a breakdown of what each part of the command does
- The `--model` flag allows you to choose which Ollama model generates your commands
- The `--dry-run` flag prints the command to the terminal without injecting it into the prompt buffer
- Warns the user before executing potentially destructive commands

---

## Prerequisites

- Docker
- zsh

---

## Installation

1. Clone the repository
```bash
git clone https://github.com/djviodes/cli-copilot.git
cd cli-copilot
```

2. Start the services with Docker Compose
```bash
docker compose up -d
```

3. Pull the default LLM model
```bash
docker exec -it ollama ollama pull llama3.2
```

4. Add the following shell function to your `~/.zshrc`
```zsh
cop() {
    local cmd=$(command cop "$@")
    print -z "$cmd"
}
```

5. Reload your shell
```bash
source ~/.zshrc
```

---

## Usage

Basic usage:
```bash
cop "your natural language request"
```

With flags:
```bash
cop "list all python files" --explain
cop "list all python files" --dry-run
cop "list all python files" --model mistral
```

---

## How It Works

CLI-Copilot sends your natural language prompt to a local Ollama LLM running in Docker. The LLM returns a bash command, a one sentence explanation, and a caution flag in a structured format. Before injecting the command into your shell buffer, CLI-Copilot checks for potentially destructive commands using both regex pattern matching and the LLM's own assessment. If flagged, the user is prompted to confirm before proceeding.
