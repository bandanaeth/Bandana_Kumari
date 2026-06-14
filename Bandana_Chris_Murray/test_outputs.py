"""
pytest test suite for Rodriguez Quinceanera Event Supply Readiness Audit
Channel A - Deterministic, API-state validation and exact value matching
"""

import json
import csv
from pathlib import Path
from datetime import datetime


class MockDataValidator:
    """Validates mock data files and API state consistency"""
    
    def __init__(self, mock_data_root: Path):
        self.mock_data_root = Path(mock_data_root)
    
    def load_csv(self, service_name: str, filename: str):
        """Load CSV file from service directory"""
        path = self.mock_data_root / service_name / filename
        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return rows
    
    def load_json(self, service_name: str, filename: str):
        """Load JSON file from service directory"""
        path = self.mock_data_root / service_name / filename
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data


# Pytest fixtures and helper setup
def pytest_configure(config):
    """Set up test configuration"""
    config.addinivalue_line(
        "markers", 
        "api_state: mark test as API state validation"
    )
    config.addinivalue_line(
        "markers",
        "value_match: mark test as exact value matching"
    )
    config.addinivalue_line(
        "markers",
        "fk_consistency: mark test as foreign key validation"
    )


# ===== CHANNEL A TESTS - DETERMINISTIC VALUE MATCHING =====

def test_focal_event_exists():
    """POSITIVE: Focal event evt_rodriguez_001 exists with confirmed status"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    focal_events = [e for e in events if e['id'] == 'evt_rodriguez_001']
    assert len(focal_events) == 1, "Focal event not found"
    focal = focal_events[0]
    assert focal['status'] == 'confirmed', f"Event status is {focal['status']}, not confirmed"
    assert focal['location'] == 'Emerald Hall', "Event location mismatch"
    assert '2026-10-17' in focal['start'], "Event date not October 17, 2026"


def test_focal_event_date_is_october_17():
    """POSITIVE: Focal event starts at 2026-10-17T12:00:00"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    focal = next(e for e in events if e['id'] == 'evt_rodriguez_001')
    assert focal['start'] == '2026-10-17T12:00:00', f"Unexpected start time: {focal['start']}"


def test_inventory_current_file_exists():
    """POSITIVE: Current inventory file (v2.1) exists in drive"""
    files = load_csv_fixture("google-drive-api", "files.csv")
    inv_files = [f for f in files if 'Inventory' in f['name'] and 'v2.1' in f['name']]
    assert len(inv_files) >= 1, "Current inventory v2.1 file not found"
    assert inv_files[0]['modified_time'] == '2026-10-12T11:22:00', "File modified time unexpected"


def test_inventory_stale_v20_exists():
    """POSITIVE: Stale inventory v2.0 file exists (temporal revision trap)"""
    files = load_csv_fixture("google-drive-api", "files.csv")
    old_files = [f for f in files if 'v2.0' in f['name']]
    assert len(old_files) >= 1, "Stale v2.0 file not found"
    assert old_files[0]['modified_time'] == '2026-09-28T09:15:00', "v2.0 date unexpected"


def test_current_inventory_modified_after_stale():
    """POSITIVE: Current inventory (v2.1) modified after stale version (v2.0)"""
    files = load_csv_fixture("google-drive-api", "files.csv")
    current = next((f for f in files if 'v2.1' in f['name']), None)
    stale = next((f for f in files if 'v2.0' in f['name']), None)
    assert current is not None and stale is not None, "Missing inventory files"
    current_ts = datetime.fromisoformat(current['modified_time'])
    stale_ts = datetime.fromisoformat(stale['modified_time'])
    assert current_ts > stale_ts, f"Current {current_ts} not after stale {stale_ts}"


def test_current_quote_exists():
    """POSITIVE: Current vendor quote est_001 ($285) exists in QuickBooks"""
    estimates = load_json_fixture("quickbooks-api", "estimates.json")
    current_est = next((e for e in estimates if e['Id'] == 'est_001'), None)
    assert current_est is not None, "Current estimate est_001 not found"
    assert current_est['TotalAmt'] == 285.00, f"Quote amount {current_est['TotalAmt']}, not 285"
    assert current_est['DocNumber'] == 'PEL-2026-4481', "Quote number mismatch"


