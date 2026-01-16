import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Keuangan Shopee", layout="wide")

st.title("📊 Dashboard Keuangan Shopee (Accrual-Based)")
st.caption("Profit dari order (accrual), cashflow dari income, iklan sebagai biaya")

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

    # --- WAJIB SHOPEE ---
    # Omzet
    omzet_col = "Total Pembayaran"
    omzet = df_order[omzet_col].sum() if omzet_col in df_order.columns else 0

    # Produk
    product_col = "Nama Produk" if "Nama Produk" in df_order.columns else df_order.columns[0]
    produk_list = df_order[product_col].unique()

    st.divider()
    st.subheader("📦 Input HPP Manual per Produk")
    st.caption("Isi HPP satuan saja, app akan mengalikan otomatis")

    hpp_data = {}
    for p in produk_list:
        hpp_data[p] = st.number_input(f"HPP {p}", min_value=0, step=500, value=0)

    # Hitung HPP total
    df_order["HPP_satuan"] = df_order[product_col].map(hpp_data)
    # pastikan HPP numerik dan aman
    df_order["HPP_satuan"] = pd.to_numeric(df_order["HPP_satuan"], errors="coerce").fillna(0)
    df_order["HPP_total"] = df_order["HPP_satuan"]
    hpp_total = df_order["HPP_total"].sum()

    profit_kotor = omzet - hpp_total

    # Iklan
    total_iklan = 0
    if ads_file:
        df_ads = pd.read_excel(ads_file)
        biaya_cols = [c for c in df_ads.columns if "Biaya" in c or "Cost" in c]
        if biaya_cols:
            total_iklan = df_ads[biaya_cols[0]].sum()

    profit_bersih = profit_kotor - total_iklan

    # Income
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
    c2.metric("HPP", f"Rp {hpp_total:,.0f}")
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
    st.info("Upload Order All untuk memulai")
