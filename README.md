# LangChain + Gemini tool-calling prototype

## Website generator MVP

Start the local website generator from the repository root:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:8765`. The server reads `GOOGLE_API_KEY` (or
`GEMINI_API_KEY`) from the process environment, repository `.env`, or the
existing parent `.env`. Enter a description and Gemini model, generate a
self-contained HTML page, inspect its preview/code/checks, then download it.
The default web UI model is `gemini-3.5-flash-lite`; change it in the interface
if your Gemini account or current provider availability requires another model.
Requests to Gemini may incur API charges and can fail due to model availability
or account quota. Generated HTML is kept in the browser until downloaded.

Checks cover basic document structure, external references, JavaScript syntax
(when Node.js is installed), and preview startup errors/text. They do not prove
that every requested feature works. Preview uses a sandboxed iframe with a
restrictive content policy; it is not a substitute for a hardened isolation
boundary. Review downloaded code before running or publishing it.

Run project tests with:

```powershell
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

**Coursework:** the separate report and presentation are described in [[Course Deliverables]]. The website generator is a later user-requested software goal, not a confirmed course requirement.

Minimal demo: a local LM Studio model or Gemini calls one LangChain tool with one string argument. The
`count_characters(text)` tool returns the length of the exact string supplied.

## Run on this computer

From this repository directory, use the existing virtual environment one level
above and the existing `.env` file in the parent directory:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe main.py
```

By default the demo uses LM Studio at `http://localhost:1234/v1` and the model
`liquid/lfm2.5-1.2b`. Start LM Studio's local server and load that model first.
Set `LM_STUDIO_MODEL` or `LM_STUDIO_BASE_URL` in the parent `.env` to override
these defaults. For Gemini, set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY` in
the parent `.env`. The API key is never printed by the demo.

Pass a request and select a provider or model without editing `.env`:

```powershell
..\.venv\Scripts\python.exe main.py --provider lmstudio "Count the characters in hello"
..\.venv\Scripts\python.exe main.py --provider gemini --model gemini-3.6-flash
```

The Gemini launcher in `test/` also accepts the prompt and `--model` options:

```powershell
..\.venv\Scripts\python.exe test\run_gemini.py
..\.venv\Scripts\python.exe test\run_gemini.py --model gemini-3.6-flash "Count the characters in hello"
```

The current prototype only exposes `count_characters`: it does not generate or
execute web projects yet. Open this repository as an Obsidian vault to browse
[[Project Overview]], [[Research]], [[Architecture]], and [[Project Plan]].
