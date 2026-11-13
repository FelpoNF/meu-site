#!/usr/bin/env python3
"""Verification for the Byline Studio site.

There is no build step and no test framework: the page is one static
index.html with the CSS and the JS inline. This script is the closest thing
to a suite, so it drives a real headless Chrome and measures the rendered
page instead of trusting the source.

Run from anywhere:
    python3 verify.py

Needs Python 3, Chrome, and Node (for the inline-script syntax check; that
one check is skipped, and said so, when node is missing).
Exits 0 when everything passes, 1 otherwise.
"""
import os, re, shutil, subprocess, sys, tempfile, pathlib

SITE = pathlib.Path(__file__).resolve().parent


def find_chrome():
    """Chrome moves around, and this script should not care where."""
    for c in (os.environ.get("CHROME_PATH"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              shutil.which("google-chrome"),
              shutil.which("chromium"),
              shutil.which("chrome")):
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome not found. Point CHROME_PATH at the Chrome binary.")


CHROME = find_chrome()
HAVE_NODE = shutil.which("node") is not None
html = (SITE / "index.html").read_text(encoding="utf-8")
priv = (SITE / "privacy.html").read_text(encoding="utf-8")
ok = fail = 0

def chk(name, cond, detail=""):
    global ok, fail
    ok, fail = ok + (1 if cond else 0), fail + (0 if cond else 1)
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else f"  — {detail}"))

# --- copy ---
chk("call length is 30 minutes everywhere",
    "Pick a 30-minute slot" in html and "30-minute call:" in html and "20-minute" not in html)
chk("calendar sits in the finale, section intact",
    'class="wrap finale-grid"' in html
    and "Let's make your first product." in html
    and 'class="cal-art"' in html
    and "Write to us with two times that do" in html)
chk("calendar css scoped, no global --paper override",
    ".cal-art{" in html and ".cal-day.today{" in html and "--cal-paper" in html)
chk("calendar js present", 'id="calGrid"' in html and "scheduleMidnight" in html)
chk("email is the gmail address",
    'const EMAIL        = "studiobyline@gmail.com"' in html
    and "studiobyline@gmail.com" in priv
    and "hello@bylineeditions.com" not in html + priv)
chk("money signature line gone",
    "The agreement is the document" not in html and 'class="sig"' not in html and ".money .sig" not in html)
chk("card says created for your audience",
    "created for your audience, and waiting for your announcement" in html)
chk("card no longer says proven with your audience", "proven with your audience" not in html)
chk("formats heading intact", "<h2>Seven products, so you know what we're capable of.</h2>" in html)
chk("no kicker/eyebrow", not re.search(r'class="eyebrow"|\.eyebrow\b', html + priv))
chk("one h1", html.count("<h1") == 1)
body = re.sub(r"<!--.*?-->", "", html.split("<script>")[0], flags=re.S)
chk("no em dash in page copy", "\u2014" not in body)
chk("money sentence uses a comma", "who owns what, all of it is written down" in html)
chk("hero note removed",
    "We take on a small number of creators at a time" not in html and "hero-note" not in html)
chk("hero headline is 10% bigger", "clamp(2.89rem,6.47vw,5.43rem)" in html)

# --- process ---
steps = html.split('<ol class="steps">')[1].split("</ol>")[0]
chk("process has 3 steps", steps.count("<li>") == 3, steps.count("<li>"))
chk("audience-test step gone", "We test it with your audience" not in html)
chk("no audience-validation promise left",
    not re.search(r"slice of your audience|Who sees it before", html))
chk("count line updated", "two of the three" in html)
chk("steps grid is 3 columns", "repeat(3,1fr);gap:0;counter-reset:s" in html)
chk("faq heading comes before the list", html.index("What creators ask first") < html.index('class="faq-list"'))
chk("faq two-column grid removed", "faq-grid" not in html)

# --- scripts ---
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="hermes-verify-"))
all_parse = True
if HAVE_NODE:
    for i, body in enumerate(scripts):
        f = tmp / f"s{i}.js"
        f.write_text(body, encoding="utf-8")
        if subprocess.run(["node", "--check", str(f)], capture_output=True).returncode != 0:
            all_parse = False
    chk(f"all {len(scripts)} inline scripts parse", all_parse)
else:
    print(f"SKIP  all {len(scripts)} inline scripts parse (node not installed)")

