import pytest
from app.engine import CallSession

pytestmark = pytest.mark.asyncio


async def run(pack, lines):
    s = CallSession(pack)
    for sp, t in lines:
        await s.ingest(sp, t)
    return s


async def test_finance_guarantee_flagged():
    s = await run("finance", [("Advisor", "This fund is risk-free, you will definitely make 12 percent")])
    assert s.flags and s.flags[0].severity == "high"


async def test_finance_hinglish_guarantee():
    s = await run("finance", [("Advisor", "Returns pakka hai, koi risk nahi")])
    assert any(f.source == "rule" for f in s.flags)


async def test_finance_checklist_ticks():
    s = await run("finance", [("Advisor", "This call is recorded. Please verify your date of birth."),
                              ("Advisor", "There is market risk and you may lose capital.")])
    assert {"id", "risk", "rec"} <= set(s.done)
    assert s.score == 0


async def test_speaker_scoping():
    s = await run("finance", [("Client", "Is it risk free?")])
    assert not s.flags  # only the advisor is policed


async def test_healthcare_phi_before_id():
    s = await run("healthcare", [("Nurse", "I am calling about your lab results")])
    assert any("identity" in f.issue for f in s.flags)


async def test_healthcare_phi_ok_after_id():
    s = await run("healthcare", [("Nurse", "Please verify your date of birth"),
                                 ("Nurse", "Thanks, your lab results are ready")])
    assert not s.flags


async def test_dose_mismatch():
    s = await run("healthcare", [("Doctor", "I am prescribing metformin 850 mg twice daily")])
    assert any(f.source == "dose_check" for f in s.flags)


async def test_dose_match_ok():
    s = await run("healthcare", [("Doctor", "Metformin 500 mg twice daily")])
    assert not any(f.source == "dose_check" for f in s.flags)


async def test_crisis_escalation_and_verdict():
    s = await run("crisis", [("Caller", "I want to end it all"), ("Counselor", "Calm down, it is not that bad")])
    assert s.report()["verdict"] == "ESCALATE"


async def test_pii_redacted_in_transcript():
    s = await run("finance", [("Client", "My email is a.b@example.com and phone 9876543210")])
    t = s.lines[0]["text"]
    assert "example.com" not in t and "9876543210" not in t


async def test_insurance_overclaim_and_checklist():
    s = await run("insurance", [
        ("Agent", "This call is recorded. Can you confirm your name?"),
        ("Customer", "John Doe."),
        ("Agent", "This plan covers everything, no exclusions whatsoever."),
    ])
    assert {"id", "rec"} <= set(s.done)
    assert any(f.severity == "high" and "coverage" in f.issue.lower() for f in s.flags)


async def test_collections_threats_and_hinglish():
    s = await run("collections", [
        ("Agent", "This is an attempt to collect a debt and info will be used for that."),
        ("Agent", "Pay now or hum police bhejenge aur kal hum ghar pe aayenge!"),
    ])
    assert "mm" in s.done
    assert any("threat" in f.issue.lower() for f in s.flags)


async def test_crisis_dv_disclosure():
    s = await run("crisis", [
        ("Caller", "Please help, he hits me and I am afraid to go home."),
    ])
    assert any("domestic violence" in f.issue.lower() for f in s.flags)
    assert s.report()["verdict"] == "ESCALATE"


async def test_finance_offchannel_detection():
    s = await run("finance", [
        ("Advisor", "Let us take this to WhatsApp, text my personal cell and delete this chat."),
    ])
    assert any("off-channel" in f.issue.lower() and f.severity == "high" for f in s.flags)


async def test_finance_market_manipulation_detection():
    s = await run("finance", [
        ("Advisor", "Let us flash a fake order to spoof the market and pump and dump before the print."),
    ])
    assert any("manipulation" in f.issue.lower() and f.severity == "high" for f in s.flags)


