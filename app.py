import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Dashboard Keuangan Shopee – Accrual Based (ZKS)",
    layout="wide"
)

st.title("📊 Dashboard Keuangan Shopee – Accrual Based (ZKS)")
st.caption("Fokus: profit real, cashflow jelas, iklan tidak bias")

# =====================================================
# HELPER FUNCTIONS (ANTI ERROR & STRING BUG)
# =====================================================
def safe_read(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        return pd.read_excel(uploaded_file)
    except:
        return pd.DataFrame()

def force_numeric(series):
    return (
        series.astype(str)
        .str.replace("Rp", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace("nan", "0")
        .astype(float)
    )

def find_col(df, keywords):
    for col in df.columns:
        for key in keywords:
            if key.lower() in col.lower():
                return col
    return None

# =====================================================
# FILE UPLOAD
# =====================================================
st.sidebar.header("📂 Upload Data")

order_file = st.sidebar.file_uploader("Order All Shopee (WAJIB)", type=["xlsx", "csv"])
income_file = st.sidebar.file_uploader("Income Shopee (Opsional)", type=["xlsx", "csv"])
ads_file = st.sidebar.file_uploader("Data Iklan (Opsional)", type=["xlsx", "csv"])

if not order_file:
    st.warning("⚠️ Upload Order All Shopee dulu.")
    st.stop()

# =====================================================
# LOAD & CLEAN ORDER DATA
# =====================================================
orders = safe_read(order_file)

status_col = find_col(orders, ["status"])
amount_col = find_col(orders, ["total", "payment", "amount", "pembayaran"])
product_col = find_col(orders, ["produk", "product", "item", "nama"])

if not all([status_col, amount_col, product_col]):
    st.error("❌ Kolom penting tidak ditemukan di Order All.")
    st.stop()

orders[amount_col] = force_numeric(orders[amount_col])

orders_valid = orders[
    orders[status_col].astype(str).str.lower().isin(["selesai", "completed"])
]

# =====================================================
# OMZET (ACCRUAL)
# =====================================================
omzet_accrual = orders_valid[amount_col].sum()

# =====================================================
# PRODUK & HPP INPUT
# =====================================================
produk_summary = (
    orders_valid
    .groupby(product_col)
    .agg(
        jumlah_order=(product_col, "count"),
        omzet_produk=(amount_col, "sum")
    )
    .reset_index()
)

st.subheader("📦 Input HPP per Produk")
hpp_input = st.data_editor(
    produk_summary.assign(HPP_Satuan=0),
    num_rows="fixed"
)

hpp_input["HPP_Satuan"] = force_numeric(hpp_input["HPP_Satuan"])
hpp_input["HPP_Total"] = hpp_input["HPP_Satuan"] * hpp_input["jumlah_order"]
hpp_input["Profit_Produk"] = hpp_input["omzet_produk"] - hpp_input["HPP_Total"]

# =====================================================
# PROFIT PER PRODUK (AUTO WARNA)
# =====================================================
def color_profit(val):
    if val < 0:
        return "background-color:#ffcccc"
    return "background-color:#ccffcc"

st.subheader("💰 Profit per Produk")
st.dataframe(
    hpp_input.style.applymap(color_profit, subset=["Profit_Produk"]),
    use_container_width=True
)

# =====================================================
# IKLAN & ROAS
# =====================================================
biaya_iklan = 0
roas = 0
roas_status = "-"

if ads_file:
    ads = safe_read(ads_file)
    cost_col = find_col(ads, ["biaya", "cost", "spend"])
    if cost_col:
        ads[cost_col] = force_numeric(ads[cost_col])
        biaya_iklan = ads[cost_col].sum()

if biaya_iklan > 0:
    roas = omzet_accrual / biaya_iklan
    if roas >= 3:
        roas_status = "🔥 Sehat"
    elif roas >= 1:
        roas_status = "⚠️ Perlu evaluasi"
    else:
        roas_status = "❌ Rugi"

# =====================================================
# PROFIT UTAMA
# =====================================================
hpp_total = hpp_input["HPP_Total"].sum()
profit_kotor = omzet_accrual - hpp_total
profit_bersih = profit_kotor - biaya_iklan

st.subheader("📊 Ringkasan Utama")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Omzet (Accrual)", f"Rp {omzet_accrual:,.0f}")
col2.metric("HPP Total", f"Rp {hpp_total:,.0f}")
col3.metric("Profit Kotor", f"Rp {profit_kotor:,.0f}")
col4.metric("Biaya Iklan", f"Rp {biaya_iklan:,.0f}")
col5.metric("Profit Bersih", f"Rp {profit_bersih:,.0f}")

st.markdown(f"**ROAS:** {roas:.2f} → {roas_status}")

# =====================================================
# CASHFLOW (INCOME)
# =====================================================
dana_cair = 0
dana_belum_cair = 0

if income_file:
    income = safe_read(income_file)
    cair_col = find_col(income, ["cair"])
    belum_col = find_col(income, ["belum"])
    if cair_col:
        income[cair_col] = force_numeric(income[cair_col])
        dana_cair = income[cair_col].sum()
    if belum_col:
        income[belum_col] = force_numeric(income[belum_col])
        dana_belum_cair = income[belum_col].sum()

st.subheader("💸 Cashflow")
c1, c2 = st.columns(2)
c1.metric("Dana Cair", f"Rp {dana_cair:,.0f}")
c2.metric("Dana Belum Cair", f"Rp {dana_belum_cair:,.0f}")

# =====================================================
# EXPORT PDF (FORMAT ZKS)
# =====================================================
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0, 8, "Laporan Keuangan Shopee – ZKS", ln=True)
    pdf.ln(3)

    def line(label, value):
        pdf.cell(0, 7, f"{label}: Rp {value:,.0f}", ln=True)

    line("Omzet (Accrual)", omzet_accrual)
    line("HPP Total", hpp_total)
    line("Profit Kotor", profit_kotor)
    line("Biaya Iklan", biaya_iklan)
    line("Profit Bersih", profit_bersih)
    line("Dana Cair", dana_cair)
    line("Dana Belum Cair", dana_belum_cair)

    return pdf.output(dest="S").encode("latin-1")

st.divider()
if st.button("📄 Export PDF – Format ZKS"):
    pdf_bytes = export_pdf()
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name="Laporan_Keuangan_Shopee_ZKS.pdf",
        mime="application/pdf"
    )
