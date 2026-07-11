import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import uuid
import re

# ══════════════════════════════════════════════════════════
#  עיצוב RTL + CSS
# ══════════════════════════════════════════════════════════
RTL_CSS = """
<style>
/* כיוון RTL בסיסי */
body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stForm"] {
    direction: rtl;
    text-align: right;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    direction: rtl;
    text-align: right;
}
/* תוויות שדות */
label, .stSelectbox label, .stTextInput label,
.stTextArea label, .stSlider label, .stRadio label {
    direction: rtl;
    text-align: right;
    width: 100%;
}
/* כפתורי radio */
[data-testid="stRadio"] > div { flex-direction: row-reverse; justify-content: flex-end; }
/* כרטיס קריטריון */
.criterion-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 18px 18px 10px 18px;
    margin-bottom: 18px;
    border-right: 5px solid #667eea;
    border-left: none;
}
/* עוגני דרגות */
.anchor-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82em;
    margin-top: 8px;
    color: #555;
}
.anchor-table th {
    background: #e2e8f0;
    padding: 4px 8px;
    text-align: center;
    border: 1px solid #cbd5e0;
}
.anchor-table td {
    padding: 4px 8px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
    text-align: right;
}
/* הודעת הצלחה מותאמת */
.success-banner {
    background: linear-gradient(135deg, #48bb78, #38a169);
    color: white;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    font-size: 1.1em;
    font-weight: bold;
    margin: 12px 0;
}
/* כרטיס מועמד */
.candidate-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 18px;
}
/* dataframe ל-RTL */
[data-testid="stDataFrame"] { direction: rtl; }
/* קונטיינר תמונה */
.photo-frame {
    border-radius: 8px;
    overflow: hidden;
    border: 3px solid #667eea;
    display: inline-block;
}
/* טאבים */
[data-testid="stTabs"] { direction: rtl; }
</style>
"""

# ══════════════════════════════════════════════════════════
#  הגדרת ששת הקריטריונים
# ══════════════════════════════════════════════════════════
CRITERIA = [
    {
        "key": "initiative",
        "label": "יוזמה והגדלת ראש",
        "anchors": {
            1: "פסיבי, ממתין שיטילו עליו.",
            3: "לוקח משימות כשמבקשים, אמין.",
            5: 'מחפש עבודה ביוזמתו, מזהה צרכים ופועל בלי שיבקשו.',
        },
    },
    {
        "key": "responsibility",
        "label": "אחריות ומקצועיות",
        "anchors": {
            1: "פערים ביסודיות / באמינות, לא מכיר גבולות.",
            3: "יסודי ואמין, מכיר את גבולות הסמכות.",
            5: "אחראי ומדויק גם תחת עומס, אפשר לסמוך עליו לחלוטין.",
        },
    },
    {
        "key": "motivation",
        "label": "מוטיבציה ורצון ללמוד",
        "anchors": {
            1: "לא מגלה עניין, לא שואל.",
            3: "מתעניין, שואל שאלות, משתלב.",
            5: 'מגיע עם ידע מקדים, לומד יזום, "ספוג".',
        },
    },
    {
        "key": "communication",
        "label": "תקשורת ויחסי אנוש",
        "anchors": {
            1: "חיכוכים, תקשורת לקויה תחת לחץ.",
            3: "תקשורת טובה עם הצוות והיולדות, רגוע.",
            5: "מגביר את הצוות סביבו, אמפתי ומכבד, נעים לעבוד איתו.",
        },
    },
    {
        "key": "fit_work",
        "label": "התאמה לאופי העבודה בליס",
        "anchors": {
            1: "לא מתאים לקצב ולאופי העבודה.",
            3: "משתלב יפה בשגרת העבודה.",
            5: "מתאים בול לאופי חדר הלידה — קצב, עומס, סוג העבודה.",
        },
    },
    {
        "key": "fit_social",
        "label": "התאמה חברתית לליס",
        "anchors": {
            1: "לא מתחבר לצוות / לתרבות המחלקה.",
            3: "משתלב חברתית בצוות.",
            5: "חלק טבעי מהצוות, מתחבר לתרבות ולאנשים.",
        },
    },
]

CRITERIA_KEYS = [c["key"] for c in CRITERIA]
CRITERIA_LABELS = {c["key"]: c["label"] for c in CRITERIA}

