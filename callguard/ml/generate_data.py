"""Generate synthetic labelled dataset for CallGuard risk prefilter.
Produces at least 600 lines across all 5 packs (finance, healthcare, insurance,
collections, crisis), including Hinglish and conversational paraphrases.
Uses combinatorial templates, with optional Claude API expansion if ANTHROPIC_API_KEY is set.
"""
import csv
import itertools
import os
import pathlib
import random

DATA_DIR = pathlib.Path(__file__).parent / "data"
OUTPUT_PATH = DATA_DIR / "seed_lines.csv"

# Structured seed templates and paraphrases across all 5 regulated domains
FINANCE_RISKY = [
    # Guarantees and return promises
    "This mutual fund is completely risk-free, you will not lose anything",
    "You are guaranteed to earn twenty percent profit on this investment",
    "This scheme is a sure thing, zero chance of losing your capital",
    "I personally guarantee that your money will double in six months",
    "There is no risk whatsoever in this equity derivative portfolio",
    "Returns are 100 percent assured by our top tier wealth desk",
    "You will definitely make twelve percent every single year",
    "Nobody has ever lost a single dollar in this fund, it cannot lose",
    "Your principal is totally protected, absolutely safe from market drops",
    "We have guaranteed fixed payouts that the market cannot touch",
    "Trust me, this is an infallible financial instrument",
    "You can't lose with this one, it is practically free money",
    # High pressure selling
    "You need to act now, this offer expires in ten minutes",
    "Sign today or you will miss the chance of a lifetime",
    "Today only, tomorrow this price doubles so commit immediately",
    "Do not delay, everyone is buying this asset right now",
    "This is your last chance to get in before the market opens tomorrow",
    "If you do not transfer funds right now the allocation is gone forever",
    "Hurry up, I only have two slots left in this exclusive pre-IPO round",
    "Sign the agreement immediately without thinking twice",
    # Concentration and unsuitable advice
    "Put your entire life savings into this single high-yield bond",
    "Liquidate all your other assets and put everything into this token",
    "Do not diversify, put all your money into this one tech stock",
    "Take out a second mortgage and invest all the proceeds here",
    "Move your entire pension into this speculative emerging market fund",
    # Hinglish & Hindi transliterated violations
    "Returns pakka hai sir, bilkul koi risk nahi hai",
    "Yeh fund bilkul safe hai, 100 percent pakka profit milega",
    "Aap saara paisa isme laga do, paise double ho jayenge",
    "Turant invest karo, aaj hi sign karo bas aaj ke liye offer hai",
    "Bina padhe sign kar do koi tension nahi hai pakka guarantee",
    "Aapki poori savings isme daal do koi khatra nahi",
]

FINANCE_COMPLIANT = [
    # Disclosures & identity
    "Can you please verify your date of birth and full legal name?",
    "This call is recorded for compliance, quality, and regulatory purposes",
    "All mutual fund investments are subject to market risks, please read carefully",
    "You may lose capital as market prices fluctuate over your investment horizon",
    "Past performance is not an indicator of future returns or yields",
    "What is your current risk appetite, investment horizon, and liquidity goal?",
    "Please take your time to review the offer documents and prospectus",
    "I recommend consulting your tax advisor before finalizing this allocation",
    "Let me send over the key investor information document for your review",
    "Can you confirm the last four digits of your registered account number?",
    "We ensure your portfolio is well diversified across uncorrelated asset classes",
    "Are you comfortable with the potential downside volatility of equity markets?",
    "There is a statutory cooling-off period where you may withdraw without penalty",
    "Thank you for calling wealth management, how may I assist you today?",
    "Please verify your residential address for KYC compliance",
    "We cannot guarantee future yields because asset values fluctuate daily",
    # Hinglish compliant
    "Yeh call training aur compliance ke liye record ho rahi hai",
    "Market me utar chadhav hota hai, risk disclosure zaroor padhein",
    "Aapka risk appetite kaisa hai, moderate ya aggressive?",
    "Aap aaram se documents padh lijiye, koi jaldi nahi hai",
]

