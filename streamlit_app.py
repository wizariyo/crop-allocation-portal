from contextlib import contextmanager
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

DB_FILE = Path(__file__).resolve().parent / "crop_allocation.db"

# Master Configuration
SOILS = ["Alluvial", "Black", "Red", "Sandy"]
SEASONS = ["Kharif", "Rabi", "Zaid"]
CONDITIONS = ["Normal", "Pest or disease affected", "Drought or flood affected"]
RESOURCES = ["Fertilizer", "Subsidy"]
FERTILIZERS = ["Urea", "DAP", "Potash"]
SCHEMES = ["Seed", "Equipment", "Irrigation"]
UNITS = ["kg", "units"]

CROPS_INFO = {
    ("Alluvial", "Kharif"): {"crop": "Rice", "icon": "🌾", "tip": "High water requirement. Ideal for rich alluvial floodplains."},
    ("Alluvial", "Rabi"): {"crop": "Wheat", "icon": "🌾", "tip": "Cool vegetative stage with bright sunny ripening weather."},
    ("Alluvial", "Zaid"): {"crop": "Watermelon", "icon": "🍉", "tip": "Quick summer cash crop with high moisture absorption."},
    ("Black", "Kharif"): {"crop": "Cotton", "icon": "🌱", "tip": "Deep moisture-retentive black soil; excellent boll development."},
    ("Black", "Rabi"): {"crop": "Chickpea", "icon": "🧆", "tip": "Nitrogen-fixing pulse; minimal irrigation needed."},
    ("Black", "Zaid"): {"crop": "Sunflower", "icon": "🌻", "tip": "Drought-hardy oilseed suitable for warm summer rotation."},
    ("Red", "Kharif"): {"crop": "Groundnut", "icon": "🥜", "tip": "Porous red soil supports easy peg entry and high pod yield."},
    ("Red", "Rabi"): {"crop": "Lentil", "icon": "🍲", "tip": "Prefers cool climate and well-aerated light soils."},
    ("Red", "Zaid"): {"crop": "Moong", "icon": "🌿", "tip": "Fast 60-day legume that restores soil fertility."},
    ("Sandy", "Kharif"): {"crop": "Pearl Millet (Bajra)", "icon": "🌾", "tip": "Thrives in arid climates with exceptional drought resistance."},
    ("Sandy", "Rabi"): {"crop": "Mustard", "icon": "🌼", "tip": "Low water footprint with high oil percentage."},
    ("Sandy", "Zaid"): {"crop": "Muskmelon", "icon": "🍈", "tip": "Warm sandy tracts produce high-brix sweet melons."},
}

