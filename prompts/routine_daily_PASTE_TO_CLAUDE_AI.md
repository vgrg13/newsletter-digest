# DAILY DIGEST ROUTINE — paste this entire prompt into claude.ai
# Schedule: every day at 7:00 AM America/New_York
# Required env vars: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, GMAIL_ADDRESS

You are a scheduled remote agent. Run the following steps every morning to deliver Vatsal's newsletter digest.

---

## STEP 0 — Setup

Install dependencies and write the pipeline code to disk:

```bash
pip install --quiet beautifulsoup4 lxml google-auth google-auth-oauthlib google-api-python-client
```

Write `renderer.py`:

```python
# renderer.py
import hashlib
from datetime import datetime
from html import escape
from typing import Iterable

PALETTE = [
    {"name":"amber","g1":"#f59e0b","g2":"#fbbf24","bg_rgba":"245,158,11","badge":"#fbbf24","arrow":"#f59e0b"},
    {"name":"blue","g1":"#3b82f6","g2":"#60a5fa","bg_rgba":"59,130,246","badge":"#60a5fa","arrow":"#3b82f6"},
    {"name":"emerald","g1":"#10b981","g2":"#34d399","bg_rgba":"16,185,129","badge":"#34d399","arrow":"#10b981"},
    {"name":"red","g1":"#ef4444","g2":"#f87171","bg_rgba":"239,68,68","badge":"#f87171","arrow":"#ef4444"},
    {"name":"indigo","g1":"#6366f1","g2":"#818cf8","bg_rgba":"99,102,241","badge":"#818cf8","arrow":"#6366f1"},
    {"name":"orange","g1":"#f97316","g2":"#fb923c","bg_rgba":"249,115,22","badge":"#fb923c","arrow":"#f97316"},
    {"name":"violet","g1":"#8b5cf6","g2":"#a78bfa","bg_rgba":"139,92,246","badge":"#a78bfa","arrow":"#8b5cf6"},
]

def _color_for(key):
    digest = hashlib.md5(key.lower().strip().encode()).hexdigest()
    return PALETTE[int(digest,16) % len(PALETTE)]

_HEAD = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
body { font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
@media screen and (max-width:600px){
  .nd-wrapper { padding:12px 8px 40px !important; }
  .nd-container { width:100% !important; max-width:100% !important; }
  .nd-header { padding:22px 16px 18px !important; border-radius:14px !important; }
  .nd-header-title { font-size:22px !important; line-height:1.25 !important; }
  .nd-header-title .nd-gradient-text { background:none !important; -webkit-text-fill-color:#a78bfa !important; color:#a78bfa !important; }
  .nd-header-meta { font-size:12px !important; margin-bottom:16px !important; }
  .nd-stat { display:inline-block !important; margin:0 4px 6px 0 !important; font-size:11px !important; }
  .nd-card { border-radius:10px !important; margin-bottom:10px !important; }
  .nd-card-inner { padding:14px 14px 14px !important; }
  .nd-badge { font-size:9px !important; padding:2px 8px !important; }
  .nd-badge-sub { font-size:10px !important; }
  .nd-card-title { font-size:15px !important; margin:8px 0 10px !important; }
  .nd-bullet { font-size:13px !important; }
  .nd-analysis { padding:12px 12px !important; border-radius:8px !important; }
  .nd-analysis p { font-size:12.5px !important; line-height:1.7 !important; }
  .nd-analysis-label { font-size:9px !important; }
  .nd-link-item { font-size:11px !important; margin-right:10px !important; }
  .nd-big-picture { padding:18px 14px !important; border-radius:10px !important; }
  .nd-big-picture p { font-size:13.5px !important; line-height:1.75 !important; }
  .nd-big-picture-label { font-size:9px !important; }
  .nd-section-label { font-size:9px !important; padding:14px 4px 8px !important; }
  .nd-footer { padding:20px 0 0 !important; font-size:10px !important; }
}
</style></head>"""
_FOOTER = """<div class="nd-footer" style="text-align:center;padding:28px 0 0;font-size:11px;color:#334155;line-height:1.8;"><div style="font-size:12px;font-weight:700;color:#475569;margin-bottom:4px;">◆ DIGEST</div>Powered by Claude</div>"""

def _render_header(eyebrow, date_label, stat_pairs):
    stats = "".join(f'<span class="nd-stat" style="display:inline-block;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:5px 13px;font-size:12px;font-weight:500;color:#cbd5e1;margin-right:6px;"><strong style="color:#fff;">{n}</strong> {escape(label)}</span>' for n,label in stat_pairs)
    return (f'<div class="nd-header" style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 45%,#0f3460 100%);border-radius:20px;padding:36px 32px 28px;margin-bottom:10px;"><div style="font-size:11px;font-weight:700;letter-spacing:0.12em;color:#6366f1;text-transform:uppercase;margin-bottom:8px;">{escape(eyebrow)}</div><div class="nd-header-title" style="font-size:28px;font-weight:800;color:#fff;line-height:1.2;margin-bottom:8px;">Your Newsletter<br><span class="nd-gradient-text" style="background:linear-gradient(90deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Digest</span></div><div class="nd-header-meta" style="font-size:13px;color:#94a3b8;margin-bottom:22px;">{escape(date_label)} &nbsp;·&nbsp; Summarized by Claude</div>{stats}</div>')

def _render_big_picture(label, body):
    return f'<div class="nd-big-picture" style="background:linear-gradient(135deg,#0f172a,#1e1b4b);border:1px solid #1e3a5f;border-radius:14px;padding:24px 26px;margin-bottom:12px;"><div class="nd-big-picture-label" style="font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#38bdf8;margin-bottom:10px;">⬡ &nbsp;{escape(label)}</div><p style="margin:0;font-size:14.5px;color:#e2e8f0;line-height:1.8;">{escape(body)}</p></div>'

def _render_section_label(text):
    return f'<div class="nd-section-label" style="font-size:10px;font-weight:700;letter-spacing:0.1em;color:#475569;text-transform:uppercase;padding:18px 4px 10px;">{escape(text)}</div>'

def _render_analysis_block(body):
    return f'<div class="nd-analysis" style="background:linear-gradient(135deg,#1e1b4b,#1a1a2e);border:1px solid #312e81;border-radius:10px;padding:14px 16px;margin-bottom:16px;"><div style="margin-bottom:8px;"><span style="display:inline-block;width:18px;height:18px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:5px;font-size:9px;text-align:center;line-height:18px;color:#fff;vertical-align:middle;margin-right:6px;">◆</span><span class="nd-analysis-label" style="font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#818cf8;vertical-align:middle;">Claude\'s Analysis</span></div><p style="margin:0;font-size:13px;color:#c7d2fe;line-height:1.75;">{escape(body)}</p></div>'

def _render_bullets(bullets, arrow_color):
    items = "".join(f'<li class="nd-bullet" style="font-size:13.5px;color:#94a3b8;line-height:1.6;padding:4px 0 4px 20px;position:relative;"><span style="position:absolute;left:0;color:{arrow_color};">→</span>{escape(b)}</li>' for b in bullets)
    return f'<ul style="list-style:none;margin:0 0 16px;padding:0;">{items}</ul>'

def _render_links_row(links):
    if not links: return ""
    items = "".join(f'<a href="{escape(l["url"],quote=True)}" class="nd-link-item" style="display:inline-block;font-size:12px;color:#6366f1;text-decoration:none;margin-right:16px;">↗ {escape(l.get("label") or l["url"])}</a>' for l in links if l.get("url"))
    return f'<div style="border-top:1px solid #1e1e2e;padding-top:12px;">{items}</div>' if items else ""

def _render_top_story_card(story):
    c = _color_for(story.get("sender_email") or story.get("source",""))
    source = story.get("source",""); sender_email = story.get("sender_email","")
    headline = story.get("headline") or source
    return (f'<div class="nd-card" style="background:#16161f;border:1px solid #1e1e2e;border-radius:14px;margin-bottom:14px;overflow:hidden;"><div style="height:3px;background:linear-gradient(90deg,{c["g1"]},{c["g2"]});border-radius:12px 12px 0 0;"></div><div class="nd-card-inner" style="padding:18px 22px 18px;"><span class="nd-badge" style="display:inline-block;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:3px 10px;border-radius:20px;background:rgba({c["bg_rgba"]},0.18);color:{c["badge"]};">{escape(source)}</span><span class="nd-badge-sub" style="font-size:11px;color:#475569;margin-left:8px;">{escape(sender_email)}</span><div class="nd-card-title" style="font-size:17px;font-weight:700;color:#f1f5f9;line-height:1.35;margin:10px 0 14px;">{escape(headline)}</div>{_render_bullets(story.get("bullets",[]),c["arrow"])}{_render_analysis_block(story.get("analysis",""))}{_render_links_row(story.get("links",[]))}</div></div>')

def _render_also_row(item):
    c = _color_for(item.get("sender_email") or item.get("source",""))
    return (f'<div style="display:flex;align-items:baseline;gap:10px;padding:9px 0;border-bottom:1px solid #1a1a28;"><span style="flex-shrink:0;font-size:9px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;padding:2px 8px;border-radius:20px;background:rgba({c["bg_rgba"]},0.18);color:{c["badge"]};">{escape(item.get("source",""))}</span><span style="font-size:12.5px;color:#64748b;line-height:1.5;">{escape(item.get("summary",""))}</span></div>')

def _render_also_section(items):
    if not items: return ""
    rows = "".join(_render_also_row(i) for i in items)
    n = len(items); label = f"Also Today — {n} more newsletter" + ("s" if n!=1 else "")
    return f'{_render_section_label(label)}<div style="background:#13131c;border:1px solid #1e1e2e;border-radius:14px;padding:4px 18px 4px;margin-bottom:14px;">{rows}</div>'

def _render_theme_card(theme):
    c = _color_for(theme.get("title",""))
    covered = "Covered by: " + ", ".join(theme.get("covered_by",[])) if theme.get("covered_by") else ""
    return (f'<div class="nd-card" style="background:#16161f;border:1px solid #1e1e2e;border-radius:14px;margin-bottom:14px;overflow:hidden;"><div style="height:3px;background:linear-gradient(90deg,{c["g1"]},{c["g2"]});border-radius:12px 12px 0 0;"></div><div class="nd-card-inner" style="padding:18px 22px 18px;"><span class="nd-badge" style="display:inline-block;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:3px 10px;border-radius:20px;background:rgba({c["bg_rgba"]},0.18);color:{c["badge"]};">Theme</span><span class="nd-badge-sub" style="font-size:11px;color:#475569;margin-left:8px;">{escape(covered)}</span><div class="nd-card-title" style="font-size:17px;font-weight:700;color:#f1f5f9;line-height:1.35;margin:10px 0 14px;">{escape(theme.get("title",""))}</div>{_render_bullets(theme.get("bullets",[]),c["arrow"])}{_render_analysis_block(theme.get("analysis",""))}</div></div>')

def render_daily(analysis, sent_at):
    date_label = sent_at.strftime("%A, %B %-d, %Y")
    stats = analysis.get("stats",{}); n = stats.get("newsletters_count",0); k = stats.get("key_points_count",0)
    body = (f'<body class="nd-wrapper" style="margin:0;padding:28px 16px 56px;background:#0e0e14;"><div class="nd-container" style="max-width:660px;margin:0 auto;width:100%;">' + _render_header("✦ Daily Intelligence",date_label,[(n,"newsletters"),(k,"key points")]) + _render_big_picture("Today\'s Big Picture",analysis.get("big_picture","")) + _render_section_label("Top Stories") + "".join(_render_top_story_card(s) for s in analysis.get("top_stories",[])) + _render_also_section(analysis.get("also_today",[])) + _FOOTER + '</div></body></html>')
    return _HEAD + body

def render_weekly(analysis, sent_at):
    date_label = sent_at.strftime("%A, %B %-d, %Y")
    stats = analysis.get("stats",{}); n = stats.get("themes_count",0); k = stats.get("key_points_count",0)
    body = (f'<body class="nd-wrapper" style="margin:0;padding:28px 16px 56px;background:#0e0e14;"><div class="nd-container" style="max-width:660px;margin:0 auto;width:100%;">' + _render_header("✦ Weekly Intelligence",date_label,[(n,"big themes"),(k,"key points")]) + _render_big_picture("Week in Review",analysis.get("week_in_review","")) + _render_section_label("This Week\'s Big Themes") + "".join(_render_theme_card(t) for t in analysis.get("themes",[])) + _FOOTER + '</div></body></html>')
    return _HEAD + body
```

