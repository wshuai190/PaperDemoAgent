"""Dark theme CSS constant for PaperDemoAgent generated demos.

Accent colours are aligned with the SVG primitives palette so that
inline SVGs and HTML/CSS components share a consistent visual language.
"""

# ── Palette (mirrors svg_primitives.py colour constants) ─────────────────
# Background layers
_BG       = "#09090b"   # page / outermost bg
_CARD     = "#18181b"   # card / panel bg
_BORDER   = "#27272a"   # subtle borders
# Text
_TEXT     = "#fafafa"   # primary text
_MUTED    = "#a1a1aa"   # secondary / caption text
# Accent — matches SVG primitives
_BLUE     = "#3b82f6"   # inputs / primary actions
_INDIGO   = "#6366f1"   # transforms / secondary actions
_AMBER    = "#f59e0b"   # decisions / warnings
_GREEN    = "#22c55e"   # outputs / success
_RED      = "#ef4444"   # loss / error
_SLATE    = "#475569"   # connector lines
_SLATE_LT = "#64748b"   # lighter connectors / disabled

DARK_THEME_CSS: str = f"""\
/* ═══════════════════════════════════════════════════════════════
   PaperDemoAgent — Dark Theme
   Background : {_BG}   Cards : {_CARD}   Borders : {_BORDER}
   Text       : {_TEXT}   Muted : {_MUTED}
   Accent     : Blue {_BLUE}  Indigo {_INDIGO}  Green {_GREEN}
                Amber {_AMBER}  Red {_RED}
   ═══════════════════════════════════════════════════════════════ */

/* ── Reset & Box Model ───────────────────────────────────────── */
*, *::before, *::after {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

/* ── Root / Tokens ───────────────────────────────────────────── */
:root {{
  --bg:          {_BG};
  --card:        {_CARD};
  --border:      {_BORDER};
  --text:        {_TEXT};
  --muted:       {_MUTED};
  --blue:        {_BLUE};
  --indigo:      {_INDIGO};
  --amber:       {_AMBER};
  --green:       {_GREEN};
  --red:         {_RED};
  --slate:       {_SLATE};
  --slate-lt:    {_SLATE_LT};

  --radius-sm:   6px;
  --radius:      10px;
  --radius-lg:   16px;
  --shadow:      0 4px 24px rgba(0,0,0,.55);
  --transition:  200ms ease;
  --font:        Inter, ui-sans-serif, system-ui, -apple-system,
                 BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
  --font-mono:   ui-monospace, SFMono-Regular, "SF Mono", Menlo,
                 Consolas, "Liberation Mono", monospace;
}}

/* ── Base ────────────────────────────────────────────────────── */
html {{
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%;
}}

body {{
  background-color: var(--bg);
  color: var(--text);
  font-family: var(--font);
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}}

/* ── Typography ──────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {{
  color: var(--text);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.02em;
}}
h1 {{ font-size: clamp(1.75rem, 4vw, 2.5rem); }}
h2 {{ font-size: clamp(1.35rem, 3vw, 1.875rem); }}
h3 {{ font-size: clamp(1.1rem,  2vw, 1.375rem); }}
h4 {{ font-size: 1.125rem; }}

p       {{ color: var(--text); margin-bottom: 1rem; }}
small,
.text-muted {{ color: var(--muted); font-size: 0.875rem; }}
strong  {{ color: var(--text); font-weight: 600; }}
a       {{
  color: var(--blue);
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: color var(--transition);
}}
a:hover {{ color: var(--indigo); }}

/* ── Layout ──────────────────────────────────────────────────── */
.container {{
  width: 100%;
  max-width: 1200px;
  margin-inline: auto;
  padding-inline: 1.5rem;
}}

.section {{
  padding-block: 4rem;
}}

/* Grid utilities */
.grid         {{ display: grid; gap: 1.5rem; }}
.grid-2       {{ grid-template-columns: repeat(2, 1fr); }}
.grid-3       {{ grid-template-columns: repeat(3, 1fr); }}
.grid-4       {{ grid-template-columns: repeat(4, 1fr); }}
.flex         {{ display: flex; }}
.flex-center  {{ display: flex; align-items: center; justify-content: center; }}
.flex-between {{ display: flex; align-items: center; justify-content: space-between; }}
.gap-1        {{ gap: 0.5rem; }}
.gap-2        {{ gap: 1rem; }}
.gap-3        {{ gap: 1.5rem; }}

/* ── Card / Panel ────────────────────────────────────────────── */
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow);
  transition: border-color var(--transition), box-shadow var(--transition);
}}
.card:hover {{
  border-color: var(--slate-lt);
  box-shadow: 0 8px 32px rgba(0,0,0,.65);
}}

/* ── Accent card variants ────────────────────────────────────── */
.card-blue   {{ border-top: 3px solid var(--blue);   }}
.card-indigo {{ border-top: 3px solid var(--indigo); }}
.card-green  {{ border-top: 3px solid var(--green);  }}
.card-amber  {{ border-top: 3px solid var(--amber);  }}
.card-red    {{ border-top: 3px solid var(--red);    }}

/* ── Buttons ─────────────────────────────────────────────────── */
.btn {{
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  border-radius: var(--radius);
  font-family: var(--font);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background var(--transition), box-shadow var(--transition),
              transform var(--transition), border-color var(--transition);
  text-decoration: none;
  white-space: nowrap;
}}
.btn:active {{ transform: scale(0.97); }}

.btn-primary {{
  background: var(--blue);
  color: #fff;
}}
.btn-primary:hover {{
  background: #2563eb;
  box-shadow: 0 0 0 3px rgba(59,130,246,.35);
}}

.btn-outline {{
  background: transparent;
  color: var(--text);
  border-color: var(--border);
}}
.btn-outline:hover {{
  background: var(--card);
  border-color: var(--slate-lt);
}}

.btn-ghost {{
  background: transparent;
  color: var(--muted);
  border: none;
}}
.btn-ghost:hover {{
  color: var(--text);
  background: var(--card);
}}

/* ── Form Controls ───────────────────────────────────────────── */
input, select, textarea {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-family: var(--font);
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
  width: 100%;
  transition: border-color var(--transition), box-shadow var(--transition);
  outline: none;
}}
input::placeholder, textarea::placeholder {{ color: var(--muted); }}
input:focus, select:focus, textarea:focus {{
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(59,130,246,.2);
}}

input[type="range"] {{
  appearance: none;
  background: var(--border);
  border: none;
  border-radius: 9999px;
  height: 5px;
  padding: 0;
  cursor: pointer;
}}
input[type="range"]::-webkit-slider-thumb {{
  appearance: none;
  background: var(--blue);
  border-radius: 50%;
  height: 16px;
  width: 16px;
  transition: background var(--transition);
}}
input[type="range"]::-webkit-slider-thumb:hover {{
  background: var(--indigo);
}}

label {{
  color: var(--muted);
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 0.35rem;
}}

/* ── Navigation ──────────────────────────────────────────────── */
nav {{
  background: rgba(9,9,11,.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding-block: 1rem;
  position: sticky;
  top: 0;
  z-index: 100;
}}

nav .nav-link {{
  color: var(--muted);
  font-weight: 500;
  text-decoration: none;
  padding: 0.35rem 0.75rem;
  border-radius: var(--radius-sm);
  transition: color var(--transition), background var(--transition);
}}
nav .nav-link:hover,
nav .nav-link.active {{
  color: var(--text);
  background: var(--card);
}}

/* ── Badges / Tags ───────────────────────────────────────────── */
.badge {{
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.4;
}}
.badge-blue   {{ background: rgba(59,130,246,.15); color: var(--blue); }}
.badge-indigo {{ background: rgba(99,102,241,.15); color: var(--indigo); }}
.badge-green  {{ background: rgba(34,197,94,.15);  color: var(--green); }}
.badge-amber  {{ background: rgba(245,158,11,.15); color: var(--amber); }}
.badge-red    {{ background: rgba(239,68,68,.15);  color: var(--red); }}

/* ── Tables ──────────────────────────────────────────────────── */
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}}
th {{
  background: var(--card);
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.6rem 1rem;
  text-align: left;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
}}
td {{
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}}
tr:hover td {{ background: rgba(255,255,255,.03); }}
.best-result {{ color: var(--green); font-weight: 700; }}

/* ── Progress / Metric bars ──────────────────────────────────── */
.progress-track {{
  background: var(--border);
  border-radius: 9999px;
  height: 8px;
  overflow: hidden;
  width: 100%;
}}
.progress-fill {{
  background: linear-gradient(90deg, var(--blue), var(--indigo));
  border-radius: 9999px;
  height: 100%;
  transition: width 600ms cubic-bezier(.4,0,.2,1);
}}

/* ── Code blocks ─────────────────────────────────────────────── */
pre, code {{
  font-family: var(--font-mono);
  font-size: 0.85em;
}}
code {{
  background: var(--border);
  border-radius: 4px;
  padding: 0.15em 0.45em;
  color: var(--blue);
}}
pre {{
  background: #111113;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
  padding: 1.25rem 1.5rem;
  line-height: 1.7;
  color: var(--text);
}}
pre code {{
  background: none;
  border-radius: 0;
  padding: 0;
  color: inherit;
}}

/* Syntax-highlight tokens (used when Prism / highlight.js not available) */
.token-keyword  {{ color: var(--indigo); }}
.token-string   {{ color: var(--green); }}
.token-comment  {{ color: var(--muted); font-style: italic; }}
.token-number   {{ color: var(--amber); }}
.token-function {{ color: var(--blue); }}

/* ── Hero section ────────────────────────────────────────────── */
.hero {{
  background: radial-gradient(ellipse 80% 60% at 50% -10%,
              rgba(99,102,241,.25), transparent);
  padding-block: 6rem 4rem;
  text-align: center;
}}

/* ── Tabs ────────────────────────────────────────────────────── */
.tabs {{
  display: flex;
  gap: 0.25rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.25rem;
}}
.tab {{
  flex: 1;
  padding: 0.45rem 1rem;
  border-radius: calc(var(--radius) - 2px);
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-family: var(--font);
  font-size: 0.875rem;
  font-weight: 500;
  transition: background var(--transition), color var(--transition);
}}
.tab:hover   {{ color: var(--text); }}
.tab.active  {{
  background: var(--bg);
  color: var(--text);
  box-shadow: 0 1px 4px rgba(0,0,0,.4);
}}

.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

/* ── Tooltip ─────────────────────────────────────────────────── */
[data-tooltip] {{ position: relative; cursor: default; }}
[data-tooltip]::after {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  content: attr(data-tooltip);
  font-size: 0.78rem;
  left: 50%;
  padding: 0.4rem 0.7rem;
  pointer-events: none;
  position: absolute;
  bottom: calc(100% + 8px);
  transform: translateX(-50%);
  white-space: nowrap;
  opacity: 0;
  transition: opacity var(--transition);
  z-index: 200;
}}
[data-tooltip]:hover::after {{ opacity: 1; }}

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar               {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track         {{ background: var(--bg); }}
::-webkit-scrollbar-thumb         {{ background: var(--border); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover   {{ background: var(--slate); }}

/* ── Utilities ───────────────────────────────────────────────── */
.text-center {{ text-align: center; }}
.text-right  {{ text-align: right; }}
.text-blue   {{ color: var(--blue); }}
.text-indigo {{ color: var(--indigo); }}
.text-green  {{ color: var(--green); }}
.text-amber  {{ color: var(--amber); }}
.text-red    {{ color: var(--red); }}
.text-muted  {{ color: var(--muted); }}
.mt-1 {{ margin-top: 0.5rem; }}
.mt-2 {{ margin-top: 1rem; }}
.mt-3 {{ margin-top: 1.5rem; }}
.mt-4 {{ margin-top: 2rem; }}
.mb-1 {{ margin-bottom: 0.5rem; }}
.mb-2 {{ margin-bottom: 1rem; }}
.mb-3 {{ margin-bottom: 1.5rem; }}
.mb-4 {{ margin-bottom: 2rem; }}
.hidden {{ display: none !important; }}

/* ── Responsive breakpoints ──────────────────────────────────── */
/* xs: <480px  sm: <640px  md: <768px  lg: <1024px  xl: ≥1024px */

@media (max-width: 1024px) {{
  .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
}}

@media (max-width: 768px) {{
  .grid-2,
  .grid-3 {{ grid-template-columns: 1fr; }}
  .grid-4 {{ grid-template-columns: 1fr; }}
  .hero   {{ padding-block: 4rem 2.5rem; }}
  .section {{ padding-block: 2.5rem; }}
  nav      {{ padding-inline: 1rem; }}
  .tabs    {{ flex-direction: column; }}
}}

@media (max-width: 480px) {{
  .container {{ padding-inline: 1rem; }}
  .card      {{ padding: 1rem; }}
  h1         {{ font-size: 1.5rem; }}
  h2         {{ font-size: 1.2rem; }}
  .btn       {{ width: 100%; justify-content: center; }}
}}
"""
