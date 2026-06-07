"""Streamlit entry point for the Campus Utility Intelligence dashboard."""

from __future__ import annotations

import streamlit as st

from campus_utility.config import get_config
from campus_utility.dashboard_data import (
    get_filter_options,
    load_emissions,
    load_emissions_assumptions,
    load_executive_summary,
    load_hourly_usage_heatmap,
    load_monthly_usage_by_campus,
    load_peak_shift_scenario_comparison,
    load_peak_shift_summary,
    load_pipeline_row_counts,
    load_quality_check_summary,
    load_reconciliation,
    load_temperature_usage_sample,
    load_top_peak_shift_results,
    load_top_usage_entities,
    load_top_weather_baseline_candidates,
    load_weather_actual_expected_trend,
    load_weather_baseline_summary,
    load_weather_candidate_rate_trend,
    table_exists,
)


def compact_number(value: float, suffix: str = "") -> str:
    """Format a large dashboard number."""

    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M{suffix}"
    if absolute >= 1_000:
        return f"{value / 1_000:,.1f}K{suffix}"
    return f"{value:,.1f}{suffix}"


def render_caption(text: str) -> None:
    """Render a consistent chart caption."""

    st.caption(text)


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

pages = [
    "Executive Overview",
    "Usage Patterns",
    "Emissions",
    "Weather-Normalized Efficiency",
    "Peak-Shifting Simulator",
    "NMI/Building Reconciliation",
    "Data Quality",
    "Methodology and Assumptions",
]

with st.sidebar:
    page = st.radio("Page", pages)
    selected_campuses = st.multiselect("Campus", campuses, default=campuses)
    selected_sources = st.multiselect("Source", sources, default=sources)

if not selected_campuses or not selected_sources:
    st.warning("Select at least one campus and one source.")
    st.stop()

has_baseline = table_exists(config.db_path, "gold", "gold_weather_normalized_usage")
has_peak_shift = table_exists(config.db_path, "gold", "gold_peak_shift_simulation")

if page == "Executive Overview":
    st.subheader("Executive Overview")
    summary = load_executive_summary(config.db_path, selected_campuses, selected_sources)

    kpi_cols = st.columns(5)
    kpi_cols[0].metric(
        "Total Electricity",
        compact_number(summary["total_consumption"], " kWh"),
        f"{summary['usage_delta_percent']:.1%} latest month",
    )
    kpi_cols[1].metric(
        "Estimated Scope 2",
        compact_number(summary["estimated_emissions_kg_co2e"] / 1_000, " tCO2e"),
    )
    kpi_cols[2].metric("Peak Demand", compact_number(summary["peak_demand_kw"], " kW"))
    kpi_cols[3].metric("High-Usage Rate", f"{summary['high_usage_rate']:.1%}")
    kpi_cols[4].metric(
        "Best Peak Reduction",
        compact_number(summary["best_peak_reduction"], " kWh"),
    )

    usage = load_monthly_usage_by_campus(config.db_path, selected_campuses, selected_sources)
    emissions = load_emissions(config.db_path, selected_campuses, selected_sources)
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("#### Monthly electricity usage")
        st.line_chart(usage, x="usage_month", y="total_consumption", color="campus_id")
        render_caption("Shows total monthly electricity usage for the selected campuses and sources.")
    with chart_cols[1]:
        st.markdown("#### Estimated Scope 2 emissions")
        st.line_chart(
            emissions,
            x="usage_month",
            y="estimated_emissions_kg_co2e",
            color="source_system",
        )
        render_caption("Estimated with the static DCCEEW Victoria Scope 2 factor.")

    st.markdown("#### Best peak-shift scenario")
    if has_peak_shift:
        comparison = load_peak_shift_scenario_comparison(
            config.db_path, selected_campuses, selected_sources
        )
        st.bar_chart(comparison, x="flexible_load_percent", y="best_peak_reduction")
        render_caption("Compares valid 5%, 10%, and 15% flexible-load scenarios by peak reduction.")
    else:
        st.info("Peak-shift simulation table not found. Run `make simulate-shift`.")

