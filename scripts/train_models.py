# -*- coding: utf-8 -*-
"""
Default Prediction Model Training Pipeline
Three-model comparison experiment:
  Model 1: Financial indicators only
  Model 2: Financial + ESG text features
  Model 3: Financial + ESG text + Remote sensing (full fusion)

Models: LightGBM + XGBoost with SHAP interpretation
Evaluation: AUC, F1, Precision, Recall on independent test set
"""
import pandas as pd, numpy as np, os, warnings, json
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (roc_auc_score, f1_score, precision_score, recall_score,
                              classification_report, confusion_matrix, roc_curve)
import lightgbm as lgb
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import seaborn as sns

OUT_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\outputs"
os.makedirs(os.path.join(OUT_DIR, "plots"), exist_ok=True)

# === Feature Groups ===
FINANCIAL_FEATURES = ["z_score", "current_ratio", "debt_ratio", "roa", "roe",
                      "asset_turnover", "ocf_ratio", "ocf_to_debt", "inv_turnover",
                      "ar_turnover", "profit_margin", "ocf_to_ni"]

ESG_FEATURES = ["cfr", "commitment_ratio", "action_ratio", "commitment_count", "action_count"]

RS_FEATURES = ["ndvi_deviation", "ndbi_deviation", "gwi"]  # added after GEE

def prepare_data(gwi_path, master_path):
    """Load GWI data and merge with company metadata (group labels)."""
    gwi = pd.read_csv(gwi_path, encoding="utf-8-sig")
    master = pd.read_csv(master_path, encoding="utf-8-sig")
    
    # Merge group info
    df = gwi.merge(master[["code", "industry", "group"]], on="code", how="left")
    
    # Create default label: companies in "独立测试集" group are known defaulters (2022-2025)
    # Also mark companies with known violations as positive cases
    df["default_label"] = 0
    df.loc[df["group"] == "独立测试集", "default_label"] = 1
    
    return df

def train_models(df, feature_sets, model_names, test_size=0.2):
    """Train and compare models with different feature sets."""
    results = {}
    
    # Split: training set (not 独立测试集) + test set (独立测试集)
    train_df = df[df["group"] != "独立测试集"].copy()
    test_df = df[df["group"] == "独立测试集"].copy()
    
    # If no independent test set, use stratified split
    if len(test_df) < 3:
        print("Warning: small independent test set, using stratified split")
        train_df, test_df = train_test_split(df, test_size=test_size, stratify=df["default_label"], random_state=42)
    
    for name, features in zip(model_names, feature_sets):
        available = [f for f in features if f in df.columns]
        if not available:
            print(f"  {name}: No features available, skipping")
            continue
        
        X_train = train_df[available].fillna(train_df[available].median())
        y_train = train_df["default_label"]
        X_test = test_df[available].fillna(test_df[available].median())
        y_test = test_df["default_label"]
        
        print(f"\n{'='*50}")
        print(f"Model: {name} ({len(available)} features)")
        print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        print(f"Pos rate: train={y_train.mean():.3f}, test={y_test.mean():.3f}")
        
        # --- LightGBM ---
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            min_child_samples=20, subsample=0.8, colsample_bytree=0.8,
            random_state=42, verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        y_pred_lgb = lgb_model.predict(X_test)
        y_prob_lgb = lgb_model.predict_proba(X_test)[:, 1]
        
        # --- XGBoost ---
        xgb_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, verbosity=0
        )
        xgb_model.fit(X_train, y_train)
        y_pred_xgb = xgb_model.predict(X_test)
        y_prob_xgb = xgb_model.predict_proba(X_test)[:, 1]
        
        # --- Ensemble (average probabilities) ---
        y_prob_ens = (y_prob_lgb + y_prob_xgb) / 2
        y_pred_ens = (y_prob_ens >= 0.5).astype(int)
        
        # --- Metrics ---
        for label, yp, yprob in [("LightGBM", y_pred_lgb, y_prob_lgb),
                                  ("XGBoost", y_pred_xgb, y_prob_xgb),
                                  ("Ensemble", y_pred_ens, y_prob_ens)]:
            auc = roc_auc_score(y_test, yprob)
            f1 = f1_score(y_test, yp, zero_division=0)
            prec = precision_score(y_test, yp, zero_division=0)
            rec = recall_score(y_test, yp, zero_division=0)
            
            results[f"{name}_{label}"] = {
                "features": len(available),
                "AUC": round(auc, 4),
                "F1": round(f1, 4),
                "Precision": round(prec, 4),
                "Recall": round(rec, 4),
                "train_n": len(X_train),
                "test_n": len(X_test),
            }
            print(f"  {label:10s} AUC={auc:.4f} F1={f1:.4f} P={prec:.4f} R={rec:.4f}")
        
        # Store best model for SHAP
        results[f"{name}_best_model"] = lgb_model
        results[f"{name}_X_train"] = X_train
        results[f"{name}_X_test"] = X_test
    
    return results

def plot_comparison(results, output_path):
    """Plot model comparison bar chart."""
    models = [k for k in results if isinstance(results[k], dict) and "AUC" in k]
    if not models:
        return
    
    df_plot = pd.DataFrame([{"model": m, **results[m]} for m in models])
    
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(df_plot))
    width = 0.2
    
    for i, metric in enumerate(["AUC", "F1", "Precision", "Recall"]):
        ax.bar([xi + i*width for xi in x], df_plot[metric], width, label=metric)
    
    ax.set_xticks([xi + 1.5*width for xi in x])
    ax.set_xticklabels(df_plot["model"], rotation=45, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison: Default Prediction Performance")
    ax.legend()
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {output_path}")

def shap_analysis(model, X_train, X_test, feature_names, output_path):
    """SHAP feature importance analysis."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"SHAP plot saved: {output_path}")

if __name__ == "__main__":
    print("Model Training Pipeline Ready")
    print("="*50)
    print("Feature Sets:")
    print(f"  Financial: {FINANCIAL_FEATURES}")
    print(f"  ESG Text:  {ESG_FEATURES}")
    print(f"  Remote:    {RS_FEATURES}")
    print()
    print("Usage:")
    print("  df = prepare_data('gwi_output.csv', 'master_company_list.csv')")
    print("  results = train_models(df,")
    print("      [FINANCIAL_FEATURES, FINANCIAL+ESG, FINANCIAL+ESG+RS],")
    print("      ['Model1_FinOnly', 'Model2_Fin+ESG', 'Model3_Fin+ESG+RS'])")
    print("  plot_comparison(results, 'plots/model_comparison.png')")
