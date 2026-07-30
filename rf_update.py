#!/usr/bin/env python3
"""RetireFlow 更新腳本 v2 — 含反向驗證，對不上帳就中止"""
import re, json, base64, subprocess, shutil, urllib.request, urllib.error, datetime
from collections import defaultdict

# ══ ① Google Drive 來源資料 ══
GD = dict(date='2026/07/30', ymd='2026-07-30',
    prev=76917860.93, total=76533884.68, debt=42686016.00,
    tw=39894926.15, us=22112777.65, jp=5840541.889, fund=8685639.00,
    div=1249645.492, mortgage=35053593, pledge=7632423)

TW=[("永豐敦南","00631L",3000,28.38),("永豐敦南","00663L",9000,80.20),("永豐敦南","00675L",4000,242.25),
 ("永豐竹科","0050",45000,93.50),("永豐竹科","0056",62700,46.29),("永豐竹科","006208",20000,214.40),
 ("永豐竹科","00631L",30000,28.38),("永豐竹科","00663L",23000,80.20),("永豐竹科","00685L",100000,9.16),
 ("永豐竹科","00881",35000,46.04),("永豐竹科","00894",33000,39.78),("永豐竹科","00927",50000,31.43),
 ("永豐竹科","00935",31000,47.90),("永豐竹科","00980A",23000,19.56),("永豐竹科","009816",17000,13.41),
 ("永豐竹科","00981A",23000,23.76),("永豐竹科","00985A",22000,18.33),("永豐竹科","00988A",14000,14.16),
 ("永豐竹科","00991A",12000,14.01),("永豐竹科","00992A",19000,13.48),
 ("永豐竹科","2330",5294,2205),("永豐竹科","5483",7000,152.5),("永豐竹科","6147",3000,118.5),
 ("玉山","00631L",15000,28.38),("台銀","006208",1000,214.40),("台銀","00631L",11000,28.38),
 ("台銀","00663L",1000,80.20),("台銀","00675L",2000,242.25),("台銀","2812",2559,20.65),
 ("凱基","00988A",15000,14.16)]

US=[("永豐豐存股","BRK.B",12,504.74),("永豐豐存股","GOOG",118,332.59),("永豐豐存股","NVDA",107,193.28),
 ("永豐豐存股","PLTR",87,123.005),("永豐豐存股","QQQ",43,678.415),("永豐豐存股","SMH",73,532.54),
 ("永豐豐存股","SOXX",9.1,496.91),("永豐豐存股","TSLA",37,305.45),("永豐豐存股","VOO",19.3,677.477),
 ("永豐豐存股","VT",166,154.26),("永豐豐存股","VTI",34.5,363.955),
 ("永豐複委託","DRAM",500,49.3499),("永豐複委託","MNST",60,96.14),("永豐複委託","MU",15,817.441),
 ("永豐複委託","MUU",500,23.845),("永豐複委託","NOK",500,9.215),("永豐複委託","RZLV",5000,2.31),
 ("永豐複委託","SGOV",500,100.68),("永豐複委託","SMH",40,532.54),("永豐複委託","SOFI",1400,15.64),
 ("永豐複委託","SOFX",500,7.4602),("永豐複委託","SOXL",120,110.39),("永豐複委託","TER",270,354.34),
 ("永豐複委託","TQQQ",200,62.10),("永豐複委託","TSM",50,398.66),("永豐複委託","TSMX",200,71.0),
 ("FirstTrade","AMD",25,472.36),("FirstTrade","DRAM",220,49.3499),("FirstTrade","INTW",100,19.44),
 ("FirstTrade","SGOV",400,100.68),("FirstTrade","SMH",35,532.54),("FirstTrade","SNXX",530,9.3401),
 ("FirstTrade","SOXL",120,110.39),("FirstTrade","SPCX",12,116.55),
 ("FirstTrade","TER",90,354.34),("FirstTrade","TQQQ",200,62.10)]

JP={"2644":dict(s=6000,p=3531,n="日本REITs ETF",t="ETF"),
    "6762":dict(s=600,p=2811.5,n="TDK",t="個股"),
    "6971":dict(s=900,p=3550,n="京瓷",t="個股"),
    "6981":dict(s=500,p=6416,n="村田製作所",t="個股")}

