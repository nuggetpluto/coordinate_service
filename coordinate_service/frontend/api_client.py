import requests


API_URL = "https://coordinate-service.onrender.com"


def get_systems():
    response = requests.get(f"{API_URL}/systems", timeout=60)

    if response.status_code != 200:
        raise Exception("Ошибка получения систем координат")

    return response.json()["systems"]


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
        timeout=120
    )

    if response.status_code != 200:
        raise Exception(response.json()["detail"])

    return response.json()