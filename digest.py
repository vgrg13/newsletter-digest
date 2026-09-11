# digest.py
from __future__ import annotations
import base64, json, os, re, signal, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from bs4 import BeautifulSoup

ALLOWLIST = {
    "ft@newsletters.ft.com","ftav@substack.com","access@interactive.wsj.com",
    "noreply@news.bloomberg.com","info@nl.mail.washingtonpost.com","nytimes@e.newyorktimes.com",
    "dan@axios.com","newsletters@techcrunch.com","dan@tldrnewsletter.com",
    "ourideas@morganstanley.com","connie@strictlyvc.com","cloudedjudgement@substack.com",
    "a16z@substack.com","account@seekingalpha.com","finstoryai@substack.com",
    "valueinvesting+stocks-paid@substack.com","capitalflows@substack.com",
    "michaeljburry@substack.com","aswathdamodaran@substack.com","thewallstreetskinny@substack.com",
    "reidhoffman@substack.com","raydalio@substack.com","stealthstartupspy@substack.com",
    "technically@substack.com","on+open-tab@substack.com","on+product@substack.com",
    "on+stories@substack.com","vchappens+roundbrief-brief-interview-on-vc@substack.com",
    "capitalflows+interest-rate-and-fx-strategy@substack.com",
    "capitalflows+equity-strategy@substack.com","peinsights@substack.com",
    "companylaunchtracker@substack.com","theeconomistoffthecharts@substack.com",
    "yadavrohit@substack.com","entrepreneursforimpact@substack.com","paulinaszyzdek@substack.com",
    "stephmui@substack.com","understandingai@substack.com","20vc@substack.com",
    "privatecreditconnect@substack.com","post+the-weekender@substack.com",
    "valueinvesting+investing@substack.com",
}
BLOCKLIST = {
    "support@apollo.io","hello@mail.apollo.io","handshake@mail.joinhandshake.com",
    "recruiting@insightpartners.com","info@bb3.wayup.com","ace@email.numerade.com",
    "communications@berkeley.edu","ucberkeley@warnme.berkeley.edu",
    "relay@relay.engage.campuslabs.com","undergrd@lists.haas.berkeley.edu",
    "enroll@uconline.edu","info@emp.apartmentlist.com","sm8599@email.bncollege.com",
    "no-reply@p.simplywall.st","product@engage.canva.com","ratings@spglobal.com",
    "subscriptions@seekingalpha.com","claudedesktop@substack.com",
    "myft@news-alerts.ft.com","no-reply@substack.com",
}
COMMERCIAL_RE = re.compile(r"order (confirmation|shipped|delivered)|your receipt|\$\d+ off|% off|flash sale|last chance|expires (today|soon)|verify your|reset your password|sign[- ]?in attempt|welcome to|invoice|payment (received|due|failed)|tracking|your (order|package|delivery)", re.IGNORECASE)
LINK_BLOCK = ["unsubscribe","utm_","email_click","mailtrack","list-manage","mailchi.mp","click.convertkit","track.customer.io","sendgrid.net/ls/click"]

TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

def _env(n):
    v = os.environ.get(n, "").strip().strip('"').strip("'")
    if v: return v
    # Fall back to secrets.env in the project directory
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                k, _, val = line.partition("=")
                if k.strip() == n:
                    return val.strip().strip('"').strip("'")
    raise RuntimeError(f"Missing credential {n} — set it in secrets.env")

