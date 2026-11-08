"""Generate the Power BI semantic model (TMDL) for powerbi/PlayersBestCaseStudy.SemanticModel.

Usage:  python src/build_semantic_model.py
Close Power BI Desktop first: the model definition is rewritten from this script.
Tables load CSVs from the DataFolder parameter (default: this repository's data folder).
"""
from pathlib import Path
import json
import uuid

ROOT = Path(__file__).resolve().parents[1]
NAME = "PlayersBestCaseStudy"
SM = ROOT / "powerbi" / f"{NAME}.SemanticModel"
DEF = SM / "definition"
DATA_FOLDER = str(ROOT / "data") + "\\"
NS = uuid.UUID("6f1d3c2a-9b7e-4c55-8a10-2d4e5f607182")    # stable lineage tags between runs


def tag(*parts):
    return str(uuid.uuid5(NS, "|".join(parts)))


def q(name):
    """Quote a TMDL object name when needed."""
    return f"'{name}'" if any(ch in name for ch in " -.()&/") or name[0].isdigit() else name


# column spec: (name, kind, format)   kind: text | int | num | date | bool
TYPES = {"text": ("string", "type text"), "int": ("int64", "Int64.Type"), "num": ("double", "type number"),
         "date": ("dateTime", "type date"), "bool": ("boolean", "type logical")}

