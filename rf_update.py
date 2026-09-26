#!/usr/bin/env python3
"""RetireFlow 更新腳本 v2 — 含反向驗證，對不上帳就中止"""
import os, re, json, base64, subprocess, shutil, urllib.request, urllib.error, datetime
from collections import defaultdict

# ══ ① Google Drive 來源資料 ══
CASH=dict(ntd=0, usd=0, jpy=0)  # 現金餘額（GD 現金表）

GD = dict(date='2026/09/25', ymd='2026-09-25',
    prev=96333559.22, total=96876368.57, debt=48860814.00,
    tw=55300675.91, us=25145343.29, jp=6805942.361, fund=9624407.00,
    div=1801422.478, mortgage=34959749, pledge=13901065)

NET_HIST={"2026-09-01":43891056.24,"2026-09-02":42093460.87,"2026-09-03":42567097.32,
 "2026-09-04":43645793.23,"2026-09-05":43145207.03,"2026-09-07":45219175.64,
 "2026-09-08":45558043.97,"2026-09-09":45043503.41,"2026-09-10":44790793.20,
 "2026-09-11":43229840.57,"2026-09-12":44126683.88,"2026-09-14":42944668.89,
 "2026-09-15":41494759.09,"2026-09-16":41752680.89,"2026-09-17":42638370.96,
 "2026-09-18":44723081.58,"2026-09-19":44610965.02,"2026-09-21":46061720.56,
 "2026-09-22":47093243.89,"2026-09-23":47341799.99,"2026-09-24":47472745.22,
 "2026-09-25":48015554.57}

GD_HIST={"2026-09-01":89938261.24,"2026-09-02":88140665.87,"2026-09-03":88614302.32,
 "2026-09-04":89692998.23,"2026-09-05":89192412.03,"2026-09-07":91266380.64,
 "2026-09-08":94418857.97,"2026-09-09":93904317.41,"2026-09-10":93651607.20,
 "2026-09-11":92090654.57,"2026-09-12":92987497.88,"2026-09-14":91805482.89,
 "2026-09-15":90355573.09,"2026-09-16":90613494.89,"2026-09-17":91499184.96,
 "2026-09-18":93583895.58,"2026-09-19":93471779.02,"2026-09-21":94922534.56,
 "2026-09-22":95954057.89,"2026-09-23":96202613.99,"2026-09-24":96333559.22,
 "2026-09-25":96876368.57}

TW=[("永豐敦南","00631L",3000,38.99),("永豐敦南","00663L",9000,112.85),("永豐敦南","00675L",4000,341.60),
 ("永豐竹科","0050",46400,112.45),("永豐竹科","0056",63600,56.60),("永豐竹科","006208",20000,257.00),
 ("永豐竹科","00631L",63000,38.99),("永豐竹科","00663L",23000,112.85),("永豐竹科","00685L",153000,12.89),
 ("永豐竹科","00881",37000,52.60),("永豐竹科","00894",34000,50.00),("永豐竹科","00927",51000,39.89),
 ("永豐竹科","00935",31000,61.45),("永豐竹科","009816",1500,16.60),("永豐竹科","00988A",16000,16.95),
 ("永豐竹科","2330",8107,2475),("永豐竹科","6121",4000,376.00),
 ("玉山","00631L",15000,38.99),
 ("台銀","006208",1000,257.00),("台銀","00631L",11000,38.99),("台銀","00663L",1000,112.85),
 ("台銀","00675L",2000,341.60),("台銀","2812",2559,19.00),
 ("凱基","00988A",15000,16.95)]

US=[("永豐豐存股","BRK.B",12,505.18),("永豐豐存股","GOOG",118,339.01),("永豐豐存股","MAGS",8.6,72.51),
 ("永豐豐存股","NVDA",107,224.58),("永豐豐存股","PLTR",87,192.59),("永豐豐存股","QQQ",44,741.10),
 ("永豐豐存股","SMH",75,600.52),("永豐豐存股","SOXX",14.3,566.07),("永豐豐存股","TSLA",37,377.94),
 ("永豐豐存股","VOO",19.3,706.99),("永豐豐存股","VT",166,159.05),("永豐豐存股","VTI",35.2,378.08),
 ("永豐複委託","DRAM",500,60.72),("永豐複委託","GRAB",2000,3.11),("永豐複委託","MU",15,1080.53),
 ("永豐複委託","MUU",450,37.71),("永豐複委託","NTSD",90,47.42),("永豐複委託","QLD",50,96.10),
 ("永豐複委託","QQQI",60,55.56),("永豐複委託","SGOV",400,100.62),("永豐複委託","SMH",45,600.52),
 ("永豐複委託","SNPS",10,424.91),("永豐複委託","SOFI",1400,16.80),("永豐複委託","SOXL",200,146.33),
 ("永豐複委託","SSO",150,70.26),("永豐複委託","TER",210,387.70),("永豐複委託","TQQQ",200,78.58),
 ("永豐複委託","TSM",50,451.15),("永豐複委託","TSMX",300,88.36),
 ("FirstTrade","AMD",16,629.26),("FirstTrade","AVGO",11,350.36),("FirstTrade","DRAM",300,60.72),
 ("FirstTrade","GOOG",4,339.01),("FirstTrade","MUU",50,37.71),("FirstTrade","NTSD",80,47.42),
 ("FirstTrade","QLD",3,96.10),("FirstTrade","QQQI",60,55.56),("FirstTrade","SGOV",115,100.62),
 ("FirstTrade","SMH",50,600.52),("FirstTrade","SNXX",1900,17.13),("FirstTrade","SOXL",200,146.33),
 ("FirstTrade","SPCX",22,148.03),("FirstTrade","TER",60,387.70),("FirstTrade","TQQQ",200,78.58)]

JP={"2644":dict(s=7000,p=4047,n="日本REITs ETF",t="ETF"),
    "6627":dict(s=300,p=11780,n="TERA PROBE",t="個股"),
    "6981":dict(s=300,p=8022,n="村田製作所",t="個股")}

