"""Generate the Power BI report pages (PBIR format) for powerbi/PlayersBestCaseStudy.Report.

Usage:  python src/build_report_pages.py
Close Power BI Desktop first (or let it reload): every page is rewritten from this script.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "powerbi" / "PlayersBestCaseStudy.Report"
PAGES = REPORT / "definition" / "pages"
VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
PAGES_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"
M = "_Measures"

INK, INK2, MUTED = "#0B0B0B", "#52514E", "#898781"
BLUE, RED, GREY = "#2A78D6", "#D03B3B", "#B4B2A9"
SEQ = {"100": "#CDE2FB", "250": "#86B6EF", "350": "#5598E7", "450": "#2A78D6", "650": "#104281"}
NEUTRAL, RED_TINT, BLUE_TINT = "#F0EFEC", "#F4C7C6", "#B7D3F6"
AUTHOR = "Independent case study · Not affiliated with PLAYERSBEST (formerly Growth Leads)"


# ---------- expression helpers ----------
def raw(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, (int, float)):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"Literal": {"Value": s}}

def lit(v):
    return {"expr": raw(v)}

def color(hexv):
    return {"solid": {"color": lit(hexv)}}

def col(table, column):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}

def meas(name):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": name}}

def qref(field):
    if "Column" in field:
        c = field["Column"]
        return f'{c["Expression"]["SourceRef"]["Entity"]}.{c["Property"]}'
    return f'{M}.{field["Measure"]["Property"]}'

def proj(field, label=None):
    p = {"field": field, "queryRef": qref(field)}
    p["nativeQueryRef"] = field["Column"]["Property"] if "Column" in field else field["Measure"]["Property"]
    if label:
        p["displayName"] = label
    return p

def C(t, c): return col(t, c)
def Ms(*names): return [meas(n) for n in names]

def series_color(field, hexv):
    return {"properties": {"fill": color(hexv)}, "selector": {"metadata": qref(field)}}

def line_style(field, hexv, dashed=False, width=2, markers=False):
    props = {"fill": color(hexv), "strokeWidth": lit(width)}
    if dashed:
        props["lineStyle"] = lit("dashed")
    if markers:
        props["showMarker"] = lit(True)
        props["markerSize"] = lit(6)
    return {"properties": props, "selector": {"metadata": qref(field)}}

def ref_line(value, label, hexv=INK2, selector_id="1"):
    v = {"expr": value} if isinstance(value, dict) else lit(value)
    return {"properties": {"show": lit(True), "value": v, "displayName": lit(label), "lineColor": color(hexv),
                           "style": lit("dashed"), "dataLabelShow": lit(True), "dataLabelColor": color(hexv)},
            "selector": {"id": selector_id}}

def bg_rule(field, lo, hi, mid=None, mid_value=None):
    rule = {"min": {"color": raw(lo)}, "max": {"color": raw(hi)},
            "nullColoringStrategy": {"strategy": raw("asZero")}}
    key = "linearGradient2"
    if mid:
        key = "linearGradient3"
        rule["mid"] = {"color": raw(mid)}
        if mid_value is not None:
            rule["mid"]["value"] = raw(mid_value)
    return {"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {"Input": field, "FillRule": {key: rule}}}}}}},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": qref(field)}}

def table_style(extra_values=(), font=12):
    fs = {"properties": {"fontSize": lit(font)}}
    return {"values": [fs, *extra_values],
            "columnHeaders": [{"properties": {"fontSize": lit(font), "fontColor": color(INK2)}}],
            "total": [{"properties": {"totals": lit(False)}}]}

NO_LEGEND = {"legend": [{"properties": {"show": lit(False)}}]}
LEGEND_TOP = {"legend": [{"properties": {"show": lit(True), "position": lit("Top")}}]}


# ---------- page / visual builders ----------
class Page:
    def __init__(self, pid, name):
        self.pid, self.name, self.visuals, self.interactions, self.n = pid, name, [], [], 0

    def _add(self, vid, x, y, w, h, visual):
        self.n += 1
        self.visuals.append({"$schema": VC_SCHEMA, "name": vid,
                             "position": {"x": round(x), "y": round(y), "z": self.n * 1000,
                                          "height": round(h), "width": round(w), "tabOrder": self.n * 1000},
                             "visual": visual})
        return vid

    def chart(self, vid, vtype, x, y, w, h, roles, title=None, objects=None, labels=None, sort=None, only=None):
        """only: list of (table, column, values, negate) visual-level filters."""
        labels = labels or {}
        visual = {"visualType": vtype,
                  "query": {"queryState": {r: {"projections": [proj(f, labels.get(qref(f))) for f in fs]}
                                           for r, fs in roles.items() if fs}},
                  "drillFilterOtherVisuals": True}
        if sort:
            field, direction = sort
            visual["query"]["sortDefinition"] = {"sort": [{"field": field, "direction": direction}], "isDefaultSort": False}
        if objects:
            visual["objects"] = objects
        visual["visualContainerObjects"] = {
            "subTitle": [{"properties": {"show": lit(False)}}],
            "title": [{"properties": {"show": lit(bool(title)), **({"text": lit(title)} if title else {})}}]}
        self._add(vid, x, y, w, h, visual)
        if only:
            filters = []
            for i, (table, column, values, negate) in enumerate(only):
                cond = {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": column}}],
                               "Values": [[raw(v)] for v in values]}}
                if negate:
                    cond = {"Not": {"Expression": cond}}
                filters.append({"name": f"visualFilter{i}", "type": "Categorical", "field": col(table, column),
                                "filter": {"Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                                           "Where": [{"Condition": cond}]}})
            self.visuals[-1]["filterConfig"] = {"filters": filters}
        return vid

    def text(self, vid, x, y, w, h, paragraphs, boxed=False):
        paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "color": c,
                                                         **({"fontWeight": "bold"} if b else {})}}
                               for t, s, c, b in runs]} for runs in paragraphs]
        visual = {"visualType": "textbox",
                  "objects": {"general": [{"properties": {"paragraphs": paras}}]},
                  "visualContainerObjects": {"background": [{"properties": {"show": lit(boxed)}}],
                                             "border": [{"properties": {"show": lit(boxed)}}],
                                             **({"padding": [{"properties": {"top": lit(16), "bottom": lit(16),
                                                                             "left": lit(20), "right": lit(20)}}]}
                                                if boxed else {})}}
        return self._add(vid, x, y, w, h, visual)

    def header(self, title, conclusion, tag):
        self.text("title", 32, 20, 1500, 56, [[(title, 22, INK, True)]])
        self.text("tag", 1540, 28, 348, 40, [[(tag, 10, INK2, True)]])
        self.text("conclusion", 32, 76, 1856, 72, [[(conclusion, 13, INK2, False)]])

    def footer(self, source):
        self.text("footer", 32, 1040, 1856, 32, [[(source + "   ·   " + AUTHOR, 9, MUTED, False)]])

    def slicer(self, vid, x, y, w, h, field, title, dropdown=True, single=False, default=None):
        objs = {"header": [{"properties": {"show": lit(False)}}]}
        if default is not None:      # pre-selected value
            table, column = field["Column"]["Expression"]["SourceRef"]["Entity"], field["Column"]["Property"]
            objs["general"] = [{"properties": {"filter": {"filter": {
                "Version": 2, "From": [{"Name": "s", "Entity": table, "Type": 0}],
                "Where": [{"Condition": {"In": {
                    "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": column}}],
                    "Values": [[raw(default)]]}}}]}}}}]
        if dropdown:
            objs["data"] = [{"properties": {"mode": lit("Dropdown")}}]
        if single:
            objs["selection"] = [{"properties": {"singleSelect": lit(True), "strictSingleSelect": lit(True)}}]
        return self.chart(vid, "slicer", x, y, w, h, {"Values": [field]}, title, objs)

    def card(self, vid, x, y, w, h, measure, title, only=None):
        return self.chart(vid, "card", x, y, w, h, {"Values": [meas(measure)]}, title,
                          {"labels": [{"properties": {"color": color(INK), "fontSize": lit(28)}}],
                           "categoryLabels": [{"properties": {"show": lit(False)}}]}, only=only)

    def no_filter(self, source, target):
        self.interactions.append({"source": source, "target": target, "type": "NoFilter"})

    def write(self):
        d = PAGES / self.pid
        if d.exists():
            shutil.rmtree(d)
        (d / "visuals").mkdir(parents=True)
        page = {"$schema": PAGE_SCHEMA, "name": self.pid, "displayName": self.name,
                "displayOption": "FitToPage", "height": 1080, "width": 1920}
        if self.interactions:
            page["visualInteractions"] = self.interactions
        (d / "page.json").write_text(json.dumps(page, indent=2, ensure_ascii=False), encoding="utf-8")
        for v in self.visuals:
            vd = d / "visuals" / v["name"]
            vd.mkdir()
            (vd / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------- layout grid ----------
L, R, TOP, BOT, GAP = 32, 1888, 164, 1028, 24
W = R - L

def cols(n, x0=L, x1=R):
    w = (x1 - x0 - (n - 1) * GAP) / n
    return [(x0 + i * (w + GAP), w) for i in range(n)]

def kpi_row(p, items, y=TOP, h=116, x0=L, x1=R):
    for (x, w), (m, t) in zip(cols(len(items), x0, x1), items):
        p.card("kpi_" + "".join(ch for ch in m if ch.isalnum())[:30], x, y, w, h, m, t)
    return y + h + GAP

SRC_PUBLIC = ("Sources: Gambling.com Group Form 20-F FY2025 (SEC); Better Collective Annual Report 2025 and Q1-Q3 2025 releases; "
              "Catena Media Year-End Report 2025 - see SOURCES.md")
SRC_SIM = "Simulated data (seed 2026), fictional operators A-G, calibrated on public benchmarks - illustrative only"
SRC_AB = "Source: public landing-page A/B test dataset ab_data.csv (Kaggle, origin undocumented), 290,584 users after cleaning"

pages = []

# ======================= Overview =======================
p = Page("a0c1e2f3a4b5c6d7e8f9", "Overview")
p.text("title", 32, 20, 1500, 56, [[("US sports-betting affiliate analytics: a case study for PLAYERSBEST", 22, INK, True)]])
p.text("tag", 1540, 28, 348, 40, [[("OVERVIEW", 10, INK2, True)]])
p.text("conclusion", 32, 76, 1856, 72, [[(
    "Six questions a BI analyst at a lead-generation affiliate answers every week - deal economics, channel and page "
    "value, A/B testing, forecasting and data quality - worked end to end with SQL (DuckDB), Python and Power BI.",
    13, INK2, False)]])
heroes = [("37%", "of Gambling.com Group's performance-marketing revenue came from CPA deals in 2025, down from 58% in 2023",
           "PUBLIC · PAGE 1"),
          ("$8.07 vs $1.11", "12-month affiliate revenue per visit: bonus-code pages vs news pages", "SIMULATED · PAGE 2"),
          ("Month 8", "when casino revenue share overtakes a $400 CPA; for sportsbook it never does within 24 months",
           "SIMULATED · PAGE 3"),
          ("3 / 3", "injected anomalies caught by ratio rules within 3 days, with zero false alarms", "SIMULATED · PAGE 6")]
hh = 250
for i, ((x, w), (num, txt, tag)) in enumerate(zip(cols(4), heroes)):
    p.text(f"hero{i+1}", x, TOP, w, hh, [[(tag, 10, INK2, True)], [(num, 38, INK, True)], [(txt, 15, INK2, False)]],
           boxed=True)
y2 = TOP + hh + GAP
(x1, w1), (x2, w2) = cols(2)
BH = 430
p.text("questions", x1, y2, w1, BH, [
    [("Business questions", 22, INK, True)],
    [("", 10, INK, False)],
    [("1 · Market   ", 16, BLUE, True), ("How do listed affiliates make money, US vs Europe?", 16, INK, False)],
    [("2 · Channels   ", 16, BLUE, True), ("Which channels and pages bring NDCs, at what EPC and ROI?", 16, INK, False)],
    [("3 · Deals   ", 16, BLUE, True), ("CPA or revenue share: which is worth more, and when?", 16, INK, False)],
    [("4 · A/B test   ", 16, BLUE, True), ("Does the new landing page lift conversion?", 16, INK, False)],
    [("5 · Forecast   ", 16, BLUE, True), ("Traffic and NDCs for the 2026-27 NFL season", 16, INK, False)],
    [("6 · Data quality   ", 16, BLUE, True), ("Catch bot clicks, broken tracking and search shifts early", 16, INK, False)],
    [("", 10, INK, False)],
    [("Recommendation: ", 16, INK, True),
     ("negotiate CPA with sportsbooks and revenue share with casinos, push traffic to bonus-code and comparison pages, "
      "keep the old landing page, and monitor ratios daily.", 16, INK2, False)],
], boxed=True)
p.text("data", x2, y2, w2, BH, [
    [("Data & methods", 22, INK, True)],
    [("", 10, INK, False)],
    [("PUBLIC   ", 13, INK2, True), ("Gambling.com Group, Better Collective and Catena Media filings, each figure sourced.", 16, INK, False)],
    [("PUBLIC DATASET   ", 13, INK2, True), ("landing-page A/B test, 290,584 users.", 16, INK, False)],
    [("SIMULATED   ", 13, INK2, True), ("two NFL seasons of sessions, click-outs, NDCs, player NGR and paid spend for a US affiliate (9 states, fictional operators).", 16, INK, False)],
    [("", 10, INK, False)],
    [("SQL   ", 13, INK2, True), ("censoring-safe cohort curves, EPC by channel and page, daily KPIs (DuckDB).", 16, INK, False)],
    [("Python   ", 13, INK2, True), ("z-test, bootstrap, power and peeking simulation; calendar GLM forecast with back-test; robust anomaly rules.", 16, INK, False)],
    [("Power BI   ", 13, INK2, True), ("star schema, DAX measures, one question per page.", 16, INK, False)],
], boxed=True)
y3 = y2 + BH + GAP
p.text("howto", L, y3, W, BOT - y3, [
    [("How to read this report", 16, INK, True)],
    [("Titles  ", 13, INK2, True), ("state the conclusion.     ", 14, INK, False),
     ("Tags  ", 13, INK2, True), ("PUBLIC / PUBLIC DATASET / SIMULATED mark where the data comes from.     ", 14, INK, False),
     ("NDC  ", 13, INK2, True), ("new depositing customer.     ", 14, INK, False),
     ("EPC  ", 13, INK2, True), ("affiliate revenue per click-out to an operator.", 14, INK, False)],
], boxed=True)
p.footer("Data sources listed in SOURCES.md")
pages.append(p)

# ======================= Page 1 - Market (public) =======================
p = Page("b1d2e3f4a5b6c7d8e9f0", "1 · How affiliates make money")
p.header("Listed affiliates are moving from one-off CPA fees to recurring revenue share",
         "At Gambling.com Group, CPA fell from 58% to 37% of performance-marketing revenue in two years. Better Collective earns 55% "
         "of European revenue from revenue share but only 24% in North America, where it is converting CPA deals (North America "
         "CPA revenue roughly halved in 2025). Revenue per NDC rises as NDC volumes fall. "
         "Next frontier: Better Collective names prediction markets as a 2026 tailwind.",
         "PUBLIC DATA")
y = kpi_row(p, [("GAMB Revenue 2025 ($m)", "Gambling.com Group revenue 2025"),
                ("GAMB North America Share 2025", "North America share of its revenue, 2025"),
                ("GAMB CPA Share 2025", "CPA share of its performance marketing, 2025"),
                ("BC NA Revenue Share 2025", "Better Collective: revenue share in North America revenue, 2025")])
(xa, wa), (xb, wb) = cols(2)
h = (BOT - y - GAP) / 2
PF, PK = "Public Figures", "Public KPIs"
p.chart("gambMix", "columnChart", xa, y, wa, h,
        {"Category": [C(PF, "period")], "Y": [meas("Public Figure Value")], "Series": [C(PF, "dimension")]},
        "Gambling.com Group: performance-marketing revenue by deal type, % (stacked)",
        {**LEGEND_TOP, "labels": [{"properties": {"show": lit(True)}}]},
        labels={"_Measures.Public Figure Value": "% of performance marketing"},
        only=[(PF, "metric", ["perf_marketing_mix"], False)])
p.chart("gambMarket", "columnChart", xb, y, wb, h,
        {"Category": [C(PF, "period")], "Y": [meas("Public Figure Value")], "Series": [C(PF, "dimension")]},
        "Gambling.com Group: revenue by market, USD thousands (stacked)", LEGEND_TOP,
        labels={"_Measures.Public Figure Value": "Revenue (USD k)"},
        only=[(PF, "metric", ["revenue_by_market"], False), (PF, "company", ["Gambling.com Group"], False)])
y += h + GAP
p.chart("bcRegion", "clusteredBarChart", xa, y, wa, BOT - y,
        {"Category": [C(PK, "region")], "Y": [meas("Public KPI Pct")], "Series": [C(PK, "year")]},
        "Better Collective: revenue share as % of revenue, by region",
        {**LEGEND_TOP, "labels": [{"properties": {"show": lit(True)}}]},
        labels={"_Measures.Public KPI Pct": "Revenue share % of revenue"},
        only=[(PK, "kpi", ["revshare_share"], False)])
p.chart("revPerNdc", "clusteredColumnChart", xb, y, wb, BOT - y,
        {"Category": [C(PK, "company")], "Y": [meas("Public KPI Value")], "Series": [C(PK, "year")]},
        "Revenue per NDC, EUR (total revenue / NDCs)",
        {**LEGEND_TOP, "labels": [{"properties": {"show": lit(True)}}]},
        labels={"_Measures.Public KPI Value": "EUR per NDC"},
        only=[(PK, "kpi", ["revenue_per_ndc_eur"], False)])
p.footer(SRC_PUBLIC)
pages.append(p)

# ======================= Page 2 - Channels & pages =======================
p = Page("c2e3f4a5b6c7d8e9f0a1", "2 · Channels & pages")
p.header("Bonus-code pages earn 7x more per visit than news pages; paid search barely covers its cost",
         "12-month affiliate revenue of NDCs acquired Sep 2024 - Aug 2025, valued under each operator's current deal. Once a visitor "
         "clicks out, pages convert alike (EPC about $18): the click-out rate is what separates them. Paid search returns +12% on "
         "spend over 12 months, social +104%.",
         "SIMULATED DATA")
(sx1, sw1), (sx2, sw2) = cols(2, L, L + 760)
p.slicer("slicer_Vertical", sx1, TOP, sw1, 64, C("Vertical", "vertical"), "Vertical")
p.slicer("slicer_State", sx2, TOP, sw2, 64, C("State", "state"), "State")
y = kpi_row(p, [("Window Sessions", "Sessions"), ("Window Clickout Rate", "Click-out rate"),
                ("Window NDCs", "NDCs"), ("EPC", "EPC (12-month revenue / click-out)"),
                ("Revenue 12m", "12-month revenue")], y=TOP + 64 + GAP, h=104)
(xa, wa), (xb, wb) = cols(2)
h = 300
rps, epc = meas("Revenue per Session"), meas("EPC")
p.chart("revPerSession", "clusteredBarChart", xa, y, wa, h,
        {"Category": [C("Page Type", "page_type")], "Y": [rps]},
        "Revenue per session by page type, $ (12-month value)",
        {"dataPoint": [{"properties": {"fill": color(BLUE)}}], "labels": [{"properties": {"show": lit(True)}}], **NO_LEGEND},
        sort=(rps, "Descending"))
p.chart("epcChannel", "clusteredBarChart", xb, y, wb, h,
        {"Category": [C("Channel", "channel")], "Y": [epc]},
        "EPC by channel, $ per click-out",
        {"dataPoint": [{"properties": {"fill": color(BLUE)}}], "labels": [{"properties": {"show": lit(True)}}], **NO_LEGEND},
        sort=(epc, "Descending"))
y += h + GAP
tbl = [C("Channel", "channel")] + Ms("Window Sessions", "Window Clickouts", "Window NDCs", "Window NDC per Clickout",
                                     "EPC", "Revenue per NDC", "Window Spend", "ROI")
p.chart("channelTable", "tableEx", xa, y, wa, BOT - y, {"Values": tbl},
        "Channel scorecard, Sep 2024 - Aug 2025 cohorts (ROI only for paid channels)",
        table_style([bg_rule(meas("ROI"), RED_TINT, BLUE_TINT, NEUTRAL, 0.5)], font=11),
        labels={"Channel.channel": "Channel", "_Measures.Window Sessions": "Sessions", "_Measures.Window Clickouts": "Click-outs",
                "_Measures.Window NDCs": "NDCs", "_Measures.Window NDC per Clickout": "NDC / click-out",
                "_Measures.Revenue per NDC": "Revenue / NDC", "_Measures.Window Spend": "Paid spend"})
p.chart("ndcMonthly", "columnChart", xb, y, wb, BOT - y,
        {"Category": [C("Date", "Month")], "Y": [meas("NDCs Reported")], "Series": [C("Channel", "channel")]},
        "NDCs per month by channel (all cohorts, stacked): NFL season peaks, summer trough", LEGEND_TOP)
p.footer(SRC_SIM)
pages.append(p)

# ======================= Page 3 - Deals =======================
p = Page("d3f4a5b6c7d8e9f0a1b2", "3 · CPA or revenue share")
p.header("Take CPA for sportsbook, revenue share for casino",
         "Cumulative revenue-share value per NDC vs the operator's CPA offer, censoring-safe (a month only counts cohorts that "
         "could reach it). Sportsbook players churn fast and have losing months: revenue share never reaches the CPA within "
         "24 months. Casino revenue share overtakes CPA by month 6-13 and is worth 1.1-2x the CPA after 24 months, discounted at 10%/year.",
         "SIMULATED DATA")
(xa, wa), (xb, wb) = cols(2)
h = 470
rv = meas("Revenue Share vs CPA")
p.chart("allOperators", "lineChart", xa, TOP, wa, h,
        {"Category": [C("Deal Curves", "month_n")], "Y": [rv], "Series": [C("Deal Curves", "operator")]},
        "Revenue-share value as % of the CPA offer, by month since first deposit (dashed = break-even)",
        {**LEGEND_TOP, "y1AxisReferenceLine": [ref_line(1, "CPA = 100%")]},
        labels={"Deal Curves.month_n": "Month since first deposit"})
sw = 220
p.slicer("slicerOperator", xb, TOP, sw, h, C("Operator", "operator"), "Pick one operator", dropdown=False, single=True)
cum, disc = meas("Cum Revenue Share per NDC"), meas("Cum Revenue Share Discounted")
p.chart("oneOperator", "lineChart", xb + sw + GAP, TOP, R - (xb + sw + GAP), h,
        {"Category": [C("Deal Curves", "month_n")], "Y": [cum, disc]},
        "Selected operator: cumulative revenue share per NDC, $ (dashed = CPA offer)",
        {**LEGEND_TOP, "dataPoint": [series_color(cum, INK), series_color(disc, MUTED)],
         "y1AxisReferenceLine": [ref_line(meas("CPA Offer"), "CPA offer")]},
        labels={qref(cum): "Revenue share", qref(disc): "Revenue share, discounted 10%/yr",
                "Deal Curves.month_n": "Month since first deposit"})
for target in ("allOperators", "dealTable"):
    p.no_filter("slicerOperator", target)
y = TOP + h + GAP
DS = "Deal Summary"
ds_cols = ["operator", "vertical", "current_deal", "cpa_offer_usd", "revshare_offer_pct", "breakeven_month",
           "breakeven_month_discounted", "breakeven_p5", "breakeven_p95", "revshare_24m_disc_usd", "ndcs_observed_m24", "better_deal"]
p.chart("dealTable", "tableEx", L, y, W, BOT - y, {"Values": [C(DS, c) for c in ds_cols]},
        "Deal scorecard (empty breakeven = revenue share never reaches the CPA within 24 months; 90% bootstrap interval)",
        table_style(font=11),
        labels={f"{DS}.operator": "Operator", f"{DS}.vertical": "Vertical", f"{DS}.current_deal": "Current deal",
                f"{DS}.cpa_offer_usd": "CPA offer", f"{DS}.revshare_offer_pct": "Rev. share offer",
                f"{DS}.breakeven_month": "Breakeven month", f"{DS}.breakeven_month_discounted": "Breakeven (discounted)",
                f"{DS}.breakeven_p5": "Breakeven P5", f"{DS}.breakeven_p95": "Breakeven P95",
                f"{DS}.revshare_24m_disc_usd": "Rev. share 24m (disc.)", f"{DS}.ndcs_observed_m24": "NDCs at month 24",
                f"{DS}.better_deal": "Better deal"})
p.footer(SRC_SIM)
pages.append(p)

# ======================= Page 4 - A/B test =======================
p = Page("e4a5b6c7d8e9f0a1b2c3", "4 · Landing-page A/B test")
p.header("Keep the old landing page: the new one does not lift conversion (p = 0.19)",
         "290,584 users randomised over 23 days. The new page converts 11.88% vs 12.04% (-0.16 pts, 95% CI -0.39 to +0.08). "
         "The test could detect +/-0.34 pts, so a lift of that size would have shown. Stopping at the first daily p < 0.05 "
         "would have raised false positives from 5% to 26%: fix the sample size before starting.",
         "PUBLIC DATASET")
y = kpi_row(p, [("AB Conversion Control", "Conversion, old page"), ("AB Conversion New Page", "Conversion, new page"),
                ("AB Difference (pts)", "Difference (new - old)"), ("AB p-value", "p-value (two-sided z-test)")])
(xa, wa), (xb, wb) = cols(2)
h = 300
cc, ct = meas("AB Cum Conversion Control"), meas("AB Cum Conversion New Page")
p.chart("cumConv", "lineChart", xa, y, wa, h,
        {"Category": [C("AB Daily", "day")], "Y": [cc, ct]},
        "Cumulative conversion by day",
        {**LEGEND_TOP, "dataPoint": [series_color(cc, BLUE), series_color(ct, GREY)]},
        labels={qref(cc): "Old page (control)", qref(ct): "New page", "AB Daily.day": "Day"})
z = meas("AB Cumulative z")
p.chart("cumZ", "lineChart", xb, y, wb, h,
        {"Category": [C("AB Daily", "day")], "Y": [z]},
        "Cumulative z-score by day (dashed = +/-1.96: crossing it on one day is not a result)",
        {**NO_LEGEND, "dataPoint": [series_color(z, INK)],
         "y1AxisReferenceLine": [ref_line(1.96, "+1.96", MUTED, "1"), ref_line(-1.96, "-1.96", MUTED, "2")],
         "valueAxis": [{"properties": {"start": lit(-3), "end": lit(3)}}]},
        labels={qref(z): "z", "AB Daily.day": "Day"})
y += h + GAP
p.chart("abStats", "tableEx", L, y, W, BOT - y, {"Values": [C("AB Stats", "statistic"), C("AB Stats", "value")]},
        "Test statistics", table_style(font=12), labels={"AB Stats.statistic": "Statistic", "AB Stats.value": "Value"},
        sort=(C("AB Stats", "statistic"), "Ascending"))
p.footer(SRC_AB)
pages.append(p)

# ======================= Page 5 - Forecast =======================
p = Page("f5b6c7d8e9f0a1b2c3d4", "5 · Forecast 2026-27")
p.header("NFL 2026-27: about +2% NDCs, because the search update cancels a year of growth",
         "Calendar model (NFL regular season, playoffs, Super Bowl week and day, March Madness, weekdays) back-tested on the whole "
         "2025-26 season: weekly error 0.3% on sessions, season error under 1.5% on NDCs. The 2026-27 forecast adds Missouri "
         "(+7% sportsbook sessions) and the March 2026 search update (-14% sessions) as known level changes. Weekly totals.",
         "SIMULATED DATA")
(sx1, sw1), (sx2, sw2) = cols(2, L, L + 560)
p.slicer("slicer_FcVertical", sx1, TOP, sw1, 64, C("Vertical", "vertical"), "Vertical", single=True, default="Sportsbook")
p.slicer("slicer_FcMetric", sx2, TOP, sw2, 64, C("Forecast", "metric"), "Metric", single=True, default="Sessions")
y = TOP + 64 + GAP
h = 320
act, fc, lo, hi = Ms("Actual", "Forecast 2026-27", "Forecast Low 80", "Forecast High 80")
p.chart("forecastChart", "lineChart", L, y, W, h,
        {"Category": [C("Date", "Week")], "Y": [act, fc, lo, hi]},
        "Weekly actuals and forecast for the 2026-27 season (dotted = 80% interval, indicative when summed to weeks)",
        {**LEGEND_TOP, "dataPoint": [series_color(act, INK), series_color(fc, BLUE), series_color(lo, SEQ["250"]),
                                     series_color(hi, SEQ["250"])],
         "lineStyles": [{"properties": {"lineStyle": lit("dotted")}, "selector": {"metadata": qref(lo)}},
                        {"properties": {"lineStyle": lit("dotted")}, "selector": {"metadata": qref(hi)}}]},
        labels={qref(act): "Actual", qref(fc): "Forecast", qref(lo): "Low (80%)", qref(hi): "High (80%)", "Date.Week": "Week"})
y += h + GAP
(xa, wa), (xb, wb) = cols(2)
ba, bf = Ms("Back-test Actual", "Back-test Forecast")
p.chart("backtestChart", "lineChart", xa, y, wa, BOT - y,
        {"Category": [C("Date", "Week")], "Y": [ba, bf]},
        "Back-test: 2025-26 season forecast from 2024-25 only (existing states), weekly",
        {**LEGEND_TOP, "dataPoint": [series_color(ba, INK), series_color(bf, BLUE)]},
        labels={qref(ba): "Actual", qref(bf): "Forecast", "Date.Week": "Week"})
bh = (BOT - y - GAP) / 2
BT, ST = "Backtest", "Season Totals"
p.chart("backtestTable", "tableEx", xb, y, wb, bh,
        {"Values": [C(BT, c) for c in ["vertical", "metric", "method", "mape_weekly", "season_error", "coverage_80"]]},
        "Back-test accuracy (NDCs = sessions x conversion beats a direct NDC model)", table_style(font=11),
        labels={f"{BT}.vertical": "Vertical", f"{BT}.metric": "Metric", f"{BT}.method": "Method",
                f"{BT}.mape_weekly": "Weekly error (MAPE)", f"{BT}.season_error": "Season total error",
                f"{BT}.coverage_80": "In 80% interval"})
p.chart("seasonTable", "tableEx", xb, y + bh + GAP, wb, bh,
        {"Values": [C(ST, c) for c in ["vertical", "metric", "actual_2025_26", "forecast_2026_27", "growth"]]},
        "Season totals, September to February", table_style(font=11),
        labels={f"{ST}.vertical": "Vertical", f"{ST}.metric": "Metric", f"{ST}.actual_2025_26": "2025-26 actual",
                f"{ST}.forecast_2026_27": "2026-27 forecast", f"{ST}.growth": "Growth"})
for s in ("slicer_FcVertical", "slicer_FcMetric"):
    for t in ("backtestTable", "seasonTable"):
        p.no_filter(s, t)
p.footer(SRC_SIM)
pages.append(p)

# ======================= Page 6 - Anomalies =======================
p = Page("a6c7d8e9f0a1b2c3d4e5", "6 · Data quality & anomalies")
p.header("Watch ratios, not volumes: three anomalies caught within 3 days, zero false alarms",
         "The rules never saw the answer key. 1) Bots: more click-outs and fewer registrations per click-out (paid search, Illinois). "
         "2) Broken postback: tracked vs operator-reported NDCs (Operator D). 3) Search update: SEO share of sessions vs its 91-day "
         "baseline. A plain volume rule raised 58 alarms on the Super Bowl and March Madness instead.",
         "SIMULATED DATA")
AF = "Anomaly Flags"
mv, mb, fv = Ms("Metric Value", "Metric Baseline", "Flagged Value")
h = 470
specs = [("rule1", "1 Click quality", ["Paid search"], "1 · Registrations per click-out, paid search (red = flagged)", [mv, fv]),
         ("rule2", "2 Tracking", ["Operator D"], "2 · Tracked / reported NDCs, Operator D (red = flagged)", [mv, fv]),
         ("rule3", "3 Level shift", ["SEO"], "3 · SEO share of sessions: 7-day median vs 91-day baseline (red = flagged)", [mv, mb, fv])]
for (x, w), (vid, rule, seg, title, ys) in zip(cols(3), specs):
    p.chart(vid, "lineChart", x, TOP, w, h, {"Category": [C(AF, "date")], "Y": ys}, title,
            {**LEGEND_TOP, "dataPoint": [series_color(mv, INK), series_color(mb, MUTED), series_color(fv, RED)],
             "lineStyles": [{"properties": {"showMarker": lit(True), "markerSize": lit(5)}, "selector": {"metadata": qref(fv)}}]},
            labels={qref(mv): "Metric", qref(mb): "Baseline", qref(fv): "Flagged", f"{AF}.date": "Date"},
            only=[(AF, "rule", [rule], False), (AF, "segment", seg, False)])
y = TOP + h + GAP
(xa, wa), (xb, wb) = cols(2)
AS = "Anomaly Score"
p.chart("scoreTable", "tableEx", xa, y, wa, BOT - y,
        {"Values": [C(AS, c) for c in ["anomaly", "start", "first_flag", "lag_days", "flagged_segments", "false_positive_days"]]},
        "Detection score against the injected anomalies", table_style(font=12),
        labels={f"{AS}.anomaly": "Anomaly", f"{AS}.start": "Started", f"{AS}.first_flag": "First flag",
                f"{AS}.lag_days": "Lag (days)", f"{AS}.flagged_segments": "Segment", f"{AS}.false_positive_days": "False alarm days"})
p.text("actions", xb, y, wb, BOT - y, [
    [("What to do when a rule fires", 16, INK, True)],
    [("", 8, INK, False)],
    [("Bot clicks   ", 14, BLUE, True), ("exclude the traffic, block the source and claim back the paid clicks "
                                         "(about $35k bought for bots in 3 days).", 14, INK, False)],
    [("Broken tracking   ", 14, BLUE, True), ("reconcile with the operator's report and fix the postback before month-end "
                                              "invoicing; never read a tracking gap as a business drop.", 14, INK, False)],
    [("Search update   ", 14, BLUE, True), ("audit the pages that lost rankings, refresh content, and shift budget to "
                                            "email and paid until SEO recovers.", 14, INK, False)],
], boxed=True)
p.footer(SRC_SIM)
pages.append(p)

# ---------- write ----------
PAGES.mkdir(parents=True, exist_ok=True)
keep = {pg.pid for pg in pages}
for d in PAGES.iterdir():
    if d.is_dir() and d.name not in keep:
        shutil.rmtree(d)
for pg in pages:
    pg.write()
meta = {"$schema": PAGES_SCHEMA, "pageOrder": [pg.pid for pg in pages], "activePageName": pages[0].pid}
(PAGES / "pages.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("pages:", [(pg.name.encode("ascii", "replace").decode(), len(pg.visuals)) for pg in pages])