Write `digest.py`:

```python
# digest.py
from __future__ import annotations
import base64, json, os, re, sys, urllib.parse, urllib.request
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
    v = os.environ.get(n,"").strip().strip('"').strip("'")
    if not v: raise RuntimeError(f"Missing env var {n}")
    return v

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
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

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

def fetch(since_hours=24, max_msgs=75):
    tok=_refresh_token()
    days=max(1,(since_hours+23)//24)
    q=f"newer_than:{days}d -in:sent -in:chats -in:trash"
    listing=_get(f"/messages?q={urllib.parse.quote(q)}&maxResults={max_msgs}",tok)
    ids=[m["id"] for m in listing.get("messages",[])]
    cutoff=(datetime.now(timezone.utc).timestamp()-since_hours*3600)*1000
    out=[]; counts={}
    for mid in ids:
        try: full=_get(f"/messages/{mid}?format=full",tok)
        except: continue
        if float(full.get("internalDate",0))<cutoff: continue
        payload=full.get("payload",{}); headers=payload.get("headers",[])
        from_raw=_hdr(headers,"From"); subject=_hdr(headers,"Subject") or "(no subject)"
        name,email=_parse_from(from_raw)
        counts[email]=counts.get(email,0)+1
        plain,links=_extract(payload)
        keep,reason=classify(headers,subject,email,plain)
        print(f"  {email} → {'INCLUDED' if keep else 'EXCLUDED'} → {reason}",file=sys.stderr)
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
        html=R.render_daily(analysis,sent_at); subject="📨 Daily Digest · "+sent_at.strftime("%A, %B %-d")
    else:
        html=R.render_weekly(analysis,sent_at); subject="📊 Weekly Digest · Week of "+sent_at.strftime("%B %-d")
    addr=_env("GMAIL_ADDRESS")
    msg=EmailMessage(); msg["From"]=addr; msg["To"]=addr; msg["Subject"]=subject
    msg.set_content("Your newsletter digest — open in an HTML-capable client.")
    msg.add_alternative(html,subtype="html")
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")
    tok=_refresh_token()
    return _post("/messages/send",tok,{"raw":raw})

def send_failure(err):
    try:
        addr=_env("GMAIL_ADDRESS"); tok=_refresh_token()
        msg=EmailMessage(); msg["From"]=addr; msg["To"]=addr; msg["Subject"]="⚠️ Digest failed"
        msg.set_content(f"Error: {err[:300]}")
        msg.add_alternative(f'<html><body style="font-family:sans-serif;background:#0e0e14;color:#e2e8f0;padding:40px;"><h2 style="color:#f87171;">Digest failed</h2><p><code>{err[:300]}</code></p></body></html>',subtype="html")
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")
        _post("/messages/send",tok,{"raw":raw})
    except: pass
```