FUND=[dict(code="鉅亨",name="鉅亨網基金",raw=4524222,color="#378ADD",type="ETF"),
      dict(code="HSBC",name="HSBC結構型",raw=3144850,color="#1D9E75",type="現金替代"),
      dict(code="基富通",name="基富通基金",raw=1955335,color="#EF9F27",type="ETF")]

NAMES={"0050":"元大台灣50","0056":"元大高股息","006208":"富邦台50","00631L":"元大台50正2",
 "00663L":"國泰加權正2","00675L":"富邦加權正2","00685L":"群益加權正2","00881":"國泰科技龍頭",
 "00894":"中信小資高價30","00927":"群益半導體收益","00935":"野村新科技50","009816":"凱基TOP50",
 "00980A":"野村臺灣優選","00981A":"統一台股增長","00985A":"野村台灣50","00988A":"統一全球創新",
 "00991A":"復華未來50","00992A":"群益科技創新","2330":"台積電","5483":"中美晶","6147":"頎邦","2812":"台中銀","6121":"新普","NTSD":"NTSD","QQQI":"QQQI","6627":"TERA PROBE",
 "BRK.B":"Berkshire B","GOOG":"Alphabet","NVDA":"NVIDIA","PLTR":"Palantir","QQQ":"QQQ",
 "SMH":"SMH半導體","SOXX":"SOXX","TSLA":"Tesla","VOO":"VOO","VT":"VT全球","VTI":"VTI全美",
 "DRAM":"DRAM ETF","MNST":"Monster","MU":"Micron","MUU":"MUU","NOK":"Nokia","RZLV":"RZLV",
 "SGOV":"SGOV超短債","SOFI":"SoFi","SOFX":"SOFX","SOXL":"SOXL 3x","TER":"Teradyne",
 "TQQQ":"TQQQ 3x","TSM":"台積電ADR","TSMX":"TSMX","AMD":"AMD","INTW":"INTW","SNXX":"SNXX","SPCX":"SPCX",
 "MAGS":"Mag7 ETF","GRAB":"Grab","QLD":"QLD 2x","SSO":"SSO 2x",
 "SNPS":"Synopsys","AVGO":"Broadcom","6981":"村田製作所","2644":"日本REITs ETF"}
TYPES={"00631L":"槓桿","00663L":"槓桿","00675L":"槓桿","00685L":"槓桿","TQQQ":"槓桿","SOXL":"槓桿",
 "SGOV":"現金替代","SNXX":"槓桿","2330":"個股","5483":"個股","6147":"個股","2812":"個股","6121":"個股",
 "BRK.B":"個股","GOOG":"個股","NVDA":"個股","PLTR":"個股","TSLA":"個股","TER":"個股",
 "MU":"個股","AMD":"個股","MNST":"個股","TSM":"個股","SOFI":"個股",
 "QLD":"槓桿","SSO":"槓桿","SNPS":"個股","AVGO":"個股","GRAB":"個股","MAGS":"ETF"}
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
# 融資維持率（擔保品=永豐台股帳戶：敦南+竹科）
collat=round(sum(s*p for b,c,s,p in TW if b in('永豐敦南','永豐竹科'))/10000)
V['collat']=collat; V['maint']=round(collat/V['pledge_w']*100,1)
V['interest']=round(V['pledge_w']*3.8/100,1)
V['bar']=round(min((V['maint']-130)/(600-130)*100,100),1)
V['drop_call']=round((collat-V['pledge_w']*1.66)/collat*100,1)

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
html=open('/home/claude/rf/retireflow_full.html',encoding='utf-8').read()
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
# 日股明細表（股數×日幣股價×匯率）— 之前遺漏，補上自動更新
_note={"2644":"核心，配息穩定","6762":"電子零件龍頭，持有",
       "6971":"精密陶瓷，穩健持有","6981":"MLCC龍頭，AI受惠"}
_jrows=''.join(f"""
        <tr>
          <td style="padding:7px 8px;font-weight:500">{d['code']}</td>
          <td style="padding:7px 8px">{d['name']}</td>
          <td style="padding:7px 8px;text-align:right">{JP[d['code']]['s']:,}</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600">¥{JP[d['code']]['p']:,}</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600">{d['val']}萬</td>
          <td style="padding:7px 8px;text-align:right;color:var(--muted)">{round(d['val']/jp_tot*100,1)}%</td>
          <td style="padding:7px 8px;color:var(--muted)">{_note.get(d['code'],'')}</td>
        </tr>""" for d in jp_d)
_s=html.find('id="tab-pareto-jp"'); _e=html.find('<!-- ════',_s+10)
_seg=html[_s:_e]
_seg2=re.sub(r'(日股明細[\s\S]*?<tbody>)[\s\S]*?(</tbody>)',
    lambda m:m.group(1)+_jrows+'\n      '+m.group(2),_seg,count=1)
# key-insight 內的數字一併更新
_seg2=re.sub(r'股數×JPY股價×[\d.]+直接計算，合計[\d.]+萬，達成率[\d.]+%',
    f'股數×JPY股價×{jpy}直接計算，合計{jp_tot}萬，達成率{V["jp_a"]}%',_seg2,count=1)
_seg2=re.sub(r'（\d+）佔[\d.]+%為核心部位',f'（2644）佔{round(jp_d[0]["val"]/jp_tot*100,1)}%為核心部位',_seg2,count=1)
_seg2=re.sub(r'距目標尚差 ?[\d.]+萬',f'距目標尚差{round(1000-jp_tot,1)}萬',_seg2,count=1)
html=html[:_s]+_seg2+html[_e:]
# Bar Chart 標題（先前寫死舊估值）
html=re.sub(r"buildHBar\('twPareto',window\.TW_DATA,'[^']*'\)",
    f"buildHBar('twPareto',window.TW_DATA,'台股持股（{V['tw_w']:,}萬｜前15大＋其他）')",html,count=1)
