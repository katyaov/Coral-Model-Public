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
    create_new_python_file(old_params, out_user_input_path, template_user_input_path)
    
    return out_excel_path, out_user_input_path

def extract_parameters_from_old_file(file_path: str) -> Dict[str, Any]:
    """Extract parameter values from the old Python file."""
    params = {}
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Execute the old file to get the variables
        # This is safe since we're working with known user input files
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
    
    # Define parameter mappings based on common coral model parameters
    # This mapping may need adjustment based on your specific parameter names
    parameter_mappings = {
        # Environmental parameters
        'temperature': ('Environmental', 'Temperature'),
        'temp': ('Environmental', 'Temperature'),
        'salinity': ('Environmental', 'Salinity'),
        'pH': ('Environmental', 'pH'),
        'light': ('Environmental', 'Light'),
        'irradiance': ('Environmental', 'Light'),
        
        # Coral parameters
        'coral_cover': ('Coral', 'Cover'),
        'growth_rate': ('Coral', 'Growth_Rate'),
        'mortality_rate': ('Coral', 'Mortality_Rate'),
        'bleaching_threshold': ('Coral', 'Bleaching_Threshold'),
        
        # Model parameters
        'time_steps': ('Model', 'Time_Steps'),
        'simulation_years': ('Model', 'Years'),
        'iterations': ('Model', 'Iterations'),
    }
    
    # Apply mappings
    for old_param, value in old_params.items():
        if old_param.lower() in parameter_mappings:
            sheet_name, column_name = parameter_mappings[old_param.lower()]
            
            if sheet_name in updated_data:
                df = updated_data[sheet_name]
                
                # Try to find and update the parameter
                if column_name in df.columns:
                    # Update the first row with the new value
                    df.loc[0, column_name] = value
                elif 'Parameter' in df.columns and 'Value' in df.columns:
                    # Alternative structure: Parameter-Value pairs
                    param_row = df[df['Parameter'] == column_name]
                    if not param_row.empty:
                        df.loc[param_row.index[0], 'Value'] = value
                    else:
                        # Add new parameter if not found
                        new_row = pd.DataFrame({'Parameter': [column_name], 'Value': [value]})
                        updated_data[sheet_name] = pd.concat([df, new_row], ignore_index=True)
        else:
            # Handle unmapped parameters - add to a general 'Custom' sheet if it exists
            if 'Custom' in updated_data:
                df = updated_data['Custom']
                if 'Parameter' in df.columns and 'Value' in df.columns:
                    new_row = pd.DataFrame({'Parameter': [old_param], 'Value': [value]})
                    updated_data['Custom'] = pd.concat([df, new_row], ignore_index=True)
    
    return updated_data

def save_excel_file(excel_data: Dict[str, pd.DataFrame], output_path: str):
    """Save the updated Excel file."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in excel_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Excel file saved to: {output_path}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")

def create_new_python_file(old_params: Dict[str, Any], output_path: str, template_python_path: str = "user_inputs.py"):
    """Create the new Python user input file with exact same structure as template."""
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Read the template Python file to preserve exact structure and formatting
        with open(template_python_path, 'r') as f:
            template_content = f.read()
        
        # Replace the Excel file name in the template to match the output Excel file
        excel_filename = os.path.basename(output_path).replace('.py', '.xlsx')
        template_content = template_content.replace(
            "excel_path = 'coral_data_and_custom_parameters.xlsx'",
            f"excel_path = '{excel_filename}'"
        )
        
        # Create new content by replacing parameter values in the template
        new_content = replace_values_in_template(template_content, old_params)
        
        # Write the new file
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
        'dhw_years', 'cyclone_years', 'growth_rate_dict'
    }
    
    # For each parameter in the old file, try to find and replace it in the template
    for param_name, param_value in old_params.items():
        
        # Skip variables that should be loaded from Excel - CHECK THIS FIRST!
        if param_name in excel_loaded_vars:
            print(f"Skipping {param_name} - should load from Excel")
            continue
            
        # Look for simple variable assignments only
        escaped_name = re.escape(param_name)
        
        # Check if this line exists and is a simple assignment
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            # Only match simple assignments that don't start with {, [, or (
            if re.match(r'^\s*' + escaped_name + r'\s*=\s*[^{\[\(]', line):
                print(f"Replacing {param_name} with {param_value}")
                
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
                print(f"  New line: {lines[i]}")
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
        template_user_input_path="user_inputs.py"  # Your template Python file
    )
    print(f"Conversion complete!")
    print(f"Excel: {out_xlsx}")
    print(f"Python: {out_py}")