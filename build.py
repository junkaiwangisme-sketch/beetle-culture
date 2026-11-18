"""Build the complete GitHub Pages site. Run with python3 build.py."""
from collections import Counter
from pathlib import Path
from html import escape
from urllib.parse import urlsplit
import json
import hashlib
import re
import argparse
import shutil
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
by_slug = {record['slug']: record for record in config['species']}
for path in sorted(ROOT.glob('post-*.json')):
    record = read(path.name)
    if path.name != 'post-' + record['slug'] + '.json':
        raise ValueError('Post filename does not match its slug: ' + path.name)
    by_slug[record['slug']] = record
guides = words(by_slug.values())
scientific_names=sorted({record['name'] for record in guides},key=len,reverse=True)
name_pattern=re.compile(r'(?<![A-Za-z])('+'|'.join(map(re.escape,scientific_names))+r')(?![A-Za-z])')
def prose(text):
    return name_pattern.sub(lambda m:'<i>'+m.group(0)+'</i>',e(text))
photos = list(config['photos'])
for record in guides:
    for picture in record.get('additional_photos', []):
        photos.append({**picture, 'species':record['name']})
pages = []
files = {item['file'] for item in photos} | {f['file'] for f in config.get('substrate',{}).get('photos',[])}
for record in guides:
    distribution=record.get('distribution',{})
    for key in ('file','data_file'):
        filename=distribution.get(key)
        if filename:
            if Path(filename).name != filename or not (ROOT/filename).is_file():
                raise ValueError('Missing or invalid distribution file: '+filename)
            files.add(filename)
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
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.(jpg|jpeg|png|webp|avif)',p['file'],re.I) or not p.get('alt') or not (ROOT / p['file']).is_file():
        raise ValueError('Check image and alt text for ' + p['file'])

def glink(s): return 'group-' + s + '.html'
def slink(s): return 'species-' + s['slug'] + '.html'
def named(s): return s.get('common') or s['name']
def public_reference(url):
    host=(urlsplit(url).hostname or '').casefold()
    return host not in ('discord.com','discordapp.com','junkaiwangisme.wixsite.com') and not host.endswith('.discord.com')
def srcs(s): return ''.join('<li><a href="%s">%s</a></li>' % (e(a['url']), e(a['title'])) for a in s['sources'] if public_reference(a['url']))
def link(url,label): return '<a href="%s">%s</a>' % (e(url),e(label))
def getphotos(s):
    pictures = [p for p in photos if p.get('species', '').casefold() == s['name'].casefold()]
    # Keep the original sequence within each group and use a verified adult as the lead.
    return sorted(pictures, key=lambda p: (p.get('stage') != 'Adults', not p.get('preferred')))
def image(p,lazy=True):
    return '<img src="%s" alt="%s"%s%s%s>' % (e(p['file']),e(p['alt']),' loading="lazy"' if lazy else ' fetchpriority="high"',' width="%s"' % int(p['width']) if p.get('width') else '', ' height="%s"' % int(p['height']) if p.get('height') else '')
def cred(p):
    credit=link(p['url'],p.get('credit') or 'Photograph source') if p.get('url') else e(p.get('credit',''))
    if p.get('license_url'): credit += ' · ' + link(p['license_url'],p['license'])
    elif p.get('license'): credit += ' · ' + e(p['license'])
    return credit
def asset(filename):
    version=hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()[:10]
    return filename+'?v='+version

