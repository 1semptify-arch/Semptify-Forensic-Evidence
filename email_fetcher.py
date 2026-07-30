# email_fetcher.py
import imaplib, email, os, getpass, csv, json
from pathlib import Path
from cryptography.fernet import Fernet

SECRETS = Path("secrets")
SECRETS.mkdir(exist_ok=True)
KEYFILE = SECRETS / "master.key"
CRED_FILE = SECRETS / "email_creds.enc"
INBOX = Path("data/semptify_inbox/email")
ATT = Path("data/semptify_inbox/email_attachments")
INBOX.mkdir(parents=True, exist_ok=True)
ATT.mkdir(parents=True, exist_ok=True)

def load_key():
    if not KEYFILE.exists():
        KEYFILE.write_bytes(Fernet.generate_key())
    return Fernet(KEYFILE.read_bytes())

def save_creds(provider, host, user, password):
    f = load_key()
    data = {}
    if CRED_FILE.exists():
        data = json.loads(f.decrypt(CRED_FILE.read_bytes()).decode())
    data[provider] = {"host":host,"user":user,"password":password}
    CRED_FILE.write_bytes(f.encrypt(json.dumps(data).encode()))

def get_creds(provider):
    f = load_key()
    if not CRED_FILE.exists():
        return None
    data = json.loads(f.decrypt(CRED_FILE.read_bytes()).decode())
    return data.get(provider)

def fetch_imap(provider, host, user, password, mailbox="INBOX", limit=0):
    print(f"Connecting to {provider} ({host}) as {user}")
    M = imaplib.IMAP4_SSL(host)
    M.login(user, password)
    M.select(mailbox)
    typ, data = M.search(None, "ALL")
    ids = data[0].split()
    if limit and len(ids) > limit:
        ids = ids[-limit:]
    log_rows = []
    for num in ids:
        typ, msg_data = M.fetch(num, '(RFC822)')
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subject = msg.get('Subject','')
        date = msg.get('Date','')
        fname = f"{num.decode()}_{subject[:50].replace('/','_').replace('\\n',' ')}.eml"
        eml_path = INBOX / fname
        with open(eml_path, 'wb') as f:
            f.write(raw)
        # attachments
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            att_name = part.get_filename()
            if att_name:
                safe = att_name.replace('/','_').replace('\\n',' ')
                att_path = ATT / f"{num.decode()}_{safe}"
                with open(att_path, 'wb') as af:
                    af.write(part.get_payload(decode=True))
        log_rows.append([num.decode(), subject, date, str(eml_path)])
    # write CSV log
    with open("data/semptify_inbox/email_fetch_log.csv","a",newline='',encoding='utf-8') as csvf:
        w = csv.writer(csvf)
        for r in log_rows:
            w.writerow(r)
    M.logout()
    print(f"Fetched {len(log_rows)} messages for {provider}")

if __name__ == "__main__":
    # providers: gmail, outlook
    providers = [
        {"name":"gmail","host":"imap.gmail.com"},
        {"name":"outlook","host":"outlook.office365.com"}
    ]
    for p in providers:
        creds = get_creds(p["name"])
        if not creds:
            print(f"Enter credentials for {p['name']}")
            user = input("Email: ").strip()
            pwd = getpass.getpass("App password or IMAP password: ")
            save_creds(p["name"], p["host"], user, pwd)
            creds = {"host":p["host"],"user":user,"password":pwd}
        fetch_imap(p["name"], creds["host"], creds["user"], creds["password"], limit=0)
