# Location versions of the Google Ads deck. Rates: ECB euro reference rates, 6 Nov 2026 (AED via the USD peg 3.6725).
import math
EUR = {'EUR': 1.0, 'GBP': 0.83415, 'HKD': 8.7505, 'THB': 37.459, 'USD': 1.1165}
EUR['AED'] = EUR['USD'] * 3.6725
LOC = {
 'UK':        dict(cur='GBP', sym='£',    sp='',  city='London',    low='london',    areas='Mayfair and Kensington',   golf='kensington',    rival='Thames Realty',  rivaldom='thamesrealty.co.uk',  living='London Living Estates', livdom='londonlivingestates.co.uk'),
 'Dubai':     dict(cur='AED', sym='AED ', sp=' ', city='Dubai',     low='dubai',     areas='Palm Jumeirah and Emirates Hills', golf='jumeirah golf estates', rival='Gulf Realty', rivaldom='gulfrealty.ae', living='Dubai Living Estates', livdom='dubailivingestates.ae'),
 'Marbella':  dict(cur='EUR', sym='€',    sp='',  city='Marbella',  low='marbella',  areas='the Golden Mile and Sierra Blanca', golf='la zagaleta', rival='Costa Realty', rivaldom='costarealty.es', living='Marbella Living Estates', livdom='marbellalivingestates.es'),
 'Hong Kong': dict(cur='HKD', sym='HK$',  sp='',  city='Hong Kong', low='hong kong', areas='The Peak and Repulse Bay',  golf='the peak',      rival='Harbour Realty', rivaldom='harbourrealty.hk',   living='Hong Kong Living Estates', livdom='hklivingestates.hk'),
 'Thailand':  dict(cur='THB', sym='฿',    sp='',  city='Phuket',    low='phuket',    areas='Laguna and Kamala',         golf='laguna',        rival='Andaman Realty', rivaldom='andamanrealty.co.th', living='Phuket Living Estates', livdom='phuketlivingestates.co.th'),
}
def conv(v, frm, to): return v / EUR[frm] * EUR[to]
def sig(v, n):
    if v == 0: return 0
    d = n - int(math.floor(math.log10(abs(v)))) - 1
    return round(v, d)
def commas(v): return f'{int(round(v)):,}'
def short(v):                      # 74000 -> 74k, 2_770_000 -> 2.77M
    if v >= 1e6:
        s = f'{sig(v,3)/1e6:.2f}'.rstrip('0').rstrip('.'); return s + 'M'
    if v >= 1e4: return f'{int(round(v/1000))}k'
    s = f'{sig(v,2)/1000:.1f}'.rstrip('0').rstrip('.'); return s + 'k'