---

## STEP 1 — Fetch today's newsletters

```python
import json, sys
sys.path.insert(0,'.')
import digest

newsletters = digest.fetch(since_hours=24, max_msgs=75)
print(f"Fetched {len(newsletters)} newsletters", file=sys.stderr)
with open('newsletters.json','w') as f:
    json.dump(newsletters, f)
```

If `newsletters` is empty, jump to the fallback at the bottom.

---

## STEP 2 — Layer 3 tiebreaker

Read `newsletters.json`. Discard anything that is clearly a receipt, account alert, or promotional email despite passing the filter. Log each drop.

---

## STEP 3 — Analyze and write analysis.json

You are a senior analyst writing the "Daily Intelligence" briefing for Vatsal — a sharp, time-poor reader who follows business, tech, finance, and policy. Find the signal across today's newsletters. Produce a digest that: (1) surfaces what actually matters today, (2) connects threads the individual writers didn't, (3) has a point of view.

Write `analysis.json` with this exact schema:

```json
{
  "big_picture": "<2–3 tight sentences. A thesis about today, not a recap. Name specific sources. Have an opinion.>",
  "top_stories": [
    {
      "source": "<newsletter brand>",
      "sender_email": "<from address>",
      "headline": "<6–10 specific words>",
      "bullets": [
        "<specific fact with number or name — max 25 words>",
        "<another concrete data point — max 25 words>",
        "<a third — max 25 words>"
      ],
      "analysis": "<2–3 sentences MAX. Implication or contrarian angle. NOT a restatement of bullets.>",
      "links": []
    }
  ],
  "also_today": [
    {
      "source": "<brand>",
      "sender_email": "<from address>",
      "summary": "<one sentence, max 20 words, single most useful fact>"
    }
  ],
  "stats": {"newsletters_count": 0, "key_points_count": 0}
}
```

Rules: 5 top_stories (or fewer if fewer newsletters). Cross-coverage = top story signal. `also_today` = 8 best remaining only. Bullets ≤ 25 words each. Analysis 2–3 sentences MAX. No hedging. No invented facts.

---

## STEP 4 — Send

```python
import json, sys
sys.path.insert(0,'.')
import digest

with open('analysis.json') as f:
    analysis = json.load(f)

result = digest.send_digest('daily', analysis)
print(f"Sent: {result.get('id')}")
```

---

## Fallback (no newsletters)

```python
import sys; sys.path.insert(0,'.'); import digest
digest.send_digest('daily', {"big_picture":"No newsletters arrived in the last 24 hours.","top_stories":[],"also_today":[],"stats":{"newsletters_count":0,"key_points_count":0}})
```

## Error handling

```python
import sys; sys.path.insert(0,'.'); import digest
digest.send_failure("BRIEF ERROR DESCRIPTION")
```
