
    // =========================================================================
    // 1. CURRENCY MID-MARKET RATES (Relative to 1 USD)
    // =========================================================================
    const FX_RATES_TO_USD = {
      USD: 1.0,
      HKD: 0.1282,   // ~7.80 HKD per USD
      JPY: 0.0067,   // ~149.25 JPY per USD
      EUR: 1.0850,   // ~0.92 EUR per USD
      GBP: 1.2950,   // ~0.77 GBP per USD
      CNY: 0.1388    // ~7.20 CNY per USD
    };

    const CURRENCY_META = {
      USD: { symbol: '$', flag: '🇺🇸', name_zh: '美元主权账户', name_en: 'USD Sovereign' },
      HKD: { symbol: 'HK$', flag: '🇭🇰', name_zh: '港币离岸账户', name_en: 'HKD Offshore' },
      JPY: { symbol: '¥', flag: '🇯🇵', name_zh: '日元清算账户', name_en: 'JPY Clearing' },
      EUR: { symbol: '€', flag: '🇪🇺', name_zh: '欧元私行账户', name_en: 'EUR Private' },
      GBP: { symbol: '£', flag: '🇬🇧', name_zh: '英镑伦敦账户', name_en: 'GBP London' },
      CNY: { symbol: '¥', flag: '🇨🇳', name_zh: '人民币跨境户', name_en: 'CNY Cross-Border' }
    };

    // =========================================================================
    // 2. COMPLETE 6 FLAGSHIP CARDS DATA MATRIX (BIN 8888 & STRICT MAX CAPS)
    // =========================================================================
    const JWB_CARDS = [
      {
        id: 'everyday',
        category: 'lifestyle',
        name: 'JWB Everyday Preferred',
        sub_zh: '日常优选卡 · 零年费信报基石',
        sub_en: 'Zero-Fee Credit History Foundation',
        bin: '8888-0188',
        maxCap: 25000,
        annualFee: 0,
        feeText_zh: '$0 (终身免年费)',
        feeText_en: '$0 / yr',
        tierMultiplier: 1.0,
        welcomeJR: 35000,
        welcomeSpendReq: 1500,
        welcome_zh: '前 3 个月消费满 $1,500 获赠 35,000 JR（保底价值 $350）',
        welcome_en: 'Earn 35,000 JR ($350 value) after $1,500 spend in first 3 months',
        badge_zh: '零年费基石 · 永久养信报',
        badge_en: 'Zero Fee · Credit Builder',
        finishClass: 'finish-everyday',
        accentHex: '#64748B',
        rates: { dining: 2, travel: 2, hotel: 2, everyday: 3 },
        autoCreditRule: { category: 'everyday', maxAnnual: 60, singleCap: 15, label_zh: '流媒体账单自动抵扣', label_en: 'Streaming Credit' },
        fixedCredits: 60,
        tags_zh: ['流媒体/通勤 3X', '全品类无上限 2X', '每年 $60 账单抵扣'],
        tags_en: ['3X Streaming/Transit', '2X Uncapped Everyday', '$60 Annual Credit'],
        earn_zh: '全球流媒体/数字订阅 3X JR，日常通勤与充电/加油 3X JR，其余全部消费无上限 2X JR。',
        earn_en: '3X JR on global streaming & transit/EV charging, uncapped 2X JR on all other purchases.',
        perks_zh: [
          '每年 $60 流媒体账单自动抵扣（每月 $5 自动入账）',
          '手机碎屏与失窃保护险（最高赔付 $800）',
          '全球购物延保与 0% 货币转换费，支持永久持有养信报'
        ],
        perks_en: [
          '$60 annual streaming statement credit ($5/month auto-applied)',
          'Cell phone protection against damage & theft (up to $800 claim)',
          'Extended warranty & 0% Foreign Transaction Fees globally'
        ]
      },
      {
        id: 'gold',
        category: 'lifestyle',
        name: 'JWB Gold',
        sub_zh: '甄选金卡 · 全球餐饮与品质生活旗舰',
        sub_en: 'Global Dining & Everyday Luxury Flagship',
        bin: '8888-0288',
        maxCap: 50000,
        annualFee: 295,
        feeText_zh: '$295 / yr',
        feeText_en: '$295 / yr',
        tierMultiplier: 1.25,
        welcomeJR: 100000,
        welcomeSpendReq: 4000,
        welcome_zh: '前 6 个月消费满 $4,000 获赠 100,000 JR（保底价值 $1,000）',
        welcome_en: 'Earn 100,000 JR ($1,000 value) after $4,000 spend in first 6 months',
        badge_zh: '等效负年费 (-$65) · 餐饮超市 5X',
        badge_en: '-$65 Net Effective Fee · 5X Dining',
        finishClass: 'finish-gold',
        accentHex: '#D4AF37',
        rates: { dining: 5, travel: 3, hotel: 3, everyday: 1.5 },
        autoCreditRule: { category: 'dining', maxAnnual: 360, singleCap: 30, label_zh: '全球餐饮与出行自动报销', label_en: 'Dining & Ride Credit' },
        fixedCredits: 360,
        tags_zh: ['全球餐饮/超市 5X', '全球机票 3X', '每年 $360 自动报销'],
        tags_en: ['5X Dining & Groceries', '3X Global Flights', '$360 Annual Credits'],
        earn_zh: '全球餐饮（含堂食与外卖）5X JR、全球超市与生鲜 5X JR、全球机票 3X JR，其余消费 1.5X JR。',
        earn_en: '5X JR on global dining & groceries, 3X JR on flights, 1.5X JR on all other spend.',
        perks_zh: [
          '每年 $240 全球餐饮账单抵扣（每月 $20 自动入账）',
          '每年 $120 全球打车出行抵扣（每月 $10 自动入账），合计报销 $360 倒赚 $65',
          '全球精选酒店预订享 $100 餐饮额度及房型升等'
        ],
        perks_en: [
          '$240 annual dining credit ($20/month auto-applied)',
          '$120 annual rideshare credit ($10/month), netting +$65 over annual fee',
          '$100 property credit & room upgrade at JWB Hotel Collection'
        ]
      },
      {
        id: 'aero',
        category: 'cobrand',
        name: 'JWB Aero Reserve',
        sub_zh: '寰宇航司联名卡 · 头等舱与里程神卡',
        sub_en: 'First Class Aviation & Global Companion Card',
        bin: '8888-0388',
        maxCap: 75000,
        annualFee: 450,
        feeText_zh: '$450 / yr',
        feeText_en: '$450 / yr',
        tierMultiplier: 1.45,
        welcomeJR: 130000,
        welcomeSpendReq: 5000,
        welcome_zh: '前 6 个月消费满 $5,000 获赠 130,000 JR（保底价值 $1,300）',
        welcome_en: 'Earn 130,000 JR ($1,300 value) after $5,000 spend in first 6 months',
        badge_zh: '全球航司 8X · 头等舱伴侣免票券',
        badge_en: '8X Airlines · First Class Companion Pass',
        finishClass: 'finish-aero',
        accentHex: '#38BDF8',
        rates: { dining: 4, travel: 8, hotel: 4, everyday: 1.5 },
        autoCreditRule: { category: 'travel', maxAnnual: 300, singleCap: 150, label_zh: '全球航司自动报销', label_en: 'Airline Statement Credit' },
        fixedCredits: 300,
        tags_zh: ['全球航司 8X', '头等舱伴侣免票券', '每年 $300 航司报销'],
        tags_en: ['8X Global Airlines', 'First Class Companion Cert', '$300 Airline Credit'],
        earn_zh: '全球所有航空公司机票及附加消费 8X JR、全球餐饮与租车 4X JR，其余消费 1.5X JR。',
        earn_en: '8X JR on all global airlines & ancillaries, 4X JR on dining & car rentals, 1.5X JR elsewhere.',
        perks_zh: [
          '开卡及每年续卡赠送 1 张全球头等舱/商务舱同行伴侣免票券（仅需付税费）',
          '每年 $300 航司消费/升舱/选座自动报销',
          '无限次全球 JWB Aero 头等舱休息室通行、免费托运 3 件行李、延误满 2 小时立赔 $500'
        ],
        perks_en: [
          'Annual Global First/Business Class Companion Certificate upon opening & renewal',
          '$300 annual automatic airline & seat upgrade statement credit',
          'Unlimited JWB Aero First Lounge access, 3 free checked bags & $500 2-hr flight delay payout'
        ]
      },
      {
        id: 'aspire',
        category: 'cobrand',
        name: 'JWB Grand Horizon Aspire',
        sub_zh: '天际酒店联名卡 · 负年费奢华度假神卡',
        sub_en: 'Luxury Resort & Diamond Elite Status Flagship',
        bin: '8888-0588',
        maxCap: 80000,
        annualFee: 550,
        feeText_zh: '$550 / yr',
        feeText_en: '$550 / yr',
        tierMultiplier: 1.55,
        welcomeJR: 160000,
        welcomeSpendReq: 5000,
        welcome_zh: '前 6 个月消费满 $5,000 获赠 160,000 JR（保底价值 $1,600）',
        welcome_en: 'Earn 160,000 JR ($1,600 value) after $5,000 spend in first 6 months',
        badge_zh: '报销倒赚 $50 · 钻石会籍 + 免房券',
        badge_en: 'Diamond Elite + Uncapped Free Night',
        finishClass: 'finish-aspire',
        accentHex: '#C084FC',
        rates: { dining: 5, travel: 5, hotel: 14, everyday: 2 },
        autoCreditRule: { category: 'hotel', maxAnnual: 600, singleCap: 200, label_zh: '奢华度假村与机票自动报销', label_en: 'Resort & Flight Credit' },
        fixedCredits: 600,
        tags_zh: ['酒店直订 14X', '直通最高钻石会籍', '$600 报销 + 免房券'],
        tags_en: ['14X Hotel Direct', 'Diamond Elite Status', '$600 Credits + Free Night'],
        earn_zh: '全球合作酒店及度假村直订 14X JR、全球机票与餐饮 5X JR，其余消费 2X JR。',
        earn_en: '14X JR on global partner hotels & resorts, 5X JR on flights & dining, 2X JR on everything else.',
        perks_zh: [
          '持卡直通全球合作奢华酒店最高级钻石会籍（保证行政酒廊、双人早餐、套房升等）',
          '开卡首年即送 1 张全球不限等级通用免房券（Uncapped Free Night Award）',
          '每年 $400 度假村自动抵扣 + $200 机票自动抵扣（仅固定报销即倒赚 $50）'
        ],
        perks_en: [
          'Complimentary top-tier Diamond Elite Status (executive lounge, daily breakfast & suite upgrades)',
          '1 Uncapped Global Free Night Award every year upon card opening & renewal',
          '$400 annual resort credit + $200 flight credit ($600 total credits exceed $550 annual fee)'
        ]
      },
      {
        id: 'platinum',
        category: 'apex',
        name: 'JWB Platinum',
        sub_zh: '寰宇白金卡 · 全球差旅与全能旗舰',
        sub_en: 'Global Travel & Fine Hotels All-Rounder',
        bin: '8888-0688',
        maxCap: 150000,
        annualFee: 695,
        feeText_zh: '$695 / yr',
        feeText_en: '$695 / yr',
        tierMultiplier: 1.85,
        welcomeJR: 175000,
        welcomeSpendReq: 6000,
        welcome_zh: '前 6 个月消费满 $6,000 获赠 175,000 JR（保底价值 $1,750）',
        welcome_en: 'Earn 175,000 JR ($1,750 value) after $6,000 spend in first 6 months',
        badge_zh: '$900 年度综合报销 · JWB FHR 礼遇',
        badge_en: '$900 Annual Credits · JWB FHR Perks',
        finishClass: 'finish-platinum',
        accentHex: '#E2E8F0',
        rates: { dining: 3, travel: 10, hotel: 10, everyday: 1.5 },
        autoCreditRule: { category: 'travel', maxAnnual: 900, singleCap: 250, label_zh: '全球差旅与数字生活自动报销', label_en: 'Global Travel Auto-Credit' },
        fixedCredits: 900,
        tags_zh: ['JWB Travel 10X', '$900 年度综合报销', 'FHR 保证 4PM 退房'],
        tags_en: ['10X JWB Travel', '$900 Annual Credits', 'FHR 4PM Late Checkout'],
        earn_zh: 'JWB Travel 平台预订 10X JR、全球航司与酒店直订 6X JR，其余消费 1.5X JR。',
        earn_en: '10X JR via JWB Travel portal, 6X JR on direct flights & hotels, 1.5X JR on all other spend.',
        perks_zh: [
          '每年 $400 差旅无门槛自动报销 + $300 数字生活与健康报销 + $200 全球专车报销（合计 $900）',
          '无限次全球 JWB Reserve Lounge 及机场贵宾厅（每次可免费携伴 2 人）',
          'JWB Fine Hotels & Resorts (FHR)：保证下午 4 点退房、客房升等、双早及 $150 住店消费额'
        ],
        perks_en: [
          '$400 travel credit + $300 digital/wellness credit + $200 global chauffeur credit ($900/yr total)',
          'Unlimited JWB Reserve Lounge & global airport lounge access with 2 complimentary guests',
          'JWB Fine Hotels & Resorts (FHR): guaranteed 4PM late checkout, upgrade, breakfast & $150 credit'
        ]
      },
      {
        id: 'centurion',
        category: 'apex',
        name: 'JWB Centurion Reserve',
        sub_zh: '黑金典藏卡 · 私人银行巅峰旗舰',
        sub_en: 'Private Banking Apex Sovereign Card',
        bin: '8888-8888',
        maxCap: 500000,
        annualFee: 2500,
        feeText_zh: '$2,500 (免首年制卡费)',
        feeText_en: '$2,500 / yr',
        tierMultiplier: 3.2,
        welcomeJR: 300000,
        welcomeSpendReq: 0.01,
        welcome_zh: '首年激活并完成任意首刷即享 300,000 JR（保底价值 $3,000）',
        welcome_en: 'Earn 300,000 JR ($3,000 value) upon activation and first purchase of any amount',
        badge_zh: '首刷立享 $3,000 · 顶奢卡段 8888-8888',
        badge_en: '$3,000 First-Swipe · BIN 8888-8888',
        finishClass: 'finish-centurion',
        accentHex: '#F59E0B',
        rates: { dining: 6, travel: 6, hotel: 6, everyday: 3.5 },
        autoCreditRule: { category: 'travel', maxAnnual: 2000, singleCap: 600, label_zh: '私人航空与顶奢百货抵扣', label_en: 'Aviation & Luxury Credit' },
        fixedCredits: 2000,
        tags_zh: ['差旅/奢品 6X', '大额 4X / 保底 2.5X', '$2,000 航司与顶奢抵扣'],
        tags_en: ['6X Travel & Luxury', '4X High-Ticket / 2.5X Base', '$2,000 Aviation & Luxury Credit'],
        earn_zh: '全球差旅与奢品消费 6X JR，单笔满 $5,000 消费享 4X JR，其余全品类无上限保底 2.5X JR。',
        earn_en: '6X JR on global travel & luxury goods, 4X JR on purchases ≥$5,000, uncapped 2.5X JR base.',
        perks_zh: [
          '每年 $1,200 私人航空/头等舱账单直接抵扣 + $800 全球顶奢百货购物抵扣',
          '24/7 专属私人银行客户经理（Dedicated Relationship Manager）及全球礼宾团队',
          '四大奢华酒店最高会籍直通、机场 VIP 独立航站楼政要通道与停机坪专车接送'
        ],
        perks_en: [
          '$1,200 annual private aviation/first-class credit + $800 global luxury department store credit',
          '24/7 Dedicated Private Bank Relationship Manager & global concierge team',
          'Top-tier status across 4 hotel groups, private VIP terminal & tarmac limousine transfers'
        ]
      }
    ];

    // =========================================================================
    // 3. EMBEDDED CORE BANKING BACKEND ENGINE (REST API + DOUBLE-ENTRY LEDGER)
    // =========================================================================
    const CORE_DB_KEY = 'jwb_core_banking_db_v4';
    let db = null;

    function createInitialDatabase() {
      return {
        version: '4.0.0',
        selectedVaultIndex: 0,
        jrPointsBalance: 35000,
        treasuryWallets: {
          USD: 50000.00,
          HKD: 50000.00,
          JPY: 300000.00,
          EUR: 0.00,
          GBP: 0.00,
          CNY: 0.00
        },
        cards: [
          {
            uid: 'v-gold-1',
            cardId: 'gold',
            holderName: 'JASA XU',
            cardNumber: '8888-0288-8842-1904',
            expDate: '10/31',
            cvv: 'AK8B0',
            creditLimit: 28500,
            statementBalance: 0.00,
            spendProgress: 800,
            welcomeUnlocked: false,
            remainingCreditPool: 360.00,
            status: 'ACTIVE'
          },
          {
            uid: 'v-everyday-2',
            cardId: 'everyday',
            holderName: 'JASA XU',
            cardNumber: '8888-0188-3319-7260',
            expDate: '10/31',
            cvv: 'JX9M2',
            creditLimit: 15000,
            statementBalance: 0.00,
            spendProgress: 1500,
            welcomeUnlocked: true,
            remainingCreditPool: 60.00,
            status: 'ACTIVE'
          }
        ],
        posFeed: [
          {
            txHash: '0x8F92...3E1A',
            time: 'INITIALIZED',
            desc: 'JWB Everyday Preferred 史高开卡礼达标入账',
            amountStr: '$0.00',
            jrStr: '+35,000 JR ($350)',
            type: 'bonus'
          }
        ],
        apiLogs: [
          {
            id: 'REQ-1001',
            time: new Date().toLocaleTimeString(),
            method: 'POST',
            endpoint: '/api/v1/core/boot',
            status: 200,
            latency: '4ms',
            summary: 'JWB Core Banking Database v4.0 mounted with ACID Double-Entry Ledger.'
          }
        ],
        generalLedger: [
          {
            entryId: 'GL-0001',
            time: new Date().toLocaleTimeString(),
            debitAccount: '1010 · Cash & Sovereign Vault (USD)',
            creditAccount: '3010 · Client Private Equity',
            amountUSD: 50000.00,
            memo: 'Initial Sovereign Checking Deposit'
          }
        ]
      };
    }

    function loadCoreDatabase() {
      try {
        const raw = localStorage.getItem(CORE_DB_KEY);
        if (raw) {
          db = validateDatabase(JSON.parse(raw));
          if (!db.treasuryWallets || !db.cards || !db.cards.length) {
            db = createInitialDatabase();
          }
        } else {
          db = createInitialDatabase();
        }
      } catch (e) {
        try {const raw=localStorage.getItem(CORE_DB_KEY);if(raw)localStorage.setItem(CORE_DB_KEY+'_recovery',raw);}catch(ignore){}
        window.jwbRecoveredInvalidStorage=true;
        db = createInitialDatabase();
      }
    }

    function commitCoreDatabase() {
      try {
        localStorage.setItem(CORE_DB_KEY, JSON.stringify(db));
      } catch (e) { window.jwbStorageFailed=true; }
    }

    // Generate short SHA-256 style cryptographic hash for clearing receipts
    function generateTxHash(seedStr) {
      let h1 = 0xdeadbeef ^ seedStr.length;
      let h2 = 0x41c6ce57 ^ seedStr.length;
      for (let i = 0, ch; i < seedStr.length; i++) {
        ch = seedStr.charCodeAt(i);
        h1 = Math.imul(h1 ^ ch, 2654435761);
        h2 = Math.imul(h2 ^ ch, 1597334677);
      }
      h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
      h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
      const hex = (h2 >>> 0).toString(16).padStart(8, '0') + (h1 >>> 0).toString(16).padStart(8, '0');
      return '0x' + hex.toUpperCase();
    }

    // Central REST API Dispatcher
    function callBackendAPI(method, endpoint, handlerFn) {
      const t0 = performance.now();
      const snapshot = JSON.stringify(db);
      let result;
      try { result = validateOperation(endpoint) || handlerFn(); }
      catch(e) { db=JSON.parse(snapshot);result={status:500,message:bi('操作失败，变更已撤销','Operation failed; changes were rolled back')};console.error(e); }
      if(result.status>=400) db=JSON.parse(snapshot);
      const latency = Math.max(2, Math.round(performance.now() - t0 + Math.random() * 6)) + 'ms';

      const logEntry = {
        id: 'REQ-' + Math.floor(1000 + Math.random() * 9000),
        time: new Date().toLocaleTimeString(),
        method,
        endpoint,
        status: result.status || 200,
        latency,
        summary: result.message || 'OK'
      };
      db.apiLogs.unshift(logEntry);
      if (db.apiLogs.length > 60) db.apiLogs.pop();

      commitCoreDatabase();
      showApiToast(`${method} ${endpoint} · ${logEntry.status}`, result.message, logEntry.status < 400);
      syncAllViews();
      if(window.jwbStorageFailed) showApiToast('Storage',bi('浏览器存储不可用，请导出备份以保留数据','Browser storage unavailable. Export a backup to keep your data'),false);
      return result;
    }

    function recordDoubleEntry(debitAccount, creditAccount, amountUSD, memo) {
      db.generalLedger.unshift({
        entryId: 'GL-' + Math.floor(10000 + Math.random() * 90000),
        time: new Date().toLocaleTimeString(),
        debitAccount,
        creditAccount,
        amountUSD: Number(amountUSD) || 0,
        memo
      });
      if (db.generalLedger.length > 60) db.generalLedger.pop();
    }

    let toastTimer = null;
    function showApiToast(routeText, msgText, isSuccess = true) {
      const toast = document.getElementById('apiToast');
      const dot = document.getElementById('apiToastDot');
      toast.setAttribute('aria-hidden','false');
      document.getElementById('apiToastRoute').textContent = routeText;
      document.getElementById('apiToastMsg').textContent = msgText;
      dot.className = `w-2.5 h-2.5 rounded-full mt-1 shrink-0 ${isSuccess ? 'bg-emerald-400' : 'bg-rose-400'}`;

      toast.classList.remove('opacity-0', 'translate-y-[-12px]');
      toast.classList.add('opacity-100', 'translate-y-0');
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-[-12px]');
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.setAttribute('aria-hidden','true');
        document.getElementById('apiToastRoute').textContent='';
        document.getElementById('apiToastMsg').textContent='';
      }, 3200);
    }

    // Calculate Total Treasury Cash in USD across all 6 currencies
    function getTotalTreasuryUSD() {
      let sum = 0;
      for (const [curr, bal] of Object.entries(db.treasuryWallets)) {
        sum += (Number(bal) || 0) * (FX_RATES_TO_USD[curr] || 1);
      }
      return sum;
    }

    // =========================================================================
    // 4. TREASURY & FX SWAP API ACTIONS
    // =========================================================================
    function apiDepositFunds(currency, amount) {
      callBackendAPI('POST', '/api/v1/treasury/wire-in', () => {
        if(!Object.hasOwn(CURRENCY_META,currency)||!validMoney(amount))return {status:400,message:bi('入金币种或金额无效','Invalid deposit currency or amount')};
        db.treasuryWallets[currency] = roundCurrency((db.treasuryWallets[currency] || 0) + amount,currency);
        const usdEq = amount * (FX_RATES_TO_USD[currency] || 1);
        recordDoubleEntry(
          `1010 · Sovereign Vault (${currency})`,
          `3010 · External Wire Inflow`,
          usdEq,
          `Wire In +${amount.toLocaleString()} ${currency}`
        );
        playLuxurySound('chime');
        return { status: 201, message: `成功电汇入金 +${CURRENCY_META[currency].symbol}${amount.toLocaleString()} ${currency}` };
      });
    }

    function apiAccrueMonthlyInterest() {
      callBackendAPI('POST', '/api/v1/treasury/accrue-apy', () => {
        const totalUsd = getTotalTreasuryUSD();
        const now = new Date();
        const period = now.getFullYear()+'-'+String(now.getMonth()+1).padStart(2,'0');
        if (db.interestPeriod === period) return {status:409,message:bi('本月已结息，请勿重复操作','Interest has already been accrued this month')};
        const monthlyInterest = Number((totalUsd * (Math.pow(1.0485,1/12)-1)).toFixed(2));
        db.interestPeriod = period;
        db.treasuryWallets.USD = Number((db.treasuryWallets.USD + monthlyInterest).toFixed(2));
        recordDoubleEntry(
          `1010 · Sovereign Vault (USD)`,
          `4020 · Treasury Interest Income`,
          monthlyInterest,
          `4.85% APY Monthly Yield Accrual`
        );
        playLuxurySound('chime');
        return { status: 200, message: `4.85% APY 月度结息入账 +$${monthlyInterest.toLocaleString()} USD` };
      });
    }

    // =========================================================================
    // 5. POS AUTHORIZATION, CARD CONTROLS & BILL REPAYMENT ENGINE
    // =========================================================================
    function quickFillPOS(merchant, category, currency, amount) {
      playLuxurySound('tick');
      document.getElementById('posMerchantInput').value = merchant;
      document.getElementById('posCategorySelect').value = category;
      document.getElementById('posCurrencySelect').value = currency;
      document.getElementById('posAmountInput').value = amount;
    }

    function executeCustomPOSSwipe() {
      const merchant = document.getElementById('posMerchantInput').value || 'Global Merchant';
      const category = document.getElementById('posCategorySelect').value || 'dining';
      const currency = document.getElementById('posCurrencySelect').value || 'USD';
      const foreignAmount = Number(document.getElementById('posAmountInput').value);

      callBackendAPI('POST', '/api/v1/pos/authorize', () => {
        const activeVC = db.cards[db.selectedVaultIndex];
        const meta = JWB_CARDS.find(c => c.id === activeVC.cardId) || JWB_CARDS[1];

        // 1. Check if Card is Frozen
        if (activeVC.status === 'FROZEN') {
          playLuxurySound('tick');
          return { status: 423, message: `拒付 (423 Locked): ${meta.name} 当前处于冻结状态，请先解冻卡片` };
        }

        // 2. Convert Currency at 0% FTF Mid-Market Rate
        const amountUSD = Number((foreignAmount * (FX_RATES_TO_USD[currency] || 1)).toFixed(2));

        // 3. Check Available Credit Limit
        const availCredit = activeVC.creditLimit - (activeVC.statementBalance || 0);
        if (amountUSD > availCredit) {
          playLuxurySound('tick');
          return { status: 402, message: `拒付 (402 Declined): 可用授信额度不足 (当前可用 $${availCredit.toFixed(2)})` };
        }

        // 4. Post Charge & Calculate JR Points
        const mult = meta.rates[category] || meta.rates.everyday || 2;
        const earnedJR = Math.round(amountUSD * mult);
        activeVC.statementBalance = Number(((activeVC.statementBalance || 0) + amountUSD).toFixed(2));
        db.jrPointsBalance += earnedJR;
        recordDoubleEntry(`1100 · JR Rewards Asset`,`4030 · Rewards Income`,earnedJR/100,`Purchase rewards: ${earnedJR} JR`);
        activeVC.spendProgress = Number(((activeVC.spendProgress || 0) + amountUSD).toFixed(2));

        const txHash = generateTxHash(`${merchant}-${Date.now()}`);
        const fxTag = currency !== 'USD' ? ` [${foreignAmount.toLocaleString()} ${currency} @ 0% FTF]` : '';

        db.posFeed.unshift({
          txHash,
          time: new Date().toLocaleTimeString(),
          desc: `${merchant}${fxTag} (${meta.name})`,
          amountStr: `+$${amountUSD.toFixed(2)}`,
          jrStr: `+${earnedJR.toLocaleString()} JR (${mult}X)`,
          type: 'spend'
        });

        recordDoubleEntry(
          `5010 · Personal Purchase Expense`,
          `2010 · Credit Card Payable (${meta.name})`,
          amountUSD,
          `POS Auth ${txHash}: ${merchant}`
        );

        // 5. Check Per-Card Annual Auto-Credit Quota
        if (meta.autoCreditRule && meta.autoCreditRule.category === category && activeVC.remainingCreditPool > 0) {
          const creditAmt = Number(Math.min(amountUSD, meta.autoCreditRule.singleCap, activeVC.remainingCreditPool).toFixed(2));
          if (creditAmt > 0) {
            activeVC.statementBalance = Number(Math.max(0, activeVC.statementBalance - creditAmt).toFixed(2));
            activeVC.remainingCreditPool = Number((activeVC.remainingCreditPool - creditAmt).toFixed(2));

            db.posFeed.unshift({
              txHash: generateTxHash(`CREDIT-${Date.now()}`),
              time: new Date().toLocaleTimeString(),
              desc: `✦ 自动报销抵扣：${meta.autoCreditRule.label_zh} (剩余额度池 $${activeVC.remainingCreditPool})`,
              amountStr: `-$${creditAmt.toFixed(2)}`,
              jrStr: 'Statement Credit Auto-Applied',
              type: 'credit'
            });

            recordDoubleEntry(
              `2010 · Credit Card Payable (${meta.name})`,
              `4010 · Statement Credit Income`,
              creditAmt,
              `Auto-Rebate Triggered (${meta.autoCreditRule.label_en})`
            );
          }
        }

        const welcomeMeta = JWB_CARDS.find(c => c.id === (activeVC.welcomeProductId || activeVC.cardId)) || meta;
        // 6. Check original account's welcome offer threshold
        if (!activeVC.welcomeUnlocked && activeVC.spendProgress >= welcomeMeta.welcomeSpendReq) {
          activeVC.welcomeUnlocked = true;
          db.jrPointsBalance += welcomeMeta.welcomeJR;
          recordDoubleEntry(`1100 · JR Rewards Asset`,`4030 · Welcome Bonus Income`,welcomeMeta.welcomeJR/100,`Welcome offer: ${welcomeMeta.name}`);
          db.posFeed.unshift({
            txHash: generateTxHash(`SUB-${Date.now()}`),
            time: new Date().toLocaleTimeString(),
            desc: `🎉 限时史高开卡礼达标入账 (${meta.name})`,
            amountStr: `$0.00`,
            jrStr: `+${welcomeMeta.welcomeJR.toLocaleString()} JR ($${(welcomeMeta.welcomeJR/100).toLocaleString()} USD)`,
            type: 'bonus'
          });
          playLuxurySound('chime');
          return { status: 200, message: `授权通过 ($${amountUSD}) 并成功解锁 +${welcomeMeta.welcomeJR.toLocaleString()} JR 史高开卡礼！` };
        }

        playLuxurySound('tick');
        return { status: 200, message: `POS 授权通过: $${amountUSD.toFixed(2)} · 累积 +${earnedJR.toLocaleString()} JR (${ txHash.slice(0, 10) })` };
      });
    }

    function apiToggleCardFreeze() {
      callBackendAPI('POST', '/api/v1/cards/security-freeze', () => {
        const activeVC = db.cards[db.selectedVaultIndex];
        activeVC.status = activeVC.status === 'FROZEN' ? 'ACTIVE' : 'FROZEN';
        playLuxurySound('flip');
        return {
          status: 200,
          message: activeVC.status === 'FROZEN'
            ? `卡片 ${escapeHTML(activeVC.cardNumber)} 已安全冻结，暂停一切 POS 授权`
            : `卡片 ${escapeHTML(activeVC.cardNumber)} 已解冻并恢复全球 0% FTF 清算`
        };
      });
    }

    function apiRotateCardCVV() {
      callBackendAPI('POST', '/api/v1/cards/rotate-cvv', () => {
        const activeVC = db.cards[db.selectedVaultIndex];
        const oldCvv = activeVC.cvv;
        activeVC.cvv = generate5CharHybridCVV();
        playLuxurySound('flip');
        return {
          status: 200,
          message: `5 位混合安全码已动态轮换: ${oldCvv} ➔ ${escapeHTML(activeVC.cvv)}`
        };
      });
    }

    function apiRepayCardBill(method) {
      callBackendAPI('POST', '/api/v1/cards/repay', () => {
        const activeVC = db.cards[db.selectedVaultIndex];
        if(!['JR','USD'].includes(method))return {status:400,message:bi('不支持的还款方式','Unsupported repayment method')};
        const bal = Number(activeVC.statementBalance || 0);
        if (bal <= 0) {
          return { status: 400, message: '当前卡片账单为 $0.00，无需还款' };
        }

        if (method === 'JR') {
          const maxUsdFromJr = db.jrPointsBalance / 100;
          if (maxUsdFromJr <= 0) {
            return { status: 402, message: 'JR 积分池余额为 0，无法抵扣账单' };
          }
          const payUsd = Number(Math.min(bal, maxUsdFromJr).toFixed(2));
          const jrUsed = Math.round(payUsd * 100);
          activeVC.statementBalance = Number((bal - payUsd).toFixed(2));
          db.jrPointsBalance -= jrUsed;

          db.posFeed.unshift({
            txHash: generateTxHash(`JR-PAY-${Date.now()}`),
            time: new Date().toLocaleTimeString(),
            desc: `✦ 1 JR = $0.01 积分直接抵扣账单`,
            amountStr: `-$${payUsd.toFixed(2)}`,
            jrStr: `-${jrUsed.toLocaleString()} JR`,
            type: 'credit'
          });

          recordDoubleEntry(
            `2010 · Credit Card Payable (${activeVC.cardNumber.slice(-4)})`,
            `1100 · JR Rewards Asset`,
            payUsd,
            `1:1 JR Statement Redemption (${jrUsed} JR)`
          );
          playLuxurySound('chime');
          return { status: 200, message: `成功使用 ${jrUsed.toLocaleString()} JR 抵扣 $${payUsd.toFixed(2)} 账单` };
        } else {
          if (db.treasuryWallets.USD < bal) {
            return { status: 402, message: `USD 主权账户余额不足 ($${db.treasuryWallets.USD.toFixed(2)})` };
          }
          db.treasuryWallets.USD = Number((db.treasuryWallets.USD - bal).toFixed(2));
          activeVC.statementBalance = 0.00;

          db.posFeed.unshift({
            txHash: generateTxHash(`ACH-PAY-${Date.now()}`),
            time: new Date().toLocaleTimeString(),
            desc: `✦ USD 主权支票账户自动全额还款`,
            amountStr: `-$${bal.toFixed(2)}`,
            jrStr: ' checking ➔ card balance',
            type: 'credit'
          });

          recordDoubleEntry(
            `2010 · Credit Card Payable (${activeVC.cardNumber.slice(-4)})`,
            `1010 · Sovereign Vault (USD)`,
            bal,
            `Full Statement Auto-Pay from USD Checking`
          );
          playLuxurySound('chime');
          return { status: 200, message: `已从 USD 主权金库全额偿还信用卡账单 $${bal.toFixed(2)}` };
        }
      });
    }

    // =========================================================================
    // 6. FULL DATABASE JSON EXPORT & IMPORT (Real Persistence)
    // =========================================================================
    function exportFullDatabaseJSON() {
      callBackendAPI('GET', '/api/v1/core/export-backup', () => {
        const dataStr = JSON.stringify(db, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `JWB_Core_Banking_Ledger_${new Date().toISOString().slice(0,10)}.json`;
        document.body.append(a);a.click();a.remove();
        setTimeout(()=>URL.revokeObjectURL(url),1000);
        playLuxurySound('chime');
        return { status: 200, message: '已导出完整 JWB 银行明文 JSON 账本备份 (.json)' };
      });
    }

    function importFullDatabaseJSON(event) {
      const input = event.target, file = input.files[0];
      if(!file) return;
      if(file.size>5*1024*1024){showApiToast('Restore · 413',bi('文件不能超过 5 MB','Backup must be under 5 MB'),false);input.value='';return;}
      const reader=new FileReader();
      reader.onload=()=>{try{
        const restored=validateDatabase(JSON.parse(reader.result));
        if(!confirm(bi('导入将覆盖当前演示数据，是否继续？','Restore will replace the current demo data. Continue?')))return;
        db=restored;commitCoreDatabase();syncAllViews();showApiToast('Restore · 200',bi('账本恢复成功','Backup restored'),true);
      }catch(e){showApiToast('Restore · 400',bi('备份校验失败，现有数据未变：','Invalid backup; current data preserved: ')+e.message,false);}finally{input.value='';}};
      reader.onerror=()=>{showApiToast('Restore · 400',bi('读取失败，请重试','Could not read the backup'),false);input.value='';};
      reader.readAsText(file);
    }

    function resetVaultData() {
      if(!confirm(bi('重置将清除当前演示数据，建议先导出备份。是否继续？','Reset clears all demo data. Export a backup first if needed. Continue?'))) return;
      db = createInitialDatabase();
      commitCoreDatabase();
      playLuxurySound('flip');
      showApiToast('POST /api/v1/core/reset · 200', '核心银行数据库已恢复至初始状态', true);
      syncAllViews();
    }

    // =========================================================================
    // 7. MULTI-PAGE SPA ROUTER & VIEW SYNCHRONIZATION
    // =========================================================================
    let currentPage = 'home';
    let currentCardCategory = 'all';
    let currentLang = 'zh';
    let currentCalcCardId = 'gold';
    let allPerksExpanded = false;
    let lastFocusedFanCardId = null;

    let activeApprovalState = {
      cardId: 'gold',
      holderName: 'JASA XU',
      cardNumber: '8888-0288-4921-8834',
      expDate: '10/31',
      cvv: 'AK8B0',
      initialLimit: 28500,
      currentLimit: 28500,
      maxCap: 50000,
      score: 785,
      cliApplied: false
    };

    function switchPage(pageId) {
      playLuxurySound('tick');
      if (!document.getElementById(`page-${pageId}`)) return;
      currentPage = pageId;
      if (location.hash !== '#' + pageId) history.pushState(null,'','#'+pageId);

      document.querySelectorAll('.spa-page').forEach(el => el.classList.remove('is-active'));
      const targetPage = document.getElementById(`page-${pageId}`);
      if (targetPage) targetPage.classList.add('is-active');

      document.querySelectorAll('[data-nav-desktop]').forEach(btn => {
        const active = btn.getAttribute('data-nav-desktop') === pageId;
        btn.setAttribute('aria-current',active?'page':'false');
        btn.className = active
          ? 'px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-amber-200 text-neutral-950 flex items-center gap-1.5'
          : 'px-3.5 py-1.5 rounded-full text-xs font-medium transition whitespace-nowrap text-neutral-300 hover:text-white flex items-center gap-1.5';
      });

      document.querySelectorAll('[data-nav-mobile]').forEach(btn => {
        const active = btn.getAttribute('data-nav-mobile') === pageId;
        btn.setAttribute('aria-current',active?'page':'false');
        btn.className = `relative flex flex-col items-center justify-center gap-1 transition ${active ? 'text-amber-200 font-semibold' : 'text-neutral-400'}`;
      });

      window.scrollTo({ top: 0, behavior: 'smooth' });
      syncAllViews();
      animateViewEntry(targetPage);
    }

    function syncAllViews() {
      if (!db) loadCoreDatabase();
      const totalTreasuryUSD = getTotalTreasuryUSD();
      const jrUsdVal = db.jrPointsBalance / 100;
      const totalCardDebt = db.cards.reduce((acc, c) => acc + (Number(c.statementBalance) || 0), 0);
      const totalCreditLimit = db.cards.reduce((acc, c) => acc + (Number(c.creditLimit) || 0), 0);
      const netWorth = totalTreasuryUSD + jrUsdVal - totalCardDebt;

      // 1. Update Home Balance Sheet
      document.getElementById('bsTotalCashUsd').textContent = `$${totalTreasuryUSD.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById('bsTotalJrUsd').textContent = `$${jrUsdVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById('bsTotalJrPts').textContent = `${db.jrPointsBalance.toLocaleString()} JR 可随时销账 ➔`;
      document.getElementById('bsTotalStatement').textContent = `$${totalCardDebt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById('bsTotalAvailCredit').textContent = `总授信 $${totalCreditLimit.toLocaleString()} ➔`;
      document.getElementById('bsNetWorth').textContent = `$${netWorth.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

      // 2. Render Treasury Wallets Grid
      renderTreasuryPage(totalTreasuryUSD);

      // 3. Render Vault & POS Terminal
      renderVaultAndSandbox();

      // 4. Render Cards Matrix
      renderCardsMatrix();

      // 5. Render Backend API & Double-Entry Ledger
      renderBackendConsole();
      filterTransactionFeed();
      localizeDocument();
      decorateCards();
      animateNumericUpdates();
    }

    function renderTreasuryPage(totalTreasuryUSD) {
      const grid = document.getElementById('treasuryWalletsGrid');
      if (!grid) return;
      grid.innerHTML = Object.entries(db.treasuryWallets).map(([curr, bal]) => {
        const meta = CURRENCY_META[curr];
        const usdEq = bal * FX_RATES_TO_USD[curr];
        return `
          <div class="glass-panel rounded-2xl p-4 flex flex-col justify-between">
            <div class="flex items-center justify-between">
              <span class="text-base">${meta.flag}</span>
              <span class="text-xs font-mono font-bold text-amber-200">${curr}</span>
            </div>
            <div class="my-2">
              <div class="text-[11px] text-neutral-400">${currentLang === 'zh' ? meta.name_zh : meta.name_en}</div>
              <div class="text-sm sm:text-base font-mono font-bold text-white mt-0.5 truncate">${meta.symbol}${bal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
            <div class="text-[10px] font-mono text-emerald-400">≈ $${usdEq.toLocaleString(undefined, { maximumFractionDigits: 0 })} USD</div>
          </div>
        `;
      }).join('');

      document.getElementById('lombardTotalUsd').textContent = `$${totalTreasuryUSD.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById('lombardBoostPool').textContent = `+$${Math.round(totalTreasuryUSD * 0.8).toLocaleString()}`;
      previewFxSwap();
    }

    function renderBackendConsole() {
      const apiContainer = document.getElementById('apiLogsContainer');
      const glContainer = document.getElementById('doubleEntryContainer');
      document.getElementById('apiTotalCallsBadge').textContent = `${db.apiLogs.length} Requests`;

      apiContainer.innerHTML = db.apiLogs.map(log => `
        <div class="p-3 rounded-xl bg-black/45 border border-white/[0.07] space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-sky-300 font-semibold">${escapeHTML(log.method)} ${escapeHTML(log.endpoint)}</span>
            <span class="px-2 py-0.2 rounded text-[10px] ${log.status < 400 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">
              HTTP ${log.status} · ${escapeHTML(log.latency)}
            </span>
          </div>
          <div class="text-neutral-300 text-[11px] leading-relaxed">${escapeHTML(log.summary)}</div>
          <div class="text-[10px] text-neutral-500">${escapeHTML(log.id)} · ${escapeHTML(log.time)}</div>
        </div>
      `).join('');

      glContainer.innerHTML = db.generalLedger.map(gl => `
        <div class="p-3 rounded-xl bg-black/45 border border-white/[0.07] space-y-1">
          <div class="flex items-center justify-between text-[11px]">
            <span class="text-amber-200 font-semibold">${escapeHTML(gl.entryId)} · ${escapeHTML(gl.memo)}</span>
            <span class="text-emerald-400 font-bold">$${gl.amountUSD.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          <div class="text-[11px] text-neutral-300">
            <div><span class="text-emerald-400">[借 DR]</span> ${escapeHTML(gl.debitAccount)}</div>
            <div><span class="text-sky-300">[贷 CR]</span> ${escapeHTML(gl.creditAccount)}</div>
          </div>
          <div class="text-[10px] text-neutral-500">${escapeHTML(gl.time)}</div>
        </div>
      `).join('');
    }

    // =========================================================================
    // 8. NATIVE WEB AUDIO SYNTHESIZER & 3D SPECULAR GLARE
    // =========================================================================
    let soundEnabled = true;
    let audioCtx = null;

    function initAudio() {
      if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    }

    function playLuxurySound(type) {
      if (!soundEnabled) return;
      try {
        initAudio();
        if (!audioCtx) return;
        const now = audioCtx.currentTime;
        if (type === 'flip' || type === 'tick') {
          const osc = audioCtx.createOscillator();
          const gain = audioCtx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(type === 'flip' ? 320 : 520, now);
          osc.frequency.exponentialRampToValueAtTime(type === 'flip' ? 680 : 280, now + 0.075);
          gain.gain.setValueAtTime(0.055, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
          osc.connect(gain);
          gain.connect(audioCtx.destination);
          osc.start(now);
          osc.stop(now + 0.085);
        } else if (type === 'chime') {
          [523.25, 659.25, 783.99, 1046.5].forEach((freq, idx) => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, now + idx * 0.055);
            gain.gain.setValueAtTime(0.065, now + idx * 0.055);
            gain.gain.exponentialRampToValueAtTime(0.0008, now + idx * 0.055 + 0.42);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now + idx * 0.055);
            osc.stop(now + idx * 0.055 + 0.44);
          });
        }
      } catch (e) {}
    }

    function toggleSound() {
      soundEnabled = !soundEnabled;
      const btn = document.getElementById('soundToggleBtn');
      btn.textContent = soundEnabled ? '🔊 音效' : '🔇 静音';
      btn.setAttribute('aria-pressed',String(soundEnabled));
      btn.dataset.muted=String(!soundEnabled);
      if (soundEnabled) playLuxurySound('tick');
    }

    document.addEventListener('mousemove', (e) => {
      const card = e.target.closest('.iso-card');
      if (!card) return;
      const rect = card.getBoundingClientRect();
      const xPct = Math.round(((e.clientX - rect.left) / rect.width) * 100);
      const yPct = Math.round(((e.clientY - rect.top) / rect.height) * 100);
      card.style.setProperty('--glare-x', `${xPct}%`);
      card.style.setProperty('--glare-y', `${yPct}%`);
      card.style.setProperty('--glare-alpha', '0.22');
    });

    // =========================================================================
    // 9. HERO 3D FAN STAGE, CARDS MATRIX & VAULT RENDERING
    // =========================================================================
    function replayFanAnimation() {
      if(motionReduced()){document.getElementById('heroFanStage').classList.add('is-unfolded');return;}
      playLuxurySound('flip');
      const stage = document.getElementById('heroFanStage');
      stage.classList.remove('is-unfolded');
      setTimeout(() => { stage.classList.add('is-unfolded'); }, 550);
    }

    function updateFanHint(cardId) {
      const card = JWB_CARDS.find(c => c.id === cardId);
      if (!card) return;
      document.getElementById('fanHoverHint').innerHTML =
        `<span class="text-amber-200 font-semibold">${card.name}</span> · 卡段 ${card.bin} · 上限 $${card.maxCap.toLocaleString()} · 史高 ${card.welcomeJR.toLocaleString()} JR ($${(card.welcomeJR/100).toLocaleString()})`;
    }

    function filterCards(cat) {
      playLuxurySound('tick');
      currentCardCategory = cat;
      document.querySelectorAll('[data-cat-btn]').forEach(btn => {
        const active = btn.getAttribute('data-cat-btn') === cat;
        btn.className = active
          ? 'px-4 py-1.5 rounded-full text-xs font-medium bg-amber-200 text-neutral-950 transition whitespace-nowrap'
          : 'px-4 py-1.5 rounded-full text-xs font-medium bg-white/[0.05] text-neutral-300 hover:text-white border border-white/10 transition whitespace-nowrap';
      });
      renderCardsMatrix();
    }

    function renderCardsMatrix() {
      const grid = document.getElementById('cardsGrid');
      if (!grid) return;
      const ownedIds = new Set((db?.cards || []).map(vc => vc.cardId));
      const filtered = currentCardCategory === 'all'
        ? JWB_CARDS
        : JWB_CARDS.filter(c => c.category === currentCardCategory);

      grid.innerHTML = filtered.map(card => {
        const sub = currentLang === 'zh' ? card.sub_zh : card.sub_en;
        const badge = currentLang === 'zh' ? card.badge_zh : card.badge_en;
        const feeText = currentLang === 'zh' ? card.feeText_zh : card.feeText_en;
        const welcomeDesc = currentLang === 'zh' ? card.welcome_zh : card.welcome_en;
        const tags = currentLang === 'zh' ? card.tags_zh : card.tags_en;
        const earnText = currentLang === 'zh' ? card.earn_zh : card.earn_en;
        const perks = currentLang === 'zh' ? card.perks_zh : card.perks_en;
        const drawerOpenClass = allPerksExpanded ? 'is-open' : '';
        const isOwned = ownedIds.has(card.id);

        return `
          <div class="glass-panel rounded-3xl p-5 sm:p-6 flex flex-col justify-between min-w-0">
            <div>
              <div class="flex items-center justify-between gap-2 mb-3">
                <span class="px-2.5 py-0.5 rounded-full bg-amber-300/10 border border-amber-300/25 text-[11px] font-mono text-amber-200 truncate">
                  ${badge}
                </span>
                ${isOwned
                  ? `<span class="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-[10px] font-mono text-emerald-300 shrink-0">✓ 已在卡包</span>`
                  : `<span class="text-[11px] font-mono text-neutral-400 shrink-0">BIN ${card.bin}</span>`
                }
              </div>

              <div onclick="openApprovalModal('${card.id}')" class="iso-card ${card.finishClass} p-4 sm:p-5 flex flex-col justify-between cursor-pointer hover:scale-[1.015]">
                <div class="relative z-10 flex items-center justify-between gap-2">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="font-mono font-bold text-sm sm:text-base tracking-wider text-white shrink-0">JWB</span>
                    <span class="text-[10px] sm:text-xs font-mono tracking-wider uppercase text-neutral-200 truncate">${card.name}</span>
                  </div>
                  <span class="px-2 py-0.5 rounded bg-black/40 border border-white/15 text-[9px] sm:text-[10px] font-mono text-emerald-300 shrink-0">
                    CAP $${card.maxCap.toLocaleString()}
                  </span>
                </div>

                <div class="relative z-10 flex items-center justify-between my-auto">
                  <div class="flex items-center gap-2.5">
                    <div class="emv-chip"></div>
                    <svg class="w-4 h-4 text-white/60" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                      <path stroke-linecap="round" d="M8.5 14.5a4 4 0 010-5M11.5 16.5a7 7 0 010-9"/>
                    </svg>
                  </div>
                  <div class="text-right font-mono">
                    <div class="text-[9px] text-neutral-400">EXCLUSIVE BIN</div>
                    <div class="text-xs sm:text-sm font-semibold text-white tracking-wider">${card.bin}-XXXX-XXXX</div>
                  </div>
                </div>

                <div class="relative z-10 flex items-end justify-between text-[9px] sm:text-[10px] font-mono text-neutral-300">
                  <span class="truncate">JASA WORLDWIDE BANK</span>
                  <span class="text-amber-200 shrink-0">JASA NETWORK · 0% FTF</span>
                </div>
              </div>

              <div class="mt-4">
                <h3 class="text-lg sm:text-xl font-semibold text-white leading-snug">${card.name}</h3>
                <p class="text-xs text-neutral-400 mt-0.5">${sub}</p>
              </div>

              <div class="mt-3.5 grid grid-cols-2 gap-2 p-3 rounded-2xl bg-black/35 border border-white/[0.06]">
                <div class="min-w-0">
                  <div class="text-[10px] font-mono text-neutral-400 truncate">MAX CREDIT CAP</div>
                  <div class="text-sm sm:text-base font-mono font-semibold text-emerald-400 mt-0.5 truncate">$${card.maxCap.toLocaleString()}</div>
                </div>
                <div class="border-l border-white/10 pl-3 min-w-0">
                  <div class="text-[10px] font-mono text-neutral-400 truncate">ANNUAL FEE</div>
                  <div class="text-xs sm:text-sm font-mono font-semibold text-white mt-0.5 truncate">${feeText}</div>
                </div>
              </div>

              <div class="mt-3 p-3 rounded-2xl bg-gradient-to-r from-amber-500/[0.08] to-transparent border border-amber-300/20">
                <div class="flex items-center justify-between gap-2 text-xs font-mono">
                  <span class="text-amber-200/90 truncate">限时史高开卡礼</span>
                  <span class="font-semibold text-amber-200 shrink-0">${card.welcomeJR.toLocaleString()} JR = $${(card.welcomeJR / 100).toLocaleString()}</span>
                </div>
                <p class="text-xs text-neutral-200 mt-1 leading-relaxed break-words">${welcomeDesc}</p>
              </div>

              <div class="mt-3 flex flex-wrap gap-1.5">
                ${tags.map(tag => `<span class="px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] text-[11px] text-neutral-300">${tag}</span>`).join('')}
              </div>

              <div class="mt-3.5 pt-3 border-t border-white/[0.07]">
                <button onclick="toggleElementDrawer('cardDrawer-${card.id}', this)" class="w-full flex items-center justify-between text-xs text-neutral-300 hover:text-amber-200 transition py-1">
                  <span>展开完整权益与回馈细则</span>
                  <span class="drawer-arrow">${allPerksExpanded ? '▴' : '▾'}</span>
                </button>
                <div id="cardDrawer-${card.id}" class="drawer-grid ${drawerOpenClass}">
                  <div class="drawer-inner">
                    <div class="pt-3 space-y-2.5 text-xs text-neutral-300 leading-relaxed">
                      <div class="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                        <span class="text-amber-200 font-medium">日常积分回馈：</span>${earnText}
                      </div>
                      <ul class="space-y-1.5 text-neutral-400 pl-1">
                        ${perks.map(p => `<li class="break-words">• ${p}</li>`).join('')}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <button onclick="openApprovalModal('${card.id}')" class="mt-4 w-full py-3 rounded-2xl bg-white/[0.07] hover:bg-amber-200 hover:text-neutral-950 border border-white/15 font-medium text-xs sm:text-sm text-white transition">
              立即申请 / 秒批授信
            </button>
          </div>
        `;
      }).join('');
    }

    function renderVaultAndSandbox() {
      const cards = db.cards;
      if (db.selectedVaultIndex >= cards.length) db.selectedVaultIndex = 0;

      const activeVC = cards[db.selectedVaultIndex];
      const activeMeta = JWB_CARDS.find(c => c.id === activeVC.cardId) || JWB_CARDS[1];

      const totalCreditLine = cards.reduce((acc, c) => acc + c.creditLimit, 0);
      document.getElementById('desktopVaultBadge').textContent = cards.length;
      document.getElementById('mobileVaultBadge').textContent = cards.length;
      document.getElementById('vaultTotalLimit').textContent = `$${totalCreditLine.toLocaleString()}`;
      document.getElementById('vaultCardCountSub').textContent = `${cards.length} Active Cards · AAoA 100%`;
      document.getElementById('vaultTotalJR').textContent = `${db.jrPointsBalance.toLocaleString()} JR`;
      document.getElementById('vaultTotalJRUsd').textContent = `= $${(db.jrPointsBalance / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD`;
      document.getElementById('vaultStatementBal').textContent = `$${(activeVC.statementBalance || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById('vaultAutoCreditsTotal').textContent = `本卡年度剩余自动报销池: $${(activeVC.remainingCreditPool ?? activeMeta.fixedCredits).toFixed(2)}`;

      // Render Card List
      document.getElementById('vaultCardsList').innerHTML = cards.map((vc, idx) => {
        const meta = JWB_CARDS.find(c => c.id === vc.cardId) || JWB_CARDS[1];
        const isSelected = idx === db.selectedVaultIndex;
        const avail = vc.creditLimit - (vc.statementBalance || 0);
        return `
          <div onclick="selectVaultCard(${idx})"
               class="p-3 rounded-2xl border cursor-pointer transition flex items-center justify-between gap-2 ${isSelected ? 'bg-amber-200/15 border-amber-300' : 'bg-white/[0.03] border-white/10 hover:bg-white/[0.06]'}">
            <div class="min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="text-xs sm:text-sm font-semibold text-white truncate">${meta.name}</span>
                ${vc.status === 'FROZEN' ? `<span class="px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 font-mono text-[10px]">❄️ 已冻结</span>` : ''}
                ${vc.welcomeUnlocked ? `<span class="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px]">史高已拿</span>` : ''}
              </div>
              <div class="text-[11px] font-mono text-neutral-400 mt-0.5">${escapeHTML(vc.cardNumber)} · CVV ${escapeHTML(vc.cvv)}</div>
            </div>
            <div class="text-right shrink-0 font-mono">
              <div class="text-xs font-bold text-emerald-400">可用 $${avail.toLocaleString()}</div>
              <div class="text-[10px] text-neutral-400">账单 $${(vc.statementBalance || 0).toFixed(0)} / 总额 $${vc.creditLimit.toLocaleString()}</div>
            </div>
          </div>
        `;
      }).join('');

      // Selected Card Visual Replica
      const freezeBtn = document.getElementById('btnFreezeCard');
      if (freezeBtn) {
        freezeBtn.textContent = activeVC.status === 'FROZEN' ? '🔥 解冻此卡 (Unfreeze)' : '❄️ 冻结此卡 (Freeze)';
      }

      document.getElementById('vaultActiveCardPreview').innerHTML = `
        <div class="iso-card ${activeMeta.finishClass} ${activeVC.status === 'FROZEN' ? 'is-frozen' : ''} p-4 sm:p-5 flex flex-col justify-between">
          <div class="relative z-10 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="font-mono font-bold text-sm sm:text-base text-white">JWB</span>
              <span class="text-xs font-mono uppercase text-neutral-200">${activeMeta.name}</span>
            </div>
            <span class="px-2 py-0.5 rounded bg-black/45 border border-white/15 text-[10px] font-mono ${activeVC.status === 'FROZEN' ? 'text-rose-300' : 'text-emerald-300'}">
              ${activeVC.status === 'FROZEN' ? 'FROZEN · LOCKED' : `AVAIL $${(activeVC.creditLimit - (activeVC.statementBalance||0)).toLocaleString()}`}
            </span>
          </div>
          <div class="relative z-10 flex items-center justify-between my-auto">
            <div class="emv-chip"></div>
            <div class="text-right font-mono">
              <div class="text-xs sm:text-sm font-bold text-white tracking-wider">${escapeHTML(activeVC.cardNumber)}</div>
              <div class="text-[10px] text-amber-200">EXP ${escapeHTML(activeVC.expDate)} · CVV ${escapeHTML(activeVC.cvv)}</div>
            </div>
          </div>
          <div class="relative z-10 flex items-end justify-between text-[10px] font-mono text-neutral-300">
            <span>${escapeHTML(activeVC.holderName)}</span>
            <span class="text-amber-200">STATEMENT: $${(activeVC.statementBalance || 0).toFixed(2)}</span>
          </div>
        </div>
      `;

      const preservedSelects = ['productChangeSelect','reallocFromSelect','reallocToSelect'].map(id=>[id,document.getElementById(id).value]);
      // Product Change & Reallocation Dropdowns
      document.getElementById('productChangeSelect').innerHTML = JWB_CARDS.map(c =>
        `<option value="${c.id}" ${c.id === activeVC.cardId ? 'selected' : ''}>${c.name} ($${c.annualFee}/yr · Cap $${c.maxCap.toLocaleString()})</option>`
      ).join('');

      const optionsHtml = cards.map((vc, idx) => {
        const m = JWB_CARDS.find(c => c.id === vc.cardId) || JWB_CARDS[0];
        return `<option value="${idx}">${m.name.replace('JWB ','')} ($${vc.creditLimit.toLocaleString()})</option>`;
      }).join('');
      const fromSel = document.getElementById('reallocFromSelect');
      const toSel = document.getElementById('reallocToSelect');
      fromSel.innerHTML = optionsHtml;
      toSel.innerHTML = optionsHtml;
      if (cards.length > 1) {
        fromSel.value = '0';
        toSel.value = '1';
      }

      if (window.lastRenderedVaultUid === activeVC.uid) preservedSelects.forEach(([id,value])=>{ const el=document.getElementById(id); if([...el.options].some(o=>o.value===value)) el.value=value; });
      window.lastRenderedVaultUid = activeVC.uid;
      // Welcome Offer Tracker
      const welcomeMeta = JWB_CARDS.find(c => c.id === (activeVC.welcomeProductId || activeVC.cardId)) || activeMeta;
      const req = welcomeMeta.welcomeSpendReq;
      const prog = Math.min(req, activeVC.spendProgress || 0);
      const pct = Math.min(100, Math.round((prog / req) * 100));
      document.getElementById('sandboxWelcomeTitle').textContent = `✦ ${welcomeMeta.name} 限时史高开卡礼进度`;
      document.getElementById('sandboxWelcomeStatus').textContent =
        activeVC.welcomeUnlocked
          ? `✓ 已解锁 +${welcomeMeta.welcomeJR.toLocaleString()} JR ($${(welcomeMeta.welcomeJR/100).toLocaleString()})`
          : `$${prog.toLocaleString()} / $${req.toLocaleString()} (${welcomeMeta.welcomeJR.toLocaleString()} JR)`;
      document.getElementById('sandboxWelcomeBar').style.width = `${pct}%`;

      // POS Clearing Feed
      document.getElementById('sandboxLedger').innerHTML = db.posFeed.map(item => `
        <div data-transaction-type="${escapeHTML(item.type)}" class="p-3 rounded-xl bg-black/40 border border-white/[0.07] flex items-center justify-between gap-2 text-xs">
          <div class="min-w-0">
            <div class="font-medium text-white truncate">${escapeHTML(item.desc)}</div>
            <div class="text-[10px] font-mono text-neutral-400">${escapeHTML(item.txHash || '')} · ${escapeHTML(item.time)}</div>
          </div>
          <div class="text-right font-mono shrink-0">
            <div class="${item.type === 'credit' || item.type === 'bonus' ? 'text-emerald-400 font-bold' : 'text-white'}">${escapeHTML(item.amountStr)}</div>
            <div class="text-[10px] text-amber-200">${escapeHTML(item.jrStr)}</div>
          </div>
        </div>
      `).join('');
    }

    function selectVaultCard(idx) {
      if(!Number.isInteger(idx)||idx<0||idx>=db.cards.length)return;
      playLuxurySound('tick');
      db.selectedVaultIndex = idx;
      commitCoreDatabase();
      renderVaultAndSandbox();
    }

    function executeLosslessProductChange() {
      const targetCardId = document.getElementById('productChangeSelect').value;
      callBackendAPI('POST', '/api/v1/cards/product-change', () => {
        const activeVC = db.cards[db.selectedVaultIndex];
        const newMeta = JWB_CARDS.find(c => c.id === targetCardId);
        if (!newMeta || newMeta.id === activeVC.cardId) return {status:400,message:bi('请选择不同的目标卡种','Choose a different product')};
        if (activeVC.statementBalance > newMeta.maxCap) return {status:409,message:bi('请先还款至目标卡种额度上限以内','Repay below the target product cap first')};
        activeVC.welcomeProductId ||= activeVC.cardId;
        activeVC.benefitPools ||= {};
        activeVC.benefitPools[activeVC.cardId] = activeVC.remainingCreditPool;
        const targetPool = activeVC.benefitPools[newMeta.id] ?? Math.min(activeVC.remainingCreditPool,newMeta.fixedCredits);
        activeVC.cardId = newMeta.id;
        if (activeVC.creditLimit > newMeta.maxCap) activeVC.creditLimit = newMeta.maxCap;
        activeVC.remainingCreditPool = targetPool;

        db.posFeed.unshift({
          txHash: generateTxHash(`PC-${Date.now()}`),
          time: new Date().toLocaleTimeString(),
          desc: `无损升降级完成 ➔ ${newMeta.name} (保留原卡号 ${escapeHTML(activeVC.cardNumber)})`,
          amountStr: '$0.00',
          jrStr: 'No Hard Pull · 账龄 100% 保留',
          type: 'bonus'
        });
        playLuxurySound('chime');
        return { status: 200, message: `已无损切换为 ${newMeta.name}，原 8888 卡号与 CVV 100% 保留` };
      });
    }

    function executeCreditReallocation() {
      callBackendAPI('POST', '/api/v1/cards/reallocate-limit', () => {
        if (db.cards.length < 2) return { status: 400, message: '卡包需至少 2 张卡片方可调配额度' };
        const fromIdx = Number(document.getElementById('reallocFromSelect').value);
        const toIdx = Number(document.getElementById('reallocToSelect').value);
        const amount = Math.max(0, Number(document.getElementById('reallocAmountInput').value) || 0);
        if (fromIdx === toIdx) return { status: 400, message: '请选择两张不同的卡片进行额度调配' };

        const fromCard = db.cards[fromIdx];
        const toCard = db.cards[toIdx];
        const toMeta = JWB_CARDS.find(c => c.id === toCard.cardId);

        if (fromCard.creditLimit - amount < Math.max(2000, fromCard.statementBalance)) {
          return { status: 400, message: '调出卡片额度必须覆盖欠款且至少保留 $2,000' };
        }
        if (toCard.creditLimit + amount > toMeta.maxCap) {
          return { status: 400, message: `超出 ${toMeta.name} 最高额度上限 ($${toMeta.maxCap.toLocaleString()})` };
        }

        fromCard.creditLimit -= amount;
        toCard.creditLimit += amount;
        playLuxurySound('chime');
        return { status: 200, message: `成功跨卡无损调拨 $${amount.toLocaleString()} 授信额度` };
      });
    }

    // =========================================================================
    // 10. 1 JR = 1 CENT CALCULATOR & UNDERWRITING STUDIO
    // =========================================================================
    function toggleElementDrawer(drawerId, btnEl) {
      playLuxurySound('tick');
      const drawer = document.getElementById(drawerId);
      if (!drawer) return;
      const isOpen = drawer.classList.toggle('is-open');
      if (btnEl) {
        const arrow = btnEl.querySelector('.drawer-arrow');
        if (arrow) arrow.textContent = isOpen ? '▴' : '▾';
      }
    }

    function toggleAllCardDrawers() {
      playLuxurySound('tick');
      allPerksExpanded = !allPerksExpanded;
      document.getElementById('toggleAllPerksBtn').textContent = allPerksExpanded ? '收起全部详细权益 ▴' : '展开全部详细权益 ▾';
      renderCardsMatrix();
    }

    function renderCalculatorTabs() {
      const container = document.getElementById('calcCardTabs');
      if (!container) return;
      container.innerHTML = JWB_CARDS.map(card => {
        const active = card.id === currentCalcCardId;
        return `
          <button onclick="selectCalcCard('${card.id}')"
                  class="px-2.5 py-2 rounded-xl text-left border transition min-w-0 ${active ? 'bg-amber-200/15 border-amber-300 text-white' : 'bg-white/[0.03] border-white/10 text-neutral-400 hover:text-white'}">
            <div class="text-xs font-semibold truncate">${card.name}</div>
            <div class="text-[10px] font-mono text-amber-200/80 truncate">${card.bin}</div>
          </button>
        `;
      }).join('');
    }

    function selectCalcCard(cardId) {
      playLuxurySound('tick');
      currentCalcCardId = cardId;
      renderCalculatorTabs();
      updateCalculator();
    }

    function updateCalculator() {
      const card = JWB_CARDS.find(c => c.id === currentCalcCardId) || JWB_CARDS[1];
      const diningMo = Number(document.getElementById('sliderDining').value);
      const travelMo = Number(document.getElementById('sliderTravel').value);
      const everydayMo = Number(document.getElementById('sliderEveryday').value);

      document.getElementById('diningValDisplay').textContent = `$${diningMo.toLocaleString()} / mo`;
      document.getElementById('travelValDisplay').textContent = `$${travelMo.toLocaleString()} / mo`;
      document.getElementById('everydayValDisplay').textContent = `$${everydayMo.toLocaleString()} / mo`;

      const annualSpendJR = Math.round(
        (diningMo * 12 * card.rates.dining) +
        (travelMo * 12 * card.rates.travel) +
        (everydayMo * 12 * card.rates.everyday)
      );
      const offerMonths = card.id==='everyday'?3:card.id==='centurion'?12:6;
      const eligibleWelcome = (diningMo + travelMo + everydayMo)*offerMonths >= card.welcomeSpendReq ? card.welcomeJR : 0;
      const totalJR = eligibleWelcome + annualSpendJR;
      const totalCashValue = Math.round(totalJR / 100);
      const spendCashValue = Math.round(annualSpendJR / 100);
      const welcomeCashValue = Math.round(eligibleWelcome / 100);
      const categorySpend = {dining:diningMo*12,travel:travelMo*12,hotel:travelMo*12,everyday:everydayMo*12};
      const usedCredits = card.autoCreditRule ? Math.min(card.fixedCredits, categorySpend[card.autoCreditRule.category] || 0,card.autoCreditRule.singleCap*12) : 0;
      const netFirstYear = totalCashValue + usedCredits - card.annualFee;

      document.getElementById('calcActiveBin').textContent = `${card.bin}-XXXX-XXXX · MAX CAP $${card.maxCap.toLocaleString()}`;
      document.getElementById('calcActiveName').textContent = card.name;
      document.getElementById('calcWelcomeJR').textContent = `${eligibleWelcome.toLocaleString()} JR ($${welcomeCashValue.toLocaleString()})`;
      document.getElementById('calcSpendJR').textContent = `${annualSpendJR.toLocaleString()} JR ($${spendCashValue.toLocaleString()})`;
      document.getElementById('calcTotalJR').textContent = `${totalJR.toLocaleString()} JR ($${totalCashValue.toLocaleString()})`;
      document.getElementById('calcFixedCredits').textContent = `+$${usedCredits.toLocaleString()}`;
      document.getElementById('calcAnnualFee').textContent = `-$${card.annualFee.toLocaleString()}`;
      document.getElementById('calcNetValue').textContent = `${netFirstYear >= 0 ? '+' : ''}$${netFirstYear.toLocaleString()}`;
    }

    function computeLuhnCheckDigit(first15Digits) {
      let sum = 0;
      for (let i = 0; i < 15; i++) {
        let d = parseInt(first15Digits.charAt(i), 10);
        if (i % 2 === 0) {
          d *= 2;
          if (d > 9) d -= 9;
        }
        sum += d;
      }
      return (10 - (sum % 10)) % 10;
    }

    function generate8888CardNumber(binPrefix, useAll8) {
      if (useAll8) return '8888-8888-8888-8888';
      const cleanPrefix = binPrefix.replace(/\D/g, '');
      let body7 = '';
      for (let i = 0; i < 7; i++) body7 += Math.floor(Math.random() * 10).toString();
      const first15 = cleanPrefix + body7;
      const checkDigit = computeLuhnCheckDigit(first15);
      const full16 = first15 + checkDigit.toString();
      return `${full16.slice(0,4)}-${full16.slice(4,8)}-${full16.slice(8,12)}-${full16.slice(12,16)}`;
    }

    function generate5CharHybridCVV() {
      const letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
      const digits = '0123456789';
      return [
        letters[Math.floor(Math.random() * letters.length)],
        letters[Math.floor(Math.random() * letters.length)],
        digits[Math.floor(Math.random() * digits.length)],
        letters[Math.floor(Math.random() * letters.length)],
        digits[Math.floor(Math.random() * digits.length)]
      ].join('');
    }

    function populateModalSelect() {
      const select = document.getElementById('modalCardSelect');
      select.innerHTML = JWB_CARDS.map(c =>
        `<option value="${c.id}" class="bg-neutral-900 text-white">${c.name} (${c.bin} · Max Cap $${c.maxCap.toLocaleString()})</option>`
      ).join('');
    }

    function openApprovalModal(cardId) {
      populateModalSelect();
      document.getElementById('modalCardSelect').value = cardId || 'gold';
      document.getElementById('cliStatusBanner').classList.add('hidden');
      document.getElementById('certPreviewBox').classList.add('hidden');
      regenerateCardCredentials();
      runUnderwriting();
      switchPage('studio');
      playLuxurySound('chime');
    }

    function regenerateCardCredentials() {
      playLuxurySound('flip');
      const cardId = document.getElementById('modalCardSelect').value || 'gold';
      const card = JWB_CARDS.find(c => c.id === cardId) || JWB_CARDS[1];
      const useAll8 = document.getElementById('toggleAll8').checked;
      const now = new Date();
      const mm = String(now.getMonth() + 1).padStart(2, '0');
      const yy = String((now.getFullYear() + 5) % 100).padStart(2, '0');

      activeApprovalState.cardNumber = generate8888CardNumber(card.bin, useAll8);
      activeApprovalState.expDate = `${mm}/${yy}`;
      activeApprovalState.cvv = generate5CharHybridCVV();
      updateStudioCardUI();
    }

    function runUnderwriting() {
      const cardId = document.getElementById('modalCardSelect').value || 'gold';
      const card = JWB_CARDS.find(c => c.id === cardId) || JWB_CARDS[1];
      const rawName = (document.getElementById('inputName').value.trim() || 'JASA XU').slice(0,40).toUpperCase();
      const income = Math.min(1e9, Math.max(0, Number(document.getElementById('inputIncome').value) || 0));
      const months = Math.min(360,Math.max(0, Number(document.getElementById('inputMonths').value) || 0));
      const existing = Math.min(1e9, Math.max(0, Number(document.getElementById('inputExisting').value) || 0));

      const totalTreasuryUSD = getTotalTreasuryUSD();
      const historyFactor = Math.min(1.8, 0.5 + (months / 24));
      const baseLimit = (income * 0.12) + (existing * 0.45) * historyFactor;
      const lombardBoost = Math.round(totalTreasuryUSD * 0.8 * 0.35);
      const rawApproved = (baseLimit * card.tierMultiplier) + lombardBoost;
      const roundedApproved = Math.round(rawApproved / 500) * 500;
      const finalApproved = Math.min(card.maxCap, Math.max(2000, roundedApproved));

      const score = Math.min(850, Math.round(730 + Math.min(60, months * 1.5) + Math.min(55, (income + totalTreasuryUSD) / 4500)));

      if (activeApprovalState.cardId !== card.id) {
        activeApprovalState.cardId = card.id;
        const useAll8 = document.getElementById('toggleAll8').checked;
        activeApprovalState.cardNumber = generate8888CardNumber(card.bin, useAll8);
        activeApprovalState.cvv = generate5CharHybridCVV();
      }

      activeApprovalState.holderName = rawName;
      activeApprovalState.initialLimit = finalApproved;
      activeApprovalState.currentLimit = finalApproved;
      activeApprovalState.maxCap = card.maxCap;
      activeApprovalState.score = score;
      activeApprovalState.cliApplied = false;

      document.getElementById('cliStatusBanner').classList.add('hidden');
      updateStudioCardUI();
    }

    function updateStudioCardUI() {
      const card = JWB_CARDS.find(c => c.id === activeApprovalState.cardId) || JWB_CARDS[1];
      const headroom = Math.max(0, card.maxCap - activeApprovalState.currentLimit);

      document.getElementById('reportScore').textContent = `${activeApprovalState.score} / 850`;
      document.getElementById('reportMaxCap').textContent = `$${card.maxCap.toLocaleString()}`;
      document.getElementById('reportInitialLimit').textContent = `$${activeApprovalState.currentLimit.toLocaleString()}`;
      document.getElementById('reportHeadroom').textContent = `$${headroom.toLocaleString()}`;

      const frontEl = document.getElementById('studioCardFront');
      const backEl = document.getElementById('studioCardBack');
      ['finish-everyday', 'finish-gold', 'finish-aero', 'finish-aspire', 'finish-platinum', 'finish-centurion'].forEach(cls => {
        frontEl.classList.remove(cls);
        backEl.classList.remove(cls);
      });
      frontEl.classList.add(card.finishClass);
      backEl.classList.add(card.finishClass);

      document.getElementById('studioFrontTitle').textContent = card.name.toUpperCase();
      document.getElementById('studioFrontBadge').textContent = `MAX CAP $${card.maxCap.toLocaleString()}`;
      document.getElementById('studioFrontLimit').textContent = `$${activeApprovalState.currentLimit.toLocaleString()}`;
      document.getElementById('studioFrontHolder').textContent = activeApprovalState.holderName;
      document.getElementById('studioFrontBin').textContent = `BIN ${card.bin}`;

      document.getElementById('studioBackNumber').textContent = activeApprovalState.cardNumber;
      document.getElementById('studioBackExp').textContent = activeApprovalState.expDate;
      document.getElementById('studioBackCvv').textContent = activeApprovalState.cvv;

      document.getElementById('plainCardNum').textContent = activeApprovalState.cardNumber;
      document.getElementById('plainExp').textContent = activeApprovalState.expDate;
      document.getElementById('plainCvv').textContent = activeApprovalState.cvv;
    }

    function flipStudioCard() {
      playLuxurySound('flip');
      document.getElementById('studioCardFlipInner').classList.toggle('is-flipped');
    }

    function saveApprovedCardToVault() {
      callBackendAPI('POST', '/api/v1/underwriting/issue-card', () => {
        const card = JWB_CARDS.find(c => c.id === activeApprovalState.cardId) || JWB_CARDS[1];
        if (db.cards.some(c=>c.cardNumber===activeApprovalState.cardNumber)) return {status:409,message:bi('此卡号已签发，请换号后重试','This number is already issued. Regenerate to create another card')};
        db.cards.unshift({
          uid: 'v-' + Date.now(),
          cardId: card.id,
          welcomeProductId: card.id,
          holderName: activeApprovalState.holderName,
          cardNumber: activeApprovalState.cardNumber,
          expDate: activeApprovalState.expDate,
          cvv: activeApprovalState.cvv,
          creditLimit: activeApprovalState.currentLimit,
          statementBalance: 0.00,
          spendProgress: 0,
          welcomeUnlocked: false,
          remainingCreditPool: card.fixedCredits,
          status: 'ACTIVE'
        });
        db.selectedVaultIndex = 0;

        recordDoubleEntry(
          `1200 · Unallocated Credit Line Commitments`,
          `2200 · Issued Card Credit Line (${card.name})`,
          activeApprovalState.currentLimit,
          `Issued ${card.name} PAN ${activeApprovalState.cardNumber}`
        );

        playLuxurySound('chime');
        return { status: 201, message: `成功签发 ${card.name} 并存入数字卡包 (授信 $${activeApprovalState.currentLimit.toLocaleString()})` };
      });
    }

    function simulate61DayCLI() {
      callBackendAPI('POST', '/api/v1/credit/cli-3x', () => {
        const card = JWB_CARDS.find(c => c.id === activeApprovalState.cardId) || JWB_CARDS[1];
        if (activeApprovalState.cliApplied) return {status:409,message:bi('本次提额预览已完成','This credit increase has already been previewed')};
        const proposed3X = activeApprovalState.initialLimit * 3;
        const newLimit = Math.min(card.maxCap, proposed3X);
        activeApprovalState.currentLimit = newLimit;
        activeApprovalState.cliApplied = true;
        const issued = db.cards.find(c=>c.cardNumber===activeApprovalState.cardNumber);
        if(issued) issued.creditLimit = newLimit;
        updateStudioCardUI();

        const banner = document.getElementById('cliStatusBanner');
        banner.classList.remove('hidden');
        banner.textContent = `✦ 61天 3X 提额批核：额度由 $${activeApprovalState.initialLimit.toLocaleString()} 提升至 $${newLimit.toLocaleString()}`;
        playLuxurySound('chime');
        return { status: 200, message: `61天 3X 提额批核通过: 最新授信额度 $${newLimit.toLocaleString()}` };
      });
    }

    function bindAppleWallet() {
      playLuxurySound('chime');
      const btn = document.getElementById('walletBindBtn');
      showApiToast('Demo Wallet',bi('已生成本地演示令牌；不支持绑定真实 Apple Wallet','Local demo token created; this does not provision Apple Wallet'),true);
      const token = 'DEMO-' + Math.random().toString(36).substring(2, 6).toUpperCase();
      btn.textContent = `✓ ${token}`;
      btn.classList.add('border-emerald-400/50', 'text-emerald-300');
    }

    async function copyCredentials() {
      playLuxurySound('tick');
      const text = `JWB Card: ${activeApprovalState.cardNumber} | EXP: ${activeApprovalState.expDate} | CVV: ${activeApprovalState.cvv}`;
      try {
        if(navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(text);
        else {const box=document.createElement('textarea');box.value=text;document.body.append(box);box.select();const ok=document.execCommand('copy');box.remove();if(!ok)throw Error('copy');}
      } catch(e){showApiToast('Clipboard',bi('复制失败，请手动选取卡片信息','Copy failed. Please select the credentials manually'),false);return;}
      const btn = document.getElementById('copyCredsBtn');
      const old = btn.textContent;
      btn.textContent = '✓ 已复制';
      setTimeout(() => { btn.textContent = old; }, 1800);
    }

    // =========================================================================
    // 11. HIGH-DPI CANVAS + JSPDF CERTIFICATE GENERATOR
    // =========================================================================
    function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
      const chars = Array.from(text);
      let line = '';
      let currentY = y;
      for (let i = 0; i < chars.length; i++) {
        const testLine = line + chars[i];
        if (ctx.measureText(testLine).width > maxWidth && i > 0) {
          ctx.fillText(line, x, currentY);
          line = chars[i];
          currentY += lineHeight;
        } else {
          line = testLine;
        }
      }
      if (line) {
        ctx.fillText(line, x, currentY);
        currentY += lineHeight;
      }
      return currentY;
    }

    let lastCertificateRecord = null;
    let certificateDownloadBusy = false;
    function certificateBytesToBase64(bytes){return btoa(String.fromCharCode(...new Uint8Array(bytes)));}
    function certificateBase64ToBytes(s){return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}
    function certificateHex(bytes){return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');}
    async function createCertificateRecord(){
      const card=JWB_CARDS.find(c=>c.id===activeApprovalState.cardId)||JWB_CARDS[1];
      const now=new Date();
      const record={payload:{schema:'JWB-DEMO-CREDIT/1.0',documentId:'JWB-DEMO-'+now.toISOString().slice(0,10).replaceAll('-','')+'-'+(crypto.randomUUID?crypto.randomUUID().slice(0,8):Math.random().toString(16).slice(2,10)).toUpperCase(),issuer:'Jasa Worldwide Bank - Demonstration System',purpose:'SIMULATION ONLY - NOT A BANK CREDIT COMMITMENT',issuedAt:now.toISOString(),cardholder:activeApprovalState.holderName,product:card.name,maskedAccount:'**** **** **** '+activeApprovalState.cardNumber.slice(-4),currency:'USD',initialLimit:activeApprovalState.initialLimit,approvedLimit:activeApprovalState.currentLimit,productCap:card.maxCap,issuerDepartment:'JWB Digital Credit Office',language:currentLang},digest:null,algorithm:null,signature:null,publicKey:null,keyFingerprint:null};
      if(crypto.subtle){
        let keys=null;
        try{const raw=localStorage.getItem('jwb_demo_certificate_keys_v1');if(raw)keys=JSON.parse(raw);}catch(e){}
        let privateKey,publicKey;
        try{
          privateKey=await crypto.subtle.importKey('jwk',keys.privateKey,{name:'ECDSA',namedCurve:'P-256'},false,['sign']);
          publicKey=await crypto.subtle.importKey('jwk',keys.publicKey,{name:'ECDSA',namedCurve:'P-256'},true,['verify']);
        }catch(e){
          const pair=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
          privateKey=pair.privateKey;publicKey=pair.publicKey;
          keys={privateKey:await crypto.subtle.exportKey('jwk',privateKey),publicKey:await crypto.subtle.exportKey('jwk',publicKey)};
          try{localStorage.setItem('jwb_demo_certificate_keys_v1',JSON.stringify(keys));}catch(e){}
        }
        const data=new TextEncoder().encode(JSON.stringify(record.payload));
        record.digest=certificateHex(await crypto.subtle.digest('SHA-256',data));
        record.algorithm='ECDSA P-256 / SHA-256';
        record.signature=certificateBytesToBase64(await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},privateKey,data));
        record.publicKey=await crypto.subtle.exportKey('jwk',publicKey);
        record.keyFingerprint=certificateHex(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(record.publicKey))));
      }
      return record;
    }
    async function verifyCertificateRecord(record=lastCertificateRecord,showResult=true){
      let valid=false;
      try{
        if(record?.signature&&record?.publicKey){
          const key=await crypto.subtle.importKey('jwk',record.publicKey,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);
          const bytes=new TextEncoder().encode(JSON.stringify(record.payload));
          const hash=certificateHex(await crypto.subtle.digest('SHA-256',bytes));
          valid=hash===record.digest&&await crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},key,certificateBase64ToBytes(record.signature),bytes);
        }
      }catch(e){valid=false;}
      if(showResult)showApiToast('JWB Certificate Record',valid?bi('签发记录校验通过；签名来自本地演示密钥，非受信任银行证书','Record verified using the local demo key; this is not a trusted bank certificate'):bi('签名校验未通过或当前环境不支持','Signature verification failed or is unavailable'),valid);
      return valid;
    }
    function downloadCertificateRecord(){
      if(!lastCertificateRecord)return;
      const blob=new Blob([JSON.stringify(lastCertificateRecord,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=url;a.download=lastCertificateRecord.payload.documentId+'-verification.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
    function renderCertificateToCanvas(record=lastCertificateRecord){
      const canvas=document.getElementById('certificateCanvas');
      canvas.width=2480;canvas.height=3508;
      const ctx=canvas.getContext('2d');ctx.scale(2,2);
      const W=1240,H=1754,L=86,R=W-L;
      const data=record?.payload||{documentId:'JWB-DEMO-PREVIEW',issuedAt:new Date().toISOString(),cardholder:activeApprovalState.holderName,product:(JWB_CARDS.find(c=>c.id===activeApprovalState.cardId)||JWB_CARDS[1]).name,maskedAccount:'**** **** **** '+activeApprovalState.cardNumber.slice(-4),currency:'USD',initialLimit:activeApprovalState.initialLimit,approvedLimit:activeApprovalState.currentLimit,productCap:activeApprovalState.maxCap};
      const zh=(record?.payload.language||currentLang)==='zh';
      const t=(a,b)=>zh?a:b;
      const sans='"JWB Inter","JWB Sans SC","Microsoft YaHei",sans-serif';
      const text=(value,x,y,size=20,color='#293746',weight=400,maxWidth)=>{ctx.font=`${weight} ${size}px ${sans}`;ctx.fillStyle=color;if(maxWidth==null)ctx.fillText(String(value),x,y);else ctx.fillText(String(value),x,y,maxWidth);};
      const line=(x,y,x2,y2,color='#dce1e5',width=1)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x2,y2);ctx.stroke();};
      const paragraph=(value,x,y,width,size=20,leading=32,color='#46515e')=>{
        ctx.font=`400 ${size}px ${sans}`;ctx.fillStyle=color;
        const tokens=/[\u3400-\u9fff]/.test(value)?Array.from(value):value.split(/(\s+)/);
        let row='',cy=y;
        for(const token of tokens){if(ctx.measureText(row+token).width>width&&row.trim()){ctx.fillText(row.trimEnd(),x,cy);cy+=leading;row=token.trimStart();}else row+=token;}
        if(row.trim()){ctx.fillText(row.trimEnd(),x,cy);cy+=leading;}
        return cy;
      };
      const section=(no,title,y)=>{text(no,L,y,14,'#987646',600);text(title,L+44,y,22,'#1b2c40',650);line(L,y+18,R,y+18);};
      ctx.fillStyle='#fffefa';ctx.fillRect(0,0,W,H);
      ctx.fillStyle='#20364b';ctx.fillRect(0,0,W,14);
      ctx.strokeStyle='#d4c39e';ctx.lineWidth=1;ctx.strokeRect(34,34,W-68,H-68);
      ctx.fillStyle='#20364b';ctx.beginPath();ctx.roundRect(L,77,78,78,16);ctx.fill();
      text('JWB',L+11,126,27,'#eddbb5',700);
      text('JASA WORLDWIDE BANK',L+100,111,26,'#20364b',650);
      text(t('JWB 数字信用管理中心','JWB DIGITAL CREDIT OFFICE'),L+101,143,14,'#77808b',500);
      ctx.textAlign='right';text('PRIVATE BANKING',R,109,12,'#8e754f',600);text('CREDIT ADMINISTRATION',R,134,11,'#7e8994',500);ctx.textAlign='left';
      line(L,183,R,183,'#bda579',1.5);
      ctx.textAlign='center';text(t('授信批核确认书','CREDIT APPROVAL CONFIRMATION'),W/2,248,zh?40:32,'#20364b',600,1068);text(t('CREDIT APPROVAL CONFIRMATION · DEMONSTRATION COPY','JWB DIGITAL CREDIT OFFICE · DEMONSTRATION COPY'),W/2,281,13,'#7e8994',500);ctx.textAlign='left';
      ctx.fillStyle='#f1f3f4';ctx.beginPath();ctx.roundRect(L,316,R-L,84,8);ctx.fill();
      text(t('文件编号','DOCUMENT REFERENCE'),L+20,345,12,'#7e8994',500);text(data.documentId,L+20,376,17,'#263c52',600);
      const when=new Date(data.issuedAt);const timestamp=when.toISOString().replace('T',' ').slice(0,19)+' UTC';
      ctx.textAlign='right';text(t('签发时间','DATE OF ISSUE'),R-20,345,12,'#7e8994',500);text(timestamp,R-20,376,16,'#263c52',500);ctx.textAlign='left';
      text(t('致：','To: ')+data.cardholder,L,452,23,'#20364b',600,1068);
      paragraph(t('兹确认，下列账户已在 JWB 演示系统中完成模拟授信评估。系统记录的产品、授信额度及相关说明如下。本确认书用于产品体验与方案展示。','This confirms that the account below has completed an illustrative credit assessment in the JWB demonstration system. The product and credit figures recorded by the system are set out below for product evaluation and presentation.'),L,495,R-L,20,31);
      section('01',t('授信摘要','CREDIT SUMMARY'),613);
      const rows=[
        [t('持卡人姓名','Cardholder'),data.cardholder],
        [t('授信产品','Product'),data.product],
        [t('关联演示账户','Demo account reference'),data.maskedAccount],
        [t('当前核准额度','Approved limit'),new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(data.approvedLimit)],
        [t('初始评估额度','Initial assessed limit'),'USD '+Number(data.initialLimit).toLocaleString('en-US')],
        [t('产品额度上限','Product limit cap'),'USD '+Number(data.productCap).toLocaleString('en-US')]
      ];
      rows.forEach(([label,value],i)=>{
        const y=654+i*52;
        ctx.fillStyle=i===3?'#edf3f4':i%2===0?'#f7f7f3':'#fffefa';ctx.fillRect(L,y,R-L,52);
        text(label,L+20,y+33,17,'#6c7782',450,350);
        text(value,L+396,y+34,i===3?27:19,'#20364b',i===3?650:500,650);
        line(L,y+52,R,y+52,'#e2e6e8');
      });
      section('02',t('适用说明','TERMS OF THIS RECORD'),1027);
      let cy=1072;
      const terms=zh?[
        '本文件中的额度为演示模型输出，不涉及真实授信审批、征信查询、资金划转或合同成立。',
        'JWB 品牌签名与电子印章仅用于系统演示，不代表持牌银行或真实授权人员签署。',
        '签发记录可使用随附公钥核验；该密钥为本地演示密钥，未获得受信任 CA 或银行机构认证。'
      ]:[
        'All figures are illustrative model outputs. This record does not establish a credit facility, contract, bureau inquiry or transfer of funds.',
        'The JWB brand signature and seal are demonstration artwork and do not represent a licensed bank or an authorized officer.',
        'The record can be checked with its included public key. The local demo key is not certified by a trusted CA or banking institution.'
      ];
      terms.forEach((value,i)=>{text(String(i+1).padStart(2,'0'),L,cy,13,'#987646',600);cy=paragraph(value,L+37,cy,R-L-37,18,28)+13;});
      // Signature artwork is distinct from the verifiable local demonstration record signature.
      section('03',t('签发机构与电子签署','ISSUER & ELECTRONIC EXECUTION'),1300);
      text('Jasa Worldwide Bank',L,1382,36,'#23415c',500,660);
      ctx.strokeStyle='#9b7e50';ctx.lineWidth=1.3;ctx.beginPath();ctx.moveTo(L,1398);ctx.bezierCurveTo(250,1372,420,1418,650,1387);ctx.stroke();
      text(t('JWB 数字签发服务','JWB Digital Issuance Service'),L,1432,17,'#20364b',600);
      text(t('电子签名图样 / 系统演示签署','Visual electronic signature / system demonstration'),L,1460,13,'#7e8994',400);
      const sx=1000,sy=1399,rad=88,red='#ac4545';
      ctx.save();ctx.translate(sx,sy);ctx.rotate(-.12);ctx.strokeStyle=red;ctx.lineWidth=2.8;ctx.beginPath();ctx.arc(0,0,rad,0,Math.PI*2);ctx.stroke();ctx.lineWidth=1;ctx.beginPath();ctx.arc(0,0,rad-8,0,Math.PI*2);ctx.stroke();
      function arcText(value,r,start,end){const chars=[...value];chars.forEach((char,i)=>{const angle=start+(end-start)*i/(chars.length-1);ctx.save();ctx.rotate(angle);ctx.translate(0,-r);ctx.font=`600 10px ${sans}`;ctx.fillStyle=red;ctx.textAlign='center';ctx.fillText(char,0,0);ctx.restore();});}
      arcText('JASA WORLDWIDE BANK',70,-1.2,1.2);
      ctx.textAlign='center';text('JWB',0,0,32,red,700);text(t('信用管理中心','CREDIT OFFICE'),0,23,12,red,600);text('DEMO SEAL',0,49,11,red,700);ctx.restore();ctx.textAlign='left';
      line(L,1503,R,1503,'#c8cdd2');
      text(t('签发记录摘要 SHA-256','ISSUANCE RECORD DIGEST · SHA-256'),L,1532,11,'#7e8994',600);
      text(record?.digest||t('当前环境仅支持签名图样，未生成密码学签名','Visual signature only; cryptographic signing unavailable'),L,1559,13,'#3b4f63',500,R-L);
      text(t('签署算法：','Algorithm: ')+(record?.algorithm||'Visual only')+'  |  '+t('密钥指纹：','Key ID: ')+(record?.keyFingerprint?.slice(0,24).toUpperCase()||'N/A'),L,1587,12,'#7e8994',500,R-L);
      ctx.save();ctx.translate(W/2,858);ctx.rotate(-Math.PI/6);ctx.globalAlpha=.055;ctx.textAlign='center';text('DEMONSTRATION',0,0,107,'#20364b',650);ctx.restore();ctx.textAlign='left';
      ctx.fillStyle='#edf0f0';ctx.fillRect(L,1611,R-L,56);
      text(t('系统演示文件 · 非真实银行授信证明 · 本地签名不具受信任机构认证效力','DEMONSTRATION ONLY · NOT PROOF OF BANK CREDIT · LOCAL KEY IS NOT CA-CERTIFIED'),L+14,1644,13,'#66717c',500,R-L-28);
      text('JASA WORLDWIDE BANK / JWB',L,1700,11,'#8a939c',600);ctx.textAlign='right';text('01 / 01',R,1700,11,'#8a939c',500);ctx.textAlign='left';
      return canvas;
    }
    let jwbPdfRuntimePromise=null;
    function ensureJwbPdfLibrary(){
      if(window.jspdf?.jsPDF)return Promise.resolve();
      if(jwbPdfRuntimePromise)return jwbPdfRuntimePromise;
      jwbPdfRuntimePromise=new Promise((resolve,reject)=>{
        const script=document.createElement('script');script.src=new URL('assets/jspdf.umd.min.js?v=6.0.1',document.baseURI);script.async=true;
        const fail=()=>{clearTimeout(timer);script.remove();jwbPdfRuntimePromise=null;reject(new Error(bi('PDF 组件加载失败，请稍后重试','PDF component could not load. Please retry.')));};
        const timer=setTimeout(fail,30000);
        script.onerror=fail;script.onload=()=>{if(!window.jspdf?.jsPDF)return fail();clearTimeout(timer);resolve();};
        document.head.append(script);
      });
      return jwbPdfRuntimePromise;
    }
    async function generateAndDownloadOfficialPDF(){
      if(certificateDownloadBusy)return;
      certificateDownloadBusy=true;
      const button=document.getElementById('pdfDownloadBtn'),old=button.textContent;button.disabled=true;button.setAttribute('aria-busy','true');button.textContent=bi('正在签发证书…','Preparing certificate…');
      try{
        await ensureJwbPdfLibrary();
        if(document.fonts){await Promise.all([document.fonts.load('400 20px "JWB Sans SC"'),document.fonts.load('600 20px "JWB Inter"')]);await document.fonts.ready;}
        lastCertificateRecord=await createCertificateRecord();
        callBackendAPI('POST','/api/v1/certificates/generate-pdf',()=>{
          const canvas=renderCertificateToCanvas(lastCertificateRecord);
          document.getElementById('certPreviewBox').classList.remove('hidden');
          const label=document.getElementById('certificateSignatureStatus');
          if(label)label.textContent=lastCertificateRecord.signature?bi('已生成 ECDSA / SHA-256 本地演示签名；验证记录随 PDF 元数据保存。','Local ECDSA / SHA-256 demo signature created; verification record is embedded in PDF metadata.'):bi('当前环境仅支持电子签名图样。','Visual signature only in this browser.');
          if(!window.jspdf?.jsPDF)return {status:503,message:bi('PDF 组件不可用，请查看证书预览','PDF component unavailable; use the preview')};
          const pdf=new window.jspdf.jsPDF({orientation:'portrait',unit:'mm',format:'a4',compress:true});
          pdf.setProperties({title:'JWB - Demonstration Credit Approval Confirmation',subject:lastCertificateRecord.payload.documentId,author:'JWB Digital Issuance Service (Demonstration)',creator:'JWB Local Demonstration System',keywords:'DEMO ONLY, illustrative credit, local ECDSA signature'});
          pdf.addImage(canvas.toDataURL('image/jpeg',.96),'JPEG',0,0,210,297);
          const xml=JSON.stringify(lastCertificateRecord).replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
          if(pdf.addMetadata)pdf.addMetadata('<jwb:record xmlns:jwb="urn:jwb:demo:credit-record">'+xml+'</jwb:record>');
          pdf.save(lastCertificateRecord.payload.documentId+'.pdf');
          playLuxurySound('chime');return {status:200,message:bi('授信演示证书已生成，含签名图样、印章和验证记录','Demo certificate generated with signature artwork, seal and verification record')};
        });
      }catch(e){console.error(e);showApiToast('Certificate · 500',bi('证书生成失败，请重试','Certificate could not be generated. Please retry'),false);}
      finally{certificateDownloadBusy=false;button.disabled=false;button.removeAttribute('aria-busy');button.textContent=old;}
    }

    const FX_CACHE_KEY='jwb_reference_rates_v1';
    const fxState={mode:'demo',source:'',asOf:'',fetchedAt:0,rates:null,loading:false,version:0,error:'',configuredProvider:'frankfurter'};
    let fxSessionKey='',fxRefreshTask=null,fxRefreshTimer=null,fxQuote=null,fxPollMs=3600000;
    function normalizeFxData(data,provider){
      if(provider==='er-api'){
        if(data?.result!=='success'||data.base_code!=='USD'||!Number.isFinite(data.time_last_update_unix))throw Error('schema');
        const normalized=normalizeFxData({base:'USD',timestamp:data.time_last_update_unix,rates:data.rates},'oxr');
        return {...normalized,source:'ExchangeRate-API · market reference',provider:'er-api',nextUpdate:data.time_next_update_unix*1000};
      }
      const keys=Object.keys(CURRENCY_META),rates={USD:1};
      let date,source;
      if(provider==='frankfurter-v2'){
        if(!Array.isArray(data))throw Error('schema');
        const relevant=data.filter(r=>keys.includes(String(r.quote).toUpperCase()));
        const dates=new Set();
        for(const row of relevant){if(String(row.base).toUpperCase()!=='USD'||typeof row.rate!=='number'||!Number.isFinite(row.rate)||row.rate<=0||row.rate>1e7||!/^\d{4}-\d{2}-\d{2}$/.test(row.date))throw Error('schema');rates[String(row.quote).toUpperCase()]=1/row.rate;dates.add(row.date);}
        if(dates.size!==1)throw Error('mixed-dates');
        date=[...dates][0];source='Frankfurter · official-source reference';
      }else{
        if(!data||data.base!=='USD'||!data.rates)throw Error('schema');
        for(const k of keys.filter(k=>k!=='USD')){const n=data.rates[k];if(typeof n!=='number'||!Number.isFinite(n)||n<=0||n>1e7)throw Error('schema');rates[k]=1/n;}
        if(provider==='oxr'){
          if(!Number.isFinite(data.timestamp)||data.timestamp*1000>Date.now()+3600000)throw Error('date');
          date=new Date(data.timestamp*1000).toISOString();source='Open Exchange Rates · midpoint';
        }else{date=data.date;source='Frankfurter · ECB reference';}
      }
      if(!keys.every(k=>Number.isFinite(rates[k])&&rates[k]>0))throw Error('incomplete');
      const time=Date.parse(date);if(!Number.isFinite(time)||time>Date.now()+86400000||Date.now()-time>7*86400000)throw Error('stale');
      return {rates,asOf:date,source,fetchedAt:Date.now(),provider};
    }
    function usableFxRates(){return fxState.mode!=='demo'&&fxState.rates&&Date.now()-Date.parse(fxState.asOf)<=7*86400000&&Date.now()-fxState.fetchedAt<86400000;}
    function applyFxData(data,mode='network'){
      const changed=fxState.asOf!==data.asOf||fxState.source!==data.source||JSON.stringify(fxState.rates)!==JSON.stringify(data.rates);
      Object.assign(fxState,data,{mode,error:''});if(changed)fxState.version++;
      for(const k of Object.keys(CURRENCY_META))FX_RATES_TO_USD[k]=data.rates[k];
      if(mode==='network')try{localStorage.setItem(FX_CACHE_KEY,JSON.stringify(data));}catch(e){}
    }
    async function fetchFxJSON(url,headers={}){
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
      try{const r=await fetch(url,{headers:{Accept:'application/json',...headers},signal:controller.signal,credentials:'omit',cache:'default',referrerPolicy:'no-referrer'});if(!r.ok)throw Error('HTTP '+r.status);return await r.json();}finally{clearTimeout(timer);}
    }
    function updateFxDependentViews(){
      const total=getTotalTreasuryUSD();
      const fmt=v=>'$'+v.toLocaleString(currentLang==='zh'?'zh-CN':'en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
      document.getElementById('bsTotalCashUsd').textContent=fmt(total);
      document.getElementById('bsNetWorth').textContent=fmt(total+db.jrPointsBalance/100-db.cards.reduce((sum,c)=>sum+c.statementBalance,0));
      renderTreasuryPage(total);
      animateNumericUpdates();
      localizeDocument();
    }
    async function refreshFxRates(manual=false){
      if(fxRefreshTask)return fxRefreshTask;
      if(!manual&&fxState.provider==='er-api'&&usableFxRates()&&Date.now()-fxState.fetchedAt<3600000)return;
      fxState.loading=true;renderFxStatus();
      fxRefreshTask=(async()=>{
        let data=null,subscriptionFailed=false;
        try{
          if(fxState.configuredProvider==='oxr'&&fxSessionKey){
            try{data=normalizeFxData(await fetchFxJSON('https://openexchangerates.org/api/latest.json?symbols=HKD,JPY,EUR,GBP,CNY',{Authorization:'Token '+fxSessionKey}),'oxr');}catch(e){subscriptionFailed=true;}
          }
          if(!data){
            try{data=normalizeFxData(await fetchFxJSON('https://api.frankfurter.dev/v2/rates?base=USD&quotes=HKD,JPY,EUR,GBP,CNY'),'frankfurter-v2');}
            catch(e){
              try{data=normalizeFxData(await fetchFxJSON('https://open.er-api.com/v6/latest/USD'),'er-api');}
              catch(fallbackError){data=normalizeFxData(await fetchFxJSON('https://api.frankfurter.app/latest?from=USD&to=HKD,JPY,EUR,GBP,CNY'),'frankfurter-v1');}
            }
          }
          applyFxData(data);
          if(subscriptionFailed)fxState.error=bi('订阅源未连接，当前使用公开日参考价','Subscription unavailable; using public daily reference rates');
          updateFxDependentViews();
          if(manual)showApiToast('Reference FX',bi('已获取最新可用参考价；数据日期见换汇面板','Latest available reference rates received; see the provider timestamp'),true);
        }catch(e){
          fxState.mode=usableFxRates()?'cached':'demo';
          fxState.error=bi('暂时无法连接汇率源，请检查网络后重试','Rate provider unavailable. Check your connection and retry');
          if(manual)showApiToast('Reference FX',fxState.error,false);
        }finally{fxState.loading=false;fxRefreshTask=null;renderFxStatus();previewFxSwap();}
      })();return fxRefreshTask;
    }
    function setFxProvider(){
      const provider=document.getElementById('fxProviderSelect').value;
      const key=document.getElementById('fxProviderKey').value.trim();
      if(provider==='oxr'&&!/^[a-f0-9]{32}$/i.test(key)){showApiToast('FX Settings',bi('请输入有效的 32 位 Open Exchange Rates App ID','Enter a valid 32-character Open Exchange Rates App ID'),false);return;}
      fxState.configuredProvider=provider;fxSessionKey=provider==='oxr'?key:'';
      if(provider!=='oxr')document.getElementById('fxProviderKey').value='';
      const requested=Number(document.getElementById('fxPollInterval').value);
      fxPollMs=provider==='oxr'&&[15,60,300,3600].includes(requested)?requested*1000:3600000;
      clearInterval(fxRefreshTimer);fxRefreshTimer=setInterval(()=>{if(document.visibilityState==='visible')refreshFxRates();},fxPollMs);
      if(fxRefreshTask){fxRefreshTask.then(()=>refreshFxRates(true));return;}
      refreshFxRates(true);
    }
    function renderFxStatus(){
      const available=usableFxRates();
      document.querySelectorAll('[data-fx-status]').forEach(el=>{el.dataset.state=fxState.loading?'loading':available?fxState.mode:'offline';el.textContent=fxState.loading?bi('正在连接参考汇率','Connecting to reference rates'):available?(fxState.mode==='cached'?bi('缓存参考价','Cached reference'):bi('参考汇率已连接','Reference feed connected')):bi('离线 · 仅演示估值','Offline · illustrative valuations');});
      const source=document.getElementById('fxSourceLabel');if(!source)return;
      source.textContent=fxState.source||bi('尚未获取外部报价','No external quote received');
      document.getElementById('fxDataDate').textContent=fxState.asOf||'—';
      document.getElementById('fxFetchedAt').textContent=fxState.fetchedAt?new Date(fxState.fetchedAt).toLocaleString(currentLang==='zh'?'zh-CN':'en-US'):'—';
      document.getElementById('fxFrequency').textContent=fxState.provider==='oxr'?bi('中间价 · 实际更新频率取决于订阅','Midpoint · cadence depends on your plan'):bi('日参考价 · 非逐笔实时报价','Daily reference · not a tick feed');
      document.getElementById('fxConnectionMessage').textContent=fxState.error||bi('换汇按屏幕所示参考价计算：平台加点 0，模拟手续费 0。实际成交价由执行机构决定。','Calculations use the displayed reference rate: zero platform markup and zero simulated fee. Executable rates depend on the provider.');
      const btn=document.getElementById('fxRefreshBtn');btn.disabled=fxState.loading;btn.setAttribute('aria-busy',String(fxState.loading));
      const execute=document.getElementById('fxExecuteBtn');execute.disabled=!available;execute.title=available?'':bi('连接有效参考价后可模拟兑换','Connect to valid reference rates to simulate an exchange');
      document.getElementById('fxProviderKeyWrap').hidden=document.getElementById('fxProviderSelect').value!=='oxr';
      document.getElementById('fxPollInterval').disabled=document.getElementById('fxProviderSelect').value!=='oxr';
    }
    function previewFxSwap(){
      const from=document.getElementById('fxSwapFrom').value,to=document.getElementById('fxSwapTo').value,amount=Number(document.getElementById('fxSwapAmount').value);
      document.getElementById('fxSwapAmount').step=from==='JPY'?'1':'0.01';
      const valid=usableFxRates()&&Number.isFinite(amount)&&amount>0;
      const rate=FX_RATES_TO_USD[from]/FX_RATES_TO_USD[to];
      fxQuote=valid?{from,to,amount,rate,usdRate:FX_RATES_TO_USD[from],source:fxState.source,asOf:fxState.asOf,version:fxState.version,expiresAt:Date.now()+60000}:null;
      document.getElementById('fxSwapRateDisplay').textContent=usableFxRates()?`1 ${from} = ${rate.toLocaleString('en-US',{maximumFractionDigits:8})} ${to}`:'—';
      document.getElementById('fxSwapReceiveDisplay').textContent=valid?`${roundCurrency(amount*rate,to).toLocaleString(currentLang==='zh'?'zh-CN':'en-US',{minimumFractionDigits:to==='JPY'?0:2,maximumFractionDigits:to==='JPY'?0:2})} ${to}`:'—';
      const quote=document.getElementById('fxQuoteMeta');if(quote)quote.textContent=valid?bi('报价有效期 60 秒 · 按到账币种最小单位四舍五入','Quote valid for 60 seconds · rounded to destination currency precision'):bi('获取有效参考价后显示换算结果','Connect to valid reference rates to see a conversion');
      renderFxStatus();
    }
    function executeRealFxSwap(){
      const from=document.getElementById('fxSwapFrom').value,to=document.getElementById('fxSwapTo').value,amount=Number(document.getElementById('fxSwapAmount').value),quote=fxQuote;
      callBackendAPI('POST','/api/v1/treasury/fx-swap',()=>{
        if(!usableFxRates())return {status:503,message:bi('无有效参考汇率，兑换未执行','No valid reference rate; exchange was not executed')};
        if(from===to)return {status:400,message:bi('请选择两个不同的币种','Choose two different currencies')};
        if(!quote||quote.from!==from||quote.to!==to||quote.amount!==amount||quote.version!==fxState.version||quote.expiresAt<Date.now())return {status:409,message:bi('报价已更新或过期，请核对新报价后重试','Quote changed or expired. Review the updated quote and retry')};
        if(db.treasuryWallets[from]<amount)return {status:402,message:bi('兑出账户余额不足','Insufficient source wallet balance')};
        const received=roundCurrency(amount*quote.rate,to);
        db.treasuryWallets[from]=roundCurrency(db.treasuryWallets[from]-amount,from);
        db.treasuryWallets[to]=roundCurrency(db.treasuryWallets[to]+received,to);
        recordDoubleEntry(`1010 · Sovereign Vault (${to})`,`1010 · Sovereign Vault (${from})`,amount*quote.usdRate,`FX ${from}/${to} @ ${quote.rate.toPrecision(12)} · ${quote.source} · ${quote.asOf} · Fee 0 / Markup 0`);
        db.posFeed.unshift({txHash:generateTxHash('FX-'+Date.now()),time:new Date().toLocaleTimeString(),desc:`${from} → ${to} · ${quote.source} · ${quote.asOf}`,amountStr:`-${amount} ${from} / +${received} ${to}`,jrStr:'Fee 0 · Markup 0',type:'fx'});
        playLuxurySound('chime');return {status:200,message:bi('模拟兑换成功：','Simulated exchange complete: ')+`${amount} ${from} → ${received} ${to}`};
      });
    }
    function reverseFxPair(){const from=document.getElementById('fxSwapFrom'),to=document.getElementById('fxSwapTo');const val=from.value;from.value=to.value;to.value=val;document.getElementById('fxSwapAmount').value=roundCurrency(Number(document.getElementById('fxSwapAmount').value)||0,from.value);previewFxSwap();playLuxurySound('flip');}
    function initFxFeed(){
      try{const c=JSON.parse(localStorage.getItem(FX_CACHE_KEY));if(c&&c.rates){const data={base:'USD',date:c.asOf,rates:Object.fromEntries(Object.entries(c.rates).map(([k,v])=>[k,1/v]))};const normalized=normalizeFxData(data,'frankfurter-v1');normalized.source=String(c.source).slice(0,100);normalized.provider=c.provider;normalized.fetchedAt=c.fetchedAt;if(typeof c.fetchedAt==='number'&&Date.now()-c.fetchedAt<86400000&&c.fetchedAt<=Date.now()){applyFxData(normalized,'cached');}}}catch(e){}
      updateFxDependentViews();renderFxStatus();previewFxSwap();refreshFxRates();
      fxRefreshTimer=setInterval(()=>{if(document.visibilityState==='visible')refreshFxRates();},3600000);
      window.addEventListener('online',()=>refreshFxRates());
      document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&Date.now()-fxState.fetchedAt>fxPollMs)refreshFxRates();});
      setInterval(()=>renderFxStatus(),30000);
    }

    let selectedHeroCardId='aspire';
    const decoratedCards=new WeakSet(),observedPanels=new WeakSet(),numericSnapshots=new Map();
    const motionReduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
    function decorateCards(){
      document.querySelectorAll('.fan-card-wrapper .iso-card,#cardsGrid .iso-card,#vaultActiveCardPreview .iso-card').forEach(el=>{
        if(decoratedCards.has(el))return;decoratedCards.add(el);
        el.classList.add('tiltable-card');
        const art=document.createElement('div');art.className='card-art';art.setAttribute('aria-hidden','true');art.innerHTML='<span class="card-orbit"></span><span class="card-monogram">JWB</span>';el.prepend(art);
      });
    }
    function focusHeroCard(cardId){
      const card=JWB_CARDS.find(c=>c.id===cardId);if(!card)return;
      selectedHeroCardId=cardId;lastFocusedFanCardId=cardId;
      document.querySelectorAll('.fan-card-wrapper').forEach(el=>el.classList.toggle('is-focused',el.id==='fanCard-'+cardId));
      document.querySelectorAll('[data-hero-card]').forEach(el=>{const selected=el.dataset.heroCard===cardId;el.classList.toggle('is-selected',selected);el.setAttribute('aria-pressed',String(selected));});
      updateFanHint(cardId);
      if(!motionReduced())document.getElementById('fanHoverHint').animate([{opacity:.35,transform:'translateY(5px)'},{opacity:1,transform:'none'}],{duration:250,easing:'ease-out'});
      localizeDocument();
    }
    function renderHeroFanStage(){
      const stage=document.getElementById('heroFanStage'),offsets=[-2.5,-1.5,-.5,.5,1.5,2.5],ranks=[10,20,30,35,25,15];
      stage.innerHTML=JWB_CARDS.map((card,i)=>`<div class="fan-card-wrapper" id="fanCard-${card.id}" role="button" tabindex="0" aria-label="${escapeHTML(card.name)}" style="--offset:${offsets[i]};--abs-offset:${Math.abs(offsets[i])};--intro-delay:${i*65}ms;z-index:${ranks[i]}" onpointerenter="if(event.pointerType==='mouse') focusHeroCard('${card.id}')" onfocus="if(this.matches(':focus-visible')) focusHeroCard('${card.id}')" onclick="handleFanCardClick('${card.id}')">
        <div class="iso-card ${card.finishClass} flex flex-col justify-between">
          <div class="relative z-10 flex items-center justify-between"><span class="card-brand">JWB</span><span class="card-tier">${card.id==='everyday'?'PREFERRED':card.id==='centurion'?'RESERVE':card.id.toUpperCase()}</span></div>
          <div class="card-middle"><div class="emv-chip"></div><svg width="18" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" style="color:#ffffff77" stroke-width="1.2" aria-hidden="true"><path d="M6 7a5 5 0 0 1 0 6M10 4a9 9 0 0 1 0 12M14 1a13 13 0 0 1 0 18"/></svg></div>
          <div class="card-bottom"><div><div class="card-name">${card.name.replace('JWB ','')}</div><div class="card-number">${card.bin} · •••• ••••</div></div><div class="card-network">JASA<br>WORLDWIDE</div></div>
        </div></div>`).join('');
      document.getElementById('heroCardPicker').innerHTML=JWB_CARDS.map(card=>`<button data-hero-card="${card.id}" class="${card.id===selectedHeroCardId?'is-selected':''}" onclick="focusHeroCard('${card.id}')" aria-pressed="${card.id===selectedHeroCardId}"><span class="picker-dot" style="--dot:${card.accentHex||'#d4bb8b'}"></span>${card.id==='everyday'?'Everyday':card.id==='centurion'?'Centurion':card.id.charAt(0).toUpperCase()+card.id.slice(1)}</button>`).join('');
      decorateCards();
      requestAnimationFrame(()=>requestAnimationFrame(()=>stage.classList.add('is-unfolded')));
      updateFanHint(selectedHeroCardId);
    }
    function handleFanCardClick(cardId){
      if(selectedHeroCardId===cardId&&lastFocusedFanCardId===cardId&&window.innerWidth>767){openApprovalModal(cardId);return;}
      const repeated=lastFocusedFanCardId===cardId;
      focusHeroCard(cardId);playLuxurySound('tick');
      if(window.innerWidth<=767&&repeated)openApprovalModal(cardId);
    }
    function openFeaturedHeroCard(){openApprovalModal(selectedHeroCardId);}
    function animateViewEntry(target){
      if(motionReduced())return;
      target.animate([{opacity:.2,transform:'translateY(12px)',filter:'blur(2px)'},{opacity:1,transform:'none',filter:'blur(0px)'}],{duration:420,easing:'cubic-bezier(.2,.8,.2,1)'});
      const bar=document.getElementById('pageTransitionLine');bar.animate([{opacity:0,transform:'scaleX(.05)'},{opacity:1,transform:'scaleX(.7)',offset:.55},{opacity:0,transform:'scaleX(1)'}],{duration:500,easing:'ease-out'});
    }
    function animateNumericUpdates(){
      for(const id of ['bsTotalCashUsd','bsTotalJrUsd','bsTotalStatement','bsNetWorth','vaultTotalLimit','vaultTotalJR','vaultStatementBal','calcNetValue']){
        const el=document.getElementById(id);if(!el)continue;const value=el.textContent,previous=numericSnapshots.get(id);
        if(previous&&previous!==value&&!motionReduced()&&el.getBoundingClientRect().width)el.animate([{opacity:.4,transform:'translateY(5px)'},{opacity:1,transform:'none'}],{duration:350,easing:'ease-out'});
        numericSnapshots.set(id,value);
      }
    }
    function initReleaseMotion(){
      decorateCards();
      const observer=new IntersectionObserver(entries=>entries.forEach(({target,isIntersecting})=>{if(isIntersecting){observer.unobserve(target);if(!motionReduced())target.animate([{opacity:.25,transform:'translateY(16px)'},{opacity:1,transform:'none'}],{duration:550,easing:'cubic-bezier(.16,1,.3,1)'});}}),{threshold:.08});
      const scan=()=>document.querySelectorAll('.glass-panel').forEach(el=>{if(!observedPanels.has(el)){observedPanels.add(el);observer.observe(el);}});
      scan();new MutationObserver(()=>{decorateCards();scan();}).observe(document.body,{childList:true,subtree:true});
      let pendingPointer=null,pointerFrame=0;
      document.addEventListener('pointermove',e=>{if(e.pointerType!=='mouse'||motionReduced())return;pendingPointer=e;if(pointerFrame)return;pointerFrame=requestAnimationFrame(()=>{pointerFrame=0;const ev=pendingPointer,card=ev.target.closest?.('.tiltable-card');if(!card)return;const r=card.getBoundingClientRect();card.style.setProperty('--tilt-x',((.5-(ev.clientY-r.top)/r.height)*7).toFixed(2)+'deg');card.style.setProperty('--tilt-y',(((ev.clientX-r.left)/r.width-.5)*9).toFixed(2)+'deg');});});
      document.addEventListener('pointerout',e=>{const card=e.target.closest?.('.tiltable-card');if(card&&!card.contains(e.relatedTarget)){card.style.setProperty('--tilt-x','0deg');card.style.setProperty('--tilt-y','0deg');}});
      document.addEventListener('pointerdown',e=>{if(motionReduced())return;const btn=e.target.closest('main button');if(!btn||btn.disabled)return;const rect=btn.getBoundingClientRect(),r=document.createElement('span'),size=Math.max(rect.width,rect.height)*2;btn.style.position='relative';btn.style.overflow='hidden';r.className='ui-ripple';r.setAttribute('aria-hidden','true');Object.assign(r.style,{width:size+'px',height:size+'px',left:e.clientX-rect.left-size/2+'px',top:e.clientY-rect.top-size/2+'px'});btn.append(r);setTimeout(()=>r.remove(),650);});
      // Horizontal gestures move focus; ordinary vertical scrolling stays native.
      let start=null;
      const stage=document.getElementById('heroFanStage');
      stage.addEventListener('touchstart',e=>{if(e.touches.length===1)start={x:e.touches[0].clientX,y:e.touches[0].clientY};},{passive:true});
      stage.addEventListener('touchend',e=>{if(!start)return;const dx=e.changedTouches[0].clientX-start.x,dy=e.changedTouches[0].clientY-start.y;start=null;if(window.innerWidth>767&&Math.abs(dx)>45&&Math.abs(dx)>Math.abs(dy)*1.5){const index=JWB_CARDS.findIndex(c=>c.id===selectedHeroCardId);focusHeroCard(JWB_CARDS[(index+(dx<0?1:-1)+6)%6].id);}} ,{passive:true});
    }

const UI_TRANSLATIONS = {"总览与净值": "Overview", "私行金库与闪兑": "Treasury & FX", "旗舰卡矩阵 (6)": "Cards (6)", "卡包与 POS 收银台": "Wallet & POS", "风控秒批与制卡": "Card Studio", "后端 API 与总账": "Activity & Ledger", "🔊 音效": "🔊 Sound", "🔇 静音": "🔇 Muted", "JWB 实时个人资产负债总览 (LIVE BALANCE SHEET)": "Live Personal Balance Sheet", "多币种金库总折合 (USD)": "Total Treasury Value (USD)", "4.85% APY 计息中 ➔": "4.85% illustrative APY ➔", "JR 积分池现金价值 (1 JR=1¢)": "Rewards Value (1 JR = 1¢)", "信用卡待还账单 / 可用授信": "Card Balances / Credit Limits", "JWB 净流动资产 (NET WORTH)": "Net Liquid Assets", "查看复式总账分录 ➔": "View ledger entries ➔", "1 JR = $0.01 USD 恒定保底兑现": "1 JR = $0.01 USD in this simulation", "六种风格，一种从容。": "Private banking, thoughtfully simulated.", "从日常到远方，探索六款 JWB 卡片。多币种金库、透明换汇与卡片管理，尽在一处。": "Explore multi-currency accounts, credit decisions, simulated POS payments, rewards and card management in one local workspace.", "进入 POS 收银台与卡包 ➔": "Open Wallet & POS ➔", "多币种金库与闪兑": "Treasury & Currency Exchange", "✦ 重播飞入动画": "✦ Replay card animation", "悬停聚焦卡片 · 点击探索详情 · 手机可左右滑动切换": "Hover to explore welcome offers. Tap a card twice on mobile to open the studio.", "JWB 极度友好申卡与持卡准则": "Explore the simulated card program", "01 · 全系无损升降级（Lossless Product Change）": "01 · Change card products", "保留原 8888 卡号与完整信报历史，随时自由切换卡种": "Keep your simulated card number and account history when changing products.", "02 · 无家族开卡礼限制（No Family Rule）": "02 · Independent welcome offers", "不论申卡先后顺序，每张卡片均可独立拿满限时史高开卡礼": "Each newly issued card has its own welcome offer progress.", "03 · 全球 0% 货币转换费与 61 天 3 倍提额（0% FTF & 61-Day 3X CLI）": "03 · No FX fee & simulated credit increases", "全系免除跨境手续费，良好用卡满 61 天支持最高 3 倍提额": "Explore fee-free currency conversion and a simulated credit increase.", "JWB 全系 6 张信用卡共享统一底层授信账户架构。您可随时在「卡包与 POS」页面一键无损降级至 $0 年费的 Everyday Preferred 永久养信报，或无损升级至更高阶旗舰卡，原 16 位 8888 卡号、CVV 与信报账龄 100% 完整继承。": "Switch among six simulated products in Wallet & POS while keeping your card credentials. Existing rewards progress and used benefit allowances are preserved; switching cannot mint another welcome bonus.", "JWB 严禁任何因“曾持有高阶卡而取消低阶卡开卡奖励”的限制条款。即使您率先获批 JWB Centurion Reserve 或 JWB Platinum，后续申请 Gold、Aero、Aspire 或 Everyday Preferred 时，依然 100% 独立享有各卡全额限时史高 JR 开卡礼。": "Each newly issued simulated account can earn one welcome bonus after meeting its spending threshold. Changing products does not create a new welcome bonus.", "包含 $0 年费的 Everyday Preferred 在内，JWB 全系卡片通过 Jasa Network 进行全球零汇损本币直连清算，永久免除货币转换费（0% FTF）。同时，持卡满 61 天后即可申请最高 3 倍信用额度提升（Soft Pull），额度上限严格对应所选卡种的 Max Credit Limit Cap。": "All products use fixed illustrative exchange rates with no simulated conversion fee. The studio previews a 61-day credit increase up to the selected product cap; this does not query a credit bureau.", "多币种金库与换汇": "Multi-currency Treasury & FX", "统一管理六种货币，连接外部参考汇率，按同一报价计算兑换。平台不额外加点，模拟兑换不收手续费。": "Manage six simulated balances, add demo funds, accrue illustrative interest and exchange currencies using fixed sample rates. Deposits inform the studio credit preview.", "+ 电汇入金 $10,000 USD": "+ Add $10,000 demo USD", "✦ 结算当月 4.85% APY 利息": "✦ Accrue this month's demo interest", "参考价透明换汇": "Currency Exchange · Fixed Illustrative Rates", "兑出账户 (Debit From)": "From account", "兑入账户 (Credit To)": "To account", "兑出金额 (Amount)": "Amount to exchange", "当前参考换算率：": "Illustrative exchange rate:", "模拟兑换到账：": "Estimated amount received:", "按参考价模拟兑换": "Exchange currencies", "私行资产质押与信用卡授信联动": "Treasury-backed Credit Preview", "系统实时读取您在 JWB 的多币种总存款折合美元价值，并按 80% 折算率自动为新卡秒批与存量卡提额提供底层授信支撑。": "The studio uses your total simulated treasury value and an illustrative 80% collateral factor to preview credit limits.", "当前私行金库总折合资产:": "Total treasury value:", "80% 质押可调配授信池:": "Illustrative collateral pool (80%):", "前往秒批中心使用质押授信加成 ➔": "Open credit preview in Studio ➔", "探索 JWB 卡片": "Explore All Six Cards", "每张卡片均处于限时史高开卡礼阶段，配备专属 8888-0X88 卡段与明确的最高信用额度上限（Max Credit Limit Cap）。": "Compare six simulated products, each with an illustrative welcome offer, card prefix and credit limit cap.", "展开全部详细权益 ▾": "Expand all benefits ▾", "收起全部详细权益 ▴": "Collapse all benefits ▴", "全部旗舰卡 (6)": "All cards (6)", "零年费与餐饮生活 (Everyday / Gold)": "Everyday / Gold", "航司与奢华酒店联名 (Aero / Aspire)": "Aero / Aspire", "差旅与私行巅峰 (Platinum / Centurion)": "Platinum / Centurion", "「1 JR = 1 Cent」交互式净收益引擎": "First-Year Value Calculator · 1 JR = 1¢", "全球餐饮、外卖与生鲜超市 (月均)": "Dining & groceries · monthly", "全球机票、奢华酒店与度假村 (月均)": "Flights & hotels · monthly", "日常综合、数字订阅与百货 (月均)": "Everyday & subscriptions · monthly", "限时史高开卡礼": "Welcome offer", "首年日常消费积分": "First-year spending rewards", "首年总积分价值": "First-year rewards value", "年度固定报销总额": "Estimated annual credits used", "年费成本": "Annual fee", "首年净正收益 (NET VALUE)": "Estimated first-year net value", "立即申请此卡 ➔": "Preview this card ➔", "卡包与支付中心": "Wallet, Card Controls & POS", "支持锁卡/解冻、轮换 5 位 CVV、无损升降级、跨卡调额、使用 USD 金库或 JR 积分还款，以及自定义商户金额外币 POS 刷卡清算。": "Freeze cards, rotate demo security codes, change products, move credit limits, repay with USD or JR and simulate purchases across currencies.", "+ 申请新卡入库": "+ Create a demo card", "持有卡片 / 总可用授信": "Cards / Total credit limits", "Jasa Rewards 积分池": "Jasa Rewards Balance", "所选卡片待还账单 / 年度报销池": "Selected Balance / Credit Allowance", "账单实时还款闭环 (REPAYMENT)": "Repay Selected Card", "1:1 积分销账": "Pay with JR rewards", "USD 金库还款": "Pay from USD wallet", "选择卡包中的卡片": "Select a Card", "❄️ 冻结此卡 (Freeze)": "❄️ Freeze card", "🔥 解冻此卡 (Unfreeze)": "🔥 Unfreeze card", "↻ 轮换 5 位动态 CVV": "↻ Rotate demo security code", "01 · 无损升降级 (保留原 8888 卡号)": "01 · Change Product · Keep Card Number", "无损切换": "Change product", "02 · 跨卡授信额度调配": "02 · Move Credit Between Cards", "划拨额度": "Move credit", "✦ 限时史高开卡礼进度追踪": "✦ Welcome Offer Progress", "JASA NETWORK VIRTUAL POS TERMINAL (自定义收单终端)": "JASA NETWORK · SIMULATED POS TERMINAL", "商户名称 (Merchant)": "Merchant name", "MCC 类别": "Merchant category", "5812 · 餐饮/超市": "5812 · Dining / groceries", "3000 · 全球航司": "3000 · Airlines", "7011 · 酒店度假村": "7011 · Hotels / resorts", "4899 · 流媒体/通勤": "4899 · Everyday / subscriptions", "币种": "Currency", "金额": "Amount", "🍽️ 餐饮 $120": "🍽️ Dining $120", "✈️ 航司 $1,200": "✈️ Flights $1,200", "🏨 东京安缦 ¥120,000": "🏨 Aman Tokyo ¥120,000", "🎬 订阅 $45": "🎬 Subscription $45", "✦ 刷卡授权清算 (Authorize)": "✦ Authorize Demo Purchase", "JASA NETWORK 实时授权与自动报销流水 (含 SHA-256 签名)": "JASA NETWORK · PURCHASES & CREDITS · LOCAL REFERENCE IDS", "授信与卡片工作室": "Credit Preview & 3D Card Studio", "实时结合您的年收入、信报账龄与私行金库 80% 质押加成计算授信额度，一键入库至您的数字卡包并导出 A4 官方证书。": "Preview an illustrative credit limit using income, account age and simulated deposits. Save a demo card and export a sample A4 certificate.", "前往我的卡包与 POS ➔": "Open My Wallet & POS ➔", "申请卡种 (Card Tier)": "Card product", "持卡人激光镌刻姓名 (Cardholder Name)": "Cardholder name", "年收入 ($)": "Annual income ($)", "信报 (月)": "Account age (months)", "现有额度 ($)": "Existing credit ($)", "切换全8典藏靓号 (8888-8888-8888-8888)": "Use collectible demo number (not Luhn valid)", "《JWB 智能风控授信评估报告》": "Illustrative Credit Assessment", "内部 JWB 信用评分": "Demo assessment score", "最高额度上限 (Max Cap)": "Product credit cap", "当前获批额度 (含金库质押)": "Illustrative approved limit", "距离上限剩余空间": "Remaining headroom", "点击卡面 180° 翻转查看背面 8888 卡号与 5 位混合 CVV": "Tap to flip the card and view its demo credentials.", "↻ 翻转卡面": "↻ Flip card", "换号": "Regenerate", "复制卡号与 CVV": "Copy demo credentials", "✦ 签发并存入卡包": "✦ Save Demo Card to Wallet", "⚡ 61天 3倍提额": "⚡ Preview 61-day 3× increase", "⬇ 下载 PDF 证书": "⬇ Download Sample PDF", "收起预览 ✕": "Hide preview ✕", "账户活动与数据管理": "Local Activity, Ledger & Backups", "实时审计所有前端触发的 REST API 事务请求、查看借贷必相等的会计分录（DR/CR），或导出完整的 `.json` 加密账本以便跨设备长期使用。": "Review local operation logs and paired ledger entries. Export a plain JSON backup to transfer your demo state between devices.", "⬇ 导出完整银行账本 (.json)": "⬇ Export JSON Backup", "⬆ 导入恢复账本": "⬆ Restore JSON Backup", "初始化数据库": "Reset Demo Data", "DOUBLE-ENTRY GENERAL LEDGER (复式记账总账)": "DOUBLE-ENTRY GENERAL LEDGER", "总览": "Home", "金库": "Treasury", "旗舰卡": "Cards", "卡包POS": "Wallet", "秒批": "Studio", "后端": "Activity", "美元": "US dollar", "港币": "HK dollar", "日元": "Japanese yen", "欧元": "Euro", "英镑": "Pound sterling", "人民币": "Chinese yuan", "云端模拟体验 · 资金、卡片与审批均为模拟；汇率接入外部参考数据，不连接真实银行或支付网络。": "Cloud simulation · Funds, cards and credit decisions are simulated. FX uses external reference data. No real banking or payment network connection.", "JASA NETWORK 实时授权与自动报销流水 (含 本地流水编号)": "JASA NETWORK · PURCHASES & CREDITS · LOCAL REFERENCE IDS", "实时审计所有前端触发的 REST API 事务请求、查看借贷必相等的会计分录（DR/CR），或导出完整的 `.json` 明文 JSON 账本以便跨设备长期使用。": "Review local operation logs and paired ledger entries. Export a plain JSON backup to transfer your demo state between devices.", "✓ 已在卡包": "✓ In wallet", "展开完整权益与回馈细则": "Explore rewards & benefits", "日常积分回馈：": "Spending rewards: ", "立即申请 / 秒批授信": "Open Card Studio", "可随时销账": "available to redeem", "总授信": "Total credit", "本卡年度剩余自动报销池:": "Annual credits remaining: ", "本卡剩余自动报销池:": "Credits remaining: ", "已冻结": "Frozen", "史高已拿": "Bonus earned", "可用": "Available", "账单": "Balance", "总额": "Limit", "限时史高开卡礼进度": "Welcome offer progress", "已解锁": "Unlocked", "借 DR": "DR", "贷 CR": "CR", "拒付": "Declined", "当前处于冻结状态，请先解冻卡片": "is frozen. Unfreeze before authorizing a purchase", "可用授信额度不足": "Insufficient available credit", "当前可用": "Available", "自动报销抵扣：": "Automatic statement credit: ", "剩余额度池": "Remaining allowance", "限时史高开卡礼达标入账": "Welcome bonus earned", "成功解锁": "Unlocked", "并": "and", "授权通过": "Authorized", "积分直接抵扣账单": "Rewards statement redemption", "USD 主权支票账户自动全额还款": "Full repayment from USD wallet", "当前卡片账单为 $0.00，无需还款": "The selected card has no balance to repay", "JR 积分池余额为 0，无法抵扣账单": "No JR rewards available for redemption", "成功使用": "Redeemed", "抵扣": "towards", "USD 主权账户余额不足": "Insufficient USD wallet balance", "已从 USD 主权金库全额偿还信用卡账单": "Fully repaid from the USD wallet: ", "卡片": "Card", "已安全冻结，暂停一切 POS 授权": "frozen; all purchases are blocked", "已解冻并恢复全球 0% FTF 清算": "unfrozen; purchases are enabled", "5 位混合安全码已动态轮换:": "Demo security code rotated: ", "请选择两个不同的币种进行零点差闪兑": "Choose two different currencies", "账户余额不足": "wallet balance is insufficient", "请选择两张不同的卡片进行额度调配": "Choose two different cards", "卡包需至少 2 张卡片方可调配额度": "At least two cards are required", "调出卡片额度必须覆盖欠款且至少保留 $2,000": "The source limit must cover its balance and remain at least $2,000", "超出": "Exceeds", "最高额度上限": "product credit cap", "成功跨卡无损调拨": "Credit moved: ", "授信额度": "credit limit", "无损升降级完成": "Product changed", "保留原卡号": "Card number preserved", "已无损切换为": "Product changed to", "原 8888 卡号与 CVV 100% 保留": "Original credentials preserved", "成功签发": "Issued", "并存入数字卡包": "and saved to wallet", "授信": "Credit", "61天 3X 提额批核：额度由": "Simulated 61-day 3× increase: ", "提升至": "to", "61天 3X 提额批核通过: 最新授信额度": "Credit increase preview: ", "核心银行数据库已恢复至初始状态": "Demo data has been reset", "已导出完整 JWB 银行明文 JSON 账本备份 (.json)": "Plain JSON backup exported", "成功电汇入金": "Demo funds added: ", "4.85% APY 月度结息入账": "4.85% illustrative APY interest credited: ", "零汇损闪兑成功:": "Currency exchange complete: ", "餐饮报销": "Dining credit", "每月餐饮": "Monthly dining", "餐饮": "Dining", "酒店": "Hotel", "航司": "Airline", "通勤": "Transit", "报销": "credit", "史高开卡礼达标入账": "welcome bonus credited", "成功": "Success", "✓ 已复制": "✓ Copied", "模拟入金币种": "Demo funding currency", "模拟入金金额": "Demo funding amount", "添加模拟资金": "Add demo funds", "搜索交易": "Search transactions", "搜索商户、流水编号或金额": "Search merchant, reference or amount", "交易类型": "Transaction type", "全部交易": "All transactions", "消费": "Purchases", "报销与还款": "Credits & repayments", "奖励与卡片变更": "Bonuses & card changes", "导出交易 CSV": "Export CSV", "没有匹配的交易": "No matching transactions", "估算假设：消费均匀分布，在该卡规定期限内达标才计入开卡奖励；按可用消费估算报销，不保证实际收益。": "Assumptions: spending is spread evenly. Welcome points count only when the selected card’s offer period meets the threshold. Credits are estimated from eligible spend; actual value may vary."};
for(const card of JWB_CARDS){for(const key of ["sub","badge","feeText","welcome","earn"]){if(card[key+"_zh"])UI_TRANSLATIONS[card[key+"_zh"]]=card[key+"_en"];}for(let i=0;i<card.perks_zh.length;i++)UI_TRANSLATIONS[card.perks_zh[i]]=card.perks_en[i];if(card.autoCreditRule)UI_TRANSLATIONS[card.autoCreditRule.label_zh]=card.autoCreditRule.label_en;}
Object.assign(UI_TRANSLATIONS,{'史高开卡礼':'welcome bonus','本月已结息，请勿重复操作':'Interest has already been accrued this month','加密':'encrypted'});
Object.assign(UI_TRANSLATIONS,{'验证签发记录':'Verify record','下载验证记录':'Download record'});
Object.assign(UI_TRANSLATIONS,{'卡包与支付中心':'Wallet & payments','授信与卡片工作室':'Credit & card studio','多币种金库与换汇':'Treasury & exchange','账户活动与数据管理':'Activity & data','探索 JWB 卡片':'Explore JWB cards'});
Object.assign(UI_TRANSLATIONS,{"六种风格，一种从容。": "Six expressions. One clear perspective.", "从日常到远方，探索六款 JWB 卡片。多币种金库、透明换汇与卡片管理，尽在一处。": "From everyday moments to distant horizons. Explore six JWB cards, multi-currency accounts and transparent reference-rate exchange.", "探索所选卡片 ➔": "Explore selected card ➔", "悬停聚焦卡片 · 点击探索详情 · 手机可左右滑动切换": "Hover to focus · Click to explore · Swipe to switch on mobile", "参考汇率与透明换汇": "Reference rates. Transparent conversion.", "↻ 刷新参考价": "↻ Refresh rates", "数据来源": "Provider", "数据时间": "Rate timestamp", "最近获取": "Last fetched", "汇率来源设置": "Rate source settings", "数据服务": "Data service", "公开日参考价 · 自动备用源": "Frankfurter · free daily reference", "Open Exchange Rates · 订阅中间价": "Open Exchange Rates · subscription midpoint", "仅在当前页面内存中使用": "Used only in this page’s memory", "应用并获取": "Apply & fetch", "订阅密钥仅保留在当前页面内存，不写入文件或账本备份。公开参考源约每小时检查；订阅源可选择检查间隔，实际数据频率及调用额度以服务商方案为准。": "Your key stays in this page’s memory and is excluded from files and ledger backups. Public rates and subscriptions are checked about hourly. Publication frequency depends on the provider.", "Frankfurter 数据说明 ↗": "Frankfurter documentation ↗", "Open Exchange Rates 数据方案 ↗": "Open Exchange Rates plans ↗", "参考价透明换汇": "Exchange at the reference midpoint", "当前参考换算率：": "Reference conversion rate:", "模拟兑换到账：": "Simulated amount received:", "按参考价模拟兑换": "Simulate reference-rate exchange", "平台加点 0%": "Platform markup 0%", "模拟手续费 0": "Simulated fee 0", "⇄ 互换币种": "⇄ Reverse currencies", "统一管理六种货币，连接外部参考汇率，按同一报价计算兑换。平台不额外加点，模拟兑换不收手续费。": "Manage six currencies with externally sourced reference rates and consistent conversion quotes. No added platform markup or simulated exchange fee.", "换汇": "FX exchange"});
Object.assign(UI_TRANSLATIONS,{"操作失败，变更已撤销": "Operation failed; changes were rolled back", "浏览器存储不可用，请导出备份以保留数据": "Browser storage unavailable. Export a backup to keep your data", "入金币种或金额无效": "Invalid deposit currency or amount", "本月已结息，请勿重复操作": "Interest has already been accrued this month", "不支持的还款方式": "Unsupported repayment method", "文件不能超过 5 MB": "Backup must be under 5 MB", "导入将覆盖当前演示数据，是否继续？": "Restore will replace the current demo data. Continue?", "账本恢复成功": "Backup restored", "备份校验失败，现有数据未变：": "Invalid backup; current data preserved: ", "读取失败，请重试": "Could not read the backup", "重置将清除当前演示数据，建议先导出备份。是否继续？": "Reset clears all demo data. Export a backup first if needed. Continue?", "请选择不同的目标卡种": "Choose a different product", "请先还款至目标卡种额度上限以内": "Repay below the target product cap first", "此卡号已签发，请换号后重试": "This number is already issued. Regenerate to create another card", "本次提额预览已完成": "This credit increase has already been previewed", "已生成本地演示令牌；不支持绑定真实 Apple Wallet": "Local demo token created; this does not provision Apple Wallet", "复制失败，请手动选取卡片信息": "Copy failed. Please select the credentials manually", "签发记录校验通过；签名来自本地演示密钥，非受信任银行证书": "Record verified using the local demo key; this is not a trusted bank certificate", "签名校验未通过或当前环境不支持": "Signature verification failed or is unavailable", "正在签发证书…": "Preparing certificate…", "已生成 ECDSA / SHA-256 本地演示签名；验证记录随 PDF 元数据保存。": "Local ECDSA / SHA-256 demo signature created; verification record is embedded in PDF metadata.", "当前环境仅支持电子签名图样。": "Visual signature only in this browser.", "PDF 组件不可用，请查看证书预览": "PDF component unavailable; use the preview", "授信演示证书已生成，含签名图样、印章和验证记录": "Demo certificate generated with signature artwork, seal and verification record", "证书生成失败，请重试": "Certificate could not be generated. Please retry", "订阅源未连接，当前使用公开日参考价": "Subscription unavailable; using public daily reference rates", "已获取最新可用参考价；数据日期见换汇面板": "Latest available reference rates received; see the provider timestamp", "暂时无法连接汇率源，请检查网络后重试": "Rate provider unavailable. Check your connection and retry", "请输入有效的 32 位 Open Exchange Rates App ID": "Enter a valid 32-character Open Exchange Rates App ID", "正在连接参考汇率": "Connecting to reference rates", "缓存参考价": "Cached reference", "参考汇率已连接": "Reference feed connected", "离线 · 仅演示估值": "Offline · illustrative valuations", "尚未获取外部报价": "No external quote received", "中间价 · 实际更新频率取决于订阅": "Midpoint · cadence depends on your plan", "日参考价 · 非逐笔实时报价": "Daily reference · not a tick feed", "换汇按屏幕所示参考价计算：平台加点 0，模拟手续费 0。实际成交价由执行机构决定。": "Calculations use the displayed reference rate: zero platform markup and zero simulated fee. Executable rates depend on the provider.", "连接有效参考价后可模拟兑换": "Connect to valid reference rates to simulate an exchange", "报价有效期 60 秒 · 按到账币种最小单位四舍五入": "Quote valid for 60 seconds · rounded to destination currency precision", "获取有效参考价后显示换算结果": "Connect to valid reference rates to see a conversion", "无有效参考汇率，兑换未执行": "No valid reference rate; exchange was not executed", "请选择两个不同的币种": "Choose two different currencies", "报价已更新或过期，请核对新报价后重试": "Quote changed or expired. Review the updated quote and retry", "兑出账户余额不足": "Insufficient source wallet balance", "模拟兑换成功：": "Simulated exchange complete: ", "数据结构或数值不合法": "Invalid data structure or numeric value", "请先连接参考汇率后再模拟外币消费": "Connect to reference rates before simulating a foreign-currency purchase", "请输入正确精度的正数金额": "Enter a positive amount with valid currency precision", "旧数据校验未通过，已保留恢复副本并加载演示初始数据": "Saved data was invalid. A recovery copy was retained and demo defaults were loaded", "· 卡段": "· BIN", "· 上限": "· Cap", "· 史高": "· Welcome offer", "公开日参考价 · 自动备用源": "Public daily reference · automatic backup", "参考价透明换汇": "Exchange at the reference rate"});
Object.assign(UI_TRANSLATIONS,{"订阅刷新间隔": "Subscription polling interval", "60 分钟 · 默认": "60 minutes · default", "5 分钟": "5 minutes", "60 秒": "60 seconds", "15 秒 · 需对应订阅": "15 seconds · matching plan required", "订阅密钥仅保留在当前页面内存，不写入文件或账本备份。公开参考源约每小时检查；订阅源可选择检查间隔，实际数据频率及调用额度以服务商方案为准。": "Your key stays in this page’s memory and is excluded from files and ledger backups. Public rates are checked about hourly; subscription polling is configurable. Data cadence and request limits depend on your provider plan."});
const SORTED_TRANSLATIONS = Object.entries(UI_TRANSLATIONS).sort((a,b)=>b[0].length-a[0].length);
    function bi(zh,en){return currentLang==='en'?en:zh;}
    function escapeHTML(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
    function validMoney(n){return typeof n==='number'&&Number.isFinite(n)&&n>0&&n<=1e10;}
    function roundCurrency(n,c){return Number(n.toFixed(c==='JPY'?0:2));}
    function validateDatabase(raw){
      const fail=()=>{throw Error(bi('数据结构或数值不合法','Invalid data structure or numeric value'));};
      const obj=x=>x&&typeof x==='object'&&!Array.isArray(x);
      const money=n=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<=1e12;
      const str=x=>typeof x==='string'&&x.length<=2000;
      if(!obj(raw)||!obj(raw.treasuryWallets)||!Array.isArray(raw.cards)||!raw.cards.length||raw.cards.length>200||!Number.isSafeInteger(raw.jrPointsBalance)||raw.jrPointsBalance<0)fail();
      const d=createInitialDatabase();
      d.jrPointsBalance=raw.jrPointsBalance;
      for(const key of Object.keys(raw.treasuryWallets))if(!Object.hasOwn(CURRENCY_META,key))fail();
      for(const key of Object.keys(CURRENCY_META)){const val=raw.treasuryWallets[key]??0;if(!money(val))fail();d.treasuryWallets[key]=val;}
      const seen=new Set();
      d.cards=raw.cards.map(c=>{
        if(!obj(c)||!JWB_CARDS.some(m=>m.id===c.cardId)||!str(c.uid)||!str(c.holderName)||!/^[0-9]{4}(-[0-9]{4}){3}$/.test(c.cardNumber)||!/^\d{2}\/\d{2}$/.test(c.expDate)||!/^\w{3,5}$/.test(c.cvv)||!['ACTIVE','FROZEN'].includes(c.status)||!money(c.creditLimit)||!money(c.statementBalance??0)||c.creditLimit<(c.statementBalance??0)||!money(c.spendProgress??0)||!money(c.remainingCreditPool??0)||seen.has(c.cardNumber))fail();
        seen.add(c.cardNumber);
        const m=JWB_CARDS.find(m=>m.id===c.cardId);
        if(c.creditLimit>m.maxCap||typeof c.welcomeUnlocked!=='boolean')fail();
        if(c.welcomeProductId&&!JWB_CARDS.some(m=>m.id===c.welcomeProductId))fail();
        const pools={};
        if(c.benefitPools){if(!obj(c.benefitPools))fail();for(const [k,v] of Object.entries(c.benefitPools)){if(!JWB_CARDS.some(m=>m.id===k)||!money(v))fail();pools[k]=v;}}
        return {uid:c.uid,cardId:c.cardId,welcomeProductId:c.welcomeProductId||c.cardId,holderName:c.holderName.slice(0,40),cardNumber:c.cardNumber,expDate:c.expDate,cvv:c.cvv,creditLimit:c.creditLimit,statementBalance:c.statementBalance??0,spendProgress:c.spendProgress??0,welcomeUnlocked:c.welcomeUnlocked,remainingCreditPool:c.remainingCreditPool??0,status:c.status,benefitPools:pools};
      });
      d.selectedVaultIndex=Number.isInteger(raw.selectedVaultIndex)&&raw.selectedVaultIndex>=0&&raw.selectedVaultIndex<d.cards.length?raw.selectedVaultIndex:0;
      for(const [key,fields] of Object.entries({posFeed:['txHash','time','desc','amountStr','jrStr','type'],apiLogs:['id','time','method','endpoint','latency','summary'],generalLedger:['entryId','time','debitAccount','creditAccount','memo']})){
        if(raw[key]!==undefined&&!Array.isArray(raw[key]))fail();
        d[key]=(raw[key]||[]).slice(0,500).map(entry=>{
          if(!obj(entry)||!fields.every(k=>str(entry[k])))fail();
          const v=Object.fromEntries(fields.map(k=>[k,entry[k]]));
          if(key==='generalLedger'){if(!money(entry.amountUSD))fail();v.amountUSD=entry.amountUSD;}
          if(key==='apiLogs'){if(!Number.isInteger(entry.status)||entry.status<100||entry.status>599)fail();v.status=entry.status;}
          return v;
        });
      }
      if(raw.interestPeriod!==undefined){if(!/^\d{4}-\d{2}$/.test(raw.interestPeriod))fail();d.interestPeriod=raw.interestPeriod;}
      d.version='4.1.0';return d;
    }
    function validateOperation(endpoint){
      const bad=(zh,en)=>({status:400,message:bi(zh,en)});
      if(endpoint.endsWith('/fx-swap')||endpoint.endsWith('/authorize')||endpoint.endsWith('/reallocate-limit')){
        const id=endpoint.endsWith('/fx-swap')?'fxSwapAmount':endpoint.endsWith('/authorize')?'posAmountInput':'reallocAmountInput';
        const n=Number(document.getElementById(id).value);
        if(!validMoney(n))return bad('请输入大于 0 的有效金额（不超过 100 亿）','Enter a finite amount above zero, up to 10 billion');
        const c=endpoint.endsWith('/fx-swap')?document.getElementById('fxSwapFrom').value:endpoint.endsWith('/authorize')?document.getElementById('posCurrencySelect').value:'USD';
        if(!Object.hasOwn(CURRENCY_META,c)||Math.abs(n-roundCurrency(n,c))>0.000001)return bad('金额精度无效：日元须为整数，其他币种最多两位小数','Invalid precision: JPY requires whole units; other currencies allow two decimals');
        if(endpoint.endsWith('/fx-swap')){
          const to=document.getElementById('fxSwapTo').value;
          if(!Object.hasOwn(CURRENCY_META,to)||roundCurrency(n*FX_RATES_TO_USD[c]/FX_RATES_TO_USD[to],to)<=0)return bad('兑换结果不足最小货币单位','Exchange result is below the smallest currency unit');
        }
        if(endpoint.endsWith('/authorize')&&Math.round(n*FX_RATES_TO_USD[c]*100)<1)return bad('消费金额不足 0.01 USD','Purchase must be worth at least USD 0.01');
      }
      if(endpoint.endsWith('/authorize')&&document.getElementById('posCurrencySelect').value!=='USD'&&!usableFxRates())return {status:503,message:bi('请先连接参考汇率后再模拟外币消费','Connect to reference rates before simulating a foreign-currency purchase')};
      if(endpoint.endsWith('/issue-card')&&db.cards.length>=200)return bad('演示卡包最多容纳 200 张卡','Demo wallet supports up to 200 cards');
      return null;
    }
    const originalTranslations=new WeakMap();
    function translateText(value){
      const trimmed=value.trim();
      if(Object.hasOwn(UI_TRANSLATIONS,trimmed))return value.replace(trimmed,UI_TRANSLATIONS[trimmed]);
      let s=value;
      for(const [zh,en] of SORTED_TRANSLATIONS) s=s.split(zh).join(en);
      return s;
    }
    function localizeDocument(){
      if(currentLang!=='en')return;
      const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
      let node;
      while(node=walker.nextNode()){
        if(['SCRIPT','STYLE','TEXTAREA'].includes(node.parentElement?.tagName)||node.parentElement?.closest('#langBtnZh,#cloudApp,#cloudAuth,#cloudAccount,.cloud-toast'))continue;
        const value=node.nodeValue;
        if(!/[\u3400-\u9fff]/.test(value))continue;
        const en=translateText(value);
        if(en!==value){originalTranslations.set(node,{zh:value,en});node.nodeValue=en;}
      }
      document.querySelectorAll('[placeholder],[title],[aria-label]').forEach(el=>{
        if(el.closest('#cloudApp,#cloudAuth,#cloudAccount'))return;
        for(const attr of ['placeholder','title','aria-label']){
          const value=el.getAttribute(attr);if(!value)continue;
          const key='data-original-'+attr;
          if(!el.hasAttribute(key))el.setAttribute(key,value);
          el.setAttribute(attr,translateText(el.getAttribute(key)));
        }
      });
    }
    function restoreTranslatedNodes(){
      const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
      while(n=walker.nextNode()){const v=originalTranslations.get(n);if(v&&n.nodeValue===v.en)n.nodeValue=v.zh;}
      document.querySelectorAll('[data-original-placeholder],[data-original-title],[data-original-aria-label]').forEach(el=>{
        for(const a of ['placeholder','title','aria-label'])if(el.hasAttribute('data-original-'+a))el.setAttribute(a,el.getAttribute('data-original-'+a));
      });
    }
    function installLocalization(){
      new MutationObserver(()=>{localizeDocument();enhanceAccess();}).observe(document.body,{subtree:true,childList:true,characterData:true});
      localizeDocument();enhanceAccess();
      window.addEventListener('hashchange',()=>{const page=location.hash.slice(1)||'home';if(document.getElementById('page-'+page)&&page!==currentPage)switchPage(page);});
      document.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('[role="button"]')){e.preventDefault();e.target.click();}});
    }
    function enhanceAccess(){
      document.querySelectorAll('div[onclick]').forEach(el=>{if(!el.hasAttribute('role')){el.setAttribute('role','button');el.tabIndex=0;}});
      document.querySelectorAll('input,select').forEach(el=>{if(!el.hasAttribute('aria-label')){const label=el.parentElement.querySelector('label');el.setAttribute('aria-label',label?.textContent.trim()||el.id);}});
      for(const lang of ['zh','en'])document.getElementById(lang==='zh'?'langBtnZh':'langBtnEn').setAttribute('aria-pressed',String(currentLang===lang));
    }


    function submitDemoDeposit(){
      const currency=document.getElementById('depositCurrency').value;
      const amount=Number(document.getElementById('depositAmount').value);
      if(!validMoney(amount)||Math.abs(amount-roundCurrency(amount,currency))>0.000001){showApiToast('Demo Deposit · 400',bi('请输入正确精度的正数金额','Enter a positive amount with valid currency precision'),false);return;}
      apiDepositFunds(currency,amount);
    }
    function filterTransactionFeed(){
      const input=document.getElementById('ledgerSearch');if(!input)return;
      const query=input.value.trim().toLowerCase();
      const type=document.getElementById('ledgerType').value;
      let count=0;
      const rows=document.querySelectorAll('#sandboxLedger > div');
      rows.forEach((row,i)=>{
        const item=db.posFeed[i];
        const source=[item.desc,item.txHash,item.amountStr,item.jrStr,translateText(item.desc)].join(' ').toLowerCase();
        const match=(!query||source.includes(query))&&(type==='all'||item.type===type);
        row.hidden=!match;row.style.display=match?'':'none';if(match)count++;
      });
      document.getElementById('ledgerEmpty').classList.toggle('hidden',count>0);
    }
    function exportTransactionsCSV(){
      const quote=v=>'"'+String(v??'').replace(/^[=+@\-]/,"'$&").replaceAll('"','""')+'"';
      const rows=[['Time','Reference','Description','Amount / currencies','Rewards','Type'],...db.posFeed.map(x=>[x.time,x.txHash,currentLang==='en'?translateText(x.desc):x.desc,x.amountStr,x.jrStr,x.type])];
      const url=URL.createObjectURL(new Blob(['\uFEFF'+rows.map(row=>row.map(quote).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'}));
      const a=document.createElement('a');a.href=url;a.download='JWB_Demo_Transactions.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }

    function setLanguage(lang) {
      playLuxurySound('tick');
      if(!['zh','en'].includes(lang))return;
      currentLang = lang;
      document.documentElement.lang = lang==='zh'?'zh-CN':'en';
      try{localStorage.setItem('jwb_language',lang);}catch(e){}
      restoreTranslatedNodes();
      updateCalculator();
      updateStudioCardUI();
      document.getElementById('langBtnZh').className = lang === 'zh'
        ? 'px-2.5 py-1 rounded-full text-xs font-medium bg-white text-black transition'
        : 'px-2.5 py-1 rounded-full text-xs font-medium text-neutral-400 hover:text-white transition';
      document.getElementById('langBtnEn').className = lang === 'en'
        ? 'px-2.5 py-1 rounded-full text-xs font-medium bg-white text-black transition'
        : 'px-2.5 py-1 rounded-full text-xs font-medium text-neutral-400 hover:text-white transition';
      localizeDocument();
      syncAllViews();
    }


  
