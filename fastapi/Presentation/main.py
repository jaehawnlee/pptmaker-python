import uvicorn
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from lib.maker import Maker
from os import getcwd
from fastapi.responses import FileResponse

class Item(BaseModel):
    command : dict
    
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "ppt maker"}

@app.post("/make")
async def create_item(item: Item):
    maker = Maker(item.dict()['command'])
    name_file = maker.making()
    #return { "file" : FileResponse(path=getcwd() + "/" + name_file, media_type='application/octet-stream', filename=name_file)} 
    return FileResponse(path=getcwd() + "/" + name_file, media_type='application/octet-stream', filename=name_file)


if __name__ == "__main__" :
    uvicorn.run(app)