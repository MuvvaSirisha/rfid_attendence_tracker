"""
SmartAttend — Student Management Page
Add / Edit / Delete / Search registered students.
"""

import streamlit as st
from database.db import (
    get_all_students, add_student, update_student, delete_student,
    roll_exists, rfid_exists,
)
from utils.ui_helpers import inject_css, section_header, page_header

DEPTS = ["CS", "EC", "ME", "Civil", "EE"]
YEARS = [1, 2, 3, 4]


def render():
    inject_css()
    page_header("🎓 Student Management", "Register, edit and manage RFID-linked student records")

    students = get_all_students()

    # ── Summary strip ─────────────────────────────────────────────────────────
    dept_counts = students["dept"].value_counts().to_dict() if not students.empty else {}
    info_parts  = [f"**{len(students)}** total students"]
    for d in DEPTS:
        if d in dept_counts:
            info_parts.append(f"{d}: {dept_counts[d]}")
    st.info("  •  ".join(info_parts))

    # ── Search & table ────────────────────────────────────────────────────────
    section_header("📋 Registered Students")
    col_search, col_dept = st.columns([3, 1])
    with col_search:
        search = st.text_input("🔍 Search by name or roll number", placeholder="e.g. Aarav or CS001")
    with col_dept:
        dept_f = st.selectbox("Filter by dept", ["All"] + DEPTS, key="stu_dept_filter")

    view = students.copy()
    if search:
        q    = search.lower()
        view = view[view["name"].str.lower().str.contains(q) |
                    view["roll"].str.lower().str.contains(q)]
    if dept_f != "All":
        view = view[view["dept"] == dept_f]

    if view.empty:
        st.info("No students match your search.")
    else:
        st.dataframe(
            view.rename(columns={
                "id": "ID", "name": "Name", "roll": "Roll No.",
                "dept": "Dept", "year": "Year", "rfid": "RFID UID"
            }),
            use_container_width=True, hide_index=True,
        )
        st.caption(f"Showing {len(view)} of {len(students)} student(s)")

    st.divider()

    # ── CRUD Tabs ─────────────────────────────────────────────────────────────
    tab_add, tab_edit, tab_delete = st.tabs(["➕ Add Student", "✏️ Edit Student", "🗑️ Delete Student"])

    # ── Add ──────────────────────────────────────────────────────────────────
    with tab_add:
        st.markdown("#### Register New Student")
        st.caption("⚠️  All fields are required. Each Roll Number and RFID UID must be unique.")
        with st.form("form_add", clear_on_submit=True):
            r1c1, r1c2 = st.columns(2)
            name = r1c1.text_input("Full Name *", placeholder="e.g. Aarav Patel")
            roll = r1c2.text_input("Roll Number *", placeholder="e.g. CS005")

            r2c1, r2c2 = st.columns(2)
            dept = r2c1.selectbox("Department *", DEPTS)
            year = r2c2.selectbox("Year *", YEARS)

            rfid = st.text_input(
                "RFID Card UID *",
                placeholder="e.g. 04:A3:F1:7C:0A  (scan from ESP32 console)",
            )
            st.caption("💡 To get the UID, hold the card on the reader and copy the UID from the ESP32 serial monitor.")

            submitted = st.form_submit_button("✅ Register Student", type="primary", use_container_width=True)
            if submitted:
                errors = []
                if not name.strip():  errors.append("Full name is required.")
                if not roll.strip():  errors.append("Roll number is required.")
                if not rfid.strip():  errors.append("RFID UID is required.")
                if roll and roll_exists(roll):
                    errors.append(f"Roll number '{roll.strip().upper()}' is already registered.")
                if rfid and rfid_exists(rfid):
                    errors.append("This RFID UID is already assigned to another student.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    add_student(name.strip(), roll.strip(), dept, int(year), rfid.strip())
                    st.success(f"✅ Student **{name.strip()}** registered successfully!")
                    st.rerun()

    # ── Edit ─────────────────────────────────────────────────────────────────
    with tab_edit:
        st.markdown("#### Edit Student Details")
        if students.empty:
            st.info("No students registered yet.")
        else:
            opts   = students["name"] + " (" + students["roll"] + ")"
            choice = st.selectbox("Select student to edit", opts, key="edit_sel")
            idx    = opts[opts == choice].index[0]
            stu    = students.loc[idx]

            with st.form("form_edit"):
                r1c1, r1c2 = st.columns(2)
                e_name = r1c1.text_input("Full Name *", value=stu["name"])
                e_roll = r1c2.text_input("Roll Number *", value=stu["roll"])

                r2c1, r2c2 = st.columns(2)
                dept_idx  = DEPTS.index(stu["dept"]) if stu["dept"] in DEPTS else 0
                e_dept = r2c1.selectbox("Department *", DEPTS, index=dept_idx)
                e_year = r2c2.selectbox("Year *", YEARS, index=YEARS.index(int(stu["year"])))

                e_rfid = st.text_input("RFID Card UID *", value=stu["rfid"])

                if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                    errors = []
                    if not e_name.strip(): errors.append("Name is required.")
                    if not e_rfid.strip(): errors.append("RFID UID is required.")
                    if roll_exists(e_roll, exclude_id=int(stu["id"])):
                        errors.append(f"Roll '{e_roll.strip().upper()}' is already in use.")
                    if rfid_exists(e_rfid, exclude_id=int(stu["id"])):
                        errors.append("RFID UID is already assigned to another student.")

                    if errors:
                        for e in errors:
                            st.error(e)
                    else:
                        update_student(int(stu["id"]), e_name.strip(), e_roll.strip(),
                                       e_dept, int(e_year), e_rfid.strip())
                        st.success("✅ Student details updated successfully!")
                        st.rerun()

    # ── Delete ───────────────────────────────────────────────────────────────
    with tab_delete:
        st.markdown("#### Remove Student")
        if students.empty:
            st.info("No students registered yet.")
        else:
            opts2   = students["name"] + " (" + students["roll"] + ")"
            choice2 = st.selectbox("Select student to delete", opts2, key="del_sel")
            idx2    = opts2[opts2 == choice2].index[0]
            stu2    = students.loc[idx2]

            st.markdown(f"""
            <div style="background:#FFF1F2;border:1px solid #FECDD3;border-radius:8px;padding:14px 18px;margin:10px 0;">
                <strong>⚠️ You are about to permanently delete:</strong><br>
                <b>{stu2['name']}</b> — Roll: {stu2['roll']} | Dept: {stu2['dept']} | Year: {stu2['year']}<br>
                <span style="color:#DC2626;font-size:0.85rem;">
                    This will also delete ALL attendance records for this student. This action cannot be undone.
                </span>
            </div>
            """, unsafe_allow_html=True)

            confirm = st.checkbox("I understand and want to permanently delete this student.")
            if st.button("🗑️ Delete Student", type="primary", disabled=not confirm):
                delete_student(int(stu2["id"]))
                st.success(f"Student **{stu2['name']}** has been deleted.")
                st.rerun()