def page(file,title,desc,body,kind='WebPage',photo=None,active=None,article=None):
    for js in ('search.js','editor.js','editor-data.js'):
        if f'src="{js}"' in body:
            body=body.replace(f'src="{js}"', f'src="{asset(js)}"')
    full=BASE+('' if file=='index.html' else file)
    data={'@context':'https://schema.org','@type':kind,'url':full,'name':title,'description':desc,'inLanguage':'en'}
    if article and article.get('primary_url') and public_reference(article['primary_url']):
        data['citation'] = article.get('primary_url')
    if article:
        data.update(headline=title,about={'@type':'Thing','name':article['name']},isPartOf={'@type':'WebSite','name':'North American Beetle Breeding','url':BASE})
    if photo: data['image']=BASE+photo['file']
    def nav(url,label,key,cls=''):
        return f'<a href="{url}" class="{cls}"'+(' aria-current="page"' if active==key else '')+'>'+label+'</a>'
    top='<a class="skip" href="#main">Skip to content</a><header><div class="wrap bar"><a class="brand" href="index.html" aria-label="North American Beetle Breeding home"><span class="crest" aria-hidden="true">B</span> North American Beetle Breeding</a><nav aria-label="Main navigation">'+nav('groups.html','Families','groups')+nav('species.html','Species','species')+nav('substrate.html','Substrate','substrate')+nav('about.html','About me','about')+nav('species.html#query','<span class="glass" aria-hidden="true"></span><span class="sr">Search guides</span><span class="searchtext" aria-hidden="true">Search</span>','search','searchlink')+'</nav></div></header>'
    foot='<footer class="footer"><div class="wrap foot"><span class="brand">North American Beetle Breeding</span><div class="footlinks">'+link('groups.html','Family directory')+link('species.html','Species index')+link('credits.html','References')+link('substrate.html','Substrate')+link('about.html','About me')+link('editor.html','Manage posts')+'</div></div></footer>'
    og=(f'<meta property="og:image" content="{e(BASE+photo["file"])}"><meta property="og:image:alt" content="{e(photo["alt"])}">' if photo else '')
    stylesheet=asset('style.css')
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    write(file,f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} | North American Beetle Breeding</title><meta name="description" content="{e(desc)}"><meta name="theme-color" content="#080908"><link rel="canonical" href="{e(full)}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="{"article" if article else "website"}"><meta property="og:url" content="{e(full)}">{og}<link rel="stylesheet" href="{stylesheet}"><script type="application/ld+json">{payload}</script></head><body>{top}<main id="main">{body}</main>{foot}</body></html>')
    pages.append(full)
def crumbs(items):
    return '<nav class="crumb" aria-label="Breadcrumb">'+link('index.html','Home')+''.join(' <span aria-hidden="true">/</span> '+(link(u,t) if u else e(t)) for u,t in items)+'</nav>'
def intro(title,desc,path,kicker='',italic=''):
    return '<div class="intro"><div class="wrap">'+crumbs(path)+(f'<div class="kicker">{e(kicker)}</div>' if kicker else '')+f'<h1 class="page-title">{e(title)}</h1>'+(f'<div class="sciname">{e(italic)}</div>' if italic else '')+(f'<p class="lead">{prose(desc)}</p>' if desc else '')+'</div></div>'
def group_rows():
    counts=Counter(s['group'] for s in guides)
    chunks=[]
    for k,g in groups.items():
        count=counts[k]
        cover = next((p for p in photos if p.get('group')==k and not p.get('species')), None) or next((p for p in photos if any(s['group'] == k and s['name'] == p.get('species') for s in guides)), None)
        thumbnail = '<span class="family-thumb">' + image(cover) + '</span>' if cover else ''
        chunks.append(f'<a class="row familyrow" href="{glink(k)}">{thumbnail}<span class="familylabel"><span class="subtag">{e(g["rank"])}</span><span class="rowtitle">{e(g["name"])}</span><span class="row-sub">{e(g["common"])}</span></span><span class="row-end">{count} guide{"s" if count!=1 else ""} <span aria-hidden="true">↗</span></span></a>')
    return '<div class="groups">'+''.join(chunks)+'</div>'
def card(s):
    pics=getphotos(s)
    common=f'<span class="card-common">{e(s["common"])}</span>' if s.get('common') else ''
    return f'<a class="guide{"" if pics else " textcard"}" href="{slink(s)}">'+(f'<span class="image">{image(pics[0])}</span>' if pics else '')+f'<span class="kicker">{e(groups[s["group"]]["name"])}</span><strong><i>{e(s["name"])}</i></strong>{common}</a>'

