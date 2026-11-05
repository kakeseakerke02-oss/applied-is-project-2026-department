from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Бағалау құралдары қоры")
st.title("Кафедраның бағалау құралдары қоры")
st.write("Пәндер, оқытушылар, бағалау құралдары және бағалау критерийлері.")
st.info("1-зертханалық жұмыс: жобаның бастапқы құрылымы дайын.")
image = Path(__file__).resolve().parents[2] / "docs" / "er_diagram.png"
st.image(str(image), caption="Деректер базасының ER диаграммасы")