html=re.sub(r"buildHBar\('usPareto',window\.US_DATA,'[^']*'\)",
    f"buildHBar('usPareto',window.US_DATA,'美股持股（{V['us_w']:,}萬｜USD/TWD {usd}）')",html,count=1)
# ── 現金管理頁（SNXX 為 2x SNDK 槓桿，不計入現金）──
_sg=sum(sh for _,c,sh,_ in US if c=='SGOV'); _sgp=[p for _,c,_,p in US if c=='SGOV'][0]
_sgv=round(_sg*_sgp*usd/10000,1)
_ntd=round(CASH['ntd']/10000,1)
_fx=round((CASH['usd']*usd+CASH['jpy']*jpy)/10000,1)
_ct=round(_sgv+_ntd+_fx,1)
_cp=round(_ct/V['total_w']*100,1)
_L5,_L8,_L10=round(V['total_w']*.05),round(V['total_w']*.08),round(V['total_w']*.10)
_snv=round(sum(sh for _,c,sh,_ in US if c=='SNXX')*([p for _,c,_,p in US if c=='SNXX'] or [0])[0]*usd/10000,1)
_low = _ct < _L5
_cs=html.find('id="tab-cash"'); _ce=html.find('<!-- ════',_cs); _seg=html[_cs:_ce]
for _p,_r in [
 (r'(SGOV )[\d,]+(股</div><div class="metric-value up">)[\d.]+',rf'\g<1>{_sg:,.0f}\g<2>{_sgv:.0f}'),
 (r'(台幣現金</div><div class="metric-value">)[\d.]+',rf'\g<1>{_ntd:.0f}'),
 (r'(NT\$)[\d,]+(</div>)',rf'\g<1>{CASH["ntd"]:,}\g<2>'),
 (r'(外幣現金</div><div class="metric-value">)[\d.]+',rf'\g<1>{_fx:.0f}'),
 (r'USD[\d,]+ \+ JPY[\d萬,]+',f'USD{CASH["usd"]:,} + JPY{CASH["jpy"]:,}'),
 (r'(現金合計</div><div class="metric-value (?:up|dn)">)[\d.]+',rf'\g<1>{_ct:.0f}'),
 (r'佔[\d.]+%（(?:低於|已達)最低5%）',f'佔{_cp}%（{"低於" if _low else "已達"}最低5%）'),
 (r'(<div class="cash-label">目前 )[\d.]+%',rf'\g<1>{_cp}%'),
 (r'(<div class="cash-val (?:up|dn)">)[\d.]+萬',rf'\g<1>{_ct:.0f}萬'),
 (r'距最低5%（[\d,]+萬）缺 [\d-]+萬',f'距最低5%（{_L5:,}萬）缺 {max(0,_L5-round(_ct))}萬'),
 (r'(<div class="cash-val warn">)[\d,]+萬',rf'\g<1>{_L8:,}萬'),
 (r'缺口 [\d-]+萬',f'缺口 {max(0,_L8-round(_ct))}萬'),
 (r'(<div class="cash-label">退休前 10%</div><div class="cash-val">)[\d,]+萬',rf'\g<1>{_L10:,}萬'),
 (r'>610股<',f'>{_sg:,.0f}股<'),
 (r'(SGOV 超短期公債</td><td[^>]*>)[\d,]+股',rf'\g<1>{_sg:,.0f}股'),
 (r'(\$)[\d.]+( × )[\d.]+( × )[\d,]+',rf'\g<1>{_sgp}\g<2>{usd}\g<3>{_sg:,.0f}'),
 (r'SNXX（[\d.]+萬）',f'SNXX（{_snv:.0f}萬）'),
 (r'現金因此由 [\d.]+萬修正為',f'現金因此由 {_ct+_snv:.0f}萬修正為'),
 (r'<b>[\d.]+萬（[\d.]+%）</b>',f'<b>{_ct:.0f}萬（{_cp}%）</b>'),
 (r'現金 [\d.]+% <b>低於最低水位 5%</b>（[\d,]+萬），缺 [\d-]+萬',
  f'現金 {_cp}% <b>{"低於" if _low else "已達"}最低水位 5%</b>（{_L5:,}萬），{"缺 "+str(_L5-round(_ct))+"萬" if _low else "已達標"}'),
 (r'距建議 8%（[\d,]+萬）缺 [\d-]+萬',f'距建議 8%（{_L8:,}萬）缺 {max(0,_L8-round(_ct))}萬'),
 (r'SNXX 停利出場（[\d.]+萬）',f'SNXX 停利出場（{_snv:.0f}萬）'),
]:
    _seg=re.sub(_p,_r,_seg,count=1)
html=html[:_cs]+_seg+html[_ce:]
print(f"  ✅ 現金管理頁（{_ct}萬 / {_cp}%）")

# ── 基金分頁（標題+三帳戶明細）──
_ft=sum(f['raw'] for f in FUND); _ftw=round(_ft/10000); _fach=round(_ft/10000000*100,1)
_fs=html.find('id="tab-fund"'); _fe=html.find('<!-- ════',_fs); _fseg=html[_fs:_fe]
_fseg=re.sub(r'基金帳戶配置（總計[\d,]+萬，目標1,000萬達成[\d.]+%）',
    f'基金帳戶配置（總計{_ftw:,}萬，目標1,000萬達成{_fach}%）',_fseg,count=1)
_fnm={"鉅亨":"鉅亨基金總額","HSBC":"HSBC結構型商品","基富通":"基富通基金總額"}
for _f in FUND:
    _n=_fnm[_f['code']]
    _fseg=re.sub(rf'({_n}</div><div[^>]*>[^<]*</div></div>\s*<div style="text-align:right"><div[^>]*>)[\d,]+萬(</div><div[^>]*>)[\d.]+%',
        rf'\g<1>{_f["val"]:.0f}萬\g<2>{_f["pct"]}%',_fseg,count=1)