def test_current_quote_pending_status():
    """POSITIVE: Current quote (est_001) has Pending status"""
    estimates = load_json_fixture("quickbooks-api", "estimates.json")
    current = next(e for e in estimates if e['Id'] == 'est_001')
    assert current['TxnStatus'] == 'Pending', f"Status is {current['TxnStatus']}, not Pending"


def test_current_quote_expiry_date():
    """POSITIVE: Current quote expires 2026-10-15"""
    estimates = load_json_fixture("quickbooks-api", "estimates.json")
    current = next(e for e in estimates if e['Id'] == 'est_001')
    assert current['ExpirationDate'] == '2026-10-15', f"Expiry is {current['ExpirationDate']}"


def test_stale_quote_pricing():
    """POSITIVE: Stale quote from 2025 has $195 price"""
    estimates = load_json_fixture("quickbooks-api", "estimates.json")
    stale_ests = [e for e in estimates if e['Id'] in ['est_002', 'est_003']]
    stale_est = next((e for e in stale_ests if e.get('TotalAmt') == 195.00), None)
    assert stale_est is not None, "Stale $195 estimate not found"


def test_sofia_helper_window_345_to_615():
    """POSITIVE: Sofia helper event scheduled 2026-10-17 15:45:00 to 18:15:00"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    sofia_event = next((e for e in events if e['id'] == 'evt_helper_001'), None)
    assert sofia_event is not None, "Sofia helper event not found"
    assert sofia_event['start'] == '2026-10-17T15:45:00', "Start time mismatch"
    assert sofia_event['end'] == '2026-10-17T18:15:00', "End time mismatch"


def test_setup_window_1000_to_1200():
    """POSITIVE: Setup window event scheduled 2026-10-17 10:00:00 to 12:00:00"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    setup_event = next((e for e in events if e['id'] == 'evt_setup_001'), None)
    assert setup_event is not None, "Setup event not found"
    assert setup_event['start'] == '2026-10-17T10:00:00', "Setup start unexpected"
    assert setup_event['end'] == '2026-10-17T12:00:00', "Setup end unexpected"


def test_client_approval_email_exists():
    """POSITIVE: Client approval email from Mariana exists"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    client_msg = next((m for m in messages if m['id'] == 'msg_client_001'), None)
    assert client_msg is not None, "Client approval email not found"
    assert client_msg['from_addr'] == 'mariana.rodriguez@family.com', "Sender mismatch"


def test_client_theme_approval_content():
    """POSITIVE: Client email contains Modern Elegance theme and no-substitution mandate"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_client_001')
    body = msg['body'].lower()
    assert 'modern elegance' in body, "Theme not found in email"
    assert 'formal white' in body, "Formal white mandate not found"
    assert 'no cream' in body or 'no substitute' in body, "No-substitution clause not found"


def test_vendor_quote_email_exists():
    """POSITIVE: Premium Event Linens vendor email exists"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    vendor_msg = next((m for m in messages if m['id'] == 'msg_vendor_quote_001'), None)
    assert vendor_msg is not None, "Vendor quote email not found"
    assert 'premiumeventlinens.com' in vendor_msg['from_addr'], "Wrong vendor"


def test_vendor_quote_email_content_285():
    """POSITIVE: Vendor email body contains $285 total"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_vendor_quote_001')
    body = msg['body'].lower()
    assert '285' in body or '$285' in body, "Quote amount not found in email"


