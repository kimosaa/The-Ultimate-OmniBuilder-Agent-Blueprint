# Data Analysis Example

Demonstrates OmniBuilder's data analysis capabilities.

## Goal

Analyze a CSV dataset and generate visualizations.

## Dataset

Sample sales data (will be generated):
- Date
- Product
- Quantity
- Price
- Region

## Running with OmniBuilder

```bash
cd examples/data_analysis

# Generate and analyze
omnibuilder run "Generate sample sales data, analyze it, and create visualizations showing sales by region and product"
```

## Expected Outputs

1. `sales_data.csv` - Generated sample data
2. `analysis.py` - Analysis script
3. `sales_by_region.png` - Regional sales chart
4. `sales_by_product.png` - Product sales chart
5. `report.md` - Analysis summary

## Requirements

OmniBuilder should:
- Generate realistic sample data
- Calculate summary statistics
- Create matplotlib visualizations
- Write a markdown report with insights
