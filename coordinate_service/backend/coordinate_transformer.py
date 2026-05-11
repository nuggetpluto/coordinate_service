import json
import pandas as pd
import sympy as sp


REQUIRED_COLUMNS = ["Name", "X", "Y", "Z"]


def load_parameters(param_file: str) -> dict:
    with open(param_file, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_dataframe(df: pd.DataFrame) -> None:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing_columns:
        raise ValueError(
            f"В файле отсутствуют обязательные столбцы: {', '.join(missing_columns)}"
        )


def transform_coordinates(
    system_from: str,
    system_to: str,
    input_file: str,
    param_file: str,
    output_file: str | None = None
) -> pd.DataFrame:
    df = pd.read_csv(input_file)
    validate_dataframe(df)

    parameters = load_parameters(param_file)

    if system_from not in parameters:
        raise ValueError(f"Неизвестная исходная система координат: {system_from}")

    if system_to not in parameters:
        raise ValueError(f"Неизвестная конечная система координат: {system_to}")

    x, y, z = sp.symbols("x y z")
    dx, dy, dz, wx, wy, wz, m = sp.symbols("dx dy dz wx wy wz m")

    wrx = wx / 3600 * sp.pi / 180
    wry = wy / 3600 * sp.pi / 180
    wrz = wz / 3600 * sp.pi / 180
    m_corr = m * 10 ** -6

    forward_formula = [
        (x + wrz * y - wry * z) * (1 + m_corr) + dx,
        (-wrz * x + y + wrx * z) * (1 + m_corr) + dy,
        (wry * x - wrx * y + z) * (1 + m_corr) + dz
    ]

    reverse_formula = [
        (x - wrz * y + wry * z) * (1 - m_corr) - dx,
        (wrz * x + y - wrx * z) * (1 - m_corr) - dy,
        (-wry * x + wrx * y + z) * (1 - m_corr) - dz
    ]

    param_from = parameters[system_from]
    param_to = parameters[system_to]

    results = []

    for _, row in df.iterrows():
        first_step_args = {
            x: row["X"],
            y: row["Y"],
            z: row["Z"],
            dx: param_from["dx"],
            dy: param_from["dy"],
            dz: param_from["dz"],
            wx: param_from["wx"],
            wy: param_from["wy"],
            wz: param_from["wz"],
            m: param_from["m"]
        }

        x_mid = forward_formula[0].evalf(subs=first_step_args)
        y_mid = forward_formula[1].evalf(subs=first_step_args)
        z_mid = forward_formula[2].evalf(subs=first_step_args)

        second_step_args = {
            x: x_mid,
            y: y_mid,
            z: z_mid,
            dx: param_to["dx"],
            dy: param_to["dy"],
            dz: param_to["dz"],
            wx: param_to["wx"],
            wy: param_to["wy"],
            wz: param_to["wz"],
            m: param_to["m"]
        }

        x_result = reverse_formula[0].evalf(subs=second_step_args)
        y_result = reverse_formula[1].evalf(subs=second_step_args)
        z_result = reverse_formula[2].evalf(subs=second_step_args)

        results.append({
            "Name": row["Name"],
            "X_new": float(x_result),
            "Y_new": float(y_result),
            "Z_new": float(z_result)
        })

    result_df = pd.DataFrame(results)

    if output_file:
        result_df.to_csv(output_file, index=False)

    return result_df


def get_available_systems(param_file: str) -> list[str]:
    parameters = load_parameters(param_file)
    return list(parameters.keys())