HEALTHCARE_RISKY = [
    # Premature PHI before ID verification
    "Hello, I am calling with your positive biopsy test results",
    "Your blood tests confirm a positive diagnosis for HIV",
    "Calling regarding your chemotherapy schedule and oncology lab report",
    "Your MRI scan shows acute spinal disc herniation",
    "I have the pathology report for your malignant melanoma here",
    "We need to discuss your recent psychiatric evaluation results",
    # Dose mismatch & improper medical instructions
    "I am prescribing metformin eight fifty mg twice daily",
    "Take metformin 850 milligrams twice daily starting today",
    "Take metformin eight hundred fifty mg with your breakfast and dinner",
    "You should double your dose if you still feel fatigued",
    "Stop taking all your medication immediately without seeing the doctor",
    "You do not need insulin anymore, just stop taking it",
    "Triple the antibiotic dose so your infection clears up faster",
    "Go ahead and take twelve tablets instead of the prescribed amount",
    # Third party PHI disclosure
    "Let me tell his wife about the terminal diagnosis right away",
    "I will inform her employer that she tested positive for hepatitis",
    "Your neighbor called so I shared your prescription details with them",
    "I told your coworker about your scheduled inpatient surgery",
    # Hinglish & Hindi transliterations
    "Aapki lab result aa gayi hai, cancer positive nikla hai",
    "Aap dawai mat lo, kal se saari dawa band kar do",
    "Metformin eight fifty mg le lo din me do baar",
    "Dose double kar lo jaldi theek ho jaoge",
    "Unki biwi ko bata do ki unko HIV hai",
    "Test result bata raha hoon aap sun lijiye",
]

HEALTHCARE_COMPLIANT = [
    # Identity verification & consent
    "Before we discuss health details, please verify your full name and date of birth",
    "For your privacy, can you confirm the first line of your street address?",
    "Do I have your explicit consent to discuss your medical records on this line?",
    "Let me verify that I am speaking directly with the patient or authorized proxy",
    # Dose match & read-back
    "I am prescribing metformin 500 mg twice daily with meals",
    "The prescribed dose is metformin five hundred milligrams twice a day",
    "Let me read back the prescription: metformin 500 mg, take twice daily",
    "To confirm the prescription, that is metformin 500 mg orally every twelve hours",
    # Follow up & warning signs
    "Please come back to the clinic or call emergency if you experience shortness of breath",
    "Seek immediate medical attention if you notice any severe allergic reaction or rash",
    "Take this medication with a full glass of water after food",
    "We will schedule your follow-up lab appointment in four weeks",
    # Hinglish compliant
    "Kripya pehle apna poora naam aur janam tithi verify kijiye",
    "Metformin 500 mg din me do baar khane ke baad leni hai",
    "Kya mujhe aapse health information discuss karne ki anumati hai?",
    "Agar chakkar aaye toh turant clinic aaiye ya doctor ko call kijiye",
]

INSURANCE_RISKY = [
    # Misleading claims and coverage
    "This health policy covers everything with zero exclusions whatsoever",
    "All pre-existing diseases and chronic illnesses are covered from day one",
    "There are no waiting periods or exclusions in this comprehensive plan",
    "Any medical bill you submit will be paid out 100 percent in full",
    "Every surgery, treatment, and hospital admission is unconditionally covered",
    "This policy has no sub-limits, no co-pay, and covers literally every disease",
    # High pressure on vulnerable customers
    "Sign today before you ask your daughter or son about it",
    "There is no need to read the policy wording or terms, just sign here",
    "Do not bother reading the fine print, trust my verbal guarantee",
    "Sign right now before the underwriters increase your premium rates",
    "You do not need to consult your family, take this policy right now",
    # False claim settlement claims
    "Our company pays out claims within one single hour without inspection",
    "Claims are always approved instantly with no questions asked",
    "We have a 100 percent claim settlement ratio, every single claim gets paid",
    # Hinglish & Hindi transliterated violations
    "Is policy me sab kuch cover hai, koi exclusion nahi hai",
    "Sab bimari cover hai pehle din se, koi waiting period nahi",
    "Aap apne bachon se mat puchiye, aaj hi sign kar dijiye",
    "Turant claim pass hota hai, ek din me paisa account me aa jayega",
    "Fine print padhne ki koi zaroorat nahi hai, bilkul tension mat lo",
]

INSURANCE_COMPLIANT = [
    # Identity & disclosures
    "This call is being recorded for documentation and quality assurance",
    "Can you please confirm your date of birth and full legal name?",
    "This health policy includes a standard 30-day initial waiting period",
    "Pre-existing conditions have a mandatory 24-month waiting period before coverage",
    "Please note that cosmetic procedures and elective treatments are excluded",
    "There is a 30-day free-look period during which you can cancel for a full refund",
    "I encourage you to discuss this policy schedule with your family members",
    "Let me explain the room rent sub-limits and the ten percent co-pay clause",
    "Claim settlement is subject to verification of hospital documentation and bills",
    "Please read the key policy exclusions listed on page four of the brochure",
    # Hinglish compliant
    "Yeh call compliance aur verification ke liye record ki ja rahi hai",
    "Pre-existing diseases ke liye do saal ka waiting period hota hai",
    "Policy me free-look period hai, agar pasand na aaye toh cancel kar sakte hain",
    "Brochure me saare exclusions aur terms clearly likhe hain, review kar lijiye",
]

