#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# GPDP / 15th Finance Commission grant dashboard  (Bihar, FY 2024-25)
# Builds a single self-contained offline dashboard.html (Plotly inlined).
# Mirrors the Jeevika MIS dashboard structure (3 tabs, maroon house style).
#
# Story (two honest facts):
#   A) ~32% of 15FC grant money sits UNSPENT - and underspending is SYSTEMIC,
#      not selective: utilisation is flat across GP types; the only real
#      variation is across districts (administrative, not GP-characteristic).
#   B) Per-capita resources are steeply unequal by SCALE: small/compact GPs
#      receive and spend far more per resident. An allocation gradient, not
#      differential effort.
#
# Run:  python3 gpdp_build_dashboard.py
# -----------------------------------------------------------------------------
import json, numpy as np, pandas as pd
import statsmodels.formula.api as smf
import plotly.graph_objects as go
import plotly.io as pio

# ---- paths -------------------------------------------------------------------
GP   = "/mnt/c/Users/shara/Dropbox/Peer Effects and Role Models/GPDP Analysis (For Non-Peer)"
PEER = "/mnt/c/Users/shara/Dropbox/Peer Effects and Role Models/Analysis_Experiment"
GEO  = "/mnt/c/Users/shara/Dropbox/Bihar Gates Team/3_Jeevika/4_MIS_Dashboard_Data/2_Data/3_Geo/bihar_districts.geojson"
OUT  = "/mnt/c/Users/shara/Dropbox/Bihar Gates Team/4_Policy Briefs/GPDP/dashboard.html"

# ---- palette -----------------------------------------------------------------
MAROON="#800019"; MAROON_D="#5c0012"; INK="#222"; MUTE="#6b6b6b"; PAPER="#ffffff"
GRID="#e9e6e2"; GOLD="#b8860b"
# high-contrast ramps (more stops so mid-range districts separate visually)
SEQ=[[0,"#fff3b0"],[0.25,"#f6a350"],[0.5,"#e34a33"],[0.75,"#b30f2a"],[1,MAROON]]   # unspent: yellow->maroon
SEQ_B=[[0,"#eaf3fb"],[0.25,"#9ec9e8"],[0.5,"#4a90c4"],[0.75,"#2166ac"],[1,"#0b3d6b"]]  # spending: light->deep blue

pio.templates.default="none"
FONT=dict(family="Georgia, 'Times New Roman', serif", color=INK)

# ---- load & build analysis frame --------------------------------------------
def load():
    x=pd.read_stata(f"{GP}/ugp_xvfc_2024_25.dta")
    x=x[x['matched']==1].copy()
    c=pd.read_stata(f"{PEER}/3_Analyse/Input/Administrative Data/NREGA/GPExtendedControls_clean.dta")
    c=c[['UGP','Tot_Pop2011C','SCGPProp2011C','Villages','TotalArea','DistHQDis','NearTownDis']].rename(columns={'UGP':'ugp'})
    r=pd.read_stata(f"{PEER}/1_Raw/Input/Raw Excel Politician Files/Reservation_Pop_F.dta")
    r=r[['ugp','sc_reserved_2016','women_2016']]
    d=x.merge(c,on='ugp',how='inner').merge(r,on='ugp',how='inner')

    d['avail']=d['consolidated_total_opening_balan']+d['consolidated_total_direct_receip']+d['consolidated_total_auto_receipt']
    d['exp']=d['consolidated_total_expenditure']; d['unspent']=d['consolidated_total_unspent_balan']
    d=d[d['avail']>0].copy()
    d['unspent_share']=d['unspent']/d['avail']
    d['util']=d['exp']/d['avail']
    d['exp_pc']=d['exp']/d['Tot_Pop2011C']
    d['grant_pc']=d['avail']/d['Tot_Pop2011C']
    d['tied_pc']=d['tied_grant_expenditure']/d['Tot_Pop2011C']        # earmarked (water/sanitation/etc.)
    d['untied_pc']=d['basic_grant_untied_expenditure']/d['Tot_Pop2011C']  # flexible
    d['pop_k']=d['Tot_Pop2011C']/1000
    # trim implausible per-cap (tiny pop) and top 1% outliers
    d=d[d['Tot_Pop2011C']>200]
    d=d[(d['exp_pc']<np.nanpercentile(d['exp_pc'],99))&(d['grant_pc']<np.nanpercentile(d['grant_pc'],99))]
    d['district']=d['districtname'].replace({'KAIMUR (BHABUA)':'KAIMUR'})
    return d