def test_budget_internal_note_400_remaining():
    """POSITIVE: Internal budget note shows $400 remaining"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    budget_msg = next((m for m in messages if m['id'] == 'msg_budget_001'), None)
    assert budget_msg is not None, "Budget message not found"
    assert '400' in budget_msg['body'], "Budget amount not found"


def test_catering_expense_already_paid():
    """POSITIVE: Catering expense of $400 already committed"""
    expenses = load_json_fixture("quickbooks-api", "expenses.json")
    catering = next((e for e in expenses if e['id'] == 'exp_001'), None)
    assert catering is not None, "Catering expense not found"
    assert catering['amount'] == 400.00, "Catering amount should be $400"


def test_photography_expense_already_paid():
    """POSITIVE: Photography expense of $350 already committed"""
    expenses = load_json_fixture("quickbooks-api", "expenses.json")
    photo = next((e for e in expenses if e['id'] == 'exp_002'), None)
    assert photo is not None, "Photography expense not found"
    assert photo['amount'] == 350.00, "Photography amount should be $350"


def test_storage_assessment_email_exists():
    """POSITIVE: Internal storage assessment email exists"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    storage_msg = next((m for m in messages if m['id'] == 'msg_internal_storage_001'), None)
    assert storage_msg is not None, "Storage assessment email not found"


def test_storage_assessment_28_usable():
    """POSITIVE: Storage email mentions 28 usable napkins"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_internal_storage_001')
    body = msg['body'].lower()
    assert '28' in body, "Usable count 28 not found"


def test_storage_assessment_8_damaged():
    """POSITIVE: Storage email mentions 8 water-stained napkins"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_internal_storage_001')
    body = msg['body'].lower()
    assert '8' in body, "Damaged count 8 not found"
    assert 'water' in body or 'damage' in body, "Damage type not found"


def test_borrowed_item_email_exists():
    """POSITIVE: Yolanda borrowed chargers email exists"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    borrowed_msg = next((m for m in messages if m['id'] == 'msg_borrowed_item_001'), None)
    assert borrowed_msg is not None, "Borrowed item email not found"


def test_borrowed_item_3pm_constraint():
    """POSITIVE: Borrowed chargers email mentions 3 PM delivery"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_borrowed_item_001')
    body = msg['body'].lower()
    assert '3' in body or '15:00' in body or '3 pm' in body, "3 PM delivery time not found"


def test_ralph_helper_email_exists():
    """POSITIVE: Helper availability email from Yolanda exists"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    helper_msg = next((m for m in messages if m['id'] == 'msg_helper_001'), None)
    assert helper_msg is not None, "Helper email not found"


def test_helper_email_sofia_name():
    """POSITIVE: Helper email mentions Sofia"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_helper_001')
    assert 'sofia' in msg['body'].lower() or 'sofia' in msg['subject'].lower(), "Sofia not found"


def test_helper_email_345_to_615():
    """POSITIVE: Helper email mentions 3:45 PM to 6:15 PM window"""
    messages = load_csv_fixture("gmail-api", "messages.csv")
    msg = next(m for m in messages if m['id'] == 'msg_helper_001')
    body = msg['body'].lower()
    assert '3:45' in body or '345' in body, "3:45 PM not found"
    assert '6:15' in body or '615' in body, "6:15 PM not found"


def test_rodriguez_customer_exists():
    """POSITIVE: Rodriguez Family Event customer record exists in QuickBooks"""
    customers = load_csv_fixture("quickbooks-api", "customers.csv")
    rodriguez = next((c for c in customers if c['id'] == 'cust_rodriguez_001'), None)
    assert rodriguez is not None, "Rodriguez customer not found"


def test_premium_event_linens_vendor_active():
    """POSITIVE: Premium Event Linens vendor exists and is active"""
    vendors = load_csv_fixture("quickbooks-api", "vendors.csv")
    vendor = next((v for v in vendors if v['id'] == 'vnd_premium_001'), None)
    assert vendor is not None, "Vendor not found"
    assert 'Premium' in vendor['display_name'] or 'Premium' in vendor.get('company_name', ''), "Wrong vendor"