elif page == "Usage Patterns":
    st.subheader("Usage Patterns")
    st.markdown("#### Monthly usage by campus")
    monthly_by_campus = load_monthly_usage_by_campus(config.db_path, selected_campuses, selected_sources)
    st.bar_chart(monthly_by_campus, x="usage_month", y="total_consumption", color="campus_id")
    render_caption("This shows which campuses drive electricity consumption in each month.")

    st.markdown("#### Hour-of-day and day-of-week heatmap")
    heatmap = load_hourly_usage_heatmap(config.db_path, selected_campuses, selected_sources)
    if not heatmap.empty:
        pivot = heatmap.pivot(index="day_of_week", columns="hour_of_day", values="avg_consumption")
        ordered_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        pivot = pivot.reindex([day for day in ordered_days if day in pivot.index])
        st.dataframe(
            pivot.round(1),
            width="stretch",
        )
        render_caption("Darker cells show higher average usage by hour and weekday.")
    else:
        st.info("No hourly usage data available for the selected filters.")

    st.markdown("#### Top meters/buildings by usage")
    top_entities = load_top_usage_entities(config.db_path, selected_campuses, selected_sources)
    st.bar_chart(top_entities, x="meter_id", y="total_consumption", color="source_system")
    render_caption("Top groups are limited to 20 so the ranking stays readable.")
    st.dataframe(top_entities, width="stretch", hide_index=True)

elif page == "Emissions":
    st.subheader("Emissions")
    st.info(
        "Estimated Scope 2 location-based electricity emissions only. "
        "This is not carbon accounting compliance reporting."
    )
    assumptions = load_emissions_assumptions(config.db_path)
    emissions = load_emissions(config.db_path, selected_campuses, selected_sources)
    st.markdown("#### Emissions assumptions")
    st.dataframe(assumptions, width="stretch", hide_index=True)
    st.markdown("#### Estimated Scope 2 emissions trend")
    st.line_chart(emissions, x="usage_month", y="estimated_emissions_kg_co2e", color="source_system")
    render_caption(
        "Uses DCCEEW NGA 2025 Victoria Scope 2 factor: 0.78 kg CO2-e/kWh. "
        "Scope 3 is documented but not used."
    )
    st.dataframe(emissions, width="stretch", hide_index=True)

elif page == "Weather-Normalized Efficiency":
    st.subheader("Weather-Normalized Efficiency")
    st.caption("High-usage candidates are investigation candidates, not confirmed waste, faults, or savings.")
    if has_baseline:
        baseline_summary = load_weather_baseline_summary(config.db_path, selected_campuses)
        actual_expected = load_weather_actual_expected_trend(
            config.db_path, selected_campuses, selected_sources
        )
        candidate_rate = load_weather_candidate_rate_trend(
            config.db_path, selected_campuses, selected_sources
        )
        baseline_candidates = load_top_weather_baseline_candidates(config.db_path, selected_campuses)
        temp_sample = load_temperature_usage_sample(config.db_path, selected_campuses, selected_sources)

        st.markdown("#### Actual versus expected usage")
        if not actual_expected.empty:
            trend = actual_expected.groupby("usage_month", as_index=False)[
                ["actual_consumption", "expected_consumption", "residual_consumption"]
            ].sum()
            st.line_chart(trend, x="usage_month", y=["actual_consumption", "expected_consumption"])
            render_caption("Expected usage comes from the grouped weather/time median baseline.")
            st.bar_chart(trend, x="usage_month", y="residual_consumption")
            render_caption("Positive residual means actual usage was higher than expected.")

        st.markdown("#### Efficiency opportunity ranking")
        st.bar_chart(
            baseline_candidates.head(20),
            x="meter_id",
            y="efficiency_opportunity_score",
            color="source_system",
        )
        render_caption("Ranks the highest investigation candidates by opportunity score.")

        st.markdown("#### High-usage candidate rate over time")
        st.line_chart(candidate_rate, x="usage_month", y="high_usage_rate", color="source_system")
        render_caption("Shows how often records were flagged as high-usage candidates each month.")

        st.markdown("#### Temperature versus usage sample")
        if not temp_sample.empty:
            st.scatter_chart(temp_sample, x="air_temperature", y="actual_consumption", color="source_system")
            render_caption("Sampled points help show whether usage rises with outside temperature.")

        st.markdown("#### Summary table")
        st.dataframe(baseline_summary, width="stretch", hide_index=True)
    else:
        st.info("Weather baseline table not found. Run `make baseline`.")

