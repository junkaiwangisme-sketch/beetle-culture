"""Build the complete GitHub Pages site. Run with python3 build.py."""
from collections import Counter
from pathlib import Path
from html import escape
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
def read(filename):
    return json.loads((ROOT / filename).read_text(encoding='utf-8'))
def write(filename, content):
    (ROOT / filename).write_text(content, encoding='utf-8')
def e(value):
    return escape(str(value), quote=True)
def words(items):
    return sorted(items, key=lambda item: item['name'].casefold())
config = read('catalog.json')
BASE = config['url'].rstrip('/') + '/'
groups = {item['slug']: item for item in config['groups']}
guides = words(config['species'])
photos = config['photos']
pages = []
files = {item['file'] for item in photos}
if len(groups) != len(config['groups']):
    raise ValueError('Duplicate group slug')
for key in ('name', 'slug'):
    values = [s[key].strip().casefold() for s in guides]
    if len(values) != len(set(values)):
        raise ValueError('Duplicate species ' + key)
for item in [*guides, *groups.values()]:
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', item['slug']):
        raise ValueError('Invalid slug ' + item['slug'])
for s in guides:
    if s['group'] not in groups or not s['sections'] or not s['sources']:
        raise ValueError('Check the group, sections and sources for ' + s['name'])
for p in photos:
    if not p.get('alt') or not (ROOT / p['file']).is_file():
        raise ValueError('Check image and alt text for ' + p['file'])

def glink(s): return 'group-' + s + '.html'
def slink(s): return 'species-' + s['slug'] + '.html'
def named(s): return s.get('common') or s['name']
def srcs(s): return ''.join('<li><a href="%s">%s</a></li>' % (e(a['url']), e(a['title'])) for a in s['sources'])
def link(url,label): return '<a href="%s">%s</a>' % (e(url),e(label))
def getphotos(s):
    return [p for p in photos if p.get('species','').casefold()==s['name'].casefold()]
def image(p,lazy=True):
    return '<img src="%s" alt="%s"%s%s%s>' % (e(p['file']),e(p['alt']),' loading="lazy"' if lazy else ' fetchpriority="high"',' width="%s"' % int(p['width']) if p.get('width') else '', ' height="%s"' % int(p['height']) if p.get('height') else '')
def cred(p):
    credit=link(p['url'],p.get('credit') or 'Photograph source') if p.get('url') else e(p.get('credit',''))
    if p.get('license_url'): credit += ' · ' + link(p['license_url'],p['license'])
    elif p.get('license'): credit += ' · ' + e(p['license'])
    return credit
def page(file,title,desc,body,kind='WebPage',photo=None,active=None,article=None):
    full=BASE+('' if file=='index.html' else file)
    data={'@context':'https://schema.org','@type':kind,'url':full,'name':title,'description':desc,'inLanguage':'en'}
    if article:
        data.update(headline=title,about={'@type':'Thing','name':article['name']},isPartOf={'@type':'WebSite','name':'Beetle Culture','url':BASE})
    if photo: data['image']=BASE+photo['file']
    def nav(url,label,key,cls=''):
        return f'<a href="{url}" class="{cls}"'+(' aria-current="page"' if active==key else '')+'>'+label+'</a>'
    top='<a class="skip" href="#main">Skip to content</a><header><div class="wrap bar"><a class="brand" href="index.html" aria-label="Beetle Culture home"><span class="crest" aria-hidden="true">B</span> Beetle Culture</a><nav aria-label="Main navigation">'+nav('groups.html','Families','groups')+nav('species.html','Species','species')+nav('species.html#query','<span class="glass" aria-hidden="true"></span><span class="sr">Search guides</span><span class="searchtext" aria-hidden="true">Search</span>','search','searchlink')+'</nav></div></header>'
    foot='<footer class="footer"><div class="wrap foot"><span class="brand">Beetle Culture</span><div class="footlinks">'+link('groups.html','Family directory')+link('species.html','Species index')+link('credits.html','Sources & photography')+link('https://www.instagram.com/beetlescholar/','@beetlescholar')+'</div></div></footer>'
    og=(f'<meta property="og:image" content="{e(BASE+photo["file"])}"><meta property="og:image:alt" content="{e(photo["alt"])}">' if photo else '')
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    write(file,f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} | Beetle Culture</title><meta name="description" content="{e(desc)}"><meta name="theme-color" content="#153a2c"><link rel="canonical" href="{e(full)}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="{"article" if article else "website"}"><meta property="og:url" content="{e(full)}">{og}<link rel="stylesheet" href="style.css"><script type="application/ld+json">{payload}</script></head><body>{top}<main id="main">{body}</main>{foot}</body></html>')
    pages.append(full)
