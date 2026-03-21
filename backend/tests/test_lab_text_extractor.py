from services.lab_text_extractor import extract_lab_values_from_text


def test_extracts_common_aliases_and_abbreviations():
    text = """
    Hemoglobină: 15,2 g/dL
    Ferritina serica 45 ng/mL
    25(OH)D: 28,4 ng/mL
    Cianocobalamina: 312 pg/mL
    """

    extracted = extract_lab_values_from_text(text)

    assert extracted["hemoglobin"] == 15.2
    assert extracted["ferritin"] == 45.0
    assert extracted["vitamin_d"] == 28.4
    assert extracted["vitamin_b12"] == 312.0


def test_extracts_vitamin_k_and_potassium_aliases():
    text = """
    Vit. K: 1,1
    Potassium: 4,2 mmol/L
    """

    extracted = extract_lab_values_from_text(text)

    assert extracted["vitamin_k"] == 1.1
    assert extracted["potassium"] == 4.2


def test_hemoglobin_does_not_pick_hematii_value():
    text = """
    Hematii 4.890.000 /mm3 (3.900.000 - 5.200.000)
    Hemoglobină 15,2 g/dL (12,0 - 15,6)
    """

    extracted = extract_lab_values_from_text(text)

    assert extracted["hemoglobin"] == 15.2