_fseg=re.sub(r'再追加 ?\d+萬即可達成基金目標1,000萬（已達 [\d.]+%）',
    f'再追加 {max(0,1000-_ftw)}萬即可達成基金目標1,000萬（已達 {_fach}%）',_fseg,count=1)
html=html[:_fs]+_fseg+html[_fe:]
print(f"  ✅ 基金分頁（{_ftw:,}萬 / {_fach}%）")

# 美股洞察 SGOV 敘述（動態）
_sgpct=round(_sgv0/V['us_w']*100,1) if (_sgv0:=round(sum(sh for _,c,sh,_ in US if c=='SGOV')*[p for _,c,_,p in US if c=='SGOV'][0]*usd/10000,1)) else 0
html=re.sub(r'SGOV（[\d,]+萬/[\d.]+%）',f'SGOV（{_sgv0:.0f}萬/{_sgpct}%）',html,count=1)

# ── 完整持股 Pareto 表（跨券商合併）──
_TC={"個股":"#E24B4A","ETF":"#378ADD","槓桿":"#EF9F27","主動ETF":"#1D9E75","現金替代":"#7F77DD"}
def _pareto(rows, fx, tab, mkt, isus):
    global html
    ag={}
    for b,c,sh,p in rows:
        e=ag.setdefault(c,{'sh':0,'p':p,'v':0.0,'bk':set()})
        e['sh']+=sh; e['p']=p; e['v']+=sh*p*fx/10000; e['bk'].add(b)
    it=sorted(ag.items(), key=lambda z:-z[1]['v'])
    tot=sum(v['v'] for _,v in it); mx=it[0][1]['v']; cum=0; tr=''
    for i,(c,v) in enumerate(it,1):
        pct=v['v']/tot*100; cum+=pct; col=_TC.get(typ(c),'#999')
        sh=f"{v['sh']:,.1f}".rstrip('0').rstrip('.') if v['sh']%1 else f"{int(v['sh']):,}"
        pr=f"${v['p']:,.2f}" if isus else f"{v['p']:,.2f}"
        tr+=f'''
        <tr><td style="padding:6px 8px;color:var(--hint);font-size:11px">{i}</td>
          <td style="padding:6px 8px;font-weight:600">{c}</td>
          <td style="padding:6px 8px;font-size:12px">{NAMES.get(c,c)}</td>
          <td style="padding:6px 8px;text-align:right;font-variant-numeric:tabular-nums">{sh}</td>
          <td style="padding:6px 8px;text-align:right;font-size:11px;color:var(--muted)">{pr}</td>
          <td style="padding:6px 8px;text-align:right;font-weight:700">{v["v"]:.1f}</td>
          <td style="padding:6px 8px;text-align:right;font-weight:600;color:{col}">{pct:.1f}%</td>
          <td style="padding:6px 8px;min-width:90px"><div style="background:var(--bg);border-radius:3px;height:14px">
            <div style="background:{col};width:{v["v"]/mx*100:.1f}%;height:100%;border-radius:3px"></div></div></td>
          <td style="padding:6px 8px;text-align:right;font-size:11px;color:var(--muted)">{cum:.1f}%</td>
          <td style="padding:6px 8px;font-size:10px;color:var(--hint)">{"、".join(sorted(v["bk"]))}</td></tr>'''
    t5=sum(v['v'] for _,v in it[:5])/tot*100; t10=sum(v['v'] for _,v in it[:10])/tot*100
    n80=next(i for i,_ in enumerate(it,1) if sum(v['v'] for _,v in it[:i])/tot>=0.8)
    _s=html.find(f'id="{tab}"'); _e=html.find('<!-- ════',_s); _sg=html[_s:_e]
    _sg=re.sub(r'完整持股 Pareto（\d+檔，總計 [\d,]+萬）',f'完整持股 Pareto（{len(it)}檔，總計 {tot:,.0f}萬）',_sg,count=1)
    _sg=re.sub(r'前5大 <b>[\d.]+%</b>',f'前5大 <b>{t5:.1f}%</b>',_sg,count=1)
    _sg=re.sub(r'前10大 <b>[\d.]+%</b>',f'前10大 <b>{t10:.1f}%</b>',_sg,count=1)
    _sg=re.sub(r'前 <b>\d+</b> 檔即佔 80%',f'前 <b>{n80}</b> 檔即佔 80%',_sg,count=1)
    _sg=re.sub(r'前 \d+ 檔就佔 80%，其餘 \d+ 檔',f'前 {n80} 檔就佔 80%，其餘 {len(it)-n80} 檔',_sg,count=1)
    _i=_sg.find('完整持股 Pareto')
    _sg=_sg[:_i]+re.sub(r'(<tbody>)[\s\S]*?(</tbody>)',lambda m:m.group(1)+tr+'\n      '+m.group(2),_sg[_i:],count=1)
    html=html[:_s]+_sg+html[_e:]
    return len(it),tot
_n1,_t1=_pareto(TW,1.0,'tab-pareto-tw','台股',False)
_n2,_t2=_pareto(US,usd,'tab-pareto-us','美股',True)
print(f"  ✅ Pareto 表（台股{_n1}檔/{_t1:,.0f}萬、美股{_n2}檔/{_t2:,.0f}萬）")

print("  ✅ Bar Chart 標題")

print("  ✅ 日股明細表")

print("  ✅ HTML bar (日股/基金)")

