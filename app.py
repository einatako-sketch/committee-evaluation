import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
import pandas as pd
from datetime import datetime
import uuid
import re

# ══════════════════════════════════════════════════════════
#  עיצוב RTL + CSS
# ══════════════════════════════════════════════════════════
RTL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap');

/* ══ צבעי בסיס ══
   --salmon:      #E8756A  עיקרי
   --salmon-dark: #C4565A  hover
   --blush:       #FEF0EE  רקע כרטיסים
   --cream:       #FFFBFA  רקע דף
   --charcoal:    #2C2C2C  טקסט כהה
   --mid:         #6B5B55  טקסט משני
   --white:       #FFFFFF
*/

/* ══ בסיס ══ */
body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stForm"] {
    font-family: 'Rubik', sans-serif !important;
    direction: rtl;
    text-align: right;
    background-color: #FFFBFA;
}

/* ══ סרגל צד ══ */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    direction: rtl;
    text-align: right;
    background: linear-gradient(180deg, #E8756A 0%, #C4565A 100%) !important;
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.3) !important; }

/* ══ כותרות ══ */
h1 {
    font-family: 'Rubik', sans-serif !important;
    color: #2C2C2C;
    font-weight: 700;
    border-bottom: 3px solid #E8756A;
    padding-bottom: 6px;
}
h2, h3 {
    font-family: 'Rubik', sans-serif !important;
    color: #2C2C2C;
    font-weight: 600;
}

/* ══ תוויות ══ */
label, .stSelectbox label, .stTextInput label,
.stTextArea label, .stRadio label {
    font-family: 'Rubik', sans-serif !important;
    direction: rtl;
    text-align: right;
    width: 100%;
    color: #2C2C2C !important;
    font-weight: 500;
}

/* ══ radio דירוג 1-5 ══ */
[data-testid="stRadio"] > div {
    flex-direction: row;
    justify-content: flex-start;
    gap: 16px;
    margin-top: 6px;
}
[data-testid="stRadio"] label {
    font-size: 1.15em !important;
    font-weight: 600 !important;
    color: #2C2C2C !important;
}

/* ══ כפתורים ══ */
.stButton > button {
    font-family: 'Rubik', sans-serif !important;
    background-color: #ffffff;
    color: #E8756A;
    border: 2px solid #E8756A;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover {
    background-color: #E8756A;
    color: #ffffff;
}
.stButton > button[kind="primary"] {
    background: #E8756A;
    color: #ffffff;
    border: none;
    font-size: 1.05em;
    padding: 10px 0;
    box-shadow: 0 3px 10px rgba(232,117,106,0.35);
}
.stButton > button[kind="primary"]:hover {
    background: #C4565A;
}

/* ══ סרגל התקדמות מותאם ══ */
.progress-wrap {
    background: #F5D6D3;
    border-radius: 20px;
    height: 10px;
    margin: 8px 0 4px 0;
    overflow: hidden;
}
.progress-fill {
    background: linear-gradient(90deg, #E8756A, #C4565A);
    height: 100%;
    border-radius: 20px;
    transition: width 0.4s ease;
}
.progress-label {
    font-size: 0.9em;
    color: #6B5B55;
    margin-bottom: 16px;
    font-weight: 500;
}

/* ══ כרטיס קריטריון ══ */
.criterion-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 22px 22px 14px 22px;
    border-right: 5px solid #E8756A;
    border-left: none;
    box-shadow: 0 2px 10px rgba(232,117,106,0.12);
}

/* ══ עוגני דרגות — רשימה אנכית ══ */
.anchor-list {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.anchor-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 0.85em;
    color: #555;
    direction: rtl;
}
.anchor-num {
    background: #E8756A;
    color: #ffffff;
    font-weight: 700;
    border-radius: 50%;
    min-width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 0.85em;
}
.anchor-row:nth-child(2) .anchor-num,
.anchor-row:nth-child(4) .anchor-num {
    background: #ddd;
    color: #999;
}
.anchor-text {
    padding-top: 2px;
    line-height: 1.4;
}