# ══════════════════════════════════════════════════════════
#  עזרים
# ══════════════════════════════════════════════════════════
def drive_url_to_direct(url: str) -> str:
    """ממיר קישור שיתוף Google Drive לכתובת תמונה ישירה."""
    if not url:
        return url
    m = re.search(r"/file/d/([^/]+)", url)
    if m:
        return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
    # תבנית id=... בכתובת
    m2 = re.search(r"[?&]id=([^&]+)", url)
    if m2:
        return f"https://drive.google.com/uc?export=view&id={m2.group(1)}"
    return url


def render_anchor_table(anchors: dict) -> str:
    return f"""
    <table class="anchor-table">
      <tr>
        <th style="width:33%">דרגה 1</th>
        <th style="width:34%">דרגה 3</th>
        <th style="width:33%">דרגה 5</th>
      </tr>
      <tr>
        <td>{anchors[1]}</td>
        <td>{anchors[3]}</td>
        <td>{anchors[5]}</td>
      </tr>
    </table>
    """


# ══════════════════════════════════════════════════════════
#  חיבור ל-Google Sheets
# ══════════════════════════════════════════════════════════
@st.cache_resource
def _get_gc():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)


@st.cache_resource
def _get_spreadsheet():
    gc = _get_gc()
    return gc.open_by_key(st.secrets["sheet_id"])


def _spreadsheet():
    """מחזיר את ה-spreadsheet; מציג שגיאה אם הסודות חסרים."""
    try:
        return _get_spreadsheet()
    except KeyError as e:
        st.error(f"סוד חסר ב-secrets.toml: {e}")
        return None
    except Exception as e:
        st.error(f"שגיאה בהתחברות ל-Google Sheets: {e}")
        return None


def _ws(name: str, headers: list):
    """מחזיר worksheet; יוצר אותו עם כותרות אם לא קיים."""
    sp = _spreadsheet()
    if sp is None:
        return None
    try:
        ws = sp.worksheet(name)
        if not ws.row_values(1):
            ws.append_row(headers)
        return ws
    except gspread.WorksheetNotFound:
        ws = sp.add_worksheet(title=name, rows=2000, cols=len(headers))
        ws.append_row(headers)
        return ws
    except Exception as e:
        st.error(f"שגיאה בגיליון '{name}': {e}")
        return None


def init_sheets():
    _ws("committees",  ["committee_id", "name", "date", "active"])
    _ws("candidates",  ["candidate_id", "committee_id", "name", "photo_url", "active"])
    _ws("submissions", [
        "timestamp", "committee_id", "candidate_id", "rater_name",
        "initiative", "responsibility", "motivation", "communication",
        "fit_work", "fit_social", "note",
    ])


# ══════════════════════════════════════════════════════════
#  קריאת נתונים (עם מטמון קצר-מועד)
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=20)
def load_committees() -> pd.DataFrame:
    ws = _ws("committees", ["committee_id", "name", "date", "active"])
    if ws is None:
        return pd.DataFrame()
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=["committee_id", "name", "date", "active"])
        df = pd.DataFrame(records)
        df["active"] = df["active"].astype(str).str.upper().isin(["TRUE", "1", "YES"])
        df["committee_id"] = df["committee_id"].astype(str)
        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת ועדות: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=20)
def load_candidates() -> pd.DataFrame:
    ws = _ws("candidates", ["candidate_id", "committee_id", "name", "photo_url", "active"])
    if ws is None:
        return pd.DataFrame()
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=["candidate_id", "committee_id", "name", "photo_url", "active"])
        df = pd.DataFrame(records)
        df["active"] = df["active"].astype(str).str.upper().isin(["TRUE", "1", "YES"])
        df["candidate_id"]  = df["candidate_id"].astype(str)
        df["committee_id"]  = df["committee_id"].astype(str)
        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת מועמדים: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=20)
def load_submissions() -> pd.DataFrame:
    cols = ["timestamp", "committee_id", "candidate_id", "rater_name",
            "initiative", "responsibility", "motivation", "communication",
            "fit_work", "fit_social", "note"]
    ws = _ws("submissions", cols)
    if ws is None:
        return pd.DataFrame()
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(records)
        for key in CRITERIA_KEYS:
            if key in df.columns:
                df[key] = pd.to_numeric(df[key], errors="coerce")
        df["committee_id"] = df["committee_id"].astype(str)
        df["candidate_id"] = df["candidate_id"].astype(str)
        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת הזנות: {e}")
        return pd.DataFrame()


