"""Phasewell (tenant 26) counterparty regex rules, kept separate from the generic parser and the bank rules.

Phasewell's bank feeds are free text and come from six banks, taken from the end of the account name:
JPMC, BofA, TD, SS (South State), Banco (Puerto Rico) and FB (First Bank). Each rule in CPTY_RULES reads one bank's narrative layout:
the first rule that matches wins, and for a "party" or "payroll" rule the first regex group is the counterparty name. The raw name
is cleaned (reference numbers and descriptor words removed) and mapped to one standard spelling with ALIASES.

Rule kinds: party and payroll give a name. internal, fee, interest, return, check, deposit and unknown are recognised but have no
outside counterparty, so no name is returned for them.

Use it through BankNarrativeParser.get_counterparties(..., tenant="phasewell", bank=<account name or bank code>). The rules are
the same ones as analytics/classification/pswl_counterparty.py in the data-analytics project (CPTY_RULES, ALIASES, clean).
"""
import re
from typing import Optional, Tuple

BANKS = ["JPMC", "BofA", "TD", "SS", "Banco", "FB"]
FREE_TEXT_BANKS = ["TD", "SS", "FB", "Banco"]


def account_bank(account_name):
    name = str(account_name).upper()
    if name.endswith("SOUTH STATE"):
        return "SS"
    for bank in BANKS:
        if name.endswith(bank.upper()):
            return bank
    return None


