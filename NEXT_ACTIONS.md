# GTPJ Next Actions

This is the current execution window. Keep only the near-term actions here.

## P0

- [x] Promote min3-confirmed `local-v3-054` to the formal version `GTPJ-v4`.
- [x] Activate TRIAL-003 best conditional-BVSA-text candidate as `GTPJ-v5` active mainline.
- [x] Apply 2026-06-29 Warehouse checkpoint retention: keep Top-5 best `model_best`/best-model files and record the retention manifest.
- [ ] Keep Warehouse checkpoint retention to Top-5 best `model_best`/best-model files after each future completed campaign.

## P1

- [ ] Continue v5-based tuning or ablation from `config/versions/v5.yaml`.
- [ ] Confirm whether v5 can exceed `v4 confirmed_H=74.45` by repeat mean after the next tuning round.

## Done

- [x] Initialized clean GTPJ repository and workflow helper.
- [x] Established `GTPJ-v1` first formal baseline, CUB seed=5 H=73.93.
- [x] Recorded `GTPJ-v2` as owner-activated, best_observed_H=74.29, confirmed_H pending.
- [x] Recorded `GTPJ-v3` as owner-accepted stochastic, best_observed_H=74.27, confirmed_H pending.
- [x] Confirmed `local-v3-054` by server min3: H=74.46 / 74.42 / 74.47.
- [x] Wrote checkpoint retention policy and cleaned Warehouse training checkpoints to Top-5 best-model files.
