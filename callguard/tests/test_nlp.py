import pytest
from app.nlp import normalize, redact, convert_number_words

def test_hinglish_finance_normalization():
    assert "guaranteed" in normalize("Returns pakka hai")
    assert "risk free" in normalize("yeh plan bilkul safe hai aur koi risk nahi")
    assert "act now" in normalize("turant invest karo")
    assert "sign today" in normalize("aaj hi sign karo")
    assert "put everything" in normalize("saara paisa yahan laga do")

def test_hinglish_healthcare_normalization():
    assert "stop taking medication" in normalize("aap dawai mat lo")
    assert "double your dose" in normalize("dose double kar lo")
    assert "lab results" in normalize("test result batao")

def test_hinglish_crisis_and_collections_normalization():
    assert "want to die" in normalize("mera marne ka mann kar raha hai")
    assert "kill myself" in normalize("main atmahatya kar lunga")
    assert "send the police" in normalize("hum police bhejenge tumhare ghar")
    assert "idiot" in normalize("tu bilkul bewakoof hai")
    assert "come to your home" in normalize("kal hum ghar pe aayenge")

def test_number_words_to_digits_doses():
    assert normalize("take metformin eight fifty mg") == "take metformin 850 mg"
    assert normalize("prescribed metformin five hundred mg twice daily") == "prescribed metformin 500 mg twice daily"
    assert normalize("take two hundred fifty milligrams") == "take 250 milligrams"
    assert normalize("dose is one thousand units") == "dose is 1000 units"
    assert normalize("twelve percent returns") == "12 percent returns"
    assert normalize("twenty five mg tablet") == "25 mg tablet"

def test_pii_redaction():
    text = "Call me at +1 415-555-2671 or email compliance@bank.com. SSN 123-45-6789 Aadhaar 1234 5678 9012"
    redacted = redact(text)
    assert "compliance@bank.com" not in redacted
    assert "[EMAIL]" in redacted
    assert "123-45-6789" not in redacted
    assert "[SSN]" in redacted
    assert "1234 5678 9012" not in redacted
    assert "[AADHAAR]" in redacted