FUND=[dict(code="鉅亨",name="鉅亨網基金",raw=4113694,color="#378ADD",type="ETF"),
      dict(code="HSBC",name="HSBC結構型",raw=3144850,color="#1D9E75",type="現金替代"),
      dict(code="基富通",name="基富通基金",raw=1427095,color="#EF9F27",type="ETF")]

NAMES={"0050":"元大台灣50","0056":"元大高股息","006208":"富邦台50","00631L":"元大台50正2",
 "00663L":"國泰加權正2","00675L":"富邦加權正2","00685L":"群益加權正2","00881":"國泰科技龍頭",
 "00894":"中信小資高價30","00927":"群益半導體收益","00935":"野村新科技50","009816":"凱基TOP50",
 "00980A":"野村臺灣優選","00981A":"統一台股增長","00985A":"野村台灣50","00988A":"統一全球創新",
 "00991A":"復華未來50","00992A":"群益科技創新","2330":"台積電","5483":"中美晶","6147":"頎邦","2812":"台中銀",
 "BRK.B":"Berkshire B","GOOG":"Alphabet","NVDA":"NVIDIA","PLTR":"Palantir","QQQ":"QQQ",
 "SMH":"SMH半導體","SOXX":"SOXX","TSLA":"Tesla","VOO":"VOO","VT":"VT全球","VTI":"VTI全美",
 "DRAM":"DRAM ETF","MNST":"Monster","MU":"Micron","MUU":"MUU","NOK":"Nokia","RZLV":"RZLV",
 "SGOV":"SGOV超短債","SOFI":"SoFi","SOFX":"SOFX","SOXL":"SOXL 3x","TER":"Teradyne",
 "TQQQ":"TQQQ 3x","TSM":"台積電ADR","TSMX":"TSMX","AMD":"AMD","INTW":"INTW","SNXX":"SNXX","SPCX":"SPCX"}
TYPES={"00631L":"槓桿","00663L":"槓桿","00675L":"槓桿","00685L":"槓桿","TQQQ":"槓桿","SOXL":"槓桿",
 "SGOV":"現金替代","SNXX":"現金替代","2330":"個股","5483":"個股","6147":"個股","2812":"個股",
 "BRK.B":"個股","GOOG":"個股","NVDA":"個股","PLTR":"個股","TSLA":"個股","TER":"個股",
 "MU":"個股","AMD":"個股","MNST":"個股","TSM":"個股","SOFI":"個股"}
def typ(c): return TYPES.get(c,'主動ETF' if c.endswith('A') else 'ETF')

# ══ ② 計算 ══
usd=round(GD['us']/sum(s*p for _,_,s,p in US),2)
jpy=round(GD['jp']/sum(JP[c]['s']*JP[c]['p'] for c in JP),5)
W=lambda n: round(n/10000)
net=GD['total']-GD['debt']
V=dict(total_w=W(GD['total']),net_w=W(net),debt_w=W(GD['debt']),tw_w=W(GD['tw']),
  us_w=W(GD['us']),jp_w=W(GD['jp']),fd_w=W(GD['fund']),div_w=round(GD['div']/10000,1),
  mort_w=W(GD['mortgage']),pledge_w=W(GD['pledge']),usd=usd,jpy=jpy)
V['div_mo']=round(V['div_w']/12,1)
V['chg']=round((GD['total']-GD['prev'])/10000)
V['arrow']='↑' if V['chg']>=0 else '↓'
V['dr']=round(GD['debt']/GD['total']*100,1)
V['ach']=round(GD['total']/160000000*100,1)
V['tw_a']=round(GD['tw']/100000000*100,1); V['us_a']=round(GD['us']/40000000*100,1)
V['jp_a']=round(GD['jp']/10000000*100,1); V['fd_a']=round(GD['fund']/10000000*100,1)
lev=sum(s*p for _,c,s,p in TW if typ(c)=='槓桿')+sum(s*p*usd for _,c,s,p in US if typ(c)=='槓桿')
V['lev']=round(lev/10000,1); V['lev_p']=round(V['lev']/V['total_w']*100,1)
dm=(datetime.date(2028,12,31)-datetime.date.fromisoformat(GD['ymd'])).days//30
V['ry'],V['rm']=dm//12,dm%12