COLLECTIONS_RISKY = [
    # Harassment, threats of physical visit & arrest
    "Pay now or we will send the police to arrest you at your house",
    "We are sending five bailiffs to your home tonight to seize your furniture",
    "We will come to your workplace and make sure everyone knows you are delinquent",
    "Pay immediately or you will spend five years behind bars in jail",
    "We will notify your employer and get you fired from your job tomorrow",
    "I will personally visit your home and tell all your neighbors about your debt",
    "We will ruin your credit score forever and destroy your family reputation",
    # Abusive and derogatory language
    "You are a lazy deadbeat and an absolute liar",
    "You are a worthless fraud who steals money from banks",
    "You stupid idiot, why did you borrow money if you cannot repay it?",
    "You have no shame or dignity, repay what you owe right now",
    # Coercive ultimatums
    "Pay right now this instant or this is your very last warning",
    "Either pay five thousand dollars today or face immediate criminal charges",
    "If money is not wired in one hour we are filing a police complaint",
    # Hinglish & Hindi transliterated violations
    "Agar abhi pay nahi kiya toh hum police bhejenge tumhare ghar",
    "Kal subah humare bande tumhare ghar pe aayenge",
    "Tumhare boss ko batayenge ki tum kitne bade chor aur fraud ho",
    "Tu bilkul nalayak aur bewakoof hai, jail karwayenge tujhe",
    "Paise abhi do varna tumhara jeena haram kar denge",
]

COLLECTIONS_COMPLIANT = [
    # Mini-Miranda & identity
    "This is an attempt to collect a debt and any information obtained will be used for that purpose",
    "Am I speaking with the account holder? Please confirm the last four digits of your SSN",
    "You have the right to request debt validation in writing within thirty days",
    "If you dispute the validity of this balance, you may notify us in writing",
    "I understand unexpected financial hardship occurs, let us explore options",
    "We can set up a structured monthly payment plan that fits your current budget",
    "Would a deferred settlement plan with reduced installments assist you?",
    "We are available during regular business hours from 8 AM to 7 PM to discuss your account",
    "I will document your update and send the settlement agreement by postal mail",
    "You may provide written notice if you prefer communication via authorized counsel",
    # Hinglish compliant
    "Yeh call ek debt collect karne ke sambandh me hai",
    "Aapke paas written dispute karne ka poora adhikar hai",
    "Kya hum ek aasaan installment plan bana sakte hain aapke budget ke anusar?",
    "Aap chahein toh validation notice ke documents check kar sakte hain",
]

CRISIS_RISKY = [
    # Caller suicide cues (need urgent escalation)
    "I want to kill myself, there is no reason to live anymore",
    "I just want to end it all tonight, everyone is better off without me",
    "I have gathered all my pills and I am ready to take an overdose",
    "Nobody cares about me and I cannot bear this suffering any longer",
    "I am standing on the edge of the bridge, I am going to jump",
    "I don't want to wake up tomorrow, life has no meaning anymore",
    "I have written my goodbye letters to my parents, this is the end",
    # Domestic violence disclosures
    "He hits me violently whenever he drinks and I am terrified to go home",
    "My partner locked me in the room and threatened me with a knife",
    "She is hurting me and threatening to take the children away",
    "I am bleeding and hiding in the bathroom because he is breaking the door",
    # Dismissive counselor responses (violations by counselor)
    "Calm down, you are totally overreacting over nothing",
    "It is really not that bad, lots of people have it worse than you",
    "Stop crying and snap out of it, just cheer up and get over it",
    "You are being overly dramatic, you will be fine tomorrow",
    # Hinglish & Hindi transliterated violations
    "Mera marne ka mann kar raha hai, main khud ko khatam karna chahta hoon",
    "Ab jeene ka koi fayda nahi bacha, main atmahatya karne ja raha hoon",
    "Woh mujhe maarta hai aur main ghar jane se bohot darta hoon",
    "Shaant ho jao kuch nahi hua, faaltu me drama mat karo",
    "Mujhe maar peet ka saamna karna pad raha hai apne pati se",
]