elif page == "Peak-Shifting Simulator":
    st.subheader("Peak-Shifting Simulator")
    st.caption(
        "Offline simulation only. Because emissions use a static DCCEEW Scope 2 factor, "
        "same-day shifting preserves total estimated emissions when total kWh is preserved."
    )
    if has_peak_shift:
        comparison = load_peak_shift_scenario_comparison(
            config.db_path, selected_campuses, selected_sources
        )
        check_cols = st.columns(3)
        check_cols[0].metric(
            "Energy Preservation Failures",
            f"{comparison['energy_preservation_failures'].sum():,.0f}",
        )
        check_cols[1].metric("Negative Simulated Peaks", f"{comparison['negative_usage_rows'].sum():,.0f}")
        check_cols[2].metric("Worse Peaks", f"{comparison['worse_peak_rows'].sum():,.0f}")

        st.markdown("#### Scenario comparison")
        st.bar_chart(comparison, x="flexible_load_percent", y="avg_peak_reduction")
        render_caption("Compares average peak reduction across valid flexible-load scenarios.")
        st.dataframe(comparison, width="stretch", hide_index=True)

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
        st.markdown("#### Peak reduction leaderboard")
        st.bar_chart(shift_summary, x="source_system", y="avg_peak_reduction", color="campus_id")
        render_caption("Ranks campus/source groups by average simulated peak reduction.")
        st.dataframe(shift_results, width="stretch", hide_index=True)
    else:
        st.info("Peak-shift simulation table not found. Run `make simulate-shift`.")

elif page == "NMI/Building Reconciliation":
    st.subheader("NMI/Building Reconciliation")
    reconciliation = load_reconciliation(config.db_path, selected_campuses)
    st.bar_chart(reconciliation, x="usage_month", y="consumption_difference", color="campus_id")
    render_caption(
        "Shows the gap between campus-level NMI usage and summed building usage. "
        "The data does not attribute the gap to exact physical causes."
    )
    st.dataframe(reconciliation, width="stretch", hide_index=True)

elif page == "Data Quality":
    st.subheader("Data Quality And Trust")
    row_counts = load_pipeline_row_counts(config.db_path)
    if not row_counts.empty:
        funnel = row_counts.groupby("schema_name", as_index=False)["row_count"].sum()
        st.markdown("#### Medallion pipeline row-count funnel")
        st.bar_chart(funnel, x="schema_name", y="row_count")
        render_caption("Shows how data moves from raw bronze tables into cleaned silver and gold marts.")
        st.dataframe(row_counts, width="stretch", hide_index=True)

    quality_summary = load_quality_check_summary(config.db_path)
    st.markdown("#### Quality checks")
    if quality_summary.empty:
        st.info("Quality check table not found. Review `reports/data_quality_report.md` after running `make quality`.")
    else:
        st.bar_chart(quality_summary, x="status", y="check_count")
        st.dataframe(quality_summary, width="stretch", hide_index=True)

    st.markdown("#### Reconciliation trust check")
    reconciliation = load_reconciliation(config.db_path, selected_campuses)
    st.bar_chart(reconciliation, x="usage_month", y="consumption_difference", color="campus_id")
    render_caption("NMI/building gaps are tracked as data trust signals, not automatically treated as errors.")

else:
    st.subheader("Methodology and Assumptions")
    st.markdown(
        """
        This dashboard reads existing DuckDB bronze, silver, gold, and reference tables.

        Emissions use the DCCEEW NGA 2025 Victoria Scope 2 factor of `0.78 kg CO2-e/kWh`.
        Scope 3 is documented but not used, and the output is not carbon accounting compliance reporting.

        Weather-normalized high-usage records are investigation candidates only. They are not confirmed waste,
        faults, or guaranteed savings.

        Peak shifting is an offline simulation. It preserves same-day total kWh and does not claim emissions
        reduction while the emissions factor is static.

        NMI readings are campus-level readings. Building readings are not expected to always equal NMI readings
        because campus-level loads can include items not represented in building-level readings.
        """
    )
