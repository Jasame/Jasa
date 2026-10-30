"""Authoritative rules for the JWB simulation. No real payment or credit network."""
import calendar
import copy
import json
import math
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name('cards.json').read_text())
PRODUCTS = {c['id']: c for c in CATALOG}
CURRENCIES = ('USD', 'HKD', 'JPY', 'EUR', 'GBP', 'CNY')

class DomainError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status
        super().__init__(message)

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def number(value, minimum=0, maximum=1_000_000_000):
    if isinstance(value, bool):
        raise DomainError('请输入有效数值 / Invalid numeric value')
    try:
        n = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise DomainError('请输入有效数值 / Invalid numeric value')
    if not n.is_finite() or n < minimum or n > maximum:
        raise DomainError('数值超出允许范围 / Numeric value out of range')
    return n

def money(value, currency='USD', positive=True):
    if currency not in CURRENCIES:
        raise DomainError('不支持的币种 / Unsupported currency')
    n = number(value, Decimal('0.000000001') if positive else 0)
    step = Decimal('1') if currency == 'JPY' else Decimal('.01')
    if n != n.quantize(step):
        raise DomainError('金额精度无效：JPY 为整数，其他币种最多两位小数 / Invalid amount precision')
    return n

def quantize(n, currency='USD'):
    return Decimal(str(n)).quantize(Decimal('1') if currency == 'JPY' else Decimal('.01'), rounding=ROUND_HALF_UP)

def set_money(obj, key, n, currency='USD'):
    obj[key] = float(quantize(n, currency))

def empty_state():
    return dict(version='5.0.0', selectedVaultIndex=0, jrPointsBalance=0,
                treasuryWallets={c: 0 for c in CURRENCIES}, cards=[], posFeed=[], apiLogs=[], generalLedger=[])

def card_for(state, uid):
    card = next((c for c in state['cards'] if c['uid'] == uid), None)
    if not card:
        raise DomainError('卡片不存在或不属于当前账户 / Card not found', 404)
    return card

def ledger(state, debit, credit, amount, memo):
    state['generalLedger'].insert(0, dict(entryId='GL-'+uuid.uuid4().hex[:12].upper(), time=now_iso(), debitAccount=debit,
        creditAccount=credit, amountUSD=float(quantize(amount)), memo=memo))
    del state['generalLedger'][500:]

def feed(state, desc, amount, jr='', kind='spend'):
    state['posFeed'].insert(0, dict(txHash='0x'+secrets.token_hex(8).upper(), time=now_iso(), desc=desc,
                                  amountStr=amount, jrStr=jr, type=kind))
    del state['posFeed'][500:]

def audit_log(state, endpoint, status, message):
    state['apiLogs'].insert(0, dict(id='REQ-'+uuid.uuid4().hex[:10], time=now_iso(), method='POST', endpoint=endpoint,
                                  status=status, latency='server', summary=message))
    del state['apiLogs'][100:]

def add_months(iso, months):
    date = datetime.fromisoformat(iso)
    year, month = divmod(date.year * 12 + date.month - 1 + months, 12)
    return date.replace(year=year, month=month+1, day=min(date.day, calendar.monthrange(year, month+1)[1])).isoformat()