def fixer(loc):
    L = LOC[loc]; cur = L['cur']; S = L['sym']
    def m(v, frm, style):          # money string in the target currency
        x = conv(v, frm, cur)
        if style == 'full3': return S + commas(sig(x, 3))
        if style == 'price': return S + commas(sig(x, 2))
        if style == 'short': return S + short(x)
        if style == 'num3': return commas(sig(x, 3))
        raise ValueError(style)
    cpc = round(conv(12.85, 'AED', cur), 2)
    budget = round(1200 * cpc); total = 3 * budget
    villa = conv(2_000_000, 'USD', cur)
    def money2(v): return f'{v:,.2f}'
    exact = {
      '€310,000 ': m(310000, 'EUR', 'full3') + ' ',
      '"€74k in 32 days"': '"%s in 32 days"' % m(74000, 'EUR', 'short'),
      '"€14k in new revenue in 32 days"': '"%s in new revenue in 32 days"' % m(14000, 'EUR', 'short'),
      '"€12k in 7 days with no extra ad budget"': '"%s in 7 days with no extra ad budget"' % m(12000, 'EUR', 'short'),
      '"€180,000 in commissions in 4 weeks"': '"%s in commissions in 4 weeks"' % m(180000, 'EUR', 'full3'),
      '"€92k through AI traffic in 4 weeks"': '"%s through AI traffic in 4 weeks"' % m(92000, 'EUR', 'short'),
      '4,950,000': m(4950000, 'AED', 'num3'), '3,200,000': m(3200000, 'AED', 'num3'), '2,750,000': m(2750000, 'AED', 'num3'),
      '3M – 5M': (short(sig(conv(3e6, 'AED', cur), 2)) + ' – ' + short(sig(conv(5e6, 'AED', cur), 2))),
      'Luxury Dubai Villas AED 10M+ | Book a Private Viewing': 'Luxury %s Villas %s+ | Book a Private Viewing' % (L['city'], S + short(sig(conv(10e6, 'AED', cur), 2))),
      'AED ': S, '12.85': money2(cpc), '15,425': commas(budget), '46,275': commas(total),
      '147k': short(villa * 0.02),
      'Commission based on a AED 7.35M ($2M) villa sale at a 2% standard commission. Off-plan deals at 5% would be ~AED 367k.':
        'Commission based on a %s ($2M) villa sale at a 2%% standard commission. Off-plan deals at 5%% would be ~%s.' % (S + short(villa), S + short(villa * 0.05)),
      '€5,000': m(5000, 'EUR', 'price'), '€2,000': m(2000, 'EUR', 'price'), '€1,000': m(1000, 'EUR', 'price'),
      '€4M': S.strip() + short(sig(conv(4e6, 'EUR', cur), 2)) if S.strip() != 'AED' else 'AED ' + short(sig(conv(4e6, 'EUR', cur), 2)),
      '€180,000 ': m(180000, 'EUR', 'full3') + ' ', '€1,500/month ': m(1500, 'EUR', 'full3') + '/month ',
      '€180,000+ ': m(180000, 'EUR', 'full3') + '+ ', '€10k+': m(10000, 'EUR', 'short') + '+', '€10k+ already spent': m(10000, 'EUR', 'short') + '+ already spent',
      '€180,000': m(180000, 'EUR', 'full3'), '+ €180,000': '+ ' + m(180000, 'EUR', 'full3'),
    }
    if loc == 'Dubai':   # Dubai is the deck's own market: keep its AED figures, only fix the budget maths (1,200 x 12.85 = 15,420)
        for k in ['147k', 'Commission based on a AED 7.35M ($2M) villa sale at a 2% standard commission. Off-plan deals at 5% would be ~AED 367k.',
                  'Luxury Dubai Villas AED 10M+ | Book a Private Viewing', '4,950,000', '3,200,000', '2,750,000', '3M – 5M', '12.85']:
            exact.pop(k, None)
    if loc != 'Dubai':
        exact.update({
          '~20,000': '[~X]', 'SECTOR · DUBAI': 'SECTOR · ' + L['city'].upper(),
          'high-intent property searches every month in Dubai': 'high-intent property searches every month in ' + L['city'],
          "Source: Google Keyword Planner, Dubai, Oct 2025 to Sep 2026. Estimate based on the midpoint of each keyword's volume range.":
            "Source: Google Keyword Planner, %s, [date range]. Estimate based on the midpoint of each keyword's volume range." % L['city'],
          'Gulf Realty': L['rival'], 'gulfrealty.ae': L['rivaldom'], 'Dubai Living Estates': L['living'], 'dubailivingestates.ae': L['livdom'],
          '625+ properties across Palm Jumeirah and Emirates Hills. Book a private viewing.': '625+ properties across %s. Book a private viewing.' % L['areas'],
          '5 bed villa jumeirah golf estates price': '5 bed villa %s price' % L['golf'],
        })
    def fix(t):
        t = t.replace('&quot;', '"')
        if t in exact: t = exact[t]
        elif t.startswith('~') and t == '~': pass
        t = t.replace('[location]', L['low']).replace('[Location]', L['city']).replace('[LOCATION]', L['city'].upper())
        if loc != 'Dubai':
            t = t.replace('Dubai', L['city']).replace('dubai', L['low'])
        return t
    info = dict(cpc=cpc, budget=budget, total=total, villa=villa, commission=villa*0.02, offplan=villa*0.05)
    return fix, info
