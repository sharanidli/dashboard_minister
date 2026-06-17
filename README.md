# Bihar GPDP / 15th Finance Commission Grant Dashboard

Self-contained offline dashboard of XV Finance Commission panchayat grant
spending in Bihar, FY 2024-25 (~7,660 Gram Panchayats, 38 districts).

Open **`dashboard/dashboard.html`** in any browser (double-click; no internet needed).

## Story (correlational)
1. **A third sits unspent** — ₹1,278 cr of ₹3,999 cr (32%) of grants unspent; the
   variation is across *districts*, not GP types.
2. **Underspending is systemic** — GP characteristics barely predict unspent share;
   utilisation is flat (~70%) across GP size.
3. **Smaller GPs deliver more per resident** — smallest GPs spend ₹407/capita vs ₹239
   in the largest (1.7×), across both earmarked and flexible funds. (Total spending
   still rises with population — the advantage is strictly per-capita, tracking the
   per-head grant allocation.)

## Build
`python3 code/gpdp_build_dashboard.py` (needs pandas, statsmodels, plotly; reads
grant + control + reservation .dta files locally — data not committed). Correlations
follow `code/GPDP_basic_correlations.do`.
