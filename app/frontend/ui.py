"""Қазақша интерфейс. Барлық дерек FastAPI арқылы оқылады және сақталады."""
from decimal import Decimal, InvalidOperation
from pathlib import Path
import streamlit as st
from app.frontend.api import APIError, api_request

ROOT = Path(__file__).resolve().parents[2]
TYPES = ["Тест", "Емтихан", "Зертханалық жұмыс", "Практикалық тапсырма"]
PAGES = ["Бағалау құралдары", "Құрал қосу", "Құралды өзгерту", "Құралды жою", "Жоба туралы"]
st.set_page_config(page_title="Кафедра қоры", page_icon="📚", layout="wide")

def reset_filters():
    for key, value in {"search": "", "discipline": 0, "author": 0, "kind": "Барлық түр", "min": None, "max": None}.items():
        st.session_state["filter_" + key] = value

def call(method, path, **kwargs):
    try:
        return api_request(method, path, **kwargs)
    except APIError as error:
        st.error(str(error))
        return None

def normalize_criteria(rows):
    result = []
    for row in rows:
        description = str(row.get("Критерий") or "").strip()
        value = row.get("Балл")
        if not description and value is None:
            continue
        try:
            score = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Әр критерийге дұрыс балл енгізіңіз") from None
        if not description or not score.is_finite() or not (0 < score <= Decimal("9999.99")):
            raise ValueError("Критерий сипаттамасын және нөлден үлкен баллын енгізіңіз")
        result.append({"description": description, "max_score": str(score)})
    if not result:
        raise ValueError("Кемінде бір бағалау критерийі қажет")
    if len({r["description"] for r in result}) != len(result):
        raise ValueError("Критерий сипаттамалары қайталанбауы тиіс")
    return result

def detail(tool):
    a, b, c = st.columns(3)
    a.write(f"**Пән:** {discipline_labels.get(tool['discipline_id'], 'Белгісіз пән')}")
    b.write(f"**Автор:** {teacher_labels.get(tool['author_id'], 'Белгісіз автор')}")
    c.write(f"**Жалпы балл:** {tool['total_score']}")
    st.write(tool["content"])
    st.dataframe([{"Критерий": r["description"], "Максималды балл": float(r["max_score"])} for r in tool["criteria"]],
                 hide_index=True, width="stretch")

st.sidebar.title("Кафедра қоры")
st.sidebar.caption("Бағалау материалдарын басқару")
if "open_created_tool" in st.session_state:
    st.session_state["page"] = PAGES[0]
    st.session_state["selected_tool"] = st.session_state.pop("open_created_tool")
    reset_filters()
page = st.sidebar.radio("Бөлім", PAGES, key="page")
st.sidebar.divider()
if st.sidebar.button("Деректерді жаңарту", width="stretch"):
    st.rerun()
st.title("Кафедраның бағалау құралдары қоры")
st.caption("Пәндерге арналған тапсырмалар, авторлар және бағалау критерийлері бір жерде.")
if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))
try:
    references = api_request("GET", "/reference-data")
    all_tools = api_request("GET", "/assessment-tools")
except APIError as error:
    st.error(str(error))
    st.info("Алдымен жоба папкасындағы бөлек терминалда серверді іске қосыңыз, содан кейін «Деректерді жаңарту» басыңыз.")
    st.code(r".\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001", language="powershell")
    st.stop()
discipline_labels = {r["id"]: r["label"] for r in references["disciplines"]}
teacher_labels = {r["id"]: r["label"] for r in references["teachers"]}
tool_labels = {t["id"]: f"№{t['id']} · {t['title']}" for t in all_tools}
st.sidebar.success("Сервермен байланыс бар")
m1, m2, m3 = st.columns(3)
m1.metric("Құралдар", len(all_tools))
m2.metric("Пәндер", len(discipline_labels))
m3.metric("Критерийлер", sum(len(t["criteria"]) for t in all_tools))
st.divider()