# (id, banks, direction, kind, regex, note). banks / direction None means any.
# For party and payroll the first group of the regex is the name.
CPTY_RULES = [
    # not an outside party
    ("X01", None, None, "internal", r"^CASH CONCENTRATION TRANSFER (CREDIT|DEBIT)\b", "JPMC cash concentration"),
    ("X02", None, None, "internal", r"^ONLINE (XFER )?TRANSFER (FROM|TO) (CHK|CK)\b|^(DEPOSIT |WITHDRAWAL )?TRANSFER (FROM|TO) CHECKING X\d{4}\b",
     "online transfer to own account (TD: between the CMR accounts)"),
    ("X03", None, None, "internal", r"^(\d+\s+)?(ACCOUNT )?TRANSFER (FROM|TO) (BUS(INESS)?|ICS|SMALL BUS|MONEY MARKET)\b", "South State sweeps"),
    ("X04", None, None, "internal", r"^\d+ ACCOUNT TRANSFER (FROM|TO)\b", "South State numbered transfers"),
    # JPMC book transfer from a foreign bank: the payer follows the ordering account (ORG:/<account> <name>). Before X05.
    ("W04", None, "credit", "party", r"^BOOK TRANSFER CREDIT\b.*?\bORG:/\S+\s+(?:\d/)?(.+?)(?=\s+(?:OGB:|REF:|TRN:|ROUTING:)|$)",
     "incoming book transfer, name after ORG:/<account>"),
    ("X05", None, None, "internal", r"^(ACCOUNT TRANSFER|BOOK TRANSFER|INTERNET FUND TRANSFER) (TO|FROM|CREDIT|DEBIT)\b", "First Bank transfers"),
    ("X06", None, None, "internal", r"^SCHWAB BROKERAGE\s*MONEYLINK\b", "sweep to brokerage"),
    ("X07", ["BofA"], "debit", "internal", r"^WIRE TYPE:WIRE OUT\b.*\bBNF:\s*(GABRAIL|SARGON|SCP|CHASE MEDICAL|RENSTAR)", "wire out to an affiliate"),
    ("X12", None, None, "fee", r"^INCOMING WIRE TRANSFER FEE\b|^SERVICE CHARGES FOR THE MONTH\b|^ANALYSIS CHARGES\b",
     "booked as Other Expenses, not Bank Fees (South State 'Analysis Charges <month> <year>' too)"),
    ("X16", ["SS"], None, "fee", r"^SERVICE CHARGE\b", "South State books its service charge as Other Expenses"),
    ("X08", None, None, "fee", r"\bACCT ANALYSIS FEE\b|\bACCOUNT ANALYSIS (SETTLEMENT )?CHARGE\b|^SERVICE CHARGE\b|^TREASURY MGMT SVCS\b"
                               r"|^OVERDRAFT (FEE|PD)\b|^OD GRACE FEE REFUND\b|^MISCELLANEOUS FEES?\b|^ANALYSIS (SERVICE )?CHARGE\b"
                               r"|^\*?CARGO (POR|IVU)\b|^BANK SERVICE FEE\b|^COMM SVC FEE\b|^WIRE TRANSFER FEE\b|^DEP RETURN FEE\b"
                               r"|^STOP I ?TEM\b", "bank fees"),
    ("X13", None, "credit", "interest", r"^INTEREST( PAID| EARNED| CREDIT| POSTING FOR DDA\b.*)?\s*$", "interest from the bank, no party"),
    ("X14", None, None, "return", r"^DEP RETURN CHARGEBACK\b|^RETURN SETTLE RETURN\b", "returned item, the bank text has no party"),
    ("X09", None, None, "check", r"^(CHECK( PAID)?\b|CHEQUE\b|CHK\b|REVERSAL OF CHECK\b)", "only a check number"),
    ("X10", None, "credit", "deposit", r"^(REMOTE ONLINE |MOBILE |OTHER |ELECTRONIC )?DEPOSITO?\b\s*(#?\s*\d+)?\s*$"
                                       r"|^OTHER DEPOSITS\b|^SBB MDEPOSIT\b|^CREDIT \(ANY TYPE\)|^BKOFAMERICA MOBILE\b.*\bDEPOSIT\b"
                                       r"|^(AJUSTE DE )?DEPOSITO\s*,\s*CUST REF\.", "deposit with no payer (Banco: DEPOSITO / AJUSTE DE DEPOSITO)"),
    ("X11", None, None, "unknown", r"^(ACH (CREDIT|DEBIT) RECEIVED|ELECTRONIC DEBIT|REAL TIME PAYMENT CREDIT|INDIVIDUAL BACK VALUE DEBIT"
                                   r"|MISCELLANEOUS DEBIT|DEBIT|ONLINE BUSINESS SUITE (DIRECT PMT SERVICES|NEXT DAY PAYMENT))\s*$"
                                   r"|^\d+\s*-\s*(INCOMING|OUTGOING) WIRE\s*,", "bank text only (Banco wires carry only a reference)"),

    # payroll funding from our own entities: "<employee no.> <ENTITY> DIR DEP / TRUST / BILLING"
    ("Y01", None, None, "payroll", r"^\d{5,7}\s+([A-Z][A-Z ]+?)\s+(DES:)?(DIR DEP|TRUST|BILLING)\b", "employee no. + entity"),
    ("Y02", None, None, "payroll", r"^ORIG CO NAME:\d{5,7}\s+(.+?)\s+ORIG ID:.*?CO ENTRY DESCR:(DIR DEP|TRUST|BILLING|FIX|REV DIRDE)", "same, as an ACH"),

    # wires, any bank
    ("W01", None, "credit", "party", r"^(?:FEDWIRE|CHIPS) CREDIT\b.*?\bB/O:\s*(?:1\s+|1/)?(.+?)(?=\s+\d{4,}|\s+[A-Z]/|\s+REF:|\s+\d/|$)", "incoming wire, name after B/O:"),
    ("W02", None, "debit", "party", r"^(?:ONLINE )?(?:DOMESTIC|INTERNATIONAL) WIRE TRANSFER\b.*?\bA/C:\s*(.+?)(?=\s+(?:REF:|\d{4,}|[A-Z]{2}\s+\d{5})|$)", "outgoing wire, name after A/C:"),
    ("W03", None, "debit", "party", r"^WIRE TRANSFER OUTGOING\s+(.+)$", "outgoing wire"),

    # JPMC
    ("J01", ["JPMC"], "debit", "party", r"CO ENTRY DESCR:BILL_PAY\b.*?\bIND ID:(.+?)\s+IND NAME:", "Intuit Bill Pay: the payee is in IND ID"),
    ("J05", ["JPMC"], None, "party", r"^ORIG CO NAME:(.+?)\s+ORIG ID:", "ACH originator, cut at 16 characters"),
    ("J06", ["JPMC"], "debit", "party", r"^ONLINE ACH PAYMENT (?:\d+ )?TO\s+(.+?)\s*(?:\(|$)", "online ACH payment"),
    ("J07", ["JPMC"], "debit", "party", r"^ONLINE (?:REALTIME VENDOR )?PAYMENT\b.*?\bTO\s+(.+?)(?:\s+\d[\d/]*)?$", "online / real-time vendor payment"),

    # BofA
    ("B01", ["BofA"], "debit", "party", r"^WIRE TYPE:WIRE OUT\b.*?\bBNF:\s*(.+?)(?=\s+(ID|BNF BK|OBI|BBI|PMT DET)\b|\s*$)", "outgoing wire"),
    ("B03", ["BofA"], "credit", "party", r"^WIRE TYPE:WIRE IN\b.*?\bORIG:\s*(.+?)(?=\s+(?:ID|ORIG BK|OBI|BNF|SND BK)\b|\s*$)", "incoming wire"),
    ("B04", ["BofA"], "debit", "party", r"^TRANSFER [^:]+:(.+?)\s+CONFIRMATION#", "online transfer to a payee: the name follows the colon"),
    ("B02", ["BofA"], None, "party", r"^(.+?)\s+DES:", "name before DES:, cut at 16 characters"),

    # TD
    ("T01", ["TD"], None, "party", r"^ACH BA TCH (.+)$", "TD writes ACH BATCH with a stray space"),
    ("T02", ["TD"], None, "party", r"^ACH CH ARGE\s*(.*)$", "same for ACH CHARGE"),
    ("T03", ["TD"], "credit", "party", r"^DEPOSIT\s+(.+)$", "deposit with a payer name"),
    ("T05", ["TD"], None, "party", r"^(.+?)\s+(EDI PYMNTS?|PAYMENTS?|PAYABLES|PUSH|WEB PMTS?|DEBITS?|DIRDEB|CORP PAY|TAX COL"
                                   r"|EPAYMENT ACH PMT|ACH PMT|ACH DEBIT|INVOICE|TPS TAXES|EIB INVOICE|ONLINE PMT)\b", "name, then the descriptor word"),

    # South State
    ("S01", ["SS"], "credit", "party", r"^INCOMING WIRE TRANSFER\s+(.+?)\s+\d{5,}\s*$", "incoming wire"),
    ("S02", ["SS"], "credit", "party", r"^(?:EDI PYMNTS|\d{6,})\s+(.+?)\s+RMR\*", "EDI remittance"),
    ("S03", ["SS"], "credit", "party", r"^PAYMENTS?\s+(.+?)\s+(?:PID:|NTE\*|RMR\*)", "descriptor first, then the payer"),
    ("S05", ["SS"], "debit", "party", r"^((?:EWALLET - DIVVYP?|DIVVY CRED)\b.*)$", "Divvy card"),
    ("S04", ["SS"], None, "party", r"^(.+?)\s+(EDI PYMNTS?|PAYMENTS?|PAYABLES|PUSH|WEB PMTS?|DEBITS?|DEBCARDTX|UTILITYBIL|UTILITY"
                                   r"|PYMNT|DIRDEB|CORP PAY|TAX COL)\b", "name, then the descriptor word"),

    # Banco (Puerto Rico)
    ("P01", ["Banco"], None, "party", r"^(.+?)\s*,\s*CUST REF\.", "text before ', CUST Ref.'"),

    # First Bank
    ("F01", ["FB"], "debit", "party", r"^ELECTRONIC DEBIT\s+(.+?)(?=\s+(WEB PAY|PURCHASE|PMT|PAYMENT|ACH)\b|\s+\d{4,}|$)", "electronic debit"),
    ("F02", ["FB"], "credit", "party", r"^ELECTRONIC DEPOSIT\s+(.+?)(?=\s+(PAYMENT|PMT|OTR|EDI|\d{4,})|$)", "electronic deposit"),
    ("F03", ["FB"], None, "party", r"^((?:HSA BANK|INTUIT PAYROLL|IRS USATAXPYMT|PREMIER RESEARCH|DRUGDEV|NEUROCRINE).*)$", "narrative starts with the name"),

    # last resorts for the free-text banks
    ("G00", FREE_TEXT_BANKS, "debit", "party", r"\bBILL_PAY\s+(.+)$", "Intuit Bill Pay outside JPMC: the payee follows BILL_PAY"),
    ("G01", FREE_TEXT_BANKS, None, "party", r"^(.+?)\s+#?\d{4,}.*$", "name followed by a reference number"),
    ("G02", FREE_TEXT_BANKS, None, "party", r"^([A-Z][A-Z0-9&.,'#* \-]{5,40})$", "the whole narrative is a name"),
]
CPTY_RULES_RE = [(rid, banks, direction, kind, re.compile(rx, re.I)) for rid, banks, direction, kind, rx, _ in CPTY_RULES]

