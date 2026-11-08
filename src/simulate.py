"""Simulated data for a US sports-betting / casino affiliate site (SIMULATED, not PLAYERSBEST data).

Calibrated on public benchmarks where possible (see SOURCES.md): listed affiliates earn roughly
$200-450 per referred depositing customer, US CPAs sit in the $250-400 range, and revenue share
deals pay 25-35% of net gaming revenue (NGR). Operators are fictional (A-G).

Outputs (data/simulated, seed 2026):
  sim_traffic_daily.csv        date x channel x state x page_type x vertical: sessions, clickouts
  sim_operator_daily.csv       date x channel x state x vertical x operator: clickouts, registrations, tracked NDCs
  sim_ndc_players.csv          one row per NDC as reported by the operator (acquisition attributes)
  sim_ndc_monthly_ngr.csv      one row per NDC x active month: NGR in USD
  sim_operator_deals.csv       contract terms per operator: CPA offer, revenue share offer, current deal
  sim_marketing_cost_daily.csv paid search / social spend by date x channel x state
  sim_anomaly_log.csv          ground truth of the anomalies injected (used only to score detection)
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
OUT = Path(__file__).resolve().parents[1] / "data" / "simulated"
OUT.mkdir(parents=True, exist_ok=True)
START, END = pd.Timestamp("2024-09-01"), pd.Timestamp("2026-08-31")
BASE_SESSIONS = 8000            # average sessions per day before seasonality and growth
ANNUAL_GROWTH = 0.15

# ---------------------------------------------------------------- dimensions
CHANNELS = {   # share of sessions, conversion quality, player value multiplier, cost per click (USD)
    "SEO":         dict(share=0.55, conv=1.00, value=1.00, cpc=0.0),
    "Paid search": dict(share=0.15, conv=1.15, value=0.95, cpc=4.5),
    "Social":      dict(share=0.12, conv=0.60, value=0.70, cpc=1.2),
    "Email":       dict(share=0.06, conv=1.30, value=1.20, cpc=0.0),
    "Direct":      dict(share=0.12, conv=1.10, value=1.15, cpc=0.0),
}
STATES = {     # share of sessions, online casino legal, launch date
    "NY": (0.22, False, None), "IL": (0.13, False, None), "PA": (0.13, True, None),
    "OH": (0.12, False, None), "NJ": (0.10, True, None), "MI": (0.10, True, None),
    "AZ": (0.08, False, None), "CO": (0.06, False, None), "MO": (0.06, False, "2025-12-01"),
}
CASINO_SHARE = 0.35            # share of sessions on casino content in casino-legal states
PAGES = {      # share of sessions, click-out rate (sessions -> operator click)
    "Operator review":    dict(share=0.25, ctr=0.30),
    "Bonus code page":    dict(share=0.20, ctr=0.45),
    "Comparison ranking": dict(share=0.20, ctr=0.38),
    "News & guides":      dict(share=0.35, ctr=0.06),
}
OPERATORS = {  # fictional operators: click share within vertical, funnel rates, player value, deal terms
    "Operator A": dict(vertical="Sportsbook", weight=0.34, reg=0.13, ftd=0.55, value=1.05, cpa=300, rs=0.30, deal="CPA"),
    "Operator B": dict(vertical="Sportsbook", weight=0.26, reg=0.12, ftd=0.52, value=1.10, cpa=275, rs=0.30, deal="Revenue share"),
    "Operator C": dict(vertical="Sportsbook", weight=0.22, reg=0.11, ftd=0.50, value=0.95, cpa=250, rs=0.25, deal="Hybrid", hyb_cpa=125, hyb_rs=0.20),
    "Operator D": dict(vertical="Sportsbook", weight=0.18, reg=0.12, ftd=0.54, value=0.85, cpa=250, rs=0.25, deal="CPA"),
    "Operator E": dict(vertical="Casino", weight=0.45, reg=0.11, ftd=0.47, value=1.00, cpa=400, rs=0.35, deal="CPA"),
    "Operator F": dict(vertical="Casino", weight=0.35, reg=0.10, ftd=0.45, value=1.15, cpa=375, rs=0.35, deal="Revenue share"),
    "Operator G": dict(vertical="Casino", weight=0.20, reg=0.10, ftd=0.44, value=0.90, cpa=350, rs=0.30, deal="Hybrid", hyb_cpa=200, hyb_rs=0.20),
}
NGR = {        # month-1 NGR per NDC (USD), monthly retention, player dispersion, share of losing months
    "Sportsbook": dict(m1=140, keep=0.84, sigma=1.1, neg=0.12),
    "Casino":     dict(m1=220, keep=0.87, sigma=1.2, neg=0.05),
}
MAX_MONTHS = 24

# ---------------------------------------------------------------- sports calendar (real dates)
NFL = [("2024-09-05", "2025-01-05", "2025-01-11", "2025-01-26", "2025-02-09"),
       ("2025-09-04", "2026-01-04", "2026-01-10", "2026-01-25", "2026-02-08")]
MARCH_MADNESS = [("2025-03-18", "2025-04-07"), ("2026-03-17", "2026-04-06")]

dates = pd.date_range(START, END, freq="D")
sport_season = pd.Series(0.65, index=dates)                       # summer: MLB only
sport_season[(dates.month >= 4) & (dates.month <= 6)] = 0.85       # NBA / NHL playoffs
sport_season[(dates.month >= 2) & (dates.month <= 3)] = 0.95
in_nfl = pd.Series(False, index=dates)
for reg_start, reg_end, po_start, po_end, sb in NFL:
    sb = pd.Timestamp(sb)
    sport_season[reg_start:reg_end] = 1.45
    sport_season[po_start:po_end] = 1.70
    sport_season[sb - pd.Timedelta(days=6):sb - pd.Timedelta(days=1)] = 1.90
    sport_season[sb] = 3.20
    in_nfl[reg_start:po_end] = True
for mm_start, mm_end in MARCH_MADNESS:
    sport_season[mm_start:mm_end] = 1.50
    first_weekend = pd.Timestamp(mm_start) + pd.Timedelta(days=2)       # Thursday-Sunday of round 1
    sport_season[first_weekend:first_weekend + pd.Timedelta(days=3)] = 2.10

dow = dates.dayofweek.values                                        # Monday = 0
sport_week = np.where(in_nfl.values,
                      np.select([dow == 6, dow == 0, dow == 3, dow == 5], [1.60, 1.15, 1.15, 1.20], 0.85),
                      np.where(dow >= 5, 1.10, 0.96))
casino_season = 1 + 0.06 * np.cos(2 * np.pi * (dates.dayofyear.values - 15) / 365)   # mild winter peak
casino_week = np.where((dow == 4) | (dow == 5), 1.10, 0.97)
growth = 1 + ANNUAL_GROWTH * (dates - START).days.values / 365

# promo intensity lifts click-outs: NFL kick-off fortnight and Super Bowl week
promo = pd.Series(1.0, index=dates)
for reg_start, *_, sb in NFL:
    promo[reg_start:pd.Timestamp(reg_start) + pd.Timedelta(days=13)] = 1.10
    promo[pd.Timestamp(sb) - pd.Timedelta(days=6):sb] = 1.10

# ---------------------------------------------------------------- daily grid
sv = [(s, "Sportsbook") for s in STATES] + [(s, "Casino") for s, v in STATES.items() if v[1]]
grid = pd.MultiIndex.from_product([range(len(dates)), list(CHANNELS), range(len(sv)), list(PAGES)],
                                  names=["d", "channel", "sv", "page_type"]).to_frame(index=False)
grid["date"] = dates.values[grid.d]
grid["state"] = [sv[i][0] for i in grid.sv]
grid["vertical"] = [sv[i][1] for i in grid.sv]
d = grid.d.values
is_casino = (grid.vertical == "Casino").values
st_share = grid.state.map({k: v[0] for k, v in STATES.items()}).values
casino_state = grid.state.map({k: v[1] for k, v in STATES.items()}).values
launch = grid.state.map({k: pd.Timestamp(v[2]) if v[2] else START for k, v in STATES.items()})
live = (grid.date >= launch).values
v_split = np.where(is_casino, CASINO_SHARE, np.where(casino_state, 1 - CASINO_SHARE, 1.0))
season = np.where(is_casino, casino_season[d] * casino_week[d], sport_season.values[d] * sport_week[d])
ch = grid.channel
expected = (BASE_SESSIONS * growth[d] * season * ch.map({k: v["share"] for k, v in CHANNELS.items()}).values
            * st_share * v_split * grid.page_type.map({k: v["share"] for k, v in PAGES.items()}).values * live)

# SEO algorithm update: SEO sessions drop 25% from 15 March 2026 (level shift)
seo_update = (ch == "SEO").values & (grid.date >= "2026-03-15").values
expected = np.where(seo_update, expected * 0.75, expected)
# email blasts on Super Bowl days and the first day of March Madness round 1
blast_days = [pd.Timestamp(x[4]) for x in NFL] + [pd.Timestamp(a) + pd.Timedelta(days=2) for a, _ in MARCH_MADNESS]
expected = np.where((ch == "Email").values & grid.date.isin(blast_days).values, expected * 2.5, expected)

conv = ch.map({k: v["conv"] for k, v in CHANNELS.items()}).values
grid["sessions"] = rng.poisson(expected)
ctr = grid.page_type.map({k: v["ctr"] for k, v in PAGES.items()}).values * np.sqrt(conv) * promo.values[d]
grid["clickouts"] = rng.binomial(grid.sessions.values, np.clip(ctr, 0, 0.95))

# new-state launch: first 30 days convert 60% better (launch bonuses)
mo_boost = np.where((grid.state == "MO").values & (grid.date < "2025-12-31").values, 1.6, 1.0)

# ---------------------------------------------------------------- anomaly 1: bot clicks (paid search, IL)
bot = ((ch == "Paid search").values & (grid.state == "IL").values & (grid.vertical == "Sportsbook").values
       & (grid.page_type == "Comparison ranking").values & grid.date.between("2025-10-20", "2025-10-22").values)
bot_sessions = np.where(bot, rng.poisson(2500, len(grid)), 0)
bot_clicks = rng.binomial(bot_sessions, 0.70)
grid["sessions"] += bot_sessions
grid["clickouts"] += bot_clicks

# ---------------------------------------------------------------- operator split and funnel
rows = []
for vertical in ["Sportsbook", "Casino"]:
    ops = [o for o, v in OPERATORS.items() if v["vertical"] == vertical]
    w = np.array([OPERATORS[o]["weight"] for o in ops]); w = w / w.sum()
    idx = np.nonzero((grid.vertical == vertical).values)[0]
    human = grid.clickouts.values[idx] - bot_clicks[idx]
    split = rng.multinomial(human, w)                       # (cells, operators)
    bot_split = rng.multinomial(bot_clicks[idx], w)
    for j, o in enumerate(ops):
        op = OPERATORS[o]
        reg = rng.binomial(split[:, j], np.clip(op["reg"] * np.sqrt(conv[idx]) * mo_boost[idx], 0, 0.9))
        ndc = rng.binomial(reg, op["ftd"])
        rows.append(pd.DataFrame({"cell": idx, "operator": o, "clickouts": split[:, j] + bot_split[:, j],
                                  "registrations": reg, "ndcs": ndc}))
opd = pd.concat(rows, ignore_index=True)
opd = opd.join(grid[["date", "channel", "state", "page_type", "vertical"]], on="cell")

# ---------------------------------------------------------------- players (operator-reported NDCs)
win = opd[opd.ndcs > 0]
pl = win.loc[win.index.repeat(win.ndcs), ["date", "channel", "state", "page_type", "vertical", "operator"]]
pl = pl.rename(columns={"date": "ftd_date"}).sort_values("ftd_date").reset_index(drop=True)
pl.insert(0, "ndc_id", np.arange(1, len(pl) + 1))

# ---------------------------------------------------------------- anomaly 2: broken postback (Operator D)
# NDCs still happen (the operator reports them monthly) but our daily tracking records zero
broken = (opd.operator == "Operator D") & opd.date.between("2026-01-12", "2026-01-15")
opd["ndcs_tracked"] = np.where(broken, 0, opd.ndcs)

# ---------------------------------------------------------------- monthly NGR per NDC
N = len(pl)
vert = pl.vertical.values
p = {k: np.array([NGR[v][k] for v in vert]) for k in ["m1", "keep", "sigma", "neg"]}
value = (p["m1"] * np.exp(p["sigma"] * rng.standard_normal(N) - p["sigma"] ** 2 / 2)
         * pl.channel.map({k: v["value"] for k, v in CHANNELS.items()}).values
         * pl.operator.map({k: v["value"] for k, v in OPERATORS.items()}).values)
keep = np.clip(p["keep"] + 0.03 * np.log(np.maximum(value, 1) / p["m1"]), 0.5, 0.97)   # better players stay longer
ftd_month = pl.ftd_date.values.astype("datetime64[M]")
last_month = np.datetime64(END, "M")
alive = np.ones(N, bool)
ngr_rows = []
for m in range(1, MAX_MONTHS + 1):
    if m > 1:
        alive &= rng.random(N) < keep
    month = ftd_month + np.timedelta64(m - 1, "M")
    obs = alive & (month <= last_month)
    i = np.nonzero(obs)[0]
    if len(i) == 0:
        break
    amt = value[i] * rng.gamma(2.0, 0.5, len(i))
    losing = rng.random(len(i)) < p["neg"][i]
    amt = np.where(losing, -0.6 * amt, amt)
    ngr_rows.append(pd.DataFrame({"ndc_id": pl.ndc_id.values[i], "month_n": m,
                                  "month_start": month[i].astype("datetime64[D]"), "ngr_usd": amt.round(2)}))
ngr = pd.concat(ngr_rows, ignore_index=True).sort_values(["ndc_id", "month_n"])

# ---------------------------------------------------------------- marketing cost (paid channels)
paid = grid[grid.channel.isin(["Paid search", "Social"])]
cost = paid.groupby(["date", "channel", "state", "vertical"], as_index=False).sessions.sum()
cpc = cost.channel.map({k: v["cpc"] for k, v in CHANNELS.items()}) * np.where(cost.vertical == "Casino", 1.3, 1.0)
cost["spend_usd"] = (cost.sessions * cpc * rng.lognormal(0, 0.10, len(cost))).round(2)
cost = cost.rename(columns={"sessions": "paid_clicks"})

# ---------------------------------------------------------------- deals and anomaly log
deals = pd.DataFrame([dict(operator=o, vertical=v["vertical"], current_deal=v["deal"],
                           cpa_offer_usd=v["cpa"], revshare_offer_pct=v["rs"],
                           hybrid_cpa_usd=v.get("hyb_cpa"), hybrid_revshare_pct=v.get("hyb_rs"))
                      for o, v in OPERATORS.items()])
anomalies = pd.DataFrame([
    dict(anomaly_id=1, start="2025-10-20", end="2025-10-22", type="Bot clicks",
         scope="Paid search / IL / Sportsbook / Comparison ranking",
         description="~2,500 extra bot sessions a day, 70% click out, no registrations"),
    dict(anomaly_id=2, start="2026-01-12", end="2026-01-15", type="Broken tracking",
         scope="Operator D", description="Postback failure: tracked NDCs = 0 while the operator still reports them"),
    dict(anomaly_id=3, start="2026-03-15", end="2026-08-31", type="Level shift",
         scope="SEO", description="Search algorithm update: SEO sessions -25% from 15 March 2026"),
])

# ---------------------------------------------------------------- write
traffic = grid[["date", "channel", "state", "page_type", "vertical", "sessions", "clickouts"]]
traffic = traffic[traffic.sessions > 0]
op_daily = (opd.groupby(["date", "channel", "state", "vertical", "operator"], as_index=False)
            [["clickouts", "registrations", "ndcs_tracked"]].sum())
op_daily = op_daily[op_daily.clickouts > 0]
fmt = dict(index=False, date_format="%Y-%m-%d")
traffic.to_csv(OUT / "sim_traffic_daily.csv", **fmt)
op_daily.to_csv(OUT / "sim_operator_daily.csv", **fmt)
pl.to_csv(OUT / "sim_ndc_players.csv", **fmt)
ngr.to_csv(OUT / "sim_ndc_monthly_ngr.csv", **fmt)
deals.to_csv(OUT / "sim_operator_deals.csv", index=False)
cost.to_csv(OUT / "sim_marketing_cost_daily.csv", **fmt)
anomalies.to_csv(OUT / "sim_anomaly_log.csv", index=False)

# ---------------------------------------------------------------- calibration check
print(f"sessions {traffic.sessions.sum():,}  clickouts {traffic.clickouts.sum():,}  "
      f"CTR {traffic.clickouts.sum() / traffic.sessions.sum():.1%}")
print(f"registrations {op_daily.registrations.sum():,}  tracked NDCs {op_daily.ndcs_tracked.sum():,}  "
      f"reported NDCs {N:,}  NDC/clickout {N / traffic.clickouts.sum():.2%}")
print("NDCs per month (mean):", int(pl.groupby(pl.ftd_date.dt.to_period('M')).size().mean()))
print(f"rows: traffic {len(traffic):,}  operator {len(op_daily):,}  players {N:,}  ngr {len(ngr):,}  cost {len(cost):,}")
early = pl[pl.ftd_date < "2025-03-01"].ndc_id     # cohorts with at least 18 observed months
cum = ngr[ngr.ndc_id.isin(early)].merge(pl[["ndc_id", "vertical", "operator"]], on="ndc_id")
for v in ["Sportsbook", "Casino"]:
    n = (pl.ndc_id.isin(early) & (pl.vertical == v)).sum()
    by_m = cum[cum.vertical == v].groupby("month_n").ngr_usd.sum().cumsum() / n
    print(f"{v}: cumulative NGR per NDC  m1 {by_m.get(1, 0):.0f}  m6 {by_m.get(6, 0):.0f}  "
          f"m12 {by_m.get(12, 0):.0f}  m18 {by_m.get(18, 0):.0f}")
print(f"paid spend USD {cost.spend_usd.sum():,.0f}")