D=load()
N=len(D)
TOT_AVAIL=D['avail'].sum(); TOT_EXP=D['exp'].sum(); TOT_UNS=D['unspent'].sum()
AGG_UNS=TOT_UNS/TOT_AVAIL*100

PRED={'pop_k':'Population','SCGPProp2011C':'SC pop. share','Villages':'No. of villages',
      'TotalArea':'Geographic area','DistHQDis':'Dist. to district HQ','NearTownDis':'Dist. to town',
      'sc_reserved_2016':'SC-reserved seat','women_2016':'Women-reserved seat'}
for p in PRED: D['z_'+p]=(D[p]-D[p].mean())/D[p].std()

def betas(outcome):
    out=[]
    for p,lab in PRED.items():
        dd=D[[outcome,'z_'+p,'district']].dropna()
        m=smf.ols(f"{outcome} ~ z_{p} + C(district)",data=dd).fit(cov_type='HC1')
        out.append(dict(pred=p,label=lab,beta=m.params['z_'+p],se=m.bse['z_'+p],p=m.pvalues['z_'+p]))
    return pd.DataFrame(out)

B_uns=betas('unspent_share'); B_exp=betas('exp_pc')

# district aggregates
G=D.groupby('district').agg(unspent=('unspent_share','mean'),util=('util','mean'),
    exp_pc=('exp_pc','mean'),grant_pc=('grant_pc','mean'),
    avail=('avail','sum'),exp=('exp','sum'),unspent_amt=('unspent','sum'),n=('ugp','size')).reset_index()
G['unspent']*=100; G['util']*=100
G['low']=G['n']<10

# population quintiles
D['popq']=pd.qcut(D['Tot_Pop2011C'],5,labels=['Smallest\n20%','Q2','Q3','Q4','Largest\n20%'])
Q=D.groupby('popq',observed=True).agg(pop=('Tot_Pop2011C','mean'),grant_pc=('grant_pc','mean'),
    exp_pc=('exp_pc','mean'),tied_pc=('tied_pc','mean'),untied_pc=('untied_pc','mean'),
    total_exp=('exp','mean'),util=('util','mean'),unspent=('unspent_share','mean')).reset_index()
Q['util']*=100; Q['unspent']*=100
PC_RATIO=Q['exp_pc'].iloc[0]/Q['exp_pc'].iloc[-1]          # small vs large per-capita spending
PC_SMALL=Q['exp_pc'].iloc[0]; PC_LARGE=Q['exp_pc'].iloc[-1]
TOT_RATIO=Q['total_exp'].iloc[-1]/Q['total_exp'].iloc[0]   # large vs small total spending

GEOJSON=json.load(open(GEO))
geo_names=set(f['properties']['dist'] for f in GEOJSON['features'])
assert set(G['district']).issubset(geo_names), set(G['district'])-geo_names

print(f"N={N}  granted ₹{TOT_AVAIL/1e7:.0f}cr  spent ₹{TOT_EXP/1e7:.0f}cr  unspent ₹{TOT_UNS/1e7:.0f}cr ({AGG_UNS:.1f}%)")

# ---- figure helpers ----------------------------------------------------------
def base_layout(fig,h=430,title=None):
    fig.update_layout(font=FONT,paper_bgcolor=PAPER,plot_bgcolor=PAPER,height=h,
        margin=dict(l=60,r=30,t=50 if title else 24,b=50),title=title,
        title_font=dict(size=16,color=MAROON_D))
    fig.update_xaxes(gridcolor=GRID,zeroline=False,linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID,zeroline=False,linecolor=GRID)
    return fig

def sig_stars(p): return '★★★' if p<.001 else '★★' if p<.01 else '★' if p<.05 else '†' if p<.10 else 'n.s.'

