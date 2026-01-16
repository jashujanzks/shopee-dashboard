import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Dashboard Keuangan Shopee – Accrual Based (ZKS)",
    layout="wide"
)

st.title("📊 Dashboard Keuangan Shopee – Accrual Based (ZKS)")
st.caption("Dashboard internal | Fokus angka | Tanpa bias | Siap ambil keputusan")

# =====================================================
# HELPER FUNCTIONS (ANTI ERROR TOTAL)
# =====================================================
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
        .str.replace(" ", "", regex=False)
        .replace(["nan", "None", ""], "0")
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

order_file = st.sidebar.file_uploader("Order All Shopee (WAJIB)", ["xlsx", "csv"])
income_file = st.sidebar.file_uploader("Income Shopee (Opsional)", ["xlsx", "csv"])
ads_file = st.sidebar.file_uploader("Data Iklan (Opsional)", ["xlsx", "csv"])

if not order_file:
    st.warning("⚠️ Upload Order All Shopee dulu.")
    st.stop()

# =====================================================
# LOAD ORDER ALL
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
# HPP INPUT PER PRODUK
# =====================================================
produk = (
    orders_valid
    .groupby(product_col)
    .agg(
        jumlah_order=(product_col, "count"),
        omzet_produk=(amount_col, "sum")
    )
    .reset_index()
)

st.subheader("📦 Input HPP Satuan per Produk")

hpp_table = st.data_editor(
    produk.assign(HPP_Satuan=0),
    num_rows="fixed",
    use_container_width=True
)

hpp_table["HPP_Satuan"] = force_numeric(hpp_table["HPP_Satuan"])
hpp_table["HPP_Total"] = hpp_table["HPP_Satuan"] * hpp_table["jumlah_order"]
hpp_table["Profit_Produk"] = hpp_table["omzet_produk"] - hpp_table["HPP_Total"]

# =====================================================
# PROFIT PER PRODUK (AUTO WARNA)
# =====================================================
def highlight_profit(val):
    if val < 0:
        return "background-color:#ffcccc"
    return "background-color:#ccffcc"

st.subheader("💰 Profit per Produk")
st.dataframe(
    hpp_table.style.applymap(highlight_profit, subset=["Profit_Produk"]),
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
hpp_total = hpp_table["HPP_Total"].sum()
profit_kotor = omzet_accrual - hpp_total
profit_bersih = profit_kotor - biaya_iklan

st.subheader("📊 Ringkasan Keuangan")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Omzet (Accrual)", f"Rp {omzet_accrual:,.0f}")
c2.metric("HPP Total", f"Rp {hpp_total:,.0f}")
c3.metric("Profit Kotor", f"Rp {profit_kotor:,.0f}")
c4.metric("Biaya Iklan", f"Rp {biaya_iklan:,.0f}")
c5.metric("Profit Bersih", f"Rp {profit_bersih:,.0f}")

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
cc1, cc2 = st.columns(2)
cc1.metric("Dana Cair", f"Rp {dana_cair:,.0f}")
cc2.metric("Dana Belum Cair", f"Rp {dana_belum_cair:,.0f}")

# =====================================================
# EXPORT PDF – FORMAT ZKS (FINAL)
# =====================================================
def export_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    def p(text):
        content.append(Paragraph(text, styles["Normal"]))

    p("<b>Laporan Keuangan Shopee – ZKS</b><br/><br/>")
    p(f"Omzet (Accrual): Rp {omzet_accrual:,.0f}<br/>")
    p(f"HPP Total: Rp {hpp_total:,.0f}<br/>")
    p(f"Profit Kotor: Rp {profit_kotor:,.0f}<br/>")
    p(f"Biaya Iklan: Rp {biaya_iklan:,.0f}<br/>")
    p(f"Profit Bersih: Rp {profit_bersih:,.0f}<br/>")
    p(f"Dana Cair: Rp {dana_cair:,.0f}<br/>")
    p(f"Dana Belum Cair: Rp {dana_belum_cair:,.0f}<br/>")

    doc.build(content)
    buffer.seek(0)
    return buffer

st.divider()
if st.button("📄 Export PDF – Format ZKS"):
    pdf_file = export_pdf()
    st.download_button(
        "Download PDF",
        pdf_file,
        file_name="Laporan_Keuangan_Shopee_ZKS.pdf",
        mime="application/pdf"
    )
