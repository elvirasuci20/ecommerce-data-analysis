import calendar
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Dashboard E-Commerce Olist 2016-2018", page_icon="🛒", layout="wide")

BASE = Path(__file__).parent

_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
FULL_WIDTH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}


def show_plot(fig):
    st.plotly_chart(fig, **FULL_WIDTH)


PRIMARY, ACCENT, MUTED, AMBER = "#1F6FB2", "#E4572E", "#B8C2CC", "#F2A541"
SEGMENT_ORDER = ["At Risk (Bernilai Tinggi)", "Big Spender Baru", "Hibernating",
                 "Pelanggan Baru", "Loyal (Lapsed)", "Champions"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "main_data.csv", parse_dates=["order_purchase_timestamp"])
    geo = pd.read_csv(BASE / "state_geo.csv")
    return df, geo


def rupiah_free(value):
    """Format angka R$ (Real Brasil) ringkas."""
    if value >= 1e6:
        return f"R$ {value / 1e6:,.2f} jt"
    if value >= 1e3:
        return f"R$ {value / 1e3:,.0f} rb"
    return f"R$ {value:,.0f}"


df, state_geo = load_data()

# SIDEBAR
st.sidebar.title("Filter Data")
st.sidebar.caption("Dataset: E-Commerce Public Dataset (Olist)")

min_d, max_d = df.order_purchase_timestamp.min().date(), df.order_purchase_timestamp.max().date()


def date_picker(label, default, key):
    """Pilih tanggal lewat tiga dropdown: tahun, bulan, tanggal."""
    st.sidebar.markdown(f"**{label}**")
    c_y, c_m, c_d = st.sidebar.columns([1.2, 1.2, 1])
    years = list(range(min_d.year, max_d.year + 1))
    year = c_y.selectbox("Tahun", years, index=years.index(default.year), key=f"{key}_y")
    month = c_m.selectbox("Bulan", list(range(1, 13)), index=default.month - 1,
                          format_func=lambda m: MONTH_NAMES[m - 1], key=f"{key}_m")
    n_days = calendar.monthrange(year, month)[1]
    day = c_d.selectbox("Tgl", list(range(1, n_days + 1)), index=min(default.day, n_days) - 1, key=f"{key}_d")
    return date(year, month, day)


start_d = date_picker("Tanggal mulai", min_d, "start")
end_d = date_picker("Tanggal akhir", max_d, "end")
if start_d > end_d:
    st.sidebar.error("Tanggal mulai setelah tanggal akhir, rentang ditukar otomatis.")
    start_d, end_d = end_d, start_d

states = sorted(df.customer_state.dropna().unique())
sel_states = st.sidebar.multiselect("State pelanggan", states, default=[], placeholder="Semua state")

top_cats = (df[~df.order_status.isin(["canceled", "unavailable"])].groupby("category").price.sum()
            .sort_values(ascending=False).index.tolist())
sel_cats = st.sidebar.multiselect("Kategori produk", top_cats, default=[], placeholder="Semua kategori")

mask = (df.order_purchase_timestamp.dt.date >= start_d) & (df.order_purchase_timestamp.dt.date <= end_d)
if sel_states:
    mask &= df.customer_state.isin(sel_states)
if sel_cats:
    mask &= df.category.isin(sel_cats)
fdf = df[mask]
sales = fdf[~fdf.order_status.isin(["canceled", "unavailable"])]
orders = sales.drop_duplicates("order_id")

st.title("🛒 Dashboard Analisis E-Commerce Olist (2016-2018)")
with st.expander("Definisi metrik yang digunakan"):
    st.markdown(
        """
        - **Revenue:** jumlah harga barang (tanpa ongkos kirim) dari pesanan yang tidak dibatalkan.
        - **Review score:** rata-rata skor review per pesanan (skala 1-5).
        - **Keterlambatan:** barang tiba setelah tanggal estimasi pengiriman.
        """
    )

if sales.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini. Silakan ubah filter pada sidebar.")
    st.stop()

# KPI
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Revenue", rupiah_free(sales.price.sum()))
c2.metric("Total Pesanan", f"{orders.order_id.nunique():,}")
c3.metric("Pelanggan Unik", f"{orders.customer_unique_id.nunique():,}")
c4.metric("Rata-rata Review", f"{orders.review_score.mean():.2f}" if orders.review_score.notna().any() else "-")
c5.metric("Rata-rata Kirim", f"{orders.delivery_days.mean():.1f} hari" if orders.delivery_days.notna().any() else "-")
c6.metric("Pesanan Terlambat", f"{orders.is_late.mean() * 100:.1f}%" if orders.is_late.notna().any() else "-")