def listed(s):
    group=groups[s['group']]
    terms=' '.join([s['name'],s.get('common',''),group['name'],group['common'],*group.get('aliases',[]),*s.get('aliases',[])])
    common=s.get('common')
    return f'<a class="row indexrow" data-group="{s["group"]}" data-terms="{e(terms.casefold())}" href="{slink(s)}"><span><span class="rowtitle"><em>{e(s["name"])}</em></span>'+ (f'<span class="row-sub">{e(common)}</span>' if common else '')+f'</span><span class="row-end">{e(group["name"])} <span aria-hidden="true">↗</span></span></a>'
def classification(references):
    if not references: return ''
    return '<section class="classification"><h2>Classification</h2><ul class="sources">'+''.join('<li>'+link(r['url'],r['title'])+'</li>' for r in references)+'</ul></section>'

def galleryfig(p, lead=False):
    caption = e(p.get('caption') or p['alt'])
    if p.get('show_credit'):
        caption += ' · ' + cred(p)
    return f'<figure class="articlepic"><a href="{e(p["file"])}">{image(p, lazy=not lead)}</a><figcaption>{caption}</figcaption></figure>'
hero=next((p for p in photos if p.get('hero')),photos[0] if photos else None)
owner=next((s for s in guides if hero and s['name']==hero.get('species')),None)
visual=''
if hero:
    visual=f'<figure class="hero-figure"><a href="{slink(owner) if owner else "credits.html"}">{image(hero,False)}</a><figcaption><i>{e(hero.get("species") or hero.get("caption") or "Beetle photography")}</i></figcaption></figure>'
home=f'<section class="hero"><div class="hero-inner"><div class="hero-copy"><span class="eyebrow">Coleoptera · Life history</span><h1>North American <em>Beetle Breeding</em></h1><p>Captive breeding records and photographs, with observations on oviposition, larval substrates, and adult emergence.</p><a class="cta" href="groups.html">Browse beetle families <span class="arrow" aria-hidden="true">↗</span></a></div>{visual}</div></section>'
def browse_form():
    return '<form class="filters" id="filterForm" hidden><label>Search species<input id="query" name="q" type="search" placeholder="Scientific or common name"></label><label>Family or subfamily<select id="group" name="group"><option value="">All groups</option>'+''.join(f'<option value="{key}">{e(group["name"])}</option>' for key,group in groups.items())+'</select></label></form>'
def browse_list(compact=False):
    limit=' data-initial-limit="5"' if compact else ''
    button='<button type="button" class="more" id="show-all" hidden>Show all species</button>' if compact else ''
    return browse_form()+f'<p id="count" class="results" role="status">{len(guides)} species guides</p><div id="listing"{limit}>'+''.join(listed(s) for s in guides)+'</div>'+button+'<p id="empty" class="noresults" hidden>No species match your search. <button id="clear" type="button">Clear filters</button></p><script src="search.js" defer></script>'
home+='<section class="wrap block home-index" id="families"><div class="section-head"><h2>Explore by family</h2></div>'+group_rows()+'</section><section class="wrap block" id="browse-species"><div class="section-head"><h2>Browse by species</h2><a class="more" href="species.html">Species index ↗</a></div>'+browse_list(True)+'</section>'

page('index.html','Beetle breeding guides and photography','Explore beetle breeding by family and species, with photographs, larval care, adult diets, and documented rearing observations.',home,'WebSite',hero)
if any(record.get('distribution') for record in guides):
    method_intro=intro('Mapping methods','North American occurrence records and the treatment of geographic outliers.',[(None,'Mapping methods')])
    method_body='<div class="wrap block"><article class="article"><section><h2>Observations</h2><p>Each species map uses wild, research-grade, georeferenced observations in the iNaturalist North America place, including Mexico, Central America and the Caribbean. Points represent public observation coordinates. Locations can overlap. Sampling intensity varies, and gaps between observations do not establish absence.</p></section><section><h2>Location precision</h2><p>Filled symbols indicate unobscured public locations with a reported uncertainty of 10 km or less. Open symbols indicate an obscured location or a larger or unknown uncertainty. The public coordinate is retained for obscured records.</p></section><section><h2>Outlier review</h2><p>We grouped observations in 0.25° latitude–longitude cells. A cell with one or two records was flagged when its center was at least 500 km from every other occupied cell for that species. Flagged records were checked against taxonomic and geographic sources. The species data file lists each reviewed observation and the reason for retaining or excluding it.</p></section><section><h2>Map projection</h2><p>Figures use an Albers equal-area conic projection with standard parallels at 20° and 50° N and Natural Earth boundaries. The scale bar and geographic extent are shown on each figure.</p></section></article></div>'
    page('distribution.html','Distribution mapping methods','Data selection, positional uncertainty and outlier decisions for the beetle occurrence maps.',method_intro+method_body)
