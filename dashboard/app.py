"""Streamlit entry point for the Campus Utility Intelligence dashboard."""

import streamlit as st

from campus_utility.config import get_config
from campus_utility.dashboard_data import (
    get_filter_options,
    load_emissions_assumptions,
    load_emissions,
    load_monthly_usage,
    load_peak_demand,
    load_peak_shift_summary,
    load_top_peak_shift_results,
    load_top_weather_baseline_candidates,
    load_weather_baseline_summary,
    load_reconciliation,
    table_exists,
)


st.set_page_config(page_title="Campus Utility Intelligence", layout="wide")
st.title("Campus Utility Intelligence")

config = get_config()

if not config.db_path.exists():
    st.error("DuckDB database not found. Run the pipeline through `make emissions` and `make reconcile`.")
    st.stop()

campuses, sources = get_filter_options(config.db_path)
if not campuses or not sources:
    st.error("Gold metric tables are empty. Run `make metrics`, `make emissions`, and `make reconcile`.")
    st.stop()

with st.sidebar:
    selected_campuses = st.multiselect("Campus", campuses, default=campuses)
    selected_sources = st.multiselect("Source", sources, default=sources)

if not selected_campuses or not selected_sources:
    st.warning("Select at least one campus and one source.")
    st.stop()

usage = load_monthly_usage(config.db_path, selected_campuses, selected_sources)
emissions = load_emissions(config.db_path, selected_campuses, selected_sources)
peak_demand = load_peak_demand(config.db_path, selected_campuses)
reconciliation = load_reconciliation(config.db_path, selected_campuses)
has_baseline = table_exists(config.db_path, "gold", "gold_weather_normalized_usage")
has_peak_shift = table_exists(config.db_path, "gold", "gold_peak_shift_simulation")

total_usage = usage["total_consumption"].sum() if not usage.empty else 0
total_emissions = emissions["estimated_emissions_kg_co2e"].sum() if not emissions.empty else 0
max_peak_kw = peak_demand["peak_demand_kw"].max() if not peak_demand.empty else 0

metric_cols = st.columns(3)
metric_cols[0].metric("Monthly Usage Total", f"{total_usage:,.0f}")
metric_cols[1].metric("Estimated Emissions", f"{total_emissions:,.0f} kg CO2e")
metric_cols[2].metric("Max Peak Demand", f"{max_peak_kw:,.0f} kW")

tab_usage, tab_peak, tab_emissions, tab_reconcile, tab_baseline, tab_shift = st.tabs(
    ["Usage", "Peak Demand", "Emissions", "Reconciliation", "Weather Baseline", "Peak Shift"]
)

with tab_usage:
    st.subheader("Monthly Electricity Usage")
    st.line_chart(
        usage,
        x="usage_month",
        y="total_consumption",
        color="source_system",
    )
    st.dataframe(usage, use_container_width=True, hide_index=True)

with tab_peak:
    st.subheader("Observed NMI Peak Demand")
    st.bar_chart(
        peak_demand,
        x="meter_id",
        y="peak_demand_kw",
        color="campus_id",
    )
    st.dataframe(peak_demand, use_container_width=True, hide_index=True)

with tab_emissions:
    st.subheader("Estimated Monthly Emissions")
    st.caption(
        "Uses DCCEEW NGA 2025 Victoria Scope 2 factor: 0.78 kg CO2-e/kWh. "
        "Scope 3 is documented but not used. This is not carbon accounting compliance."
    )
    assumptions = load_emissions_assumptions(config.db_path)
    st.dataframe(assumptions, use_container_width=True, hide_index=True)
    st.line_chart(
        emissions,
        x="usage_month",
        y="estimated_emissions_kg_co2e",
        color="source_system",
    )
    st.dataframe(emissions, use_container_width=True, hide_index=True)

with tab_reconcile:
    st.subheader("NMI vs Building Usage Gaps")
    st.bar_chart(
        reconciliation,
        x="usage_month",
        y="consumption_difference",
        color="campus_id",
    )
    st.dataframe(reconciliation, use_container_width=True, hide_index=True)

with tab_baseline:
    st.subheader("Weather-Normalized Usage")
    st.caption(
        "High-usage candidates are investigation candidates, not confirmed waste, faults, or savings."
    )
    if has_baseline:
        baseline_summary = load_weather_baseline_summary(config.db_path, selected_campuses)
        baseline_candidates = load_top_weather_baseline_candidates(config.db_path, selected_campuses)
        baseline_cols = st.columns(2)
        baseline_cols[0].metric(
            "High-Usage Candidates",
            f"{baseline_summary['high_usage_candidates'].sum():,.0f}"
            if not baseline_summary.empty
            else "0",
        )
        baseline_cols[1].metric(
            "Candidate Rate",
            f"{baseline_summary['high_usage_candidates'].sum() / baseline_summary['baseline_rows'].sum():.1%}"
            if not baseline_summary.empty and baseline_summary["baseline_rows"].sum()
            else "0.0%",
        )
        st.bar_chart(
            baseline_summary,
            x="source_system",
            y="high_usage_rate",
            color="campus_id",
        )
        st.dataframe(baseline_summary, use_container_width=True, hide_index=True)
        st.subheader("Top Investigation Candidates")
        st.dataframe(baseline_candidates, use_container_width=True, hide_index=True)
    else:
        st.info("Weather baseline table not found. Run `make baseline`.")

with tab_shift:
    st.subheader("Peak-Shifting Simulation")
    st.caption(
        "Offline simulation only. Under the static DCCEEW Scope 2 factor, emissions remain unchanged when total kWh is preserved."
    )
    if has_peak_shift:
        flexible_load_percent = st.selectbox(
            "Flexible load percent",
            [0.05, 0.10, 0.15],
            format_func=lambda value: f"{value:.0%}",
        )
        shift_summary = load_peak_shift_summary(
            config.db_path, selected_campuses, flexible_load_percent
        )
        shift_results = load_top_peak_shift_results(
            config.db_path, selected_campuses, flexible_load_percent
        )
        shift_cols = st.columns(3)
        shift_cols[0].metric(
            "Avg Peak Reduction",
            f"{shift_summary['avg_peak_reduction'].mean():,.2f}"
            if not shift_summary.empty
            else "0.00",
        )
        shift_cols[1].metric(
            "Avg Reduction %",
            f"{shift_summary['avg_peak_reduction_percent'].mean():.1%}"
            if not shift_summary.empty
            else "0.0%",
        )
        shift_cols[2].metric(
            "Energy Preserved Rows",
            f"{shift_summary['energy_preserved_rows'].sum():,.0f}"
            if not shift_summary.empty
            else "0",
        )
        st.bar_chart(
            shift_summary,
            x="source_system",
            y="avg_peak_reduction",
            color="campus_id",
        )
        st.dataframe(shift_summary, use_container_width=True, hide_index=True)
        st.subheader("Top Peak-Reduction Scenarios")
        st.dataframe(shift_results, use_container_width=True, hide_index=True)
    else:
        st.info("Peak-shift simulation table not found. Run `make simulate-shift`.")