# --- live behaviour ---
PROBE = """<script>
const E=[];addEventListener("error",e=>E.push(e.message));
addEventListener("load",()=>{const lis=[...document.querySelector(".steps").children];
const lefts=lis.map(l=>Math.round(l.getBoundingClientRect().left));
const fq=document.querySelector(".faq h2"),fl=document.querySelector(".faq-list");
const gap=Math.round(fl.getBoundingClientRect().top-fq.getBoundingClientRect().bottom);
const heroPct=Math.round(document.querySelector(".hero").getBoundingClientRect().height/innerHeight*100);
const h1=document.querySelector("h1"),h1cs=getComputedStyle(h1),h1r=h1.getBoundingClientRect();
const h1lines=Math.round(h1r.height/parseFloat(h1cs.lineHeight)), h1fs=parseFloat(h1cs.fontSize).toFixed(1);
const wr=document.querySelector(".faq .wrap").getBoundingClientRect();
const gapL=Math.round(fl.getBoundingClientRect().left-wr.left);
const gapR=Math.round(wr.right-fl.getBoundingClientRect().right);
const aligned=gapL===gapR?1:0;
document.title=[document.documentElement.clientWidth,lis.length,lefts.join(","),
[...document.querySelectorAll("body *")].filter(e=>!e.closest("#stage,#ring,.veil")&&e.getBoundingClientRect().right>document.documentElement.clientWidth+1).length,
E.length,document.querySelectorAll(".spine").length,
document.querySelector("[data-primary]").textContent.trim(),gap,aligned,gapL,h1lines,h1fs,heroPct,
document.querySelectorAll(".cal-day").length,
(document.querySelector(".cal-day.today")||{}).textContent||"none",
Math.round(document.querySelector(".cal-art").getBoundingClientRect().width)].join("|");});
</script>"""
pf = tmp / "p.html"
pf.write_text(html.replace("</body>", PROBE + "</body>"), encoding="utf-8")

for w, want in ((1440, "158,522,886"), (1100, "skip"), (1000, "skip"), (981, "skip"), (1024, "24,496,24"), (600, None), (489, None)):
    out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
                          f"--window-size={w},1200", "--dump-dom", pf.as_uri()],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    m = re.search(r"<title>([^<]*)</title>", out)
    if not m:
        chk(f"{w}px probe ran", False, "no output"); continue
    (_, n, lefts, over, err, spines, cta, fqgap, fqalign, gapL,
     h1lines, h1fs, heroPct, caldays, caltoday, calw) = m.group(1).split("|")
    stacked = len(set(lefts.split(","))) == 1
    chk(f"{w}px: 3 steps", n == "3", n)
    if want != "skip":
        chk(f"{w}px: columns placed correctly",
            stacked if want is None else lefts == want, f"{lefts} vs {want or 'one column'}")
    chk(f"{w}px: no overflow", over == "0", over)
    chk(f"{w}px: no JS errors", err == "0", err)
    chk(f"{w}px: 7 spines + CTA", spines == "7" and cta == "Email us", f"{spines}/{cta}")
    chk(f"{w}px: faq heading sits above the list", int(fqgap) > 0, f"gap={fqgap}")
    chk(f"{w}px: faq lines symmetric with the walls", fqalign == "1", f"left gap {gapL} vs right gap mismatch")
    chk(f"{w}px: hero headline on 2 lines", h1lines == "2", f"{h1lines} lines at {h1fs}px")
    if w >= 981:
        chk(f"{w}px: hero fills ~90% of the screen", 88 <= int(heroPct) <= 92, f"{heroPct}%")
    chk(f"{w}px: calendar renders 42 cells", caldays == "42", caldays)
    chk(f"{w}px: calendar marks today", caltoday.isdigit(), caltoday)
    chk(f"{w}px: calendar fits its column", 280 <= int(calw) <= 370, calw)

# --- header: brand left, links centred, CTA right ---
chk("whatsapp button swaps in over a ghost fallback",
    'class="btn wpp" data-wa' in html and 'data-wa-fallback' in html
    and "const WHATSAPP" in html and "https://wa.me/" in html)
chk("document asks not to be cached",
    'http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"' in html)
chk("whatsapp button is green", "#25D366" in html)
chk("colour ribbon is back above the footer",
    html.count('class="ribbon"') == 1 and html.count("<i></i>") == 7
    and html.index('class="ribbon"') < html.index('<footer class="site">'))
