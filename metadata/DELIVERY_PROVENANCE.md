# Delivery source and model provenance

Audit date: 2026-10-04. CSV files were read directly and notebook JSON source was inspected; notebooks were not executed and serialized models were not loaded.

## Active analytical source: d1 order-level package

- `DataCo_Final_Order_Level_Dataset.csv`: 65,752 rows, one unique `Order Id` per row, no nulls or duplicate rows. Dates span 2015-01-01 through 2018-01-31. This is the user-selected primary analytical dataset.
- `DataCo_Final_Scored_Orders.csv`: 2,123 unique orders from January 2018. Every order joins the primary dataset one-to-one, and every shared field matches exactly. This is 3.23% of primary orders. Other primary orders are unscored; absent scores must remain missing rather than becoming low risk or a zero probability.
- Scored model is `Tuned XGBoost`; each scored row explicitly supplies decision threshold `0.35`. Predicted labels exactly match `Late_Delivery_Probability >= 0.35`. Risk tiers are separate: Low below 0.40, Medium from 0.40 to below 0.70, High at least 0.70.
- `DataCo_Late_Delivery_Predictions.csv` is the earlier Random Forest output according to the notebook. Its 2,123 IDs match the scored file, but all probabilities differ and only 48.05% of predicted labels agree. It is a reference model output, not a second source of the final XGBoost scores.
- `DataCo_Risk_Level_Summary.csv` matches grouping of the final scored data: 564 Low, 857 Medium, 702 High. Its probability and actual-rate aggregates are percentages (0–100).
- `DataCo_Model_Comparison.csv` and `DataCo_Model_Comparison (1).csv` are byte-identical copies; preserve the names as supplied but do not count them as independent evaluations.
- `DataCo_Feature_Importance.csv` has 264 rows and is generated from the original Random Forest pipeline in the notebook. It is not an explanation of the final tuned XGBoost scores.
- `DataCo_Late_Delivery_Model.pkl` is the original Random Forest pipeline according to its export cell. `DataCo_Tuned_XGBoost.pkl` is the tuned XGBoost pipeline, with preprocessing included according to notebook source. Serialization contents/runtime compatibility require separate validation before inference.

## Evaluation interpretation

Notebook train/test split: 63,629 orders before 2018 for training and 2,123 orders in 2018 for testing. The notebook selects threshold 0.35 by maximizing F1 using those test predictions. This threshold is test-selected; the same rows do not provide an independent evaluation of threshold selection.

Recomputed accuracy of final scored predictions at threshold 0.35 is **0.6208195949128592** (62.08%). At threshold 0.50, recomputed accuracy is **0.7206782854451248**, exactly matching the `Tuned XGBoost` row in `DataCo_Final_Model_Comparison.csv`. These represent different thresholds, not corrupt files. Do not show the comparison accuracy as accuracy of the selected 0.35 operating point.

## Primary CSV schema and normalization

Primary columns:

```text
Order Id, Late_delivery_risk, Type, Customer Segment, Customer Country,
Customer State, Market, Order Country, Order Region, Shipping Mode,
Order Item Quantity, Sales, Order Item Discount, Order Item Discount Rate,
Order Profit Per Order, Order Item Profit Ratio, Order_Year, Order_Month,
Order_DayOfWeek, Order_Hour, Order_Weekend, Number_of_Items,
Number_of_Products, Number_of_Categories, Order_Date, Average_Sales_Per_Item,
Average_Quantity_Per_Item, Discount_to_Sales_Ratio, Profit_Margin,
Order_Complexity
```

Canonical mappings: `Order Id` → `Order`; `Order_Date` → `Date`; `Order Country` → `Country`; `Order Region` → `Region`; `Customer Segment` → `Segment`; `Order Profit Per Order` → `Profit`; `Late_delivery_risk` → `Actual Late`. `Sales`, `Market`, and `Shipping Mode` retain their names. Final score fields map `Late_Delivery_Probability` → `Risk Score`, `Predicted_Late_Delivery` → `Predicted Late`, `Risk_Level` → `Risk` (remove the ` Risk` suffix).

The primary source supplies sales/profit and order geography, but does not supply product/category names, delivery duration, scheduled shipping duration, inventory, or demand measures. `Number_of_Categories` is a count, not a category label.

## Tuned XGBoost input contract from notebook

Categorical features (in declared input order):

```text
Type, Customer Segment, Customer Country, Customer State,
Market, Order Country, Order Region, Shipping Mode
```

Numeric features (following the categorical inputs):

```text
Order Item Quantity, Sales, Order Item Discount, Order Item Discount Rate,
Order Profit Per Order, Order Item Profit Ratio, Number_of_Items,
Number_of_Products, Number_of_Categories, Order_Month, Order_DayOfWeek,
Order_Hour, Order_Weekend, Average_Sales_Per_Item,
Average_Quantity_Per_Item, Discount_to_Sales_Ratio, Profit_Margin,
Order_Complexity
```

There are 26 input columns (8 categorical + 18 numeric). Numeric preprocessing uses median imputation then `StandardScaler`. Categorical preprocessing uses most-frequent imputation then `OneHotEncoder(handle_unknown='ignore')`. The `ColumnTransformer` emits numeric features followed by encoded categorical features. Pipeline steps are `preprocessor` and `classifier`. Do not supply target, order identifier, or date string as model inputs. The earlier Random Forest omits the last five engineered numeric features.

## Separate d3 delivery package

`Late_Delivery_Scored_Orders.csv` is a different, line-item-level experiment: 24,369 rows and 13,670 unique orders, including 1,757 exact duplicate rows. All order IDs, dates, and targets match the d1 primary, but 1,229 orders have multiple distinct probabilities. It must not be joined as a one-to-one source or substituted silently for d1 scores.

The d3 model is XGBoost with threshold 0.56 and risk boundaries 0.41/0.71. Recomputed test scored accuracy is **0.6948992572530674**, which correctly rounds to the supplied final summary **0.6949**. Threshold-analysis accuracy **0.6874313408723748** at 0.56 is from the validation split, per notebook. Model comparison is also validation data. The earlier project claim of an unresolved accuracy mismatch conflated validation and test results and should not be retained.

The d3 notebook includes profitability research and several delivery revisions; notebook sections must be tied to their exact exports. Preserve d3 as a separate version/reference with its own thresholds and row grain.

`Unconfirmed 506925.crdownload` is an incomplete-download artifact and is excluded.
