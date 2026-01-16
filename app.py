import streamlit as st
import pandas as pd
import numpy as np

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="Dashboard Keuangan Shopee (Accrual)",
    layout="wide"
)

st.title("📊 Dashboard Keuangan Shopee")
st.caption("Metode: Accrual-Based Profit Analysis (Order-Based)")

# ==============================
# HELPER FUNCTIONS (ANTI ERROR)
# ==============================
def safe_read(file):
    try:
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_excel(file)
    except:
        return pd.DataFrame()

def force_numeric(series):
    return (
        series.astype(str)
        .str.replace("Rp", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(float)
    )

def find_column(df, keywords):
    for col in df.columns:
        for kw in keywords:
            if kw.lower() in col.lower():
                return col
    return None

# ==============================
# FILE UPLOAD
# ==============================
c1, c2, c3 = st.columns(3)

with c1:
    order_file = st.file_uploader("📦 Upload Order All (WAJIB)", type=["xlsx", "csv"])

with c2:
    income_file = st.file_uploader("💰 Upload Income (OpsIONAL)", type=["xlsx", "csv"])

with c3:
    ads_file = st.file_uploader("📢 Upload Iklan (OpsIONAL)", type=["xlsx", "csv"])

# ==============================
# LOAD DATA
# ==============================
order_df = safe_read(order_file) if order_file else pd.DataFrame()
income_df = safe_read(income_file) if income_file else pd.DataFrame()
ads_df = safe_read(ads_file) if ads_file else pd.DataFrame()

# ==============================
# OMZET (ORDER ALL)
# ==============================
omzet_col = find_column(order_df, ["total pembayaran", "total payment", "amount"])
if omzet_col:
    order_df[omzet_col] = force_numeric(order_df[omzet_col])
    omzet = float(order_df[omzet_col].sum())
else:
    omzet = 0.0

# ==============================
# PRODUK & HPP
# ==============================
product_col = find_column(order_df, ["nama produk", "product"])
if not product_col and not order_df.empty:
    product_col = order_df.columns[0]

qty_col = find_column(order_df, ["jumlah", "qty", "quantity"])
if qty_col:
    order_df[qty_col] = force_numeric(order_df[qty_col])
else:
    order_df["__qty"] = 1.0
    qty_col = "__qty"

if product_col:
    product_summary = (
        order_df.groupby(product_col)[qty_col]
        .sum()
        .reset_index()
        .rename(columns={qty_col: "Jumlah Order"})
    )
else:
    product_summary = pd.DataFrame(columns=["Produk", "Jumlah Order"])

st.subheader("📦 Input HPP per Produk")

if not product_summary.empty:
    product_summary["HPP Satuan"] = 0.0

    edited = st.data_editor(
        product_summary,
        use_container_width=True,
        num_rows="fixed"
    )

    edited["HPP Satuan"] = force_numeric(edited["HPP Satuan"])
    edited["Jumlah Order"] = force_numeric(edited["Jumlah Order"])

    hpp_total = float((edited["HPP Satuan"] * edited["Jumlah Order"]).sum())
else:
    hpp_total = 0.0

# ==============================
# IKLAN
# ==============================
ads_cost = 0.0
if not ads_df.empty:
    cost_col = find_column(ads_df, ["biaya", "cost", "spend"])
    if cost_col:
        ads_df[cost_col] = force_numeric(ads_df[cost_col])
        ads_cost = float(ads_df[cost_col].sum())

# ==============================
# PROFIT
# ==============================
profit_kotor = float(omzet - hpp_total)
profit_bersih = float(profit_kotor - ads_cost)

# ==============================
# CASHFLOW (INCOME)
# ==============================
dana_cair = 0.0
dana_belum_cair = 0.0

if not income_df.empty:
    cair_col = find_column(income_df, ["cair", "settled", "released"])
    pending_col = find_column(income_df, ["belum", "pending", "hold"])

    if cair_col:
        income_df[cair_col] = force_numeric(income_df[cair_col])
        dana_cair = float(income_df[cair_col].sum())

    if pending_col:
        income_df[pending_col] = force_numeric(income_df[pending_col])
        dana_belum_cair = float(income_df[pending_col].sum())

# ==============================
# OUTPUT METRICS
# ==============================
st.divider()
st.subheader("📈 Ringkasan Keuangan")

m1, m2, m3, m4 = st.columns(4)
m5, m6, m7 = st.columns(3)

m1.metric("Omzet (Accrual)", f"Rp {omzet:,.0f}")
m2.metric("HPP Total", f"Rp {hpp_total:,.0f}")
m3.metric("Profit Kotor", f"Rp {profit_kotor:,.0f}")
m4.metric("Biaya Iklan", f"Rp {ads_cost:,.0f}")

m5.metric("Profit Bersih", f"Rp {profit_bersih:,.0f}")
m6.metric("Dana Cair", f"Rp {dana_cair:,.0f}")
m7.metric("Dana Belum Cair", f"Rp {dana_belum_cair:,.0f}")

st.caption("✅ Semua perhitungan berbasis FLOAT | Aman dari error string & kolom kosong")

