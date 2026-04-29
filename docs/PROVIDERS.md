# Provider setup

Goose talks to a model provider. The starter kit asks you to pick one at
install time and then hands the API-key entry off to `goose configure`,
which stores credentials in your OS keyring (macOS Keychain, Windows
Credential Manager, or libsecret on Linux). The starter-kit installer
itself never writes a secret to disk.

## Anthropic (Claude)

Best default for "AI scientist" work — strong on long context, retrieval,
and structured output.

1. Get an API key from <https://console.anthropic.com/>.
2. Pick `anthropic` at the installer prompt; paste the key when
   `goose configure` asks.
3. Default model written to `config.yaml`: `claude-sonnet-4-6`. Change
   `GOOSE_MODEL` to upgrade or downgrade — see Anthropic's [model
   list](https://docs.claude.com/en/docs/about-claude/models) for current
   options.

## OpenAI

1. Get an API key from <https://platform.openai.com/api-keys>.
2. Pick `openai`; paste the key.
3. Default model: `gpt-4o`.

## Ollama (local)

Free, runs locally, no API key. Trades capability for privacy.

1. Install Ollama: <https://ollama.com/download>.
2. Pull at least one model — for this kit, a 7B-class model is the
   minimum useful size:
   ```bash
   ollama pull llama3.1
   ```
3. Pick `ollama` at the installer prompt. The script probes
   `localhost:11434` and warns if Ollama isn't running.

Note that the bundled skills assume a model with reasonable tool-use
ability. Smaller / older Ollama models will struggle with multi-step
recipes like `weekly-lit-scan`.

## Switching provider after install

Either re-run the installer (it'll re-prompt unless you pass `--update`)
or edit `~/.config/goose/config.yaml` directly:

```yaml
GOOSE_PROVIDER: openai
GOOSE_MODEL: gpt-4o
```

Re-run `goose configure` to enter a new API key for the new provider.