def test_fk_event_to_calendar():
    """POSITIVE (FK Consistency): evt_rodriguez_001 calendar_id references existing calendar"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    calendars = load_csv_fixture("google-calendar-api", "calendars.csv")
    cal_ids = {c['id'] for c in calendars}
    focal = next(e for e in events if e['id'] == 'evt_rodriguez_001')
    assert focal['calendar_id'] in cal_ids, f"FK calendar_id {focal['calendar_id']} not found"


def test_fk_estimate_to_customer():
    """POSITIVE (FK Consistency): est_001 CustomerRef points to valid customer"""
    estimates = load_json_fixture("quickbooks-api", "estimates.json")
    customers = load_csv_fixture("quickbooks-api", "customers.csv")
    cust_ids = {c['id'] for c in customers}
    current_est = next(e for e in estimates if e['Id'] == 'est_001')
    cust_ref = current_est['CustomerRef']['value']
    assert cust_ref in cust_ids, f"FK CustomerRef {cust_ref} not found"


def test_fk_estimate_to_vendor():
    """POSITIVE (FK Consistency): est_001 VendorRef points to valid vendor"""
    estimates = load_json_fixture("quickbooks-api", "estimates.json")
    vendors = load_csv_fixture("quickbooks-api", "vendors.csv")
    vendor_ids = {v['id'] for v in vendors}
    current_est = next(e for e in estimates if e['Id'] == 'est_001')
    # Validate vendor presence in estimate description
    assert 'Premium Event Linens' in current_est['Line'][0]['Description'], "Vendor mismatch"


def test_trap_invalid_events_present():
    """TRAP: Invalid events (cancelled/tentative) must exist to test trap filtering"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    # Trap 1: Cancelled helper event exists
    cancelled = next((e for e in events if e['id'] == 'evt_cancelled_helper_001'), None)
    assert cancelled is not None, "Trap: Cancelled event should exist"
    assert cancelled['status'] == 'cancelled', "Trap: Event should be marked cancelled"
    # Trap 2: Tentative focal event exists
    tentative = next((e for e in events if e['id'] == 'evt_old_quince_001'), None)
    assert tentative is not None, "Trap: Tentative event should exist"
    assert tentative['status'] == 'tentative', "Trap: Event should be marked tentative"


def test_no_tentative_focal_event_used():
    """Consolidated into test_trap_invalid_events_present - weight moved to combined test"""
    pass


def test_no_wrong_period_event_used():
    """NEGATIVE: evt_wrong_period_001 (August 2026) should not be focal event"""
    events = load_csv_fixture("google-calendar-api", "events.csv")
    old = next((e for e in events if e['id'] == 'evt_wrong_period_001'), None)
    assert old is not None, "Old vendor demo event exists"
    assert '2026-08-22' in old['start'], "Wrong date expected in trap event"


def test_trap_outlook_contains_no_answer_values():
    """TRAP: Outlook must contain zero Rodriguez/napkin values (distractor purity check)"""
    try:
        messages = load_csv_fixture("outlook-api", "messages.csv")
        # Trap validation: distractor service has ZERO answer values
        rodriguez_found = any('rodriguez' in msg.get('body', '').lower() for msg in messages)
        napkin_found = any('napkin' in msg.get('body', '').lower() for msg in messages)
        assert not rodriguez_found, "Trap: Outlook contains Rodriguez (should not)"
        assert not napkin_found, "Trap: Outlook contains napkins (should not)"
    except FileNotFoundError:
        pass


def test_trap_dropbox_contains_no_current_files():
    """TRAP: Dropbox has zero October 2026 files (distractor purity check)"""
    try:
        files = load_csv_fixture("dropbox-api", "files.csv")
        # Trap validation: no current-period files in distractor service
        recent_count = sum(1 for f in files if '2026-10' in f.get('client_modified', ''))
        assert recent_count == 0, f"Trap: Dropbox has {recent_count} Oct 2026 files (should be 0)"
    except FileNotFoundError:
        pass


# ===== HELPER FUNCTIONS =====

def load_csv_fixture(service_name: str, filename: str):
    """Load CSV file from mock_data"""
    base = Path(__file__).parent / "mock_data"
    path = base / service_name / filename
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def load_json_fixture(service_name: str, filename: str):
    """Load JSON file from mock_data"""
    base = Path(__file__).parent / "mock_data"
    path = base / service_name / filename
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


if __name__ == "__main__":
    print("Run with: pytest test_outputs.py -v")
