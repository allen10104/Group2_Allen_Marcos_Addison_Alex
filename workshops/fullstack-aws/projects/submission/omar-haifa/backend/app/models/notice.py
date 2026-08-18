from pydantic import BaseModel


# Defines the information needed when creating a new notice
class NoticeCreate(BaseModel):
    name: str
    message: str
    priority: str = "Normal"


# Defines how a notice will be returned from the API
class NoticeResponse(BaseModel):
    id: str
    name: str
    message: str
    priority: str