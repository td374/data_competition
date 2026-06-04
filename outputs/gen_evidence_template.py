# -*- coding: utf-8 -*-
"""
============================================================================
 独立测试集10家漂绿证据自动化检索 + 模板生成
 多模态漂绿识别与信贷风险预警研究
============================================================================
 输出: outputs/independent_test_evidence_template.xlsx
       含有10家企业 + 分级搜索关键词 + 证据记录表
============================================================================
"""
import pandas as pd
import os

# ====== 10家独立测试集 ======
companies = [
    {
        "code": "600157", "name": "永泰能源", "industry": "发电", "group": "独立测试集",
        "search_l1": "永泰能源 环保处罚 超标排放 行政处罚 site:creditchina.gov.cn",
        "search_l1b": "永泰能源 生态环境局 罚单",
        "search_l2": "永泰能源 超标排放 媒体调查 财新 OR 21世纪经济报道",
        "search_l3": "永泰能源 ESG报告 减排承诺 实际排放 矛盾",
        "notes": "煤炭+火电，转型期常有'超低排放'声称与实际超标矛盾"
    },
    {
        "code": "600509", "name": "天富能源", "industry": "发电", "group": "独立测试集",
        "search_l1": "天富能源 环保处罚 行政处罚 新疆",
        "search_l1b": "天富能源 石河子 生态环境局 处罚",
        "search_l2": "天富能源 环保 媒体报道 调查",
        "search_l3": "天富能源 年报 环保投入 vs 实际排放 新疆生态环境厅",
        "notes": "新疆石河子地区火电+供热，查新疆生态环境厅公示"
    },
    {
        "code": "600221", "name": "海南航空", "industry": "航空", "group": "独立测试集",
        "search_l1": "海南航空 碳排放 处罚 EU ETS 超标",
        "search_l1b": "海南航空 ESG 造假 证监会 问询函",
        "search_l2": "海南航空 碳排放 漂绿 媒体调查",
        "search_l3": "海南航空 碳抵消 声称 vs 实际碳排放 民航局数据",
        "notes": "航空碳排放是国际监管重点，EU ETS对中国航司有罚款记录可查"
    },
    {
        "code": "000932", "name": "华菱钢铁", "industry": "钢铁", "group": "独立测试集",
        "search_l1": "华菱钢铁 环保处罚 超标排放 湖南",
        "search_l1b": "华菱钢铁 湘钢 OR 涟钢 OR 衡钢 行政处罚",
        "search_l2": "华菱钢铁 环保 调查报道 媒体",
        "search_l3": "华菱钢铁 超低排放改造 声称 实际监测数据",
        "notes": "旗下湘钢/涟钢/衡钢三家基地，分别查各地生态环境局"
    },
    {
        "code": "600782", "name": "新余钢铁", "industry": "钢铁", "group": "独立测试集",
        "search_l1": "新余钢铁 环保处罚 超标排放 江西",
        "search_l1b": "新余钢铁 新余市生态环境局 处罚",
        "search_l2": "新余钢铁 环保 媒体报道 调查",
        "search_l3": "新余钢铁 绿色工厂 声称 vs 实际处罚记录",
        "notes": "江西新余，地方钢企，查江西省生态环境厅公示"
    },
    {
        "code": "002233", "name": "塔牌集团", "industry": "建材", "group": "独立测试集",
        "search_l1": "塔牌集团 环保处罚 超标排放 水泥 广东",
        "search_l1b": "塔牌集团 梅州 生态环境局 处罚",
        "search_l2": "塔牌集团 水泥 环保 媒体调查",
        "search_l3": "塔牌集团 绿色矿山 声称 vs 实际开采 处罚",
        "notes": "广东梅州水泥企业，查广东省生态环境厅+梅州市局"
    },
    {
        "code": "000554", "name": "泰山石油", "industry": "石化", "group": "独立测试集",
        "search_l1": "泰山石油 环保处罚 山东 油品 泄漏",
        "search_l1b": "泰山石油 中石化 行政处罚 生态环境",
        "search_l2": "泰山石油 油品泄漏 污染 媒体报道",
        "search_l3": "泰山石油 绿色加油站 声称 vs 实际环保检查结果",
        "notes": "中石化旗下山东成品油销售公司，查加油站环保检查记录"
    },
    {
        "code": "300082", "name": "奥克化学", "industry": "化工", "group": "独立测试集",
        "search_l1": "奥克化学 环保处罚 化工 辽宁",
        "search_l1b": "奥克化学 辽阳 OR 扬州 生态环境局 处罚",
        "search_l2": "奥克化学 化工污染 媒体调查",
        "search_l3": "奥克化学 环氧乙烷 安全生产 环保问题",
        "notes": "辽宁辽阳+江苏扬州均有基地，做环氧乙烷深加工，化工安全+环保双重关注"
    },
    {
        "code": "002511", "name": "中顺洁柔", "industry": "造纸", "group": "独立测试集",
        "search_l1": "中顺洁柔 环保处罚 废水排放 广东",
        "search_l1b": "中顺洁柔 造纸 行政处罚 超标",
        "search_l2": "中顺洁柔 造纸污染 媒体报道",
        "search_l3": "中顺洁柔 绿色产品 FSC认证 声称 vs 实际废水排放数据",
        "notes": "广东中山/江门造纸企业，查造纸废水排放监测数据"
    },
    {
        "code": "600456", "name": "宝钛股份", "industry": "有色", "group": "独立测试集",
        "search_l1": "宝钛股份 环保处罚 钛冶炼 陕西",
        "search_l1b": "宝钛股份 宝鸡 生态环境局 处罚",
        "search_l2": "宝钛股份 钛冶炼 污染 媒体调查",
        "search_l3": "宝钛股份 绿色工厂 声称 vs 实际处罚记录",
        "notes": "陕西宝鸡，钛材加工，有色冶炼行业，查陕西省生态环境厅"
    },
]