# words that can be left on the end of a captured name
NOISE_AT_END = re.compile(
    r"\s*(-SETT-.*|\bSEC:\w+|\bCCD\b|\bPPD\b|\bCTX\b|\bWEB\b|\bTAX COL\b|\bTAX\b|\bDIR DEP\b|\bTRUST\b|\bPAYMENTS?\b|\bPAYABLES\b"
    r"|\bEDI PYMNTS?\b|\bPUSH\b|\bDEBITS?\b|\bPMTS?\b|\bPYMNT\b|\bRMR\*.*|\bINV(OICES?)?\b.*|\bINV#?\d.*|\bPOP SCVE\b.*|\bBILL\.COM\b.*|[#*]\s*\d.*|\s\d{4,}.*"
    r"|\bWEB PAGE\b|\bDD\s+\d+/\d+.*|\bACH\d+\S*|\bX{3,}\d+"
    r"|\b(ECHECKPAY|MSINVOICE|ACHPAYMENT|ACHPMT|INS ?PMT ?CL|INSRFDCL|AUTOPAYBUS|EPAY|BILL ?PAY|SALE|FACTURAS|SIGONFILE)\b"
    r"|\bDIRECT DEB(IT)?\b|\bONLINE FEE\b.*|\bCORP PAY\b.*|\bCOBROS?\b.*"
    r"|\s[A-Z]{1,4}\d{4,}\S*"           # a reference token, letters then digits: GA10372-100
    r"|\s(?=\S*\d\S*[A-Z])\S{3,}"       # a reference token with letters after a digit: 7YMN3QW, G8MF, I05O
    r"|(?<=[A-Z])\d{3,})$",             # digits stuck to the name: CtiClinTria5534, Premier Research37981
    re.I)
