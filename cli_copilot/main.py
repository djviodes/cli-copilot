import argparse
import os
import re
import requests
import sys


def main():
    """
    Generates a bash command from a natural language prompt using a local Ollama LLM.
    Warns the user if the command is potentially destructive before injecting it into the shell buffer.
    """

    # Define the CLI arguments. Prompt is required while the flags are optional
    parser = argparse.ArgumentParser(description="CLI Copilot")
    parser.add_argument("prompt", help="Natural language description of the command you want")
    parser.add_argument("--model", default="llama3.2", help="Specify which Ollama model to use")
    parser.add_argument("--dry-run", action="store_true", help="See the command without injecting it into the buffer")
    parser.add_argument("--explain", action="store_true", help="Explain what the command does")

    args = parser.parse_args()

    # Prompt the LLM for proper formatting of the response
    prompt_prefix = """You are a bash command generator. You must respond in exactly this format with no deviations:

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

    request_payload = {
        "model": args.model,
        "prompt": prompt_prefix + args.prompt,
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
    except Exception as err:
        print(err, file=sys.stderr)
        return

    # Parse the response from the LLM to get your command, explanation, and caution warning
    bash_command = response_payload['response'].split("|")[0].strip().replace('<', '').replace('>', '')
    bash_explanation = response_payload['response'].split("|")[1]
    bash_with_caution = response_payload['response'].split("|")[2]

    # Built in caution warning checks using regex
    pattern = r"sudo|rm\b|rmdir|chmod|chown|mkfs|curl|wget|scp|\bkill\b|killall|install|fdisk|\bsu\b|\bPATH\b"
    caution_command = re.search(pattern, bash_command, re.IGNORECASE)
    
    # Warn the user if regex or LLM flagged the command as dangerous
    if caution_command or bash_with_caution.strip().lower() == 'y':
        print(
            "The following command should be handled with caution. Proceed? [y/n]: ",
            file=sys.stderr,
            end=''
        )
        decision = input()

        if decision == 'y':
            if args.explain:
                print(bash_explanation, file=sys.stderr)

            if args.dry_run:
                print(bash_command, file=sys.stderr)
            else:
                print(bash_command)
            return
        else:
            print("Cancelled command creation", file=sys.stderr)
            return
    else:
        if args.explain:
                print(bash_explanation, file=sys.stderr)

        if args.dry_run:
            print(bash_command, file=sys.stderr)
        else:
            print(bash_command)
        return
