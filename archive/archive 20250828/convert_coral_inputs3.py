import pandas as pd
import shutil
import os
import re
from typing import Tuple, Dict, Any

def convert(old_py_path: str, template_excel_path: str, out_excel_path: str, out_user_input_path: str, template_user_input_path: str = "user_inputs.py") -> Tuple[str, str]:
    """
    Convert old Python user input file to new Excel + Python format.
    
    Args:
        old_py_path: Path to the old Python user input file
        template_excel_path: Path to the template Excel file
        out_excel_path: Output path for the new Excel file
        out_user_input_path: Output path for the new Python file
        template_user_input_path: Path to the template Python user input file
    
    Returns:
        Tuple of (excel_path, python_path)
    """
    
    # Read the old Python file and extract variables
    old_params = extract_parameters_from_old_file(old_py_path)
    
    # Load the template Excel file
    excel_data = load_excel_template(template_excel_path)
    
    # Map old parameters to new Excel structure
    updated_excel_data = map_parameters_to_excel(old_params, excel_data)
    
    # Save the updated Excel file
    save_excel_file(updated_excel_data, out_excel_path)
    
    # Create the new Python user input file using the template structure
    create_new_python_file(old_params, out_user_input_path, template_user_input_path, out_excel_path)
    
    return out_excel_path, out_user_input_path

def extract_parameters_from_old_file(file_path: str) -> Dict[str, Any]:
    """Extract parameter values from the old Python file."""
    params = {}
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Execute the old file to get the variables
        exec_globals = {}
        exec(content, exec_globals)
        
        # Filter out built-in variables and functions
        for key, value in exec_globals.items():
            if not key.startswith('__') and not callable(value):
                params[key] = value
                
    except Exception as e:
        print(f"Warning: Could not extract parameters from {file_path}: {e}")
        
    return params

def load_excel_template(template_path: str) -> Dict[str, pd.DataFrame]:
    """Load all sheets from the Excel template."""
    try:
        excel_file = pd.ExcelFile(template_path)
        sheets = {}
        for sheet_name in excel_file.sheet_names:
            sheets[sheet_name] = pd.read_excel(template_path, sheet_name=sheet_name)
        return sheets
    except Exception as e:
        print(f"Error loading Excel template: {e}")
        return {}