TABLES = {
    "Public Figures": ("public/affiliates_public.csv", [
        ("company", "text", None), ("period", "text", None), ("metric", "text", None), ("dimension", "text", None),
        ("value", "num", "#,0.0"), ("unit", "text", None), ("source_id", "text", None)]),
    "Public KPIs": ("output/page1_public_kpis.csv", [
        ("year", "text", None), ("kpi", "text", None), ("value", "num", "#,0.000"), ("company", "text", None),
        ("region", "text", None)]),
    "Traffic": ("simulated/sim_traffic_daily.csv", [
        ("date", "date", None), ("channel", "text", None), ("state", "text", None), ("page_type", "text", None),
        ("vertical", "text", None), ("sessions", "int", "#,0"), ("clickouts", "int", "#,0")]),
    "Operator Daily": ("simulated/sim_operator_daily.csv", [
        ("date", "date", None), ("channel", "text", None), ("state", "text", None), ("vertical", "text", None),
        ("operator", "text", None), ("clickouts", "int", "#,0"), ("registrations", "int", "#,0"),
        ("ndcs_tracked", "int", "#,0")]),
    "NDCs": ("output/05_ndcs_valued.csv", [
        ("ndc_id", "int", "0"), ("ftd_date", "date", None), ("channel", "text", None), ("state", "text", None),
        ("page_type", "text", None), ("vertical", "text", None), ("operator", "text", None),
        ("revenue_12m_usd", "num", "$#,0.00")]),
    "Marketing Cost": ("simulated/sim_marketing_cost_daily.csv", [
        ("date", "date", None), ("channel", "text", None), ("state", "text", None), ("vertical", "text", None),
        ("paid_clicks", "int", "#,0"), ("spend_usd", "num", "$#,0")]),
    "Operator": ("simulated/sim_operator_deals.csv", [
        ("operator", "text", None), ("vertical", "text", None), ("current_deal", "text", None),
        ("cpa_offer_usd", "num", "$#,0"), ("revshare_offer_pct", "num", "0%"),
        ("hybrid_cpa_usd", "num", "$#,0"), ("hybrid_revshare_pct", "num", "0%")]),
    "Deal Curves": ("output/page3_deal_curves.csv", [
        ("operator", "text", None), ("vertical", "text", None), ("current_deal", "text", None),
        ("month_n", "int", "0"), ("ndcs_observed", "int", "#,0"), ("ngr_per_ndc_usd", "num", "$#,0.00"),
        ("cum_ngr_per_ndc_usd", "num", "$#,0"), ("cpa_offer_usd", "num", "$#,0"),
        ("revshare_offer_pct", "num", "0%"), ("cum_revshare_per_ndc_usd", "num", "$#,0"),
        ("revshare_ahead", "bool", None), ("disc_factor", "num", "0.000"),
        ("disc_revshare_per_ndc_usd", "num", "$#,0")]),
    "Deal Summary": ("output/page3_deal_summary.csv", [
        ("operator", "text", None), ("vertical", "text", None), ("current_deal", "text", None),
        ("cpa_offer_usd", "num", "$#,0"), ("revshare_offer_pct", "num", "0%"), ("ndcs", "int", "#,0"),
        ("breakeven_month", "num", "0"), ("breakeven_month_discounted", "num", "0"),
        ("breakeven_p5", "num", "0"), ("breakeven_p95", "num", "0"), ("share_of_boot_never", "num", "0%"),
        ("revshare_24m_usd", "num", "$#,0"), ("revshare_24m_disc_usd", "num", "$#,0"),
        ("ndcs_observed_m24", "int", "#,0"), ("better_deal", "text", None)]),
    "AB Summary": ("output/page4_ab_summary.csv", [
        ("users_control", "int", "#,0"), ("users_treatment", "int", "#,0"), ("conv_control", "num", "0.00%"),
        ("conv_treatment", "num", "0.00%"), ("diff_pts", "num", "+0.00;-0.00"), ("rel_lift", "num", "0.0%"),
        ("z", "num", "0.00"), ("p_two_sided", "num", "0.000"), ("p_one_sided_new_better", "num", "0.000"),
        ("ci95_lo_pts", "num", "0.00"), ("ci95_hi_pts", "num", "0.00"), ("boot_share_new_better", "num", "0.0%"),
        ("mde_pts_at_80pct_power", "num", "0.00"), ("users_per_group_for_0_5pt_lift", "int", "#,0"),
        ("days", "int", "0"), ("false_positive_single_look", "num", "0.0%"),
        ("false_positive_daily_peeking", "num", "0.0%")]),
    "AB Stats": ("output/page4_ab_stats.csv", [
        ("sort_order", "int", "0"), ("statistic", "text", None), ("value", "text", None)]),
    "AB Daily": ("output/page4_ab_daily.csv", [
        ("day", "date", None), ("cum_conv_control", "num", "0.00%"), ("cum_conv_treatment", "num", "0.00%"),
        ("cum_users", "int", "#,0"), ("cum_z", "num", "0.00")]),
    "Forecast": ("output/page5_forecast.csv", [
        ("date", "date", None), ("forecast", "num", "#,0"), ("lo80", "num", "#,0"), ("hi80", "num", "#,0"),
        ("actual", "num", "#,0"), ("vertical", "text", None), ("metric", "text", None), ("phase", "text", None)]),
    "Backtest": ("output/page5_backtest.csv", [
        ("vertical", "text", None), ("metric", "text", None), ("method", "text", None),
        ("mape_daily", "num", "0.0%"), ("mape_weekly", "num", "0.0%"), ("season_error", "num", "+0.0%;-0.0%"),
        ("coverage_80", "num", "0%")]),
    "Season Totals": ("output/page5_season_totals.csv", [
        ("vertical", "text", None), ("metric", "text", None), ("forecast_2026_27", "num", "#,0"),
        ("actual_2025_26", "num", "#,0"), ("growth", "num", "+0.0%;-0.0%")]),
    "Anomaly Flags": ("output/page5_anomaly_flags.csv", [
        ("date", "date", None), ("rule", "text", None), ("segment", "text", None), ("value", "num", "0.000"),
        ("baseline", "num", "0.000"), ("z", "num", "0.0"), ("flagged", "bool", None),
        ("in_true_window", "bool", None)]),
    "Anomaly Score": ("output/page5_anomaly_score.csv", [
        ("anomaly", "text", None), ("start", "date", None), ("detected", "bool", None), ("first_flag", "date", None),
        ("lag_days", "num", "0"), ("flagged_segments", "text", None), ("false_positive_days", "int", "0")]),
}

# small dimension tables built in M
DIMENSIONS = {
    "Channel": ("channel", ["SEO", "Paid search", "Social", "Email", "Direct"]),
    "State": ("state", ["NY", "IL", "PA", "OH", "NJ", "MI", "AZ", "CO", "MO"]),
    "Page Type": ("page_type", ["Bonus code page", "Comparison ranking", "Operator review", "News & guides"]),
    "Vertical": ("vertical", ["Sportsbook", "Casino"]),
}

