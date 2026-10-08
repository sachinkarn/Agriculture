"""Irrigation advice: should the farmer water today, how much and when?

Rule-based on purpose: it is transparent and explainable. The function signature is the
seam where a trained model can replace the rules later.
"""


def advise_irrigation(crop: str, soil_moisture: float, temperature: float, humidity: float,
                      rain_probability: float, diseased: bool = False) -> dict:
    mo, t, h, r = soil_moisture, temperature, humidity, rain_probability
    go = False
    if r >= 60:
        title, why, save, mm, when = ("Do not irrigate today",
                                      f"Rain chance is {r:g}%, so rainfall will water the crop.",
                                      25, 0, "No watering needed")
    elif mo >= 55:
        title, why, save, mm, when = ("Do not irrigate today",
                                      f"Soil moisture is {mo:g}%, which is sufficient.",
                                      18, 0, "Recheck tomorrow morning")
    elif mo < 30:
        title, why, save, mm, when, go = ("Irrigate now",
                                          f"Soil is dry ({mo:g}%) and rain chance is only {r:g}%.",
                                          0, 25 if t > 35 else 20, "Early morning", True)
    else:
        title, why, save, mm, when = ("Light irrigation this evening",
                                      f"Soil moisture is moderate ({mo:g}%) and rain chance is {r:g}%.",
                                      10, 10, "Evening")
    if diseased and h > 70 and mm:
        why += " Water at the base. Wet leaves can spread the disease."
    return {
        "title": title, "why": why, "mm": mm, "time": when, "go": go, "save": save,
        "inputs": [["Crop", crop], ["Soil moisture", f"{mo:g}%"], ["Rain probability", f"{r:g}%"],
                   ["Temperature", f"{t:g}°C"], ["Humidity", f"{h:g}%"]],
    }
