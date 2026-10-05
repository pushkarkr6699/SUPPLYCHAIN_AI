# Trained artifact provenance

Audit source: the user-supplied `D:/IBM Prac/d1`, `d2`, and `d3` packages. Notebooks were read as JSON, never executed. Models were inspected as bytes and pickle opcodes; this document does not claim that static inspection proves arbitrary pickle files safe. Runtime parity checks, when available, are recorded separately.

## Primary order-level delivery model (d1)

- Primary analytical file: `DataCo_Final_Order_Level_Dataset.csv`, 65,752 unique orders.
- Final scored output: `DataCo_Final_Scored_Orders.csv`, 2,123 orders from 2018; all IDs exist in the primary file.
- Final serialized model: `DataCo_Tuned_XGBoost.pkl`; notebook cells 182 and 212 select and export `best_xgb_model` (`Tuned XGBoost`).
- Decision rule: positive probability >= **0.35**. Source risk labels use `< 0.40` Low, `< 0.70` Medium, otherwise High. Risk bands and the decision threshold have different purposes.
- The pipeline contains a `ColumnTransformer`, median imputation and `StandardScaler` for numeric inputs, most-frequent imputation and `OneHotEncoder(handle_unknown='ignore')` for categorical inputs, followed by `XGBClassifier` with `binary:logistic` objective.
- Serialized version markers: scikit-learn **1.6.1**, XGBoost **3.4.1**. Initial project runtime was Python 3.13.5 with pandas 3.0.6 and NumPy 2.5.3; scikit-learn, XGBoost, and joblib were initially absent.
- All 26 required input columns are supplied by the primary CSV. Order ID, target, and order year are not model features.

Categorical feature order:

```text
Type, Customer Segment, Customer Country, Customer State,
Market, Order Country, Order Region, Shipping Mode
```

Numeric feature order:

```text
Order Item Quantity, Sales, Order Item Discount, Order Item Discount Rate,
Order Profit Per Order, Order Item Profit Ratio, Number_of_Items,
Number_of_Products, Number_of_Categories, Order_Month, Order_DayOfWeek,
Order_Hour, Order_Weekend, Average_Sales_Per_Item,
Average_Quantity_Per_Item, Discount_to_Sales_Ratio, Profit_Margin,
Order_Complexity
```

The dataframe training order is categorical columns followed by numeric columns. Pass the full named dataframe to the saved pipeline; do not manually one-hot encode its inputs.

For new orders, preserve the notebook's aggregation: sum quantity, sales, discount, and profit; mean discount rate and profit ratio; count line items, distinct products, and distinct categories. Calendar features derive from the order timestamp (Monday=0; weekend >=5). Derived fields are sales/items, quantity/items, discount/sales, profit/sales, and products+categories. Zero denominators become missing values for pipeline imputation. Profit fields must be known at scoring time; the supplied training data do not establish their availability before fulfillment.

The notebook trains on years before 2018 and evaluates on 2018. It selects threshold 0.35 by maximizing F1 on that same test data (cells 144 and 177). Its displayed classification metrics therefore are retrospective diagnostics, not an untouched final holdout. Recomputed agreement from the scored CSV is 62.08195949%.

`DataCo_Late_Delivery_Model.pkl` is an earlier **RandomForestClassifier** pipeline using 21 features. `DataCo_Feature_Importance.csv` was exported from that earlier random forest (cells 98 and 104); it must not be presented as tuned-XGBoost feature importance. `DataCo_Late_Delivery_Predictions.csv` is also an earlier reference output.

## Demand forecasting (d2)

`AccessLogs_Final_XGBoost_Demand_Model.pkl` is a pipeline containing numeric median imputation, categorical most-frequent imputation plus one-hot encoding, and `XGBRegressor` (`reg:squarederror`, 250 estimators, max depth 5). Serialized version markers are scikit-learn 1.6.1 and XGBoost 3.4.1.

Input dataframe order:

```text
Product, Category, Department, Visits, Visits_Lag_1, Visits_Lag_2,
Visits_Lag_7, Rolling_Mean_3, Rolling_Mean_7, Rolling_Mean_14,
Rolling_Std_7, Month, DayOfWeek, Weekend, DayOfMonth
```