# 聚合
def build(rows,fx=1.0):
    agg=defaultdict(lambda:dict(s=0,p=0,v=0.0)); brk=defaultdict(lambda:defaultdict(lambda:dict(s=0,p=0,v=0.0)))
    for b,c,s,p in rows:
        v=s*p*fx/10000
        agg[c]['s']+=s; agg[c]['p']=p; agg[c]['v']+=v
        brk[b][c]['s']+=s; brk[b][c]['p']=p; brk[b][c]['v']+=v
    return agg,brk
twA,twB=build(TW); usA,usB=build(US,usd)
arr=lambda A: sorted([dict(code=c,name=NAMES.get(c,c),val=round(x['v'],1),type=typ(c))
    for c,x in A.items() if x['v']>0],key=lambda d:-d['val'])
tw_d,us_d=arr(twA),arr(usA)
jp_d=sorted([dict(code=c,name=JP[c]['n'],val=round(JP[c]['s']*JP[c]['p']*jpy/10000,1),type=JP[c]['t'])
    for c in JP],key=lambda d:-d['val'])
jp_tot=round(sum(d['val'] for d in jp_d),1)
for f in FUND: f['val']=round(f['raw']/10000,1); f['pct']=round(f['raw']/GD['fund']*100,1)

AJ=lambda I:'[\n'+',\n'.join(f'  {{code:"{d["code"]}",name:"{d["name"]}",val:{d["val"]},type:"{d["type"]}"}}' for d in I)+'\n]'
def BJ(B):
    o=['{\n']
    for b,st in dict(B).items():
        it=sorted([(c,dict(x)) for c,x in dict(st).items() if x['v']>0],key=lambda z:-z[1]['v'])
        o.append('  "%s": {total:%s, items:[\n    %s\n  ]},\n'%(b,round(sum(x['v'] for x in dict(st).values()),1),
          ',\n    '.join('{code:"%s",name:"%s",shares:%s,price:%s,val:%s,type:"%s"}'%(
            c,NAMES.get(c,c),x['s'],round(x['p'],2),round(x['v'],1),typ(c)) for c,x in it)))
    return ''.join(o)+'}'

print(f"計算：總{V['total_w']}萬 淨{V['net_w']}萬 {V['ach']}% {V['chg']:+}萬 USD={usd} JPY={jpy}")
print(f"  台股{V['tw_w']}萬 美股{V['us_w']}萬 日股{V['jp_w']}萬(算得{jp_tot}) 基金{V['fd_w']}萬")

# ══ ③ 替換（全部 re.sub）══
html=open('/tmp/retireflow_full.html',encoding='utf-8').read()
def sub(pat,rep,tag):
    global html
    new,n=re.subn(pat,rep,html,count=1)
    if n==0: print(f"  ⚠️  {tag} 未匹配"); return False
    html=new; return True

# JS 陣列
for var,s in [('TW_DATA',AJ(tw_d)),('US_DATA',AJ(us_d)),('JP_DATA',AJ(jp_d)),('FD_DATA',AJ(FUND))]:
    html=re.sub(rf'window\.{var}=\s*\[[\s\S]*?\];',f'window.{var}=\n{s};',html,count=1)
for var,s in [('TW_BROKER',BJ(twB)),('US_BROKER',BJ(usB))]:
    html=re.sub(rf'window\.{var} = \{{[\s\S]*?\n\}};',f'window.{var} = {s};',html,count=1)
print("  ✅ JS 陣列 6 組")