RELATIONSHIPS = [  # (from table, from column, to table, to column)
    *[(t, c, "Date", "Date") for t, c in [("Traffic", "date"), ("Operator Daily", "date"), ("NDCs", "ftd_date"),
                                          ("Marketing Cost", "date"), ("Forecast", "date")]],
    *[(t, "channel", "Channel", "channel") for t in ["Traffic", "Operator Daily", "NDCs", "Marketing Cost"]],
    *[(t, "state", "State", "state") for t in ["Traffic", "Operator Daily", "NDCs", "Marketing Cost"]],
    *[(t, "vertical", "Vertical", "vertical") for t in ["Traffic", "Operator Daily", "NDCs", "Marketing Cost", "Forecast"]],
    *[(t, "page_type", "Page Type", "page_type") for t in ["Traffic", "NDCs"]],
    *[(t, "operator", "Operator", "operator") for t in ["Operator Daily", "NDCs", "Deal Curves", "Deal Summary"]],
]

W0, W1 = "DATE ( 2024, 9, 1 )", "DATE ( 2025, 8, 31 )"       # 12-month valuation window (cohorts)
WINDOW = f"DATESBETWEEN ( 'Date'[Date], {W0}, {W1} )"
MEASURES = [  # (folder, name, DAX, format)
    ("Funnel", "Sessions", "SUM ( Traffic[sessions] )", "#,0"),
    ("Funnel", "Clickouts", "SUM ( Traffic[clickouts] )", "#,0"),
    ("Funnel", "Clickout Rate", "DIVIDE ( [Clickouts], [Sessions] )", "0.0%"),
    ("Funnel", "Registrations", "SUM ( 'Operator Daily'[registrations] )", "#,0"),
    ("Funnel", "Registration Rate", "DIVIDE ( [Registrations], SUM ( 'Operator Daily'[clickouts] ) )", "0.0%"),
    ("Funnel", "NDCs Reported", "COUNTROWS ( NDCs )", "#,0"),
    ("Funnel", "NDCs Tracked", "SUM ( 'Operator Daily'[ndcs_tracked] )", "#,0"),
    ("Funnel", "NDC per Clickout", "DIVIDE ( [NDCs Reported], [Clickouts] )", "0.00%"),
    ("Funnel", "Paid Spend", "SUM ( 'Marketing Cost'[spend_usd] )", "$#,0"),
    ("Value (12m cohorts)", "Revenue 12m", "SUM ( NDCs[revenue_12m_usd] )", "$#,0"),
    ("Value (12m cohorts)", "Window Sessions", f"CALCULATE ( [Sessions], {WINDOW} )", "#,0"),
    ("Value (12m cohorts)", "Window Clickouts", f"CALCULATE ( [Clickouts], {WINDOW} )", "#,0"),
    ("Value (12m cohorts)", "Window NDCs", f"CALCULATE ( [NDCs Reported], {WINDOW} )", "#,0"),
    ("Value (12m cohorts)", "Window Spend", f"CALCULATE ( [Paid Spend], {WINDOW} )", "$#,0"),
    ("Value (12m cohorts)", "Window Clickout Rate", "DIVIDE ( [Window Clickouts], [Window Sessions] )", "0.0%"),
    ("Value (12m cohorts)", "Window NDC per Clickout", "DIVIDE ( [Window NDCs], [Window Clickouts] )", "0.00%"),
    ("Value (12m cohorts)", "EPC", "DIVIDE ( [Revenue 12m], [Window Clickouts] )", "$#,0.00"),
    ("Value (12m cohorts)", "Revenue per NDC", "DIVIDE ( [Revenue 12m], [Window NDCs] )", "$#,0"),
    ("Value (12m cohorts)", "Revenue per Session", "DIVIDE ( [Revenue 12m], [Window Sessions] )", "$#,0.00"),
    ("Value (12m cohorts)", "ROI", "IF ( [Window Spend] > 0, DIVIDE ( [Revenue 12m] - [Window Spend], [Window Spend] ) )", "0%"),
    ("Public", "GAMB CPA Share 2025",
     "DIVIDE ( CALCULATE ( SUM ( 'Public Figures'[value] ), 'Public Figures'[metric] = \"perf_marketing_mix\", "
     "'Public Figures'[dimension] = \"CPA\", 'Public Figures'[period] = \"FY2025\" ), 100 )", "0%"),
    ("Public", "GAMB Revenue 2025 ($m)",
     "DIVIDE ( CALCULATE ( SUM ( 'Public Figures'[value] ), 'Public Figures'[company] = \"Gambling.com Group\", "
     "'Public Figures'[metric] = \"revenue\", 'Public Figures'[period] = \"FY2025\" ), 1000 )", "$#,0.0 \\m"),
    ("Public", "GAMB North America Share 2025",
     "CALCULATE ( SUM ( 'Public KPIs'[value] ), 'Public KPIs'[kpi] = \"north_america_share\", 'Public KPIs'[year] = \"FY2025\" )", "0%"),
    ("Public", "BC NA Revenue Share 2025",
     "CALCULATE ( SUM ( 'Public KPIs'[value] ), 'Public KPIs'[kpi] = \"revshare_share\", 'Public KPIs'[year] = \"FY2025\", "
     "'Public KPIs'[region] = \"North America\" )", "0%"),
    ("Public", "Public KPI Value", "SUM ( 'Public KPIs'[value] )", "#,0"),
    ("Public", "Public KPI Pct", "SUM ( 'Public KPIs'[value] )", "0%"),
    ("Public", "Public Figure Value", "SUM ( 'Public Figures'[value] )", "#,0"),
    ("Deals", "Cum Revenue Share per NDC", "AVERAGE ( 'Deal Curves'[cum_revshare_per_ndc_usd] )", "$#,0"),
    ("Deals", "Cum Revenue Share Discounted", "AVERAGE ( 'Deal Curves'[disc_revshare_per_ndc_usd] )", "$#,0"),
    ("Deals", "CPA Offer", "AVERAGE ( 'Deal Curves'[cpa_offer_usd] )", "$#,0"),
    ("Deals", "Revenue Share vs CPA",
     "DIVIDE ( SUM ( 'Deal Curves'[cum_revshare_per_ndc_usd] ), SUM ( 'Deal Curves'[cpa_offer_usd] ) )", "0%"),
    ("AB test", "AB Conversion Control", "MAX ( 'AB Summary'[conv_control] )", "0.00%"),
    ("AB test", "AB Conversion New Page", "MAX ( 'AB Summary'[conv_treatment] )", "0.00%"),
    ("AB test", "AB Difference (pts)", "MAX ( 'AB Summary'[diff_pts] )", "+0.00 \\p\\t\\s;-0.00 \\p\\t\\s"),
    ("AB test", "AB p-value", "MAX ( 'AB Summary'[p_two_sided] )", "0.00"),
    ("AB test", "AB Cumulative z", "AVERAGE ( 'AB Daily'[cum_z] )", "0.00"),
    ("AB test", "AB Cum Conversion Control", "AVERAGE ( 'AB Daily'[cum_conv_control] )", "0.00%"),
    ("AB test", "AB Cum Conversion New Page", "AVERAGE ( 'AB Daily'[cum_conv_treatment] )", "0.00%"),
    ("Forecast", "Actual", "CALCULATE ( SUM ( Forecast[actual] ), Forecast[phase] = \"Actual\" )", "#,0"),
    ("Forecast", "Forecast 2026-27", "CALCULATE ( SUM ( Forecast[forecast] ), Forecast[phase] = \"Forecast 2026-27\" )", "#,0"),
    ("Forecast", "Forecast Low 80", "CALCULATE ( SUM ( Forecast[lo80] ), Forecast[phase] = \"Forecast 2026-27\" )", "#,0"),
    ("Forecast", "Forecast High 80", "CALCULATE ( SUM ( Forecast[hi80] ), Forecast[phase] = \"Forecast 2026-27\" )", "#,0"),
    ("Forecast", "Back-test Actual", "CALCULATE ( SUM ( Forecast[actual] ), Forecast[phase] = \"Back-test (existing states)\" )", "#,0"),
    ("Forecast", "Back-test Forecast", "CALCULATE ( SUM ( Forecast[forecast] ), Forecast[phase] = \"Back-test (existing states)\" )", "#,0"),
    ("Forecast", "Sportsbook NDC Growth 2026-27",
     "CALCULATE ( SUM ( 'Season Totals'[growth] ), 'Season Totals'[vertical] = \"Sportsbook\", 'Season Totals'[metric] = \"NDCs\" )",
     "+0.0%;-0.0%"),
    ("Forecast", "Sportsbook Session Error Back-test",
     "CALCULATE ( SUM ( Backtest[season_error] ), Backtest[vertical] = \"Sportsbook\", Backtest[metric] = \"Sessions\" )", "+0.0%;-0.0%"),
    ("Anomalies", "Metric Value", "AVERAGE ( 'Anomaly Flags'[value] )", "0.000"),
    ("Anomalies", "Metric Baseline", "AVERAGE ( 'Anomaly Flags'[baseline] )", "0.000"),
    ("Anomalies", "Flagged Value", "CALCULATE ( AVERAGE ( 'Anomaly Flags'[value] ), 'Anomaly Flags'[flagged] = TRUE () )", "0.000"),
    ("Anomalies", "Anomalies Detected", "COUNTROWS ( FILTER ( 'Anomaly Score', 'Anomaly Score'[detected] = TRUE () ) )", "0"),
    ("Anomalies", "False Alarm Days", "SUM ( 'Anomaly Score'[false_positive_days] )", "0"),
]