tab1, tab2, tab3 = st.tabs(["Pertanyaan 1: Produk & Penjualan", "Pertanyaan 2: Wilayah & Pengiriman",
                            "Analisis Lanjutan: RFM & Binning"])

# TAB 1
with tab1:
    st.subheader("Kategori produk apa yang masuk Top 10 berdasarkan total revenue, serta bagaimana review score dan tren revenue bulanannya?")
    n_top = st.slider("Jumlah kategori teratas", 5, 15, 10)

    cat = sales.groupby("category").agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
    cat["share"] = cat.revenue / cat.revenue.sum() * 100
    cat["avg_review"] = sales.drop_duplicates(["order_id", "category"]).groupby("category").review_score.mean()
    cat["aov"] = cat.revenue / cat.orders
    top = cat.sort_values("revenue", ascending=False).head(n_top)
    overall_review = orders.review_score.mean()

    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        t = top.iloc[::-1].reset_index()
        colors = [PRIMARY if i >= len(t) - 3 else MUTED for i in range(len(t))]
        fig = go.Figure(go.Bar(
            x=t.revenue / 1e6, y=t.category, orientation="h", marker_color=colors,
            text=[f"R$ {r / 1e6:.2f} jt ({s:.1f}%)" for r, s in zip(t.revenue, t.share)], textposition="outside",
            hovertemplate="%{y}<br>Revenue: R$ %{x:.2f} jt<extra></extra>"))
        fig.update_layout(title=f"Top {n_top} kategori = {top.share.sum():.1f}% dari revenue",
                          xaxis_title="Total revenue (juta R$)", yaxis_title=None, height=480,
                          margin=dict(l=0, r=40, t=50, b=0), xaxis=dict(range=[0, t.revenue.max() / 1e6 * 1.45]))
        show_plot(fig)
    with col_b:
        t = top.iloc[::-1].reset_index()
        fig = go.Figure(go.Scatter(
            x=t.avg_review, y=t.category, mode="markers+text", text=[f"{v:.2f}" for v in t.avg_review],
            textposition="middle right",
            marker=dict(size=13, color=[ACCENT if v < overall_review else PRIMARY for v in t.avg_review]),
            hovertemplate="%{y}<br>Review: %{x:.2f}<extra></extra>"))
        fig.add_vline(x=overall_review, line_dash="dash", line_color="black",
                      annotation_text=f"Rata-rata {overall_review:.2f}", annotation_position="bottom")
        fig.update_layout(title="Review score per kategori", height=480, yaxis_title=None,
                          xaxis=dict(title="Rata-rata review (merah = di bawah rata-rata)", range=[3.7, 4.4]),
                          margin=dict(l=0, r=20, t=50, b=0))
        fig.update_yaxes(showticklabels=False)
        show_plot(fig)

    monthly = sales.groupby("order_month").agg(revenue=("price", "sum"), orders=("order_id", "nunique")).reset_index()
    monthly = monthly[monthly.orders >= 500]       # abaikan bulan dengan data sangat sedikit
    fig = px.line(monthly, x="order_month", y="revenue", markers=True, color_discrete_sequence=[PRIMARY])
    fig.update_traces(hovertemplate="%{x}<br>Revenue: R$ %{y:,.0f}<extra></extra>")
    if not monthly.empty:
        pk = monthly.loc[monthly.revenue.idxmax()]
        fig.add_annotation(x=pk.order_month, y=pk.revenue, text=f"Puncak {pk.order_month}: {rupiah_free(pk.revenue)}",
                           showarrow=True, arrowcolor=ACCENT, font=dict(color=ACCENT), ay=-40)
    fig.update_layout(title="Tren revenue bulanan (bulan dengan <500 pesanan tidak ditampilkan)",
                      xaxis_title=None, yaxis_title="Revenue (R$)", height=380, margin=dict(l=0, r=0, t=50, b=0))
    show_plot(fig)

    col_c, col_d = st.columns([1, 1.2])
    with col_c:
        pay = orders.payment_type.value_counts(normalize=True).mul(100).rename_axis("payment").reset_index(name="pct")
        label_map = {"credit_card": "Kartu kredit", "boleto": "Boleto", "voucher": "Voucher",
                     "debit_card": "Kartu debit", "unknown": "Tidak terdefinisi"}
        pay["label"] = pay.payment.map(label_map)
        fig = px.bar(pay.iloc[::-1], x="pct", y="label", orientation="h", text=pay.iloc[::-1].pct.map("{:.1f}%".format),
                     color=pay.iloc[::-1].payment.eq("credit_card"),
                     color_discrete_map={True: ACCENT, False: MUTED})
        fig.update_layout(title="Metode pembayaran utama (% pesanan)", showlegend=False, height=330,
                          xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=20, t=50, b=0),
                          xaxis=dict(range=[0, 100]))
        show_plot(fig)
    with col_d:
        st.markdown("**Ringkasan kategori**")
        show = top.reset_index().rename(columns={"category": "Kategori", "revenue": "Revenue (R$)", "orders": "Pesanan",
                                                 "share": "Kontribusi (%)", "avg_review": "Review", "aov": "Nilai/Pesanan (R$)"})
        st.dataframe(show.style.format({"Revenue (R$)": "{:,.0f}", "Kontribusi (%)": "{:.1f}", "Review": "{:.2f}",
                                        "Nilai/Pesanan (R$)": "{:,.0f}"}), hide_index=True, **FULL_WIDTH)

