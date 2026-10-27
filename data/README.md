# Data provenance

Human questions and answers are from **HC3**, Biyang Guo et al. (2023), “How Close is ChatGPT to Human Experts? Comparison Corpus, Evaluation, and Detection,” https://arxiv.org/abs/2301.07597; dataset https://huggingface.co/datasets/Hello-SimpleAI/HC3, CC BY-SA 4.0 as declared by its dataset card.

`prompts/hc3-50.jsonl` and `texts/human.jsonl` are selected and reformatted excerpts from the pinned HC3 ELI5 subset. Modifications: select the first length-eligible answer per question, seed-sample 50 questions, add stable source line IDs, and add a common generation prompt plus provenance hashes. The manifest records the raw-file hash, dataset commit, and selection settings. These dataset-derived files remain under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/ . The repository's MIT code license does not relicense the dataset or supplied paper.

`texts/frontier.jsonl` contains API model outputs on these questions, labeled `kind: frontier`, with request/response provenance, response IDs, timing, usage, and completion status. It contains no API secrets. Model API aliases may change; a pinned request does not guarantee a bit-identical future response.

`texts/local.jsonl` is created on the GPU server and can be committed or transferred back for analysis. Large token arrays and raw responses remain ignored. Do not commit `.env` files, account credentials, or downloaded model weights.
