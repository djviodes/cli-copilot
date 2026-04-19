import argparse
import os
import re
import requests
import sys

CAUTION_PATTERN = r"sudo|\brm\b|rmdir|chmod|chown|mkfs|\bcurl\b|wget|scp|\bkill\b|killall|\binstall\b|fdisk|\bsu\b|\bPATH\b"
DEFAULT_MODEL = "llama3.2"
PROMPT_PREFIX = """You are a bash command generator. You must respond in exactly this format with no deviations:

    <command> | <explanation> | <caution>

    Rules:
    - <command>: The bash command only, no extra text or formatting
    - <explanation>: A brief one sentence explanation of what the command does
    - <caution>: The single letter 'y' if the command deletes, overwrites, or modifies files, directories, or system settings. Otherwise the single letter 'n'

    Example:
    User: list all files including hidden ones
    Response: ls -a | Lists all files in the current directory including hidden files that start with a dot | n

    User: force delete the test folder
    Response: rm -rf test | Forcefully and recursively deletes the test folder and all its contents | y

    Now respond to this prompt: """


def generate_command(model: str, prompt: str) -> dict | None:
    """
    Calls the Ollama API to generate the CLI command using the provided prompt
    """
    # Prompt the LLM for proper formatting of the response
    request_payload = {
        "model": model,
        "prompt": PROMPT_PREFIX + prompt,
        "stream": False
    }

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    url = f"{host}/api/generate"

    # Request the LLM, catch connection errors if Ollama isn't running
    try:
        response = requests.request(
            'POST',
            json=request_payload,
            url=url
        )

        response_payload = response.json()

        return response_payload
    except requests.exceptions.ConnectionError:
        print("Could not connect to Ollama. Is it running?", file=sys.stderr)
        return
    except requests.exceptions.RequestException as err:
        print(err, file=sys.stderr)
        return


def check_caution(bash_command: str) -> re.Match | None:
    """
    Checks if the bash command contains any parts that may be deemed dangerous or destructive
    """
    # Built in caution warning checks using regex
    caution_command = re.search(CAUTION_PATTERN, bash_command, re.IGNORECASE)

    return caution_command


def handle_output(
    bash_command: str,
    bash_explanation: str,
    bash_with_caution: str,
    caution_command: re.Match | None,
    dry_run: bool,
    explain: bool
) -> None:
    """
    Returns the command to the user
    Warns the user if the command was deemed destructive or dangerous
    """
    # Warn the user if regex or LLM flagged the command as dangerous
    if caution_command or bash_with_caution.strip().lower() == 'y':
        print(
            "The following command should be handled with caution. Proceed? [y/n]: ",
            file=sys.stderr,
            end=''
        )
        decision = input()

        if decision == 'y':
            if explain:
                print(bash_explanation, file=sys.stderr)

            if dry_run:
                print(bash_command, file=sys.stderr)
            else:
                print(bash_command)
            return
        else:
            print("Cancelled command creation", file=sys.stderr)
            return
    else:
        if explain:
                print(bash_explanation, file=sys.stderr)

        if dry_run:
            print(bash_command, file=sys.stderr)
        else:
            print(bash_command)
        return


def main():
    """
    Generates a bash command from a natural language prompt using a local Ollama LLM.
    Warns the user if the command is potentially destructive before injecting it into the shell buffer.
    """

    # Define the CLI arguments. Prompt is required while the flags are optional
    parser = argparse.ArgumentParser(description="CLI Copilot")
    parser.add_argument("prompt", help="Natural language description of the command you want")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Specify which Ollama model to use")
    parser.add_argument("--dry-run", action="store_true", help="See the command without injecting it into the buffer")
    parser.add_argument("--explain", action="store_true", help="Explain what the command does")

    args = parser.parse_args()

    response_payload = generate_command(args.model, args.prompt)

    if response_payload is None:
        return

    # Parse the response from the LLM to get your command, explanation, and caution warning
    response_parts = response_payload['response'].split("|")
    if len(response_parts) != 3:
        print("Unexpected response format", file=sys.stderr)
        return

    bash_command = response_parts[0].strip().replace('<', '').replace('>', '')
    bash_explanation = response_parts[1]
    bash_with_caution = response_parts[2]

    caution_command = check_caution(bash_command)

    handle_output(
        bash_command,
        bash_explanation,
        bash_with_caution,
        caution_command,
        args.dry_run,
        args.explain
    )