# TAB 2
with tab2:
    st.subheader("Di mana pelanggan dan seller terkonsentrasi, dan bagaimana waktu pengiriman serta keterlambatan tiap state?")
    st_sum = orders.groupby("customer_state").agg(
        customers=("customer_unique_id", "nunique"), orders=("order_id", "nunique"),
        avg_days=("delivery_days", "mean"), late_pct=("is_late", lambda s: s.mean() * 100),
        avg_review=("review_score", "mean"))
    st_sum["sellers"] = sales.groupby("seller_state").seller_id.nunique()
    st_sum["sellers"] = st_sum.sellers.fillna(0).astype(int)
    st_sum["revenue"] = sales.groupby("customer_state").price.sum()
    st_sum["customer_share"] = st_sum.customers / st_sum.customers.sum() * 100
    all_sellers = sales.groupby("seller_state").seller_id.nunique()
    st_sum["seller_share"] = st_sum.sellers / max(all_sellers.sum(), 1) * 100
    st_sum = st_sum.sort_values("customers", ascending=False)
    nat_days, nat_late = orders.delivery_days.mean(), orders.is_late.mean() * 100

    left, right = st.columns(2)
    with left:
        t = st_sum.head(10).iloc[::-1].reset_index()
        fig = go.Figure()
        fig.add_bar(y=t.customer_state, x=t.customer_share, orientation="h", name="Pelanggan", marker_color=PRIMARY,
                    text=t.customer_share.map("{:.1f}%".format), textposition="outside")
        fig.add_bar(y=t.customer_state, x=t.seller_share, orientation="h", name="Seller", marker_color=AMBER,
                    text=t.seller_share.map("{:.1f}%".format), textposition="outside")
        fig.update_layout(barmode="group", title="Pelanggan vs seller (10 state teratas)",
                          xaxis_title="% dari total", height=520, margin=dict(l=0, r=30, t=50, b=0),
                          legend=dict(orientation="h", y=-0.12),
                          xaxis=dict(range=[0, max(t.customer_share.max(), t.seller_share.max()) * 1.25]))
        show_plot(fig)
    with right:
        t = st_sum.dropna(subset=["avg_days"]).sort_values("avg_days")
        fig = go.Figure(go.Bar(
            y=t.index, x=t.avg_days, orientation="h",
            marker_color=[ACCENT if v > nat_days else MUTED for v in t.avg_days],
            text=t.avg_days.map("{:.1f}".format), textposition="outside",
            customdata=np.stack([t.late_pct, t.avg_review, t.customers], axis=1),
            hovertemplate="%{y}<br>Rata-rata kirim: %{x:.1f} hari<br>Terlambat: %{customdata[0]:.1f}%"
                          "<br>Review: %{customdata[1]:.2f}<br>Pelanggan: %{customdata[2]:,.0f}<extra></extra>"))
        fig.add_vline(x=nat_days, line_dash="dash", line_color="black", annotation_text=f"Rata-rata {nat_days:.1f} hari")
        fig.update_layout(title="Rata-rata waktu pengiriman per state", height=520,
                          xaxis_title="Hari", yaxis_title=None, margin=dict(l=0, r=30, t=50, b=0),
                          xaxis=dict(range=[0, t.avg_days.max() * 1.2]))
        show_plot(fig)

    left, right = st.columns(2)
    with left:
        t = st_sum.dropna(subset=["late_pct"]).sort_values("late_pct")
        fig = go.Figure(go.Bar(
            y=t.index, x=t.late_pct, orientation="h",
            marker_color=[ACCENT if v > nat_late else MUTED for v in t.late_pct],
            text=t.late_pct.map("{:.1f}%".format), textposition="outside"))
        fig.add_vline(x=nat_late, line_dash="dash", line_color="black", annotation_text=f"Nasional {nat_late:.1f}%")
        fig.update_layout(title="Persentase pesanan terlambat per state", height=560, xaxis_title="% pesanan terlambat",
                          yaxis_title=None, margin=dict(l=0, r=30, t=50, b=0),
                          xaxis=dict(range=[0, t.late_pct.max() * 1.2]))
        show_plot(fig)
    with right:
        geo = st_sum.reset_index().merge(state_geo, left_on="customer_state", right_on="state", how="left").dropna(subset=["lat", "lng"])
        fig = px.scatter_geo(geo, lat="lat", lon="lng", size="customers", color="avg_days", hover_name="customer_state",
                             hover_data={"customers": ":,", "avg_days": ":.1f", "late_pct": ":.1f", "avg_review": ":.2f",
                                         "lat": False, "lng": False},
                             color_continuous_scale="YlOrRd", size_max=55, scope="south america",
                             labels={"avg_days": "Hari kirim", "customers": "Pelanggan"})
        fig.update_geos(lataxis_range=[-35, 6], lonaxis_range=[-75, -32], showcountries=True, countrycolor="#999",
                        showland=True, landcolor="#F4F4F4", showocean=True, oceancolor="#EAF2F8")
        fig.update_layout(title="Peta pelanggan dan lama pengiriman", height=560,
                          margin=dict(l=0, r=0, t=50, b=0))
        show_plot(fig)

    worst = st_sum[st_sum.customers >= 300].sort_values("late_pct", ascending=False).head(3)
    if not worst.empty:
        txt = ", ".join(f"**{i}** ({r.late_pct:.1f}% terlambat, review {r.avg_review:.2f})" for i, r in worst.iterrows())
        st.info(f"State prioritas perbaikan logistik (minimal 300 pelanggan pada filter saat ini): {txt}.")