# HTML bar
jb=',\n      '.join(f"{{code:'{d['code']}',name:'{d['name']}',val:{d['val']},pct:{round(d['val']/jp_tot*100,1)},color:'{'#378ADD' if d['type']=='ETF' else '#E24B4A'}'}}" for d in jp_d)
html=re.sub(r'const jitems=\[[\s\S]*?\];',f'const jitems=[{jb}];',html,count=1)
html=re.sub(r'const jmax=[\d.]+;',f'const jmax={jp_d[0]["val"]};',html,count=1)
html=re.sub(r'日股持股分析（[\d.]+萬｜[\d.]+ JPY/TWD）',f'日股持股分析（{jp_tot}萬｜{jpy} JPY/TWD）',html,count=1)
fb=',\n      '.join(f"{{name:'{f['name']}',val:{f['val']},pct:{f['pct']},color:'{f['color']}'}}" for f in FUND)
html=re.sub(r"const items=\[\{name:'[\s\S]*?\];", f'const items=[{fb}];', html, count=1)
print("  ✅ HTML bar (日股/基金)")

# 靜態欄位
for pat,rep,tag in [
 (r'Google Drive 即時同步｜\d{4}/\d{2}/\d{2}｜',f'Google Drive 即時同步｜{GD["date"]}｜','日期'),
 (r'達成率 [\d.]+%',f'達成率 {V["ach"]}%','達成率pill'),
 (r'槓桿 [\d.]+%',f'槓桿 {V["lev_p"]}%','槓桿pill'),
 (r'(metric-value">)[\d,]+(<span[^>]*>萬</span></div>\s*<div class="metric-sub [ud][np]">)[↑↓] [+-]?\d+萬 今日',
  rf'\g<1>{V["total_w"]:,}\g<2>{V["arrow"]} {V["chg"]:+}萬 今日','總資產+變化'),
 (r'(metric-value">)[\d,]+(<span[^>]*>萬</span></div>\s*<div class="metric-sub">)負債比 [\d.]+%',
  rf'\g<1>{V["net_w"]:,}\g<2>負債比 {V["dr"]}%','淨資產+負債比'),
 (r'(metric-value warn">)[\d.]+(<span[^>]*>萬</span></div>\s*<div class="metric-sub">佔總資產) [\d.]+%',
  rf'\g<1>{V["lev"]}\g<2> {V["lev_p"]}%','槓桿ETF'),
 (r'年股息 [\d.]+萬｜月均 [\d.]+萬',f'年股息 {V["div_w"]}萬｜月均 {V["div_mo"]}萬','年股息'),
 (r'(cd-n">)\d+(</span><span class="cd-u">年)',rf'\g<1>{V["ry"]}\g<2>','距退休年'),
 (r'(cd-n">)\d+(</span><span class="cd-u">月)',rf'\g<1>{V["rm"]}\g<2>','距退休月'),
 (r'(letter-spacing:-1px">)[\d.]+%',rf'\g<1>{V["ach"]}%','達成率大字'),
 (r'width:[\d.]+%;background:linear-gradient',f'width:{V["ach"]}%;background:linear-gradient','進度條'),
 (r'總資產 [\d,]+萬 ／ 目標 16,000萬',f'總資產 {V["total_w"]:,}萬 ／ 目標 16,000萬','副標'),
 (r'還需增加 [\d,]+萬',f'還需增加 {16000-V["total_w"]:,}萬','還需增加'),
 (r's-current" value="\d+"',f's-current" value="{V["total_w"]}"','試算'),
 (r"drawGauge\('g-tw',[\d.]+,'[^']+',",f"drawGauge('g-tw',{V['tw_a']},'{V['tw_w']:,}萬',",'油表台'),
 (r"drawGauge\('g-us',[\d.]+,'[^']+',",f"drawGauge('g-us',{V['us_a']},'{V['us_w']:,}萬',",'油表美'),
 (r"drawGauge\('g-jp',[\d.]+,'[^']+',",f"drawGauge('g-jp',{V['jp_a']},'{V['jp_w']:,}萬',",'油表日'),
 (r"drawGauge\('g-fd',[\d.]+,'[^']+',",f"drawGauge('g-fd',{V['fd_a']},'{V['fd_w']:,}萬',",'油表基'),
 (r'"USDTWD":[\d.]+,',f'"USDTWD":{usd},','USD匯率'),
 (r'"JPYTWD":[\d.]+,',f'"JPYTWD":{jpy},','JPY匯率'),
]:
    sub(pat,rep,tag)
