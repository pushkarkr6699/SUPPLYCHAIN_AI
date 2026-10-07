# Discovered data dictionary

This is a schema inventory of registered supplied CSV files. The official DescriptionDataCoSupplyChain.csv is absent; types and field names below are observed, not invented definitions. Credential/contact columns are removed before application output.

## data/delivery/final/DataCo_Final_Order_Level_Dataset.csv

Role: primary order-level analytical dataset. Rows: 65752. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Order Id | int64 |
| Late_delivery_risk | int64 |
| Type | str |
| Customer Segment | str |
| Customer Country | str |
| Customer State | str |
| Market | str |
| Order Country | str |
| Order Region | str |
| Shipping Mode | str |
| Order Item Quantity | int64 |
| Sales | float64 |
| Order Item Discount | float64 |
| Order Item Discount Rate | float64 |
| Order Profit Per Order | float64 |
| Order Item Profit Ratio | float64 |
| Order_Year | int64 |
| Order_Month | int64 |
| Order_DayOfWeek | int64 |
| Order_Hour | int64 |
| Order_Weekend | int64 |
| Number_of_Items | int64 |
| Number_of_Products | int64 |
| Number_of_Categories | int64 |
| Order_Date | str |
| Average_Sales_Per_Item | float64 |
| Average_Quantity_Per_Item | float64 |
| Discount_to_Sales_Ratio | float64 |
| Profit_Margin | float64 |
| Order_Complexity | int64 |

## data/delivery/final/DataCo_Final_Scored_Orders.csv

Role: Tuned XGBoost scored test orders. Rows: 2123. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Order Id | int64 |
| Order_Date | str |
| Type | str |
| Customer Segment | str |
| Market | str |
| Order Country | str |
| Order Region | str |
| Shipping Mode | str |
| Sales | float64 |
| Order Profit Per Order | float64 |
| Number_of_Items | int64 |
| Number_of_Products | int64 |
| Number_of_Categories | int64 |
| Late_delivery_risk | int64 |
| Predicted_Late_Delivery | int64 |
| Late_Delivery_Probability | float64 |
| Risk_Level | str |
| Prediction_Model | str |
| Decision_Threshold | float64 |

## data/delivery/final/DataCo_Late_Delivery_Predictions.csv

Role: earlier Random Forest prediction reference. Rows: 2123. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Order Id | int64 |
| Market | str |
| Order Region | str |
| Shipping Mode | str |
| Late_delivery_risk | int64 |
| Predicted_Late_Risk | int64 |
| Late_Risk_Probability | float64 |
| Risk_Level | str |

## data/delivery/final/DataCo_Risk_Level_Summary.csv

Role: scored risk aggregation reference. Rows: 3. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Risk_Level | str |
| Orders | int64 |
| Average_Predicted_Risk | float64 |
| Actual_Late_Rate | float64 |

## data/delivery/final/evaluation/DataCo_Feature_Importance.csv

Role: Random Forest importance. Rows: 264. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Feature | str |
| Importance | float64 |

## data/delivery/final/evaluation/DataCo_Final_Model_Comparison.csv

Role: model evaluation reference. Rows: 3. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Model | str |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |
| ROC_AUC | float64 |
| PR_AUC | float64 |
| Brier_Score | float64 |

## data/delivery/final/evaluation/DataCo_Model_Comparison.csv

Role: model evaluation reference. Rows: 4. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Model | str |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 Score | float64 |
| ROC AUC | float64 |

## data/delivery/final/evaluation/DataCo_Model_Comparison (1).csv

Role: model evaluation reference. Rows: 4. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Model | str |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 Score | float64 |
| ROC AUC | float64 |

## data/demand/final/AccessLogs_Final_Advanced_Forecast.csv

Role: forecast output. Rows: 2280. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| DateOnly | str |
| Product | str |
| Category | str |
| Department | str |
| Visits | int64 |
| Next_Day_Visits | float64 |
| Predicted_Next_Day_Visits | float64 |
| Error | float64 |
| Absolute_Error | float64 |
| Prediction_Lower_90 | float64 |
| Prediction_Upper_90 | float64 |
| Demand_Level | str |
| Stock_Attention_Flag | str |

## data/demand/final/AccessLogs_Final_Model_Comparison.csv

Role: mixed comparison reference. Rows: 3. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Model | str |
| MAE | float64 |
| RMSE | float64 |
| R2 | float64 |
| WAPE_% | float64 |
| SMAPE_% | float64 |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |
| ROC_AUC | float64 |
| PR_AUC | float64 |
| Brier_Score | float64 |

## data/delivery/legacy/d3/Late_Delivery_Feature_Importance.csv

Role: separate line-item model reference. Rows: 4349. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Feature | str |
| Importance | float64 |

## data/delivery/legacy/d3/Late_Delivery_Final_Summary.csv

Role: separate line-item model reference. Rows: 15. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Property | str |
| Value | str |

## data/delivery/legacy/d3/Late_Delivery_Model_Comparison.csv

Role: separate line-item model reference. Rows: 4. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Model | str |
| Accuracy | float64 |
| Balanced_Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |
| ROC_AUC | float64 |
| PR_AUC | float64 |
| MCC | float64 |

