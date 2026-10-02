# tool desde api rest
from langchain_core.tools import tool


@tool("book_appointment", description="Book a medical appointment for a given date, time, doctor and patient")
def book_appointment(date: str, time: str, doctor: str, patient: str):
    # TODO : Implementar la lógica para reservar una cita médica.
    return f"Appointment booked for {patient} with Dr. {doctor} on {date} at {time}."

@tool("get_appointment_availability", description="Get the availability of a medical appointment.")
def get_appointment_availability(date: str, time: str, doctor: str):
    # TODO : Implementar la lógica para obtener la disponibilidad de una cita médica.
    return f"""
    The Availability for Dr. {doctor} on {date} at {time} is as follows:
    - Monday: 9:00 AM - 5:00 PM
    - Tuesday: 10:00 AM - 4:00 PM
    - Wednesday: 9:00 AM - 5:00 PM
    - Thursday: 10:00 AM - 4:00 PM
    - Friday: 9:00 AM - 3:00 PM
    """

tools = [get_appointment_availability, book_appointment]