# 靜態欄位
for pat,rep,tag in [
 (r'Google Drive 即時同步｜[\d/]+(?: v[\d\-]+)?｜',f'Google Drive 即時同步｜{GD["date"]}｜','日期'),
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
 (r'(metric-value" style="color:#1D9E75">)[\d.]+',rf'\g<1>{V["maint"]}','維持率數值'),
 (r'(質借餘額</div><div class="metric-value">)\d+',rf'\g<1>{V["pledge_w"]}','質借餘額'),
 (r'(年利息支出</div><div class="metric-value warn">)[\d.]+',rf'\g<1>{V["interest"]}','質借年息'),
 (r'left:[\d.]+%;top:-6px',f'left:{V["bar"]}%;top:-6px','維持率刻度'),
 (r'維持率 [\d.]+%，遠高於追繳線',f'維持率 {V["maint"]}%，遠高於追繳線','維持率說明'),
 (r'擔保品需跌 <b>[\d.]+%</b>',f'擔保品需跌 <b>{V["drop_call"]}%</b>','追繳跌幅'),
 (r'"USDTWD":[\d.]+,',f'"USDTWD":{usd},','USD匯率'),
 (r'"JPYTWD":[\d.]+,',f'"JPYTWD":{jpy},','JPY匯率'),
]:
    sub(pat,rep,tag)
for c,x in twA.items(): html=re.sub(rf'"{c}":(?!\d{{4}})[\d.]+,',f'"{c}":{round(x["p"],2)},',html)
for c in JP: html=re.sub(rf'"{c}\.T":[\d.]+,',f'"{c}.T":{JP[c]["p"]},',html)
print("  ✅ 靜態欄位 + FALLBACK")

# 融資維持率：壓力測試表 + 明細表重建
_cl,_pl=V['collat'],V['pledge_w']
_rows=''.join(f"""<tr>
          <td style="padding:7px 8px;font-weight:500">-{d}%</td>
          <td style="padding:7px 8px;text-align:right">{round(_cl*(1-d/100)):,}萬</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600;color:{'#1D9E75' if _cl*(1-d/100)/_pl*100>=250 else '#EF9F27' if _cl*(1-d/100)/_pl*100>=166 else '#E24B4A'}">{round(_cl*(1-d/100)/_pl*100)}%</td>
          <td style="padding:7px 8px;color:var(--muted)">{'安全' if _cl*(1-d/100)/_pl*100>=250 else '注意' if _cl*(1-d/100)/_pl*100>=166 else '追繳'}</td>
        </tr>""" for d in [10,20,30,40,50,60,70])
html=re.sub(r'(壓力測試 — 台股下跌情境[\s\S]*?<tbody>)[\s\S]*?(</tbody>)',
    lambda m:m.group(1)+'\n        '+_rows+'\n      '+m.group(2),html,count=1)
html=re.sub(r'即使台股腰斬（-50%），維持率仍有 \d+%',
    f'即使台股腰斬（-50%），維持率仍有 {round(_cl*0.5/_pl*100)}%',html,count=1)
html=re.sub(r'(擔保品市值（永豐台股）</td><td style="padding:7px 8px;text-align:right;font-weight:600">)[\d,]+萬',
    rf'\g<1>{_cl:,}萬',html,count=1)
html=re.sub(r'(質借餘額</td><td style="padding:7px 8px;text-align:right;font-weight:600;color:#E24B4A">)[\d,]+萬',
    rf'\g<1>{_pl:,}萬',html,count=1)
html=re.sub(r'(可再質借額度（估）</td><td[^>]*>)[\d,-]+萬',rf'\g<1>{round(_cl*0.6-_pl):,}萬',html,count=1)
html=re.sub(r'(追繳觸發擔保品</td><td[^>]*>)[\d,]+萬',rf'\g<1>{round(_pl*1.66):,}萬',html,count=1)
html=re.sub(r'(斷頭觸發擔保品</td><td[^>]*>)[\d,]+萬',rf'\g<1>{round(_pl*1.30):,}萬',html,count=1)
html=re.sub(r'質借年息 [\d.]+萬，需靠股息覆蓋。目前年股息 [\d.]+萬，覆蓋後淨收 [\d.-]+萬',
    f'質借年息 {V["interest"]}萬，需靠股息覆蓋。目前年股息 {V["div_w"]}萬，覆蓋後淨收 {round(V["div_w"]-V["interest"],1)}萬',html,count=1)
_lev_tw=round(sum(s*p for _,c,s,p in TW if typ(c)=='槓桿')/10000)
html=re.sub(r'台股含槓桿ETF約 [\d,]+萬',f'台股含槓桿ETF約 {_lev_tw:,}萬',html,count=1)
print("  ✅ 融資維持率分頁")

# ── 總覽頁：各類資產現值 / 負債 / 基金帳戶（先前遺漏）──
_cats=[("台股","#378ADD",V['tw_w'],V['tw_a']),("美股","#1D9E75",V['us_w'],V['us_a']),
       ("日股","#EF9F27",V['jp_w'],V['jp_a']),("基金","#7F77DD",V['fd_w'],V['fd_a'])]
_rows=''.join(
  f'<div class="risk-row"><div class="risk-label" style="color:{col};width:120px">{nm} {v:,}萬</div>'
  f'<div style="flex:1"><div class="risk-bar-bg"><div class="risk-bar-fill" style="width:{min(round(a),100)}%;background:{col}"></div></div></div>'
  f'<div class="risk-val" style="color:{col}">{a}%</div></div>\n      '
  for nm,col,v,a in _cats)
_os=html.find('<div class="stitle">各類資產現值</div>')
_oe=html.find('    </div>',_os)
html=html[:_os]+'<div class="stitle">各類資產現值</div>\n'+_rows+html[_oe:]

# 負債區塊
_mort_r,_pl_r=2.8,3.8
_tot_int=round(V['mort_w']*_mort_r/100+V['pledge_w']*_pl_r/100,1)
html=re.sub(r'(房貸</div><div[^>]*>星展-東方文華 @)[\d.]+(%</div><div class="risk-val[^>]*>)[\d,]+萬',
    rf'\g<1>{_mort_r}\g<2>{V["mort_w"]:,}萬',html,count=1)
html=re.sub(r'(股票質借</div><div[^>]*>永豐台股 @)[\d.]+(%</div><div class="risk-val[^>]*>)[\d,]+萬',
    rf'\g<1>{_pl_r}\g<2>{V["pledge_w"]:,}萬',html,count=1)
