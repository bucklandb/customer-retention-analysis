# Provenance and preparation

This is Benjamin Buckland's independent customer-retention learning/showcase project, built with AI-assisted coaching and presentation refinement. It is not a client or employer project. The portfolio packaging adds documentation, a local reproduction script, synthetic unit tests, explicit ordering, and reproducibility checks with AI assistance.

The original presentation preparation calculations and Snowflake model workflow were retained as the starting point. Notebook outputs were cleared, paths made portable, and the Snowflake SQL separated from the Python notebook. Original source files were not changed.

The exact original Snowflake row order was not retained. A fixed random seed is not sufficient to reconstruct the same holdout if row order changes. This version sorts by customer and invoice before splitting and reports its own execution results. Historical showcase metrics must not be represented as newly reproduced.

The data is Chen, D. (2015), Online Retail, UCI Machine Learning Repository, https://doi.org/10.24432/C5BW33, licensed CC BY 4.0. Dataset download: https://archive.ics.uci.edu/dataset/352/online+retail . Dataset license: https://creativecommons.org/licenses/by/4.0/ . Derived aggregate results and charts retain that attribution. The raw workbook, customer-level exports, recordings, account details, course instructions, and employer materials are excluded from Git.

Original code is licensed under the [MIT License](../LICENSE), copyright 2026 Benjamin Buckland. The UCI Online Retail dataset and derived aggregate results and charts remain under CC BY 4.0; the MIT license does not change their license or attribution requirements.

Source notebook SHA-256 hashes (audit identifiers, not publication of original paths):
{
  "retention_presentation.ipynb": "5d5a9d7e2d8c608b841e8f4ad11c2617d38fcd47cb0c9bd8d9f29e4b48b1dc34",
  "snowflake_presentation.ipynb": "8b10e2aa4085d919af8a5675eca8ecc62da2d86b832daba51190af708cd5ae2c"
}