for c,x in twA.items(): html=re.sub(rf'"{c}":(?!\d{{4}})[\d.]+,',f'"{c}":{round(x["p"],2)},',html)
for c in JP: html=re.sub(rf'"{c}\.T":[\d.]+,',f'"{c}.T":{JP[c]["p"]},',html)
print("  ✅ 靜態欄位 + FALLBACK")

# 月曆 + 走勢圖
cc=round((GD['total']-GD['prev'])/10000,1); cp=round((GD['total']-GD['prev'])/GD['prev']*100,2)
if f'"{GD["ymd"]}"' in html:
    html=re.sub(rf'"{GD["ymd"]}":\{{[^}}]+\}}',f'"{GD["ymd"]}":{{"v":{V["total_w"]},"c":{cc},"p":{cp}}}',html)
else:
    for ld in ['2026-07-28','2026-07-27']:
        if f'"{ld}"' in html:
            i=html.find(f'"{ld}"'); e=html.find('}',i)+1
            html=html[:e]+f',"{GD["ymd"]}":{{"v":{V["total_w"]},"c":{cc},"p":{cp}}}'+html[e:]; break
md=GD['ymd'][5:].replace('-','/')
for a,v in [('HD',f'"{md}"'),('HT',V['total_w']),('HN',V['net_w']),('HDbt',V['debt_w']),
            ('HTW',V['tw_w']),('HUS',V['us_w']),('HJP',V['jp_w']),('HFD',V['fd_w'])]:
    m=re.search(rf'const {a}=\[([^\]]*)\]',html)
    if m and (v.strip('"') if a=='HD' else str(v)) not in m.group(1).split(',')[-1:][0].strip():
        html=html[:m.end()-1]+f',{v}'+html[m.end()-1:]
print("  ✅ 月曆 + 走勢圖")

# ══ ④ 反向驗證：從 HTML 解析回來對帳 ══
print("\n── 反向驗證（解析 HTML 對帳 Google Drive）──")
errs=[]
def grab(var):
    m=re.search(rf'window\.{var}=\s*(\[[\s\S]*?\]);',html)
    return re.findall(r'val:([\d.]+)',m.group(1)) if m else []
def grab_brk(var):
    m=re.search(rf'window\.{var} = (\{{[\s\S]*?\n\}});',html)
    if not m: return {},[]
    b=m.group(1)
    return dict(re.findall(r'"([^"]+)": \{total:([\d.]+)',b)), re.findall(r'val:([\d.]+)',b)

for var,gd_val,label in [('TW_DATA',GD['tw'],'台股'),('US_DATA',GD['us'],'美股'),('JP_DATA',GD['jp'],'日股')]:
    vals=[float(v) for v in grab(var)]
    s=round(sum(vals),1); t=round(gd_val/10000,1); d=abs(s-t)
    ok=d<=max(2.0,t*0.005)
    print(f"  {'✅' if ok else '❌'} {var} 加總 {s}萬 vs GD {t}萬 (差{d:.1f})")
    if not ok: errs.append(f"{var} 對帳差 {d:.1f}萬")

for var,gd_val,label in [('TW_BROKER',GD['tw'],'台股券商'),('US_BROKER',GD['us'],'美股券商')]:
    tots,items=grab_brk(var)
    bt=round(sum(float(v) for v in tots.values()),1)
    it=round(sum(float(v) for v in items)-bt,1)  # items 含 total 值需扣除
    t=round(gd_val/10000,1); d=abs(bt-t)
    ok=d<=max(2.0,t*0.005)
    print(f"  {'✅' if ok else '❌'} {var} 券商小計 {bt}萬 vs GD {t}萬 (差{d:.1f})")
    for b,v in tots.items(): print(f"       {b}: {v}萬")
    if not ok: errs.append(f"{var} 對帳差 {d:.1f}萬")

