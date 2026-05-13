import base64

import pandas as pd
import streamlit as st

from api_client import (
    get_systems,
    transform_file
)


REQUIRED_COLUMNS = ["Name", "X", "Y", "Z"]


def validate_csv(df: pd.DataFrame) -> list[str]:
    errors = []

    if df.empty:
        errors.append("CSV-файл пустой.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            "В файле отсутствуют обязательные столбцы: "
            + ", ".join(missing_columns)
        )

    for column in ["X", "Y", "Z"]:
        if column in df.columns:
            numeric_column = pd.to_numeric(df[column], errors="coerce")

            if numeric_column.isna().any():
                errors.append(
                    f"Столбец {column} должен содержать только числовые значения."
                )

    return errors


st.set_page_config(
    page_title="Coordinate Transformer",
    layout="wide"
)

st.title("Система преобразования координат")

st.write(
    "Веб-приложение для загрузки CSV-файлов и преобразования координат "
    "между различными геодезическими системами координат."
)

with st.spinner("Подключение к backend. Если сервис спал, запуск может занять до минуты..."):
    try:
        systems = get_systems()

    except Exception as error:
        st.error(f"Ошибка подключения к backend: {error}")
        st.stop()


st.subheader("Параметры преобразования")

col1, col2 = st.columns(2)

with col1:
    system_from = st.selectbox(
        "Исходная система координат",
        systems
    )

with col2:
    system_to = st.selectbox(
        "Конечная система координат",
        systems,
        index=min(1, len(systems) - 1)
    )


if system_from == system_to:
    st.warning("Исходная и конечная системы совпадают. Выберите разные системы координат.")


uploaded_file = st.file_uploader(
    "Загрузите CSV-файл с координатами",
    type=["csv"]
)


if uploaded_file:
    st.success(f"Файл загружен: {uploaded_file.name}")

    try:
        preview_df = pd.read_csv(uploaded_file)

        validation_errors = validate_csv(preview_df)

        if validation_errors:
            st.error("Файл не прошёл проверку.")

            for error in validation_errors:
                st.write(f"— {error}")

            st.info("CSV-файл должен содержать столбцы: Name, X, Y, Z")
            st.stop()

        st.subheader("Предпросмотр исходных данных")
        st.dataframe(preview_df, use_container_width=True)

        st.subheader("Краткая информация о файле")

        info_col1, info_col2, info_col3 = st.columns(3)

        info_col1.metric("Количество точек", len(preview_df))
        info_col2.metric("Количество столбцов", len(preview_df.columns))
        info_col3.metric(
            "Пропущенные значения",
            int(preview_df.isna().sum().sum())
        )

        uploaded_file.seek(0)

        transform_disabled = system_from == system_to

        if st.button(
            "Преобразовать координаты",
            disabled=transform_disabled
        ):
            with st.spinner("Выполняется преобразование координат..."):
                result = transform_file(
                    system_from,
                    system_to,
                    uploaded_file
                )

                result_df = pd.DataFrame(result["result"])

                st.success("Преобразование выполнено успешно")

                st.subheader("Результат преобразования")
                st.dataframe(result_df, use_container_width=True)

                csv_data = result_df.to_csv(index=False)

                st.download_button(
                    label="Скачать результат CSV",
                    data=csv_data,
                    file_name="transformed_coordinates.csv",
                    mime="text/csv"
                )

                report_bytes = base64.b64decode(
                    result["report_file"]
                )

                st.download_button(
                    label="Скачать Word-отчёт",
                    data=report_bytes,
                    file_name="coordinate_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

    except Exception as error:
        st.error(f"Ошибка при обработке файла: {error}")