page('groups.html','Beetle family directory','Browse beetle breeding guides by family and scarab subfamily.',intro('Family directory','Choose a group to open its species guides.',[(None,'Families')])+'<section class="wrap block">'+group_rows()+'</section>','CollectionPage',active='groups')
for k,g in groups.items():
    items=[s for s in guides if s['group']==k]
    desc=g['description']
    body=intro(g['name'],desc,[('groups.html','Families'),(None,g['name'])],g['rank']+(' · Scarabaeidae' if g['rank']=='Subfamily' else '')+' · '+g['common'])
    body+='<section class="wrap block"><div class="section-head"><h2>Species guides</h2></div><div class="guidegrid">'+''.join(card(s) for s in items)+'</div></section>'
    body += '<div class="wrap classlinks">'+classification(g.get('classification',[]))+'</div>'
    page(glink(k),g['name']+' breeding guides',desc,body,'CollectionPage',active='groups')
for s in guides:
    g=groups[s['group']]; name=s['name']; common=s.get('common',''); ps=getphotos(s)
    body=intro(name,s['intro'],[('groups.html','Families'),(glink(s['group']),g['name']),(None,name)],g['name']+' · Species account',common).replace('class="page-title"','class="page-title species-title"').replace('class="sciname"','class="common-name"')
    if s.get('account_credit'):
        body += '<div class="wrap account-credit"><p>'+e(s['account_credit'])+'</p></div>'
    facts = s.get('facts', [])
    summary = ('<section class="facts"><h2>Life-history data</h2><dl class="factlist">'+''.join('<div><dt>'+e(x['title'])+'</dt><dd>'+e(x['text'])+'</dd></div>' for x in facts)+'</dl></section>') if facts else ''
    parts=[];toc=[]
    for i,item in enumerate(s['sections'],1):
        anchor='section-'+str(i)
        toc.append('<li>'+link('#'+anchor,item['title'])+'</li>')
        text=''.join('<p>'+prose(t)+'</p>' for t in item['text'].split('\n') if t.strip())
        parts.append(f'<section id="{anchor}"><h2>{e(item["title"])}</h2>{text}</section>')
    if facts:
        summary=summary.replace('class="facts"','class="facts" id="life-history"');toc.insert(0,'<li>'+link('#life-history','Life-history data')+'</li>')
    for i,trial in enumerate(s.get('trials',[]),1):
        anchor=f'trial-{i}'
        toc.append('<li>'+link('#'+anchor,trial['title'])+'</li>')
        content='<p>'+prose(trial.get('text') or trial.get('intro',''))+'</p>'
        for fact in trial.get('facts',[]):
            content+='<p><b>'+e(fact['title'])+'</b> · '+e(fact['text'])+'</p>'
        for section in trial.get('sections',[]):
            content+='<h3>'+e(section['title'])+'</h3><p>'+prose(section['text'])+'</p>'
        if trial.get('url') and public_reference(trial['url']):content+='<p>'+link(trial['url'],'Original account')+'</p>'
        parts.insert(1 if len(parts)>1 else len(parts),f'<section id="{anchor}" class="trial"><h2>{e(trial["title"])}</h2>{content}</section>')
    adult_lead = ps[0] if ps and ps[0].get('stage') == 'Adults' else None
    gallery_photos = ps[1:] if adult_lead else ps
    body+='<div class="wrap article-layout"><article class="article">'+(galleryfig(adult_lead, lead=True) if adult_lead else '')+summary+''.join(parts)
    if g['slug'] in ('lucanidae', 'dynastinae', 'rutelinae', 'cetoniinae') or s['slug'] == 'stenodontes-chevrolati':
        body += '<p class="guide-related">'+link('substrate.html', 'How I prepare hardwood flake soil')+'</p>'
    if s['slug'] == 'strategus-aloeus':
        body += '<p class="guide-related">'+link('species-chrysina-woodi.html', 'My clay layer for pupating Chrysina woodi')+'</p>'
    for related_slug in s.get('related_species', []):
        related = by_slug.get(related_slug)
        if related:
            body += '<p class="guide-related">'+link(slink(related),'Breeding '+related['name'])+'</p>'
    if gallery_photos:
        toc.append('<li>'+link('#photographs','Photographs')+'</li>')
        body+='<section id="photographs"><h2>Photographs</h2>'
        for stage in ('Eggs','Larvae','Prepupae and pupae','Adults','Additional views'):
            group_photos=[p for p in gallery_photos if (p.get('stage') or 'Additional views')==stage]
            if group_photos:
                body+='<h3>'+e(stage)+'</h3><div class="gallery">'+''.join(galleryfig(p) for p in group_photos)+'</div>'
        body+='</section>'
    native=s.get('native_status')
    if native:
        toc.append('<li>'+link('#geography','Geographic status')+'</li>')
        body+='<section id="geography"><h2>Geographic status</h2><p>'+prose(native['text'])+'</p>'
        if native.get('sources'):
            body+='<ul class="sources">'+srcs(native)+'</ul>'
        body+='</section>'
    dist=s.get('distribution')
    if dist:
        filename=e(dist['file'])
        toc.append('<li>'+link('#distribution','Distribution records')+'</li>')
        caption=e(dist.get('caption',''))
        body+='<section id="distribution"><h2>Distribution records</h2><figure class="distribution-map"><a href="'+filename+'"><img loading="lazy" src="'+filename+'" alt="'+e('North American iNaturalist occurrence map for '+name)+'"></a><figcaption>'+caption+'</figcaption></figure>'
        body+='<p class="mapmeta">Retrieved '+e(dist['date'])+' UTC · '+link(dist['url'],'View observations on iNaturalist')
        if dist.get('data_file'):body+=' · '+link(dist['data_file'],'Map data and outlier decisions')
        body+=' · '+link('distribution.html','Mapping methods')+'</p></section>'
    references = srcs(s)
    if references:
        toc.append('<li>'+link('#references', 'Sources')+'</li>')
        body += '<section id="references"><h2>Sources</h2><ul class="sources">'+references+'</ul></section>'
    body+=classification(s.get('classification',[]))
    body+='</article><aside class="toc"><div class="onthis">In this guide</div><ol>'+''.join(toc)+'</ol>'+link(glink(s['group']),'All '+g['name']+' guides')+'</aside></div>'
    page(slink(s),((common+' ('+name+')') if common else name)+' breeding guide',s['intro'],body,'Article',ps[0] if ps else None,article=s)
