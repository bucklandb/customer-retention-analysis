# Snowflake workflow

The SQL preserves the showcase's invoice-level grouping, LEAD, QUALIFY, and exact 90-day label. It adds an explicit final customer/invoice order so the Python holdout is reproducible.

1. Run the local preparation notebook, or the CLI with `--export-data`.
2. In an existing authorized Snowflake account, load `data/processed/purchases.csv` into `CUSTOMER_RETENTION_DEMO.PUBLIC.PURCHASES`. Use the upload wizard in its own session; do not copy temporary wizard-stage references to a different editor. Raw data is not bundled here.
3. Preserve UnitPrice as a decimal with four fractional places; use TIMESTAMP_NTZ for InvoiceDate. InvoiceNo/StockCode are identifiers, not continuous predictors.
4. Run `first_order_features.sql`. Expected cohort is 3,370 customers, with 1,605 positive outcomes. Export the result to `data/processed/model_data.csv` and run `notebooks/02_model_evaluation.ipynb`.
5. In Snowflake Workspaces you can instead pass the SQL result's actual dataframe pointer to `.to_pandas()`. The pointer name depends on the notebook; no credentials belong in code.

The fixed cutoff is specific to this dataset and its last invoice-level timestamp, 2011-12-09 12:50:00. Recalculate that endpoint if using another dataset. Existing compute/storage can cost money. No account, warehouse, or permanent resource is created by this repository's SQL.

The November 2026 packaging checks ran the local Python reproduction. They did not compile or execute this SQL in Snowflake. Historical Snowflake results are described separately in the main README.