html=re.sub(r'年利息支出約 [\d,]+萬',f'年利息支出約 {_tot_int:.0f}萬',html,count=1)
html=re.sub(r'年股息 [\d,]+萬，淨現金流 [+\-\d,]+萬',
    f'年股息 {V["div_w"]:.0f}萬，淨現金流 +{round(V["div_w"]-_tot_int):,}萬',html,count=1)

# 基金帳戶區塊
_frows=''.join(
  f'<div class="risk-row"><div class="risk-label" style="width:140px">{f["name"]}</div>'
  f'<div style="flex:1"><div class="risk-bar-bg"><div class="risk-bar-fill" style="width:{round(f["pct"])}%;background:{f["color"]}"></div></div></div>'
  f'<div class="risk-val">{f["val"]:.0f}萬</div></div>\n      '
  for f in FUND)
html=re.sub(r'(<div class="stitle">基金帳戶</div>\n)(?:.*\n)*?(?=      <div class="risk-row"><div class="risk-label" style="width:140px">基金小計)', lambda m:m.group(1)+_frows, html, count=1)
html=re.sub(r'(基金小計[^>]*>)[\d,]+萬',rf'\g<1>{V["fd_w"]:,}萬',html,count=1)
print("  ✅ 總覽頁（資產現值/負債/基金帳戶）")

# 月曆 + 走勢圖
cc=round((GD['total']-GD['prev'])/10000,1); cp=round((GD['total']-GD['prev'])/GD['prev']*100,2)
# 解析既有 CAL_DATA → 更新/新增當日 → 依日期排序重建
_m=re.search(r'const CAL_DATA\s*=\s*(\{[\s\S]*?\});',html)
_cal=dict((d,(v,c,p)) for d,v,c,p in
    re.findall(r'"(\d{4}-\d{2}-\d{2})":\{"v":([\d.]+),"c":([-\d.]+),"p":([-\d.]+)\}',_m.group(1)))
_cal[GD['ymd']]=(str(V['total_w']),str(cc),str(cp))
# 回填 GD_HIST 中缺漏的日期（漏更新那天不會消失）
_hd=sorted(GD_HIST)
for _i,_d in enumerate(_hd):
    _pv=GD_HIST[_hd[_i-1]] if _i>0 else GD_HIST[_d]
    _tv=GD_HIST[_d]
    _new=(str(round(_tv/10000)),str(round((_tv-_pv)/10000,1)),str(round((_tv-_pv)/_pv*100,2)))
    if _d not in _cal: print(f"  ✅ 月曆回填 {_d}: {_new[0]}萬")
    _cal[_d]=_new
html=re.sub(r'const CAL_DATA\s*=\s*\{[\s\S]*?\};',
    'const CAL_DATA = {'+','.join(f'"{d}":{{"v":{v},"c":{c},"p":{p}}}'
        for d,(v,c,p) in sorted(_cal.items()))+'};',html,count=1)
# CAL_MONTHS 自動補當月
# 淨資產月曆（同步追加）
_nm_=re.search(r'const NET_CAL_DATA = (\{[\s\S]*?\});',html)
if _nm_:
    _nc=dict(re.findall(r'"(\d{4}-\d{2}-\d{2})":\{"v":([\d.]+),"c":[-\d.]+,"p":[-\d.]+\}',_nm_.group(1)))
    _pn=(GD['prev']-_prevdebt)/10000 if (_prevdebt:=GD.get('prev_debt',GD['debt'])) else 0
    _nv=V['net_w']; _ncg=round(_nv-_pn,1); _npc=round(_ncg/_pn*100,2) if _pn else 0
    _nc[GD['ymd']]=str(_nv)
    _all=dict(re.findall(r'"(\d{4}-\d{2}-\d{2})":(\{"v":[\d.]+,"c":[-\d.]+,"p":[-\d.]+\})',_nm_.group(1)))
    # 回填 NET_HIST 缺漏日期（漏更新那天不會消失）──與 CAL_DATA 同步
    _nh=sorted(NET_HIST)
    for _i,_d in enumerate(_nh):
        _prev=NET_HIST[_nh[_i-1]] if _i>0 else NET_HIST[_d]
        _cur=NET_HIST[_d]
        _v=round(_cur/10000); _c=round((_cur-_prev)/10000,1)
        _p=round((_cur-_prev)/_prev*100,2) if _prev else 0
        if _d not in _all: print(f"  ✅ 淨資產月曆回填 {_d}: {_v}萬")
        _all[_d]=f'{{"v":{_v},"c":{_c},"p":{_p}}}'
    _all[GD['ymd']]=f'{{"v":{_nv},"c":{_ncg},"p":{_npc}}}'
    html=re.sub(r'const NET_CAL_DATA = \{[\s\S]*?\};',
        'const NET_CAL_DATA = {'+','.join(f'"{k}":{v}' for k,v in sorted(_all.items()))+'};',html,count=1)
    print(f"  ✅ 淨資產月曆（{len(_all)}筆，末筆 {_nv}萬 {_ncg:+}萬）")

_ym=GD['ymd'][:7]
_mm=re.search(r'const CAL_MONTHS\s*=\s*(\[[^\]]+\])',html)
_months=json.loads(_mm.group(1))
if _ym not in _months:
    _months.append(_ym); _months.sort()
    html=re.sub(r'const CAL_MONTHS\s*=\s*\[[^\]]+\]',
        'const CAL_MONTHS = '+json.dumps(_months),html,count=1)
    print(f"  ✅ CAL_MONTHS 新增 {_ym}")

# MONTH_NAMES 同步補齊（無條件執行；缺漏會導致月份標題空白）
_nm=re.search(r'const MONTH_NAMES\s*=\s*(\{[^}]*\})',html)
_names=json.loads(_nm.group(1))
_mm2=re.search(r'const CAL_MONTHS\s*=\s*(\[[^\]]+\])',html)
for _k in json.loads(_mm2.group(1)):
    if _k not in _names: _names[_k]=f"{_k[:4]}年 {int(_k[5:7])}月"