opts=''.join(f'<option value="{k}">{e(g["name"])}</option>' for k,g in groups.items())
body=intro('Species index','Find a breeding guide by scientific name, common name, or beetle family.',[(None,'Species')])
body+='<section class="wrap block">'+browse_list()+'</section>'
page('species.html','Search beetle species guides','Search the breeding guide directory by scientific name, common name, and family.',body,'CollectionPage',active='species')
substrate=config.get('substrate')
if substrate:
    body=intro('Making substrate','',[(None,'Substrate')])
    contents=[]; blocks=[]
    for number,section in enumerate(substrate['sections'],1):
        title=section['title']; anchor='substrate-'+str(number)
        contents.append('<li>'+link('#'+anchor,title)+'</li>')
        block='<section id="'+anchor+'"><h2>'+e(title)+'</h2><p><i>'+e(section['subtitle'])+'</i></p>'
        for index,paragraph in enumerate(section['paragraphs']):
            if paragraph.strip(' \t\n\u200b'):
                block+='<p>'+prose(paragraph)+'</p>'
            credit=substrate['credit_after']
            if credit['section']==title and credit['paragraph_index']==index:
                block+='<p class="ratio-note"><strong>15 lb of unbleached flour per 40 lb of sawdust.</strong> '+link(substrate["credit_url"], "Leg and Leaf")+' developed this flour-to-sawdust ratio.</p>'
        for picture in substrate.get('photos',[]):
            if picture.get('section')==title:block+=galleryfig(picture)
        blocks.append(block+'</section>')
    body+='<div class="wrap article-layout"><article class="article">'+''.join(blocks)+'</article><aside class="toc"><div class="onthis">On this page</div><ol>'+''.join(contents)+'</ol></aside></div>'
    page('substrate.html','Making substrate and flake soil','Preparing raised-bed soil mixes and fermented hardwood flake soil for beetle larvae.',body,active='substrate')
