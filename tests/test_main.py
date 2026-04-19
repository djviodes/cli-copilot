import os
import pytest
import requests
from unittest.mock import patch
from cli_copilot.main import check_caution, generate_command


def test_check_caution_catches_dangerous_command():
    result = check_caution("sudo rm -rf /tmp/test")
    assert result

def test_check_caution_allows_safe_command():
    result = check_caution("ls -a")
    assert result is None

def test_check_caution_allows_empty_string():
    result = check_caution("")
    assert result is None

def test_check_caution_is_case_insensitive():
    result = check_caution("CURL https://example.com")
    assert result

def test_check_caution_catches_rm_with_flags():
    result = check_caution("rm -rf")
    assert result

def test_check_caution_allows_au_inside_word():
    result = check_caution("asus")
    assert result is None

def test_check_caution_ignores_rm_in_word():
    result = check_caution("harm none")
    assert result is None

def test_check_caution_ignores_curl_in_word():
    result = check_caution("curly")
    assert result is None

@patch('cli_copilot.main.requests.request')
def test_generate_command_creates_list_all_files(mock_request):
    mock_request.return_value.json.return_value = {
        'response': 'ls -a | Lists all files | n'
    }

    result = generate_command('llama3.2', 'list all files')
    assert result is not None

@patch('cli_copilot.main.requests.request')
def test_generate_command_hits_connection_error(mock_request):
    mock_request.side_effect = requests.exceptions.ConnectionError

    result = generate_command('llama3.2', 'list all files')
    assert result is None

@patch('cli_copilot.main.requests.request')
@patch.dict(os.environ, {'OLLAMA_HOST': 'http://ollama:11434'})
def test_generate_command_uses_ollama_host(mock_request):
    mock_request.return_value.json.return_value = {
        'response': 'ls -a | Lists all files | n'
    }

    generate_command('llama3.2', 'list all files')
    called_url = mock_request.call_args.kwargs['url']
    assert called_url == 'http://ollama:11434/api/generate'