# TAB 3
with tab3:
    st.subheader("RFM Analysis")
    st.info(
        """
        **Cara membaca RFM**
        - **Recency (R):** hari sejak pembelian terakhir. Semakin kecil, semakin baik.
        - **Frequency (F):** jumlah pesanan pelanggan.
        - **Monetary (M):** total belanja pelanggan (R$).

        **Metode skor:** R dan F memakai binning manual (`pd.cut`), M memakai kuartil (`pd.qcut`).
        Hasil mengikuti filter periode, state, dan kategori pada sidebar.
        """
    )
    ref_date = sales.order_purchase_timestamp.max() + pd.Timedelta(days=1)
    rfm = (sales.groupby("customer_unique_id")
           .agg(last_purchase=("order_purchase_timestamp", "max"), frequency=("order_id", "nunique"),
                monetary=("price", "sum")).reset_index())
    rfm["recency"] = (ref_date - rfm.last_purchase).dt.days
    rfm["R"] = pd.cut(rfm.recency, bins=[-1, 90, 180, 365, 100000], labels=[4, 3, 2, 1]).astype(int)
    rfm["F"] = pd.cut(rfm.frequency, bins=[0, 1, 2, 10000], labels=[1, 2, 3]).astype(int)
    try:
        rfm["M"] = pd.qcut(rfm.monetary, 4, labels=[1, 2, 3, 4]).astype(int)
    except ValueError:      # batas kuartil kembar (data filter sangat sedikit)
        try:
            rfm["M"] = pd.qcut(rfm.monetary.rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
        except ValueError:  # hanya 1-3 pelanggan pada filter: kuartil tidak bisa dibuat
            rfm["M"] = 1

    def segment(r):
        if r.F >= 2 and r.R >= 3:
            return "Champions"
        if r.F >= 2:
            return "Loyal (Lapsed)"
        if r.R >= 3 and r.M >= 3:
            return "Big Spender Baru"
        if r.R >= 3:
            return "Pelanggan Baru"
        if r.M >= 3:
            return "At Risk (Bernilai Tinggi)"
        return "Hibernating"

    rfm["segment"] = rfm.apply(segment, axis=1)
    seg = rfm.groupby("segment").agg(customers=("customer_unique_id", "count"), avg_recency=("recency", "mean"),
                                     avg_frequency=("frequency", "mean"), avg_monetary=("monetary", "mean"),
                                     total_monetary=("monetary", "sum")).reindex(SEGMENT_ORDER).dropna()
    seg["customer_pct"] = seg.customers / seg.customers.sum() * 100
    seg["revenue_pct"] = seg.total_monetary / seg.total_monetary.sum() * 100

    l, r = st.columns([1.2, 1])
    with l:
        t = seg.iloc[::-1].reset_index()
        fig = go.Figure()
        fig.add_bar(y=t.segment, x=t.customer_pct, orientation="h", name="% pelanggan", marker_color=MUTED,
                    text=t.customer_pct.map("{:.1f}%".format), textposition="outside")
        fig.add_bar(y=t.segment, x=t.revenue_pct, orientation="h", name="% revenue", marker_color=PRIMARY,
                    text=t.revenue_pct.map("{:.1f}%".format), textposition="outside")
        fig.update_layout(barmode="group", title="Porsi pelanggan vs porsi revenue per segmen RFM", height=460,
                          xaxis_title="Persentase (%)", yaxis_title=None, legend=dict(orientation="h", y=-0.15),
                          margin=dict(l=0, r=30, t=50, b=0),
                          xaxis=dict(range=[0, max(t.customer_pct.max(), t.revenue_pct.max()) * 1.25]))
        show_plot(fig)
    with r:
        st.dataframe(seg.rename(columns={"customers": "Pelanggan", "avg_recency": "Rata2 Recency (hari)",
                                         "avg_frequency": "Rata2 Frekuensi", "avg_monetary": "Rata2 Monetary (R$)",
                                         "total_monetary": "Total (R$)", "customer_pct": "% Pelanggan",
                                         "revenue_pct": "% Revenue"}).style.format(
            {"Pelanggan": "{:,.0f}", "Rata2 Recency (hari)": "{:.0f}", "Rata2 Frekuensi": "{:.2f}",
             "Rata2 Monetary (R$)": "{:,.0f}", "Total (R$)": "{:,.0f}", "% Pelanggan": "{:.1f}", "% Revenue": "{:.1f}"}),
            **FULL_WIDTH)
        one_time = (rfm.frequency == 1).mean() * 100
        st.metric("Pelanggan yang hanya membeli 1x", f"{one_time:.1f}%")

    st.subheader("Clustering dengan Binning: lama pengiriman vs review score")
    o = orders.dropna(subset=["delivery_days"]).copy()
    o["bin"] = pd.cut(o.delivery_days, bins=[-1, 7, 14, 21, 1000], labels=["<= 7 hari", "8-14 hari", "15-21 hari", "> 21 hari"])
    b = o.groupby("bin", observed=True).agg(orders=("order_id", "count"), avg_review=("review_score", "mean")).reset_index()
    b["pct"] = b.orders / b.orders.sum() * 100
    fig = go.Figure(go.Bar(x=b.bin.astype(str), y=b.avg_review,
                           marker_color=[ACCENT if x == "> 21 hari" else MUTED for x in b.bin.astype(str)],
                           text=[f"{v:.2f}<br>({p:.0f}% pesanan)" for v, p in zip(b.avg_review, b.pct)], textposition="outside"))
    fig.update_layout(title="Review score menurun tajam ketika pengiriman melebihi 21 hari",
                      yaxis=dict(range=[0, 5.5], title="Rata-rata review"),
                      xaxis_title="Kelompok lama pengiriman", height=400, margin=dict(l=0, r=0, t=50, b=0))
    show_plot(fig)

st.caption("Proyek Analisis Data | Elvira Tiara Suci Tambunan | ds284b6x0513")
