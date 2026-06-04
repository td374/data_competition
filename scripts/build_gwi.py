# -*- coding: utf-8 -*-
"""
GWI (Greenwashing Index) Construction via Entropy-Weight Method
Combines 3 dimensions:
  1. ESG Text CFR (Commitment-Fulfillment Ratio) - from esg_text_analysis.py
  2. Financial Risk Score - from calc_financial_indicators.py  
  3. Remote Sensing Deviation (placeholder: NDVI deviation) - from GEE extraction

Output: GWI score per company per year, used as feature in default prediction model.
"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings("ignore")

def entropy_weight(df):
    """Calculate entropy weights for columns in df. Higher dispersion = higher weight."""
    df_clean = df.dropna()
    if len(df_clean) < 3:
        return pd.Series(1.0/len(df.columns), index=df.columns)
    
    # Normalize (min-max)
    norm = (df_clean - df_clean.min()) / (df_clean.max() - df_clean.min() + 1e-10)
    
    # Entropy
    n = len(norm)
    k = 1.0 / np.log(n)
    p = norm / norm.sum()
    e = -k * (p * np.log(p + 1e-10)).sum()
    
    # Weights
    d = 1 - e
    w = d / d.sum()
    return w

def build_gwi(financial_path, esg_path, remote_sensing_path=None, output_path=None):
    """
    Construct GWI from financial indicators, ESG text CFR, and optional remote sensing.
    
    financial_path: CSV with columns [code, year, z_score, current_ratio, ...]
    esg_path: CSV with columns [code, year, cfr, commitment_ratio, action_ratio, ...]
    remote_sensing_path: (optional) CSV with columns [code, year, ndvi_deviation, ...]
    """
    fin = pd.read_csv(financial_path, encoding="utf-8-sig") if os.path.exists(financial_path) else None
    esg = pd.read_csv(esg_path, encoding="utf-8-sig") if os.path.exists(esg_path) else None
    
    if fin is None and esg is None:
        raise FileNotFoundError("Need at least one of financial or ESG data files")
    
    # Merge available data
    if fin is not None and esg is not None:
        df = fin.merge(esg, on=["code", "year"], how="outer")
    elif fin is not None:
        df = fin.copy()
    else:
        df = esg.copy()
    
    # Add remote sensing features if available
    if remote_sensing_path and os.path.exists(remote_sensing_path):
        rs = pd.read_csv(remote_sensing_path, encoding="utf-8-sig")
        df = df.merge(rs, on=["code", "year"], how="left")
    
    # --- Dimension 1: Financial Risk (inverse: higher risk = higher greenwash suspicion) ---
    financial_cols = ["z_score", "current_ratio", "debt_ratio", "roa", "roe", 
                      "asset_turnover", "ocf_ratio", "profit_margin"]
    available_fin = [c for c in financial_cols if c in df.columns]
    
    if available_fin:
        # Invert Z-score, ROA, ROE (higher = better, so we want 1- to get risk direction)
        fin_df = df[available_fin].copy()
        for col in ["z_score", "roa", "roe", "profit_margin", "current_ratio", "ocf_ratio"]:
            if col in fin_df.columns:
                fin_df[col] = 1 / (1 + np.exp(fin_df[col]))  # sigmoid squash
        if "debt_ratio" in fin_df.columns:
            fin_df["debt_ratio"] = fin_df["debt_ratio"]  # Already risk-direction
        fin_weights = entropy_weight(fin_df)
        df["fin_risk_score"] = (fin_df * fin_weights).sum(axis=1)
    else:
        df["fin_risk_score"] = 0.5
    
    # --- Dimension 2: ESG Text Greenwash (low CFR = high greenwash suspicion) ---
    if "cfr" in df.columns:
        df["esg_greenwash_score"] = 1 - df["cfr"]  # Inverse: low CFR = more greenwash
    else:
        df["esg_greenwash_score"] = 0.5
    
    # --- Dimension 3: Remote Sensing Deviation (if available) ---
    rs_col = "ndvi_deviation" if "ndvi_deviation" in df.columns else None
    if rs_col:
        df["rs_deviation_score"] = df[rs_col].fillna(df[rs_col].median())
    else:
        df["rs_deviation_score"] = 0.5  # Placeholder
    
    # --- Combine into GWI ---
    gwi_cols = ["fin_risk_score", "esg_greenwash_score", "rs_deviation_score"]
    df_clean = df[gwi_cols].dropna()
    
    if len(df_clean) > 2:
        gwi_weights = entropy_weight(df_clean)
    else:
        gwi_weights = pd.Series([0.4, 0.4, 0.2], index=gwi_cols)
    
    print(f"GWI weights: {dict(gwi_weights.round(4))}")
    
    df["GWI"] = (df[gwi_cols].fillna(0.5) * gwi_weights).sum(axis=1)
    df["GWI"] = df["GWI"].clip(0, 1)  # Normalize to [0,1]
    
    # Risk level classification
    df["GWI_level"] = pd.cut(df["GWI"], bins=[0, 0.3, 0.5, 0.7, 1.0],
                             labels=["Low", "Medium-Low", "Medium-High", "High"])
    
    if output_path:
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"GWI saved to: {output_path}")
    
    return df

if __name__ == "__main__":
    print("GWI Construction Module Ready")
    print("="*50)
    print("Usage:")
    print("  df = build_gwi('financial_indicators.csv', 'esg_cfr.csv',")
    print("                  'ndvi_deviation.csv', 'gwi_output.csv')")
    print()
    print("GWI = w1 * FinancialRiskScore + w2 * ESG_GreenwashScore + w3 * RS_DeviationScore")
    print("Weights determined by entropy method (data-driven, no subjective bias).")