def _clear_caches():
    load_committees.clear()
    load_candidates.clear()
    load_submissions.clear()


# ══════════════════════════════════════════════════════════
#  כתיבת נתונים
# ══════════════════════════════════════════════════════════
def add_committee(name: str, date) -> str | bool:
    ws = _ws("committees", ["committee_id", "name", "date", "active"])
    if ws is None:
        return False
    try:
        cid = str(uuid.uuid4())[:8]
        ws.append_row([cid, name, str(date), "TRUE"])
        load_committees.clear()
        return cid
    except Exception as e:
        st.error(f"שגיאה ביצירת ועדה: {e}")
        return False


def set_committee_active(committee_id: str, active: bool):
    ws = _ws("committees", ["committee_id", "name", "date", "active"])
    if ws is None:
        return
    try:
        rows = ws.get_all_records()
        for i, row in enumerate(rows, start=2):
            if str(row["committee_id"]) == str(committee_id):
                ws.update_cell(i, 4, "TRUE" if active else "FALSE")
                load_committees.clear()
                return
    except Exception as e:
        st.error(f"שגיאה בעדכון ועדה: {e}")


def add_candidate(committee_id: str, name: str, photo_url: str) -> str | bool:
    ws = _ws("candidates", ["candidate_id", "committee_id", "name", "photo_url", "active"])
    if ws is None:
        return False
    try:
        cid = str(uuid.uuid4())[:8]
        ws.append_row([cid, str(committee_id), name, photo_url, "TRUE"])
        load_candidates.clear()
        return cid
    except Exception as e:
        st.error(f"שגיאה בהוספת מועמד: {e}")
        return False


def set_candidate_active(candidate_id: str, active: bool):
    ws = _ws("candidates", ["candidate_id", "committee_id", "name", "photo_url", "active"])
    if ws is None:
        return
    try:
        rows = ws.get_all_records()
        for i, row in enumerate(rows, start=2):
            if str(row["candidate_id"]) == str(candidate_id):
                ws.update_cell(i, 5, "TRUE" if active else "FALSE")
                load_candidates.clear()
                return
    except Exception as e:
        st.error(f"שגיאה בעדכון מועמד: {e}")


def submit_rating(committee_id, candidate_id, rater_name, ratings: dict, note: str) -> str:
    """שומר או מעדכן הזנה. מחזיר 'created'/'updated'/False."""
    ws = _ws("submissions", [
        "timestamp", "committee_id", "candidate_id", "rater_name",
        "initiative", "responsibility", "motivation", "communication",
        "fit_work", "fit_social", "note",
    ])
    if ws is None:
        return False
    try:
        rows = ws.get_all_records()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [
            ts, str(committee_id), str(candidate_id), rater_name,
            ratings["initiative"], ratings["responsibility"], ratings["motivation"],
            ratings["communication"], ratings["fit_work"], ratings["fit_social"], note,
        ]
        for i, row in enumerate(rows, start=2):
            if (
                str(row.get("committee_id")) == str(committee_id)
                and str(row.get("candidate_id")) == str(candidate_id)
                and str(row.get("rater_name", "")).strip().lower()
                   == rater_name.strip().lower()
            ):
                ws.update(f"A{i}:K{i}", [new_row])
                load_submissions.clear()
                return "updated"

        ws.append_row(new_row)
        load_submissions.clear()
        return "created"
    except Exception as e:
        st.error(f"שגיאה בשמירת הדירוג: {e}")
        return False


def existing_submission(committee_id, candidate_id, rater_name):
    """מחזיר שורת הזנה קיימת או None."""
    subs = load_submissions()
    if subs.empty:
        return None
    mask = (
        (subs["committee_id"].astype(str) == str(committee_id))
        & (subs["candidate_id"].astype(str) == str(candidate_id))
        & (subs["rater_name"].astype(str).str.strip().str.lower()
           == rater_name.strip().lower())
    )
    rows = subs[mask]
    return rows.iloc[0] if len(rows) > 0 else None


