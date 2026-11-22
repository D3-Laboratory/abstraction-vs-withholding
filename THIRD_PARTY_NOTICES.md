# Third-party notices

## ConVerse

- Source: https://github.com/amrgomaaelhady/ConVerse
- Commit: `d474f6a7eee5caec6df19ea42f112f898d6f10ac` (recorded in every run manifest as `upstream_commit` and in
  the configurations as `benchmark.commit`; the local checkout had no uncommitted changes to tracked files)
- License: MIT (`experiments/third_party/converse/LICENSE`, copied unchanged). The upstream LICENSE file contains the
  MIT permission notice without a copyright line; copyright remains with the ConVerse authors.
- Included subset (unchanged copies): `read_toolkits.py`; `assistant/assistant_prompts.py`;
  `external_agent/external_prompts_{general,adv,benign}.py`; `user_environment/environment_prompts.py`;
  `judge/{generic_prompts,utility_prompts}.py`; the package `__init__.py` files; and
  `resources/{insurance,real_estate,travel_planning}_usecase/` (persona environments, options, privacy and security
  attacks, ratings).
- Our modifications to these files: none. Our code imports the prompt modules and reads the resources. Prompts
  adapted from ConVerse's judges are our own files under `experiments/prompts/` (see `SOURCES.md` there and the
  README); `judge_counterfactual_v25/converse_abstraction.txt` is checked against
  `judge/generic_prompts.py` by `run_judge_counterfactual_v25.py`.

## PrivacyAlign and PrivacyLens judge prompts

`experiments/prompts/judge_counterfactual_v25/privacyalign_leak_omit_no_annotations.txt`,
`privacylens_leakage.txt` and `privacylens_helpfulness.txt` reproduce the judge prompts released with those
benchmarks, with the changes and sources listed in `experiments/prompts/judge_counterfactual_v25/SOURCES.md`.
They remain subject to the licenses of their original repositories.

## Python packages

`numpy`, `scipy`, `matplotlib`, `requests`, `jsonschema` and `certifi` are installed from PyPI under their own
licenses and are not redistributed here.
