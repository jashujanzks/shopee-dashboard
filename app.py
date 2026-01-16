import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Keuangan Shopee", layout="wide")

st.title("📊 Dashboard Keuangan Shopee (Accrual-Based)")
st.caption("Profit dihitung dari order, cashflow dari income, iklan sebagai biaya")

# Upload files
col1, col2, col3 = st.columns(3)
with col1:
    order_file = st.file_uploader("Upload Order All (WAJIB)", type=["xlsx", "csv"])
with col2:
    income_file = st.file_uploader("Upload Income (Opsional)", type=["xlsx", "csv"])
with col3:
    ads_file = st.file_uploader("Upload Iklan (Opsional)", type=["xlsx", "csv"])

if order_file:
    df_order = pd.read_excel(order_file)

    # Basic assumptions (can be adjusted later)
    omzet_col = [c for c in df_order.columns if "Total" in c or "Omzet" in c]
    hpp_col = [c for c in df_order.columns if "HPP" in c]

    omzet = df_order[omzet_col[0]].sum() if omzet_col else 0
    hpp = df_order[hpp_col[0]].sum() if hpp_col else 0
    profit_kotor = omzet - hpp

    total_iklan = 0
    if ads_file:
        df_ads = pd.read_excel(ads_file)
        biaya_cols = [c for c in df_ads.columns if "Biaya" in c or "Cost" in c]
        if biaya_cols:
            total_iklan = df_ads[biaya_cols[0]].sum()

    profit_bersih = profit_kotor - total_iklan

    dana_cair = 0
    dana_belum_cair = 0
    if income_file:
        df_income = pd.read_excel(income_file)
        cair_cols = [c for c in df_income.columns if "Cair" in c]
        belum_cols = [c for c in df_income.columns if "Belum" in c]
        if cair_cols:
            dana_cair = df_income[cair_cols[0]].sum()
        if belum_cols:
            dana_belum_cair = df_income[belum_cols[0]].sum()

    st.divider()
    st.subheader("📌 Ringkasan Utama")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Omzet", f"Rp {omzet:,.0f}")
    c2.metric("HPP", f"Rp {hpp:,.0f}")
    c3.metric("Profit Kotor", f"Rp {profit_kotor:,.0f}")
    c4.metric("Biaya Iklan", f"Rp {total_iklan:,.0f}")
    c5.metric("Profit Bersih", f"Rp {profit_bersih:,.0f}")

    if income_file:
        st.divider()
        st.subheader("💰 Cashflow")
        c6, c7 = st.columns(2)
        c6.metric("Dana Cair", f"Rp {dana_cair:,.0f}")
        c7.metric("Dana Belum Cair", f"Rp {dana_belum_cair:,.0f}")

else:
    st.info("Silakan upload minimal file Order All untuk memulai")
