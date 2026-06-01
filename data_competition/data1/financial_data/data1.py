# -*- coding: utf-8 -*-
"""
完整版：获取上市公司三大财务报表并计算关键财务指标
使用 AKShare 接口，股票代码需带市场前缀（sh/sz）
"""

import akshare as ak
import pandas as pd
import os   # 新增：用于创建目录

# ==================== 配置参数 ====================
STOCK_CODE = "sh600011"      # 华能国际，沪市
SAVE_CSV = True              # 是否保存原始数据到 CSV
OUTPUT_DIR = "/"  # 保存路径

# 如果保存路径不存在，则自动创建
if SAVE_CSV and not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"已创建目录: {OUTPUT_DIR}")

# ==================== 1. 获取资产负债表 ====================
print("正在获取资产负债表...")
balance_df = ak.stock_balance_sheet_by_report_em(symbol=STOCK_CODE)
# 按报告期排序（最新在前）
balance_df = balance_df.sort_values("REPORT_DATE", ascending=False)
print("资产负债表获取成功，共 {} 行，{} 列".format(*balance_df.shape))
if SAVE_CSV:
    balance_df.to_csv(OUTPUT_DIR + f"{STOCK_CODE}_balance_sheet.csv", index=False, encoding="utf-8-sig")

# ==================== 2. 获取利润表 ====================
print("\n正在获取利润表...")
income_df = ak.stock_profit_sheet_by_report_em(symbol=STOCK_CODE)
income_df = income_df.sort_values("REPORT_DATE", ascending=False)
print("利润表获取成功，共 {} 行，{} 列".format(*income_df.shape))
if SAVE_CSV:
    income_df.to_csv(OUTPUT_DIR + f"{STOCK_CODE}_income_statement.csv", index=False, encoding="utf-8-sig")

# ==================== 3. 获取现金流量表 ====================
print("\n正在获取现金流量表...")
cash_df = ak.stock_cash_flow_sheet_by_report_em(symbol=STOCK_CODE)
cash_df = cash_df.sort_values("REPORT_DATE", ascending=False)
print("现金流量表获取成功，共 {} 行，{} 列".format(*cash_df.shape))
if SAVE_CSV:
    cash_df.to_csv(OUTPUT_DIR + f"{STOCK_CODE}_cash_flow.csv", index=False, encoding="utf-8-sig")

# ==================== 4. 提取关键财务指标 ====================
# 选取最近一期年报（假设 REPORT_DATE 含 '12-31'）
annual_balance = balance_df[balance_df["REPORT_DATE"].str.contains("12-31", na=False)].iloc[0]
annual_income = income_df[income_df["REPORT_DATE"].str.contains("12-31", na=False)].iloc[0]
annual_cash = cash_df[cash_df["REPORT_DATE"].str.contains("12-31", na=False)].iloc[0]

print("\n资产负债表列名示例：", balance_df.columns.tolist()[:10])
print("利润表列名示例：", income_df.columns.tolist()[:10])
print("现金流量表列名示例：", cash_df.columns.tolist()[:10])

# 打印最近一期年报的关键数值（方便你确认列名）
print("\n最近一期资产负债表（年度）关键数值：")
print(annual_balance.to_dict())

print("\n最近一期利润表（年度）关键数值：")
print(annual_income.to_dict())

print("\n最近一期现金流量表（年度）关键数值：")
print(annual_cash.to_dict())

print("\n所有原始数据已保存至目录：", OUTPUT_DIR)