# ====== 生成Excel模板 ======
rows = []
for c in companies:
    rows.append({
        "股票代码": c["code"],
        "企业名称": c["name"],
        "行业": c["industry"],
        "L1搜索-处罚": c["search_l1"],
        "L1搜索-补充": c["search_l1b"],
        "L2搜索-媒体": c["search_l2"],
        "L3搜索-矛盾": c["search_l3"],
        "重点提示": c["notes"],
        "L1证据-发现": "",
        "L1证据-来源URL": "",
        "L2证据-发现": "",
        "L2证据-来源URL": "",
        "证据等级(填写L1/L2/L3)": "",
        "是否合格(≥L1或L2)": "",
        "截图保存路径": "",
    })

df = pd.DataFrame(rows)

OUT = r"C:\Users\28129\Desktop\共享1-数据收集与核对\outputs"
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "independent_test_evidence_template.xlsx")

with pd.ExcelWriter(path, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="证据收集模板", index=False)
    
    # 加一个说明sheet
    instructions = pd.DataFrame({
        "说明": [
            "L1 铁证：生态环境部门/证监会正式行政处罚或问询函（最有说服力）",
            "L2 强证：权威媒体深度调查报告（财新/新华社/21世纪经济报/IPE等）",
            "L3 辅助：数据矛盾，年报声称 vs 监管监测数据（需两个来源截图对比）",
            "不合格：纯逻辑推断（'火电=高污染=漂绿'），不能单独作为证据",
            "",
            "每家企业至少要有1条L1或L2级别证据",
            "所有证据截图保存到 screenshots/ 文件夹",
            "",
            "搜索渠道优先级：",
            "1. 信用中国 creditchina.gov.cn - 行政处罚查询",
            "2. 天眼查 tianyancha.com - 快速浏览企业风险信息",
            "3. 各省级生态环境厅官网 - 环境处罚公示",
            "4. 百度/Google: 企业名+关键词",
            "5. IPE公众环境研究中心 ipe.org.cn - 企业环境监管记录",
        ]
    })
    instructions.to_excel(writer, sheet_name="说明", index=False)

print(f"Template saved: {path}")
print(f"10 companies ready for evidence collection")