def crumbs(items):
    return '<nav class="crumb" aria-label="Breadcrumb">'+link('index.html','Home')+''.join(' <span aria-hidden="true">/</span> '+(link(u,t) if u else e(t)) for u,t in items)+'</nav>'
def intro(title,desc,path,kicker='',italic=''):
    return '<div class="intro"><div class="wrap">'+crumbs(path)+(f'<div class="kicker">{e(kicker)}</div>' if kicker else '')+f'<h1 class="page-title">{e(title)}</h1>'+(f'<div class="sciname">{e(italic)}</div>' if italic else '')+(f'<p class="lead">{e(desc)}</p>' if desc else '')+'</div></div>'
def group_rows():
    counts=Counter(s['group'] for s in guides)
    chunks=[]
    for k,g in groups.items():
        count=counts[k]
        chunks.append(f'<a class="row" href="{glink(k)}"><span><span class="subtag">{e(g["rank"])}</span><span class="rowtitle">{e(g["name"])}</span><span class="row-sub">{e(g["common"])}</span></span><span class="row-end">{count} guide{"s" if count!=1 else ""} <span aria-hidden="true">↗</span></span></a>')
    return '<div class="groups">'+''.join(chunks)+'</div>'
def card(s):
    pics=getphotos(s)
    return f'<a class="guide{"" if pics else " textcard"}" href="{slink(s)}">'+(f'<span class="image">{image(pics[0])}</span>' if pics else '')+f'<span class="kicker">{e(groups[s["group"]]["name"])}</span><strong>{e(named(s))}</strong><em>{e(s["name"])}</em></a>'
def listed(s):
    group=groups[s['group']]
    terms=' '.join([s['name'],s.get('common',''),group['name'],group['common'],*group.get('aliases',[]),*s.get('aliases',[])])
    common=s.get('common')
    return f'<a class="row indexrow" data-group="{s["group"]}" data-terms="{e(terms.casefold())}" href="{slink(s)}"><span><span class="rowtitle"><em>{e(s["name"])}</em></span>'+ (f'<span class="row-sub">{e(common)}</span>' if common else '')+f'</span><span class="row-end">{e(group["name"])} <span aria-hidden="true">↗</span></span></a>'
def galleryfig(p):
    return f'<figure class="articlepic"><a href="{e(p["file"])}">{image(p)}</a><figcaption>{e(p.get("caption") or p["alt"])} · {cred(p)}</figcaption></figure>'
hero=next((p for p in photos if p.get('hero')),photos[0] if photos else None)
owner=next((s for s in guides if hero and s['name']==hero.get('species')),None)
visual=''
if hero:
    visual=f'<figure class="hero-figure"><a href="{slink(owner) if owner else "credits.html"}">{image(hero,False)}</a><figcaption>{e(hero.get("species") or hero.get("caption") or "Beetle photography")}</figcaption></figure>'
selected=[]
for s in [s for s in guides if getphotos(s)]+guides:
    if len(selected)<3 and all(o['group']!=s['group'] for o in selected): selected.append(s)
home=f'<section class="hero"><div class="hero-inner"><div class="hero-copy"><span class="eyebrow">A breeder’s field guide</span><h1>Beetle <em>Culture</em></h1><p>Explore beetle breeding through species guides, rearing notes, and photographs.</p><a class="cta" href="groups.html">Browse beetle families <span class="arrow" aria-hidden="true">↗</span></a></div>{visual}</div></section>'
home+='<section class="wrap block home-index" id="families"><div class="section-head"><div><h2>Explore by family</h2><p class="section-note">Choose a family or scarab subfamily to find its species guides.</p></div></div>'+group_rows()+'</section><section class="wrap block"><div class="section-head"><h2>Species in focus</h2><a class="more" href="species.html">All species ↗</a></div><div class="guidegrid">'+''.join(card(s) for s in selected)+'</div></section>'
page('index.html','Beetle breeding guides and photography','Explore beetle breeding by family and species, with photographs, larval care, adult diets, and documented rearing observations.',home,'WebSite',hero)
page('groups.html','Beetle family directory','Browse beetle breeding guides by family and scarab subfamily.',intro('Family directory','Choose a group to open its species guides.',[(None,'Families')])+'<section class="wrap block">'+group_rows()+'</section>','CollectionPage',active='groups')
for k,g in groups.items():
    items=[s for s in guides if s['group']==k]
    desc=g['description']
    body=intro(g['name'],desc,[('groups.html','Families'),(None,g['name'])],g['rank']+(' · Scarabaeidae' if g['rank']=='Subfamily' else '')+' · '+g['common'])
    body+='<section class="wrap block"><div class="section-head"><h2>Species guides</h2></div>'+''.join(listed(s) for s in items)+'</section>'
    page(glink(k),g['name']+' breeding guides',desc,body,'CollectionPage',active='groups')