# ---- TAB A: choropleth + ranked bar of unspent share -------------------------
def fig_map_unspent():
    g=G[~G['low']]                                   # drop thin-coverage districts (ARWAL)
    zlo,zhi=np.floor(g['unspent'].min()),np.ceil(g['unspent'].max())
    fig=go.Figure(go.Choropleth(geojson=GEOJSON,locations=g['district'],z=g['unspent'],
        featureidkey='properties.dist',colorscale=SEQ,zmin=zlo,zmax=zhi,
        marker_line_color='white',marker_line_width=0.5,
        colorbar=dict(title='% unspent',thickness=14,len=0.8),
        customdata=np.stack([g['n']],-1),
        hovertemplate='<b>%{location}</b><br>Unspent: %{z:.0f}%<br>GPs: %{customdata[0]}<extra></extra>'))
    fig.update_layout(geo=dict(fitbounds="locations",visible=False,projection_type="mercator",
        bgcolor=PAPER))  # same config as the Jeevika dashboard
    base_layout(fig,h=460); fig.update_layout(margin=dict(l=0,r=0,t=10,b=0))
    return fig

def fig_rank_unspent():
    g=G[~G['low']].sort_values('unspent')
    fig=go.Figure(go.Bar(y=g['district'],x=g['unspent'],orientation='h',
        marker=dict(color=g['unspent'],colorscale=SEQ,line=dict(width=0)),
        customdata=np.stack([g['n']],-1),
        hovertemplate='<b>%{y}</b><br>Unspent: %{x:.0f}%<br>GPs: %{customdata[0]}<extra></extra>'))
    fig.add_vline(x=AGG_UNS,line=dict(color=GOLD,width=2,dash='dash'))
    fig.add_annotation(x=AGG_UNS,y=g['district'].iloc[-1],text=f"State avg {AGG_UNS:.0f}%",
        showarrow=False,yshift=14,font=dict(color=GOLD,size=12))
    base_layout(fig,h=820)
    fig.update_layout(margin=dict(l=130,r=20,t=10,b=40))
    fig.update_xaxes(title="Share of 15FC funds unspent (%)")
    fig.update_yaxes(tickfont=dict(size=10))
    return fig

