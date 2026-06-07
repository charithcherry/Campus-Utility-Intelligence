"""Streamlit entry point for the Campus Utility Intelligence dashboard."""

import streamlit as st

from campus_utility.config import get_config
from campus_utility.dashboard_data import (
    get_filter_options,
    load_emissions,
    load_monthly_usage,
    load_peak_demand,
    load_reconciliation,
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

total_usage = usage["total_consumption"].sum() if not usage.empty else 0
total_emissions = emissions["estimated_emissions_kg_co2e"].sum() if not emissions.empty else 0
max_peak_kw = peak_demand["peak_demand_kw"].max() if not peak_demand.empty else 0

metric_cols = st.columns(3)
metric_cols[0].metric("Monthly Usage Total", f"{total_usage:,.0f}")
metric_cols[1].metric("Estimated Emissions", f"{total_emissions:,.0f} kg CO2e")
metric_cols[2].metric("Max Peak Demand", f"{max_peak_kw:,.0f} kW")

tab_usage, tab_peak, tab_emissions, tab_reconcile = st.tabs(
    ["Usage", "Peak Demand", "Emissions", "Reconciliation"]
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
