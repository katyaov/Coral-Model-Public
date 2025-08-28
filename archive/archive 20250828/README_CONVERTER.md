
# Coral-Model Old → New Input Converter

This creates **coral_data_and_custom_parameters_CONVERTED.xlsx** and **user_input_new.py** from one of your older `user_input.py` files.

## How to use

1) Upload one of your **old** `user_input.py` files here.
2) Run the following in a notebook cell:
```python
from convert_coral_inputs import convert
out_xlsx, out_py = convert(
    old_py_path="/mnt/data/OLD_USER_INPUT.py",   # <-- change to your uploaded file
    template_excel_path="/mnt/data/coral_data_and_custom_parameters.xlsx",
    out_excel_path="/mnt/data/coral_data_and_custom_parameters_CONVERTED.xlsx",
    out_user_input_path="/mnt/data/user_input_new.py"
)
out_xlsx, out_py
```
3) Download the two outputs and use them with your model.

The converter is permissive about variable names and will:
- Transfer benthic covers, rugosity, reef area/shape, years.
- Convert `dhw_years` and `cyclone_years` from relative to absolute years (using `year_start`), then write them into **DHW_Years** and **Cyclone_Years** sheets.
- Fill **Population_size_distribution**, **Partial_Mortality**, **Whole_Mortality**, and **Growth_Rates** if your old file included the corresponding `custom_*` lists/dicts.
- Generate a new `user_input_new.py` that matches your latest loader pattern and points to the converted Excel file.

If a field is missing in the old file, sensible defaults are used and any existing values already present in the template workbook are preserved unless explicitly replaced.