# ---- TAB B: drivers of unspent (flat) + utilisation flat across pop ----------
def fig_betas_unspent():
    b=B_uns.copy().sort_values('beta')
    b['pct']=b['beta']*100  # pct points per 1 SD
    fig=go.Figure(go.Bar(y=b['label'],x=b['pct'],orientation='h',
        marker=dict(color=[MAROON if pv<.05 else "#c9b8bb" for pv in b['p']]),
        text=[sig_stars(pv) for pv in b['p']],textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x:.2f} pp per 1 SD<extra></extra>'))
    fig.add_vline(x=0,line=dict(color=INK,width=1))
    base_layout(fig,h=430)
    fig.update_xaxes(title="Effect on unspent share (pp per 1 SD of characteristic)",range=[-1.2,1.2])
    fig.update_layout(margin=dict(l=160,r=40,t=10,b=50))
    return fig

def fig_util_flat():
    fig=go.Figure(go.Bar(x=Q['popq'],y=Q['util'],marker_color=MAROON,width=0.6,
        text=[f"{v:.0f}%" for v in Q['util']],textposition='outside',
        hovertemplate='%{x}<br>Utilisation: %{y:.0f}%<extra></extra>'))
    base_layout(fig,h=430)
    fig.update_yaxes(title="Funds utilised (%)",range=[0,90])
    fig.update_xaxes(title="GP population quintile")
    return fig

# ---- TAB C: drivers of per-cap spending + allocation gradient + scatter ------
def fig_betas_exp():
    b=B_exp.copy().sort_values('beta')
    fig=go.Figure(go.Bar(y=b['label'],x=b['beta'],orientation='h',
        marker=dict(color=["#1f4e79" if pv<.05 else "#b9c4d1" for pv in b['p']]),
        text=[sig_stars(pv) for pv in b['p']],textposition='outside',
        hovertemplate='<b>%{y}</b><br>₹%{x:.0f} per capita per 1 SD<extra></extra>'))
    fig.add_vline(x=0,line=dict(color=INK,width=1))
    base_layout(fig,h=430)
    fig.update_xaxes(title="Effect on spending per capita (₹ per 1 SD of characteristic)")
    fig.update_layout(margin=dict(l=160,r=50,t=10,b=50))
    return fig

def fig_percap_split():
    # stacked per-capita spending = earmarked (tied) + flexible (untied), by GP size
    tot=Q['tied_pc']+Q['untied_pc']
    fig=go.Figure()
    fig.add_bar(x=Q['popq'],y=Q['tied_pc'],name='Earmarked (water, sanitation, …)',marker_color="#1f4e79",
        hovertemplate='%{x}<br>Earmarked: ₹%{y:.0f}/cap<extra></extra>')
    fig.add_bar(x=Q['popq'],y=Q['untied_pc'],name='Flexible (untied)',marker_color="#9db8d6",
        hovertemplate='%{x}<br>Flexible: ₹%{y:.0f}/cap<extra></extra>')
    for xi,ti in zip(Q['popq'],tot):
        fig.add_annotation(x=xi,y=ti,text=f"₹{ti:.0f}",showarrow=False,yshift=12,
            font=dict(size=12,color=INK))
    base_layout(fig,h=430)
    fig.update_layout(barmode='stack',legend=dict(orientation='h',y=1.14,x=0.5,xanchor='center'),
        margin=dict(l=60,r=20,t=46,b=50))
    fig.update_yaxes(title="Spending per capita (₹)",range=[0,460])
    fig.update_xaxes(title="GP population quintile")
    return fig

def fig_scatter():
    # binned-mean scatter with dropdown over predictors (avoid 7700-pt overplot)
    items=[('pop_k','Population (000s)'),('TotalArea','Geographic area (ha)'),
           ('SCGPProp2011C','SC population share'),('DistHQDis','Distance to district HQ (km)')]
    fig=go.Figure(); buttons=[]; vis_blocks=[]
    for i,(col,lab) in enumerate(items):
        dd=D[[col,'exp_pc']].dropna().copy()
        dd['bin']=pd.qcut(dd[col],20,duplicates='drop')
        gb=dd.groupby('bin',observed=True).agg(x=(col,'mean'),y=('exp_pc','mean'),n=('exp_pc','size')).reset_index()
        fig.add_trace(go.Scatter(x=gb['x'],y=gb['y'],mode='markers+lines',
            marker=dict(size=9,color="#1f4e79"),line=dict(color="#9db8d6",width=1.5),
            visible=(i==0),name=lab,hovertemplate=f'{lab}: %{{x:.0f}}<br>Spent/cap: ₹%{{y:.0f}}<extra></extra>'))
        vis_blocks.append(i)
    for i,(col,lab) in enumerate(items):
        vis=[j==i for j in range(len(items))]
        buttons.append(dict(label=lab,method='update',args=[{'visible':vis},
            {'xaxis':{'title':lab,'gridcolor':GRID}}]))
    base_layout(fig,h=430)
    fig.update_layout(updatemenus=[dict(buttons=buttons,x=0,xanchor='left',y=1.16,yanchor='top',
        bgcolor='white',bordercolor=GRID)],margin=dict(l=60,r=20,t=60,b=50))
    fig.update_xaxes(title=items[0][1]); fig.update_yaxes(title="Spending per capita (₹)")
    return fig

def fig_map_exp():
    g=G[~G['low']]
    zlo,zhi=np.floor(g['exp_pc'].min()/10)*10,np.ceil(g['exp_pc'].max()/10)*10
    fig=go.Figure(go.Choropleth(geojson=GEOJSON,locations=g['district'],z=g['exp_pc'],
        featureidkey='properties.dist',colorscale=SEQ_B,zmin=zlo,zmax=zhi,
        marker_line_color='white',marker_line_width=0.5,
        colorbar=dict(title='₹/capita',thickness=14,len=0.8),
        hovertemplate='<b>%{location}</b><br>Spent/capita: ₹%{z:.0f}<extra></extra>'))
    fig.update_layout(geo=dict(fitbounds="locations",visible=False,projection_type="mercator",
        bgcolor=PAPER))  # same config as the Jeevika dashboard
    base_layout(fig,h=460); fig.update_layout(margin=dict(l=0,r=0,t=10,b=0))
    return fig

# ---- assemble HTML -----------------------------------------------------------
def div(fig,first=False):
    return pio.to_html(fig,include_plotlyjs=('inline' if first else False),full_html=False,
        config={'displayModeBar':False,'responsive':True})

figs=dict(mapU=fig_map_unspent(),rankU=fig_rank_unspent(),betaU=fig_betas_unspent(),
          utilF=fig_util_flat(),betaE=fig_betas_exp(),split=fig_percap_split(),
          scat=fig_scatter(),mapE=fig_map_exp())

# render: first div inlines plotly.js
d_mapU=div(figs['mapU'],first=True)
d=lambda k:div(figs[k])

def fmt_cr(x): return f"₹{x/1e7:,.0f}"

# strongest exp drivers for caption
top_exp=B_exp.reindex(B_exp['beta'].abs().sort_values(ascending=False).index).iloc[:2]

HTML=f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bihar 15FC Panchayat Grants — FY 2024-25</title>
<style>
 *{{box-sizing:border-box}} html,body{{margin:0;background:#ffffff;color:{INK};
   font-family:'Calibri','Segoe UI',Arial,sans-serif}}
 .wrap{{max-width:1180px;margin:0 auto;padding:26px 22px 60px}}
 h1{{font-family:Georgia,serif;color:{MAROON_D};font-size:30px;margin:0 0 2px}}
 .sub{{color:{MUTE};font-size:15px;margin-bottom:18px}}
 .kpis{{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 22px}}
 .kpi{{flex:1;min-width:150px;background:#fff;border:1px solid {GRID};border-top:3px solid {MAROON};
   border-radius:6px;padding:12px 16px}}
 .kpi .v{{font-family:Georgia,serif;font-size:26px;color:{MAROON_D};font-weight:bold}}
 .kpi .l{{font-size:12.5px;color:{MUTE};text-transform:uppercase;letter-spacing:.4px}}
 .tabs{{display:flex;gap:4px;border-bottom:2px solid {MAROON};margin-bottom:0}}
 .tab{{padding:11px 20px;cursor:pointer;font-size:15px;font-weight:600;color:{MUTE};
   border:1px solid transparent;border-bottom:none;border-radius:7px 7px 0 0}}
 .tab.on{{background:#fff;color:{MAROON_D};border-color:{GRID};border-bottom:2px solid #fff;margin-bottom:-2px}}
 .panel{{display:none;background:#fff;border:1px solid {GRID};border-top:none;border-radius:0 0 8px 8px;
   padding:22px 24px 28px}}
 .panel.on{{display:block}}
 .lede{{font-family:Georgia,serif;font-size:19px;color:{INK};line-height:1.45;margin:2px 0 4px}}
 .lede b{{color:{MAROON_D}}}
 .note{{font-size:13px;color:{MUTE};line-height:1.5;margin:8px 0 18px}}
 .row{{display:flex;gap:24px;flex-wrap:wrap}} .col{{flex:1;min-width:330px}}
 .cap{{font-size:13px;color:{MUTE};line-height:1.5;margin-top:6px}}
 .ch{{font-family:Georgia,serif;font-size:15px;color:{MAROON_D};font-weight:bold;margin:0 0 4px}}
 footer{{margin-top:22px;font-size:12px;color:{MUTE};line-height:1.6}}
 .star{{color:{GOLD}}}
</style></head><body><div class="wrap">
 <h1>Bihar Panchayat Grants — 15th Finance Commission, FY 2024-25</h1>
 <div class="sub">{N:,} Gram Panchayats · 38 districts · untied + tied grants. Built {pd.Timestamp.today():%d %b %Y}.</div>

 <div class="kpis">
  <div class="kpi"><div class="v">{fmt_cr(TOT_AVAIL)} cr</div><div class="l">Total funds available</div></div>
  <div class="kpi"><div class="v">{fmt_cr(TOT_EXP)} cr</div><div class="l">Spent</div></div>
  <div class="kpi"><div class="v">{fmt_cr(TOT_UNS)} cr</div><div class="l">Unspent</div></div>
  <div class="kpi"><div class="v">{AGG_UNS:.0f}%</div><div class="l">Share unspent</div></div>
 </div>

 <div class="tabs">
  <div class="tab on" onclick="show(0)">① A third sits unspent</div>
  <div class="tab" onclick="show(1)">② Underspending is systemic</div>
  <div class="tab" onclick="show(2)">③ Smaller GPs, more per resident</div>
 </div>

 <div class="panel on" id="p0">
  <div class="lede">Bihar's panchayats left <b>{fmt_cr(TOT_UNS)} crore — {AGG_UNS:.0f}% of their 15FC money — unspent</b> in 2024-25.</div>
  <div class="note">Underspending is the norm, but its severity is a <b>district</b> story: it ranges from the low-20s to over 40% across districts.</div>
  <div class="row">
   <div class="col"><div class="ch">Share of funds unspent, by district</div>{d_mapU}
     <div class="cap">Darker = more money left unspent. Hover for the GP count behind each district.</div></div>
   <div class="col"><div class="ch">Districts ranked by unspent share</div>{d('rankU')}</div>
  </div>
 </div>

 <div class="panel" id="p1">
  <div class="lede">You <b>cannot tell which GPs will underspend</b> from their size, remoteness, or social composition.</div>
  <div class="note">Every GP characteristic moves the unspent share by well under one percentage point per standard deviation, and almost none is statistically distinguishable from zero. Utilisation is essentially <b>flat across the population distribution</b> — small and large GPs alike spend about 70% of what they receive. Underspending is administrative and broad-based, not concentrated in a particular kind of GP.</div>
  <div class="row">
   <div class="col"><div class="ch">What predicts a GP's unspent share?</div>{d('betaU')}
     <div class="cap">Bars are within-district associations (district fixed effects). Maroon = significant at 5%; grey = not. <span class="star">★★★</span> p&lt;.001 · <span class="star">★★</span> p&lt;.01 · <span class="star">★</span> p&lt;.05 · † p&lt;.10.</div></div>
   <div class="col"><div class="ch">Utilisation by GP population quintile</div>{d('utilF')}
     <div class="cap">Share of available funds actually spent. Near-identical from the smallest to the largest GPs.</div></div>
  </div>
 </div>

 <div class="panel" id="p2">
  <div class="lede">A resident of one of Bihar's smallest GPs has <b>₹{PC_SMALL:.0f} of grant money spent on them — {PC_RATIO:.1f}× the ₹{PC_LARGE:.0f}</b> spent per resident in the largest GPs.</div>
  <div class="note">The advantage holds for <b>both</b> earmarked funds (water, sanitation and other tied works) and flexible untied funds — small GPs deliver more per head across the board. And they don't fritter it away: utilisation and unspent share are flat across GP size (Tab ②). <b>Caveat for honesty:</b> larger GPs still spend more in <i>total</i> ({TOT_RATIO:.1f}× as much), since they have more residents — the small-GP advantage is strictly <i>per capita</i>, and it tracks how the grant itself is allocated per head.</div>
  <div class="row">
   <div class="col"><div class="ch">What predicts spending per capita?</div>{d('betaE')}
     <div class="cap">Within-district associations, ₹ per capita per 1 SD. Population and area dominate; blue = significant at 5%.</div></div>
   <div class="col"><div class="ch">Spending per resident, by GP size</div>{d('split')}
     <div class="cap">Total height = ₹ spent per capita, split into earmarked and flexible funds. Both fall monotonically with GP size.</div></div>
  </div>
  <div class="row" style="margin-top:18px">
   <div class="col"><div class="ch">Spending per capita vs. GP characteristic</div>{d('scat')}
     <div class="cap">Binned means (20 bins). Use the dropdown to switch characteristic.</div></div>
   <div class="col"><div class="ch">Spending per capita, by district</div>{d('mapE')}</div>
  </div>
 </div>

 <footer>
  <b>Source:</b> 15th Finance Commission expenditure report (consolidated, FY 2024-25), matched to UGP and merged with Census 2011 / NREGA GP controls and 2016 reservation status. {N:,} GPs with positive available funds, top-1% per-capita outliers and GPs under 200 population trimmed.<br>
  <b>Note:</b> All associations are correlational, estimated within district (district fixed effects). Choropleth colour ranges are clamped to the observed district range so within-state variation is visible. ARWAL has only 1 matched GP and is excluded from district maps and rankings.<br>
  Build script: <code>gpdp_build_dashboard.py</code>. Underlying correlations follow Ankita's <code>GPDP_basic_correlations.do</code>.
 </footer>
</div>
<script>
 function show(i){{
   for(var k=0;k<3;k++){{
     document.getElementById('p'+k).classList.toggle('on',k===i);
     document.getElementsByClassName('tab')[k].classList.toggle('on',k===i);
   }}
   refit(i);
 }}
 function refit(i){{
   // re-fit every Plotly graph in the visible panel (geo fitbounds needs a sized div)
   var panel=document.getElementById('p'+i);
   panel.querySelectorAll('.plotly-graph-div').forEach(function(gd){{
     try{{ Plotly.Plots.resize(gd); }}catch(e){{}}
   }});
 }}
 // re-fit the first (visible) tab AFTER the page has fully laid out, so the
 // initial choropleth measures its real container width, not a transient one.
 window.addEventListener('load',function(){{ refit(0); setTimeout(function(){{refit(0);}},150); }});
</script>
</body></html>"""

with open(OUT,'w') as f: f.write(HTML)
print("wrote",OUT,f"({len(HTML)/1e6:.1f} MB)")
