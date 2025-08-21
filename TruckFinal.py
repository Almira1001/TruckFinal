import streamlit as st
import pandas as pd
import datetime as dt
import calendar
import uuid
from io import BytesIO

# =============================
# Konfigurasi Halaman
# =============================
st.set_page_config(
    page_title="Trucking Planner System",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# Konstanta & Akun Demo
# =============================
STATUS_TRUCKING = [
    "Pending",
    "Confirm Order",
    "otw depo",
    "muat depo",
    "otw pabrik",
    "muat gudang",
    "gate in port"
]

VENDORS_DEFAULT = ["KAMBING", "BINTANG TIMUR", "CAHAYA LOGISTIK", "MAJU JAYA"]
DATE_FMT = "%Y-%m-%d"

ACCOUNTS = {
    "Almira@app.co.id": {"password": "1110", "role": "admin"},
    "kambing@vendor.com": {"password": "123", "role": "vendor", "vendor": "KAMBING"},
    "bintang@vendor.com": {"password": "123", "role": "vendor", "vendor": "BINTANG TIMUR"},
    "cahaya@vendor.com": {"password": "123", "role": "vendor", "vendor": "CAHAYA LOGISTIK"},
    "maju@vendor.com": {"password": "123", "role": "vendor", "vendor": "MAJU JAYA"},
}

# =============================
# Utilitas
# =============================
def today_str():
    return dt.date.today().strftime(DATE_FMT)

def gen_id(prefix="ORD"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def to_date(s: str) -> dt.date:
    return dt.datetime.strptime(s, DATE_FMT).date()

# =============================
# Styling
# =============================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    .main > div {font-family: 'Poppins', sans-serif;}
    .main-header {background: linear-gradient(135deg, #3498db, #2980b9);padding: 1rem 1.2rem;border-radius: 14px;color: #fff;margin-bottom: 1rem;}
    .card {background: #fff;border-radius: 14px;padding: 1rem;box-shadow: 0 4px 14px rgba(0,0,0,.08); margin-bottom: 1rem;}
    .small {font-size:.85rem;color:#6b7280}
    .muted {color:#6b7280}
    .stButton>button {border-radius:10px; font-weight:600}
    /* Kalender */
    .cal-grid {display:grid; grid-template-columns: repeat(7, 1fr); gap:.65rem;}
    .cal-head {text-align:center;font-weight:600;color:#374151;margin-bottom:.25rem}
    .cal-cell {border:2px solid #e11d48;border-radius:12px; padding:.5rem; min-height:72px; display:flex; flex-direction:column; justify-content:space-between}
    .cal-cell.ok {border-color:#16a34a}
    .cal-cell.today {box-shadow:inset 0 0 0 2px #2563eb}
    .cal-top {display:flex; align-items:center; justify-content:space-between; font-weight:600}
    .cal-num {background:#f3f4f6;border-radius:8px;padding:.1rem .45rem}
    .cal-total {font-size:.8rem; color:#111}
    .legend {display:flex; gap:1rem; align-items:center}
    .dot {width:10px;height:10px;border-radius:999px;display:inline-block}
    .dot.green{background:#16a34a}.dot.red{background:#e11d48}.dot.blue{background:#2563eb}
    /* Kartu vendor */
    .v-grid {display:grid; grid-template-columns: repeat(2, 1fr); gap:1rem;}
    .v-card {background:#4f46e5; color:#fff; border-radius:16px; padding:1rem; position:relative}
    .v-title {font-weight:700; letter-spacing:.3px}
    .v-badge {display:inline-block; background:#fff; color:#111; border-radius:8px; padding:.15rem .5rem; font-weight:700; margin-right:.4rem}
    .v-sub {opacity:.9; font-size:.8rem; margin-top:.35rem}

    /* Tabel list & detail ala mockup biru */
    .grid-head {display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr .8fr .8fr .8fr;gap:.5rem;padding:.6rem .75rem;border-bottom:1px solid #eee;font-weight:600;color:#374151;background:#f9fafb;border-top-left-radius:10px;border-top-right-radius:10px}
    .grid-row {display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr .8fr .8fr .8fr;gap:.5rem;padding:.6rem .75rem;align-items:center;border-bottom:1px dashed #e5e7eb}
    .detail-head {display:grid;grid-template-columns:.5fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr .8fr;gap:.4rem;padding:.5rem .75rem;font-weight:600;background:#eef5ff;color:#1f2937;border-top-left-radius:12px;border-top-right-radius:12px;border:1px solid #dbeafe;border-bottom:none}
    .detail-row {display:grid;grid-template-columns:.5fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr .8fr;gap:.4rem;padding:.45rem .75rem;border:1px solid #dbeafe;border-top:none}
    
        /* Injected: show dynamic labels inside each calendar box */
        .cal-cell { position: relative; }
        .cal-cell::after {
            content: var(--lbl20) "\A" var(--lbl40);
            white-space: pre;
            position: absolute;
            left: .55rem;
            bottom: .5rem;
            font-size: .9rem;
            color: #111827;
            font-variant-numeric: tabular-nums;
        }
    
        
        /* Injected: show dynamic labels inside each calendar box */
        .cal-cell { position: relative; }
        .cal-cell::after {
            content: var(--lbl20) "\A" var(--lbl40);
            white-space: pre;
            position: absolute;
            left: .55rem;
            bottom: .5rem;
            font-size: .9rem;
            color: #111827;
            font-variant-numeric: tabular-nums;
        }
    
        </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Inisialisasi Session State
# =============================
def init_state():
    ss = st.session_state
    ss.setdefault("authenticated", False)
    ss.setdefault("user_role", None)
    ss.setdefault("username", None)
    ss.setdefault("vendor_name", None)
    ss.setdefault("order_vendor_prefill", None)

    if "availability" not in ss:
        ss.availability = {}

    ss.setdefault("orders", [])
    ss.setdefault("containers", {})
    ss.setdefault("selected_date_admin", today_str())
    ss.setdefault("selected_date_vendor", today_str())
    ss.setdefault("active_order_for_detail", None)

init_state()

# =============================
# Auth
# =============================
def login_page():
    st.markdown(
        """
        <div class="main-header"><h2 style="margin:0">🚛 Trucking Planner System</h2>
        <div class="small">Sistem Admin & Vendor (demo)</div></div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        u = st.text_input("👤 Username", value="")
        p = st.text_input("🔒 Password", type="password", value="")
        role = st.selectbox("👥 Role", ["", "Admin", "Vendor"], index=0, key="login_role")
        ok = st.form_submit_button("Masuk")
        if ok:
            if u in ACCOUNTS and ACCOUNTS[u]["password"] == p:
                acct = ACCOUNTS[u]
                if (role.lower() == acct["role"]):
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.session_state.user_role = acct["role"]
                    st.session_state.vendor_name = acct.get("vendor") if acct["role"] == "vendor" else None
                    st.rerun()
            st.error("Login gagal. Admin: Almira@app.co.id/1110 | Vendor: kambing@vendor.com/123")

# =============================
# Order helpers
# =============================
def create_order(vendor: str, tgl_stuffing: str, closing_date: str, no_dn: str, shipping_point: str, j20: int, j40: int):
    order_id = gen_id("ORD")
    order = {
        "order_id": order_id,
        "vendor": vendor,
        "tgl_stuffing": tgl_stuffing,
        "closing_date": closing_date,
        "no_dn": no_dn,
        "shipping_point": shipping_point,
        "jml_20ft": int(j20),
        "jml_40ft": int(j40),
        "created_at": dt.datetime.now(),
        "summary_status": "Pending",
    }
    containers = []
    for _ in range(order["jml_20ft"]):
        containers.append({"no": len(containers)+1, "size": "20ft", "accept": None,
                           "no_container": "", "no_seal": "", "no_mobil": "",
                           "nama_supir": "", "contact": "", "depo": "", "status": STATUS_TRUCKING[0]})
    for _ in range(order["jml_40ft"]):
        containers.append({"no": len(containers)+1, "size": "40ft/HC", "accept": None,
                           "no_container": "", "no_seal": "", "no_mobil": "",
                           "nama_supir": "", "contact": "", "depo": "", "status": STATUS_TRUCKING[0]})
    st.session_state.orders.append(order)
    st.session_state.containers[order_id] = containers
    return order_id

def update_order_summary(order_id: str):
    items = st.session_state.containers.get(order_id, [])
    if not items: return
    acc = sum(1 for r in items if r["accept"] is True)
    rej = sum(1 for r in items if r["accept"] is False)
    pen = sum(1 for r in items if r["accept"] is None)
    if pen == 0 and acc > 0 and rej == 0: status = "Accepted"
    elif pen == 0 and rej > 0 and acc == 0: status = "Rejected"
    elif pen == 0 and acc > 0 and rej > 0: status = "Partial"
    else: status = "Pending"
    for o in st.session_state.orders:
        if o["order_id"] == order_id:
            o["summary_status"] = status
            break

# =============================
# ADMIN — Home (sesuai mockup)
# =============================
def admin_home():
    st.markdown("""
        <div class="main-header"><h3 style="margin:0">🏠 Admin — Home</h3>
        <div class="small">Pilih tanggal pada kalender untuk melihat ketersediaan vendor per jenis container.</div></div>
    """, unsafe_allow_html=True)


    # --- Override: Kalender full-fill colors ---
    st.markdown(
        """
        <style>
        /* FULL FILL for calendar cells (red/green) */
        .cal-cell { 
            border: 2px solid #e11d48; 
            border-radius: 12px; 
            padding: .5rem; 
            min-height: 110px; 
            background: #fee2e2; /* default: ≤50% */
            display: flex; 
            flex-direction: column; 
            justify-content: space-between;
        }
        .cal-cell.ok { 
            border-color: #16a34a; 
            background: #dcfce7; /* >50% */
        }
        .cal-cell.today { 
            box-shadow: inset 0 0 0 3px #2563eb; /* ring for today */
        }
        .cal-num { 
            background: rgba(255,255,255,.8);
            border-radius: 8px;
            padding: .1rem .45rem;
        }
        </style>
        """, unsafe_allow_html=True
    )




    # Dropdown Bulan/Tahun
    today = to_date(st.session_state.selected_date_admin)
    colm, coly = st.columns(2)
    with colm:
        month = st.selectbox("Pilih Bulan", list(range(1,13)),
                             index=today.month-1, format_func=lambda x: calendar.month_name[x], key="home_month")
    with coly:
        years = list(range(today.year-1, today.year+2))
        year = st.selectbox("Pilih Tahun", years, index=years.index(today.year), key="home_year")

    # Kalender
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(f"{calendar.month_name[month]} {year}")
    # header day names
    cols = st.columns(7)
    for i, name in enumerate(["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]):
        cols[i].markdown(f"<div class='cal-head'>{name}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)
    kapasitas_total = 156  # asumsi kapasitas untuk pewarnaan
    for week in cal:
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                if d == 0:
                    st.write("")
                    continue
                the_date = dt.date(year, month, d)
                s = the_date.strftime(DATE_FMT)
                data = st.session_state.availability.get(s, {})
                total_20 = sum(v.get("20ft", 0) for v in data.values()) if data else 0
                total_40 = sum(v.get("40ft/HC", 0) for v in data.values()) if data else 0
                total_all = total_20 + total_40
                ok = total_all > kapasitas_total * 0.5
                is_today = (the_date == dt.date.today())

                classes = "cal-cell " + ("ok " if ok else "") + ("today" if is_today else "")
                st.markdown(
    f"<div class='{classes}' style=\"--lbl20:'20ft : {total_20}'; --lbl40:'40ft/HC: {total_40}';\">",
    unsafe_allow_html=True
)
                top = st.columns([1,1])
                with top[0]:
                    st.markdown(f"<div class='cal-num'>{d}</div>", unsafe_allow_html=True)
                with top[1]:
                    st.markdown("<div style='display:none'></div>", unsafe_allow_html=True)

                if st.button("Pilih", key=f"pick_admin_{s}"):
                    st.session_state.selected_date_admin = s
                    st.session_state["show_vendor_detail_admin"] = True
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # legend
    st.markdown(
        "<div class='legend small' style='margin-top:.5rem'>"
        "<span class='dot green'></span> Tersedia Banyak (>50% truck) "
        "<span class='dot red'></span> Tersedia Sedikit (≤50% truck) "
        "<span class='dot blue'></span> Hari ini"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Panel detail vendor utk tanggal terpilih
    target_date = st.session_state.selected_date_admin
    if st.session_state.get("show_vendor_detail_admin", False):
        

        st.markdown(f"#### Detail Ketersediaan — {target_date}")
        avail = st.session_state.availability.get(target_date, {})

        # Rekap tabel: tampilkan SEMUA vendor (0 jika belum mengisi)
        rows = []
        for v in VENDORS_DEFAULT:
            r = avail.get(v, {"20ft": 0, "40ft/HC": 0})
            rows.append((v, int(r.get("20ft", 0)), int(r.get("40ft/HC", 0))))

        # CSS tabel yang bersih & ergonomis
        st.markdown(
            """
            <style>
            .table-wrap { margin:.25rem 0 .5rem 0; }
            .tbl { width:100%; border-collapse:separate; border-spacing:0; font-size:0.95rem; }
            .tbl thead th {
                background: linear-gradient(180deg,#f8fafc,#eef2f7);
                color:#111827; text-align:center; padding:.6rem .75rem;
                border-top:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;
            }
            .tbl thead th:first-child { text-align:left; border-top-left-radius:12px; }
            .tbl thead th:last-child  { border-top-right-radius:12px; }
            .tbl tbody td { padding:.55rem .75rem; border-bottom:1px solid #f0f2f5; }
            .tbl tbody tr:nth-child(even) td { background:#fbfbfd; }
            .tbl tbody tr:nth-child(odd)  td { background:#ffffff; }
            .tbl tbody td:first-child { font-weight:600; }
            .badge {
                display:inline-block; background:#eef2ff; border:1px solid #e5e7eb;
                padding:.15rem .55rem; border-radius:10px; font-variant-numeric: tabular-nums;
            }
            </style>
            """, unsafe_allow_html=True
        )

        # Render HTML tabel
        html = "<div class='table-wrap'><table class='tbl'><thead><tr><th>VENDOR</th><th>20ft</th><th>40ft/HC</th></tr></thead><tbody>"
        for v,a20,a40 in rows:
            html += f"<tr><td>{v}</td><td><span class='badge'>{a20}</span></td><td><span class='badge'>{a40}</span></td></tr>"
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)

# =============================
# ADMIN — Order to Vendor (sinkron tanggal)
# =============================
def admin_order_to_vendor():
    st.markdown("""
        <div class="main-header"><h3 style="margin:0">📦 Admin — Order to Vendor</h3>
        <div class="small">Pilih vendor dari tabel ketersediaan, tanggalnya sinkron dengan Home.</div></div>
    """, unsafe_allow_html=True)

    # Tanggal sinkron Home
    cdate = to_date(st.session_state.selected_date_admin)
    new_date = st.date_input("Tanggal (sinkron Home)", value=cdate, key="admin_date_link")
    if new_date != cdate:
        st.session_state.selected_date_admin = new_date.strftime(DATE_FMT)

    # Tabel ketersediaan per vendor (tanggal terpilih)
    show_date_str = st.session_state.selected_date_admin
    avail = st.session_state.availability.get(show_date_str, {})
    st.caption(f"Menampilkan ketersediaan untuk tanggal: **{show_date_str}**")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div style='display:grid;grid-template-columns:1.8fr .8fr .8fr .8fr;gap:.75rem;padding:.5rem .75rem;border-bottom:1px solid #eee;font-weight:600;color:#374151;background:#f9fafb;border-top-left-radius:10px;border-top-right-radius:10px'>"
                "<div>Vendor</div><div>20ft</div><div>40ft/HC</div><div>Aksi</div></div>", unsafe_allow_html=True)
    for v in VENDORS_DEFAULT:
        row = avail.get(v, {"20ft": 0, "40ft/HC": 0})
        c1, c2, c3, c4 = st.columns([1.8, .8, .8, .8])
        with c1: st.write(v)
        with c2: st.write(row.get("20ft", 0))
        with c3: st.write(row.get("40ft/HC", 0))
        with c4:
            if st.button("Order", key=f"orderbtn_{v}"):
                st.session_state.order_vendor_prefill = v
                st.toast(f"Prefill vendor: {v}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Form Order (prefill vendor & tanggal dari atas)
    st.markdown("#### Buat Order Baru")
    default_vendor_idx = 0
    if st.session_state.order_vendor_prefill in VENDORS_DEFAULT:
        default_vendor_idx = VENDORS_DEFAULT.index(st.session_state.order_vendor_prefill)

    with st.form("form_order_admin"):
        c1, c2, c3 = st.columns(3)
        with c1:
            vendor = st.selectbox("Vendor", VENDORS_DEFAULT, index=default_vendor_idx, key="order_vendor")
            tgl_stuff = st.date_input("Tgl Stuffing", value=to_date(show_date_str), key="order_tglstuff")
            closing = st.date_input("Closing date", value=to_date(show_date_str) + dt.timedelta(days=2), key="order_closing")
        with c2:
            no_dn = st.text_input("No.DN", placeholder="DN0001", key="order_dn")
            ship_point = st.text_input("Shipping Point", placeholder="Jakarta", key="order_shippoint")
        with c3:
            j20 = st.number_input("Jml container 20ft", min_value=0, value=0, key="order_j20")
            j40 = st.number_input("Jml container 40ft/HC", min_value=0, value=0, key="order_j40")
        ok = st.form_submit_button("OK")
        if ok:
            if not no_dn:
                st.error("No.DN wajib diisi.")
            elif j20 + j40 == 0:
                st.error("Minimal pesan 1 container.")
            else:
                # Validasi ketersediaan vendor pada tanggal stuffing
                date_key = tgl_stuff.strftime(DATE_FMT)
                av_for_date = st.session_state.availability.get(date_key, {})
                vendor_av = av_for_date.get(vendor, {"20ft": 0, "40ft/HC": 0})
                has_any = int(vendor_av.get("20ft", 0)) + int(vendor_av.get("40ft/HC", 0)) > 0

                if not has_any:
                    st.error(f"Vendor {vendor} belum mengisi ketersediaan untuk {date_key}. Order tidak dapat dibuat.")
                else:
                    avail20 = int(vendor_av.get("20ft", 0))
                    avail40 = int(vendor_av.get("40ft/HC", 0))

                    # Cek per-size: tidak boleh melebihi ketersediaan vendor
                    if j20 > avail20:
                        st.error(f"Jumlah 20ft yang dipesan ({int(j20)}) melebihi ketersediaan vendor ({avail20}).")
                    elif j40 > avail40:
                        st.error(f"Jumlah 40ft/HC yang dipesan ({int(j40)}) melebihi ketersediaan vendor ({avail40}).")
                    else:
                        oid = create_order(
                            vendor, tgl_stuff.strftime(DATE_FMT), closing.strftime(DATE_FMT), no_dn, ship_point, j20, j40
                        )
                        st.success(f"Order dibuat: {oid}")
                        st.session_state.order_vendor_prefill = None
                        st.rerun()

    st.divider()

    
    # Rekap List Orderan + filter
    st.markdown("#### Rekap List Orderan")
    f1, f2, f3 = st.columns(3)
    with f1:
        vendor_filter = st.selectbox("Filter Vendor", ["-- Semua --"] + VENDORS_DEFAULT, index=0, key="rekap_vendor")
    with f2:
        tgl_start = st.date_input("Tgl Stuffing (start)", value=dt.date.today() - dt.timedelta(days=7), key="rekap_start")
    with f3:
        tgl_end = st.date_input("Tgl Stuffing (end)", value=dt.date.today(), key="rekap_end")

    # Kumpulkan dan render sebagai SATU tabel gabungan
    rows_html = []

    for o in st.session_state.orders:
        d = to_date(o["tgl_stuffing"])
        if not (tgl_start <= d <= tgl_end):
            continue
        if vendor_filter != "-- Semua --" and o["vendor"] != vendor_filter:
            continue

        items = st.session_state.containers.get(o["order_id"], [])

        # Hitung accept/reject per ukuran
        acc20 = sum(1 for r in items if r.get("size") == "20ft" and r.get("accept") is True)
        rej20 = sum(1 for r in items if r.get("size") == "20ft" and r.get("accept") is False)
        acc40 = sum(1 for r in items if r.get("size") == "40ft/HC" and r.get("accept") is True)
        rej40 = sum(1 for r in items if r.get("size") == "40ft/HC" and r.get("accept") is False)

        t20 = o.get("jml_20ft", 0)
        t40 = o.get("jml_40ft", 0)

        # Dua baris per order, dengan rowspan pada kolom info
        rows_html.append(f"""
            <tr>
              <td rowspan='2' style='border:1px solid #e5e7eb; padding:.5rem .6rem'>{o['no_dn']}</td>
              <td rowspan='2' style='border:1px solid #e5e7eb; padding:.5rem .6rem'>{o['vendor']}</td>
              <td rowspan='2' style='border:1px solid #e5e7eb; padding:.5rem .6rem'>{o['tgl_stuffing']}</td>
              <td rowspan='2' style='border:1px solid #e5e7eb; padding:.5rem .6rem'>{o['closing_date']}</td>
              <td rowspan='2' style='border:1px solid #e5e7eb; padding:.5rem .6rem'>{o['shipping_point']}</td>
              <td style='border:1px solid #e5e7eb; padding:.5rem .6rem'>20ft</td>
              <td style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:right'>{int(t20)}</td>
              <td style='border:1px solid #93d1a3; background:#e6f4ea; padding:.5rem .6rem; text-align:center'>{int(acc20)}</td>
              <td style='border:1px solid #e7a19d; background:#fde2e1; padding:.5rem .6rem; text-align:center'>{int(rej20)}</td>
            </tr>
            <tr>
              <td style='border:1px solid #e5e7eb; padding:.5rem .6rem'>40ft/HC</td>
              <td style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:right'>{int(t40)}</td>
              <td style='border:1px solid #93d1a3; background:#e6f4ea; padding:.5rem .6rem; text-align:center'>{int(acc40)}</td>
              <td style='border:1px solid #e7a19d; background:#fde2e1; padding:.5rem .6rem; text-align:center'>{int(rej40)}</td>
            </tr>
        """)

    if rows_html:

        # Hilangkan spasi awal di setiap baris agar tidak dianggap code-block Markdown
        tbody_rows = "\n".join(rows_html)
        tbody_rows = "\n".join(line.lstrip() for line in tbody_rows.splitlines())
        table_html = f"""<table style='width:100%; border-collapse:collapse; font-size:.95rem; margin:.4rem 0'>
  <thead>
    <tr style='background:#f9fafb;color:#374151'>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>No DN</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>Vendor</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>Tanggal Stuffing</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>Closing Date</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>Shipping Point</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>Container</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:right'>Jumlah Container</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:center; background:#e6f4ea'>Accept</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:center; background:#fde2e1'>Reject</th>
    </tr>
  </thead>
  <tbody>
{tbody_rows}
  </tbody>
</table>"""
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("Tidak ada data pada filter ini.")

        # Separator
        st.markdown("<hr style='border:none;border-top:1px dashed #e5e7eb;margin:.6rem 0'/>", unsafe_allow_html=True)



# =============================
# ADMIN — Status Truck
# =============================
def admin_status_truck():
    st.markdown("""
        <div class="main-header"><h3 style="margin:0">🚛 Admin — Status Truck</h3>
        <div class="small">Hasil update dari Vendor (berdasarkan DN)</div></div>
    """, unsafe_allow_html=True)

    anchor = to_date(st.session_state.selected_date_admin)
    period = st.selectbox("Periode", ["Minggu ini", "Bulan ini", "Custom"], key="status_period")
    if period == "Minggu ini":
        start = anchor - dt.timedelta(days=anchor.weekday()); end = start + dt.timedelta(days=6)
    elif period == "Bulan ini":
        start = anchor.replace(day=1); end = anchor.replace(day=calendar.monthrange(anchor.year, anchor.month)[1])
    else:
        c1, c2 = st.columns(2)
        with c1: start = st.date_input("Start", value=anchor - dt.timedelta(days=7), key="status_start")
        with c2: end = st.date_input("End", value=anchor, key="status_end")

    orders = [o for o in st.session_state.orders if start <= to_date(o["tgl_stuffing"]) <= end]
    if not orders:
        st.info("Tidak ada order pada periode ini."); return

    dn_map = {o["no_dn"]: o for o in orders}
    dn_selected = st.selectbox("Pilih No.DN", list(dn_map.keys()), key="status_dn")
    order = dn_map[dn_selected]

    st.markdown("---")
    st.write(
        f"**Vendor:** {order['vendor']} | **Stuffing:** {order['tgl_stuffing']} | **Closing:** {order['closing_date']} | "
        f"**20ft:** {order['jml_20ft']} | **40ft/HC:** {order['jml_40ft']} | **Status Order:** {order['summary_status']}"
    )

    items = st.session_state.containers.get(order["order_id"], [])
    # Hanya baris yang di-OK (accept=True)
    items = [r for r in items if r.get("accept") is True]
    tbl = [{
        "no.": r["no"], "jenis container": r["size"], "no. container": r["no_container"],
        "no.seal": r["no_seal"], "no.mobil": r["no_mobil"], "nama supir": r["nama_supir"],
        "contact": r["contact"], "depo": r["depo"], "status": r["status"],
    } for r in items]
    st.dataframe(pd.DataFrame(tbl), use_container_width=True)

# =============================
# VENDOR — Home
# =============================


# --- Helper to ensure calendar cells are full-filled with colors ---
def inject_calendar_css():
    st.markdown(
        """
        <style>
        .cal-head { font-weight: 600; text-align:center; padding:.25rem 0 .5rem 0; }
        .cal-cell { 
            border: 2px solid #e11d48; 
            border-radius: 12px; 
            padding: .5rem; 
            min-height: 110px; 
            background: #fee2e2; /* default: ≤50% */
            display: flex; 
            flex-direction: column; 
            justify-content: space-between;
        }
        .cal-cell.ok { 
            border-color: #16a34a; 
            background: #dcfce7; /* >0 for vendor; >50% for admin if sudah */
        }
        .cal-cell.today { 
            box-shadow: inset 0 0 0 3px #2563eb; /* ring for today */
        }
        .cal-num { 
            background: rgba(255,255,255,.8);
            border-radius: 8px;
            padding: .1rem .45rem;
            display:inline-block;
        }
        .cal-total {
            background: rgba(255,255,255,.8);
            border-radius: 8px;
            padding: .1rem .45rem;
            font-variant-numeric: tabular-nums;
        }
        </style>
        """, unsafe_allow_html=True
    )



def vendor_home():
    st.markdown("""
        <div class="main-header"><h3 style="margin:0">🏠 Vendor — Home</h3>
        <div class="small">Kalender & update ketersediaan container</div></div>
    """, unsafe_allow_html=True)

    inject_calendar_css()

    vendor_name = st.session_state.get("vendor_name") or "UNKNOWN"
    # Pilihan bulan & tahun sederhana (default: bulan ini)
    today = dt.date.today()
    month = st.session_state.get("v_home_month", today.month)
    year  = st.session_state.get("v_home_year",  today.year)

    colm, coly = st.columns(2)
    with colm:
        month = st.selectbox("Pilih Bulan", list(range(1,13)),
                             index=month-1, format_func=lambda x: calendar.month_name[x], key="v_home_month")
    with coly:
        years = list(range(today.year-1, today.year+2))
        if year not in years:
            year = today.year
        year  = st.selectbox("Pilih Tahun", years, index=years.index(year), key="v_home_year")

    # --- Render Kalender (7 kolom)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    cols = st.columns(7)
    for i, name in enumerate(["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]):
        cols[i].markdown(f"<div class='cal-head'>{name}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                if d == 0:
                    st.write("")
                    continue
                the_date = dt.date(year, month, d)
                s = the_date.strftime(DATE_FMT)

                data = st.session_state.availability.get(s, {})
                row = data.get(vendor_name, {"20ft": 0, "40ft/HC": 0})
                total_20 = int(row.get("20ft", 0))
                total_40 = int(row.get("40ft/HC", 0))
                total_all = total_20 + total_40

                # Vendor: hijau bila ada stok (>0), merah bila 0
                ok = total_all > 0
                is_today = (the_date == dt.date.today())

                classes = "cal-cell " + ("ok " if ok else "") + ("today" if is_today else "")
                st.markdown(
    f"<div class='{classes}' style=\"--lbl20:'20ft : {total_20}'; --lbl40:'40ft/HC: {total_40}';\">",
    unsafe_allow_html=True
)
                top = st.columns([1,1])
                with top[0]:
                    st.markdown(f"<div class='cal-num'>{d}</div>", unsafe_allow_html=True)
                with top[1]:
                    st.markdown("<div style='display:none'></div>", unsafe_allow_html=True)

                if st.button("Pilih", key=f"v_pick_{s}"):
                    st.session_state.selected_date_vendor = s
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Panel input untuk tanggal terpilih (khusus vendor yang login)
    selected = st.session_state.get("selected_date_vendor") or dt.date(year, month, 1).strftime(DATE_FMT)
    st.subheader(f"Ketersediaan Container Anda — {selected}")
    avail = st.session_state.availability.get(selected, {})
    current = avail.get(vendor_name, {"20ft": 0, "40ft/HC": 0})

    c1, c2 = st.columns(2)
    with c1:
        a20 = st.number_input("Jumlah container 20ft", min_value=0, value=int(current.get("20ft", 0)), key=f"v_av20_{selected}")
    with c2:
        a40 = st.number_input("Jumlah container 40ft/HC", min_value=0, value=int(current.get("40ft/HC", 0)), key=f"v_av40_{selected}")

    if st.button("Simpan Ketersediaan", key=f"save_av_{selected}"):
        st.session_state.availability.setdefault(selected, {})[vendor_name] = {"20ft": int(a20), "40ft/HC": int(a40)}
        st.success(f"Ketersediaan {vendor_name} diperbarui untuk {selected}.")
        st.rerun()


# =============================
# VENDOR — Orderan (accept/reject) — hanya melihat order vendor sendiri
# =============================
def vendor_orderan():
    st.markdown("""
        <div class="main-header"><h3 style="margin:0">📑 Vendor — Orderan</h3>
        <div class="small">Terima/Tolak order dari Admin. Gunakan <b>Others</b> untuk partial accept.</div></div>
    """, unsafe_allow_html=True)

    vendor_name = st.session_state.vendor_name
    if not vendor_name:
        st.error("Akun vendor tidak dikenali.")
        return

    orders = [o for o in st.session_state.orders if o["vendor"] == vendor_name]
    if not orders:
        st.info("Belum ada order dari Admin untuk vendor Anda.")
        return

    df = pd.DataFrame([{
        "Order ID": o["order_id"], "Vendor": o["vendor"], "No.DN": o["no_dn"],
        "Tgl Stuffing": o["tgl_stuffing"], "Closing": o["closing_date"],
        "Shipping Point": o["shipping_point"], "20ft": o["jml_20ft"],
        "40ft/HC": o["jml_40ft"], "Status": o["summary_status"],
    } for o in orders])
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Aksi per Order")

    for o in orders:
        with st.expander(f"{o['order_id']} — DN: {o['no_dn']} — Vendor: {o['vendor']}"):
            c1, c2, c3 = st.columns(3)

            if c1.button("Reject", key=f"rej_{o['order_id']}"):
                for r in st.session_state.containers[o["order_id"]]: r["accept"] = False
                update_order_summary(o["order_id"]); st.success("Order ditolak."); st.rerun()
            if c2.button("Accept", key=f"acc_{o['order_id']}"):
                for r in st.session_state.containers[o["order_id"]]:
                    r["accept"] = True
                    if r.get("status", STATUS_TRUCKING[0]) == STATUS_TRUCKING[0]:
                        r["status"] = STATUS_TRUCKING[1]
                update_order_summary(o["order_id"]); st.success("Order diterima."); st.rerun()
            if c3.button("Others", key=f"oth_{o['order_id']}"):
                st.session_state[f"show_partial_{o['order_id']}"] = True

            if st.session_state.get(f"show_partial_{o['order_id']}", False):
                total_20, total_40 = o["jml_20ft"], o["jml_40ft"]
                p1, p2 = st.columns(2)
                with p1:
                    take_20 = st.number_input("Ambil 20ft", min_value=0, max_value=total_20, value=min(1, total_20), key=f"p20_{o['order_id']}")
                with p2:
                    take_40 = st.number_input("Ambil 40ft/HC", min_value=0, max_value=total_40, value=min(1, total_40), key=f"p40_{o['order_id']}")
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("OK", key=f"ok_{o['order_id']}"):
                        cnt20, cnt40 = int(take_20), int(take_40)
                        for r in st.session_state.containers[o["order_id"]]:
                            if r["size"] == "20ft" and cnt20 > 0:
                                r["accept"] = True; cnt20 -= 1
                                if r.get("status", STATUS_TRUCKING[0]) == STATUS_TRUCKING[0]:
                                    r["status"] = STATUS_TRUCKING[1]
                            elif r["size"] == "40ft/HC" and cnt40 > 0:
                                r["accept"] = True; cnt40 -= 1
                                if r.get("status", STATUS_TRUCKING[0]) == STATUS_TRUCKING[0]:
                                    r["status"] = STATUS_TRUCKING[1]
                            else:
                                r["accept"] = False
                        update_order_summary(o["order_id"])
                        st.session_state[f"show_partial_{o['order_id']}"] = False
                        st.success("Partial accept tersimpan."); st.rerun()
                with col_cancel:
                    if st.button("Cancel", key=f"cancel_{o['order_id']}"):
                        st.session_state[f"show_partial_{o['order_id']}"] = False
                        st.rerun()

                # --- Ringkasan hasil isian (per ukuran) ---
                items_now = st.session_state.containers.get(o["order_id"], [])
                sum_rows = []
                for sz in ["20ft","40ft/HC"]:
                    total = sum(1 for r in items_now if r["size"] == sz)
                    acc   = sum(1 for r in items_now if r["size"] == sz and r["accept"] is True)
                    rej   = sum(1 for r in items_now if r["size"] == sz and r["accept"] is False)
                    pen   = sum(1 for r in items_now if r["size"] == sz and r["accept"] is None)
                    sum_rows.append({"Container": sz, "Order": total, "Accept": acc, "Reject": rej, "Pending": pen})
                
                st.caption("Ringkasan per ukuran (hasil aksi di atas):")
                # Tabel mini seperti admin: Container | Jumlah Container | Accept | Reject
                _map = {r["Container"]: r for r in sum_rows}
                _r20 = _map.get("20ft", {"Order":0, "Accept":0, "Reject":0})
                _r40 = _map.get("40ft/HC", {"Order":0, "Accept":0, "Reject":0})
                table_html = f"""<table style='width:100%; border-collapse:collapse; font-size:.95rem; margin:.4rem 0'>
  <thead>
    <tr style="background:#f9fafb;color:#374151">
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:left'>Container</th>
      <th style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:right'>Jumlah Container</th>
      <th style='border:1px solid #93d1a3; background:#e6f4ea; padding:.5rem .6rem; text-align:center'>Accept</th>
      <th style='border:1px solid #e7a19d; background:#fde2e1; padding:.5rem .6rem; text-align:center'>Reject</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style='border:1px solid #e5e7eb; padding:.5rem .6rem'>20ft</td>
      <td style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:right'>{int(_r20["Order"])}</td>
      <td style='border:1px solid #93d1a3; background:#e6f4ea; padding:.5rem .6rem; text-align:center'>{int(_r20["Accept"])}</td>
      <td style='border:1px solid #e7a19d; background:#fde2e1; padding:.5rem .6rem; text-align:center'>{int(_r20["Reject"])}</td>
    </tr>
    <tr>
      <td style='border:1px solid #e5e7eb; padding:.5rem .6rem'>40ft/HC</td>
      <td style='border:1px solid #e5e7eb; padding:.5rem .6rem; text-align:right'>{int(_r40["Order"])}</td>
      <td style='border:1px solid #93d1a3; background:#e6f4ea; padding:.5rem .6rem; text-align:center'>{int(_r40["Accept"])}</td>
      <td style='border:1px solid #e7a19d; background:#fde2e1; padding:.5rem .6rem; text-align:center'>{int(_r40["Reject"])}</td>
    </tr>
  </tbody>
</table>"""
                st.markdown(table_html, unsafe_allow_html=True)

# =============================
# VENDOR — List Orderan (Add Detail) versi tabel + OK di samping status
# =============================
def vendor_list_orderan_add_detail():
    st.markdown("""
        <div class="main-header"><h3 style="margin:0">📋 Vendor — List Orderan (Add Detail)</h3>
        <div class="small">Tampilan list berbentuk <b>tabel</b>. Klik <b>Add Detail</b> untuk membuka <b>satu tabel biru</b> yang bisa diedit seperti contohmu. Untuk menyimpan per baris, centang kolom <b>OK</b> di samping <b>Status</b> lalu klik <b>Simpan baris bertanda OK</b>.</div></div>
    """, unsafe_allow_html=True)

    vendor_name = st.session_state.vendor_name
    if not vendor_name:
        st.error("Akun vendor tidak dikenali.")
        return

    # 1) Tabel List Orderan (hanya milik vendor ini)
    owned_orders = []
    for __o in st.session_state.orders:
        if __o["vendor"] != vendor_name:
            continue
        if __o.get("summary_status") not in ("Accepted", "Partial"):
            continue
        __rows = st.session_state.containers.get(__o["order_id"], [])
        if any((isinstance(__r, dict) and __r.get("accept") is True) for __r in __rows):
            owned_orders.append(__o)
    if not owned_orders:
        st.info("Belum ada order untuk vendor Anda.")
        return

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='grid-head'><div>No.DN</div><div>Tgl Stuffing</div><div>Closing</div><div>Shipping Point</div><div>20FT</div><div>40FT/HC</div><div>Aksi</div></div>", unsafe_allow_html=True)
    for o in owned_orders:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1.2, 1, 1, 1, .8, .8, .8])
        cont = st.session_state.containers.get(o['order_id'], [])
        acc20 = sum(1 for r in cont if r.get('size') == '20ft' and r.get('accept') is True)
        acc40 = sum(1 for r in cont if r.get('size') == '40ft/HC' and r.get('accept') is True)
        with c1: st.write(o["no_dn"])  
        with c2: st.write(o["tgl_stuffing"])  
        with c3: st.write(o["closing_date"])  
        with c4: st.write(o["shipping_point"])  
        with c5: st.write(acc20)  
        with c6: st.write(acc40)  
        with c7:
            if st.button("Add Detail", key=f"add_{o['order_id']}"):
                st.session_state.active_order_for_detail = o["order_id"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # 2) Satu TABEL (editable) ala mockup biru
    selected_id = st.session_state.active_order_for_detail
    if not selected_id:
        return

    order = next((x for x in owned_orders if x["order_id"] == selected_id), None)
    if not order:
        st.warning("Order tidak ditemukan.")
        return

    st.markdown("---")
    st.markdown(f"**Vendor:** {order['vendor']} | **DN:** {order['no_dn']} | **Stuffing:** {order['tgl_stuffing']} | **Closing:** {order['closing_date']} | **Shipping Point:** {order['shipping_point']}")

    items = st.session_state.containers.get(selected_id, [])
    # Hanya tampilkan baris yang sudah di-OK (accept=True)
    items = [r for r in items if r.get('accept') is True]
    # hanya yang di-ACCEPT yang bisa diisi
    accepted = [r for r in items if r.get("accept") is True]
    if not accepted:
        st.info("Order ini belum di-ACCEPT. Mohon ACCEPT dulu di menu *Orderan*.")
        if st.button("⬅️ Kembali ke List"):
            st.session_state.active_order_for_detail = None
            st.rerun()
        return

    # siapkan dataframe editor (semua baris tampil dalam SATU tabel)
    df_src = pd.DataFrame([
        {
            "No.": r["no"],
            "Jenis": r["size"],
            "No. Container": r.get("no_container", ""),
            "No. Seal": r.get("no_seal", ""),
            "No. Mobil": r.get("no_mobil", ""),
            "Nama Supir": r.get("nama_supir", ""),
            "Contact": r.get("contact", ""),
            "Depo": r.get("depo", ""),
            "Status": r.get("status", STATUS_TRUCKING[0]),
            "OK": False,
        }
        for r in accepted
    ])

    edited = st.data_editor(
        df_src,
        key=f"editor_{selected_id}",
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(options=STATUS_TRUCKING),
            "OK": st.column_config.CheckboxColumn(),
        },
    )

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("💾 Simpan baris bertanda OK", use_container_width=True):
            rows = edited.to_dict(orient="records")
            for row in rows:
                if not row.get("OK"):  # hanya baris yang dicentang OK
                    continue
                no = row["No."]
                for r in items:
                    if r["no"] == no and r.get("accept") is True:
                        r["no_container"] = str(row.get("No. Container", ""))
                        r["no_seal"] = str(row.get("No. Seal", ""))
                        r["no_mobil"] = str(row.get("No. Mobil", ""))
                        r["nama_supir"] = str(row.get("Nama Supir", ""))
                        r["contact"] = str(row.get("Contact", ""))
                        r["depo"] = str(row.get("Depo", ""))
                        # validasi Status agar tetap di list
                        status_val = row.get("Status", STATUS_TRUCKING[0])
                        r["status"] = status_val if status_val in STATUS_TRUCKING else STATUS_TRUCKING[0]
                        break
            st.toast("Baris bertanda OK tersimpan.")
            st.rerun()
    with c2:
        if st.button("💾 Simpan SEMUA baris", use_container_width=True):
            rows = edited.to_dict(orient="records")
            for row in rows:
                no = row["No."]
                for r in items:
                    if r["no"] == no and r.get("accept") is True:
                        r["no_container"] = str(row.get("No. Container", ""))
                        r["no_seal"] = str(row.get("No. Seal", ""))
                        r["no_mobil"] = str(row.get("No. Mobil", ""))
                        r["nama_supir"] = str(row.get("Nama Supir", ""))
                        r["contact"] = str(row.get("Contact", ""))
                        r["depo"] = str(row.get("Depo", ""))
                        status_val = row.get("Status", STATUS_TRUCKING[0])
                        r["status"] = status_val if status_val in STATUS_TRUCKING else STATUS_TRUCKING[0]
                        break
            st.toast("Semua baris tersimpan.")
            st.rerun()
    with c3:
        if st.button("⬅️ Kembali ke List", use_container_width=True):
            st.session_state.active_order_for_detail = None
            st.rerun()

# =============================
# Sidebar & Routing
# =============================
def sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div style='text-align:center;padding:.75rem'>
            <h2 style='margin:.25rem 0'>🚛 Trucking Planner</h2>
            <div class='small'>Hi, <b>{st.session_state.username or '-'}</b></div>
            <div class='small'>Role: <b>{(st.session_state.user_role or '').title()}</b></div>
            {"<div class='small'>Vendor: <b>" + (st.session_state.vendor_name or "-") + "</b></div>" if st.session_state.user_role=="vendor" else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        role = st.session_state.user_role
        if role == "admin":
            menu = st.radio("Menu", ["🏠 Home", "📦 Order to Vendor", "🚛 Status Truck"], label_visibility="visible", key="menu_admin")
        else:
            menu = st.radio("Menu", ["🏠 Home", "📑 Orderan", "📋 List Orderan (Add Detail)"], label_visibility="visible", key="menu_vendor")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in ["authenticated", "user_role", "username", "vendor_name", "order_vendor_prefill", "show_vendor_detail_admin", "active_order_for_detail"]:
                st.session_state[k] = None if k not in ["authenticated"] else False
            st.rerun()

        st.caption(f"Last Update: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')} | v1.5")
    return menu

# =============================
# Entry Point
# =============================

def main():
    if not st.session_state.authenticated:
        login_page()
        return

    menu = sidebar()
    role = st.session_state.user_role

    if role == "admin":
        if menu == "🏠 Home":
            admin_home()
        elif menu == "📦 Order to Vendor":
            admin_order_to_vendor()
        elif menu == "🚛 Status Truck":
            admin_status_truck()
    else:
        if menu == "🏠 Home":
            vendor_home()
        elif menu == "📑 Orderan":
            vendor_orderan()
        elif menu == "📋 List Orderan (Add Detail)":
            vendor_list_orderan_add_detail()

if __name__ == "__main__":
    main()
