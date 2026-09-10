#импорт билблиотек
import re
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

#путь до файла это одно и тоже просто бедолага не видит почему то raw
LOCAL_FILE = "primers_example_database.xlsx"
DATA_URL = "https://raw.githubusercontent.com/rerarkkkkch/pomogite123/main/primers_example_database.xlsx"

#основные настройки страницы
st.set_page_config(
    layout="wide",
    page_title="Evogen primer search",
    page_icon="♿",
)

#подгрузка данных
@st.cache_data
def load_data(file_path: str = LOCAL_FILE) -> pd.DataFrame:
    path = Path(file_path)
    if path.exists():
        try:
            df = pd.read_excel(path, engine="openpyxl")
        except Exception as exc:
            st.warning(f"Не удалось прочитать локальный Excel: {exc}")
            return pd.DataFrame()
        return _normalize_dataframe(df)

#это добавил копилот-клод-гпт-гитаб ии без понятия но оно рабоатет и ладно
    if DATA_URL and DATA_URL.startswith(("http://", "https://")):
        try:
            req = Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=30) as response:
                payload = response.read()
            if not payload:
                st.warning("Удалённый Excel-файл пустой или недоступен.")
                return pd.DataFrame()
            df = pd.read_excel(BytesIO(payload), engine="openpyxl")
            return _normalize_dataframe(df)
        except Exception as exc:
            st.warning(f"Файл не найден и удалённый источник недоступен: {exc}")
            return pd.DataFrame()

    st.warning(f"Файл {file_path} не найден. Положите Excel в корень проекта или укажите корректную ссылку на .xlsx.")
    return pd.DataFrame()

#переводим колонки с координатами в числовой формат, чтобы можно было сравнивать
def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "grch37_start_coordinates",
        "grch37_end_coordinates",
        "grch38_start_coordinates",
        "grch38_end_coordinates",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

#проверка координат
def validate_coordinates(coordinates: str):
    coordinates_lower = coordinates.strip().lower()
    pattern = r"^(chr[a-zA-Z0-9]+):(\d+)-(\d+)$"
    match = re.fullmatch(pattern, coordinates_lower)
    if not match:
        return False, None, None, None, "Неверный формат координат. Используйте пример: chrx:12345-12346"

    chr_name, start, end = match.group(1), int(match.group(2)), int(match.group(3))
    if start > end:
        return False, chr_name, start, end, "Начало диапазона больше конца. Проверьте координаты."
    return True, chr_name, start, end, ""

#поиск праймера
def find_primer(df: pd.DataFrame, chr_name: str, start: int, end: int, assembly: str):
    if df.empty:
        return None, "Данные не загружены"

    if assembly == "Grch37":
        start_col = "grch37_start_coordinates"
        end_col = "grch37_end_coordinates"
    else:
        start_col = "grch38_start_coordinates"
        end_col = "grch38_end_coordinates"

    required_cols = {"chr", start_col, end_col}
    missing = required_cols - set(df.columns)
    if missing:
        return None, f"В данных отсутствуют колонки: {sorted(missing)}"

    mask = (
        df["chr"].astype(str).str.lower() == chr_name.lower()
    ) & (
        df[start_col].between(start, end, inclusive="both")
    )

    result = df.loc[mask]
    if result.empty:
        return None, "Праймер не найден"
    return result.iloc[0], "match"

#псевдографика 
def draw_primer_landing(primer_data, coordinates_start: int, coordinates_end: int, assembly: str) -> str:
    if assembly == "Grch37":
        p_start = int(primer_data["grch37_start_coordinates"])
        p_end = int(primer_data["grch37_end_coordinates"])
    else:
        p_start = int(primer_data["grch38_start_coordinates"])
        p_end = int(primer_data["grch38_end_coordinates"])

    total_length: int = max(coordinates_end - coordinates_start, 1)
    line_length = 50

    if "lenght" in primer_data and pd.notna(primer_data["lenght"]):
        primer_length = int(primer_data["lenght"])
    else:
        primer_length = max(p_end - p_start, 1)

    # Позиция праймера на шкале.
    start_percent = ((p_start - coordinates_start) / total_length) * 100
    end_percent = ((p_start + primer_length - coordinates_start) / total_length) * 100
    start_pos = int((max(start_percent, 0) / 100) * line_length)
    end_pos = int((min(end_percent, 100) / 100) * line_length)

    visual = [
        f"Диапазон: {coordinates_start:,} - {coordinates_end:,} ({total_length:,} bp)",
        f"Праймер: {p_start:,} - {p_end:,} ({primer_length:,} bp)",
        "",
    ]

    chars = ["X" if start_pos <= i <= end_pos else "-" for i in range(line_length)]
    visual.append("".join(chars))
    visual.append(f"{coordinates_start:,}{' ' * 25}{coordinates_end:,}")
    return "\n".join(visual)

#основное приложение 
df = load_data()

st.title("Evogen primer search")
st.write("Впишите координаты как на примере: chrx:123456789-123467810")

col1, col2, col3 = st.columns([1.5, 4, 1])
with col1:
    assembly = st.selectbox(
        "Grch38/Grch37",
        options=["Grch38", "Grch37"],
        label_visibility="collapsed",
        key="assembly_selector",
        index=0,
    )
with col2:
    coordinates = st.text_input(
        "Coordinates",
        placeholder="chrx:123456789-123467810",
        label_visibility="collapsed",
        key="coordinates_input",
    )
with col3:
    st.button("🔍", use_container_width=True, key="search_btn")

if df.empty:
    st.warning("Данные не загружены. Проверьте файл primers_example_database.xlsx или доступ к удалённому источнику.")
    st.stop()

if st.session_state.get("search_btn"):
    is_valid, chr_name, start, end, error_msg = validate_coordinates(coordinates)
    if not is_valid:
        st.error(error_msg)
        st.stop()

    primer_data, status = find_primer(df, chr_name, start, end, assembly)
    if primer_data is None:
        st.warning(f"Праймер {chr_name}:{start}-{end} не найден в сборке {assembly}.")
        st.info("Проверьте сборку и координаты. Возможно, праймер находится в другой сборке.")
        st.stop()

    primer_name = primer_data.get("primer_name", "-")
    st.markdown(f"**{primer_name}**")

    sequence = primer_data.get("sequence", "-")
    st.write(f"Последовательность: {sequence}")

    chain = primer_data.get("chain", "-")
    st.write(f"Цепь: {chain}")

    st.markdown("Посадка праймера:")
    visual = draw_primer_landing(primer_data, start, end, assembly)
    st.code(visual, language="text")

