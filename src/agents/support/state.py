from langgraph.graph import MessagesState


class State(MessagesState):
    customer_name: str | None
    name: str | None
    email: str | None
    phone: str | None
    age: int | None
