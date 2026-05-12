import os
import uuid
import base64
import pandas as pd

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from coordinate_transformer import (
        transform_coordinates,
        get_available_systems,
        load_parameters
    )
    from report_generator import generate_report
except ModuleNotFoundError:
    from coordinate_transformer import (
        transform_coordinates,
        get_available_systems,
        load_parameters
    )
    from report_generator import generate_report


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAM_FILE = os.path.join(BASE_DIR, "backend", "parameters.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Coordinate Transformation Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Coordinate Transformation API работает",
        "endpoints": {
            "systems": "/systems",
            "transform": "/transform"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/systems")
def systems():
    return {
        "systems": get_available_systems(PARAM_FILE)
    }


@app.post("/transform")
async def transform(
    system_from: str = Form(...),
    system_to: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только CSV-файлы"
        )

    input_filename = f"{uuid.uuid4()}_{file.filename}"
    report_filename = f"{uuid.uuid4()}_report.docx"

    input_path = os.path.join(UPLOAD_DIR, input_filename)
    report_path = os.path.join(UPLOAD_DIR, report_filename)

    try:
        content = await file.read()

        with open(input_path, "wb") as saved_file:
            saved_file.write(content)

        input_df = pd.read_csv(input_path)

        result_df = transform_coordinates(
            system_from=system_from,
            system_to=system_to,
            input_file=input_path,
            param_file=PARAM_FILE
        )
        all_parameters = load_parameters(PARAM_FILE)
        transform_parameters = all_parameters[system_from]

        generate_report(
            source_system=system_from,
            target_system=system_to,
            input_df=input_df,
            result_df=result_df,
            output_path=report_path,
            transform_parameters=transform_parameters
        )

        with open(report_path, "rb") as report_file:
            report_base64 = base64.b64encode(report_file.read()).decode("utf-8")

        return {
            "system_from": system_from,
            "system_to": system_to,
            "rows": len(result_df),
            "result": result_df.to_dict(orient="records"),
            "report_file": report_base64
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки файла: {str(error)}"
        )

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

        if os.path.exists(report_path):
            os.remove(report_path)