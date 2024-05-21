import uvicorn
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from lib.translate import Translator

class Item(BaseModel):
    data: str
    
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "Wod"}

@app.post("/translate")
async def create_item(item: Item):
    translator = Translator(item.dict()['data'])
    return translator.translate()

if __name__ == "__main__" :
    uvicorn.run(app)