def assess(state, data, rates, settings):
    product = PRODUCTS.get(data.get('cardId'))
    if not product:
        raise DomainError('请选择有效卡种 / Invalid product')
    income = number(data.get('income', 0), 0, 1_000_000_000)
    existing = number(data.get('existing', 0), 0, 100_000_000)
    months = number(data.get('months', 0), 0, 360)
    if months != int(months):
        raise DomainError('账龄必须为整数月 / Account age must be whole months')
    holder = str(data.get('holderName', '')).strip().upper()
    if not holder or len(holder) > 40 or any(ord(c) < 32 for c in holder):
        raise DomainError('姓名需为 1–40 个可显示字符 / Invalid cardholder name')
    cash = sum(Decimal(str(v)) * Decimal(str(rates.get(c, 0))) for c, v in state['treasuryWallets'].items())
    if income < Decimal(str(settings.get('min_income', 5000))) and cash < 2500:
        return dict(approved=False, reason='模拟年收入未达最低标准，且模拟资产不足 / Income and assets below the model threshold',
                    score=600, currentLimit=0, initialLimit=0, maxCap=product['maxCap'], cardId=product['id'], holderName=holder)
    factor = min(Decimal('1.8'), Decimal('.5') + months/24)
    base = income*Decimal('.12') + existing*Decimal('.45')*factor
    boost = (cash*Decimal('.8')*Decimal('.35')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    raw = (base*Decimal(str(product['tierMultiplier']))+boost)/500
    limit = min(product['maxCap'], max(2000, int(raw.quantize(Decimal('1'), rounding=ROUND_HALF_UP))*500))
    if limit < product['annualFee']:
        return dict(approved=False, reason='预批额度不足以覆盖首年年费 / Approved limit does not cover the first-year fee', score=600, currentLimit=0, initialLimit=0, maxCap=product['maxCap'], cardId=product['id'], holderName=holder)
    score = min(850, round(730+min(60,float(months)*1.5)+min(55,float(income+cash)/4500)))
    return dict(approved=True, reason='模拟规则预审通过 / Simulation rules passed', score=score, currentLimit=limit,
                initialLimit=limit, maxCap=product['maxCap'], cardId=product['id'], holderName=holder,
                incomeComponent=float(quantize(base)), collateralComponent=float(boost), annualFee=product['annualFee'])

def pan(prefix):
    first15 = ''.join(filter(str.isdigit, prefix))+''.join(str(secrets.randbelow(10)) for _ in range(7))
    total = 0
    for i, c in enumerate(first15):
        d = int(c)*(2 if i % 2 == 0 else 1)
        total += d-9 if d > 9 else d
    n = first15+str((10-total%10)%10)
    return '-'.join(n[i:i+4] for i in range(0,16,4))

def execute(state, endpoint, data, rates, settings):
    route = endpoint.removeprefix('/api/v1/')
    wallets = state['treasuryWallets']
    from suite import refresh_benefit_period,VOUCHERS
    for existing_card in state['cards']:
        if existing_card.get('status')!='CLOSED':refresh_benefit_period(existing_card,settings.get('_now',int(datetime.now(timezone.utc).timestamp())))
    if route == 'treasury/wire-in':
        currency = data.get('currency')
        amount = money(data.get('amount'), currency)
        if amount > 1_000_000 or Decimal(str(wallets[currency]))+amount > 1_000_000_000:
            raise DomainError('模拟入金单笔最多 100 万，账户上限 10 亿 / Demo deposit limit exceeded')
        if currency != 'USD' and currency not in rates:
            raise DomainError('请先连接有效参考汇率 / Valid reference rates required', 503)
        set_money(wallets, currency, Decimal(str(wallets[currency]))+amount, currency)
        ledger(state, f'1010 · Cash ({currency})', '3010 · Demo Contribution', amount*Decimal(str(rates[currency])), f'Demo funding {amount} {currency}')
        feed(state, f'模拟入金 / Demo funding · {currency}', f'+{amount} {currency}', '', 'deposit')
        return {'message': f'模拟入金成功 / Demo funds added: {amount} {currency}'}
    if route == 'treasury/accrue-apy':
        period = now_iso()[:7]
        if state.get('interestPeriod') == period:
            raise DomainError('本月已结息 / Interest already accrued this month', 409)
        cash = sum(Decimal(str(v))*Decimal(str(rates.get(c,0))) for c,v in wallets.items())
        interest = quantize(cash*Decimal(str(1.0485**(1/12)-1)))
        if interest <= 0:
            raise DomainError('余额不足以产生最低计息金额 / No interest available')
        set_money(wallets,'USD',Decimal(str(wallets['USD']))+interest)
        state['interestPeriod']=period
        ledger(state,'1010 · Cash (USD)','4020 · Demo Interest Income',interest,'Illustrative 4.85% APY monthly accrual')
        return {'message':f'模拟利息已入账 / Demo interest credited: USD {interest}'}
    if route == 'treasury/fx-swap':
        q = data['_quote']
        amount, received = Decimal(q['amount']), Decimal(q['received'])
        if Decimal(str(wallets[q['from']])) < amount:
            raise DomainError('兑出账户余额不足 / Insufficient source balance', 402)
        set_money(wallets,q['from'],Decimal(str(wallets[q['from']]))-amount,q['from'])
        set_money(wallets,q['to'],Decimal(str(wallets[q['to']]))+received,q['to'])
        ledger(state,f'1010 · Cash ({q["to"]})',f'1010 · Cash ({q["from"]})',amount*Decimal(q['usdRate']),f'FX @ {q["rate"]} · {q["source"]} · {q["asOf"]} · Fee 0 / Markup 0')
        feed(state,f'{q["from"]} → {q["to"]} · {q["source"]} · {q["asOf"]}',f'-{amount} {q["from"]} / +{received} {q["to"]}','Fee 0 · Markup 0','fx')
        return {'message':f'模拟兑换成功 / Exchange complete: {received} {q["to"]}'}
    if route == 'underwriting/issue-card':
        if any(c['cardId']==data.get('cardId') and c.get('status')!='CLOSED' for c in state['cards']):
            raise DomainError('每种卡片最多持有一张 / One card of each product is allowed',409)
        decision = assess(state,data,rates,settings)
        if not decision['approved']:
            raise DomainError(decision['reason'],422)
        product = PRODUCTS[decision['cardId']]
        if product['annualFee'] > decision['currentLimit']:
            raise DomainError('预批额度不足以覆盖首年年费 / Approved limit does not cover the first-year fee',422)
        created = now_iso()
        card = dict(uid=uuid.uuid4().hex,cardId=product['id'],welcomeProductId=product['id'],holderName=decision['holderName'],cardNumber=pan(product['bin']),
                    expDate=f'{datetime.now().month:02}/{(datetime.now().year+5)%100:02}',cvv=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(5)),
                    creditLimit=decision['currentLimit'],initialCreditLimit=decision['currentLimit'],statementBalance=product['annualFee'],annualFeePaid=product['annualFee'],spendProgress=0,
                    welcomeUnlocked=False,remainingCreditPool=product['fixedCredits'],benefitPools={},status='ACTIVE',openedAt=created,cliApplied=False,
                    welcomeExpiresAt=add_months(created,3 if product['id']=='everyday' else 12 if product['id']=='centurion' else 6))
        state['cards'].insert(0,card);state['selectedVaultIndex']=0
        if product['annualFee']:
            ledger(state,'5020 · Annual Fee Expense',f'2010 · Card Payable ({card["uid"]})',product['annualFee'],f'First-year demo annual fee · {product["name"]}')
            feed(state,f'首年模拟年费 / First-year annual fee · {product["name"]}',f'+${product["annualFee"]:.2f}','','fee')
        feed(state,f'卡片签发 / Card issued · {product["name"]}','$0.00','','bonus')
        return {'status':201,'message':'卡片已签发，首年模拟年费已计入账单 / Card issued; first-year annual fee posted', 'issuedCard':card,'assessment':decision}
    if route == 'cards/reallocate-limit':
        source,target=card_for(state,data.get('fromUid')),card_for(state,data.get('toUid'))
        if source['status'] not in ('ACTIVE','FROZEN') or target['status'] not in ('ACTIVE','FROZEN'):raise DomainError('只能在有效卡片间调拨额度 / Only current cards can transfer credit',409)
        amount=money(data.get('amount'))
        if source['uid']==target['uid']:
            raise DomainError('请选择不同卡片 / Choose different cards')
        if Decimal(str(source['creditLimit']))-amount < max(Decimal('2000'),Decimal(str(source['statementBalance']))):
            raise DomainError('调出额度须覆盖欠款且至少保留 $2,000 / Source limit must cover debt and retain $2,000')
        if Decimal(str(target['creditLimit']))+amount > PRODUCTS[target['cardId']]['maxCap']:
            raise DomainError('超出目标卡种上限 / Target product limit exceeded')
        set_money(source,'creditLimit',Decimal(str(source['creditLimit']))-amount)
        set_money(target,'creditLimit',Decimal(str(target['creditLimit']))+amount)
        return {'message':'额度调拨完成 / Credit limits reallocated'}
    if route == 'core/reset':
        state.clear();state.update(empty_state())
        return {'message':'当前账户已恢复为零资产状态 / Your account has been reset to zero'}
    card=card_for(state,data.get('uid'))
    meta=PRODUCTS[card['cardId']]
    if card['status'] in ('CLOSED','EXPIRED') and route!='cards/repay':raise DomainError('卡片已关闭或到期 / Card closed or expired',409)
    if route=='benefits/use':
        if card['status']!='ACTIVE':raise DomainError('卡片已冻结，无法使用权益 / Unfreeze the card to use benefits',423)
        benefit=next((v for v in VOUCHERS[card['cardId']] if v[0]==data.get('benefitId')),None)
        if not benefit:raise DomainError('无此权益 / Benefit not available',404)
        key=f'{card["benefitPeriod"]}:{card["cardId"]}:{benefit[0]}'
        used=card['benefitUses'].get(key,0)
        if benefit[3] is not None and used>=benefit[3]:raise DomainError('本周期权益已用完 / Benefit exhausted this period',409)
        note=str(data.get('merchant','')).strip()
        if not 1<=len(note)<=120:raise DomainError('请填写 1–120 字的模拟使用说明 / Enter a demo usage note (1–120 characters)')
        card['benefitUses'][key]=used+1
        feed(state,benefit[2]+' · '+note,'$0.00','','benefit')
        return {'message':'权益使用已记录，仅供模拟 / Benefit usage recorded for simulation only'}
    if route == 'cards/security-freeze':
        card['status']='FROZEN' if card['status']=='ACTIVE' else 'ACTIVE'
        return {'message':'卡片状态已更新 / Card status updated'}
    if route == 'cards/rotate-cvv':
        card['cvv']=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(5))
        return {'message':'模拟安全码已轮换 / Demo security code rotated'}
    if route == 'cards/product-change':
        target=PRODUCTS.get(data.get('cardId'))
        if not target or target['id']==card['cardId']:
            raise DomainError('请选择不同的目标卡种 / Choose another product')
        if any(c['uid']!=card['uid'] and c['cardId']==target['id'] and c.get('status')!='CLOSED' for c in state['cards']):
            raise DomainError('已持有目标卡种 / Target product is already in your wallet',409)
        difference=max(0,target['annualFee']-card.get('annualFeePaid',meta['annualFee']))
        if card['statementBalance']+difference > min(card['creditLimit'],target['maxCap']):
            raise DomainError('请先还款至目标额度范围 / Repay below the target credit cap',409)
        card['benefitPools'][card['cardId']]=card['remainingCreditPool']
        card['remainingCreditPool']=card['benefitPools'].get(target['id'],min(card['remainingCreditPool'],target['fixedCredits']))
        card['cardId']=target['id'];card['creditLimit']=min(card['creditLimit'],target['maxCap'])
        if difference:
            set_money(card,'statementBalance',Decimal(str(card['statementBalance']))+difference)
            card['annualFeePaid']=target['annualFee']
            ledger(state,'5020 · Annual Fee Expense',f'2010 · Card Payable ({card["uid"]})',difference,'Demo product-change annual fee difference')
        feed(state,f'产品变更 / Product changed · {target["name"]}',f'+${difference:.2f}','Original welcome offer preserved','fee' if difference else 'bonus')
        return {'message':'已变更卡种，原开卡奖励进度保留 / Product changed; original welcome progress retained'}
    if route == 'cards/repay':
        balance=Decimal(str(card['statementBalance']))
        if balance<=0:raise DomainError('没有待还账单 / No outstanding balance')
        requested=money(data['amount']) if data.get('amount') not in (None,'') else balance
        if requested>balance:raise DomainError('还款金额超过欠款 / Repayment exceeds the balance')
        method=data.get('method')
        if method=='JR':
            paid=min(requested,Decimal(state['jrPointsBalance'])/100)
            if paid<=0:raise DomainError('积分不足 / No rewards available',402)
            state['jrPointsBalance']-=int(paid*100)
            credit='1100 · JR Rewards Asset'
        elif method=='USD':
            if Decimal(str(wallets['USD']))<requested:raise DomainError('USD 余额不足 / Insufficient USD balance',402)
            paid=requested;set_money(wallets,'USD',Decimal(str(wallets['USD']))-paid);credit='1010 · Cash (USD)'
        else:raise DomainError('不支持的还款方式 / Unsupported repayment method')
        set_money(card,'statementBalance',balance-paid)
        ledger(state,f'2010 · Card Payable ({card["uid"]})',credit,paid,'Demo card repayment')
        feed(state,'账单还款 / Card repayment',f'-${paid:.2f}',method,'credit')
        return {'message':f'还款成功 / Repaid: USD {paid}'}
    if route == 'pos/authorize':
        if card['status']!='ACTIVE':raise DomainError('卡片已冻结 / Card is frozen',423)
        currency=data.get('currency');amount=money(data.get('amount'),currency)
        if currency not in rates:raise DomainError('无有效汇率 / Reference rates unavailable',503)
        usd=quantize(amount*Decimal(str(rates[currency])))
        if usd<=0:raise DomainError('消费金额不足 0.01 USD / Purchase below USD 0.01')
        if usd > Decimal(str(card['creditLimit']))-Decimal(str(card['statementBalance'])):raise DomainError('可用额度不足 / Insufficient available credit',402)
        category=data.get('category')
        if category not in ('dining','travel','hotel','everyday'):raise DomainError('不支持的商户类别 / Invalid merchant category')
        merchant=str(data.get('merchant','')).strip()
        if not merchant or len(merchant)>120:raise DomainError('商户名称长度需为 1–120 / Invalid merchant name')
        mult=meta['rates'].get(category,meta['rates']['everyday'])
        earned=int((usd*Decimal(str(mult))).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        state['jrPointsBalance']+=earned;set_money(card,'statementBalance',Decimal(str(card['statementBalance']))+usd)
        set_money(card,'spendProgress',Decimal(str(card['spendProgress']))+usd)
        ledger(state,'5010 · Purchase Expense',f'2010 · Card Payable ({card["uid"]})',usd,f'{merchant} · {amount} {currency}')
        ledger(state,'1100 · JR Rewards Asset','4030 · Rewards Income',Decimal(earned)/100,'Purchase rewards')
        feed(state,f'{merchant} · {amount} {currency} · {meta["name"]}',f'+${usd:.2f}',f'+{earned:,} JR ({mult}X)')
        rule=meta.get('autoCreditRule')
        if rule and rule['category']==category and card['remainingCreditPool']>0:
            credit=min(usd,Decimal(str(rule['singleCap'])),Decimal(str(card['remainingCreditPool'])))
            set_money(card,'statementBalance',Decimal(str(card['statementBalance']))-credit)
            set_money(card,'remainingCreditPool',Decimal(str(card['remainingCreditPool']))-credit)
            ledger(state,f'2010 · Card Payable ({card["uid"]})','4010 · Statement Credit Income',credit,'Automatic demo credit')
            feed(state,f'自动抵扣 / Statement credit · {rule["label_en"]}',f'-${credit:.2f}','','credit')
        welcome=PRODUCTS[card['welcomeProductId']]
        if not card['welcomeUnlocked'] and now_iso()<=card['welcomeExpiresAt'] and card['spendProgress']>=welcome['welcomeSpendReq']:
            card['welcomeUnlocked']=True;state['jrPointsBalance']+=welcome['welcomeJR']
            ledger(state,'1100 · JR Rewards Asset','4030 · Welcome Bonus Income',Decimal(welcome['welcomeJR'])/100,'Original product welcome bonus')
            feed(state,f'开卡奖励 / Welcome bonus · {welcome["name"]}','$0.00',f'+{welcome["welcomeJR"]:,} JR','bonus')
        return {'message':f'模拟消费已入账 / Purchase posted: USD {usd} · +{earned} JR'}
    if route == 'credit/cli-3x':
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(card['openedAt'])).days
        if age < 61:raise DomainError(f'尚需持卡 {61-age} 天；当前仅支持提额预览 / {61-age} days until eligibility',409)
        if card.get('cliApplied'):raise DomainError('本账户的三倍提额机会已使用 / Increase already applied',409)
        card['creditLimit']=min(meta['maxCap'],max(card['creditLimit'],card['initialCreditLimit']*3));card['cliApplied']=True
        return {'message':'提额已生效 / Credit increase applied'}
    raise DomainError('不支持的操作 / Unsupported operation',404)