if page == "Бағалау құралдары":
    st.subheader("Құралдар қоры")
    with st.container(border=True):
        a, b, c = st.columns([2, 1, 1])
        search = a.text_input("Атауы бойынша іздеу", placeholder="Мысалы, SQL", key="filter_search", live=True)
        discipline = b.selectbox("Пән", [0] + list(discipline_labels), format_func=lambda k: discipline_labels.get(k, "Барлық пән"), key="filter_discipline")
        author = c.selectbox("Автор", [0] + list(teacher_labels), format_func=lambda k: teacher_labels.get(k, "Барлық автор"), key="filter_author")
        a, b, c = st.columns(3)
        kind = a.selectbox("Құрал түрі", ["Барлық түр"] + TYPES, key="filter_kind")
        minimum = b.number_input("Ең төменгі жалпы балл", min_value=0.0, value=None, key="filter_min")
        maximum = c.number_input("Ең жоғарғы жалпы балл", min_value=0.0, value=None, key="filter_max")
        st.button("Сүзгілерді тазарту", on_click=reset_filters)
    if minimum is not None and maximum is not None and minimum > maximum:
        st.error("Ең төменгі балл жоғарғы баллдан үлкен болмауы тиіс")
        st.stop()
    values = {"search": search.strip(), "discipline_id": discipline, "author_id": author,
              "tool_type": None if kind == "Барлық түр" else kind, "min_score": minimum, "max_score": maximum}
    params = {k: v for k, v in values.items() if v is not None and v != "" and not (k.endswith("_id") and v == 0)}
    tools = call("GET", "/assessment-tools", params=params) if params else all_tools
    if tools is not None:
        st.caption(f"Табылды: {len(tools)} құрал")
        if not tools:
            st.info("Бұл шарттарға сәйкес құрал табылмады. Сүзгілерді өзгертіп көріңіз.")
        else:
            st.dataframe([{"№": t["id"], "Атауы": t["title"], "Түрі": t["tool_type"],
                           "Пән": discipline_labels.get(t["discipline_id"], ""), "Автор": teacher_labels.get(t["author_id"], ""),
                           "Жалпы балл": float(t["total_score"])} for t in tools], hide_index=True, width="stretch")
            tool_ids = [t["id"] for t in tools]
            if st.session_state.get("selected_tool") not in tool_ids:
                st.session_state["selected_tool"] = tool_ids[0]
            chosen = st.selectbox("Толық көру үшін құралды таңдаңыз", tool_ids, format_func=tool_labels.get, key="selected_tool")
            current = next(t for t in tools if t["id"] == chosen)
            with st.expander(current["title"], expanded=True):
                detail(current)

