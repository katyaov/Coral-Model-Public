def plot_bubble_chart_from_dataframe(df, title, category_col='MG', year_interval=4, bubble_scale=100, parallel_offset = 1.2, figsize=(18, 12), x_spacing=1.5, y_spacing=5):
    """
    Create a bubble chart showing population distribution by category over time.
    
    Parameters:
    - df: DataFrame with columns for category, year, and bin data (percentages)
    - y_label: Label for y-axis (default: "Bin Size")
    - y_unit: Unit for y-axis (default: "cm")
    - category_col: Column name for categories (default: 'MG')
    - year_interval: Select every Nth year (default: 4 for every 4th year)
    - year_start: Starting year for converting model years to actual years (default: 2000)
    - bubble_scale: Multiplier for bubble sizes (default: 100)
    
    Expected DataFrame structure:
    - Column 0: Category (MG)
    - Column 1: Year (model years: 0, 1, 2, 3, ...)
    - Columns 2+: Bin diameter columns (5, 10, 15, ..., 100) with percentages
    """
    
    # Configuration parameters
    parallel_offset = parallel_offset  # Horizontal offset between categories
    
    # Get actual bin diameter columns (columns 2 onwards contain bin data)
    bin_columns = df.columns[2:].tolist()  # Skip category and year columns
    
    # Extract bin diameters from column names (assuming they contain numeric values)
    bin_diameters = []
    for col in bin_columns:
        # Extract numeric value from column name (e.g., "Bin_5" -> 5, "5cm" -> 5, etc.)
        import re
        numbers = re.findall(r'\d+', str(col))
        if numbers:
            bin_diameters.append(float(numbers[0]))
        else:
            # If no number found, use column index * 5 (assuming 5cm increments)
            bin_diameters.append((len(bin_diameters)) * 5 + 5)
    
    MaxBinId = len(bin_diameters)
    
    # Get unique years and categories from the data
    if 'Year' in df.columns:
        all_years_list = sorted(df['Year'].unique().tolist())
    else:
        all_years_list = [0, 4, 7, 11]
    
    # Select every Nth year to reduce clutter - filter by year values, not array indices
    if year_interval > 1:
        # Select years that are multiples of the interval
        years = [year for year in all_years_list if year % year_interval == 0]
    else:
        # If interval is 1, use all years
        years = all_years_list.copy()
    
    print(f"All years in data: {all_years_list}")
    print(f"Selected years (multiples of {year_interval}): {years}")
    
    # Convert model years to actual years
    actual_years = [year + year_start for year in years]
    print(f"Actual years for display: {actual_years}")
    
    categories = sorted(df[category_col].unique()) if category_col in df.columns else ['Branching', 'Foliose', 'Other']
    
    # Color schemes for each category
    color_palette = ["#1F77B4", "#C026D3", "#FF7F0E"]  # blue, fuchsia, orange
    colors = {}
    for i, category in enumerate(categories):
        base_color = color_palette[i % len(color_palette)]
        colors[category] = {
            'mean': base_color,
            'std': base_color + '40'  # Add transparency for std
        }
    
    # Calculate category offsets for parallel display
    category_offsets = {}
    if len(categories) == 1:
        category_offsets[categories[0]] = 0
    elif len(categories) == 2:
        category_offsets[categories[0]] = -parallel_offset/2
        category_offsets[categories[1]] = parallel_offset/2
    else:  # 3 or more categories
        for i, cat in enumerate(categories):
            category_offsets[cat] = (i - (len(categories)-1)/2) * parallel_offset
    
    # Prepare data for plotting
    plot_data = []
    
    for category in categories:
        for model_year in years:  # Use model years for filtering data
            actual_year = model_year + year_start  # Convert to actual year for positioning
            # Filter data for this category and model year
            year_df = df[(df[category_col] == category) & (df['Year'] == model_year)]
            
            if not year_df.empty:
                # Get bin data (columns 2 onwards contain the percentage data)
                bin_data = year_df.iloc[:, 2:]  # All bin columns
                
                # Calculate mean and std for each bin across all rows for this category/year
                mean_values = bin_data.mean(axis=0)
                std_values = bin_data.std(axis=0)
                
                # Create data points for each bin using actual bin diameters
                for bin_idx, (col_name, mean_val, std_val) in enumerate(zip(bin_columns, mean_values, std_values)):
                    if bin_idx < len(bin_diameters):
                        # Convert to float and check if valid
                        try:
                            mean_val = float(mean_val) if pd.notna(mean_val) else 0
                            std_val = float(std_val) if pd.notna(std_val) else 0
                        except (ValueError, TypeError):
                            mean_val = 0
                            std_val = 0
                        
                        # Always define position variables
                        x_pos = actual_year + category_offsets[category]  # Use actual year for positioning
                        y_pos = bin_diameters[bin_idx]  # Use actual bin diameter from column
                        
                        if mean_val > 0:
                            # Add mean point (main bubble)
                            plot_data.append({
                                'x': x_pos,
                                'y': y_pos,
                                'size': mean_val,
                                'color': colors[category]['mean'],
                                'category': category,
                                'year': actual_year,  # Store actual year
                                'type': 'mean',
                                'bin_idx': bin_idx
                            })
                        
                        # Add std point (background shading) if std exists
                        if std_val > 0:
                            plot_data.append({
                                'x': x_pos,
                                'y': y_pos,
                                'size': std_val,
                                'color': colors[category]['std'],
                                'category': category,
                                'year': actual_year,  # Store actual year
                                'type': 'std',
                                'bin_idx': bin_idx
                            })
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Group data by position for proper std shading around mean
    position_data = {}
    for point in plot_data:
        key = (point['x'], point['y'], point['category'])
        if key not in position_data:
            position_data[key] = {'mean': None, 'std': None}
        position_data[key][point['type']] = point
    
    # Plot standard deviation as shading around mean bubbles
    for (x, y, category), data in position_data.items():
        if data['mean'] is not None:
            mean_point = data['mean']
            
            # Plot mean bubble
            ax.scatter(
                mean_point['x'], 
                mean_point['y'], 
                s=float(mean_point['size']) * bubble_scale,  # Ensure float conversion
                c=mean_point['color'],
                alpha=0.8,
                linewidth=0.5,
                edgecolors='black',
                zorder=2,
                label=f'{category}' if mean_point['bin_idx'] == 0 and mean_point['year'] == actual_years[0] else ""
            )
            
            # Plot std shading around the mean if std data exists
            if data['std'] is not None:
                std_point = data['std']
                # Create larger bubble for std shading
                std_size = float(mean_point['size']) + float(std_point['size'])  # Ensure float conversion
                
                ax.scatter(
                    std_point['x'], 
                    std_point['y'], 
                    s=std_size * bubble_scale,  # Use configurable scale factor
                    c=std_point['color'],
                    alpha=0.2,  # Very light for background
                    edgecolors='none',
                    zorder=1
                )
    
    # Add vertical lines to separate years (optional) - position at actual years
    if len(actual_years) > 1:
        for i in range(len(actual_years)-1):
            separator_x = (actual_years[i] + actual_years[i+1]) / 2
            ax.axvline(x=separator_x, color='lightgray', linestyle='--', alpha=0.5)
    
    # Customize plot appearance
    ax.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax.set_ylabel(f'Bin diameter (cm)', fontsize=14, fontweight='bold')
    
    # Set x-axis ticks and labels with actual years - more robust approach
    ax.set_xticks(actual_years)
    
    # Create distinct labels for each year
    year_labels = []
    for actual_year in actual_years:
        year_labels.append(str(int(actual_year)))
    
    ax.set_xticklabels(year_labels, rotation=0, ha='center')
    
    # Force the x-axis to show the full range with proper spacing
    if len(actual_years) > 1:
        year_span = max(actual_years) - min(actual_years)
        margin = max(1, year_span * 0.1)  # 10% margin
        ax.set_xlim(min(actual_years) - margin, max(actual_years) + margin)
    else:
        ax.set_xlim(actual_years[0] - 1, actual_years[0] + 1)
    
    # Ensure ticks are visible and properly spaced
    ax.tick_params(axis='x', labelsize=12)
    
    # Update title to reflect actual year range
    if len(actual_years) > 1:
        year_range = f"({actual_years[0]}-{actual_years[-1]})"
    else:
        year_range = f"({actual_years[0]})"
    
    ax.set_title(f'{title} by Category Over Time {year_range}\n(Bubble size represents {title})', fontsize=16, fontweight='bold', pad=20)

