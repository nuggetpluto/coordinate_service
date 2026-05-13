import time
import requests


API_URL = "https://coordinate-service.onrender.com"


def get_systems():
    last_error = None

    for _ in range(5):
        try:
            response = requests.get(f"{API_URL}/systems", timeout=90)

            if response.status_code == 200:
                return response.json()["systems"]

            last_error = response.text

        except requests.RequestException as error:
            last_error = str(error)

        time.sleep(5)

    raise Exception(f"Ошибка получения систем координат: {last_error}")


def transform_file(system_from, system_to, file):
    files = {
        "file": (file.name, file, "text/csv")
    }

    data = {
        "system_from": system_from,
        "system_to": system_to
    }

    response = requests.post(
        f"{API_URL}/transform",
        files=files,
        data=data,
        timeout=180
    )

    if response.status_code != 200:
        raise Exception(response.json()["detail"])

    return response.json()