# Internal / one-off scripts

Ad-hoc scripts that produced (or maintain) the `kaggle_solutions/` tree — batch generators, optimizers, counters. **Not part of the public API or supported user workflow.**

If a contributor wants to repeat one of these batches, the scripts are here as reference. Don't expect them to be polished or kept in sync with the main code.

## What's in here

| Script | What it does |
|---|---|
| `batch_create_geospatial.py` | One-shot generator for the `12_geospatial/` solutions |
| `batch_create_solutions.py` | Generic batch generator |
| `batch_optimizer.py` | Batch optimization pass over generated solutions |
| `count_solutions.py` | Counts solutions across the 17 categories |
| `create_anomaly_solutions.py` | Generator for the `10_anomaly_detection/` solutions |
| `expand_solutions.py` | Expands stub solutions to fuller implementations |
| `generate_dl_solutions.py` | Generator for the `08_deep_learning/` solutions |
| `generate_remaining_anomaly_solutions.sh` | Shell wrapper around the anomaly generator |
| `optimize_all_solutions.py` | Repo-wide optimization pass |
| `new_solutions_record.json` | One-shot record of generated solution metadata |

For the user-facing CLI / library, see the main `data_analysis_chatbots/` package and the project [README](../../README.md).
