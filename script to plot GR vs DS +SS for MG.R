#19032025
#script to plot GR vs DS +SS for MG
#
# Load necessary libraries
library(readxl)
library(ggplot2)
library(ggpmisc)

# Define the file path
file_path <- "C:/Users/uqrbutto/OneDrive - The University of Queensland/PhD_proj_pollution_on_coral_reefs/Sediment model extension/Processes where sediment impacts v2 13032025.xlsx"

# Import the first sheet of the Excel file
data <- read_excel(file_path, sheet = 1)



# Plot DS sediment exposure vs raw growth rate for each reef type with linear fit and equation
plot_ds <- function(data) {
  ggplot(data, aes(x = `DS sedi exposure (g/cm2/day)`, y = `gr cm/month OR cm2/mon`, color = `reef type`)) +
    geom_point() +
    geom_smooth(method = "lm", se = FALSE) +
    facet_wrap(~ `morph group`) +
    labs(x = "DS sediment exposure (g/cm2/day)", y = "Growth Rate (cm/month or cm2/month)") +
    theme_minimal() +
    stat_poly_eq(aes(label = paste(..eq.label.., ..rr.label.., sep = "~~~")), 
                 formula = y ~ x, parse = TRUE)
}

# Plot SS sediment exposure vs raw growth rate for each reef type with linear fit and equation
plot_ss <- function(data) {
  ggplot(data, aes(x = `SS sediment exposure mg/l`, y = `gr cm/month OR cm2/mon`, color = `reef type`)) +
    geom_point() +
    geom_smooth(method = "lm", se = FALSE) +
    facet_wrap(~ `morph group`) +
    labs(x = "SS sediment exposure (mg/l)", y = "Growth Rate (cm/month or cm2/month)") +
    theme_minimal() +
    stat_poly_eq(aes(label = paste(..eq.label.., ..rr.label.., sep = "~~~")), 
                 formula = y ~ x, parse = TRUE)
}

# Plot for reef type = clear water and morph group = O
plot_clear_water <- function(data) {
  subset_data <- subset(data, `reef type` == "clear water" & `morph group` == "O")
  ggplot(subset_data, aes(x = `DS sedi exposure (g/cm2/day)`, y = `raw growth rate`)) +
    geom_point() +
    geom_smooth(method = "lm", se = FALSE) +
    labs(x = "DS sediment exposure (g/cm2/day)", y = "g (change in buoyant mass * proportion of live coral tissue cover of each colony)") +
    theme_minimal() +
    stat_poly_eq(aes(label = paste(..eq.label.., ..rr.label.., sep = "~~~")), 
                 formula = y ~ x, parse = TRUE)
}

# Execute the plotting functions
plot_ds(data)
plot_ss(data)

plot_clear_water(data)