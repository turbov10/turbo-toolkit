# web-search

A small Python CLI that runs online web searches against pluggable engines and
emits JSON results.

## Setup

```bash
cd web-search
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Configure API keys

Copy `.env.example` to `.env` and fill in the keys for the engines you want to
use:

| Variable        | Required by engine | Where to get it                                                                 |
| --------------- | ------------------ | ------------------------------------------------------------------------------- |
| `GOOGLE_API_KEY`| `google`           | Google Cloud Console → APIs & Services → Credentials → API key                  |
| `GOOGLE_CX`     | `google`           | [Programmable Search Engine](https://programmablesearchengine.google.com/) cx id |
| `BING_API_KEY`  | `bing`             | Azure Portal → Bing Search v7 resource → Keys                                  |
| `GEMINI_API_KEY`| `gemini`           | [Google AI Studio](https://aistudio.google.com/apikey)                          |
| `GEMINI_MODEL`  | `gemini` (optional)| Default `gemini-2.5-flash`. Must support the `google_search` tool.              |

The `baidu` engine needs **no** keys (it scrapes `baidu.com` directly and may
hit an anti-bot wall under heavy use). You can also export the variables in
your shell instead of using a `.env` file.

## Usage

```bash
# default engine (google)
.venv/bin/python cli.py "python argparse tutorial"

# bing (zh-CN market, accessible from China) - needs Azure key
.venv/bin/python cli.py bing "python 教程"

# baidu: scrapes baidu.com directly, no key needed
.venv/bin/python cli.py baidu "python 教程"

# gemini: model picks results, grounds via Google Search
.venv/bin/python cli.py gemini "latest python 3.14 release notes"

# cap result count
.venv/bin/python cli.py google "asyncio" -n 5

# point at a custom env file
.venv/bin/python cli.py bing "foo" --env-file /path/to/.env
```

`type` is an enum of `google` | `bing` | `baidu` | `gemini`, defaulting to
`google`.

### Engine notes

- **baidu** — zero-config scraper of `baidu.com`. No key needed, accessible
  from China. Will hit a security verification wall under sustained use; for
  production pick the Azure `bing` engine.
- **gemini** — uses Google's `google_search` grounding tool. The model picks
  the most relevant sources; the response text is used as a fallback snippet
  when a particular source has no grounded text. Requires a Gemini API key and
  is subject to Gemini API availability (may be blocked in mainland China).

## Output

```json
{
  "duration": 423,
  "results": [
    {
      "title": "...",
      "link": "https://...",
      "snippet": "..."
    }
  ]
}
```

`duration` is the wall-clock time of the upstream call in milliseconds. On
failure the CLI prints `{"error": "...", "type": "...", "query": "..."}` to
stdout and exits with code `2`.

## Exit codes

| Code | Meaning                                          |
| ---- | ------------------------------------------------ |
| 0    | success (results array may still be empty)       |
| 2    | engine misconfigured or upstream request failed  |
