# Architecture

Campus Utility Intelligence will use a local medallion-style analytics architecture:

1. Raw Kaggle files in `data/raw/`
2. Bronze DuckDB tables with minimal transformation
3. Silver cleaned electricity readings
4. Gold reporting marts for usage, peak demand, and emissions estimates
5. SQL analytics and Streamlit dashboard views

Feature 1 establishes the repository structure only. Data ingestion and transformations are planned future features.
