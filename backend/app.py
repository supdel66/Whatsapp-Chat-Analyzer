from fastapi import FastAPI
from fastapi import UploadFile
from fastapi.responses import JSONResponse
import preprocessor
import uuid
import pandas as pd

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://whatsappanalyze.supriyapoudel.com.np",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Global store for the processed DataFrame
store={}

@app.get("/")
def home():
    return {"message": "Hello welcome to whatsapp chat analyzer"}

# file upload option
@app.post("/uploadfile")
async def upload_file(file: UploadFile):
    df = preprocessor.preprocess(file.file)
    file_id=str(uuid.uuid1())
    store[file_id]=df
    count=preprocessor.get_analysis(df)
    return {"file_id": file_id, "analysis": count} 


@app.post("/search")
async def search(file_id:str,keyword:str=None):
    df=store[file_id]
    results = [
        {
            "date": str(row.date).split(" ")[0],
            "time": str(row.date).split(" ")[1],
            "user": str(row.user),
            "text": str(row.text)
        }
        for _, row in df.iterrows()
        if keyword.lower() in str(row.text).lower()
    ]
    return results

@app.post("/dated_convo")
async def dated_convo(file_id:str,date:str=None):
    df=store[file_id]
    target_date = pd.to_datetime(date).date()
    results = [
        {
            "date": str(row.date).split(" ")[0],
            "time": str(row.date).split(" ")[1],
            "user": str(row.user),
            "text": str(row.text)
        }
        for _, row in df.iterrows()
        if row.date.date() == target_date
    ]
    return results

