# -*- coding: utf-8 -*-
"""
================================================================================
 任务1：财务12个预警指标批量计算脚本
 多模态漂绿识别与信贷风险预警研究
================================================================================
 输入：financial_data/ 下75家公司的3张报表CSV
 输出：outputs/financial_indicators_2019_2021.csv
================================================================================
"""

import pandas as pd
import numpy as np
import os, sys, warnings
warnings.filterwarnings("ignore")

BASE = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
MASTER = os.path.join(BASE, "核验结果", "最终企业样本名单.xlsx")
FIN_DIR = os.path.join(BASE, "data_competition", "data1", "financial_data")
OUT_DIR = os.path.join(BASE, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

COL_MAP = {
    "bs_total_assets": "TOTAL_ASSETS",
    "bs_total_equity": "TOTAL_EQUITY",
    "bs_total_liab": "TOTAL_LIABILITIES",
    "bs_current_assets": "TOTAL_CURRENT_ASSETS",
    "bs_current_liab": "TOTAL_CURRENT_LIAB",
    "bs_inventory": "INVENTORY",
    "bs_accounts_rece": "ACCOUNTS_RECE",
    "bs_monetary_funds": "MONETARYFUNDS",
    "is_operate_income": "OPERATE_INCOME",
    "is_operate_cost": "OPERATE_COST",
    "is_total_profit": "TOTAL_PROFIT",
    "is_finance_expense": "FINANCE_EXPENSE",
    "cf_netcash_operate": "NETCASH_OPERATE",
    "cf_netprofit": "NETPROFIT",
}

def load_company_list():
    df = pd.read_excel(MASTER, engine="openpyxl")
    data = df[df.iloc[:, 3].notna() & df.iloc[:, 3].astype(str).str.match(r"^\d{6}$")].copy()
    codes = []
    for _, row in data.iterrows():
        code = str(int(row.iloc[3])).zfill(6)
        codes.append({
            "code": code,
            "name": str(row.iloc[4])[:30],
            "industry": str(row.iloc[1])[:10],
            "group": str(row.iloc[2])[:10],
        })
    return codes

def code_to_symbol(code):
    code = code.zfill(6)
    return f"sh{code}" if code.startswith(("6", "9")) else f"sz{code}"

def safe_get(df, col_name, default=np.nan):
    if col_name in df.columns:
        return pd.to_numeric(df[col_name], errors="coerce")
    return pd.Series([default] * len(df), index=df.index)

def read_statement(sym, stype):
    path = os.path.join(FIN_DIR, sym, f"{sym}_{stype}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, encoding="utf-8-sig")
    if "REPORT_DATE" not in df.columns:
        return None
    df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"], errors="coerce")
    df = df.sort_values("REPORT_DATE").reset_index(drop=True)
    return df

def compute_indicators(company):
    sym = code_to_symbol(company["code"])
    bs = read_statement(sym, "balance_sheet")
    is_df = read_statement(sym, "income_statement")
    cf = read_statement(sym, "cash_flow")
    
    if bs is None or is_df is None or cf is None:
        return None
    
    result = {
        "code": company["code"],
        "name": company["name"],
        "industry": company["industry"],
        "group": company["group"],
    }
    
    years = [2019, 2020, 2021]
    year_data = {}
    
    for yr in years:
        bs_yr = bs[bs["REPORT_DATE"].dt.year == yr]
        is_yr = is_df[is_df["REPORT_DATE"].dt.year == yr]
        cf_yr = cf[cf["REPORT_DATE"].dt.year == yr]
        
        if bs_yr.empty or is_yr.empty or cf_yr.empty:
            continue
        
        bs_row = bs_yr.iloc[-1]
        is_row = is_yr.iloc[-1]
        cf_row = cf_yr.iloc[-1]
        
        total_assets = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_total_assets"]).iloc[0]
        total_equity = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_total_equity"]).iloc[0]
        total_liab = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_total_liab"]).iloc[0]
        current_assets = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_current_assets"]).iloc[0]
        current_liab = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_current_liab"]).iloc[0]
        inventory = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_inventory"]).iloc[0]
        accounts_rece = safe_get(pd.DataFrame([bs_row]), COL_MAP["bs_accounts_rece"]).iloc[0]
        
        operate_income = safe_get(pd.DataFrame([is_row]), COL_MAP["is_operate_income"]).iloc[0]
        operate_cost = safe_get(pd.DataFrame([is_row]), COL_MAP["is_operate_cost"]).iloc[0]
        total_profit = safe_get(pd.DataFrame([is_row]), COL_MAP["is_total_profit"]).iloc[0]
        finance_expense = safe_get(pd.DataFrame([is_row]), COL_MAP["is_finance_expense"]).iloc[0]
        
        netcash_operate = safe_get(pd.DataFrame([cf_row]), COL_MAP["cf_netcash_operate"]).iloc[0]
        netprofit = safe_get(pd.DataFrame([cf_row]), COL_MAP["cf_netprofit"]).iloc[0]
        
        ind = {}
        # 1. ROA
        ind["roa"] = netprofit / total_assets if total_assets > 0 else np.nan
        # 2. ROE
        ind["roe"] = netprofit / total_equity if total_equity > 0 else np.nan
        # 3. 资产负债率
        ind["debt_ratio"] = total_liab / total_assets if total_assets > 0 else np.nan
        # 4. 流动比率
        ind["current_ratio"] = current_assets / current_liab if current_liab > 0 else np.nan
        # 5. 速动比率
        ind["quick_ratio"] = (current_assets - inventory) / current_liab if current_liab > 0 else np.nan
        # 6. 总资产周转率
        ind["asset_turnover"] = operate_income / total_assets if total_assets > 0 else np.nan
        # 7. 存货周转率
        ind["inventory_turnover"] = operate_cost / inventory if inventory > 0 else np.nan
        # 8. 应收账款周转率
        ind["ar_turnover"] = operate_income / accounts_rece if accounts_rece > 0 else np.nan
        # 9. 经营现金流/营业收入
        ind["cf_to_revenue"] = netcash_operate / operate_income if operate_income > 0 else np.nan
        # 10. 利息保障倍数
        interest_cost = abs(finance_expense) if abs(finance_expense) > 0 else np.nan
        ind["interest_coverage"] = (total_profit + abs(finance_expense)) / interest_cost if not np.isnan(interest_cost) else np.nan
        
        year_data[yr] = ind
    
    if len(year_data) < 2:
        return None
    
    # 三年均值
    all_keys = year_data[list(year_data.keys())[0]].keys()
    for key in all_keys:
        vals = [year_data[yr].get(key, np.nan) for yr in years if yr in year_data]
        vals = [v for v in vals if not np.isnan(v)]
        result[key] = round(np.mean(vals) if vals else np.nan, 6)
    
    # 逐年值
    for yr in years:
        if yr in year_data:
            for k in ["roa", "roe", "debt_ratio", "current_ratio", "quick_ratio"]:
                result[f"{k}_{yr}"] = round(year_data[yr][k], 6)
    
    # ROA增长率 (2021 vs 2019)
    if 2019 in year_data and 2021 in year_data:
        roa_19 = year_data[2019]["roa"]
        roa_21 = year_data[2021]["roa"]
        if not np.isnan(roa_19) and roa_19 != 0:
            result["roa_growth"] = round((roa_21 - roa_19) / abs(roa_19), 6)
    
    return result

def main():
    companies = load_company_list()
    print(f"Loaded {len(companies)} companies")
    
    results = []
    failed = []
    
    for i, company in enumerate(companies):
        sym = code_to_symbol(company["code"])
        try:
            ind = compute_indicators(company)
            if ind:
                results.append(ind)
            else:
                failed.append(f"{company['code']} {company['name']}")
        except Exception as e:
            failed.append(f"{company['code']} {company['name']}: {str(e)[:80]}")
        
        if (i + 1) % 15 == 0:
            print(f"  Progress: {i+1}/{len(companies)}")
    
    print(f"\nSuccess: {len(results)} companies")
    if failed:
        print(f"Failed: {len(failed)}")
        for f in failed:
            print(f"  - {f}")
    
    df_out = pd.DataFrame(results)
    out_path = os.path.join(OUT_DIR, "financial_indicators_2019_2021.csv")
    df_out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nOutput: {out_path}")
    print(f"Shape: {df_out.shape[0]} rows x {df_out.shape[1]} cols")
    
    # Industry summary
    print("\n=== Industry Mean Indicators ===")
    ind_list = ["roa", "roe", "debt_ratio", "current_ratio", "quick_ratio",
                "asset_turnover", "inventory_turnover", "ar_turnover",
                "cf_to_revenue", "interest_coverage"]
    summary = df_out.groupby("industry")[ind_list].mean().round(4)
    print(summary.to_string())
    
    return df_out

if __name__ == "__main__":
    main()
    print("\nDone!")