def m_csv(path, cols):
    types = ", ".join('{"%s", %s}' % (c, TYPES[k][1]) for c, k, _ in cols)
    win = path.replace("/", "\\")
    return "\n".join([
        "let",
        f'\tSource = Csv.Document(File.Contents(DataFolder & "{win}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "\tPromoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        '\tBlanks = Table.TransformColumns(Promoted, {}, each if _ = "" then null else _),',
        f'\tTyped = Table.TransformColumnTypes(Blanks, {{{types}}}, "en-US")',
        "in",
        "\tTyped"])


SORT_BY = {("AB Stats", "statistic"): "sort_order"}
HIDDEN = {("AB Stats", "sort_order")}


def column_block(table, name, kind, fmt, hidden=False, key=False, sort_by=None):
    sort_by = sort_by or SORT_BY.get((table, name))
    hidden = hidden or (table, name) in HIDDEN
    lines = [f"\tcolumn {q(name)}", f"\t\tdataType: {TYPES[kind][0]}"]
    if key:
        lines.append("\t\tisKey")
    if hidden:
        lines.append("\t\tisHidden")
    if fmt or kind == "date":
        lines.append(f"\t\tformatString: {fmt or 'dd mmm yyyy'}")
    lines += [f"\t\tlineageTag: {tag(table, name)}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {name}"]
    if sort_by:
        lines.append(f"\t\tsortByColumn: {sort_by}")
    if kind == "date":
        lines += ["", "\t\tannotation UnderlyingDateTimeDataType = Date"]
    return "\n".join(lines) + "\n"