# wire text runs on into the address, so keep only up to the legal suffix
UP_TO_LEGAL_SUFFIX = re.compile(r"^(.*?\b(LLC|INC|LTD|LIMITED|GMBH|CORP|LP|CO)\b\.?(?=[\s,]|$)|.*)", re.I)
# a legal suffix at the end, whole or cut short by the 15/16-character limit ("Blue Margin, In", "Health Think Ll"),
# dropped so 'Oxeon', 'Oxeon Llc' and 'Trialist Inc.' / 'Trialist Inc' are one name
LEGAL_AT_END = re.compile(r",?\s+(INC|LLC|LLP|LTD|CORP|GMBH|PLLC|IN|LL|LT|PL|L)\.?$", re.I)
# a JPMC ACH originator (J05) that is a processor code, not a name: FMDKL (one word, no vowels)
CODE_LIKE = re.compile(r"[B-DF-HJ-NP-TV-XZ]{4,16}", re.I)


def without_repeat(s):
    """'CITRIN COOPERMAN CITRIN COO' -> 'CITRIN COOPERMAN': the bank repeats the name, cut short, after itself.
    The repeat must start with the whole first word, so 'JOHNSON JOHNSO' (Johnson & Johnson, cut at 16) is left alone."""
    words = s.split()
    for i in range(1, len(words)):
        head, tail = " ".join(words[:i]), " ".join(words[i:])
        if len(tail) >= 4 and words[i].upper() == words[0].upper() and head.upper().startswith(tail.upper()):
            return head
    return s