# 逐筆抽驗：台積電、TER
m=re.search(r'\{code:"2330",name:"[^"]+",shares:(\d+),price:([\d.]+),val:([\d.]+)',html)
if m:
    exp=round(int(m.group(1))*float(m.group(2))/10000,1); got=float(m.group(3))
    ok=abs(exp-got)<0.15
    print(f"  {'✅' if ok else '❌'} 台積電 {m.group(1)}股×{m.group(2)}元={exp}萬, HTML={got}萬")
    if not ok: errs.append("台積電估值錯誤")
    src_p=[p for _,c,_,p in TW if c=='2330'][0]
    if abs(float(m.group(2))-src_p)>0.01: errs.append(f"台積電股價未更新({m.group(2)}≠{src_p})")

for code,sh in [("TER",270),("SGOV",500)]:
    m=re.search(rf'\{{code:"{code}",name:"[^"]+",shares:{sh},price:([\d.]+),val:([\d.]+)',html)
    if m:
        exp=round(sh*float(m.group(1))*usd/10000,1); got=float(m.group(2))
        ok=abs(exp-got)<0.15
        print(f"  {'✅' if ok else '❌'} {code} {sh}股×${m.group(1)}×{usd}={exp}萬, HTML={got}萬")
        if not ok: errs.append(f"{code} 估值錯誤")

# 靜態欄位存在性
for pat,d in [(f'>{V["total_w"]:,}<','總資產'),(f'>{V["net_w"]:,}<','淨資產'),
  (f'達成率 {V["ach"]}%','達成率pill'),(f'letter-spacing:-1px">{V["ach"]}%','達成率大字'),
  (f'width:{V["ach"]}%','進度條'),(f'年股息 {V["div_w"]}萬','年股息'),
  (f'>{V["lev"]}<','槓桿ETF'),(f'{GD["date"]}','日期'),(f'"{GD["ymd"]}"','月曆'),
  (f"drawGauge('g-tw',{V['tw_a']},",'油表台'),(f'"USDTWD":{usd}','USD匯率')]:
    if pat not in html: errs.append(f"{d} 未更新")

# CSS 完整性（防止無錨點正則改壞版面）
css=html[html.find('<style>'):html.find('</style>')]
bad=[(m.group(1),m.group(2)) for m in re.finditer(r'([.\w-]+)\{[^}]*?width:([\d.]+)%',css)
     if m.group(2) not in ('100','50','33','25')]
if bad: errs.append(f"CSS width 異常: {bad}")
else: print("  ✅ CSS 完整性")

# JS 語法
open('/tmp/c.js','w').write(html[html.rfind('<script>')+8:html.rfind('</script>')])
r=subprocess.run(['node','--check','/tmp/c.js'],capture_output=True,text=True)
if r.returncode: errs.append(f"JS 語法錯誤: {r.stderr[:120]}")
else: print("  ✅ JS 語法")

# ══ ⑤ 通過才 push ══
if errs:
    print(f"\n⛔ {len(errs)} 項未通過，中止 push：")
    for e in errs: print(f"   • {e}")
    raise SystemExit(1)

print("\n✅ 全部驗證通過")
open('/tmp/retireflow_full.html','w',encoding='utf-8').write(html)
shutil.copy('/tmp/retireflow_full.html','/mnt/user-data/outputs/RetireFlow_Dashboard_v2.html')
import os
T=os.environ.get("GH_TOKEN","")  # export GH_TOKEN=github_pat_...
R="HuowenChen/Claud_RetireApp"; H={"Authorization":f"token {T}","Content-Type":"application/json","User-Agent":"RF"}
def api(m,p,d=None):
    q=urllib.request.Request(f"https://api.github.com{p}",json.dumps(d).encode() if d else None,H,method=m)
    try:
        with urllib.request.urlopen(q) as x: return json.loads(x.read())
    except urllib.error.HTTPError as e: return json.loads(e.read())
sha=api("GET",f"/repos/{R}/contents/index.html").get("sha")
d={"message":f"📊 {GD['date']} 更新（含反向對帳驗證）：{V['total_w']:,}萬/淨{V['net_w']:,}萬/{V['ach']}%",
   "content":base64.b64encode(html.encode()).decode(),"branch":"main"}
if sha: d["sha"]=sha
print("✅ Push:" if api("PUT",f"/repos/{R}/contents/index.html",d).get('content') else "❌",
      "https://huowenchen.github.io/Claud_RetireApp/")
