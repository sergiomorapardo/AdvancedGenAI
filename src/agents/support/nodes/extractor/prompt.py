from pydantic import BaseModel, Field


# En este nodo el esquema y las descripciones son las instrucciones del modelo.
class ContactInfo(BaseModel):
    """Contact information for a person."""

    name: str | None = Field(description="The name of the person", default=None)
    email: str | None = Field(description="The email address of the person", default=None)
    phone: str | None = Field(description="The phone number of the person", default=None)
    age: int | None = Field(description="The age of the person", default=None)