chk("logo lockup is the big one", "font-size:1.9rem" in html and "brand:hover .brand-mark" not in html)
chk("hover targets books, not the svg",
    '.brand-mark path{transform-box:fill-box' in html and 'link.addEventListener("mousemove"' in html)
chk("logo is the five-book mark, header and stage copies only",
    html.count('class="brand-mark"') == 2 and html.count('fill="#8FC1E8"') == 2
    and 'class="mark"' not in html and html.index('class="brand-mark"') < html.index('<header class="top"'))
_mark = html[html.index('class="brand-mark"'):]
_mark = _mark[:_mark.index('</svg>')]
_fills = re.findall(r'<path[^>]*fill="(#[0-9A-Fa-f]{6})"', _mark)
chk("logo has all five books",
    len(_fills) == 5 and len(set(_fills)) == 5, f"{len(_fills)} paths, {len(set(_fills))} distinct: {_fills}")
chk("wordmark takes the cobalt", ".brand .bw-st{color:#2B4EFF}" in html)
chk("one blue only: no stray #2F5BEA", "2F5BEA" not in html.upper())
chk("brand reads Byline Studio everywhere",
    "Byline Editions" not in html + priv + (SITE / "README.md").read_text(encoding="utf-8"))
chk("wordmark uses Inter 800", "family=Inter:wght@800" in html and '"Inter"' in html)
fav = (SITE / "favicon.svg").read_text(encoding="utf-8")
chk("favicon is the five-book mark, transparent",
    fav.count("<path") == 5 and fav.count("<rect") == 1
    and all(c in fav for c in ("#2B4EFF", "#F4A21F", "#1B2A4A", "#8FC1E8", "#E8472B"))
    and "fill=\"#FFFFFF\"" not in fav and "fill=\"#ffffff\"" not in fav)
chk("page references the favicon", 'rel="icon" href="favicon.svg?v=3" type="image/svg+xml"' in html)
chk("apple-touch-icon is wired and 180px",
    'rel="apple-touch-icon" href="apple-touch-icon.png"' in html + priv
    and (SITE / "apple-touch-icon.png").stat().st_size > 1000)
chk("header CTA sits outside the link group",
    'class="btn small nav-cta"' in html and '<a class="btn small" data-cta' not in html)
chk("header uses a three-track grid", "grid-template-columns:1fr auto 1fr" in html)

NAV = """<script>window.addEventListener("load",function(){
var w=document.querySelector(".nav").getBoundingClientRect();
var n=document.querySelector(".nav-links").getBoundingClientRect();
var c=document.querySelector(".nav-cta");
document.title="NAV|"+Math.round(w.left+w.width/2)+"|"+Math.round(n.left+n.width/2)+"|"+
Math.round(c.getBoundingClientRect().right)+"|"+Math.round(w.right-parseFloat(getComputedStyle(document.querySelector(".nav")).paddingRight))+"|"+(getComputedStyle(c).display!=="none");});
</script>"""
navf = tmp / "nav.html"
navf.write_text(html.replace("</body>", NAV + "</body>"), encoding="utf-8")
for w in (1440, 1024, 489):
    out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
                          f"--window-size={w},800", "--dump-dom", navf.as_uri()],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    m = re.search(r"<title>NAV\|(-?\d+)\|(-?\d+)\|(\d+)\|(\d+)\|(true|false)</title>", out)
    if not m:
        chk(f"{w}px nav probe", False, "no output"); continue
    wm, nm, ctaR, wrapR, vis = m.groups()
    if w > 860:
        chk(f"{w}px: nav group is centred", abs(int(wm) - int(nm)) <= 2, f"wrap mid {wm} vs nav mid {nm}")
    chk(f"{w}px: CTA anchored right", abs(int(ctaR) - int(wrapR)) <= 2, f"cta {ctaR} vs wrap {wrapR}")
    chk(f"{w}px: CTA stays visible", vis == "true", vis)