# Database Helpers
@contextmanager
def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def init_db():
    with connect_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS farmers (
                farmer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                contact TEXT NOT NULL UNIQUE,
                village TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS requests (
                request_id INTEGER PRIMARY KEY,
                farmer_id INTEGER NOT NULL,
                resource INTEGER NOT NULL,
                crop TEXT NOT NULL,
                area REAL NOT NULL,
                farm_condition INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                detail TEXT NOT NULL,
                allocated INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id)
            )"""
        )

def calculate_need_score(area: float, condition_idx: int, resource_idx: int) -> int:
    if resource_idx == 0:
        cond_pts = [0, 10, 30, 40]
        land_pts = [20, 15, 10]
    else:
        cond_pts = [0, 10, 35, 50]
        land_pts = [25, 20, 15]
    land_score = land_pts[0] if area <= 2 else land_pts[1] if area <= 5 else land_pts[2]
    return cond_pts[condition_idx] + land_score

def seed_demo_data():
    sample_farmers = [
        (1001, "Ramesh Kumar", "9876543210", "Rampur"),
        (1002, "Sunita Devi", "9812345678", "Kalyanpur"),
        (1003, "Baldev Singh", "9765432109", "Fatehgarh"),
        (1004, "Anoop Sharma", "9923456781", "Bhopalpur"),
    ]
    sample_requests = [
        (1, 1001, 0, "Wheat", 1.8, 3, 200, "Urea", 0, "Pending"),
        (2, 1002, 1, "Mustard", 3.5, 2, 2, "Irrigation", 1, "Partially Allocated"),
        (3, 1003, 0, "Cotton", 6.0, 1, 400, "DAP", 400, "Allocated"),
        (4, 1004, 1, "Rice", 1.5, 2, 5, "Seed", 0, "Pending"),
    ]
    with connect_db() as conn:
        for f in sample_farmers:
            conn.execute("INSERT OR IGNORE INTO farmers VALUES (?, ?, ?, ?)", f)
        for r in sample_requests:
            conn.execute("INSERT OR IGNORE INTO requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", r)

def get_farmer_by_id(farmer_id: int):
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM farmers WHERE farmer_id = ?", (farmer_id,)).fetchone()
        return dict(row) if row else None

def get_farmer_by_contact(contact: str):
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM farmers WHERE contact = ?", (contact,)).fetchone()
        return dict(row) if row else None

# Modern CSS
def apply_custom_css():
    st.markdown(
        """
        <style>
        /* Hide Streamlit default header and footer */
        header[data-testid="stHeader"], footer, [data-testid="stToolbar"] {
            display: none !important;
        }
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px !important;
        }
        /* Clean input styling */
        input, textarea, div[data-baseweb="base-input"], div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-color: #cbd5e1 !important;
        }
        input {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }
        div[data-baseweb="select"] span, div[data-baseweb="select"] div {
            color: #0f172a !important;
        }
        /* Base Styling */
        .stApp {
            background-color: #f8fafc;
        }
        
        /* Auth Container */
        .auth-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 36px 32px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
            margin-top: 20px;
        }
        
        .auth-title {
            text-align: center;
            font-size: 26px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 6px;
        }
        
        .auth-subtitle {
            text-align: center;
            font-size: 14px;
            color: #64748b;
            margin-bottom: 24px;
        }

        /* Top App Bar */
        .top-nav {
            background: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            padding: 14px 24px;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }

        .metric-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }
        .metric-val {
            font-size: 28px;
            font-weight: 800;
            color: #047857;
            margin-top: 4px;
        }
        .metric-lbl {
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 600;
        }

        .badge-pending {
            background-color: #fef3c7;
            color: #b45309;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 12px;
            border: 1px solid #fde68a;
        }
        .badge-partial {
            background-color: #e0f2fe;
            color: #0369a1;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 12px;
            border: 1px solid #bae6fd;
        }
        .badge-allocated {
            background-color: #dcfce7;
            color: #15803d;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 12px;
            border: 1px solid #86efac;
        }

        .content-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }

        .score-pill {
            background: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            padding: 4px 12px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# 1. AUTH SCREEN (Clean Gatekeeper)
def render_auth_page():
    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 30px;">
                <div style="font-size: 50px;">🌾</div>
                <h1 style="font-size: 28px; font-weight: 800; color: #065f46; margin-bottom: 4px;">AgriAlloc Portal</h1>
                <p style="color: #64748b; font-size: 15px;">Smart Crop Matching & Priority Resource Allocation</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        role = st.segmented_control(
            "Select Account Type",
            options=["🧑‍🌾 Farmer Login", "📝 New Farmer Register"],
            default="🧑‍🌾 Farmer Login",
            label_visibility="collapsed"
        )

        # A. Farmer Login
        if role == "🧑‍🌾 Farmer Login":
            with st.container(border=True):
                st.markdown("#### 🔐 Farmer Sign In")
                st.caption("Access crop recommendations, submit requests, and track allocations.")

                with st.form("farmer_login_form"):
                    fid = st.number_input("Farmer ID", min_value=1000, max_value=999999, step=1, value=1001, help="Your permanent 4+ digit Farmer ID")
                    contact = st.text_input("10-Digit Mobile Number", max_chars=10, value="9876543210")
                    submitted = st.form_submit_button("Sign In to Portal", type="primary", use_container_width=True)

                if submitted:
                    farmer = get_farmer_by_id(fid)
                    if farmer and farmer["contact"] == contact.strip():
                        st.session_state["user_role"] = "farmer"
                        st.session_state["user_data"] = farmer
                        st.toast(f"Welcome back, {farmer['name']}!", icon="👋")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Farmer ID or Mobile Number. Please check or Register.")

                st.divider()
                st.caption("💡 Quick test accounts:")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    if st.button("Ramesh (#1001)", use_container_width=True):
                        seed_demo_data()
                        st.session_state["user_role"] = "farmer"
                        st.session_state["user_data"] = get_farmer_by_id(1001)
                        st.rerun()
                with col_d2:
                    if st.button("Sunita (#1002)", use_container_width=True):
                        seed_demo_data()
                        st.session_state["user_role"] = "farmer"
                        st.session_state["user_data"] = get_farmer_by_id(1002)
                        st.rerun()

        # B. New Farmer Registration
        else:
            with st.container(border=True):
                st.markdown("#### 📝 Register as New Farmer")
                st.caption("Create your agricultural account to access government subsidies.")

                with st.form("farmer_reg_form"):
                    name = st.text_input("Full Name", placeholder="e.g. Balwinder Singh").strip()
                    contact = st.text_input("10-Digit Mobile Number", max_chars=10, placeholder="e.g. 9876512345").strip()
                    village = st.text_input("Village / Tehsil", placeholder="e.g. Rampur, Ludhiana").strip()
                    submitted = st.form_submit_button("Complete Registration", type="primary", use_container_width=True)

                if submitted:
                    if not name or not village:
                        st.error("Name and Village are mandatory.")
                    elif len(contact) != 10 or not contact.isdigit():
                        st.error("Please enter a valid 10-digit mobile number.")
                    elif get_farmer_by_contact(contact):
                        st.warning("This mobile number is already registered! Please switch to Login.")
                    else:
                        with connect_db() as conn:
                            next_id = conn.execute("SELECT COALESCE(MAX(farmer_id), 1000) + 1 FROM farmers").fetchone()[0]
                            conn.execute(
                                "INSERT INTO farmers (farmer_id, name, contact, village) VALUES (?, ?, ?, ?)",
                                (next_id, name, contact, village),
                            )
                        farmer = get_farmer_by_id(next_id)
                        st.session_state["user_role"] = "farmer"
                        st.session_state["user_data"] = farmer
                        st.balloons()
                        st.success(f"Registered successfully! Your Farmer ID is #{next_id}")
                        st.rerun()

# 2. FARMER PORTAL (Opened only after login)
def render_farmer_portal(farmer):
    # Top Bar Header with Farmer Profile & Logout
    c_head, c_logout = st.columns([4, 1])
    with c_head:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 32px;">🧑‍🌾</span>
                <div>
                    <h2 style="margin: 0; color: #065f46;">Welcome, {farmer['name']}</h2>
                    <p style="margin: 0; color: #64748b; font-size: 14px;">Farmer ID: <strong>#{farmer['farmer_id']}</strong> • Contact: <strong>{farmer['contact']}</strong> • Village: <strong>{farmer['village']}</strong></p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_logout:
        st.write("")
        if st.button("🚪 Log Out", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()

    # Main Farmer Tabs
    tab_rec, tab_req, tab_history = st.tabs([
        "🌱 1. Crop Recommendation Engine",
        "📝 2. Apply for Fertilizer / Subsidy",
        "📋 3. My Applications & Allocation Status",
    ])

    # Tab 1: Crop Recommendation
    with tab_rec:
        st.markdown("### 🎯 Find the Best Crop for Your Soil & Season")
        st.caption("Our agronomist recommendation matrix matches optimal soil types with seasonal factors.")

        col1, col2 = st.columns(2)
        with col1:
            sel_soil = st.selectbox("Select Soil Type:", SOILS, index=0)
        with col2:
            sel_season = st.selectbox("Select Season:", SEASONS, index=0)

        crop_info = CROPS_INFO[(sel_soil, sel_season)]

        st.markdown(
            f"""
            <div class="content-card" style="border-left: 6px solid #10b981; background: #f0fdf4;">
                <h3 style="color: #065f46; margin-top: 0;">{crop_info['icon']} Recommended Crop: {crop_info['crop']}</h3>
                <p style="color: #166534; font-size: 15px; margin-bottom: 6px;"><strong>Scientific Recommendation:</strong> {crop_info['tip']}</p>
                <span style="font-size: 13px; color: #65a30d;">Optimal for <strong>{sel_soil} Soil</strong> during <strong>{sel_season}</strong>.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(f"👉 Proceed to Request Subsidies for {crop_info['crop']}", type="primary"):
            st.session_state["pref_soil"] = sel_soil
            st.session_state["pref_season"] = sel_season
            st.session_state["pref_crop"] = crop_info["crop"]
            st.toast(f"Crop '{crop_info['crop']}' selected! Navigate to tab 2 to submit.", icon="🌾")

    # Tab 2: Resource Request
    with tab_req:
        st.markdown("### 📝 Submit Government Resource / Subsidy Application")

        with connect_db() as conn:
            active_req = conn.execute(
                """SELECT * FROM requests WHERE farmer_id = ? AND status IN ('Pending', 'Partially Allocated')
                   ORDER BY request_id DESC LIMIT 1""",
                (farmer["farmer_id"],),
            ).fetchone()

        if active_req:
            st.info(
                f"📋 **Current Status**: Active Request #{active_req['request_id']} for **{active_req['crop']}** ({active_req['status']}). "
                "You can explore the resource calculator and submit updates below:"
            )

        col_s, col_se = st.columns(2)
        with col_s:
            req_soil = st.selectbox("Soil Type", SOILS, index=SOILS.index(st.session_state.get("pref_soil", SOILS[0])))
        with col_se:
            req_season = st.selectbox("Crop Season", SEASONS, index=SEASONS.index(st.session_state.get("pref_season", SEASONS[1])))

        rec_crop = CROPS_INFO[(req_soil, req_season)]["crop"]
        st.info(f"🌾 Applying for Recommended Crop: **{rec_crop}**")

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            res_type = st.radio("Resource Type Needed:", RESOURCES, horizontal=True)
        with col_res2:
            res_idx = RESOURCES.index(res_type)
            sub_opts = FERTILIZERS if res_idx == 0 else SCHEMES
            sub_detail = st.selectbox(f"Select {res_type}:", sub_opts)

        col_a, col_c = st.columns(2)
        with col_a:
            area = st.number_input("Land Area Cultivated (in Acres):", min_value=0.2, max_value=100.0, value=2.0, step=0.2)
        with col_c:
            cond = st.selectbox("Current Farm Condition:", CONDITIONS, index=0)
            cond_idx = CONDITIONS.index(cond) + 1

        unit = UNITS[res_idx]
        qty = st.number_input(f"Quantity Required ({unit}):", min_value=1, max_value=50000, value=100 if res_idx == 0 else 2, step=1)

        # Live Priority Score
        score = calculate_need_score(area, cond_idx, res_idx)
        st.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px; margin: 15px 0;">
                <span style="font-weight: 600; color: #1e293b;">⚡ Your Priority Need Score: </span>
                <span class="score-pill">{score} Points</span>
                <span style="font-size: 13px; color: #64748b; margin-left: 8px;">
                    (Higher score gives earlier dispatch in the Officer Priority Queue)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚀 Submit Application to Officer Desk", type="primary", use_container_width=True):
            if active_req:
                st.warning("⚠️ You already have an open request. Please wait for officer disbursement.")
            else:
                with connect_db() as conn:
                    next_rid = conn.execute("SELECT COALESCE(MAX(request_id), 0) + 1 FROM requests").fetchone()[0]
                    conn.execute(
                        """INSERT INTO requests
                           (request_id, farmer_id, resource, crop, area, farm_condition, quantity, detail, allocated, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'Pending')""",
                        (next_rid, farmer["farmer_id"], res_idx, rec_crop, area, cond_idx, qty, sub_detail),
                    )
                st.balloons()
                st.success(f"Application #{next_rid} submitted successfully! Your Priority Score is {score}.")
                st.rerun()

    # Tab 3: History & Live Status
    with tab_history:
        st.markdown("### 📋 Application Status & History")
        with connect_db() as conn:
            rows = conn.execute(
                "SELECT * FROM requests WHERE farmer_id = ? ORDER BY request_id DESC",
                (farmer["farmer_id"],),
            ).fetchall()

        if not rows:
            st.info("No applications submitted yet. Switch to Tab 2 to apply.")
        else:
            for r in rows:
                r_dict = dict(r)
                unit = UNITS[r_dict["resource"]]
                res_name = RESOURCES[r_dict["resource"]]
                status = r_dict["status"]
                allocated = r_dict["allocated"]
                qty = r_dict["quantity"]
                pct = min(100, int((allocated / qty) * 100)) if qty > 0 else 0

                badge = "badge-allocated" if status == "Allocated" else ("badge-partial" if status == "Partially Allocated" else "badge-pending")

                with st.container():
                    st.markdown(
                        f"""
                        <div class="content-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; color: #0f172a;">Application #{r_dict['request_id']} — {r_dict['crop']}</h4>
                                <span class="{badge}">{status}</span>
                            </div>
                            <div style="font-size: 14px; color: #475569; margin-top: 8px;">
                                <strong>Resource:</strong> {res_name} ({r_dict['detail']}) • 
                                <strong>Land:</strong> {r_dict['area']} acres • 
                                <strong>Condition:</strong> {CONDITIONS[r_dict['farm_condition'] - 1]}
                            </div>
                            <div style="font-size: 14px; color: #047857; font-weight: 600; margin-top: 6px;">
                                Allocated: {allocated} / {qty} {unit} ({pct}%)
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.progress(pct / 100.0)

# 3. OFFICER PORTAL (Opened only after Officer login)
def render_officer_portal():
    c_head, c_logout = st.columns([4, 1])
    with c_head:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 32px;">🏛️</span>
                <div>
                    <h2 style="margin: 0; color: #065f46;">District Agricultural Resource Portal</h2>
                    <p style="margin: 0; color: #64748b; font-size: 14px;">Priority Queue Dispatch & Resource Management</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_logout:
        st.write("")
        if st.button("🚪 Log Out", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()

    with connect_db() as conn:
        all_reqs = conn.execute(
            """SELECT r.*, f.name as farmer_name, f.village, f.contact
               FROM requests r
               JOIN farmers f ON r.farmer_id = f.farmer_id
               ORDER BY r.status DESC, r.request_id ASC"""
        ).fetchall()

    req_data = [dict(r) for r in all_reqs]
    for r in req_data:
        r["need_score"] = calculate_need_score(r["area"], r["farm_condition"], r["resource"])

    # High-level KPIs
    total = len(req_data)
    pending = sum(1 for r in req_data if r["status"] == "Pending")
    partial = sum(1 for r in req_data if r["status"] == "Partially Allocated")
    allocated = sum(1 for r in req_data if r["status"] == "Allocated")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-lbl">Total Requests</div><div class="metric-val">{total}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-lbl">Pending Review</div><div class="metric-val" style="color: #d97706;">{pending}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-lbl">Partially Granted</div><div class="metric-val" style="color: #0284c7;">{partial}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><div class="metric-lbl">Fully Disbursed</div><div class="metric-val" style="color: #16a34a;">{allocated}</div></div>', unsafe_allow_html=True)

    st.write("")

    tab_dispatch, tab_analytics, tab_farmers = st.tabs([
        "⚡ Priority Dispatch Queue",
        "📊 Transparency & Analytics",
        "👥 Farmer Directory",
    ])

    with tab_dispatch:
        st.markdown("#### ⚡ Priority Dispatch Queue (Ranked by Urgency Score)")

        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            status_filter = st.multiselect("Filter Status:", ["Pending", "Partially Allocated", "Allocated"], default=["Pending", "Partially Allocated"])
        with col_f2:
            res_filter = st.selectbox("Filter Resource:", ["All", "Fertilizer", "Subsidy"])

        filtered = [
            r for r in req_data
            if r["status"] in status_filter and (res_filter == "All" or RESOURCES[r["resource"]] == res_filter)
        ]
        # Sort by status (open first) and need score descending
        filtered.sort(key=lambda x: (x["status"] == "Allocated", -x["need_score"]))

        if not filtered:
            st.success("✅ No requests pending action matching this filter.")
        else:
            for r in filtered:
                unit = UNITS[r["resource"]]
                res_label = RESOURCES[r["resource"]]
                remaining = r["quantity"] - r["allocated"]
                status = r["status"]
                badge = "badge-allocated" if status == "Allocated" else ("badge-partial" if status == "Partially Allocated" else "badge-pending")

                with st.expander(f"⭐ Need Score: {r['need_score']} | Application #{r['request_id']} — {r['farmer_name']} ({r['village']}) — {r['crop']}", expanded=(status != "Allocated")):
                    c1, c2, c3 = st.columns([2, 2, 2])
                    with c1:
                        st.write(f"**Farmer:** {r['farmer_name']} (`#{r['farmer_id']}`)")
                        st.write(f"**Contact:** `{r['contact']}` | **Village:** {r['village']}")
                        st.write(f"**Crop:** {r['crop']} | **Area:** {r['area']} acres")
                    with c2:
                        st.write(f"**Resource:** {res_label} ({r['detail']})")
                        st.write(f"**Condition:** {CONDITIONS[r['farm_condition'] - 1]}")
                        st.write(f"**Requested:** {r['quantity']} {unit} | **Allocated:** {r['allocated']} {unit}")
                    with c3:
                        st.markdown(f"**Status:** <span class='{badge}'>{status}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Priority Score:** <span class='score-pill'>{r['need_score']} pts</span>", unsafe_allow_html=True)
                        st.write(f"**Remaining Needed:** `{remaining} {unit}`")

                    if remaining > 0:
                        st.divider()
                        st.markdown("**Officer Disburse Action:**")
                        act1, act2, act3 = st.columns([2, 1, 1])
                        with act1:
                            disburse_qty = st.number_input(
                                f"Quantity to disburse ({unit}):",
                                min_value=1,
                                max_value=remaining,
                                value=remaining,
                                step=1,
                                key=f"q_{r['request_id']}",
                            )
                        with act2:
                            st.write("")
                            st.write("")
                            if st.button(f"✅ Disburse {disburse_qty} {unit}", key=f"btn_{r['request_id']}", type="primary", use_container_width=True):
                                new_alloc = r["allocated"] + disburse_qty
                                new_st = "Allocated" if new_alloc >= r["quantity"] else "Partially Allocated"
                                with connect_db() as conn:
                                    conn.execute(
                                        "UPDATE requests SET allocated = ?, status = ? WHERE request_id = ?",
                                        (new_alloc, new_st, r["request_id"]),
                                    )
                                st.toast(f"Allocated {disburse_qty} {unit} to {r['farmer_name']}!", icon="🎯")
                                st.rerun()
                        with act3:
                            st.write("")
                            st.write("")
                            if st.button("⚡ Full 100%", key=f"full_{r['request_id']}", use_container_width=True):
                                with connect_db() as conn:
                                    conn.execute(
                                        "UPDATE requests SET allocated = quantity, status = 'Allocated' WHERE request_id = ?",
                                        (r["request_id"],),
                                    )
                                st.toast(f"Fully allocated application #{r['request_id']}!", icon="✨")
                                st.rerun()

    with tab_analytics:
        st.markdown("#### 📊 Crop & Allocation Analytics")
        if req_data:
            df = pd.DataFrame(req_data)
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.write("**Applications by Recommended Crop:**")
                st.bar_chart(df["crop"].value_counts())
            with col_ch2:
                st.write("**Allocation Status Breakdown:**")
                st.bar_chart(df["status"].value_counts())

    with tab_farmers:
        st.markdown("#### 👥 Registered Farmers Directory")
        with connect_db() as conn:
            farmers_df = pd.read_sql_query("SELECT farmer_id as 'Farmer ID', name as 'Name', contact as 'Mobile', village as 'Village' FROM farmers", conn)
        st.dataframe(farmers_df, use_container_width=True, hide_index=True)

# Main Router
def main():
    st.set_page_config(
        page_title="AgriAlloc Portal",
        page_icon="🌾",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_db()
    apply_custom_css()

    user_role = st.session_state.get("user_role")

    # 1. Gatekeeper: If NOT logged in, show ONLY Farmer Login/Register screen
    if not user_role:
        render_auth_page()
    else:
        render_farmer_portal(st.session_state["user_data"])

if __name__ == "__main__":
    main()
