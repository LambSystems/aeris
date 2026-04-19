from app.sustainability.schemas import CASTNETReading, SustainabilityAdvice, YOLODetection


OBJECT_FACTS = {
    "soda_can": {
        "material": "aluminum",
        "concern": "can persist for decades if littered even though it is highly recyclable",
        "action": "Place it in a recycling bin that accepts aluminum cans.",
    },
    "plastic_bottle": {
        "material": "PET plastic",
        "concern": "breaks down into microplastics and can move through stormwater",
        "action": "Empty it, cap it, and place it in a plastics recycling bin.",
    },
    "cardboard_box": {
        "material": "paper fiber",
        "concern": "loses recycling value when wet or contaminated outdoors",
        "action": "Flatten it and place it in paper/cardboard recycling if it is clean and dry.",
    },
    "cigarette_butt": {
        "material": "cellulose acetate filter material",
        "concern": "leaches toxic residue and is one of the most common litter items",
        "action": "Pick it up with protection and place it in a sealed trash container.",
    },
    "plastic_bag": {
        "material": "thin film plastic",
        "concern": "blows into waterways and can harm wildlife",
        "action": "Bring it to a film-plastic drop-off location if clean, otherwise place it in trash.",
    },
    "food_wrapper": {
        "material": "mixed flexible packaging",
        "concern": "is rarely recyclable and can fragment outdoors",
        "action": "Place it in trash unless the local program explicitly accepts that wrapper.",
    },
    "glass_bottle": {
        "material": "glass",
        "concern": "can break into sharp fragments outdoors",
        "action": "Place it in glass recycling if accepted locally, or secure it safely for disposal.",
    },
    "styrofoam_cup": {
        "material": "expanded polystyrene foam",
        "concern": "breaks into lightweight fragments that are hard to recover",
        "action": "Place it in trash unless a dedicated foam recycling option is available.",
    },
}


def build_fallback_advice(detection: YOLODetection, castnet: CASTNETReading) -> SustainabilityAdvice:
    fact = OBJECT_FACTS.get(
        detection.object_class,
        {
            "material": "unknown material",
            "concern": "may become litter or environmental contamination if left outdoors",
            "action": "Remove it from the area and dispose of it using the nearest appropriate bin.",
        },
    )
    air_context = _air_context(castnet)
    context = (
        f"A {detection.object_class.replace('_', ' ')} was detected. "
        f"It is associated with {fact['material']} and {fact['concern']}; "
        f"nearby CASTNET context shows {air_context}."
    )
    return SustainabilityAdvice(
        object_detected=detection.object_class,
        confidence=detection.confidence,
        context=context,
        action=fact["action"],
    )


def _air_context(castnet: CASTNETReading) -> str:
    if castnet.ozone_ppb >= 70:
        ozone_label = "high ozone"
    elif castnet.ozone_ppb >= 50:
        ozone_label = "moderate ozone"
    else:
        ozone_label = "lower ozone"

    return (
        f"{ozone_label} ({castnet.ozone_ppb:.1f} ppb), "
        f"sulfate {castnet.sulfate_ug_m3:.2f} ug/m3, "
        f"nitrate {castnet.nitrate_ug_m3:.2f} ug/m3"
    )