elif page in ("Құрал қосу", "Құралды өзгерту"):
    editing = page == "Құралды өзгерту"
    st.subheader(page)
    if not discipline_labels or not teacher_labels:
        st.info("Алдымен бастапқы пәндер мен оқытушыларды seed.py арқылы енгізіңіз.")
        st.stop()
    current = None
    if editing:
        if not all_tools:
            st.info("Өзгертетін құрал жоқ. «Құрал қосу» бөлімінен жаңасын жасаңыз.")
            st.stop()
        chosen = st.selectbox("Өзгертетін құрал", list(tool_labels), format_func=tool_labels.get)
        current = call("GET", f"/assessment-tools/{chosen}")
        if current is None:
            st.stop()
    form_key = f"edit_{current['id']}" if editing else f"create_{st.session_state.get('create_generation', 0)}"
    initial = current or {"title": "", "content": "", "tool_type": TYPES[0], "discipline_id": next(iter(discipline_labels)), "author_id": next(iter(teacher_labels))}
    criteria = ([{"Критерий": c["description"], "Балл": float(c["max_score"])} for c in current["criteria"]]
                if editing else [{"Критерий": "Дұрыс орындалуы", "Балл": 20.0}, {"Критерий": "Шешімді түсіндіру", "Балл": 10.0}])
    with st.form(form_key):
        title = st.text_input("Құрал атауы", value=initial["title"], max_chars=200)
        a, b, c = st.columns(3)
        discipline = a.selectbox("Пән", list(discipline_labels), index=list(discipline_labels).index(initial["discipline_id"]), format_func=discipline_labels.get)
        author = b.selectbox("Автор", list(teacher_labels), index=list(teacher_labels).index(initial["author_id"]), format_func=teacher_labels.get)
        kind = c.selectbox("Құрал түрі", TYPES, index=TYPES.index(initial["tool_type"]))
        content = st.text_area("Тапсырманың мазмұны", value=initial["content"], height=140, max_chars=20000)
        st.markdown("**Бағалау критерийлері**")
        st.caption("Әр критерийге сипаттама мен нөлден үлкен балл енгізіңіз. Төменгі жол арқылы жаңа критерий қосуға болады.")
        rows = st.data_editor(criteria, num_rows="dynamic", hide_index=True, width="stretch", key=form_key + "_criteria",
                              column_config={"Критерий": st.column_config.TextColumn("Бағалау критерийі", required=True),
                                             "Балл": st.column_config.NumberColumn("Максималды балл", min_value=0.01, max_value=9999.99, step=0.5, format="%.2f", required=True)})
        submitted = st.form_submit_button("Өзгерістерді сақтау" if editing else "Құралды қосу", type="primary")
    if submitted:
        try:
            if not title.strip() or not content.strip():
                raise ValueError("Құрал атауы мен тапсырманың мазмұнын толтырыңыз")
            normalized = normalize_criteria(rows)
            payload = {"title": title.strip(), "discipline_id": discipline, "author_id": author, "tool_type": kind, "content": content.strip()}
            if editing:
                payload = {k: v for k, v in payload.items() if v != current[k]}
                if normalized != normalize_criteria(criteria):
                    payload["criteria"] = normalized
                if not payload:
                    st.info("Өзгертілген мән жоқ.")
                else:
                    saved = api_request("PATCH", f"/assessment-tools/{current['id']}", data=payload)
                    st.session_state["notice"] = f"№{saved['id']} құралдың өзгерістері сақталды."
                    st.rerun()
            else:
                payload["criteria"] = normalized
                saved = api_request("POST", "/assessment-tools", data=payload)
                st.session_state["notice"] = f"№{saved['id']} бағалау құралы қосылды."
                st.session_state["create_generation"] = st.session_state.get("create_generation", 0) + 1
                st.session_state["open_created_tool"] = saved["id"]
                st.rerun()
        except (ValueError, APIError) as error:
            st.error(str(error))

elif page == "Құралды жою":
    st.subheader("Бағалау құралын жою")
    if not all_tools:
        st.info("Жоятын құрал жоқ.")
        st.stop()
    chosen = st.selectbox("Жоятын құрал", list(tool_labels), format_func=tool_labels.get)
    current = next(t for t in all_tools if t["id"] == chosen)
    st.markdown(f"**Таңдалған құрал: {current['title']}**")
    detail(current)
    st.warning("Бұл құрал және оған тиесілі барлық бағалау критерийлері базадан жойылады.")
    confirmed = st.checkbox("Осы құралды және оның критерийлерін жоюды растаймын", key=f"confirm_delete_{chosen}")
    if st.button("Құралды жою", type="primary", disabled=not confirmed):
        try:
            api_request("DELETE", f"/assessment-tools/{chosen}")
            st.session_state["notice"] = f"№{chosen} бағалау құралы жойылды."
            st.rerun()
        except APIError as error:
            st.error(str(error))
else:
    st.subheader("Жоба туралы")
    st.write("Жүйе кафедраның бағалау материалдарын пән, автор және критерийлер бойынша бір қорда сақтауға арналған.")
    st.write("Іске асырылған мүмкіндіктер: деректер базасы, қосу, көру, өзгерту, жою және сүзгілеу. Интерфейс FastAPI серверіне қосылған.")
    st.image(str(ROOT / "docs/er_diagram_lab2.png"), caption="Кафедра қорының деректер құрылымы")
