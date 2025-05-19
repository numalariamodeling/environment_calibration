import pandas as pd
import os
from glob import glob
import re

# Base directory
base_dir = "/home/upf3610/b1139/ipti_pmc/environment_calibration/simulations/output"

# DataFrames lists
translated_params_dfs = []
emod_best_dfs = []

# Process each LGA
for lga_path in glob(os.path.join(base_dir, "*", "LF_0")):
    full_folder = os.path.basename(os.path.dirname(lga_path))  # e.g. "Aiyedade_20250427_155803"
    
    # Extract clean LGA name: keep only before _20...
    lga_name = re.split(r'_20\d{6}.*$', full_folder)[0]

    translated_params_file = os.path.join(lga_path, "translated_params.csv")
    emod_best_file = os.path.join(lga_path, "emod.best.csv")

    # Load translated_params.csv
    if os.path.exists(translated_params_file):
        df_translated = pd.read_csv(translated_params_file)
        df_translated = df_translated.loc[:, ~df_translated.columns.str.contains("^Unnamed")]
        for col in ['unit_value', 'emod_value']:
            if col in df_translated.columns:
                df_translated[col] = df_translated[col].astype(str).str.extract(r'tensor\((.*?)\)').astype(float)
        df_translated["LGA"] = lga_name
        translated_params_dfs.append(df_translated)

    # Load emod.best.csv
    if os.path.exists(emod_best_file):
        df_emod = pd.read_csv(emod_best_file)
        df_emod = df_emod.loc[:, ~df_emod.columns.str.contains("^Unnamed")]
        df_emod["LGA"] = lga_name
        emod_best_dfs.append(df_emod)

# Combine and export
combined_translated_params = pd.concat(translated_params_dfs, ignore_index=True)
combined_emod_best = pd.concat(emod_best_dfs, ignore_index=True)

combined_translated_params.to_csv("combined_translated_params.csv", index=False)
combined_emod_best.to_csv("combined_emod_best.csv", index=False)