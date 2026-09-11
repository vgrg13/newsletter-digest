# renderer.py
import hashlib
from datetime import datetime
from html import escape

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
