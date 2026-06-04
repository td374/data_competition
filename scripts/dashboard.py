# -*- coding: utf-8 -*-
"""
Streamlit Evidence-Chain Dashboard
Interactive greenwash risk explorer with evidence traceability.
Run: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd, numpy as np, json, os

st.set_page_config(page_title="漂绿识别与信贷风险预警系统", layout="wide",
                   page_icon="assets/favicon.png" if os.path.exists("assets/favicon.png") else None)

# === Load Data ===
@st.cache_data
def load_data():
    """Load GWI results and master list."""
    gwi_path = "outputs/gwi_results.csv"
    master_path = "outputs/master_company_list.csv"
    
    if os.path.exists(gwi_path):
        gwi = pd.read_csv(gwi_path, encoding="utf-8-sig")
    else:
        gwi = pd.DataFrame()
    
    if os.path.exists(master_path):
        master = pd.read_csv(master_path, encoding="utf-8-sig")
    else:
        master = pd.DataFrame()
    
    if not gwi.empty and not master.empty:
        df = gwi.merge(master[["code", "industry", "group", "name"]], on="code", how="left")
    elif not gwi.empty:
        df = gwi.copy()
    else:
        df = pd.DataFrame()
    
    return df

df = load_data()

# === Sidebar ===
st.sidebar.title("漂绿识别与信贷风险预警系统")
st.sidebar.markdown("---")

if not df.empty:
    industries = ["全部"] + sorted(df["industry"].dropna().unique().tolist())
    selected_industry = st.sidebar.selectbox("行业筛选", industries)
    
    groups = ["全部"] + sorted(df["group"].dropna().unique().tolist())
    selected_group = st.sidebar.selectbox("分组筛选", groups)
    
    # Filter
    filtered = df.copy()
    if selected_industry != "全部":
        filtered = filtered[filtered["industry"] == selected_industry]
    if selected_group != "全部":
        filtered = filtered[filtered["group"] == selected_group]
else:
    filtered = df
    st.sidebar.warning("数据尚未加载。请先运行数据采集和GWI构建脚本。")

# === Main Page ===
st.title("多模态数据驱动的上市公司漂绿识别与信贷风险预警")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["漂绿风险总览", "企业详情", "证据链追溯", "模型对比"])

# --- Tab 1: Overview ---
with tab1:
    st.header("漂绿风险总览")
    
    if not filtered.empty and "GWI" in filtered.columns:
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk = len(filtered[filtered["GWI_level"] == "High"])
        total = len(filtered)
        
        col1.metric("样本总数", f"{total}家")
        col2.metric("高风险企业", f"{high_risk}家", f"{high_risk/total*100:.0f}%")
        col3.metric("平均GWI", f"{filtered['GWI'].mean():.3f}")
        col4.metric("GWI标准差", f"{filtered['GWI'].std():.3f}")
        
        st.markdown("---")
        
        # Industry comparison
        st.subheader("行业GWI分布")
        if "industry" in filtered.columns:
            industry_gwi = filtered.groupby("industry")["GWI"].agg(["mean", "std", "count"]).round(3)
            industry_gwi.columns = ["平均GWI", "标准差", "企业数"]
            st.dataframe(industry_gwi, use_container_width=True)
        
        # Risk distribution
        st.subheader("风险等级分布")
        if "GWI_level" in filtered.columns:
            level_counts = filtered["GWI_level"].value_counts()
            st.bar_chart(level_counts)
        
        # Top risk companies
        st.subheader("GWI Top 10 高风险企业")
        top10 = filtered.nlargest(10, "GWI")[["code", "name", "industry", "group", "GWI", "GWI_level"]]
        st.dataframe(top10, use_container_width=True, hide_index=True)
    else:
        st.info("请先运行 build_gwi.py 生成GWI数据后再查看。")

# --- Tab 2: Company Detail ---
with tab2:
    st.header("企业详情查询")
    
    if not df.empty:
        companies = df["code"].dropna().unique().tolist()
        selected_code = st.selectbox("选择企业代码", companies, 
                                      format_func=lambda x: f"{x} - {df[df['code']==x]['name'].values[0][:20]}" if len(df[df['code']==x]) > 0 else x)
        
        company_data = df[df["code"] == selected_code]
        if not company_data.empty:
            row = company_data.iloc[0]
            
            cols = st.columns(3)
            cols[0].metric("GWI漂绿指数", f"{row.get('GWI', 'N/A')}")
            cols[1].metric("风险等级", row.get("GWI_level", "N/A"))
            cols[2].metric("行业", row.get("industry", "N/A"))
            
            st.markdown("---")
            st.subheader("三维度得分")
            
            dim_cols = st.columns(3)
            fin_score = row.get("fin_risk_score", 0.5)
            esg_score = row.get("esg_greenwash_score", 0.5)
            rs_score = row.get("rs_deviation_score", 0.5)
            
            dim_cols[0].metric("财务风险", f"{fin_score:.3f}", 
                               delta="高" if fin_score > 0.5 else "低" if fin_score < 0.5 else "中")
            dim_cols[1].metric("ESG漂绿嫌疑", f"{esg_score:.3f}",
                               delta="高" if esg_score > 0.5 else "低" if esg_score < 0.5 else "中")
            dim_cols[2].metric("遥感偏离度", f"{rs_score:.3f}",
                               delta="高" if rs_score > 0.5 else "低" if rs_score < 0.5 else "中")

# --- Tab 3: Evidence Chain ---
with tab3:
    st.header("证据链追溯")
    st.markdown("""
    漂绿嫌疑的证据链由三个维度交叉验证：
    - **文本自述** (ESG报告)：企业说了什么承诺
    - **遥感实情** (卫星影像)：实际生产活动是否改善
    - **财务结果** (财务指标)：经营状况是否支撑环保投入
    """)
    
    if not filtered.empty and "cfr" in filtered.columns:
        st.subheader("承诺-行动偏差")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("平均CFR (承诺兑现比)", f"{filtered['cfr'].mean():.3f}",
                     help="CFR = 行动句数 / (承诺句数 + 行动句数)。越高表示行动多于承诺。")
        with col2:
            low_cfr = len(filtered[filtered["cfr"] < 0.4])
            st.metric("低CFR企业 (<0.4)", f"{low_cfr}家",
                     help="承诺远多于行动，存在漂绿嫌疑。")
        
        st.scatter_chart(filtered[["cfr", "GWI"]].dropna().rename(
            columns={"cfr": "CFR承诺兑现比", "GWI": "GWI漂绿指数"}))
    else:
        st.info("请先运行 esg_text_analysis.py 生成CFR数据。")

# --- Tab 4: Model Comparison ---
with tab4:
    st.header("违约预测模型对比")
    st.markdown("""
    三组对比实验验证多模态数据的增量价值：
    - **Model 1**: 仅财务指标 (Baseline)
    - **Model 2**: 财务 + ESG文本
    - **Model 3**: 财务 + ESG文本 + 遥感 (Full Fusion)
    """)
    
    # Placeholder results
    comparison_data = pd.DataFrame({
        "模型": ["Model 1 仅财务", "Model 2 财务+ESG", "Model 3 财务+ESG+遥感"],
        "AUC": [0.72, 0.81, 0.88],
        "F1": [0.65, 0.74, 0.82],
        "特征数": [12, 17, 20],
    })
    
    st.dataframe(comparison_data, use_container_width=True, hide_index=True)
    st.bar_chart(comparison_data.set_index("模型")[["AUC", "F1"]])
    
    st.caption("注：以上为预期结果示意。实际数值需运行 train_models.py 后更新。")

# === Footer ===
st.markdown("---")
st.caption("多模态数据驱动的上市公司漂绿识别与信贷风险预警系统 | 数据要素大赛")
