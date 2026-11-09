"""Reproduce the existing retention workflow without a Snowflake account."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_version
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["ORDER_VALUE", "TOTAL_QUANTITY", "DISTINCT_PRODUCTS"]
REQUIRED = ["CustomerID", "InvoiceNo", "InvoiceDate", "Quantity", "UnitPrice", "StockCode"]

def prepare_purchases(raw):
    """Match the original: known customer, positive quantity and unit price."""
    missing = set(REQUIRED) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    purchases = raw.loc[raw.CustomerID.notna() & (raw.Quantity > 0) & (raw.UnitPrice > 0)].copy()
    if purchases.empty:
        raise ValueError("No qualifying purchase lines")
    purchases["InvoiceDate"] = pd.to_datetime(purchases.InvoiceDate, format="ISO8601", errors="raise")
    if purchases[["InvoiceNo", "InvoiceDate", "StockCode"]].isna().any().any():
        raise ValueError("Qualifying purchases have a missing order, timestamp, or product")
    if not np.isfinite(purchases[["Quantity", "UnitPrice"]].to_numpy(dtype=float)).all():
        raise ValueError("Quantity and price must be finite")
    if purchases.groupby("InvoiceNo").CustomerID.nunique().max() != 1:
        raise ValueError("An invoice belongs to multiple customers")
    return purchases

def build_customer_features(purchases):
    """One first-order record per customer with an exact, mature time window."""
    window_days = 90
    p = purchases.assign(line_value=purchases.Quantity * purchases.UnitPrice)
    orders = p.groupby(["CustomerID", "InvoiceNo"], as_index=False).agg(
        order_date=("InvoiceDate", "min"), ORDER_VALUE=("line_value", "sum"),
        TOTAL_QUANTITY=("Quantity", "sum"), DISTINCT_PRODUCTS=("StockCode", "nunique"))
    orders = orders.sort_values(["CustomerID", "order_date", "InvoiceNo"], kind="stable")
    endpoint = orders.order_date.max()
    orders["second_order_date"] = orders.groupby("CustomerID").order_date.shift(-1)
    first = orders.groupby("CustomerID", sort=True).head(1).copy()
    first = first.loc[first.order_date <= endpoint - pd.Timedelta(days=window_days)].copy()
    first["RETURNED_WITHIN_90"] = (first.second_order_date <= first.order_date + pd.Timedelta(days=window_days)).astype(int)
    first = first.rename(columns={"CustomerID":"CUSTOMERID", "InvoiceNo":"INVOICENO"})
    return first.sort_values(["CUSTOMERID", "INVOICENO"]).reset_index(drop=True), endpoint

def evaluate(model_data):
    data = model_data.sort_values(["CUSTOMERID", "INVOICENO"]).reset_index(drop=True)
    X, y = data[FEATURES], data.RETURNED_WITHIN_90
    if len(y.unique()) != 2:
        raise ValueError("Evaluation requires both outcome classes")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    model.fit(X_train, y_train)
    baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    predictions, probabilities = model.predict(X_test), model.predict_proba(X_test)[:, 1]
    metrics = {"train_customers":len(y_train), "test_customers":len(y_test),
               "accuracy":float(accuracy_score(y_test,predictions)),
               "baseline_accuracy":float(baseline.score(X_test,y_test)),
               "roc_auc":float(roc_auc_score(y_test,probabilities)),
               "returner_recall":float(recall_score(y_test,predictions)),
               "confusion_matrix_true_rows_predicted_columns":confusion_matrix(y_test,predictions,labels=[0,1]).tolist(),
               "seed":42,"test_size":0.2,"row_order":["CUSTOMERID","INVOICENO"],
               "features":FEATURES,"threshold":0.5,
               "python":platform.python_version(),"pandas":pd.__version__,"sklearn":sklearn_version}
    return metrics, y_test, predictions, probabilities

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True,help="UCI Online Retail.xlsx")
    parser.add_argument("--output-dir",type=Path,default=Path("reports"))
    parser.add_argument("--export-data",action="store_true",help="Write ignored local CSVs for notebooks/Snowflake")
    args = parser.parse_args()
    raw = pd.read_excel(args.input)
    purchases = prepare_purchases(raw)
    customers, endpoint = build_customer_features(purchases)
    metrics, y_test, predictions, probabilities = evaluate(customers)
    metrics.update({"raw_rows":len(raw),"purchase_rows":len(purchases),"eligible_customers":len(customers),
                    "returned_within_90":int(customers.RETURNED_WITHIN_90.sum()),
                    "retention_rate":float(customers.RETURNED_WITHIN_90.mean()),
                    "observation_end":str(endpoint),"eligibility_cutoff":str(endpoint-pd.Timedelta(days=90)),
                    "input_sha256":hashlib.sha256(args.input.read_bytes()).hexdigest(),
                    "execution":"Local Python reproduction; Snowflake SQL not executed in this run"})
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay
    ConfusionMatrixDisplay.from_predictions(y_test,predictions,labels=[0,1],display_labels=["No 90-day return","90-day return"],cmap="Blues",colorbar=False)
    plt.title("Local reproducible holdout");plt.tight_layout();plt.savefig(args.output_dir/"confusion_matrix.png",dpi=160);plt.close()
    fig, ax=plt.subplots(figsize=(6,4))
    RocCurveDisplay.from_predictions(y_test,probabilities,name="Logistic regression",ax=ax)
    ax.plot([0,1],[0,1],"--",color="gray",label="Chance")
    ax.set_title("First-order features: 90-day return");ax.legend(loc="lower right")
    fig.tight_layout();fig.savefig(args.output_dir/"roc_curve.png",dpi=160);plt.close(fig)
    if args.export_data:
        processed=Path("data/processed");processed.mkdir(parents=True,exist_ok=True)
        purchases.to_csv(processed/"purchases.csv",index=False)
        customers.to_csv(processed/"model_data.csv",index=False)
    print(json.dumps(metrics,indent=2))
if __name__ == "__main__": main()
