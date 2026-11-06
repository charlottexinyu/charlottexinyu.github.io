"""Build the AI for Business journal directory from verified paper records."""
import argparse
import html
import json
import posixpath
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlparse

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "研究地图/网站"
OUT = WEB / "首页设计稿"
PAPERS_PATH = WEB / "设计样本.json"
COVERAGE_PATH = WEB / "检索覆盖.json"
JOURNALS_PATH = ROOT / "研究地图/标准与审核/AI_for_Business期刊范围_2026-11.md"
PAPERS = []
FIELDS = {
    "finance": ("Finance", "金融", "企业价值、资产定价、信贷与金融中介"),
    "accounting": ("Accounting", "会计", "审计、信息披露与财务报告"),
    "strategy": ("Strategy", "战略", "战略评估、竞争与企业决策"),
    "marketing": ("Marketing", "营销", "消费者、广告、推荐与市场测量"),
    "information-systems": ("Information Systems", "信息系统", "平台、人机协作与数字工作"),
    "management": ("Management", "管理", "组织、工作设计与技术采用"),
    "entrepreneurship": ("Entrepreneurship", "创业", "创业机会、新创企业与创新"),
    "operations": ("Operations Management", "运营管理", "需求预测、库存与补货、产能与排程、服务运营和供应链决策"),
    "economics": ("Economics & Policy", "经济与政策", "劳动、生产率、市场与政策"),
    "cs-econ": ("CS & Economics", "计算与经济", "计算机制、市场设计与激励"),
}
LEGACY = {"FIN":"finance","ACC":"accounting","MKT":"marketing","IS":"information-systems","MGT/STRAT/ENT":"management","OM/SC":"operations","ECON/POLICY":"economics","CS_ECON":"cs-econ"}
AS_OF = date.today()
COUNTS = Counter()
def esc(x):
    return html.escape(str(x or ""), quote=True)

def link(url, label, attrs=""):
    return f'<a href="{esc(url)}" {attrs}>{label}</a>'

def external(url, label):
    if urlparse(url or "").scheme not in ("http", "https"):
        return esc(label)
    return link(url, esc(label), 'rel="noopener noreferrer" target="_blank"')

def fieldpath(k):
    return f"fields/{k}.html"

def paperpath(p):
    return f'papers/{p["id"]}.html'

def rel(page, target):
    return posixpath.relpath(target, posixpath.dirname(page) or ".")

def write(path, body):
    dest = OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")

def nav(page, active):
    def item(target, label, tag, count=None):
        current = ' aria-current="page"' if tag == active else ""
        return link(rel(page, target), f'<span>{esc(label)}</span>'+ (f'<b>{count}</b>' if count is not None else ''),f'class="nav-item"{current}')
    first = item("index.html","研究统计","home")+item("papers/index.html","全部论文","papers",len(PAPERS))+item("fields/index.html","学科索引","fields")
    categories = "".join(item(fieldpath(k), val[0], k, COUNTS[k]) for k,val in FIELDS.items())
    return f'<nav aria-label="主要页面"><div class="nav-group">{first}</div><div class="nav-group"><p class="nav-title">学科目录</p>{categories}</div><div class="nav-group">{item("about.html","数据与口径","about")}</div></nav>'