Each row represents a product on a base date and predicts `Next_Day_Visits`. Demand is web visits, not purchased units. The notebook zero-fills a complete product/date grid, then derives lags within product. Rolling means use `Visits.shift(1)` with windows 3, 7, and 14 (`min_periods=1`). Rolling standard deviation uses the shifted series, window 7 and `min_periods=2`, then fills missing standard deviation with zero. Current visits and calendar features are from the base date. Train dates precede 2018-01-01; forecast output base dates are in January 2018.

The forecast CSV supplies current `Visits` and forecast outputs, but does not contain all precomputed model inputs. Its 30 days of history can reconstruct features for later January dates; the first 14 days do not contain complete prior history. Historical reconstruction must never substitute target `Next_Day_Visits` as an input. A future forecast requires an up-to-date per-product daily visits series.

### Export defects and uncertainty

- In notebook cell 35, the assignment `xgb_result = forecast_metrics(...)` is indented after the function's `return`; it cannot run. The comparison CSV's XGBoost row consequently contains stale classification metrics and missing regression metrics. Exclude that row from regression comparisons; compute MAE/RMSE/WAPE/SMAPE directly from matched forecast outputs instead.
- The nominal 90% intervals are based on the training residuals' 5th/95th percentiles; observed coverage on the supplied forecast rows is approximately 67.63%. Their name is not evidence of calibration.
- Stock flags mean high predicted visits / review stock. No inventory-on-hand data are supplied, so these flags are not demonstrated stockout predictions.

The d2 and d3 `AccessLogs_Final_Advanced_Forecast.csv` copies are byte-identical (SHA-256 `593b58deeb3d7ec1fac4858b513f230c9bd5268ce1d763867075db2c9110800a`). Keep one active source and preserve the other package's provenance.

## Separate delivery experiment (d3)

`Final_Late_Delivery_Model.pkl` is a pipeline with median numeric imputation, most-frequent categorical imputation and `OneHotEncoder(handle_unknown='ignore', min_frequency=5)`, followed by `XGBClassifier` (280 estimators, max depth 5). Serialized markers are scikit-learn 1.6.1 and XGBoost 3.4.1. Its rule uses probability >=0.56, selected against validation MCC. Its 31 raw features include item/product/category metadata absent from the d1 order-level dataset.

This is a **line-item** experiment: 24,369 scored rows are not 24,369 unique orders. Training dates precede 2017-01-01, validation is January–June 2017, and test begins 2017-07-01. The notebook explicitly selects its model and threshold on validation; comparison and threshold files are validation artifacts. Do not reuse these metrics, threshold, or pipeline for the primary d1 order-level model.

Numeric features:

```text
Days for shipment (scheduled), Category Id, Department Id,
Order Item Discount, Order Item Discount Rate, Order Item Quantity,
Order Item Product Price, Product Category Id, Product Price, Sales,
Sales per customer, Order Item Total, Order_Year, Order_Month,
Order_Quarter, Order_DayOfWeek, Weekend
```

Categorical features:

```text
Type, Category Name, Customer Segment, Department Name, Market,
Order Country, Order Region, Shipping Mode, Product Name, Product Card Id,
Order State, Order City, Customer Country, Customer State
```

The d3 test scored CSV recomputes to 69.48992573%, matching its summary rounded to 69.49%. The 68.74313409% threshold-analysis figure belongs to validation. The earlier discrepancy claim conflated those splits. Keep d3 separate because its schema, threshold and row grain differ from d1.

## Completed runtime parity

Original d1 delivery and d2 demand pipelines were loaded in isolated Linux and exported as native XGBoost JSON with their original fitted preprocessors, without retraining. Windows delivery reproduced all 2,123 probabilities within 2.97e-8 with all labels matching at 0.35. Demand reconstructed only full-history rows and reproduced 1,216 forecasts within 1.53e-5 visits. Hash-checked conversion manifests and runtime reports are stored in metadata. Changed artifacts or runtime dependencies disable inference until revalidation.
