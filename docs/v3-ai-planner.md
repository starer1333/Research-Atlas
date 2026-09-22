# V3-10 — Optional AI Research Planner

The AI Research Planner is an optional intelligence layer, not part of the deterministic evidence/finance core.

## Boundary

The planner may produce:

- suggested research questions
- possible investigation paths
- evidence to seek
- counter-evidence to seek
- suggested next actions

It may not:

- write or modify observations
- mark evidence reviewed / verified
- calculate financial metrics
- create a final Claim automatically
- issue investment recommendations
- execute model-suggested tool calls

Nothing is persisted until the user explicitly chooses Add question.

## Enable

AI networking is off by default.

PowerShell example:

    $env:ATLAS_AI_BASE_URL="https://api.example.com/v1"
    $env:ATLAS_AI_API_KEY="..."
    $env:ATLAS_AI_MODEL="your-model"
    python -B serve_atlas.py --enable-ai

The endpoint must be HTTPS and OpenAI-compatible for /chat/completions. The API key is never returned to the browser.

## Grounding

The planner receives a compact research snapshot:

- company / industry / research-as-of
- deterministic findings
- current research questions
- industry-driver prompts
- source metadata
- explicit allowed evidence IDs and source IDs

Raw documents are not sent by default. Unknown model-generated evidence/source IDs are dropped and surfaced as a warning.

## Security

- browser cannot provide an arbitrary AI endpoint
- localhost/private-IP endpoints are rejected
- document text is data, never an executable instruction
- model output is parsed as JSON and rendered as ai_suggested / not_verified
- the planner has no write path into verified evidence