def layout(page, active, title, trail, body):
    brand=link(rel(page,"index.html"),"AI for Business",'class="wordmark"')
    navbar=nav(page,active)
    crumbs=" / ".join(link(rel(page,x),esc(t)) if x else esc(t) for t,x in trail)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · AI for Business</title><link rel="stylesheet" href="{rel(page,"assets/site.css")}"><script defer src="{rel(page,"assets/site.js")}"></script></head><body><a class="skip" href="#main">跳到正文</a><header class="mobile">{brand}<details class="mobile-nav"><summary>目录</summary>{navbar}</details></header><div class="shell"><aside class="sidebar">{brand}<p class="site-caption">商学研究文献库</p>{navbar}</aside><main class="content" id="main"><div class="crumbs" aria-label="当前位置">{crumbs}</div>{body}<footer class="foot">AI for Business · 论文目录更新于 {AS_OF.year} 年 {AS_OF.month} 月 {AS_OF.day} 日　{link(rel(page,"about.html"),"收录口径")}</footer></main></div></body></html>'''

def head(title, note="", scope=""):
    return f'<header class="page-head"><h1>{esc(title)}</h1>'+ (f'<p class="lede">{esc(note)}</p>' if note else "")+(f'<p class="scope">{esc(scope)}</p>' if scope else "")+'</header>'

def sections(title, content):
    return f'<section class="record-section"><h2>{esc(title)}</h2>{content}</section>'

def row(page,p):
    authors=" · ".join(a["name"] for a in p["authors"])
    attrs={"title":p["title"].lower(),"author":authors.lower(),"year":p["date"][:4],"category":p["category"],"topic":p["topic"],"venue":p["venue"],"method":p["method"]}
    data=" ".join(f'data-{k}="{esc(v)}"' for k,v in attrs.items())
    title_link=link(rel(page,paperpath(p)),esc(p["title"]),'class="paper-title" lang="en"')
    return f'<article class="paper-row" {data}><span class="year-stamp">{esc(p["date"][:4])}</span><div>{title_link}<p class="byline">{esc(authors)}</p><p class="source"><em>{esc(p["venue"])}</em>　{esc(FIELDS[p["category"]][1])}</p></div></article>'

def rows(page,papers):
    return '<div class="paper-list">'+''.join(row(page,p) for p in papers)+'</div>'

def directory_link(**params):
    return "papers/index.html?"+urlencode(params)

def ranklist(key):
    counts=Counter(p[key] for p in PAPERS)
    if key == "category":
        for category in FIELDS:
            counts.setdefault(category, 0)
    parts=[]
    for name,n in sorted(counts.items(),key=lambda x:(-x[1],x[0])):
        label=FIELDS[name][1] if key=="category" else name
        target=fieldpath(name) if key=="category" else directory_link(**{key:name})
        parts.append(link(target,f'<span class="label">{esc(label)}</span><span class="track"><i style="width:{100*n/max(counts.values()):.1f}%"></i></span><b>{n}</b>','class="rank"'))
    if key in ("topic", "method") and len(parts) > 8:
        return ('<div class="rank-list">'+''.join(parts[:8])+'</div><details>'
                +f'<summary>其余 {len(parts)-8} 项</summary><div class="rank-list">'
                +''.join(parts[8:])+'</div></details>')
    return '<div class="rank-list">'+''.join(parts)+'</div>'

def homepage():
    yearcounts=Counter(int(p['date'][:4]) for p in PAPERS)
    cols=[]
    for year in range(2020, AS_OF.year + 1):
        n=yearcounts[year]
        h=100*n/max(yearcounts.values())
        cols.append(link(directory_link(year=year),f'<span class="num">{n if n else "—"}</span><i class="col" style="--h:{h:.1f}%"></i><span class="year">{year}</span>',f'class="year-col {"zero" if not n else ""}" style="--h:{h:.1f}%" aria-label="{year} 年，已收录 {n} 篇"'))
    metrics=[(len(PAPERS),"篇已收录论文","papers/index.html"),(len({p["venue"] for p in PAPERS}),"本有收录的期刊","about.html#journals"),(len(COUNTS),"个已有收录的学科","fields/index.html")]
    stats='<div class="stats">'+''.join('<div>'+link(url,f'<strong>{n}</strong><span>{label}</span>')+'</div>' for n,label,url in metrics)+'</div>'
    body=head("AI 商学研究","2020 年以来，商学期刊里的 AI 研究关注哪些问题？","UTD24 与 FT50 · 51 本目标期刊 · 持续回溯中")+stats
    body+='<p class="note">图中统计已核实并收录的论文。各期刊和年份的筛查进度不同，点击图表可查看对应论文。 <a href="about.html#coverage">查看逐刊检索进度</a>。</p>'
    body+='<div class="chart-pair"><section class="chart-block"><h2>按发表年份</h2><p>期刊首次正式在线的年份，单位为篇。</p><div class="year-chart">'+''.join(cols)+f'</div><small>— 表示该年暂无收录。{AS_OF.year} 年截至 {AS_OF.month} 月 {AS_OF.day} 日。</small></section>'
    body+='<section class="chart-block"><h2>按学科</h2><p>按主要研究问题归类。0 表示本库暂未收录该学科论文。</p>'+ranklist("category")+'</section></div>'
    body+='<div class="chart-pair"><section class="chart-block"><h2>研究关注什么？</h2><p>根据作者摘要归纳的主要商业问题。</p>'+ranklist("topic")+'</section>'
    body+='<section class="chart-block"><h2>怎样研究这些问题？</h2><p>按摘要中可辨认的主要研究方法分类。</p>'+ranklist("method")+'</section></div>'
    return layout("index.html","home","研究统计",[("首页",None)],body)

def fieldpages():
    cards=[]
    for k,(en,zh,desc) in FIELDS.items():
        page=fieldpath(k)
        papers=[p for p in PAPERS if p["category"]==k]
        body=head(f"{en} · {zh}",desc,f"本页已收录 {len(papers)} 篇论文")
        body+=rows(page,papers) if papers else '<p class="empty">本学科的论文待补。后续按目标期刊目录回溯，论文核实后列在这里。</p>'
        write(page,layout(page,k,en,[("首页","index.html"),("学科索引","fields/index.html"),(en,None)],body))
        cards.append(link(f"{k}.html",f'<span class="field-title">{esc(en)} · {esc(zh)}</span><span class="field-desc">{esc(desc)}</span><b>{COUNTS[k]}</b>','class="field"'))
    page="fields/index.html"
    write(page,layout(page,"fields","学科索引",[("首页","index.html"),("学科索引",None)],head("学科索引","选择一个学科，阅读相关 AI 论文。")+ '<div class="field-list">'+''.join(cards)+'</div>'))

def paperpages():
    for p in PAPERS:
        page=paperpath(p); k=p["category"]; pub=p["publication"]
        authors=' · '.join(external(a.get("url"),a["name"])+(f'（{esc(a["affiliation"])}）' if a.get("affiliation") else "") for a in p["authors"])
        conferences=''.join('<li>'+external(c.get("url"),c["name"])+(f' · {esc(c["year"])}' if c.get("year") else "")+'</li>' for c in p["conferences"])
        materials=''.join('<li>'+external(a.get("url"),a["label"])+'</li>' for a in p["links"])
        wp=[a for a in p["links"] if a.get("kind") in ("wp","working_paper","preprint")]
        pubtext=external(pub.get("url"),p["venue"])+" · 正式在线 "+external(p.get("dateSource"),p["date"])+''.join(' · '+external(a["url"],a["label"]) for a in wp)
        body=head(p["title"],p["topic"])
        body+=sections("期刊与工作论文","<p>"+pubtext+"</p>")+sections("会议经历","<ul>"+conferences+"</ul>" if conferences else '<p>尚无已核实的会议记录。</p>')
        body+=sections("作者信息","<p>"+authors+"</p>")
        body+=sections("作者摘要要点","<ul>"+''.join("<li>"+esc(s)+"</li>" for s in p["abstract_points"])+"</ul><p>"+external(p["abstract_source_url"],p.get("abstractVersion") or "作者摘要原文")+"</p>")
        body+=sections("文章与公开演示","<ul>"+materials+"</ul>"+('' if any(a.get("kind") in ('slides','poster','video','presentation') for a in p['links']) else '<p class="scope">公开演示材料待补。</p>'))
        body+='<details class="note"><summary>研究方法归类 · '+esc(p["method"])+'</summary><p>'+esc(p["methodBasis"])+'</p></details>'
        body+='<p class="back-link">'+link(rel(page,fieldpath(k)),"← 返回 "+esc(FIELDS[k][0]))+'</p>'
        write(page,layout(page,k,p["title"],[("首页","index.html"),(FIELDS[k][0],fieldpath(k)),("论文",None)],body))

def catalogue():
    page="papers/index.html"
    keys=[("year","年份",[str(y) for y in range(AS_OF.year, 2019, -1)]),("category","学科",FIELDS.keys()),("topic","主题",sorted({p["topic"] for p in PAPERS})),("method","方法",sorted({p["method"] for p in PAPERS})),("venue","期刊",sorted({p["venue"] for p in PAPERS}))]
    form='<form class="filters" id="filters"><label>题名或作者<input name="q" type="search" placeholder="搜索文献"></label>'
    for key,label,opts in keys:
        form+=f'<label>{label}<select name="{key}"><option value="">全部</option>'+''.join(f'<option value="{esc(v)}">{esc(FIELDS[v][0] if key=="category" else v)}</option>' for v in opts)+'</select></label>'
    form+='<button type="reset">清除筛选</button></form>'
    body=head("全部论文","按期刊正式在线日期倒序排列。")+form+f'<p id="matches" role="status">共 {len(PAPERS)} 篇</p>'+rows(page,PAPERS)+'<p id="noMatches" class="empty" hidden>该条件下暂无收录，可以更改或清除筛选。</p>'
    write(page,layout(page,"papers","全部论文",[("首页","index.html"),("全部论文",None)],body))

def coverage_section():
    coverage = json.loads(COVERAGE_PATH.read_text())
    journals = coverage["journals"]
    indexed = sum(j["status"] == "indexed" for j in journals)
    total = sum(j["indexed"] for j in journals)
    abstracts = sum(j["with_abstract"] for j in journals)
    hits = sum(j["hits"] for j in journals)
    summary = (f'截至 {esc(coverage["through"])}，对 51 种期刊发起了题录检索。'
               f'其中 {indexed} 刊取回了与索引返回总数一致的登记题录。共取得 {total:,} 条题录，'
               f'其中 {abstracts:,} 条含可检索摘要。题名或摘要命中关键词的 {hits:,} 条进入候选筛查。')
    rows = []
    for j in journals:
        status = "题录已取回" if j["status"] == "indexed" else "题录待补查"
        numbers = [f'{j[k]:,}' if j["indexed"] else "—" for k in ("indexed","with_abstract","hits")]
        rows.append("<tr><td>"+esc(j["name"])+"</td><td>"+status+"</td>"+ "".join("<td>"+n+"</td>" for n in numbers)+"</tr>")
    grid = ('<details><summary>查看 51 种期刊</summary><div class="coverage-table"><table><thead><tr>'
            '<th>期刊</th><th>检索状态</th><th>登记题录</th><th>有摘要</th><th>词项命中</th></tr></thead><tbody>'
            + "".join(rows)+"</tbody></table></div></details>")
    return ('<section id="coverage" class="record-section"><h2>期刊检索进度</h2><p>'+summary+'</p>'
            '<p>题录来自 Crossref，检索窗自 2020 年 1 月 1 日开始，按索引登记的发表日期取回。'
            '网页论文另据出版方的正式在线日期归年。只查到题名时容易漏掉以具体应用命名的 AI 研究。'
            '期刊目录、在线优先文章和候选论文仍在逐项核查。表中横线表示尚无可用题录数。</p>'
            '<p>另查 <a href="https://hbr.org/archive-toc">Harvard Business Review 官方目录</a>，2020 年至 2026 年 11–12 月刊共 42 期、769 条目录记录，其中 68 条题名含显式 AI 词项。最近一期的文章仍须逐条核实截至日，网络独发与实践文章的筛选另行记录。此处期次记录未计入上面的 Crossref 数字。</p>'
            '<p>MIT Sloan Management Review 的索引题录较少，<a href="https://sloanreview.mit.edu/issue/">官网期次档案</a>部分分页暂时无法核实。管理与运营期刊中，缺少摘要的题录仍需对照官网补查。</p>'+grid+'</section>')

def about():
    page="about.html"
    body=head("数据与口径","如何阅读这个目录和首页图表。")
    venues=[l.split("|")[2].strip() for l in JOURNALS_PATH.read_text().splitlines() if re.match(r"^\| \d+ \|",l)]
    assert len(venues)==51
    body+=sections("期刊范围","<p>将 2026 年 4 月版 FT50 与 UTD24 合并，两份名单共有 23 本重合期刊，去重后共 51 本。采用这份固定名单回溯 2020 年至今，按首次正式在线的年份计数。工作论文和会议经历归入同一研究的详情。</p><details><summary>查看全部 51 本目标期刊</summary><ol>"+''.join('<li>'+esc(s)+'</li>' for s in venues)+'</ol></details>')
    body+=sections("样本与分类","<p>图表的分母是本库已核实收录的独立论文。回溯期间，同一学科或年份仍会补入较早发表的论文。每篇论文按研究问题归入一个学科，并依据作者摘要标注一个主要主题和一种研究方法。论文页附摘要来源与方法归类依据。</p>")
    body += coverage_section()
    counts=Counter(p["venue"] for p in PAPERS)
    body+='<section class="record-section" id="journals"><h2>已收录论文来自哪些期刊</h2><ul>'+''.join('<li>'+link(directory_link(venue=v),esc(v))+f' · {n} 篇</li>' for v,n in counts.most_common())+'</ul></section>'
    body+=sections("页面设计","<p>学科目录与摘要链接参考 "+external("https://aipapers.wiki/","AI Papers Atlas")+"，统计图到论文的阅读路径参考 "+external("https://empirical-economics-of-ai.vercel.app/visualize","The Empirical Economics of AI")+"。侧栏索引与面包屑布局参考 "+external("https://github.com/just-the-docs/just-the-docs","Just the Docs（GitHub，MIT）")+"。本站使用独立编写的静态页面和样式。</p>")
    write(page,layout(page,"about","数据与口径",[("首页","index.html"),("数据与口径",None)],body))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=AS_OF, help="Website data cutoff (YYYY-MM-DD)")
    parser.add_argument("--papers", type=Path, default=PAPERS_PATH)
    parser.add_argument("--coverage", type=Path, default=COVERAGE_PATH)
    parser.add_argument("--journals", type=Path, default=JOURNALS_PATH)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    AS_OF = args.as_of
    COVERAGE_PATH = args.coverage
    JOURNALS_PATH = args.journals
    OUT = args.output
    PAPERS = sorted(json.loads(args.papers.read_text()), key=lambda p: p["date"], reverse=True)
    for paper in PAPERS:
        paper["category"] = paper.get("category") or LEGACY[paper["domain"]]
        assert paper["category"] in FIELDS and re.fullmatch(r"[a-z0-9-]+", paper["id"])
    assert len({p["id"] for p in PAPERS}) == len(PAPERS)
    COUNTS = Counter(p["category"] for p in PAPERS)
    if any(date.fromisoformat(p["date"]) > AS_OF for p in PAPERS):
        parser.error("Data cutoff precedes a paper in the catalogue")
    fieldpages()
    paperpages()
    catalogue()
    about()
    write("index.html",homepage())