# Set y-axis to show actual bin diameters with custom spacing
    if len(bin_diameters) > 0:
        ax.set_ylim(min(bin_diameters) - y_spacing, max(bin_diameters) + y_spacing)
        # Use actual bin diameters for y-axis ticks
        ax.set_yticks(bin_diameters)
        ax.set_yticklabels([f'{int(diameter)}' for diameter in bin_diameters]) 

    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Create legend
    legend_elements = []
    for category in categories:
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor=colors[category]['mean'], 
                                        markersize=10, label=f'{category}',
                                        markeredgecolor='black', markeredgewidth=0.5))
    
    # Add legend with better positioning
    cat_legend = ax.legend(
    handles=legend_elements,
    loc='upper right',
    bbox_to_anchor=(0.99, 1.00),   # (x, y) in axes coords
    bbox_transform=ax.transAxes,   # interpret bbox in axes coords
    frameon=True,
    fancybox=True,
    shadow=True,
    fontsize=12
)

    # Bubble size legend: collect the sizes used for mean bubbles
    _used_sizes = [p['size'] for p in plot_data if p['type'] == 'mean' and p['size'] > 0]

    if _used_sizes:
        vmin = float(min(_used_sizes))
        vmax = float(max(_used_sizes))
    
        # dynamic base = 1/5 of max bubble value
        base = max(vmax / 5.0, 1e-12)
    
        # pick 3 representative values between vmin and vmax
        raw_ticks = np.linspace(vmin, vmax, 3)
    
        # --- neat rounding: choose granularity to keep ~3 significant digits ---
        exp = int(np.floor(np.log10(base)))         # order of magnitude of base
        gran = 10 ** max(exp - 2, 0)                # e.g. base=17729 -> exp=4 -> gran=10**2=100
    
        # snap to nearest multiple of gran
        tick_vals = np.round(raw_ticks / gran) * gran
        tick_vals = np.array(sorted(set(tick_vals)))
        tick_vals[tick_vals <= 0] = gran  # avoid zero-size markers
    
        # fallback if rounding collapsed distincts
        if tick_vals.size < 3:
            mids = [vmin, (vmin + vmax)/2.0, vmax]
            tick_vals = np.array(sorted(set(np.round(np.array(mids)/gran) * gran)))
            tick_vals[tick_vals <= 0] = gran

    # build legend handles with SAME size mapping (s = value * bubble_scale)
    size_handles = [
        ax.scatter([], [], s=float(val) * bubble_scale, color='black', alpha=0.35, edgecolors='black')
        for val in tick_vals
    ]

    # pretty labels: integers with commas when gran >= 1; otherwise sensible decimals
    def _fmt(v):
        if gran >= 1:
            return f"{int(v):,}"
        # decimals: number of places based on gran (e.g., gran=0.01 -> 2 dp)
        places = max(0, int(np.ceil(-np.log10(gran))))
        return f"{v:.{places}f}"
        
    size_labels = [_fmt(val) for val in tick_vals]

    size_legend = ax.legend(
        size_handles, size_labels,
        title=f"{title} scale",
        loc="upper right",
        bbox_to_anchor=(0.99, 0.89),      # same x, lower y (under the category legend)
        bbox_transform=ax.transAxes,
        frameon=True, fancybox=True, shadow=False,
        fontsize=11,
        title_fontsize=12,
        borderpad=1.4,      # ↑ makes the legend box itself roomier
        labelspacing=1.5,
        handlelength=2.2,
        handletextpad=0.8,
        borderaxespad=0.0
)
    # keep both legends
    ax.add_artist(cat_legend)

    # Define the graph directory path
    graph_dir = r'output/figures'

    # Save the combined plot to the specified folder
    graph_path = os.path.join(graph_dir, f'{title} bubble_graph.png')
    plt.savefig(graph_path)

    # Adjust layout and display
    plt.tight_layout()
    plt.show()
    
    
    return fig, ax