def partition(table, source_m):
    body = "\n".join("\t\t\t\t" + line for line in source_m.splitlines())
    return f"\tpartition {q(table)} = m\n\t\tmode: import\n\t\tsource =\n{body}\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- files
tables_dir = DEF / "tables"
if tables_dir.exists():
    for f in tables_dir.glob("*.tmdl"):
        f.unlink()
order = []

for table, (path, cols) in TABLES.items():
    out = f"table {q(table)}\n\tlineageTag: {tag(table)}\n\n"
    out += "\n".join(column_block(table, c, k, f) for c, k, f in cols) + "\n"
    out += partition(table, m_csv(path, cols))
    write(tables_dir / f"{table}.tmdl", out)
    order.append(table)

for table, (colname, values) in DIMENSIONS.items():
    rows = ", ".join('{"%s"}' % v for v in values)
    out = f"table {q(table)}\n\tlineageTag: {tag(table)}\n\n"
    out += column_block(table, colname, "text", None) + "\n"
    out += f"\tpartition {q(table)} = m\n\t\tmode: import\n\t\tsource = #table(type table [{colname} = text], {{{rows}}})\n"
    write(tables_dir / f"{table}.tmdl", out)
    order.append(table)

date_m = "\n".join([
    "let",
    "\tDates = List.Dates(#date(2024, 9, 1), Duration.Days(#date(2027, 2, 28) - #date(2024, 9, 1)) + 1, #duration(1, 0, 0, 0)),",
    "\tT = Table.FromList(Dates, Splitter.SplitByNothing(), type table [Date = date]),",
    '\tWk = Table.AddColumn(T, "Week", each Date.StartOfWeek([Date], Day.Monday), type date),',
    '\tMo = Table.AddColumn(Wk, "Month", each Date.ToText([Date], "MMM yyyy", "en-US"), type text),',
    '\tMs = Table.AddColumn(Mo, "MonthStart", each Date.StartOfMonth([Date]), type date),',
    '\tSeason = Table.AddColumn(Ms, "NFL Season", each if Date.Month([Date]) >= 9 then Text.From(Date.Year([Date])) & "-" & Text.End(Text.From(Date.Year([Date]) + 1), 2) else if Date.Month([Date]) <= 2 then Text.From(Date.Year([Date]) - 1) & "-" & Text.End(Text.From(Date.Year([Date])), 2) else "Off-season " & Text.From(Date.Year([Date])), type text)',
    "in",
    "\tSeason"])