def map_parameters_to_excel(old_params: Dict[str, Any], excel_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Map old parameters to the Excel sheets structure."""
    
    # Create a copy of the excel data to modify
    updated_data = {}
    for sheet_name, df in excel_data.items():
        updated_data[sheet_name] = df.copy()
    
    # 1. Map real_data to Real_Cover sheet
    if 'real_data' in old_params and 'Real_Cover' in updated_data:
        real_data = old_params['real_data']
        new_real_cover = pd.DataFrame({
            'Year': real_data.get('Year', []),
            'RealBranching_Area (%)': real_data.get('RealBranching_Area (%)', []),
            'RealFoliose_Area (%)': real_data.get('RealFoliose_Area (%)', []),
            'RealOther_Area (%)': real_data.get('RealOther_Area (%)', [])
        })
        updated_data['Real_Cover'] = new_real_cover
    
    # 2. Map custom_PSD_T0 to Population_size_distribution sheet
    if 'custom_PSD_T0' in old_params and 'Population_size_distribution' in updated_data:
        psd_data = old_params['custom_PSD_T0']
        new_psd = pd.DataFrame({
            'Bins': psd_data.get('Bins', []),
            'Branching': psd_data.get('Branching', []),
            'Foliose': psd_data.get('Foliose', []),
            'Other': psd_data.get('Other', [])
        })
        updated_data['Population_size_distribution'] = new_psd
    
    # 3. Map partial mortality rates to Partial_Mortality sheet
    if ('custom_partial_mortality_rates_branching' in old_params and 
        'custom_partial_mortality_rates_foliose' in old_params and 
        'custom_partial_mortality_rates_other' in old_params and 
        'Partial_Mortality' in updated_data):
        
        new_pmr = pd.DataFrame({
            'Branching_PMR': old_params['custom_partial_mortality_rates_branching'],
            'Foliose_PMR': old_params['custom_partial_mortality_rates_foliose'],
            'Other_PMR': old_params['custom_partial_mortality_rates_other']
        })
        updated_data['Partial_Mortality'] = new_pmr
    
    # 4. Map whole colony mortality rates to Whole_Mortality sheet
    if ('custom_wcm_branching' in old_params and 
        'custom_wcm_foliose' in old_params and 
        'custom_wcm_other' in old_params and 
        'Whole_Mortality' in updated_data):
        
        new_wcm = pd.DataFrame({
            'Branching_WCM': old_params['custom_wcm_branching'],
            'Foliose_WCM': old_params['custom_wcm_foliose'],
            'Other_WCM': old_params['custom_wcm_other']
        })
        updated_data['Whole_Mortality'] = new_wcm
    
    # 5. Map growth rates to Growth_Rates sheet
    if ('custom_growth_rate_branching' in old_params and 
        'custom_growth_rate_foliose' in old_params and 
        'custom_growth_rate_other' in old_params and 
        'Growth_Rates' in updated_data):
        
        new_growth = pd.DataFrame({
            'CoralType': ['Branching', 'Foliose', 'Other'],
            'GrowthRate_cm_per_year': [
                old_params['custom_growth_rate_branching'],
                old_params['custom_growth_rate_foliose'],
                old_params['custom_growth_rate_other']
            ]
        })
        updated_data['Growth_Rates'] = new_growth
    
    # 6. Map dhw_years to DHW_Years sheet
    if 'dhw_years' in old_params and 'year_start' in old_params and 'DHW_Years' in updated_data:
        dhw_data = old_params['dhw_years']
        year_start = old_params['year_start']
        
        # Convert relative years back to absolute years
        dhw_records = []
        for relative_year, dhw_value in dhw_data.items():
            absolute_year = year_start + relative_year
            dhw_records.append({'Year': absolute_year, 'DHW': dhw_value})
        
        new_dhw = pd.DataFrame(dhw_records)
        updated_data['DHW_Years'] = new_dhw
    
    # 7. Map cyclone_years to Cyclone_Years sheet
    if 'cyclone_years' in old_params and 'year_start' in old_params and 'Cyclone_Years' in updated_data:
        cyclone_data = old_params['cyclone_years']
        year_start = old_params['year_start']
        
        # Convert relative years back to absolute years
        cyclone_records = []
        for relative_year, cyclone_info in cyclone_data.items():
            absolute_year = year_start + relative_year
            severity, distance = cyclone_info
            cyclone_records.append({
                'Year': absolute_year, 
                'Severity': severity, 
                'Distance_km': distance
            })
        
        new_cyclone = pd.DataFrame(cyclone_records)
        updated_data['Cyclone_Years'] = new_cyclone
    
    # Handle other simple parameter mappings
    parameter_mappings = {
        'temperature': ('Environmental', 'Temperature'),
        'temp': ('Environmental', 'Temperature'),
        'salinity': ('Environmental', 'Salinity'),
        'pH': ('Environmental', 'pH'),
        'light': ('Environmental', 'Light'),
        'irradiance': ('Environmental', 'Light'),
        'coral_cover': ('Coral', 'Cover'),
        'growth_rate': ('Coral', 'Growth_Rate'),
        'mortality_rate': ('Coral', 'Mortality_Rate'),
        'bleaching_threshold': ('Coral', 'Bleaching_Threshold'),
        'time_steps': ('Model', 'Time_Steps'),
        'simulation_years': ('Model', 'Years'),
        'iterations': ('Model', 'Iterations'),
    }
    
    # Apply simple parameter mappings
    for old_param, value in old_params.items():
        if old_param.lower() in parameter_mappings:
            sheet_name, column_name = parameter_mappings[old_param.lower()]
            
            if sheet_name in updated_data:
                df = updated_data[sheet_name]
                
                if column_name in df.columns:
                    df.loc[0, column_name] = value
                elif 'Parameter' in df.columns and 'Value' in df.columns:
                    param_row = df[df['Parameter'] == column_name]
                    if not param_row.empty:
                        df.loc[param_row.index[0], 'Value'] = value
                    else:
                        new_row = pd.DataFrame({'Parameter': [column_name], 'Value': [value]})
                        updated_data[sheet_name] = pd.concat([df, new_row], ignore_index=True)
        else:
            # Handle unmapped parameters - add to Custom sheet if it exists
            if 'Custom' in updated_data:
                df = updated_data['Custom']
                if 'Parameter' in df.columns and 'Value' in df.columns:
                    new_row = pd.DataFrame({'Parameter': [old_param], 'Value': [value]})
                    updated_data['Custom'] = pd.concat([df, new_row], ignore_index=True)
    
    return updated_data

def save_excel_file(excel_data: Dict[str, pd.DataFrame], output_path: str):
    """Save the updated Excel file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in excel_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Excel file saved to: {output_path}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")

def create_new_python_file(old_params: Dict[str, Any], output_path: str, template_python_path: str = "user_inputs.py", out_excel_path: str = None):
    """Create the new Python user input file with exact same structure as template."""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(template_python_path, 'r') as f:
            template_content = f.read()
        
        # Replace the Excel file name in the template to match the output Excel file
        if out_excel_path:
            excel_filename = os.path.basename(out_excel_path)
            template_content = template_content.replace(
                "excel_path = 'coral_data_and_custom_parameters.xlsx'",
                f"excel_path = '{excel_filename}'"
            )
        
        # Create new content by replacing parameter values in the template
        new_content = replace_values_in_template(template_content, old_params)
        
        with open(output_path, 'w') as f:
            f.write(new_content)
        print(f"Python file saved to: {output_path}")
        
    except Exception as e:
        print(f"Error creating Python file: {e}")

def replace_values_in_template(template_content: str, old_params: Dict[str, Any]) -> str:
    """Replace values in the template while preserving exact formatting."""
    
    new_content = template_content
    
    # Variables that should be loaded from Excel, NOT replaced with hardcoded values
    excel_loaded_vars = {
        'custom_PSD_T0', 'custom_partial_mortality_rates_branching', 
        'custom_partial_mortality_rates_foliose', 'custom_partial_mortality_rates_other',
        'custom_wcm_branching', 'custom_wcm_foliose', 'custom_wcm_other',
        'custom_growth_rate_branching', 'custom_growth_rate_foliose', 'custom_growth_rate_other',
        'dhw_years', 'cyclone_years', 'growth_rate_dict', 'MaxYear'
    }
    
    # For each parameter in the old file, try to find and replace it in the template
    for param_name, param_value in old_params.items():
        
        # Skip variables that should be loaded from Excel
        if param_name in excel_loaded_vars:
            continue
            
        # Look for simple variable assignments only
        escaped_name = re.escape(param_name)
        
        # Check if this line exists and is a simple assignment
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            # Only match simple assignments that don't start with {, [, or (
            if re.match(r'^\s*' + escaped_name + r'\s*=\s*[^{\[\(]', line):
                # Create replacement based on the type of value
                if isinstance(param_value, str):
                    replacement_value = '"' + param_value + '"'
                elif isinstance(param_value, (list, tuple)):
                    replacement_value = repr(param_value)
                else:
                    replacement_value = str(param_value)
                
                # Replace the entire line while preserving indentation
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f"{indent}{param_name} = {replacement_value}"
                break
        
        new_content = '\n'.join(lines)
    
    return new_content

# Example usage
if __name__ == "__main__":
    # Test the conversion
    out_xlsx, out_py = convert(
        old_py_path="user_inputs_old_4-1.py",
        template_excel_path="coral_data_and_custom_parameters.xlsx",
        out_excel_path="coral_data_and_custom_parameters_converted.xlsx",
        out_user_input_path="user_inputs_converted.py",
        template_user_input_path="user_inputs.py"
    )
    print(f"Conversion complete!")
    print(f"Excel: {out_xlsx}")
    print(f"Python: {out_py}")