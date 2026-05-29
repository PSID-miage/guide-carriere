import pandas as pd
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full paths to the CSV files
codes_file = os.path.join(script_dir, "unix_referentiel_code_rome_v460_utf8.csv")
appel_file = os.path.join(script_dir, "unix_referentiel_appellation_v460_utf8.csv")

# Read the CSV file with debugging
codes = pd.read_csv(codes_file, sep=";", encoding="utf-8")
print("Columns in 'codes':", codes.columns)  # Debugging: Check column names

# Clean column names (strip whitespace)
codes.columns = codes.columns.str.strip()

# Check if 'code_rome' exists
if 'code_rome' not in codes.columns:
    raise ValueError("'code_rome' column not found in the CSV file!")

# Filter rows where 'code_rome' starts with "M18"
mask = codes["code_rome"].str.startswith("M18")  # M18 = SI/Tech
print(codes[mask][["code_rome", "libelle_rome"]])

# For all appellations linked to each M18 code
appel = pd.read_csv(appel_file, sep=";", encoding="utf-8")
appel.columns = appel.columns.str.strip()  # Clean column names
m18_codes = codes[mask]["code_rome"].tolist()
print(appel[appel["code_rome"].isin(m18_codes)][["code_rome", "libelle_appellation"]])