out = f"table Date\n\tlineageTag: {tag('Date')}\n\tdataCategory: Time\n\n"
out += column_block("Date", "Date", "date", None, key=True) + "\n"
out += column_block("Date", "Week", "date", None) + "\n"
out += column_block("Date", "Month", "text", None, sort_by="MonthStart") + "\n"
out += column_block("Date", "MonthStart", "date", "mmm yyyy", hidden=True) + "\n"
out += column_block("Date", "NFL Season", "text", None) + "\n"
out += partition("Date", date_m)
write(tables_dir / "Date.tmdl", out)
order.append("Date")

out = f"table _Measures\n\tlineageTag: {tag('_Measures')}\n\n"
for folder, name, dax, fmt in MEASURES:
    out += (f"\tmeasure {q(name)} = {dax}\n\t\tformatString: {fmt}\n\t\tdisplayFolder: {folder}\n"
            f"\t\tlineageTag: {tag('_Measures', name)}\n\n")
out += ("\tcolumn _\n\t\tdataType: string\n\t\tisHidden\n\t\tlineageTag: " + tag("_Measures", "_")
        + "\n\t\tsummarizeBy: none\n\t\tsourceColumn: _\n\n")
out += "\tpartition _Measures = m\n\t\tmode: import\n\t\tsource = #table(type table [_ = text], {})\n"
write(tables_dir / "_Measures.tmdl", out)
order.append("_Measures")

rel = ""
for i, (ft, fc, tt, tc) in enumerate(RELATIONSHIPS, 1):
    rel += f"relationship rel_{i:02d}\n\tfromColumn: {q(ft)}.{q(fc)}\n\ttoColumn: {q(tt)}.{q(tc)}\n\n"
write(DEF / "relationships.tmdl", rel)

write(DEF / "expressions.tmdl",
      f'expression DataFolder = "{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
      f"\tlineageTag: {tag('DataFolder')}\n\n\tannotation PBI_ResultType = Text\n\n")
write(DEF / "database.tmdl", "database\n\tcompatibilityLevel: 1606\n\n")
write(DEF / "model.tmdl", "\n".join([
    "model Model",
    "\tculture: en-US",
    "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
    "\tsourceQueryCulture: en-US",
    "\tdataAccessOptions",
    "\t\tlegacyRedirects",
    "\t\treturnErrorValuesAsNull",
    "",
    "annotation __PBI_TimeIntelligenceEnabled = 0",
    "",
    "annotation PBI_QueryOrder = " + json.dumps(order + ["DataFolder"]),
    "",
    *[f"ref table {q(t)}" for t in order],
    # Power BI Desktop adds a culture file on first open; keep referencing it once it exists
    *(["", "ref cultureInfo en-US"] if (DEF / "cultures" / "en-US.tmdl").exists() else []),
    ""]))
write(SM / "definition.pbism", json.dumps({"version": "4.2", "settings": {}}, indent=2))
write(SM / ".platform", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": NAME},
    "config": {"version": "2.0", "logicalId": tag("semantic-model")}}, indent=2))
print(f"{len(order)} tables, {len(MEASURES)} measures, {len(RELATIONSHIPS)} relationships -> {SM}")