/* ══ הצלחה ══ */
.success-banner {
    background: linear-gradient(135deg, #E8756A, #C4565A);
    color: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-size: 1.2em;
    font-weight: 700;
    margin: 16px 0;
    box-shadow: 0 4px 14px rgba(232,117,106,0.35);
}

/* ══ כרטיס מועמד (תוצאות) ══ */
.candidate-header {
    background: linear-gradient(135deg, #E8756A 0%, #C4565A 100%);
    color: white;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 18px;
}

/* ══ dataframe ══ */
[data-testid="stDataFrame"] { direction: rtl; }

/* ══ טאבים ══ */
[data-testid="stTabs"] { direction: rtl; }
[data-testid="stTab"] {
    font-family: 'Rubik', sans-serif !important;
    font-weight: 600;
}

/* ══ התראות ══ */
[data-testid="stAlert"] {
    direction: rtl;
    text-align: right;
    font-family: 'Rubik', sans-serif !important;
}

/* ══ מפריד ══ */
hr { border-color: #F5D6D3; }

input, textarea {
    font-family: 'Rubik', sans-serif !important;
    direction: rtl !important;
}
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
            5: "מגיע עם ידע מקדים, לומד ביוזמתו, שואל שאלות עמוקות.",
        },
    },
    {
        "key": "communication",
        "label": "תקשורת ויחסי אנוש",
        "anchors": {
            1: "חיכוכים, תקשורת לקויה תחת לחץ.",
            3: "תקשורת טובה עם הצוות והיולדות, רגוע.",
            5: "משפיע לטובה על האנשים סביבו, אמפתי ומכבד, נעים לעבוד איתו.",
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


def _option_label(n: int, anchors: dict) -> str:
    text = anchors.get(n, "")
    return f"{n} — {text}" if text else str(n)


def _option_to_int(s) -> int:
    try:
        return int(str(s).strip().split()[0])
    except Exception:
        return 3


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


@st.cache_resource
def _get_drive_service():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds)


def upload_photo_to_drive(file_bytes: bytes, filename: str, mime_type: str) -> str:
    """מעלה תמונה ל-Drive ומחזירה URL ישיר לתצוגה."""
    service = _get_drive_service()
    media = MediaInMemoryUpload(file_bytes, mimetype=mime_type, resumable=False)
    file_meta = {"name": filename}
    uploaded = service.files().create(
        body=file_meta, media_body=media, fields="id"
    ).execute()
    file_id = uploaded.get("id")
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()
    return f"https://drive.google.com/uc?export=view&id={file_id}"


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
def add_committee(name: str, date):
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


def update_committee(committee_id: str, new_name: str, new_date):
    ws = _ws("committees", ["committee_id", "name", "date", "active"])
    if ws is None:
        return False
    try:
        rows = ws.get_all_records()
        for i, row in enumerate(rows, start=2):
            if str(row["committee_id"]) == str(committee_id):
                ws.update_cell(i, 2, new_name)
                ws.update_cell(i, 3, str(new_date))
                load_committees.clear()
                return True
        return False
    except Exception as e:
        st.error(f"שגיאה בעדכון ועדה: {e}")
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


def add_candidate(committee_id: str, name: str, photo_url: str):
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


def submit_rating(committee_id, candidate_id, rater_name, ratings: dict, note: str):
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


def delete_submissions_for_committee(committee_id: str) -> int:
    """מוחקת את כל ההזנות לוועדה נתונה. מחזירה מספר שורות שנמחקו."""
    ws = _ws("submissions", [
        "timestamp", "committee_id", "candidate_id", "rater_name",
        "initiative", "responsibility", "motivation", "communication",
        "fit_work", "fit_social", "note",
    ])
    if ws is None:
        return 0
    try:
        rows = ws.get_all_values()  # כולל כותרת בשורה 1
        to_delete = [
            i + 2  # +2: שורה 1 היא כותרת, enumerate מתחיל ב-0
            for i, row in enumerate(rows[1:])
            if len(row) > 1 and str(row[1]) == str(committee_id)
        ]
        # מוחקים מהסוף להתחלה כדי לא לשבש אינדקסים
        for row_num in reversed(to_delete):
            ws.delete_rows(row_num)
        load_submissions.clear()
        return len(to_delete)
    except Exception as e:
        st.error(f"שגיאה במחיקה: {e}")
        return 0


def delete_single_submission(committee_id: str, candidate_id: str, rater_name: str) -> bool:
    """מוחקת הזנה בודדת לפי ועדה + מועמד + מדרג."""
    ws = _ws("submissions", [
        "timestamp", "committee_id", "candidate_id", "rater_name",
        "initiative", "responsibility", "motivation", "communication",
        "fit_work", "fit_social", "note",
    ])
    if ws is None:
        return False
    try:
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if (len(row) >= 4
                    and str(row[1]) == str(committee_id)
                    and str(row[2]) == str(candidate_id)
                    and str(row[3]).strip().lower() == rater_name.strip().lower()):
                ws.delete_rows(i)
                load_submissions.clear()
                return True
        return False
    except Exception as e:
        st.error(f"שגיאה במחיקה: {e}")
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
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        try:
            st.image("images.png", width=90)
        except Exception:
            pass
    with col_title:
        st.title("הערכת מועמד לוועדת קבלה")

    # ── ועדות פעילות ──
    committees = load_committees()
    active = committees[committees["active"]] if not committees.empty else pd.DataFrame()
    if active.empty:
        st.warning("אין ועדות פעילות כרגע. פנו למנהל המערכת.")
        return

    if len(active) == 1:
        comm = active.iloc[0]
        st.info(f"**ועדה פעילה:** {comm['name']}  |  {comm['date']}")
    else:
        opts = {f"{r['name']} ({r['date']})": r["committee_id"] for _, r in active.iterrows()}
        chosen = st.selectbox("בחרי ועדה", list(opts.keys()))
        comm = active[active["committee_id"] == opts[chosen]].iloc[0]

    committee_id = comm["committee_id"]
    st.markdown("---")

    # ── שם מדרג ──
    rater_name = st.text_input("שמך (חובה)", placeholder="הכניסי את שמך המלא", key="rater_name_input")

    # ── מועמדים ──
    candidates = load_candidates()
    comm_candidates = (
        candidates[(candidates["committee_id"] == committee_id) & candidates["active"]]
        if not candidates.empty else pd.DataFrame()
    )
    if comm_candidates.empty:
        st.warning("אין מועמדים פעילים בוועדה זו.")
        return

    selected_name = st.selectbox("בחרי מועמד לדירוג", comm_candidates["name"].tolist(), key="cand_select")
    candidate = comm_candidates[comm_candidates["name"] == selected_name].iloc[0]
    candidate_id = candidate["candidate_id"]

    # תמונה
    photo_url = drive_url_to_direct(str(candidate.get("photo_url", "") or ""))
    if photo_url:
        col_img, col_nm = st.columns([1, 4])
        with col_img:
            try:
                st.image(photo_url, width=100)
            except Exception:
                pass
        with col_nm:
            st.markdown(f"### {selected_name}")
    else:
        st.markdown(f"### {selected_name}")

    # ── איפוס שלב כשמחליפים מועמד/ועדה ──
    ctx = f"{committee_id}__{candidate_id}"
    if st.session_state.get("_entry_ctx") != ctx:
        st.session_state._entry_ctx = ctx
        st.session_state._entry_step = 0
        existing = existing_submission(committee_id, candidate_id, rater_name) if rater_name.strip() else None
        for crit in CRITERIA:
            default_int = 3
            if existing is not None:
                try:
                    default_int = int(existing[crit["key"]])
                except Exception:
                    pass
            st.session_state[f"sl_{crit['key']}"] = _option_label(default_int, crit["anchors"])
        st.session_state._entry_note = (
            str(existing["note"]) if existing is not None and pd.notna(existing.get("note")) else ""
        )

    # בדיקת הזנה קיימת (לתצוגה בלבד)
    existing = None
    if rater_name.strip():
        existing = existing_submission(committee_id, candidate_id, rater_name)
    if existing is not None:
        st.warning("⚠️ כבר הזנת הערכה על מועמד זה — השינויים ישמרו כעדכון.")

    st.markdown("---")

    # ══ סרגל התקדמות ══
    TOTAL = len(CRITERIA)
    step = st.session_state.get("_entry_step", 0)
    pct = int((step / TOTAL) * 100)

    st.markdown(
        f'<div class="progress-wrap"><div class="progress-fill" style="width:{pct}%"></div></div>'
        f'<div class="progress-label">קריטריון {step + 1} מתוך {TOTAL}</div>',
        unsafe_allow_html=True,
    )

    # ══ קריטריון נוכחי ══
    crit = CRITERIA[step]
    options = [_option_label(n, crit["anchors"]) for n in [1, 2, 3, 4, 5]]

    st.markdown('<div class="criterion-card">', unsafe_allow_html=True)
    st.radio(
        f"### {crit['label']}",
        options=options,
        key=f"sl_{crit['key']}",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # הערה — בשלב האחרון
    if step == TOTAL - 1:
        st.markdown("---")
        note_val = st.text_area(
            "הערה חופשית (אופציונלי)",
            value=st.session_state.get("_entry_note", ""),
            placeholder="הוסיפי כל הערה שתרצי...",
            key="_entry_note_input",
        )
        st.session_state._entry_note = note_val

    st.markdown("---")

    # ══ ניווט ══
    col_back, col_spacer, col_next = st.columns([2, 1, 2])

    with col_back:
        if step > 0:
            if st.button("← הקריטריון הקודם", use_container_width=True):
                st.session_state._entry_step = step - 1
                st.rerun()

    with col_next:
        if step < TOTAL - 1:
            if st.button("הקריטריון הבא →", type="primary", use_container_width=True):
                st.session_state._entry_step = step + 1
                st.rerun()
        else:
            if st.button("שלחי הערכה ✓", type="primary", use_container_width=True):
                if not rater_name.strip():
                    st.error("יש להכניס שם לפני שליחה.")
                else:
                    ratings = {c["key"]: _option_to_int(st.session_state.get(f"sl_{c['key']}", "3")) for c in CRITERIA}
                    note = st.session_state.get("_entry_note", "")
                    result = submit_rating(committee_id, candidate_id, rater_name.strip(), ratings, note)
                    if result == "created":
                        st.markdown(
                            f'<div class="success-banner">ההערכה על {selected_name} נשמרה בהצלחה ✓</div>',
                            unsafe_allow_html=True,
                        )
                        st.balloons()
                        st.session_state._entry_step = 0
                    elif result == "updated":
                        st.success(f"ההערכה על {selected_name} עודכנה בהצלחה ✓")
                        st.session_state._entry_step = 0


# ══════════════════════════════════════════════════════════
#  מסך 2 — תוצאות (נעול בסיסמה)
# ══════════════════════════════════════════════════════════
def page_results():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        try:
            st.image("images.png", width=90)
        except Exception:
            pass
    with col_title:
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
    tab_c, tab_k, tab_del = st.tabs(["ועדות", "מועמדים", "מחיקת הזנות"])

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
                cid = comm["committee_id"]
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1:
                    st.markdown(f"**{comm['name']}** ({comm['date']})")
                with c2:
                    st.markdown("✅ פעילה" if comm["active"] else "🔒 סגורה")
                with c3:
                    lbl = "סגרי" if comm["active"] else "הפעילי"
                    if st.button(lbl, key=f"tog_{cid}"):
                        set_committee_active(cid, not comm["active"])
                        _clear_caches()
                        st.rerun()
                with c4:
                    if st.button("ערכי", key=f"edit_btn_{cid}"):
                        st.session_state[f"editing_{cid}"] = True

                # טופס עריכה — נפתח בלחיצה
                if st.session_state.get(f"editing_{cid}"):
                    with st.form(f"edit_form_{cid}"):
                        st.markdown(f"**עריכת ועדה:** {comm['name']}")
                        edited_name = st.text_input("שם חדש", value=comm["name"])
                        try:
                            from datetime import date as date_type
                            current_date = date_type.fromisoformat(str(comm["date"]))
                        except Exception:
                            current_date = None
                        edited_date = st.date_input("תאריך חדש", value=current_date)
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("שמרי"):
                                if edited_name.strip():
                                    update_committee(cid, edited_name.strip(), edited_date)
                                    st.session_state[f"editing_{cid}"] = False
                                    st.success("הוועדה עודכנה.")
                                    st.rerun()
                        with col_cancel:
                            if st.form_submit_button("בטלי"):
                                st.session_state[f"editing_{cid}"] = False
                                st.rerun()

    with tab_k:
        if not committee_id:
            st.info("בחרי ועדה תחילה.")
            return

        st.markdown("#### הוספת מועמד לוועדה הנוכחית")
        with st.form("form_new_cand"):
            cand_name    = st.text_input("שם מלא")
            uploaded_img = st.file_uploader(
                "תמונת מועמד (אופציונלי)",
                type=["png", "jpg", "jpeg"],
                help="גררי קובץ או לחצי לבחירה",
            )
            if uploaded_img:
                st.image(uploaded_img, width=120, caption="תצוגה מקדימה")

            if st.form_submit_button("הוסיפי מועמד"):
                if cand_name.strip():
                    photo_url = ""
                    if uploaded_img:
                        with st.spinner("מעלה תמונה..."):
                            try:
                                photo_url = upload_photo_to_drive(
                                    uploaded_img.read(),
                                    uploaded_img.name,
                                    uploaded_img.type,
                                )
                            except Exception as e:
                                st.warning(f"התמונה לא הועלתה: {e}")
                    cid = add_candidate(committee_id, cand_name.strip(), photo_url)
                    if cid:
                        st.success(f"מועמד נוסף{'עם תמונה' if photo_url else ''} ✓")
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

    with tab_del:
        st.markdown("#### מחיקת הזנות")
        if not committee_id:
            st.info("בחרי ועדה תחילה.")
        else:
            subs = load_submissions()
            comm_subs = (
                subs[subs["committee_id"] == str(committee_id)]
                if not subs.empty else pd.DataFrame()
            )
            all_cands = load_candidates()

            if comm_subs.empty:
                st.info("אין הזנות לוועדה זו.")
            else:
                st.markdown(f"סה\"כ הזנות בוועדה: **{len(comm_subs)}**")

                # מחיקת הזנה בודדת
                st.markdown("---")
                st.markdown("**מחיקת הזנה בודדת:**")
                if not all_cands.empty:
                    cmap = dict(zip(all_cands["candidate_id"], all_cands["name"]))
                    comm_subs = comm_subs.copy()
                    comm_subs["שם מועמד"] = comm_subs["candidate_id"].map(cmap)

                display_options = [
                    f"{row.get('שם מועמד', row['candidate_id'])} — {row['rater_name']} ({row.get('timestamp','')})"
                    for _, row in comm_subs.iterrows()
                ]
                if display_options:
                    chosen_idx = st.selectbox(
                        "בחרי הזנה למחיקה",
                        range(len(display_options)),
                        format_func=lambda i: display_options[i],
                        key="del_single_sel",
                    )
                    chosen_row = comm_subs.iloc[chosen_idx]
                    if st.button("מחקי הזנה זו", key="del_single_btn"):
                        ok = delete_single_submission(
                            str(chosen_row["committee_id"]),
                            str(chosen_row["candidate_id"]),
                            str(chosen_row["rater_name"]),
                        )
                        if ok:
                            st.success("ההזנה נמחקה.")
                            st.rerun()

                # מחיקת הכל
                st.markdown("---")
                st.markdown("**מחיקת כל ההזנות לוועדה זו:**")
                confirm = st.checkbox("כן, אני רוצה למחוק את כל ההזנות", key="del_all_confirm")
                if confirm:
                    if st.button("מחקי הכל", type="primary", key="del_all_btn"):
                        n = delete_submissions_for_committee(str(committee_id))
                        st.success(f"נמחקו {n} הזנות.")
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
        try:
            st.image("images.png", width=140)
        except Exception:
            pass
        st.markdown("---")
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
