import unittest
import pandas as pd
from src.retention import FEATURES, prepare_purchases, build_customer_features, evaluate

def rows(records):
    return pd.DataFrame(records,columns=["CustomerID","InvoiceNo","InvoiceDate","Quantity","UnitPrice","StockCode"])

class RetentionTests(unittest.TestCase):
    def test_cleaning_matches_original_and_retains_duplicates(self):
        data=rows([(1,1,"2020-01-01",1,2,"A"),(1,1,"2020-01-01",1,2,"A"),(None,2,"2020-01-01",1,2,"A"),(2,3,"2020-01-01",0,2,"A"),(2,4,"2020-01-01",1,0,"A"),(2,5,"2020-01-01",-1,2,"A")])
        self.assertEqual(len(prepare_purchases(data)),2)
    def test_exact_cutoff_and_nonreturner_denominator(self):
        data=rows([(1,1,"2020-01-01 12:00",1,2,"A"),(1,2,"2020-03-31 12:00",1,2,"A"),(2,3,"2020-01-01 12:00",1,2,"A"),(3,4,"2020-01-01 12:00:01",1,2,"A"),(4,5,"2020-03-31 12:00",1,2,"A")])
        out,_=build_customer_features(prepare_purchases(data))
        self.assertEqual(out.CUSTOMERID.tolist(),[1,2]);self.assertEqual(out.RETURNED_WITHIN_90.tolist(),[1,0])
    def test_late_return_is_zero(self):
        data=rows([(1,1,"2020-01-01",1,2,"A"),(1,2,"2020-03-31 00:00:01",1,2,"A")])
        out,_=build_customer_features(prepare_purchases(data));self.assertEqual(out.RETURNED_WITHIN_90.iloc[0],0)
    def test_invoice_aggregation_and_first_order_features(self):
        data=rows([(1,1,"2020-01-01 12:00",2,3,"A"),(1,1,"2020-01-01 12:01",1,4,"B"),(1,2,"2020-01-02",999,999,"C"),(2,3,"2020-05-01",1,1,"D")])
        out,_=build_customer_features(prepare_purchases(data))
        self.assertEqual(out.loc[0,FEATURES].tolist(),[10,3,2]);self.assertEqual(out.RETURNED_WITHIN_90.iloc[0],1)
    def test_same_timestamp_distinct_orders_and_stable_sort(self):
        data=rows([(1,2,"2020-01-01",2,2,"B"),(1,1,"2020-01-01",1,1,"A"),(2,3,"2020-05-01",1,1,"C")])
        a,_=build_customer_features(prepare_purchases(data));b,_=build_customer_features(prepare_purchases(data.iloc[::-1]))
        pd.testing.assert_frame_equal(a,b);self.assertEqual(a.INVOICENO.iloc[0],1);self.assertEqual(a.RETURNED_WITHIN_90.iloc[0],1)
    def test_reject_invoice_shared_by_customers(self):
        with self.assertRaisesRegex(ValueError,"multiple customers"):
            prepare_purchases(rows([(1,1,"2020-01-01",1,1,"A"),(2,1,"2020-01-01",1,1,"A")]))
    def test_reject_missing_schema(self):
        with self.assertRaisesRegex(ValueError,"Missing required"):
            prepare_purchases(pd.DataFrame({"CustomerID":[1]}))
    def test_reject_invalid_timestamp(self):
        with self.assertRaises(ValueError):
            prepare_purchases(rows([(1,1,"not-a-date",1,1,"A")]))
    def test_evaluation_is_independent_of_input_row_order(self):
        data=pd.DataFrame({"CUSTOMERID":range(1,41),"INVOICENO":range(100,140),
            "ORDER_VALUE":[float(i+1) for i in range(40)],"TOTAL_QUANTITY":[i%5+1 for i in range(40)],
            "DISTINCT_PRODUCTS":[i%3+1 for i in range(40)],"RETURNED_WITHIN_90":[i%2 for i in range(40)]})
        a,*_=evaluate(data);b,*_=evaluate(data.sample(frac=1,random_state=9))
        self.assertEqual(a,b);self.assertEqual(a["train_customers"],32);self.assertEqual(a["test_customers"],8)
        self.assertEqual(a["features"],FEATURES)
    def test_reject_nonfinite_purchase_amount(self):
        with self.assertRaisesRegex(ValueError,"finite"):
            prepare_purchases(rows([(1,1,"2020-01-01",1,float("inf"),"A")]))
if __name__=="__main__":unittest.main()