if _names!=json.loads(_nm.group(1)):
    html=re.sub(r'const MONTH_NAMES\s*=\s*\{[^}]*\}',
        'const MONTH_NAMES = '+json.dumps(_names,ensure_ascii=False),html,count=1)
    print(f"  ✅ MONTH_NAMES 補齊 → {list(_names)}")
md=GD['ymd'][5:].replace('-','/')
_TA=[('HD',f'"{md}"'),('HT',V['total_w']),('HN',V['net_w']),('HDbt',V['debt_w']),
     ('HTW',V['tw_w']),('HUS',V['us_w']),('HJP',V['jp_w']),('HFD',V['fd_w'])]
# 以 HD 是否已含當日判斷「本次是否為新交易日」，確保 8 陣列同步追加
_hd=re.search(r'const HD=\[([^\]]*)\]',html).group(1).split(',')
_isnew = _hd[-1].strip().strip('"') != md
for a,v in _TA:
    if not _isnew: continue
    m=re.search(rf'const {a}=\[([^\]]*)\]',html)
    html=html[:m.end()-1]+f',{v}'+html[m.end()-1:]
# 長度補齊（向後補當期值）
_mx=max(len(re.search(rf'const {a}=\[([^\]]*)\]',html).group(1).split(',')) for a,_ in _TA)
for a,v in _TA:
    _m=re.search(rf'const {a}=\[([^\]]*)\]',html); _v=_m.group(1).split(',')
    if len(_v)<_mx:
        _v=_v+[str(v)]*(_mx-len(_v))
        html=re.sub(rf'const {a}=\[[^\]]*\]',f'const {a}=[{",".join(_v)}]',html,count=1)
print(f"  ✅ 月曆 + 走勢圖（{'新增' if _isnew else '更新'} {md}，{_mx}筆）")

# ══ ④ 反向驗證：從 HTML 解析回來對帳 ══
print("\n── 反向驗證（解析 HTML 對帳 Google Drive）──")
errs=[]
# HTML 結構完整性（div 不平衡會導致分頁全部疊在一起）
_g=html.count('<div')-html.count('</div>')
_bd=html[html.find('<body>'):html.rfind('<script>')]
_b=_bd.count('<div')-_bd.count('</div>')
if _g!=0: errs.append(f"div 不平衡（全域 {_g:+}）")
elif _b!=0: errs.append(f"div 不平衡（body {_b:+}）")
else: print("  ✅ HTML div 結構平衡")
_nt=len(re.findall(r'id="tab-[\w-]+"',html))
if _nt!=18: errs.append(f"分頁數異常 {_nt}（應18）")
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
  (f'>{V["lev"]}<','槓桿ETF'),(f'即時同步｜{GD["date"]}｜','日期'),(f'"{GD["ymd"]}"','月曆'),
  (f"drawGauge('g-tw',{V['tw_a']},",'油表台'),(f'"USDTWD":{usd}','USD匯率')]:
    if pat not in html: errs.append(f"{d} 未更新")

# CSS 完整性（防止無錨點正則改壞版面）
css=html[html.find('<style>'):html.find('</style>')]
bad=[(m.group(1),m.group(2)) for m in re.finditer(r'([.\w-]+)\{[^}]*?width:([\d.]+)%',css)
     if m.group(2) not in ('100','50','33','25')]
if bad: errs.append(f"CSS width 異常: {bad}")
else: print("  ✅ CSS 完整性")

# 日股明細表與資料源一致性
_s2=html.find('id="tab-pareto-jp"'); _e2=html.find('<!-- ════',_s2+10)
_tbl=html[_s2:_e2]
for _d in jp_d:
    _p=JP[_d['code']]['p']
    if f'¥{_p:,}' not in _tbl: errs.append(f"日股明細表 {_d['code']} 股價非 ¥{_p:,}")
    elif f'{_d["val"]}萬' not in _tbl: errs.append(f"日股明細表 {_d['code']} 估值非 {_d['val']}萬")
if not [e for e in errs if '日股明細表' in e]:
    print(f"  ✅ 日股明細表與資料源一致（{jp_d[0]['code']} ¥{JP[jp_d[0]['code']]['p']:,}）")

# 總覽頁各類資產現值
for _nm,_v,_a in [("台股",V['tw_w'],V['tw_a']),("美股",V['us_w'],V['us_a']),
                  ("日股",V['jp_w'],V['jp_a']),("基金",V['fd_w'],V['fd_a'])]:
    if f'{_nm} {_v:,}萬' not in html: errs.append(f"總覽 {_nm} 現值未更新（應{_v:,}萬）")
if not [e for e in errs if '總覽' in e]: print("  ✅ 總覽頁各類資產現值")

# Bar Chart 標題與資料一致
if f"台股持股（{V['tw_w']:,}萬" not in html: errs.append("台股Bar標題未更新")
elif f"美股持股（{V['us_w']:,}萬" not in html: errs.append("美股Bar標題未更新")
else: print(f"  ✅ Bar Chart 標題（台股{V['tw_w']:,}萬/美股{V['us_w']:,}萬）")

# 現金管理頁
if f'>{_ct:.0f}<' not in html: errs.append(f"現金合計 {_ct}萬 未更新")
else: print(f"  ✅ 現金管理頁 {_ct}萬（{_cp}%）")

# 基金分頁 vs 油表一致
if f'總計{_ftw:,}萬' not in html: errs.append(f"基金分頁標題非 {_ftw:,}萬")
elif f"drawGauge('g-fd',{_fach}," not in html: errs.append(f"基金油表非 {_fach}%")
else: print(f"  ✅ 基金分頁與油表一致（{_ftw:,}萬/{_fach}%）")