def _refresh_token():
    data = urllib.parse.urlencode({"client_id":_env("GMAIL_CLIENT_ID"),"client_secret":_env("GMAIL_CLIENT_SECRET"),"refresh_token":_env("GMAIL_REFRESH_TOKEN"),"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        b = json.loads(r.read())
    t = b.get("access_token")
    if not t: raise RuntimeError(f"Token refresh failed: {b}")
    return t

def _get(path, tok):
    req = urllib.request.Request(GMAIL_BASE+path)
    req.add_header("Authorization",f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read(4 * 1024 * 1024))  # cap at 4 MB per response

def _post(path, tok, payload):
    req = urllib.request.Request(GMAIL_BASE+path, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Authorization",f"Bearer {tok}"); req.add_header("Content-Type","application/json")
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

def _decode(data):
    p = data + "=" * (-len(data)%4)
    try: return base64.urlsafe_b64decode(p).decode("utf-8",errors="replace")
    except: return ""

def _flatten(payload):
    out=[]; stack=[payload]
    while stack:
        p=stack.pop(); out.append(p)
        for c in p.get("parts",[]) or []: stack.append(c)
    return out

def _extract(payload):
    parts=_flatten(payload); plain=""; html_raw=""
    for p in parts:
        mime=p.get("mimeType",""); data=(p.get("body") or {}).get("data","")
        if not data: continue
        if mime=="text/plain" and not plain: plain=_decode(data)
        elif mime=="text/html" and not html_raw: html_raw=_decode(data)
    links=[]
    if html_raw:
        html_raw = html_raw[:300_000]  # cap at 300 KB before parsing
        soup=BeautifulSoup(html_raw,"lxml"); seen=set()
        for a in soup.find_all("a",href=True):
            href=(a.get("href") or "").strip()
            if not href or href.startswith(("mailto:","tel:","#")): continue
            if any(s in href.lower() for s in LINK_BLOCK): continue
            if href in seen: continue
            seen.add(href); links.append({"url":href,"anchor_text":(a.get_text(strip=True) or "")[:80]})
            if len(links)>=5: break
    if not plain and html_raw:
        soup=BeautifulSoup(html_raw,"lxml")
        for a in soup.find_all("a",href=True): a.replace_with(f"{a.get_text(strip=True)} ({a['href']})")
        plain=soup.get_text(separator="\n",strip=True)
    return plain.strip(), links

def _hdr(headers, name):
    nl=name.lower()
    for h in headers:
        if h.get("name","").lower()==nl: return h.get("value","")
    return ""

def _parse_from(raw):
    if "<" in raw and ">" in raw:
        name=raw.split("<")[0].strip().strip('"'); email=raw.split("<",1)[1].split(">")[0].strip().lower()
        return name or email.split("@")[0], email
    c=raw.strip().lower(); return c.split("@")[0], c

def classify(headers, subject, email, plain):
    if email in BLOCKLIST: return False, "blocklist"
    ct=_hdr(headers,"Content-Type").lower()
    if "text/calendar" in ct: return False, "calendar invite"
    auto=_hdr(headers,"Auto-Submitted").lower()
    if auto and auto!="no": return False, f"auto-submitted"
    if email in ALLOWLIST: return True, "allowlist"
    if not _hdr(headers,"List-Unsubscribe"): return False, "no List-Unsubscribe"
    lid=_hdr(headers,"List-Id"); prec=_hdr(headers,"Precedence").lower()
    if not lid and "bulk" not in prec and "list" not in prec: return False, "no List-Id/bulk"
    if COMMERCIAL_RE.search(subject): return False, "commercial subject"
    if len(plain)<400: return False, f"too short ({len(plain)} chars)"
    return True, "layer 2"

def fetch(since_hours=168, max_msgs=200):
    tok=_refresh_token()
    days=max(1,(since_hours+23)//24)
    q=f"newer_than:{days}d -in:sent -in:chats -in:trash"
    listing=_get(f"/messages?q={urllib.parse.quote(q)}&maxResults={max_msgs}",tok)
    ids=[m["id"] for m in listing.get("messages",[])]
    cutoff=(datetime.now(timezone.utc).timestamp()-since_hours*3600)*1000
    def _alarm(signum, frame): raise TimeoutError
    signal.signal(signal.SIGALRM, _alarm)
    out=[]; counts={}
    for mid in ids:
        try:
            signal.alarm(25)
            full=_get(f"/messages/{mid}?format=full",tok)
            signal.alarm(0)
        except Exception:
            signal.alarm(0)
            continue
        if float(full.get("internalDate",0))<cutoff: continue
        payload=full.get("payload",{}); headers=payload.get("headers",[])
        from_raw=_hdr(headers,"From"); subject=_hdr(headers,"Subject") or "(no subject)"
        name,email=_parse_from(from_raw)
        counts[email]=counts.get(email,0)+1
        plain,links=_extract(payload)
        keep,reason=classify(headers,subject,email,plain)
        print(f"  {email} -> {'INCLUDED' if keep else 'EXCLUDED'} -> {reason}",file=sys.stderr)
        if not keep: continue
        dt=datetime.fromtimestamp(float(full.get("internalDate",0))/1000,tz=timezone.utc)
        out.append({"id":mid,"source":name,"sender_email":email,"subject":subject,"received_at":dt.isoformat(),"content":plain[:8000],"links":links})
    thresh=max(4,int(since_hours/24)*5)
    bursty={e for e,n in counts.items() if n>thresh}
    out=[m for m in out if m["sender_email"] not in bursty]
    return out

def send_digest(kind, analysis):
    import renderer as R
    sent_at=datetime.now()
    if kind=="daily":
        html=R.render_daily(analysis,sent_at); subject="Daily Digest - "+sent_at.strftime("%A, %B %-d")
    else:
        html=R.render_weekly(analysis,sent_at); subject="Weekly Digest - Week of "+sent_at.strftime("%B %-d")
    addr=_env("GMAIL_ADDRESS")
    msg=EmailMessage(); msg["From"]=addr; msg["To"]=addr; msg["Subject"]=subject
    msg.set_content("Your newsletter digest - open in an HTML-capable client.")
    msg.add_alternative(html,subtype="html")
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")
    tok=_refresh_token()
    return _post("/messages/send",tok,{"raw":raw})

def send_failure(err):
    try:
        addr=_env("GMAIL_ADDRESS"); tok=_refresh_token()
        msg=EmailMessage(); msg["From"]=addr; msg["To"]=addr; msg["Subject"]="Digest failed"
        msg.set_content(f"Error: {err[:300]}")
        msg.add_alternative(f'<html><body style="font-family:sans-serif;background:#0e0e14;color:#e2e8f0;padding:40px;"><h2 style="color:#f87171;">Digest failed</h2><p><code>{err[:300]}</code></p></body></html>',subtype="html")
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")
        _post("/messages/send",tok,{"raw":raw})
    except: pass
