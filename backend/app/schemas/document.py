import datetime as dt

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: str
    filename: str
    size_bytes: int
    content_type: str
    uploaded_at: dt.datetime