for s in guides:
    g=groups[s['group']]; name=s['name']; common=s.get('common',''); ps=getphotos(s)
    body=intro(common or name,s['intro'],[('groups.html','Families'),(glink(s['group']),g['name']),(None,name)],g['name']+' · Species guide',name if common else '')
    parts=[];toc=[]
    for i,item in enumerate(s['sections'],1):
        anchor='section-'+str(i)
        toc.append('<li>'+link('#'+anchor,item['title'])+'</li>')
        text=''.join('<p>'+e(t)+'</p>' for t in item['text'].split('\n') if t.strip())
        parts.append(f'<section id="{anchor}"><h2>{e(item["title"])}</h2>{text}</section>')
    body+='<div class="wrap article-layout"><article class="article">'+(galleryfig(ps[0]) if ps else '')+''.join(parts)
    if len(ps)>1: body+='<section><h2>Photographs</h2><div class="gallery">'+''.join(galleryfig(p) for p in ps[1:])+'</div></section>'
    body+='<section id="sources"><h2>Sources</h2><ul class="sources">'+srcs(s)+'</ul></section></article><aside class="toc"><div class="onthis">In this guide</div><ol>'+''.join(toc)+'<li>'+link('#sources','Sources')+'</li></ol>'+link(glink(s['group']),'All '+g['name']+' guides')+'</aside></div>'
    page(slink(s),((common+' ('+name+')') if common else name)+' breeding guide',s['intro'],body,'Article',ps[0] if ps else None,article=s)
opts=''.join(f'<option value="{k}">{e(g["name"])}</option>' for k,g in groups.items())
body=intro('Species index','Find a breeding guide by scientific name, common name, or beetle family.',[(None,'Species')])
body+=f'<section class="wrap block"><form class="filters" id="filterForm" hidden><label>Search species<input id="query" name="q" type="search" placeholder="e.g. Hercules, Lucanus, or flower beetle"></label><label>Family or subfamily<select id="group" name="group"><option value="">All groups</option>{opts}</select></label></form><p class="results" id="count" role="status">{len(guides)} species guides</p><div id="listing">'+''.join(listed(s) for s in guides)+'</div><p id="empty" class="noresults" hidden>No guides match your search. <button id="clear" type="button">Clear filters</button></p></section><script src="search.js" defer></script>'
page('species.html','Search beetle species guides','Search the breeding guide directory by scientific name, common name, and family.',body,'CollectionPage',active='species')
creditbody=intro('Sources & photography','Sources appear on each species guide. Photographs are credited individually below.',[(None,'Sources & photography')])+'<div class="wrap article-layout"><article class="article"><section><h2>Breeding collections</h2><ul class="sources"><li>'+link('https://junkaiwangisme.wixsite.com/usbeetlebreeding','US Beetle Breeding by Junkai Wang')+'</li><li>'+link('https://junkaiwangisme.wixsite.com/website-1','Junkai Wang’s Wix collection')+'</li><li>'+link('https://www.instagram.com/beetlescholar/','@beetlescholar on Instagram')+'</li></ul></section><section><h2>Photograph credits</h2><ul class="sources">'+''.join('<li><i>'+e(p.get('species',''))+'</i> · '+cred(p)+'</li>' for p in photos)+'</ul></section><section><h2>Family names</h2><p>Dynastinae, Rutelinae, and Cetoniinae are treated as subfamilies of Scarabaeidae. You can also find the flower chafers by searching for Cetoniidae.</p><ul><li>'+link('https://coleopsoc.org/resources/suborders-series-superfamilies-families-and-subfamilies/','The Coleopterists Society classification')+'</li></ul></section></article></div>'
page('credits.html','Sources and photograph credits','Sources and image attributions for the Beetle Culture breeding guide.',creditbody)
sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for url in pages: ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=url
write('sitemap.xml',ET.tostring(sitemap,encoding='unicode'))
write('robots.txt','User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n')
print(f'Built {len(pages)} pages for {len(guides)} species, {len(groups)} groups, {len(photos)} images.')
