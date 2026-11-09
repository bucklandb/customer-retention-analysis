-- Run after loading the prepared purchases CSV. Read sql/README.md first.
-- Final ordering is added for a reproducible downstream split.
WITH first_orders AS (
    SELECT
        CUSTOMERID, INVOICENO,
        SUM(QUANTITY * UNITPRICE) as order_value,
        MIN(InvoiceDate) AS order_date,
        SUM(QUANTITY) AS total_quantity,
        COUNT(DISTINCT STOCKCODE) as distinct_products,
        LEAD(MIN(INVOICEDATE)) OVER (
            PARTITION BY CUSTOMERID
            ORDER BY MIN(INVOICEDATE), INVOICENO
        ) AS second_order_date
    FROM CUSTOMER_RETENTION_DEMO.PUBLIC.PURCHASES
    GROUP BY CUSTOMERID, INVOICENO
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY CUSTOMERID
        ORDER BY MIN(INVOICEDATE), INVOICENO
    ) = 1
)
SELECT *,
    CASE
        WHEN second_order_date <= DATEADD(day, 90, order_date)
        THEN 1 ELSE 0
    END AS returned_within_90
FROM first_orders
WHERE order_date <= '2011-09-10 12:50:00'::TIMESTAMP_NTZ
ORDER BY CUSTOMERID, INVOICENO;