# ══════════════════════════════════════════════════════════
#  מסך 1 — הזנה (פתוח לכולם)
# ══════════════════════════════════════════════════════════
def page_entry():
    st.title("הערכת מועמד לוועדת קבלה")

    # טעינת ועדות פעילות
    committees = load_committees()
    active = committees[committees["active"]] if not committees.empty else pd.DataFrame()

    if active.empty:
        st.warning("אין ועדות פעילות כרגע. פנו למנהל המערכת.")
        return

    # בורר ועדה
    if len(active) == 1:
        comm = active.iloc[0]
        st.info(f"**ועדה פעילה:** {comm['name']}  |  {comm['date']}")
    else:
        opts = {f"{r['name']} ({r['date']})": r["committee_id"] for _, r in active.iterrows()}
        chosen = st.selectbox("בחרי ועדה", list(opts.keys()))
        cid_sel = opts[chosen]
        comm = active[active["committee_id"] == cid_sel].iloc[0]

    committee_id = comm["committee_id"]

    st.markdown("---")

    # שם מדרג
    rater_name = st.text_input(
        "שמך (חובה)",
        placeholder="הכניסי את שמך המלא",
        key="rater_name_input",
    )

    # מועמדים בוועדה
    candidates = load_candidates()
    comm_candidates = (
        candidates[
            (candidates["committee_id"] == committee_id) & (candidates["active"])
        ]
        if not candidates.empty
        else pd.DataFrame()
    )

    if comm_candidates.empty:
        st.warning("אין מועמדים פעילים בוועדה זו. פנו למנהל המערכת.")
        return

    cand_names = comm_candidates["name"].tolist()
    selected_name = st.selectbox("בחרי מועמד לדירוג", cand_names, key="cand_select")
    candidate = comm_candidates[comm_candidates["name"] == selected_name].iloc[0]
    candidate_id = candidate["candidate_id"]

    # תמונה
    photo_raw = candidate.get("photo_url", "")
    photo_url = drive_url_to_direct(str(photo_raw)) if photo_raw else ""
    if photo_url:
        col_img, col_name = st.columns([1, 4])
        with col_img:
            try:
                st.image(photo_url, width=110)
            except Exception:
                pass
        with col_name:
            st.markdown(f"### {selected_name}")
    else:
        st.markdown(f"### {selected_name}")

    # בדיקת הזנה קיימת
    existing = None
    if rater_name.strip():
        existing = existing_submission(committee_id, candidate_id, rater_name)

    if existing is not None:
        st.warning("⚠️ כבר הזנת הערכה על מועמד זה. השינויים ישמרו כעדכון.")

    st.markdown("---")
    st.subheader("דירוג קריטריונים")

    ratings = {}
    for crit in CRITERIA:
        key    = crit["key"]
        label  = crit["label"]
        anchors = crit["anchors"]

        default = 3
        if existing is not None:
            try:
                default = int(existing[key])
            except (KeyError, ValueError, TypeError):
                default = 3

        st.markdown(f'<div class="criterion-card">', unsafe_allow_html=True)
        st.markdown(f"**{label}**")
        rating = st.slider(
            label,
            min_value=1,
            max_value=5,
            value=default,
            label_visibility="collapsed",
            key=f"sl_{key}",
        )
        st.markdown(render_anchor_table(anchors), unsafe_allow_html=True)
        ratings[key] = rating
        st.markdown("</div>", unsafe_allow_html=True)

    # הערה חופשית
    default_note = str(existing["note"]) if existing is not None and pd.notna(existing.get("note")) else ""
    note = st.text_area(
        "הערה חופשית (אופציונלי)",
        value=default_note,
        placeholder="הוסיפי כל הערה שתרצי...",
        key="free_note",
    )

    st.markdown("---")
    if st.button("שלחי הערכה", type="primary", use_container_width=True):
        if not rater_name.strip():
            st.error("יש להכניס שם לפני שליחה.")
        else:
            result = submit_rating(committee_id, candidate_id, rater_name.strip(), ratings, note)
            if result == "created":
                st.markdown(
                    f'<div class="success-banner">ההערכה על {selected_name} נשמרה בהצלחה ✓</div>',
                    unsafe_allow_html=True,
                )
                st.balloons()
            elif result == "updated":
                st.success(f"ההערכה על {selected_name} עודכנה בהצלחה ✓")