## data/delivery/legacy/d3/Late_Delivery_Scored_Orders.csv

Role: separate line-item model reference. Rows: 24369. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Order Id | int64 |
| Market | str |
| Order Region | str |
| Order Country | str |
| Category Name | str |
| Department Name | str |
| Customer Segment | str |
| Shipping Mode | str |
| Order_Date | str |
| Actual_Late_Delivery | int64 |
| Late_Delivery_Probability | float64 |
| Predicted_Late_Delivery | int64 |
| Correct_Prediction | int64 |
| Delivery_Risk_Level | str |

## data/delivery/legacy/d3/Late_Delivery_Threshold_Analysis.csv

Role: separate line-item model reference. Rows: 62. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Threshold | float64 |
| Accuracy | float64 |
| Balanced_Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |
| MCC | float64 |

## data/demand/legacy/d3/AccessLogs_Final_Advanced_Forecast.csv

Role: duplicate forecast reference. Rows: 2280. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| DateOnly | str |
| Product | str |
| Category | str |
| Department | str |
| Visits | int64 |
| Next_Day_Visits | float64 |
| Predicted_Next_Day_Visits | float64 |
| Error | float64 |
| Absolute_Error | float64 |
| Prediction_Lower_90 | float64 |
| Prediction_Upper_90 | float64 |
| Demand_Level | str |
| Stock_Attention_Flag | str |

## data/profitability/final/DataCo_Calibration_Check.csv

Role: training evaluation reference. Rows: 5. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Probability_Band | str |
| Records | int64 |
| Average_Predicted_Probability | float64 |
| Actual_Profitability | float64 |

## data/profitability/final/DataCo_CatBoost_Tuning.csv

Role: training evaluation reference. Rows: 4. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Candidate | int64 |
| Iterations | int64 |
| Depth | int64 |
| Learning_Rate | float64 |
| L2 | int64 |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |
| ROC_AUC | float64 |
| PR_AUC | float64 |

## data/profitability/final/DataCo_Category_Summary.csv

Role: training evaluation reference. Rows: 45. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Category Name | str |
| Orders | int64 |
| Actual_Profitability | float64 |
| Average_Profit | float64 |
| Average_Prediction | float64 |

## data/profitability/final/DataCo_Feature_Importance.csv

Role: training evaluation reference. Rows: 238. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Feature | str |
| Importance | float64 |

## data/profitability/final/DataCo_Final_Project_Summary.csv

Role: training evaluation reference. Rows: 14. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Property | str |
| Value | str |

## data/profitability/final/DataCo_Final_Scored_Orders.csv

Role: scored line items. Rows: 27078. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Order Id | int64 |
| Market | str |
| Order Region | str |
| Order Country | str |
| Category Name | str |
| Department Name | str |
| Customer Segment | str |
| Shipping Mode | str |
| Order Item Quantity | int64 |
| Order Item Discount Rate | float64 |
| Order Item Product Price | float64 |
| Order_Date | str |
| Order Profit Per Order | float64 |
| Actual_Profitable | int64 |
| Profitability_Probability | float64 |
| Predicted_Profitable | int64 |
| Correct_Prediction | int64 |
| Profitability_Risk | str |

## data/profitability/final/DataCo_High_Loss_Risk_Orders.csv

Role: training evaluation reference. Rows: 5. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Order Id | int64 |
| Market | str |
| Order Region | str |
| Order Country | str |
| Category Name | str |
| Department Name | str |
| Customer Segment | str |
| Shipping Mode | str |
| Order Item Quantity | int64 |
| Order Item Discount Rate | float64 |
| Order Item Product Price | float64 |
| Order_Date | str |
| Order Profit Per Order | float64 |
| Actual_Profitable | int64 |
| Profitability_Probability | float64 |
| Predicted_Profitable | int64 |
| Correct_Prediction | int64 |
| Profitability_Risk | str |

## data/profitability/final/DataCo_Market_Summary.csv

Role: training evaluation reference. Rows: 3. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Market | str |
| Orders | int64 |
| Actual_Profitability | float64 |
| Average_Profit | float64 |
| Average_Prediction | float64 |

## data/profitability/final/DataCo_Model_Comparison.csv

Role: training evaluation reference. Rows: 6. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Model | str |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |
| ROC_AUC | float64 |
| PR_AUC | float64 |

## data/profitability/final/DataCo_Shipping_Summary.csv

Role: training evaluation reference. Rows: 4. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Shipping Mode | str |
| Orders | int64 |
| Actual_Profitability | float64 |
| Average_Profit | float64 |

## data/profitability/final/DataCo_Threshold_Analysis.csv

Role: training evaluation reference. Rows: 62. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Threshold | float64 |
| Accuracy | float64 |
| Precision | float64 |
| Recall | float64 |
| F1 | float64 |

## data/profitability/final/DataCo_Train_Test_Drift.csv

Role: training evaluation reference. Rows: 15. Grain follows the source family; evaluation tables are not business observations.

| Field | Observed dtype |
| --- | --- |
| Feature | str |
| Train_Mean | float64 |
| Test_Mean | float64 |
| Relative_Change | float64 |
