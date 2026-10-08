"""Static agronomy knowledge: supported crops, disease types and the "what to do" steps.

The advice here is general guidance for a hackathon prototype. It is not a substitute for
a local agriculture officer, and no chemical product or dose is recommended.
"""

SUPPORTED_CROPS = ["Apple", "Corn", "Orange", "Potato"]

CROP_DEFAULT_TYPE = {"Apple": "fungal", "Corn": "fungal", "Orange": "bacterial", "Potato": "fungal"}

# Used when the model predicts a disease we have no specific advice for.
CROP_DEFAULT_ACTIONS = {
    "Apple": ["Remove and destroy fallen infected leaves", "Prune for better airflow",
              "Avoid overhead watering", "Recheck in 3 days"],
    "Corn": ["Scout the upper leaves weekly", "Avoid dense planting",
             "Plan crop rotation next season", "Recheck in 3 days"],
    "Orange": ["Mark and isolate affected trees", "Control psyllid insects on new shoots",
               "Inform your local agri officer", "Recheck in 7 days"],
    "Potato": ["Remove infected leaves and plants", "Avoid overhead irrigation",
               "Hill soil over the tubers", "Recheck in 48 hours"],
}

# disease name -> (type, actions)
DISEASE_INFO = {
    "Apple scab": ("fungal", CROP_DEFAULT_ACTIONS["Apple"]),
    "Black rot": ("fungal", ["Prune out dead or cankered wood and mummified fruit",
                             "Remove infected leaves and fruit from the orchard",
                             "Improve airflow through pruning", "Recheck in 3 days"]),
    "Cedar apple rust": ("fungal", ["Remove nearby juniper or cedar hosts if possible",
                                    "Remove heavily infected leaves",
                                    "Avoid overhead watering", "Recheck in 3 days"]),
    "Northern leaf blight": ("fungal", CROP_DEFAULT_ACTIONS["Corn"]),
    "Gray leaf spot": ("fungal", ["Scout the upper leaves weekly", "Avoid dense planting",
                                  "Rotate away from maize residue next season", "Recheck in 3 days"]),
    "Common rust": ("fungal", ["Scout both sides of the leaves weekly", "Avoid dense planting",
                               "Ask your local agri officer about resistant varieties", "Recheck in 3 days"]),
    "Citrus greening": ("bacterial", CROP_DEFAULT_ACTIONS["Orange"]),
    "Late blight": ("fungal", CROP_DEFAULT_ACTIONS["Potato"]),
    "Early blight": ("fungal", ["Remove the lowest infected leaves", "Avoid overhead irrigation",
                                "Keep plants well fed and watered at the base", "Recheck in 3 days"]),
}

HEALTHY_ACTIONS = ["Keep your current routine", "Scout once a week"]


def disease_type(disease: str, crop: str) -> str:
    return DISEASE_INFO.get(disease, (CROP_DEFAULT_TYPE.get(crop, "fungal"), None))[0]


def disease_actions(disease: str, crop: str) -> list[str]:
    info = DISEASE_INFO.get(disease)
    if info:
        return list(info[1])
    return list(CROP_DEFAULT_ACTIONS.get(crop, HEALTHY_ACTIONS))