# ══════════════════════════════════════════════════════════
#  מסך 2 — תוצאות (נעול בסיסמה)
# ══════════════════════════════════════════════════════════
def page_results():
    st.title("תוצאות ודירוג")

    # אימות
    if not st.session_state.get("auth_ok"):
        with st.form("login_form"):
            pwd = st.text_input("סיסמה", type="password")
            ok  = st.form_submit_button("כניסה")
        if ok:
            try:
                correct = st.secrets["results_password"]
            except KeyError:
                st.error("הסוד results_password לא מוגדר.")
                return
            if pwd == correct:
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("סיסמה שגויה.")
        return

    if st.button("התנתקות"):
        st.session_state["auth_ok"] = False
        st.rerun()

    # טעינת נתונים
    committees = load_committees()
    candidates = load_candidates()
    submissions = load_submissions()

    if committees.empty:
        st.info("אין ועדות במערכת — צרי אחת בלשונית ניהול.")
        _tab_management(committees, pd.DataFrame(), "")
        return

    # בורר ועדה
    opts = {
        f"{r['name']} ({r['date']})  {'✅ פעילה' if r['active'] else '🔒 סגורה'}": r["committee_id"]
        for _, r in committees.iterrows()
    }
    chosen = st.selectbox("ועדה", list(opts.keys()), key="res_comm")
    committee_id = opts[chosen]

    # סינון לוועדה
    comm_cands = (
        candidates[candidates["committee_id"] == committee_id]
        if not candidates.empty
        else pd.DataFrame()
    )
    comm_subs = (
        submissions[submissions["committee_id"] == committee_id]
        if not submissions.empty
        else pd.DataFrame()
    )

    t1, t2, t3, t4, t5 = st.tabs(
        ["דירוג מצרפי", "הזנות גולמיות", "כרטיס מועמד", "ניהול", "ייצוא"]
    )

    with t1:
        _tab_rankings(comm_cands, comm_subs)
    with t2:
        _tab_raw(comm_cands, comm_subs)
    with t3:
        _tab_card(comm_cands, comm_subs)
    with t4:
        _tab_management(committees, comm_cands, committee_id)
    with t5:
        _tab_export(comm_cands, comm_subs)


# ── לשונית דירוג מצרפי ──────────────────────────────────
def _tab_rankings(candidates: pd.DataFrame, submissions: pd.DataFrame):
    st.subheader("דירוג מצרפי")
    if candidates.empty:
        st.info("אין מועמדים בוועדה זו.")
        return
    if submissions.empty:
        st.info("אין הזנות עדיין.")
        return

    rows = []
    for _, cand in candidates.iterrows():
        cid = cand["candidate_id"]
        subs = submissions[submissions["candidate_id"] == cid]
        if subs.empty:
            continue
        row = {"שם מועמד": cand["name"]}
        for crit in CRITERIA:
            vals = pd.to_numeric(subs[crit["key"]], errors="coerce").dropna()
            row[crit["label"]] = round(vals.mean(), 2) if len(vals) else None
        all_vals = pd.to_numeric(subs[CRITERIA_KEYS].values.flatten(), errors="coerce")
        row["ממוצע כולל"] = round(pd.Series(all_vals).dropna().mean(), 2)
        row["מדרגים"]     = len(subs)
        rows.append(row)

    if not rows:
        st.info("אין נתונים מספיקים.")
        return

    df = (
        pd.DataFrame(rows)
        .sort_values("ממוצע כולל", ascending=False)
        .reset_index(drop=True)
    )
    df.index += 1
    st.dataframe(df, use_container_width=True)


# ── לשונית הזנות גולמיות ────────────────────────────────
def _tab_raw(candidates: pd.DataFrame, submissions: pd.DataFrame):
    st.subheader("הזנות גולמיות")
    if submissions.empty:
        st.info("אין הזנות עדיין.")
        return

    options = ["כל המועמדים"] + (candidates["name"].tolist() if not candidates.empty else [])
    filt = st.selectbox("סינון לפי מועמד", options, key="raw_filt")

    df = submissions.copy()
    if filt != "כל המועמדים" and not candidates.empty:
        cid = candidates[candidates["name"] == filt]["candidate_id"].values[0]
        df = df[df["candidate_id"] == cid]

    if not candidates.empty:
        cmap = dict(zip(candidates["candidate_id"], candidates["name"]))
        df.insert(0, "שם מועמד", df["candidate_id"].map(cmap))

    rename = {
        "rater_name":    "מדרג",
        "initiative":    "יוזמה",
        "responsibility":"אחריות",
        "motivation":    "מוטיבציה",
        "communication": "תקשורת",
        "fit_work":      "התאמה עבודה",
        "fit_social":    "התאמה חברתית",
        "note":          "הערה",
        "timestamp":     "זמן",
    }
    cols_show = (
        ["שם מועמד"] if "שם מועמד" in df.columns else []
    ) + [c for c in rename if c in df.columns]
    st.dataframe(
        df[cols_show].rename(columns=rename),
        use_container_width=True,
    )