# --- whatsapp button: hidden without a number, wired with one ---
WA = """<script>window.addEventListener("load",function(){
var a=document.querySelector("[data-wa]");
document.title="WA|"+(a.hidden?"hidden":"shown")+"|"+(a.getAttribute("href")||"")+"|"+getComputedStyle(a).backgroundColor;});
</script>"""
waf = tmp / "wa.html"
waf.write_text(html.replace("</body>", WA + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
                      "--window-size=1440,900", "--dump-dom", waf.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>WA\|(\w+)\|([^|]*)\|([^<]*)</title>", out)
if m:
    state, href, bg = m.groups()
    chk("whatsapp button is green in the page", bg.strip() == "rgb(37, 211, 102)", bg)
    if 'const WHATSAPP     = ""' in html:
        chk("no number set: ghost CTA stays", state == "hidden", state)
    else:
        chk("whatsapp links to wa.me with prefilled text", href.startswith("https://wa.me/") and "text=" in href, href)
else:
    chk("whatsapp probe ran", False, "no output")

# --- ribbon geometry ---
RIB = """<script>window.addEventListener("load",function(){
var r=document.querySelector(".ribbon").getBoundingClientRect();
var f=document.querySelector("footer.site").getBoundingClientRect();
var segs=[].slice.call(document.querySelectorAll(".ribbon i")).map(function(i){return Math.round(i.getBoundingClientRect().width)});
document.title="RIB|"+Math.round(r.height)+"|"+Math.round(r.width)+"|"+Math.round(f.top-r.bottom)+"|"+segs.join(",");});
</script>"""
ribf = tmp / "rib.html"
ribf.write_text(html.replace("</body>", RIB + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
                      "--window-size=1440,900", "--dump-dom", ribf.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>RIB\|(\d+)\|(\d+)\|(\d+)\|([\d,]+)</title>", out)
if m:
    rh, rw, gap, segs = m.groups()
    widths = [int(x) for x in segs.split(",")]
    chk("ribbon is a thin 10px band", rh == "10", rh)
    chk("ribbon runs full width", int(rw) >= 1000, rw)
    chk("ribbon sits flush on the footer", gap == "0", gap)
    chk("ribbon has 7 equal segments", len(widths) == 7 and max(widths) - min(widths) <= 1, segs)
else:
    chk("ribbon probe ran", False, "no output")

# --- one cobalt, painted: wordmark, first book and ribbon segment 1 ---
COB = """<script>window.addEventListener("load",function(){
var st=document.querySelector(".brand .bw-st");
var bk=document.querySelector(".brand-mark path");
var s1=document.querySelector(".ribbon i");
document.title="COB|"+getComputedStyle(st).color+"|"+bk.getAttribute("fill")+"|"+getComputedStyle(s1).backgroundColor;
});</script>"""
cobf = tmp / "cob.html"
cobf.write_text(html.replace("</body>", COB + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
                      "--window-size=1440,900", "--dump-dom", cobf.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>COB\|([^|]*)\|([^|]*)\|([^<]*)</title>", out)
if m:
    st_c, bk_c, s1_c = (x.strip() for x in m.groups())
    chk("wordmark paints the cobalt", st_c == "rgb(43, 78, 255)", st_c)
    chk("first logo book is the cobalt", bk_c.upper() == "#2B4EFF", bk_c)
    chk("ribbon segment 1 is the cobalt", s1_c == "rgb(43, 78, 255)", s1_c)
else:
    chk("cobalt probe ran", False, "no output")

# --- logo hover: shelf still, books rise by proximity ---
HOV = """<script>window.addEventListener("load",function(){setTimeout(function(){
var mark=document.querySelector(".top .brand-mark"), link=document.querySelector(".top .brand");
var books=[].slice.call(mark.querySelectorAll("path")), shelf=mark.querySelector("rect");
var t=books[1].getBoundingClientRect(), x=t.left+t.width/2;
link.dispatchEvent(new MouseEvent("mousemove",{bubbles:true,clientX:x,clientY:200}));
var lifts=books.map(function(b){var m=b.style.transform.match(/(-?[0-9.]+)px/);return m?Math.abs(parseFloat(m[1])):0;});
var shelfMoved=!!shelf.style.transform, svgMoved=!!mark.style.transform;
link.dispatchEvent(new MouseEvent("mouseleave",{bubbles:true}));
var cleared=books.every(function(b){return !b.style.transform;});
document.title="HOV|"+lifts.map(function(v){return v.toFixed(1)}).join(",")+"|"+shelfMoved+"|"+svgMoved+"|"+cleared;
},90)});</script>"""
hov = tmp / "hov.html"
hov.write_text(html.replace("</body>", HOV + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=5000",
                      "--window-size=1440,900", "--dump-dom", hov.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>HOV\|([\d.,]+)\|(\w+)\|(\w+)\|(\w+)</title>", out)
if m:
    lifts, shelf_moved, svg_moved, cleared = m.groups()
    vals = [float(v) for v in lifts.split(",")]
    chk("hover: books lift", sum(1 for v in vals if v > 0) >= 3, lifts)
    chk("hover: closest book lifts most", vals[1] == max(vals), lifts)
    chk("hover: lifts differ book to book", len(set(round(v, 1) for v in vals)) >= 3, lifts)
    chk("hover: shelf never moves", shelf_moved == "false" and svg_moved == "false", f"{shelf_moved}/{svg_moved}")
    chk("hover: resets on mouseleave", cleared == "true", cleared)
else:
    chk("logo hover probe ran", False, "no output")

# --- FAQ accordion: opening one closes the previous ---
ACC = """<script>window.addEventListener("load",function(){
var d=[].slice.call(document.querySelectorAll(".faq-list details"));
d[0].querySelector("summary").click();
setTimeout(function(){
  var a=document.querySelectorAll(".faq-list details[open]").length;
  d[1].querySelector("summary").click();
  setTimeout(function(){
    var b=document.querySelectorAll(".faq-list details[open]").length;
    d[1].querySelector("summary").click();
    setTimeout(function(){
      var c=document.querySelectorAll(".faq-list details[open]").length;
      document.title="ACC|"+a+"|"+b+"|"+c;
    },900);
  },900);
},900);});</script>"""
acc = tmp / "acc.html"
acc.write_text(html.replace("</body>", ACC + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=9000",
                      "--window-size=1440,1000", "--dump-dom", acc.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>ACC\|(\d+)\|(\d+)\|(\d+)</title>", out)
if m:
    a, b, c = m.groups()
    chk("faq: first answer opens", a == "1", a)
    chk("faq: opening another closes the previous", b == "1", f"{b} open at once")
    chk("faq: clicking the open one closes it", c == "0", c)
else:
    chk("faq accordion probe ran", False, "no output")


# --- intro: curtain before paint, exact landing, escape hatch, reduced motion ---
chk("intro curtain is armed in the head",
    'sessionStorage.getItem("byline-intro")' in html and 'd.classList.add("intro")' in html
    and html.index('sessionStorage.getItem("byline-intro")') < html.index("<body>"))
chk("no intro on the privacy page", 'id="stage"' not in priv and "byline-intro" not in priv)
chk("stage repeats the header's five books, not a second drawing",
    html.count('fill="#2E3A55"') == 2 and html.count("data-fall=") == 5)
chk("intro speaks the site palette", "2F60E3" not in html.upper() and "F5A623" not in html.upper())

INTRO = """<script>
(function(){
  var out={}, t0=Date.now(), done=false;
  function read(){
    var st=document.querySelector("#stage .brand"), nv=document.querySelector(".top .brand");
    var sr=st.getBoundingClientRect(), nr=nv.getBoundingClientRect(), pg=document.getElementById("page");
    out.intro=document.documentElement.classList.contains("intro");
    out.stageH=Math.round(sr.height);
    out.ratio=(sr.width/sr.height).toFixed(3);
    out.navRatio=(nr.width/nr.height).toFixed(3);
    out.navHidden=getComputedStyle(nv).visibility;
    var mk=st.querySelector(".brand-mark").getBoundingClientRect();
    var sg=document.getElementById("stage").getBoundingClientRect();   // the stage is the visible box
    out.iconOff=Math.round(Math.abs((mk.left+mk.width/2)-(sg.left+sg.width/2)));
    out.word=getComputedStyle(st.querySelector(".bw-st")).color;
    out.clip=getComputedStyle(pg).clipPath||"none";
    out.inert=!!pg.inert;
  }
  function after(){
    if(done) return; done=true;
    var pg=document.getElementById("page");
    out.afterIntro=document.documentElement.classList.contains("intro");
    out.afterClip=getComputedStyle(pg).clipPath||"none";
    out.afterNav=getComputedStyle(document.querySelector(".top .brand")).visibility;
    out.afterInert=!!pg.inert;
    out.stored=sessionStorage.getItem("byline-intro");
    var kv=[]; for(var k in out) kv.push(k+"="+out[k]);
    document.title="INTRO|"+kv.join(";");
  }
  function landing(){
    var st=document.querySelector("#stage .brand").getBoundingClientRect();
    var nv=document.querySelector(".top .brand").getBoundingClientRect();
    out.dLeft=Math.round(st.left-nv.left); out.dTop=Math.round(st.top-nv.top);
    out.dW=Math.round(st.width-nv.width); out.dH=Math.round(st.height-nv.height);
  }
  (function wait(){
    if(window.bylineIntro&&window.bylineIntro.ready){
      read();
      window.bylineIntro.seek(4500);            // past the flight: where does it actually end up?
      setTimeout(function(){ landing(); window.bylineIntro.skip(); setTimeout(after,300); }, 160);
      return;
    }
    if(Date.now()-t0>6000){ out.error="intro never became ready"; after(); return; }
    setTimeout(wait,50);
  })();
})();
</script>"""
f = tmp / "intro.html"
f.write_text(html.replace("</body>", INTRO + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=14000",
                      "--window-size=1440,900", "--dump-dom", f.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>INTRO\|([^<]*)</title>", out)
if m:
    d = dict(kv.split("=", 1) for kv in m.group(1).split(";") if "=" in kv)
    chk("curtain is up on a first load", d.get("intro") == "true", d.get("error", ""))
    chk("stage lockup is big", d.get("stageH", "0").isdigit() and int(d.get("stageH", 0)) >= 100, d.get("stageH"))
    chk("stage and nav lockups share proportions (landing cannot distort)",
        abs(float(d.get("ratio", 0)) - float(d.get("navRatio", 1))) <= 0.01,
        f"{d.get('ratio')} vs {d.get('navRatio')}")
    chk("nav logo waits for the flight", d.get("navHidden") == "hidden", d.get("navHidden"))
    chk("the icon sits centred while it is alone on screen",
        d.get("iconOff", "999").isdigit() and int(d.get("iconOff", 999)) <= 2, f"{d.get('iconOff')}px off")
    chk("intro wordmark paints the cobalt", d.get("word") == "rgb(43, 78, 255)", d.get("word"))
    chk("page starts clipped to the corner", d.get("clip", "none").startswith("circle(0px"), d.get("clip"))
    chk("page is inert behind the curtain", d.get("inert") == "true", d.get("inert"))
    chk("the flight lands exactly on the nav slot",
        all(d.get(k, "99").lstrip("-").isdigit() and abs(int(d.get(k, 99))) <= 1
            for k in ("dLeft", "dTop", "dW", "dH")),
        f"dx={d.get('dLeft')} dy={d.get('dTop')} dw={d.get('dW')} dh={d.get('dH')}")
    chk("skip reveals the page", d.get("afterIntro") == "false" and d.get("afterClip") == "none", d.get("afterClip"))
    chk("skip un-hides the nav logo", d.get("afterNav") == "visible", d.get("afterNav"))
    chk("skip makes the page focusable again", d.get("afterInert") == "false", d.get("afterInert"))
    chk("the session is marked as seen", d.get("stored") == "1", d.get("stored"))
else:
    chk("intro probe ran", False, "no title")

RM = """<script>window.addEventListener("load",function(){setTimeout(function(){
var d=document.documentElement, pg=document.getElementById("page");
document.title="RM|"+d.classList.contains("intro")+"|"+(getComputedStyle(pg).clipPath||"none")+"|"+
getComputedStyle(document.querySelector(".top .brand")).visibility+"|"+!!window.bylineIntro;},400);});</script>"""
frm = tmp / "intro-rm.html"
frm.write_text(html.replace("</body>", RM + "</body>"), encoding="utf-8")
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--force-prefers-reduced-motion",
                      "--virtual-time-budget=6000", "--window-size=1440,900", "--dump-dom", frm.as_uri()],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
m = re.search(r"<title>RM\|(\w+)\|([^|]*)\|(\w+)\|(\w+)</title>", out)
if m:
    rm_intro, rm_clip, rm_nav, rm_hook = m.groups()
    chk("reduced motion: no curtain at all", rm_intro == "false" and rm_clip == "none", f"{rm_intro}/{rm_clip}")
    chk("reduced motion: nav logo is just there", rm_nav == "visible", rm_nav)
    chk("reduced motion: hook still defined", rm_hook == "true", rm_hook)
else:
    chk("reduced motion probe ran", False, "no title")

print(f"\n{ok} passed, {fail} failed")
if fail:
    print(f"probe files kept for inspection: {tmp}")
else:
    shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fail else 0)
