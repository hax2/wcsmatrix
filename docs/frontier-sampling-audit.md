# Frontier sampling audit — 2026-10-28

This audit distinguishes submitted request settings, provider metadata defaults, and the effective historical sampler. The original 2026-10-27 requests omitted temperature, top-p, top-k, penalties, seed, custom stop sequences, and logit bias. Every request set low reasoning effort, reasoning exclusion from the returned response, and a 4096-token output cap. No generation was rerun for this audit.

## Findings

| Model | Actual recorded route | Sampler evidence |
| --- | --- | --- |
| GPT-6 Astra | OpenAI, all 50 | Temperature/top-p unsupported with non-none reasoning. OpenRouter's endpoint exposes neither. Numeric internal temperature, top-p, and top-k are not disclosed by the checked metadata or documentation. |
| Claude Opus 5.5 | Claude Platform on AWS, all 50 | Anthropic removed temperature/top-p/top-k controls for this model. The checked API documentation does not give numeric internal equivalents. |
| Gemini 4 Argon | Google, 48; Google AI Studio, 2 | Google's `models.get` metadata advertises temperature **1.0**, top-p **0.95**, top-k **64**. These are directly retrieved model defaults, not values echoed by the 150 historical completions. Google's current migration guide also says temperature/top-p/top-k inputs are ignored. |

The Gemini metadata response is preserved in `gemini-model-metadata-2026-10-28.json`. The REST model resource documentation defines these fields as backend defaults, so they are the strongest available numeric default evidence. They do not establish the exact effective per-token sampler for the earlier Google/AI Studio routes. The metadata also differs from current descriptive documentation in its output-token limit; preserve it as observed metadata rather than treating every field as a definitive statement about current endpoint behavior.

## Historical record checks

Inspected every stored answer's provider/model fields and the saved raw completion responses. Queried authenticated OpenRouter generation metadata for one historical completion from each of the four distinct model/provider routes. Those lookups succeeded and reported no preset, but did not return temperature, top-p, top-k, or other effective sampling controls. Account-specific lookup responses are retained only in ignored `results/manifests/sampling-audit/`.

OpenRouter documents that absent sampler fields are omitted from the upstream request. Its conventional parameter defaults (temperature 1, top-p 1, top-k 0) are **not** values it inserts. Consequently it would be incorrect to assign temperature=1/top-p=1/top-k=0 to this whole collection. Provider-managed decoding remains part of the frontier-source experimental condition; it is not a controlled greedy condition.

## Sources

- OpenRouter parameter forwarding: https://openrouter.ai/docs/api_reference/parameters
- OpenRouter historical generation metadata: https://openrouter.ai/docs/api-reference/get-a-generation
- OpenAI sampler restrictions under reasoning: https://developers.openai.com/api/docs/guides/latest-model
- Anthropic removal of sampler controls: https://platform.claude.com/docs/en/models/opus-5-5/migration-guide
- Gemini ignored sampler controls: https://ai.google.dev/gemini-api/docs/latest-model?hl=en
- Gemini metadata field semantics: https://ai.google.dev/api/models
- Gemini live metadata endpoint, authenticated with the existing local Gemini key: `GET https://generativelanguage.googleapis.com/v1beta/models/gemini-4-argon`. The key was sent in a header and is not included in the archived response.

No request settings, source texts, frozen prompts, or experiment identities were changed by this audit.
