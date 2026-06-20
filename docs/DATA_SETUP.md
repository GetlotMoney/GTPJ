# Data Setup

Datasets and feature caches are not tracked by Git.

Expected local paths:

```text
data/xlsa17/data/CUB/
data/xlsa17/data/AWA2/
data/xlsa17/data/SUN/
data/CUB/images/
data/gpt4_data/
data/cache/
```

Do not commit:

- raw datasets
- CLIP feature caches
- checkpoints
- large training logs

For a run record, store only lightweight summaries in Git and record the local or cloud path for large artifacts.