def split_camel(s):
    """J06 drops the spaces: 'KevinOffel' -> 'Kevin Offel', 'SCPClinicalResearch' -> 'SCP Clinical Research'."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", s)


def clean(name):
    """Remove reference numbers and descriptor words from a captured name."""
    s = re.sub(r"\s+", " ", name).strip(" ,;:-*+")
    s = re.sub(r"^\d+\s*-\s*|^WEB_", "", s, flags=re.I)  # Banco: leading reference + dash, WEB_ prefix (ACH SEC code)
    previous = None
    while s != previous:  # more than one can be stacked, e.g. "IQVIA RDS INC EDI PYMNTS 123"
        previous = s
        s = NOISE_AT_END.sub("", s).strip(" ,;:-*")
    s = re.sub(r"^\d{4,}\s*(?=[A-Z])", "", s, flags=re.I)  # leading reference or employee number, also glued: 29027THE MT GROU
    s = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", s, flags=re.I)  # a word written twice: SUMTER ELECTRIC ELECTRIC
    return without_repeat(s) or None


# One standard name per payer or payee. Bank feeds cut names at 16 characters, so most of these are prefixes.
# The first match wins, so the specific ones go first.
ALIASES = [
    # sponsors and CROs
    (r"^PAREXEL", "Parexel International"), (r"^SYNEOS", "Syneos Health"), (r"^MEDPACE", "Medpace"),
    (r"^IQVIA", "IQVIA RDS"), (r"^ICON CLINICAL", "ICON Clinical"), (r"^FORTREA", "Fortrea"),
    (r"^PRECISION FOR ME", "Precision for Medicine"), (r"^PSI PHARMA", "PSI Pharma Support"),
    (r"^CLINICAL FINANCI", "Clinical Financial Services"), (r"^PHARMACEUTICAL R", "Pharmaceutical Research Associates"),
    (r"^BOEHRINGER", "Boehringer Ingelheim"), (r"^ELI LILLY", "Eli Lilly"), (r"^MERCK", "Merck"),
    (r"^SANOFI", "Sanofi"), (r"^GENENTECH", "Genentech"), (r"^BEONE|^BEIGENE", "BeOne Medicines"),
    (r"^INDAPTUS", "Indaptus Therapeutics"), (r"^DRUGDEV", "DrugDev (IQVIA)"), (r"^NEUROCRINE", "Neurocrine Biosciences"),
    (r"^PREMIER RESEARCH", "Premier Research"), (r"^INTERNATIONAL GR", "International Grants Administration"),
    (r"^BLOCK CLINICAL", "Block Clinical"), (r"^NCGS", "NCGS"), (r"^HONGKONG TIGERMED|^TIGERMED", "Hongkong Tigermed"),
    (r"^GREENPHIRE", "Greenphire"), (r"^PROMIS NEURO", "Promis Neurosciences"), (r"^CLINIPACE", "Clinipace"),
    (r"^POPULACE HEALTH", "Populace Health"), (r"^ARG\b", "ARG Pass Through"), (r"^SHORE CAPITAL", "Shore Capital"),
    (r"^BENEFLEX", "Beneflex"), (r"^PPD INVESTIGATOR", "PPD Investigator Services"), (r"^AXSOME", "Axsome Therapeutics"), (r"^PROSCIENTO", "ProSciento"),
    (r"^CTI ?CLIN", "CTI Clinical Trial Services"), (r"^PRECISION BIOSPE", "Precision Biospecimen Solutions"),
    (r"^JOHNSON (& )?JOHNSO", "Johnson & Johnson"), (r"^NOVOTECH", "Novotech"), (r"^HUNGAROTRIAL", "Hungarotrial"),
    # payroll, benefits, insurance
    (r"^ADP\b", "ADP"), (r"^AFLAC", "Aflac"), (r"^DELTA DENTAL", "Delta Dental"), (r"^PRINCIPAL", "Principal (ESOP / retirement)"),
    (r"^UNITEDHEALTHCARE", "UnitedHealthcare"), (r"^MCS LIFE", "MCS Life"), (r"^TRIPLE-S", "Triple-S"),
    (r"^FIRST MEDICAL HE", "First Medical Health Plan"), (r"^PAYLOCITY", "Paylocity"), (r"^PAYCHEX", "Paychex"),
    (r"^JOHN HANCOCK", "John Hancock"), (r"^EMPOWER", "Empower Retirement"), (r"^HSA BANK", "HSA Bank"),
    (r"^INTUIT PAYROLL|^INTUIT\b.*QUICKBOOKS", "Intuit Payroll"), (r"^INTUIT", "Intuit"),
    (r"^OUTSOURCING SOLU", "Outsourcing Solutions"), (r"^HEALTH CARE SERV", "Health Care Service Corp"),
    (r"^ERISA (SERVICES|SVCS)", "ERISA Services"), (r"^LINCOLN NATIONA", "Lincoln National"), (r"^THE HARTFORD", "The Hartford"),
    (r"^HUB INTERNATION|^HUB$", "HUB International"),
    # taxes, loans, cards
    (r"^IRS|^US TREASURY|^USATAXPYMT", "IRS"), (r"^DEPT DE HACIENDA|^DEPARTAMENTO DE HACIENDA", "Departamento de Hacienda PR"),
    (r"^(STATE|MUNICIPAL) IVU", "Puerto Rico IVU (sales tax)"),
    (r"^(STATE OF CT DRS|SC DEPT REVENUE|NJ WEB|WEBFILE TAX|OHIO-TAX)", "State tax authority"),
    (r"^PENNANTPARK", "PennantPark Loan Agency"), (r"^PENNANT PARK INVESTMENT", "Pennant Park Investment Admin"), (r"^MERRILL LYNCH", "Merrill Lynch"),
    (r"^AMERICAN EXPRESS|^AMEX", "American Express"), (r"^BK OF AMER VISA|^BANK OF AMERICA VISA|^BOFA VISA", "Bank of America Visa"),
    (r"^CHASE CARD|^JPMCB CARD|^CHASE CREDIT CRD", "Chase Card"), (r"^EWALLET - DIVVYP?$", "Divvy eWallet"), (r"^EWALLET - DIVVY|^DIVVY", "Divvy (expense card)"),
    # our own group entities
    (r"^LATIN CLI", "Latin Clinical (affiliate)"), (r"\b(GABRAIL|GABRIAL)\b", "Gabrail (affiliate)"),
    (r"\bSARGON\b", "Sargon (affiliate)"), (r"^SCP CLINICAL RESEARCH HOLDINGS$", "SCP Clinical Research Holdings (affiliate)"), (r"\bSCP CLINI|^SCP\b", "SCP Clinical (affiliate)"),
    (r"\bRENSTAR\b", "Renstar (affiliate)"), (r"^CHASE MED", "Chase Medical Research (affiliate)"),
    (r"\bBIO ?BEHAV", "Bio Behavioral (affiliate)"),
    # utilities and vendors
    (r"^CITY OF OCALA", "City of Ocala"), (r"^TECO", "TECO / Peoples Gas"), (r"^VERIZON", "Verizon Wireless"),
    (r"^COMCAST", "Comcast Xfinity"), (r"^BRINKS", "Brinks Home Security"), (r"^ADT", "ADT Security"),
    (r"^QUEST ?DIAGNOSTI", "Quest Diagnostics"), (r"^CLEVELAND CLINI", "Cleveland Clinic Laboratories"),
    (r"^CLOUDBYZ", "Cloudbyz"), (r"^CRIO", "CRIO"), (r"^GLENWOOD", "Glenwood Systems"), (r"^LANDAUER", "Landauer"),
    (r"^FEDEX", "FedEx"), (r"^AIRGAS", "Airgas"), (r"^LINDE", "Linde Gas"), (r"^STANDLEY", "Standley Pest Control"),
    (r"^WELLS FARGO VEND", "Wells Fargo Vendor Financial"), (r"^INOVALON", "Inovalon"), (r"^ORACLE", "Oracle America"),
    (r"^WRL ADV", "WRL Advertising"), (r"^FLORIDA NATURAL", "Florida Natural Gas"), (r"^NICOLAUS", "Nicolaus Telephone"),
    (r"^CITRIN COOPERMAN", "Citrin Cooperman"), (r"^(THE )?CROSSROADS G", "Crossroads Group"),
    (r"^CENTRISERVE", "Centriserve IT"), (r"^PLANTE (& )?MORAN", "Plante Moran"), (r"^MC ?DERMOTT", "McDermott Will & Emery"),
    (r"^C\.?B\.? ?RAGLAND(?! COMPANY ESCROW)", "C.B. Ragland Co"),
    (r"^AEE\b", "AEE (PR Electric Power Authority)"), (r"^WORLDNET", "WorldNet (PR telecom)"), (r"^COX COMM", "Cox Communications"),
]
ALIASES_RE = [(re.compile(rx, re.I), name) for rx, name in ALIASES]


def standard_name(name):
    for rx, standard in ALIASES_RE:
        if rx.search(name):
            return standard
    return name.title() if name.isupper() else name


def extract(bank, direction, narrative):
    """Run CPTY_RULES on one narrative. Returns (rule id, kind, raw text, name); rule id is None if nothing matched."""
    text = re.sub(r"\s+", " ", str(narrative or "")).strip()
    for rid, banks, rule_direction, kind, rx in CPTY_RULES_RE:
        if (banks and bank not in banks) or (rule_direction and rule_direction != direction):
            continue
        match = rx.search(text)
        if not match:
            continue
        if kind not in ("party", "payroll"):
            return rid, kind, None, None
        raw = match.group(1)
        name = clean(raw)
        if name and rid.startswith("W"):
            name = UP_TO_LEGAL_SUFFIX.match(name).group(1)
        if name and rid == "J06":
            name = split_camel(name)
        if name:
            name = LEGAL_AT_END.sub("", name).strip(" ,;:-*")
        if not name or len(name) < 3:
            continue
        if rid == "J05" and CODE_LIKE.fullmatch(name) and standard_name(name) == name.title():  # a code, unless an alias knows it
            continue
        if kind == "payroll":
            entity = standard_name(name).replace(" (affiliate)", "")
            return rid, kind, raw, f"Payroll funding ({entity})"
        return rid, kind, raw, standard_name(name)
    return None, "none", None, None


def derive_phasewell_counterparty(bank: Optional[str], direction: Optional[str], narrative: str) -> Tuple[Optional[str], Optional[str], str]:
    """Return (counterparty name, rule id, kind) for one Phasewell bank narrative.

    bank is an account name ending in the bank (e.g. "Operating - JPMC") or a bank code (JPMC, BofA, TD, SS, Banco, FB);
    direction is 'credit' or 'debit' (rules for the other direction are skipped; None skips the direction check).
    The rule id is None when no rule matches (the caller can fall back to the generic parser). When a rule matches but its kind
    has no outside counterparty (internal, fee, check, ...) the name is None and the kind says why.
    """
    code = bank if bank in BANKS else account_bank(bank)
    rid, kind, _raw, name = extract(code, direction, narrative)
    return name, rid, kind