# ── לשונית כרטיס מועמד ──────────────────────────────────
def _tab_card(candidates: pd.DataFrame, submissions: pd.DataFrame):
    st.subheader("כרטיס מועמד")
    if candidates.empty:
        st.info("אין מועמדים בוועדה זו.")
        return

    sel = st.selectbox("בחרי מועמד", candidates["name"].tolist(), key="card_sel")
    cand = candidates[candidates["name"] == sel].iloc[0]
    cid  = cand["candidate_id"]
    subs = submissions[submissions["candidate_id"] == cid] if not submissions.empty else pd.DataFrame()

    # כותרת
    photo_raw = cand.get("photo_url", "")
    photo_url = drive_url_to_direct(str(photo_raw)) if photo_raw else ""
    col_img, col_info = st.columns([1, 4])
    with col_img:
        if photo_url:
            try:
                st.image(photo_url, width=140)
            except Exception:
                st.markdown("(תמונה לא זמינה)")
        else:
            st.markdown("(אין תמונה)")
    with col_info:
        active_str = "פעיל" if cand.get("active") else "מושבת"
        st.markdown(f"## {sel}")
        st.markdown(f"**סטטוס:** {active_str}  |  **מדרגים:** {len(subs)}")

    if subs.empty:
        st.info("אין הזנות עדיין למועמד זה.")
        return

    # ממוצעים לפי קריטריון
    st.markdown("### ציונים לפי קריטריון")
    avgs = {}
    for crit in CRITERIA:
        vals = pd.to_numeric(subs[crit["key"]], errors="coerce").dropna()
        avgs[crit["label"]] = round(vals.mean(), 2) if len(vals) else 0.0

    avg_df = pd.DataFrame(
        {"קריטריון": list(avgs.keys()), "ממוצע": list(avgs.values())}
    ).set_index("קריטריון")
    st.bar_chart(avg_df)

    # חוזק וחולשה
    best  = max(avgs, key=avgs.get)
    worst = min(avgs, key=avgs.get)
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"**חוזק:** {best}  ({avgs[best]:.2f})")
    with c2:
        st.error(f"**חולשה:** {worst}  ({avgs[worst]:.2f})")

    # הערות חופשיות
    st.markdown("### הערות חופשיות")
    notes = subs["note"].dropna().astype(str).str.strip()
    notes = notes[notes.str.len() > 0]
    if notes.empty:
        st.info("אין הערות.")
    else:
        for n in notes:
            st.markdown(f"- {n}")


