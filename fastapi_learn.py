from fastapi import FastAPI
from pydantic import BaseModel
from collections import defaultdict

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{items}")
async def root(items):
    return {"items" : [1,2,3,4,5,6,7]}

'''
FastAPI supports so many different datatypes so we need not worry about returning anything
'''

@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: int, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item

'''
A function written using both query parameters and path parameters
'''

items = [
    {'id' : 1,'name' : 'Scrubber'},
    {'id' : 2,'name' : "Mirror"}
]

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None



@app.post("/postitems/")
async def postitems(item : dict):
    item['id'] = len(items)+1
    items.append(item)
    return items

@app.put("/items/{item_id}")
async def replace_item(item_id: int, new_item: dict):
    for i in range(len(items)):
        if items[i]['id'] == item_id:
            items[i] = {'id': item_id, **new_item}
            return items[i]
    
    return {"error": "Item not found"}

from fastapi import HTTPException

@app.delete("/delitems/{item_id}")
async def delete_item(item_id: int):
    for i in range(len(items)):
        if items[i]['id'] == item_id:
            deleted_item = items.pop(i)
            return {"deleted" : deleted_item,"items":items}
        #Deleted item along with the items array with the item deleted
    
    raise HTTPException(status_code=404, detail="Item not found")