about=intro('About me','',[(None,'About me')])
about+='<div class="wrap block about-layout"><article class="article bio"><h2>Junkai Wang</h2><p>I’m a PhD student in entomology at Michigan State University. I study the diversity and evolution of bark beetles, particularly <i>Ips</i> and its relatives. I studied ecology and evolutionary biology and art and design at the University of Michigan.</p><p>I keep records of the beetles I rear, including the substrates I use, the eggs I recover, and when the adults emerge. This site brings those records and photographs together by species.</p><p>'+link('https://www.instagram.com/beetlescholar/','Instagram · @beetlescholar')+'</p>'+(' <p>'+link(config['facebook_url'],'Facebook · Junkai Wang')+'</p>' if config.get('facebook_url') else '')+'</article>'
profile = config['instagram_gallery']
files.add(profile['avatar'])
about += '<section class="social-panel" aria-labelledby="insta-title"><h2 id="insta-title">Instagram</h2>'
about += '<div class="instagram-card"><a class="instagram-profile" href="'+e(profile['url'])+'"><img src="'+e(profile['avatar'])+'" alt="Beetle portrait from the beetlescholar profile" width="62" height="62"><span><strong>@'+e(profile['handle'])+'</strong><span>'+e(profile['display_name'])+'</span></span><span class="profile-arrow" aria-hidden="true">↗</span></a>'
about += '<div class="instagram-grid">'
for post in profile['posts']:
    files.add(post['file'])
    about += '<a href="'+e(post['url'])+'"><img loading="lazy" width="320" height="320" src="'+e(post['file'])+'" alt="'+e(post['alt'])+'"></a>'
about += '</div><a class="instagram-footer" href="'+e(profile['url'])+'">View full profile on Instagram ↗</a></div></section></div>'
page('about.html','About Junkai Wang','About the creator of North American Beetle Breeding and photographs from @beetlescholar.',about,active='about')
creditbody=intro('References','Published literature and publicly accessible rearing records cited in the species accounts.',[(None,'References')])+'<div class="wrap article-layout"><article class="article">'
for s in guides:
    if not srcs(s):continue
    creditbody += '<section><h2><i>'+e(s['name'])+'</i></h2><ul class="sources">'+srcs(s)+'</ul></section>'
creditbody+='</article></div>'
page('credits.html','References','Primary breeding accounts and species-specific references.',creditbody)
edit_template=(ROOT/'editor-template.html').read_text()
edit_template=edit_template.replace('%%SPECIES%%',''.join('<option value="'+e(s['slug'])+'">'+e(s['name'])+'</option>' for s in guides)).replace('%%GROUPS%%',opts)
write('editor-data.js','window.guideEditor = '+json.dumps({'species':guides},ensure_ascii=False).replace('<','\\u003c')+';')
page('editor.html','Manage species posts','Prepare a new or revised species post for publication.',intro('Manage species posts','',[(None,'Manage posts')])+edit_template)

sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for url in pages: ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=url
write('sitemap.xml',ET.tostring(sitemap,encoding='unicode'))
write('robots.txt','User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n')
print(f'Built {len(pages)} pages for {len(guides)} species, {len(groups)} groups, {len(photos)} images.')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--publish-dir', type=Path, help='Copy public pages and photographs into this directory')
output = parser.parse_args().publish_dir
if output:
    output.mkdir(parents=True, exist_ok=True)
    public = {'index.html', 'style.css', 'search.js', 'editor-data.js','editor.js', 'sitemap.xml', 'robots.txt'} | files
    public.update(url[len(BASE):] for url in pages if url != BASE)
    for filename in sorted(public):
        dest = output / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / filename, dest)
