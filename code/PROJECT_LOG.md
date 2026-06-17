# Project Log — GPDP / 15FC Grant Policy Brief

**Folder:** `Bihar Gates Team/4_Policy Briefs/GPDP/`
**Log started:** 2026-06-16 (Sharan + Claude)

---

## What this is

A policy brief on **15th Finance Commission (15FC) panchayat grant spending** in
Bihar, FY 2024-25. Ankita's `GPDP_basic_correlations.do` runs first-pass
correlations; the deliverable here is a **standalone offline dashboard**
(`dashboard.html`) mirroring the Jeevika MIS dashboard (3 tabs, maroon house style,
Plotly inlined, double-click to open).

## Data

- **Grant data:** `GPDP Analysis (For Non-Peer)/ugp_xvfc_2024_25.dta` — 7,796 GPs
  matched to UGP (of 8,392), all 38 districts. Basic (untied) + Tied grants, each
  split Opening / Direct Receipt / Auto Receipt / Expenditure / Unspent + consolidated.
  - **Accounting identity holds exactly:** opening + receipts = expenditure + unspent.
    So utilisation = exp/available, unspent share = 1 − utilisation.
- **GP controls:** `…/NREGA/GPExtendedControls_clean.dta` (pop, villages, area,
  dist-to-HQ, dist-to-town, SC share).
- **Reservation:** `…/Reservation_Pop_F.dta` (SC-reserved, women-reserved 2016).
- **Geo:** reused Jeevika's `bihar_districts.geojson`. District names match except
  `KAIMUR (BHABUA)` → `KAIMUR` (1 fix). 38/38 assert passes.
- Analysis frame: 7,660 GPs (positive available funds, pop > 200, top-1% per-cap trim).

## The story (two honest facts)

1. **₹1,278 cr of ₹3,999 cr (32%) sits UNSPENT — and it's systemic, not selective.**
   Utilisation ≈ 68–71% flat across every population quintile; GP characteristics
   barely predict unspent share (only population sig, β = −0.55 pp/SD, p=.016; rest n.s.).
   Real variation is **across districts** (low-20s to >40%) — an administrative pattern.
2. **Smaller GPs deliver more per resident (the "better for residents" case).** Smallest
   quintile spends ₹407/cap vs ₹239 in the largest — **1.7×**. Holds for BOTH earmarked/tied
   (₹234 vs ₹142) and flexible/untied (₹173 vs ₹97). Population (−₹66/SD, p≈1e-126) and area
   (−₹29/SD, p≈1e-14) dominate. **Honesty caveat:** total spending RISES with population
   (₹29L→₹41L, large GPs spend ~1.4× more total) — the advantage is strictly per-capita, and
   tracks how the grant is allocated per head (grant/cap falls with pop just as fast).

## Files

- `gpdp_build_dashboard.py` — self-contained build: loads 3 .dta, merges, runs
  within-district (FE) regressions via statsmodels, builds 8 Plotly figs, writes HTML.
  Re-run: `python3 gpdp_build_dashboard.py`. Deps: pandas, statsmodels, plotly (WSL).
- `dashboard.html` — 5.0 MB offline deliverable. 3 tabs:
  - ① unspent share choropleth + district ranking
  - ② drivers-of-unspent effect-size bars (flat) + utilisation-flat-by-quintile
  - ③ "Smaller GPs, more per resident": per-cap drivers bars + tied/untied per-capita
    stacked-by-quintile + binned scatter (dropdown) + per-cap choropleth
  - Choropleths exclude ARWAL (n=1) and clamp colour range to observed district range
    (yellow→maroon for unspent; the old light-pink→maroon ramp washed out mid-range districts)
- `GPDP_basic_correlations.do` — Ankita's original correlations (input do-file).

## Status

- [x] Built dashboard end-to-end (2026-06-16). Structure validated (plotly inlined once,
  8 plots, 3 tabs).
- [ ] Visual check — Sharan to open `dashboard.html` in Windows (WSL can't screenshot).
- [ ] Possible: CEO/brief slide or figure exports if needed (not yet built).

## Gotchas

- ARWAL has only 1 matched GP — shown on maps, excluded from district rankings; footnoted.
- Paths in the build script are Sharan's WSL paths; Ankita's .do uses her own (`C:\Users\ankita`).
- Big N (~7.7k) makes p<.001 trivial — story leans on effect sizes/gradients, not stars.