# Pareto 表與資料一致
if f'完整持股 Pareto（{_n1}檔，總計 {_t1:,.0f}萬）' not in html: errs.append(f"台股Pareto表未更新")
elif f'完整持股 Pareto（{_n2}檔，總計 {_t2:,.0f}萬）' not in html: errs.append(f"美股Pareto表未更新")
else: print(f"  ✅ Pareto 表一致")

# 淨資產月曆
if f'"{GD["ymd"]}":{{"v":{V["net_w"]}' not in html: errs.append("淨資產月曆當日未更新")
else: print(f"  ✅ 淨資產月曆末筆 {V['net_w']}萬")

# 融資維持率
if f'>{V["maint"]}<' not in html: errs.append(f"維持率 {V['maint']}% 未更新")
elif f'left:{V["bar"]}%' not in html: errs.append("維持率刻度未更新")
else: print(f"  ✅ 融資維持率 {V['maint']}%（擔保品{V['collat']}萬/質借{V['pledge_w']}萬）")

# 走勢圖 8 陣列長度一致（不一致會導致負債線等提早中斷）
_TL={_a:len(re.search(rf'const {_a}=\[([^\]]+)\]',html).group(1).split(','))
     for _a in ['HD','HT','HN','HDbt','HTW','HUS','HJP','HFD']}
if len(set(_TL.values()))!=1: errs.append(f"走勢圖長度不一致: {_TL}")
else: print(f"  ✅ 走勢圖 8 陣列長度一致（{list(_TL.values())[0]}筆）")

# 月曆完整性
_m=re.search(r'const CAL_DATA\s*=\s*(\{[\s\S]*?\});',html)
_e=re.findall(r'"(\d{4}-\d{2}-\d{2})":\{"v":([\d.]+)',_m.group(1))
if not _e or _e[-1][0]!=GD['ymd']: errs.append(f"月曆最後一筆非當日({_e[-1][0] if _e else 'None'})")
elif int(float(_e[-1][1]))!=V['total_w']: errs.append(f"月曆當日數值錯({_e[-1][1]}≠{V['total_w']})")
elif [d for d,_ in _e]!=sorted(d for d,_ in _e): errs.append("月曆日期未排序")
else:
    _miss=[d for d in GD_HIST if f'"{d}"' not in html]
    if _miss: errs.append(f"月曆缺漏日期: {_miss}")
    else: print(f"  ✅ 月曆 {len(_e)}筆，末筆 {_e[-1][0]}={_e[-1][1]}萬（GD_HIST 全數在列）")

# 兩個月曆日期必須一致（抓出「淨資產月曆沒更新」這類漏洞）
_c1=set(re.findall(r'"(\d{4}-\d{2}-\d{2})"',re.search(r'const CAL_DATA\s*=\s*(\{[\s\S]*?\});',html).group(1)))
_n1_=re.search(r'const NET_CAL_DATA = (\{[\s\S]*?\});',html)
_c2=set(re.findall(r'"(\d{4}-\d{2}-\d{2})"',_n1_.group(1))) if _n1_ else set()
_lo=min(_c2) if _c2 else None
_gap=sorted(d for d in _c1 if _lo and d>=_lo and d not in _c2)
if _gap: errs.append(f"淨資產月曆缺漏 {len(_gap)} 天: {_gap[:8]}")
else: print(f"  ✅ 兩月曆日期一致（資產{len(_c1)}筆 / 淨資產{len(_c2)}筆）")
_mm=re.search(r'const CAL_MONTHS\s*=\s*(\[[^\]]+\])',html)
_ms=json.loads(_mm.group(1))
_nm2=json.loads(re.search(r'const MONTH_NAMES\s*=\s*(\{[^}]*\})',html).group(1))
if GD['ymd'][:7] not in _ms: errs.append(f"CAL_MONTHS 缺 {GD['ymd'][:7]}")
elif [k for k in _ms if k not in _nm2]: errs.append(f"MONTH_NAMES 缺 {[k for k in _ms if k not in _nm2]}")
else: print(f"  ✅ CAL_MONTHS/MONTH_NAMES 完整（{len(_ms)}個月）")

# 全站殘留舊數字掃描（任何前期數值出現即中止）
_bd2=html[html.find('<body>'):html.rfind('<script>')]
_stale=[]
for _v in [f"{V['tw_w']:,}萬",f"{V['us_w']:,}萬",f"{V['jp_w']:,}萬",f"{_ftw:,}萬"]: pass
# 只檢查「確定非當期」的舊值（避免與當期數字巧合而誤判）
_cur={f"{V['tw_w']:,}萬",f"{V['us_w']:,}萬",f"{V['jp_w']:,}萬",f"{_ftw:,}萬",
      f"{V['total_w']:,}萬",f"{V['net_w']:,}萬",f"{_ct:.0f}萬",f"{_sgv:.0f}萬",
      f"{V['mort_w']:,}萬",f"{V['pledge_w']:,}萬"}
_known_old=[v for v in ['869萬','357萬','4,460萬','2,242萬','3,505萬'] if v not in _cur]
_stale=[v for v in _known_old if v in _bd2]
if _stale: errs.append(f"殘留舊數字: {_stale}")
else: print("  ✅ 無殘留舊數字")

# JS 語法
open('/home/claude/rf/c.js','w').write(html[html.rfind('<script>')+8:html.rfind('</script>')])
r=subprocess.run(['node','--check','/home/claude/rf/c.js'],capture_output=True,text=True)
if r.returncode: errs.append(f"JS 語法錯誤: {r.stderr[:120]}")
else: print("  ✅ JS 語法")

# ══ ⑤ 通過才 push ══
if errs:
    print(f"\n⛔ {len(errs)} 項未通過，中止 push：")
    for e in errs: print(f"   • {e}")
    raise SystemExit(1)

print("\n✅ 全部驗證通過")
open('/home/claude/rf/retireflow_full.html','w',encoding='utf-8').write(html)
shutil.copy('/home/claude/rf/retireflow_full.html','/home/claude/rf/RetireFlow_Dashboard_v2.html')
T=os.environ.get("GH_TOKEN","")
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