# ── לשונית ניהול ────────────────────────────────────────
def _tab_management(committees: pd.DataFrame, comm_candidates: pd.DataFrame, committee_id: str):
    st.subheader("ניהול")
    tab_c, tab_k = st.tabs(["ועדות", "מועמדים"])

    with tab_c:
        st.markdown("#### יצירת ועדה חדשה")
        with st.form("form_new_comm"):
            new_name = st.text_input("שם הוועדה")
            new_date = st.date_input("תאריך הוועדה")
            if st.form_submit_button("צרי ועדה"):
                if new_name.strip():
                    cid = add_committee(new_name.strip(), new_date)
                    if cid:
                        st.success(f"ועדה נוצרה (מזהה: {cid})")
                        st.rerun()
                else:
                    st.error("יש להכניס שם לוועדה.")

        st.markdown("---")
        st.markdown("#### ועדות קיימות")
        if not committees.empty:
            for _, comm in committees.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{comm['name']}** ({comm['date']})")
                with c2:
                    st.markdown("✅ פעילה" if comm["active"] else "🔒 סגורה")
                with c3:
                    lbl = "סגרי" if comm["active"] else "הפעילי"
                    if st.button(lbl, key=f"tog_{comm['committee_id']}"):
                        set_committee_active(comm["committee_id"], not comm["active"])
                        _clear_caches()
                        st.rerun()

    with tab_k:
        if not committee_id:
            st.info("בחרי ועדה תחילה.")
            return

        st.markdown("#### הוספת מועמד לוועדה הנוכחית")
        with st.form("form_new_cand"):
            cand_name  = st.text_input("שם מלא")
            cand_photo = st.text_input("קישור לתמונה מ-Google Drive (אופציונלי)")
            if st.form_submit_button("הוסיפי מועמד"):
                if cand_name.strip():
                    cid = add_candidate(committee_id, cand_name.strip(), cand_photo.strip())
                    if cid:
                        st.success(f"מועמד נוסף (מזהה: {cid})")
                        _clear_caches()
                        st.rerun()
                else:
                    st.error("יש להכניס שם מועמד.")

        st.markdown("---")
        st.markdown("#### מועמדים בוועדה")
        all_cands = load_candidates()
        if not all_cands.empty:
            in_comm = all_cands[all_cands["committee_id"] == str(committee_id)]
            for _, cand in in_comm.iterrows():
                c1, c2 = st.columns([5, 1])
                with c1:
                    icon = "✓" if cand["active"] else "✗ מושבת"
                    st.markdown(f"{cand['name']}  {icon}")
                with c2:
                    if cand["active"]:
                        if st.button("השבת", key=f"deact_{cand['candidate_id']}"):
                            set_candidate_active(cand["candidate_id"], False)
                            _clear_caches()
                            st.rerun()
                    else:
                        if st.button("הפעל", key=f"act_{cand['candidate_id']}"):
                            set_candidate_active(cand["candidate_id"], True)
                            _clear_caches()
                            st.rerun()


# ── לשונית ייצוא ────────────────────────────────────────
def _tab_export(candidates: pd.DataFrame, submissions: pd.DataFrame):
    st.subheader("ייצוא נתונים")

    # דירוג מצרפי
    if not submissions.empty and not candidates.empty:
        rows = []
        for _, cand in candidates.iterrows():
            cid  = cand["candidate_id"]
            subs = submissions[submissions["candidate_id"] == cid]
            if subs.empty:
                continue
            row = {"שם מועמד": cand["name"]}
            for crit in CRITERIA:
                vals = pd.to_numeric(subs[crit["key"]], errors="coerce").dropna()
                row[crit["label"]] = round(vals.mean(), 2) if len(vals) else None
            all_vals = pd.to_numeric(subs[CRITERIA_KEYS].values.flatten(), errors="coerce")
            row["ממוצע כולל"] = round(pd.Series(all_vals).dropna().mean(), 2)
            row["מדרגים"]     = len(subs)
            rows.append(row)

        if rows:
            agg_df = pd.DataFrame(rows).sort_values("ממוצע כולל", ascending=False)
            st.download_button(
                "הורדת דירוג מצרפי (CSV)",
                data=agg_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name="rankings.csv",
                mime="text/csv",
            )

    if not submissions.empty:
        st.download_button(
            "הורדת כל ההזנות הגולמיות (CSV)",
            data=submissions.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name="submissions.csv",
            mime="text/csv",
        )

    if submissions.empty and (candidates.empty or True):
        st.info("אין נתונים לייצוא עדיין.")


# ══════════════════════════════════════════════════════════
#  נקודת כניסה
# ══════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="ועדות קבלה — ליס",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(RTL_CSS, unsafe_allow_html=True)

    # אתחול גיליונות (יוצר worksheet-ים אם חסרים)
    if "sheets_initialized" not in st.session_state:
        try:
            init_sheets()
            st.session_state["sheets_initialized"] = True
        except Exception:
            # אם הסודות עדיין לא הוגדרו — לא נכשל בצלצול; יכשל בטעינת נתונים
            st.session_state["sheets_initialized"] = False

    # ניווט בסרגל הצד
    with st.sidebar:
        st.markdown("## תפריט")
        page = st.radio(
            "מסך",
            ["הזנת הערכה", "תוצאות ודירוג"],
            label_visibility="collapsed",
            key="nav_radio",
        )

    if page == "הזנת הערכה":
        page_entry()
    else:
        page_results()


if __name__ == "__main__":
    main()
