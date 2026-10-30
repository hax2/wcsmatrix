# Data provenance

Human questions and answers are from **HC3**, Biyang Guo et al. (2023), “How Close is ChatGPT to Human Experts? Comparison Corpus, Evaluation, and Detection,” https://arxiv.org/abs/2301.07597; dataset https://huggingface.co/datasets/Hello-SimpleAI/HC3, CC BY-SA 4.0 as declared by its dataset card.

`prompts/hc3-50.jsonl` and `texts/human.jsonl` are selected and reformatted excerpts from the pinned HC3 ELI5 subset. Modifications: select the first length-eligible answer per question, seed-sample 50 questions, add stable source line IDs, and add a common generation prompt plus provenance hashes. The manifest records the raw-file hash, dataset commit, and selection settings. These dataset-derived files remain under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/ . The repository's MIT code license does not relicense the dataset or supplied paper.

`texts/frontier.jsonl` contains API model outputs on these questions, labeled `kind: frontier`, with request/response provenance, response IDs, timing, usage, and completion status. It contains no API secrets. Model API aliases may change; a pinned request does not guarantee a bit-identical future response.

`texts/local.jsonl` is created on the GPU server and can be committed or transferred back for analysis. Large token arrays and raw responses remain ignored. Do not commit `.env` files, account credentials, or downloaded model weights.

`texts/open-frontier-20261030.jsonl` is the separate hosted open-weight cohort. Each row records explicit sampling/reasoning requests, provider/model identity, and reference weight repository/commit/license metadata. Reference commits do not certify the hosted provider's exact weight revision. The original closed-frontier file is preserved; the combined experiment reads both files. See [the open-frontier protocol](../docs/open-frontier.md).

The Wiki CS/AI frontier files (`texts/wiki-closed-frontier-20261030.jsonl` and `texts/wiki-open-frontier-20261030.jsonl`) answer the frozen questions in `prompts/wiki-50.jsonl`, using the same cohort-specific generation requests as their ELI5 counterparts. The pre-existing Wiki human/local source files and manifest are preserved. See [the Wiki protocol](../docs/wiki-frontier.md).