CRISIS_COMPLIANT = [
    # Safety, location & protocol
    "You are through to the confidential crisis helpline, where are you located right now?",
    "Are you in a safe and private place where you can speak freely?",
    "What is your address or landmark in case we get disconnected or need help?",
    "Can you share a callback phone number where I can reach you if the call drops?",
    "Do you have a plan or means to hurt yourself right now?",
    "That sounds extraordinarily painful and overwhelming, but I am right here with you",
    "Thank you for reaching out today, you are not alone and we will walk through this together",
    "Can you step into a secure room while we contact local emergency services?",
    "Would you like me to stay on the line with you until help arrives?",
    "Take a slow deep breath with me, let us take this one step at a time",
    # Hinglish compliant
    "Aap crisis helpline se baat kar rahe hain, aap abhi kahan par hain?",
    "Kya aap abhi surakshit jagah par hain jahan baat kar sakte hain?",
    "Yeh bohot mushkil waqt hai lekin main aapke saath hoon, hum isse suljhayenge",
    "Apna callback number batayein taaki call cut hone par main phone kar sakoon",
]

PACK_DATA = {
    "finance": (FINANCE_RISKY, FINANCE_COMPLIANT),
    "healthcare": (HEALTHCARE_RISKY, HEALTHCARE_COMPLIANT),
    "insurance": (INSURANCE_RISKY, INSURANCE_COMPLIANT),
    "collections": (COLLECTIONS_RISKY, COLLECTIONS_COMPLIANT),
    "crisis": (CRISIS_RISKY, CRISIS_COMPLIANT),
}

PARAPHRASE_PREFIXES = [
    "",
    "Honestly, ",
    "To be frank, ",
    "As I mentioned earlier, ",
    "Listen to me carefully, ",
    "I want to make sure you know that ",
    "Let me be very clear: ",
    "In my opinion, ",
    "I am telling you, ",
]

PARAPHRASE_SUFFIXES = [
    "",
    ", believe me.",
    ", understand?",
    ", right now.",
    ", absolutely.",
    " without any doubt.",
    ", take my word for it.",
    " without delay.",
]


def expand_templates(base_lines: list[str], target_count: int = 70) -> list[str]:
    """Expand base lines using prefix/suffix variations and word mutations."""
    results = set(base_lines)
    for line in base_lines:
        for p in PARAPHRASE_PREFIXES:
            for s in PARAPHRASE_SUFFIXES:
                mod = f"{p}{line[0].lower() + line[1:] if p else line}{s}".strip()
                results.add(mod)
                if len(results) >= target_count:
                    break
            if len(results) >= target_count:
                break
        if len(results) >= target_count:
            break
    res_list = list(results)
    random.shuffle(res_list)
    return res_list[:target_count]


def generate_dataset(min_per_category: int = 70) -> list[dict]:
    """Generate balanced dataset across all 5 packs with >= 600 total lines."""
    all_rows = []
    random.seed(42)

    for pack_name, (risky_seeds, safe_seeds) in PACK_DATA.items():
        risky_lines = expand_templates(risky_seeds, target_count=min_per_category)
        safe_lines = expand_templates(safe_seeds, target_count=min_per_category)

        for line in risky_lines:
            all_rows.append({"text": line, "label": 1, "pack": pack_name})
        for line in safe_lines:
            all_rows.append({"text": line, "label": 0, "pack": pack_name})

    # Optional Claude API expansion if ANTHROPIC_API_KEY is available
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        print("[generate_data] ANTHROPIC_API_KEY detected. Augmenting with Claude API...")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = (
                "Generate 20 subtle conversational lines for voice compliance monitoring across "
                "finance, healthcare, insurance, collections, crisis lines. Format each line as: "
                "LABEL|PACK|TEXT where LABEL is 1 (risky) or 0 (safe)."
            )
            resp = client.messages.create(
                model=os.getenv("CALLGUARD_MODEL", "claude-haiku-5-5"),
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            for item in resp.content[0].text.split("\n"):
                parts = item.strip().split("|")
                if len(parts) == 3 and parts[0] in ("0", "1"):
                    lbl = int(parts[0])
                    pck = parts[1].strip().lower()
                    txt = parts[2].strip()
                    if pck in PACK_DATA and len(txt) > 5:
                        all_rows.append({"text": txt, "label": lbl, "pack": pck})
        except Exception as e:
            print(f"[generate_data] Claude augmentation skipped: {e}")

    random.shuffle(all_rows)
    return all_rows


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = generate_dataset(min_per_category=75)  # 75 * 2 * 5 = 750 lines
    
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "pack"])
        writer.writeheader()
        writer.writerows(rows)

    risky_cnt = sum(1 for r in rows if r["label"] == 1)
    safe_cnt = sum(1 for r in rows if r["label"] == 0)
    print(f"Generated {len(rows)} synthetic lines -> {OUTPUT_PATH}")
    print(f"Risky (label 1): {risky_cnt}, Safe (label 0): {safe_cnt}")
    for p in PACK_DATA:
        cnt = sum(1 for r in rows if r["pack"] == p)
        print(f"  Pack '{p}': {cnt} lines")


if __name__ == "__main__":
    main()
