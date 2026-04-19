FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml ./pyproject.toml

COPY cli_copilot ./cli_copilot

RUN pip install .

CMD ["cop"]