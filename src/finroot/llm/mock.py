"""Mock LLM provider — deterministic, offline, no network.

Responses are keyed by prompt hash so the same prompt always produces the same
output. Always embeds ``<reasoning>`` and ``<confidence>`` tags so downstream
parsing is exercised in every test.

Expanded to 120+ canned responses for rich demo variety across all financial
domains with domain-specific keyword matching.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Generator

from finroot.llm.base import LLMResult, parse_reasoning_confidence

_CANNED: list[str] = [
    # ---- Portfolio analysis (15) ----
    "<reasoning>Portfolio allocation review. The holdings show a balanced mix across equity, debt, and alternatives.</reasoning>\nYour current allocation is 45% equity, 35% debt, 15% gold, 5% cash. This is well-diversified for a moderate risk profile. Consider rebalancing if equity exceeds 55%.\n<confidence>high</confidence>",
    "<reasoning>Diversification analysis. Multiple asset classes reduce concentration risk.</reasoning>\nDiversification across 4 asset classes with correlation below 0.3 reduces portfolio volatility by approximately 15-20%. Your current mix achieves this.\n<confidence>high</confidence>",
    "<reasoning>Rebalancing recommendation based on drift from target allocation.</reasoning>\nEquity has drifted 8% above target. Recommend booking partial profits in large-cap and redirecting to short-term debt funds to restore balance.\n<confidence>medium</confidence>",
    "<reasoning>Concentration risk assessment. Single stock exposure needs evaluation.</reasoning>\nYour portfolio has 28% exposure to a single stock. This exceeds the recommended 15% limit for individual positions. Consider diversifying through an index fund.\n<confidence>high</confidence>",
    "<reasoning>SIP analysis for systematic investment planning.</reasoning>\nA monthly SIP of ₹25,000 across large-cap, mid-cap, and debt funds over 10 years at 12% expected return would accumulate approximately ₹58 lakhs.\n<confidence>medium</confidence>",
    "<reasoning>Asset allocation for different life stages requires age-based adjustment.</reasoning>\nAt age 35, a 70% equity / 30% debt allocation is appropriate. As you approach 50, gradually shift to 50-50. Use the 100-minus-age rule as a starting point.\n<confidence>medium</confidence>",
    "<reasoning>Liquid fund vs savings account comparison for emergency corpus.</reasoning>\nLiquid funds offer 6.5-7% vs savings account 3-4%. For your ₹5L emergency fund, liquid funds provide better returns with T+1 redemption. Keep ₹1L in savings for immediate access.\n<confidence>high</confidence>",
    "<reasoning>Index fund vs active fund analysis for cost-conscious investors.</reasoning>\nOver 10 years, 80% of active funds underperform their benchmark after fees. Index funds at 0.1% expense ratio vs 1.5% active save ₹1.5L on a ₹10L investment over 10 years.\n<confidence>high</confidence>",
    "<reasoning>Goal-based portfolio mapping to financial objectives.</reasoning>\nMap each goal to a portfolio: retirement (aggressive, 20yr horizon), child education (balanced, 10yr), emergency (liquid, immediate). Each goal needs its own asset allocation.\n<confidence>high</confidence>",
    "<reasoning>Review of portfolio performance against benchmark.</reasoning>\nYour portfolio returned 14.2% vs Nifty 50's 12.8% over 3 years. The alpha of 1.4% comes from mid-cap allocation. Risk-adjusted return (Sharpe 1.1) is above average.\n<confidence>high</confidence>",
    "<reasoning>Mutual fund selection criteria for core portfolio allocation.</reasoning>\nSelect funds based on: 1) Consistent top-quartile returns over 5 years, 2) Expense ratio below category average, 3) Fund manager tenure > 3 years, 4) AUM > ₹5,000 Cr for stability.\n<confidence>high</confidence>",
    "<reasoning>ELSS fund comparison for tax-saving under Section 80C.</reasoning>\nELSS funds offer shortest lock-in (3 years) among 80C options with equity growth potential. Top funds: Axis Bluechip (21% 5yr CAGR), Mirae Asset Large Cap (19%). Invest up to ₹1.5L annually.\n<confidence>medium</confidence>",
    "<reasoning>International fund diversification benefits for Indian portfolios.</reasoning>\nAdding 20% international exposure reduces portfolio volatility by 8-12% due to low correlation (0.4-0.5) with Indian markets. Consider Feeder funds for simplicity or LRS for direct US access.\n<confidence>medium</confidence>",
    "<reasoning>Gold allocation role in portfolio as inflation hedge and diversifier.</reasoning>\n5-15% gold allocation provides inflation protection and crisis alpha. Gold ETFs (0.5% expense) outperform physical gold on cost. Gold has -0.05 correlation with equity, reducing drawdowns.\n<confidence>high</confidence>",
    "<reasoning>Debt fund selection for stable income and capital preservation.</reasoning>\nFor stable income: choose short-duration or corporate bond funds (3-5yr maturity). Avoid credit risk funds for safety. Current yields: 7-7.5% for AAA-rated portfolios. Check credit quality distribution.\n<confidence>medium</confidence>",
    # ---- Risk assessment (15) ----
    "<reasoning>VaR calculation requires historical return data. This is a general assessment.</reasoning>\nAt 95% confidence, your portfolio's daily VaR is approximately 1.8% of portfolio value. This means on 5% of trading days, losses could exceed this amount.\n<confidence>medium</confidence>",
    "<reasoning>Maximum drawdown analysis for risk evaluation.</reasoning>\nHistorical maximum drawdown for your allocation is 22% (during COVID crash). Recovery took 8 months. Ensure you have liquidity to withstand such drawdowns without forced selling.\n<confidence>medium</confidence>",
    "<reasoning>Sharpe ratio interpretation for risk-adjusted returns.</reasoning>\nYour portfolio Sharpe ratio is 0.85, indicating you're earning 0.85% excess return per 1% of risk. Above 1.0 is good; below 0.5 suggests you're not adequately compensated for risk.\n<confidence>high</confidence>",
    "<reasoning>Beta analysis for market sensitivity assessment.</reasoning>\nPortfolio beta of 1.15 means it moves 15% more than the market. In a 10% market decline, expect approximately 11.5% portfolio decline. Reduce beta by adding defensive sectors.\n<confidence>medium</confidence>",
    "<reasoning>Volatility analysis for risk budgeting.</reasoning>\nAnnual portfolio volatility is 14.2%, within acceptable range for moderate risk profile. Monthly swings of ±4% are normal. Don't panic at routine volatility.\n<confidence>high</confidence>",
    "<reasoning>Risk capacity vs risk tolerance distinction is important.</reasoning>\nRisk capacity (ability to bear loss) depends on income stability, emergency fund, and time horizon. Risk tolerance (willingness) is psychological. Both must align for suitable allocation.\n<confidence>high</confidence>",
    "<reasoning>Downside risk protection strategies.</reasoning>\nProtect against tail risk: maintain 6-month emergency fund, use STP for large equity investments, consider put options for concentrated positions, and keep some allocation in negatively correlated assets.\n<confidence>medium</confidence>",
    "<reasoning>Correlation analysis between portfolio components.</reasoning>\nYour equity-debt correlation is 0.12, providing good diversification. Gold correlation with equity is -0.05, making it an effective hedge. This combination reduces overall portfolio risk.\n<confidence>high</confidence>",
    "<reasoning>Value-at-Risk methodology comparison for accurate risk measurement.</reasoning>\nHistorical VaR uses past returns; parametric VaR assumes normal distribution. For Indian markets with fat tails, parametric VaR underestimates risk by 15-20%. Consider using Monte Carlo VaR.\n<confidence>medium</confidence>",
    "<reasoning>Stress testing portfolio against historical scenarios.</reasoning>\nUnder 2008-like crisis (40% equity decline), your 60/40 portfolio would drop 24%. Under 2020 COVID crash (30% decline), drop would be 18%. Ensure emergency fund covers these scenarios.\n<confidence>medium</confidence>",
    "<reasoning>Portfolio concentration risk using HHI index.</reasoning>\nHHI of 0.18 indicates moderate concentration. Top 3 stocks hold 45% of equity allocation. Diversify by adding mid-cap or sectoral funds to reduce single-stock risk below 10% per position.\n<confidence>high</confidence>",
    "<reasoning>Sequence of returns risk for near-retirees.</reasoning>\nIf markets crash in first 3 years of retirement, withdrawal rate jumps from 4% to 7%, depleting corpus 8 years earlier. Build 3-year expense buffer in liquid funds to avoid selling equity in downturns.\n<confidence>medium</confidence>",
    "<reasoning>Risk parity approach for balanced portfolio construction.</reasoning>\nRisk parity allocates based on risk contribution, not capital. Equal risk from equity (30% capital, 70% risk) and debt (70% capital, 30% risk). Requires leverage for implementation in practice.\n<confidence>medium</confidence>",
    "<reasoning>Drawdown recovery time analysis for equity portfolios.</reasoning>\nHistorical average: 10% drawdown recovers in 3-4 months, 20% in 8-12 months, 30% in 2-3 years. Your 60% equity allocation means 18% drawdown in a 30% market crash. Plan liquidity accordingly.\n<confidence>high</confidence>",
    "<reasoning>Sortino ratio for downside risk assessment.</reasoning>\nPortfolio Sortino ratio of 1.2 means you're earning 1.2% excess return per 1% of downside risk. Better than Sharpe ratio (0.85) because it ignores upside volatility. Above 1.0 is acceptable.\n<confidence>medium</confidence>",
    # ---- Tax planning (15) ----
    "<reasoning>LTCG equity tax computation. Held > 12 months, 10% above ₹1L exemption, 4% cess.</reasoning>\nTax on ₹2,00,000 LTCG from equity: ₹10,400 (10% on ₹1L above exemption + 4% cess). Effective rate: 5.2%. Budget 2024 rules.\n<confidence>high</confidence>",
    "<reasoning>STCG equity tax computation. Held ≤ 12 months, 15% flat + 4% cess.</reasoning>\nSTCG of ₹1,50,000 from equity: ₹23,400 tax (15% + 4% cess). Effective rate: 15.6%. Consider holding for 12+ months to qualify for LTCG rates.\n<confidence>high</confidence>",
    "<reasoning>Tax-loss harvesting strategy for reducing capital gains liability.</reasoning>\nHarvest ₹50,000 in unrealized losses to offset gains. This saves ₹5,200 in LTCG tax. Repurchase after 30 days to avoid wash sale rules (India has no wash sale rule, but maintain substance).\n<confidence>medium</confidence>",
    "<reasoning>Section 80C deduction optimization for salaried individuals.</reasoning>\nMaximize ₹1.5L 80C via EPF (mandatory) + ELSS (₹50K) + PPF (₹50K) + term insurance premium. ELSS has shortest lock-in (3 years) with equity growth potential.\n<confidence>high</confidence>",
    "<reasoning>NPS tax benefit under Section 80CCD(1B) for additional deduction.</reasoning>\nAdditional ₹50,000 deduction under 80CCD(1B) for NPS contribution. At 30% tax bracket, saves ₹15,600 in tax. NPS also offers 80CCD(2) for employer contribution.\n<confidence>high</confidence>",
    "<reasoning>Debt fund taxation after Budget 2023 changes.</reasoning>\nPost April 2023, debt fund gains are taxed at slab rate (no indexation benefit). For ₹8L income + ₹1L debt gain: tax at 10% slab = ₹10,000 + cess ₹400.\n<confidence>high</confidence>",
    "<reasoning>Home loan tax benefits under Sections 24 and 80C analysis.</reasoning>\nHome loan: ₹2L deduction under Sec 24(b) for interest + ₹1.5L under 80C for principal. Total tax saving at 30% bracket: ₹1.05L annually.\n<confidence>high</confidence>",
    "<reasoning>Capital gains tax planning across financial years.</reasoning>\nSpread large redemptions across 2 financial years to utilize ₹1L LTCG exemption each year. ₹3L gain over 2 years = ₹20,800 tax vs ₹31,200 in single year.\n<confidence>high</confidence>",
    "<reasoning>Tax implications of switching between mutual fund schemes.</reasoning>\nSwitching between schemes is treated as redemption + fresh purchase. LTCG/STCG tax applies. Use STP (Systematic Transfer Plan) to spread the tax impact.\n<confidence>medium</confidence>",
    "<reasoning>Dividend taxation after removal of DDT in Budget 2020.</reasoning>\nDividends are now taxed at slab rate in the investor's hands. For ₹50K dividend at 30% bracket: ₹15,600 tax. Growth option with SWP is more tax-efficient.\n<confidence>high</confidence>",
    "<reasoning>PPF investment tax benefits and maturity planning.</reasoning>\nPPF offers EEE status: deduction under 80C (₹1.5L), tax-free interest (7.1%), and tax-free maturity. 15-year lock-in with partial withdrawal from year 7. Ideal for conservative long-term savings.\n<confidence>high</confidence>",
    "<reasoning>LIC premium tax deduction limits under Section 80C.</reasoning>\nLIC premium paid qualifies for 80C deduction (within ₹1.5L limit). However, surrender value or maturity proceeds may be taxable under certain conditions. Consider term insurance for pure protection.\n<confidence>medium</confidence>",
    "<reasoning>Real estate capital gains tax with indexation benefits.</reasoning>\nLTCG on property (held > 24 months) taxed at 20% with indexation. Indexed cost = ₹50L × (363/272) = ₹66.7L. Gain = ₹1Cr - ₹66.7L = ₹33.3L. Tax = ₹6.66L + cess ₹26,640.\n<confidence>high</confidence>",
    "<reasoning>Gold investment tax treatment — physical vs digital vs ETF.</reasoning>\nGold LTCG (held > 36 months) taxed at 20% with indexation. STCG at slab rate. Sovereign Gold Bonds (SGBs) offer tax-free redemption after 8 years. Digital gold attracts GST on purchase.\n<confidence>high</confidence>",
    "<reasoning>FD interest taxation and TDS implications for senior citizens.</reasoning>\nFD interest is taxable at slab rate. TDS deducted if interest > ₹40K/year (₹50K for seniors). Submit Form 15G/15H if total income below taxable limit to avoid TDS. Senior citizens get higher exemption.\n<confidence>high</confidence>",
    # ---- News/market impact (15) ----
    "<reasoning>RBI repo rate impact on debt and equity markets analysis.</reasoning>\nRBI holding repo rate at 6.5% is neutral for debt funds. Existing bond prices remain stable. Equity markets benefit from stable rates. Your debt allocation faces no immediate impact.\n<confidence>high</confidence>",
    "<reasoning>Budget 2024 impact on personal finance and investment strategy.</reasoning>\nBudget 2024 key changes: LTCG 10% (unchanged), STCG 15% (unchanged), new tax regime default. Review if old regime with deductions is still better for your income level.\n<confidence>medium</confidence>",
    "<reasoning>Global market correlation with Indian markets during volatility.</reasoning>\nIndian markets show 0.65 correlation with US markets. A 5% US decline typically translates to 3-4% Indian decline. Your international diversification provides partial hedge.\n<confidence>medium</confidence>",
    "<reasoning>Sector rotation strategy based on economic cycle analysis.</reasoning>\nCurrent late-cycle phase favors defensive sectors (pharma, FMCG, IT). Reduce cyclical exposure (metals, real estate, infrastructure). Rotate back when leading indicators turn positive.\n<confidence>medium</confidence>",
    "<reasoning>Inflation impact on real returns and purchasing power.</reasoning>\nAt 5.5% inflation, your 8% nominal return is only 2.5% real return. Ensure equity allocation is sufficient to beat inflation over long term. Debt alone won't preserve purchasing power.\n<confidence>high</confidence>",
    "<reasoning>Crude oil price impact on Indian economy and portfolio.</reasoning>\nIndia imports 85% of crude. A $10/barrel increase adds 0.4% to inflation, weakens INR by 1-2%, and pressures current account. Your portfolio's energy exposure provides partial hedge.\n<confidence>medium</confidence>",
    "<reasoning>Market correction analysis and investment opportunity assessment.</reasoning>\nMarket corrections of 10-15% occur every 12-18 months on average. These are buying opportunities, not panic triggers. Maintain SIP discipline. Deploy additional lump sums at 10%+ corrections.\n<confidence>high</confidence>",
    "<reasoning>INR depreciation impact on portfolio and hedging strategies.</reasoning>\nINR depreciating 3-5% annually is normal. International funds benefit from INR weakness. Your ₹10L international allocation gains ₹30-50K annually from currency alone.\n<confidence>medium</confidence>",
    "<reasoning>Fed rate cut impact on Indian equity and debt markets.</reasoning>\nFed rate cuts typically weaken USD, strengthen INR, and boost Indian equity flows. Debt funds benefit from falling global yields. Expect 2-3% equity rally and debt NAV appreciation over 6 months.\n<confidence>medium</confidence>",
    "<reasoning>SEBI regulatory changes impact on mutual fund industry.</reasoning>\nSEBI's expense ratio cap reduction will lower fund house revenues. Index funds gain appeal as active funds face margin pressure. Small-cap fund flow restrictions may reduce momentum in mid/small segments.\n<confidence>medium</confidence>",
    "<reasoning>Earnings season impact on portfolio holdings and sector allocation.</reasoning>\nQ2 results show IT sector beating estimates by 8% while banking missed by 3%. Consider rotating from underperforming PSBs to private banks. Pharma sector guidance upgrade suggests overweight.\n<confidence>medium</confidence>",
    "<reasoning>Geopolitical risk assessment for portfolio positioning.</reasoning>\nUS-China tensions and Middle East conflicts create short-term volatility but rarely impact Indian fundamentals long-term. Maintain allocation; add 5% gold for geopolitical hedge if concerned.\n<confidence>medium</confidence>",
    "<reasoning>GST rate change impact on consumer and manufacturing sectors.</reasoning>\nGST rate increase on luxury goods from 18% to 28% will compress margins for auto and consumer durables. FMCG and pharmaceuticals unaffected. Portfolio impact minimal if diversified.\n<confidence>medium</confidence>",
    "<reasoning>Monetary policy stance change implications for debt duration.</reasoning>\nRBI shifting from 'withdrawal of accommodation' to 'neutral' signals future rate cuts. Extend debt duration to 4-5 years to lock in current yields before they fall. Short-duration funds will underperform.\n<confidence>high</confidence>",
    "<reasoning>Corporate governance red flags in portfolio holdings.</reasoning>\nThree holdings show governance concerns: 1) Promoter pledge > 50%, 2) Auditor qualifications, 3) Related-party transactions > 20% of revenue. Review and consider exiting positions with multiple red flags.\n<confidence>high</confidence>",
    # ---- Cashflow (15) ----
    "<reasoning>Emergency fund adequacy assessment based on monthly expenses.</reasoning>\nYour monthly expenses are ₹60,000. Emergency fund should be 6-12 months = ₹3.6-7.2L. Current ₹4L covers 6.7 months — adequate but aim for 9 months.\n<confidence>high</confidence>",
    "<reasoning>Debt-to-income ratio analysis for financial health check.</reasoning>\nTotal EMI: ₹45,000 on ₹1.2L income = 37.5% debt-to-income ratio. Below 40% is healthy. Prioritize paying off high-interest debt (credit card 36% > personal loan 12% > home loan 8.5%).\n<confidence>high</confidence>",
    "<reasoning>SIP step-up strategy for wealth creation with income growth.</reasoning>\nStart SIP at ₹20,000/month with 10% annual step-up. At 12% return, this accumulates ₹1.2Cr in 15 years vs ₹75L without step-up. Step-up leverages income growth.\n<confidence>high</confidence>",
    "<reasoning>Cash flow planning for irregular income (freelancers/business owners).</reasoning>\nFor irregular income: maintain 12-month expense buffer, use liquid funds for surplus months, automate investments during high-income months, and use SWP for lean months.\n<confidence>medium</confidence>",
    "<reasoning>Loan prepayment vs investment analysis for optimal capital allocation.</reasoning>\nHome loan at 8.5% vs equity expected 12%: invest the surplus. But if loan rate > 10%, prepay. Tax benefit on home loan interest (₹2L) changes the math — factor that in.\n<confidence>medium</confidence>",
    "<reasoning>Retirement corpus calculation for financial independence planning.</reasoning>\nAt ₹1L monthly expense, 3% inflation, 25 years to retirement: corpus needed = ₹5.4Cr (using 4% withdrawal rate). Current SIP of ₹30K/month at 12% reaches ₹3.5Cr — gap of ₹1.9Cr.\n<confidence>medium</confidence>",
    "<reasoning>Compound interest power demonstration for long-term wealth creation.</reasoning>\n₹10,000/month at 12% CAGR for 30 years = ₹3.5Cr total corpus (₹36L invested, ₹3.14Cr interest). Starting 10 years earlier creates 3.5x more wealth. Time is the most powerful wealth-building tool.\n<confidence>high</confidence>",
    "<reasoning>FD vs equity SIP comparison for different time horizons.</reasoning>\nFD at 7%: ₹10K/month for 10 years = ₹17.3L. Equity SIP at 12%: ₹10K/month for 10 years = ₹23.2L. Difference: ₹5.9L. For 20 years: FD ₹52L vs equity ₹99L. Longer horizon favors equity.\n<confidence>high</confidence>",
    "<reasoning>PPF investment strategy for retirement corpus building.</reasoning>\nPPF at 7.1% with ₹1.5L annual contribution for 15 years = ₹40.7L corpus. Extend for 5 more years: ₹58.2L. PPF suits conservative investors with long horizon. Maximize annual contribution before March 31.\n<confidence>high</confidence>",
    "<reasoning>NPS contribution strategy for retirement and tax benefits.</reasoning>\nNPS offers additional ₹50K deduction under 80CCD(1B). At ₹10K/month contribution for 25 years at 10% return: ₹1.05Cr corpus. 40% mandatory annuity provides guaranteed income. Optimize for tax + retirement.\n<confidence>high</confidence>",
    "<reasoning>Monthly surplus allocation framework for balanced financial planning.</reasoning>\nSurplus of ₹40K/month: 30% equity SIP (₹12K), 20% debt (₹8K), 10% gold (₹4K), 20% emergency fund (₹8K), 20% goal-specific (₹8K). Adjust based on risk profile and existing allocations.\n<confidence>medium</confidence>",
    "<reasoning>Education expense planning with systematic investment approach.</reasoning>\nChild's higher education in 15 years: ₹50L needed (at 6% education inflation). Monthly SIP of ₹15K at 12% = ₹50L. Start now — delaying 5 years requires ₹33K/month. Education costs rise faster than general inflation.\n<confidence>high</confidence>",
    "<reasoning>Wedding expense planning with short-term investment strategy.</reasoning>\nWedding in 3 years needs ₹25L. Save ₹70K/month in ultra-short debt funds (7% yield). Avoid equity for <3 year goals — sequence risk too high. Consider RD for guaranteed corpus with bank.\n<confidence>medium</confidence>",
    "<reasoning>Car purchase planning with depreciation and opportunity cost analysis.</reasoning>\n₹10L car at 25% depreciation annually: worth ₹5.6L in 3 years. Opportunity cost of lump sum payment: ₹12% return = ₹3.6L lost. Consider 50% down + 3-year loan at 8.5% to balance cost vs opportunity.\n<confidence>medium</confidence>",
    "<reasoning>Healthcare expense planning for retirement years.</reasoning>\nAt 6% medical inflation, ₹10L current hospitalization cost becomes ₹43L in 25 years. Build ₹50L health corpus via: ₹20L super top-up now + ₹30L through equity SIP for long-term healthcare needs.\n<confidence>medium</confidence>",
    # ---- Credit (15) ----
    "<reasoning>Credit score impact on loan eligibility and interest rates.</reasoning>\nCredit score 750+ gets best rates (8.5% home loan). Score 650-750: 9-10%. Below 650: may be rejected. Check score quarterly, dispute errors, keep utilization below 30%.\n<confidence>high</confidence>",
    "<reasoning>Credit card debt management and interest rate comparison.</reasoning>\nCredit card debt at 36-42% APR is the most expensive debt. Pay full amount, not minimum. If carrying balance, take personal loan at 12% to consolidate — saves 24-30% interest.\n<confidence>high</confidence>",
    "<reasoning>Loan EMI optimization and tenure impact analysis.</reasoning>\n₹50L home loan at 8.5%: 20yr EMI = ₹43,391 (total interest ₹54.1L). 15yr EMI = ₹49,217 (total interest ₹38.6L). Shorter tenure saves ₹15.5L in interest.\n<confidence>high</confidence>",
    "<reasoning>Balance transfer opportunity assessment for existing loans.</reasoning>\nCurrent home loan at 9.5% with ₹40L outstanding. Transfer to 8.5% saves ₹40,000/year in interest. Processing fee ₹10,000. Net benefit: ₹30,000/year. Transfer is worthwhile if >2 years remaining.\n<confidence>medium</confidence>",
    "<reasoning>Credit utilization ratio optimization for score improvement.</reasoning>\nYour credit utilization is 80% (₹2L on ₹2.5L limit). This is the primary reason for your 50-point score drop. Pay down to below ₹75K (30%) immediately. Score should recover 30-50 points in 1-2 billing cycles.\n<confidence>high</confidence>",
    "<reasoning>Credit score factors breakdown and improvement strategy.</reasoning>\nScore components: Payment history (35%), Credit utilization (30%), Credit age (15%), Credit mix (10%), New inquiries (10%). Focus on utilization and payment history for fastest improvement. Never miss payment due dates.\n<confidence>high</confidence>",
    "<reasoning>Multiple loan application impact on credit score.</reasoning>\nEach loan application creates a hard inquiry, reducing score by 5-10 points. Three applications in short period signal desperation to lenders. Wait 3-6 months between applications. Check pre-approved offers first.\n<confidence>high</confidence>",
    "<reasoning>Credit card closing impact on credit score and history.</reasoning>\nClosing old cards reduces credit history length and available credit, increasing utilization ratio. Keep oldest card open even with zero balance. Your ₹10L available credit dropping to ₹2L will spike utilization to 100% on new card.\n<confidence>high</confidence>",
    "<reasoning>Personal loan vs credit card debt consolidation strategy.</reasoning>\n₹3L credit card debt at 36% APR: interest = ₹1.08L/year. Personal loan at 12%: interest = ₹36K/year. Savings: ₹72K/year. But ensure you don't accumulate new card debt while repaying the loan.\n<confidence>high</confidence>",
    "<reasoning>Loan prepayment priority based on interest rate ranking.</reasoning>\nRank debts by interest rate: Credit card (36%) > Personal loan (12%) > Car loan (9%) > Home loan (8.5%). Prepay highest rate first. Exception: if home loan tax benefit exceeds interest differential, maintain it.\n<confidence>high</confidence>",
    "<reasoning>Credit card settlement vs full payment — long-term impact analysis.</reasoning>\nSettlement marks 'settled' on CIBIL for 7 years, reducing score by 75-100 points. Future loan rejection probability: 40-60%. If unavoidable, negotiate for 'paid in full' reporting. Otherwise, convert to EMI plan.\n<confidence>high</confidence>",
    "<reasoning>EMI affordability check using debt-to-income ratio.</reasoning>\nTotal EMIs should not exceed 40-50% of take-home pay. Your ₹80K EMI on ₹1.5L income = 53%. Exceeds safe threshold. Reduce by extending tenure or prepaying highest-rate loan first. Maintain 20% buffer for emergencies.\n<confidence>high</confidence>",
    "<reasoning>Home loan floating vs fixed rate comparison for current environment.</reasoning>\nFixed rate (9%) higher than floating (8.5%). Floating benefits if rates fall; risk if rates rise. Given RBI's neutral stance, floating is preferable. Lock in fixed only if you expect >100 bps rate increase.\n<confidence>medium</confidence>",
    "<reasoning>Credit score recovery timeline after financial setbacks.</reasoning>\nScore recovery after default: 6-12 months for minor delinquency, 2-3 years for major default, 7 years for settlement/write-off. Focus on: 1) Never miss payments, 2) Keep utilization <30%, 3) Avoid new hard inquiries for 6 months.\n<confidence>medium</confidence>",
    "<reasoning>Loan eligibility calculation based on income and existing obligations.</reasoning>\nAt ₹1.2L income, max EMI = ₹48K (40% rule). Existing EMI ₹20K. Available for new loan: ₹28K. At 8.5% for 20 years, this supports ₹32L home loan. Consider prepaying existing loan to increase eligibility.\n<confidence>high</confidence>",
    # ---- Insurance (15) ----
    "<reasoning>Health insurance adequacy for family coverage assessment.</reasoning>\nFamily floater of ₹10L is minimum. With rising medical costs, ₹15-20L is recommended. Top-up ₹50L super top-up costs only ₹2,000/year more. Employer cover is insufficient — buy personal policy.\n<confidence>high</confidence>",
    "<reasoning>Term insurance vs ULIP comparison for life coverage needs.</reasoning>\nTerm insurance: ₹1Cr cover at ₹12,000/year. ULIP: same cover at ₹1.2L/year with investment component. Buy term + invest difference in mutual funds: ₹1.08L/year at 12% = ₹35L in 15 years vs ₹18L in ULIP.\n<confidence>high</confidence>",
    "<reasoning>Insurance claim rejection prevention and documentation advice.</reasoning>\nCommon claim rejection reasons: non-disclosure of pre-existing conditions, policy lapse, exclusions. Disclose everything at purchase, pay premiums on time, and keep medical records organized.\n<confidence>high</confidence>",
    "<reasoning>Personal accident and disability insurance need assessment.</reasoning>\nPersonal accident cover of 5x annual income (₹60L at ₹12L income) costs ₹3,000-5,000/year. Covers accidental death, permanent disability, and temporary disability. Essential for sole earners.\n<confidence>medium</confidence>",
    "<reasoning>Term insurance coverage calculation using human life value approach.</reasoning>\nHLV = Annual income × Working years - Personal consumption. At ₹15L income, 25 years, 30% consumption: HLV = ₹15L × 25 × 0.7 = ₹2.62Cr. Minimum ₹1Cr term cover is insufficient; aim for ₹1.5-2Cr.\n<confidence>high</confidence>",
    "<reasoning>Health insurance waiting period implications for pre-existing conditions.</reasoning>\nPED waiting period: typically 3-4 years from policy inception. If disclosed at purchase and 4 years have passed, claim should be honored. If not disclosed, insurer can reject. Check policy wordings for specific waiting period.\n<confidence>high</confidence>",
    "<reasoning>ULIP charges breakdown — premium allocation, mortality, fund management.</reasoning>\nULIP charges: Premium allocation (2-5%), Mortality charges (varies with age), Fund management (1-1.5%). For ₹1L premium, ₹5K allocation charge + ₹3K mortality + ₹1.5K fund charge = ₹9.5K deductions. Actual investment: ₹90.5K.\n<confidence>high</confidence>",
    "<reasoning>Health insurance super top-up strategy for cost-effective high coverage.</reasoning>\nBase policy: ₹10L (₹15K/year) + Super top-up: ₹50L with ₹5L deductible (₹3K/year). Total: ₹18K/year for ₹60L coverage. Super top-up costs only 20% more for 5x additional coverage.\n<confidence>high</confidence>",
    "<reasoning>Term insurance rider evaluation — critical illness, accident, waiver.</reasoning>\nCritical illness rider adds 20-30% to premium but pays lump sum on diagnosis. Worth it if no separate CI policy. Accident rider: ₹500/year for ₹25L cover — good value. Premium waiver: useful if sole earner with dependents.\n<confidence>medium</confidence>",
    "<reasoning>Endowment policy surrender analysis and opportunity cost calculation.</reasoning>\n₹50K/year premium for 8 years = ₹4L invested. Surrender value: ₹1.5-2L (37-50% of premiums). ₹1Cr term plan: ₹15K/year. Invest ₹35K/year difference in equity SIP at 12%: ₹48L in 15 years vs ₹25L endowment maturity.\n<confidence>high</confidence>",
    "<reasoning>Group health insurance portability when changing employers.</reasoning>\nGroup health insurance is employer-specific and non-portable. Buy personal policy before leaving job. Port employer cover to personal policy within 30-45 days of leaving to avoid fresh waiting periods. Pre-existing conditions carry over.\n<confidence>high</confidence>",
    "<reasoning>Health insurance cashless vs reimbursement claim process comparison.</reasoning>\nCashless: Network hospital, pre-approval, no upfront payment. Reimbursement: Any hospital, pay first, submit bills. Cashless saves ₹2-5L upfront for major surgeries. Check network hospital list before hospitalization. Keep all bills for reimbursement.\n<confidence>high</confidence>",
    "<reasoning>Life insurance needs change analysis through life stages.</reasoning>\nAge 25 (single): ₹25L term cover. Age 30 (married): ₹50L. Age 35 (2 kids): ₹1Cr. Age 45 (teenagers): ₹1.5Cr. Age 55 (pre-retirement): ₹75L (reducing dependency). Review coverage every 3-5 years or after major life events.\n<confidence>high</confidence>",
    "<reasoning>Health insurance premium optimization strategies for cost savings.</reasoning>\nReduce premiums: 1) Buy early (age 25 vs 35: 40% cheaper), 2) Choose family floater over individual, 3) Opt for 2-year policy (5-10% discount), 4) Add super top-up instead of increasing base, 5) Use preventive health check-up benefits.\n<confidence>medium</confidence>",
    "<reasoning>Insurance claim documentation checklist for smooth settlement.</reasoning>\nEssential documents: 1) Claim form, 2) Discharge summary, 3) Hospital bills (itemized), 4) Prescription receipts, 5) Diagnostic reports, 6) Pre-auth approval (cashless). Submit within 15-30 days of discharge. Keep photocopies of everything.\n<confidence>high</confidence>",
    # ---- Estate planning (15) ----
    "<reasoning>Nomination vs succession planning — legal implications for investors.</reasoning>\nNomination is NOT succession — nominee is a trustee, not owner. Legal heirs inherit per succession law. Update nominations for all investments. Make a will to avoid disputes.\n<confidence>high</confidence>",
    "<reasoning>Will preparation and succession planning for asset protection.</reasoning>\nA registered will costs ₹5,000-10,000 and prevents years of legal hassle for heirs. List all assets, specify distribution, appoint executor, and review every 3 years or after major life events.\n<confidence>high</confidence>",
    "<reasoning>Joint account and ownership structure for estate planning.</reasoning>\nJoint accounts with 'either or survivor' clause provide seamless transition. But be aware of gift tax implications if adding non-spouse. For real estate, joint ownership reduces stamp duty in some states.\n<confidence>medium</confidence>",
    "<reasoning>EPF and PPF nomination update requirements after marriage.</reasoning>\nEPF/PPF nominations do NOT auto-update after marriage. Legal heirs (wife, children) have rights under succession laws regardless of nomination. Update nomination forms at EPFO/PPF office within 30 days of marriage.\n<confidence>high</confidence>",
    "<reasoning>Intestate succession process for assets without a will.</reasoning>\nWithout will: Hindu Succession Act applies. Class I heirs (wife, children, mother) inherit equally. Process: Succession certificate (3-6 months) → Asset transfer. Bank FDs: nominee claim. Property: Mutation in revenue records. Time: 6-18 months.\n<confidence>high</confidence>",
    "<reasoning>Will registration vs unregistered will — legal validity comparison.</reasoning>\nUnregistered will is valid but can be challenged more easily. Registered will (₹50-100 at Sub-Registrar) provides proof of execution and reduces disputes. Recommend registration for assets > ₹50L or complex family situations.\n<confidence>high</confidence>",
    "<reasoning>Succession planning for financial assets — MF, stocks, bank accounts.</reasoning>\nMF folios: Add nominee + update transmission form with death certificate. Bank accounts: Nominee can claim directly if balance < ₹5L. Stocks: Transmission via depository with death certificate + legal heir proof. Process takes 2-4 weeks.\n<confidence>high</confidence>",
    "<reasoning>Real estate succession — mutation, transfer, and stamp duty implications.</reasoning>\nProperty transfer requires: 1) Death certificate, 2) Will/succession certificate, 3) Mutation application at municipal office, 4) Stamp duty (varies by state, often reduced for family transfers). Process: 3-12 months depending on state.\n<confidence>medium</confidence>",
    "<reasoning>Trust formation for estate planning and asset protection benefits.</reasoning>\nPrivate trust can: 1) Avoid probate, 2) Control asset distribution, 3) Minimize estate tax (if applicable), 4) Protect assets from creditors. Irrevocable trust is more tax-efficient but loses control. Revocable trust maintains control but offers less protection.\n<confidence>medium</confidence>",
    "<reasoning>Nomination for insurance policies — legal implications and update process.</reasoning>\nInsurance nominee receives proceeds but is trustee for legal heirs. Update nomination after marriage, birth of children, or divorce. IRDAI mandates insurers to accept nomination changes. Submit form with ID proof; no fee.\n<confidence>high</confidence>",
    "<reasoning>Estate planning for HUF (Hindu Undivided Family) structure.</reasoning>\nHUF provides: 1) Additional ₹1.5L 80C deduction, 2) Separate tax slab, 3) Asset protection from individual creditors. Create HUF with self-contributed assets. Succession: Karta manages; coparceners inherit equally.\n<confidence>medium</confidence>",
    "<reasoning>Digital asset estate planning — email, crypto, online accounts.</reasoning>\nDigital assets: 1) Email/social media: Designate legacy contact (Google) or provide credentials in sealed envelope, 2) Crypto: Store seed phrase securely with attorney, 3) Online banking: Update nominee, 4) Cloud storage: Document access details.\n<confidence>medium</confidence>",
    "<reasoning>Probate avoidance strategies for smooth asset transfer.</reasoning>\nAvoid probate: 1) Joint ownership with survivorship, 2) Nomination on all accounts, 3) Living trust, 4) Payable-on-death bank accounts, 5) Transfer-on-death for investments. Combined approach reduces probate estate to zero.\n<confidence>high</confidence>",
    "<reasoning>Estate duty and inheritance tax considerations in India.</reasoning>\nIndia abolished estate duty in 1985. Currently no inheritance tax. But wealth tax may apply if net wealth > ₹30L (rarely enforced). Plan for potential future estate tax through trust formation and gifting strategies.\n<confidence>medium</confidence>",
    "<reasoning>Family settlement deed vs will for ancestral property distribution.</reasoning>\nAncestral property: Family settlement deed (unregistered) can distribute among coparceners without stamp duty. Will requires probate for immovable property. Settlement deed is faster (2-4 weeks) vs will (6-12 months for probate).\n<confidence>medium</confidence>",
    # ---- Behavioral biases (15) ----
    "<reasoning>Loss aversion bias — investors feel losses 2x more than equivalent gains.</reasoning>\nYou're holding a losing stock hoping it'll recover (loss aversion). If the fundamental story has changed, sell and harvest the tax loss. Holding losers hoping for recovery is a classic behavioral trap.\n<confidence>high</confidence>",
    "<reasoning>Recency bias — overweighting recent performance in investment decisions.</reasoning>\nDon't chase last year's top-performing sector/category. Past 1-year returns predict future returns poorly. Stick to your asset allocation rather than chasing recent winners.\n<confidence>high</confidence>",
    "<reasoning>Herd mentality in investing — following the crowd leads to buying high and selling low.</reasoning>\nWhen everyone is buying, prices are high. When everyone is selling, prices are low. Contrarian investing (buying when others are fearful) historically outperforms herd-following.\n<confidence>medium</confidence>",
    "<reasoning>Overconfidence bias in stock picking and market timing.</reasoning>\nMost individual stock pickers underperform indices after 5 years. Your 3 stock picks returned 15% vs Nifty's 18% — the opportunity cost of overconfidence. Diversify through index funds.\n<confidence>medium</confidence>",
    "<reasoning>Anchoring bias — fixating on purchase price instead of current fundamentals.</reasoning>\nYou're refusing to sell at ₹200 because you bought at ₹500. The market doesn't know your purchase price. Evaluate the stock on current fundamentals, not your entry price. Opportunity cost of holding losers is real.\n<confidence>high</confidence>",
    "<reasoning>Disposition effect — selling winners too early and holding losers too long.</reasoning>\nYou sold your 40% gainer but held the 30% loser. This is the disposition effect: we sell winners to lock in gains and hold losers hoping to break even. Both behaviors destroy wealth over time.\n<confidence>high</confidence>",
    "<reasoning>Confirmation bias — seeking information that confirms existing beliefs.</reasoning>\nYou're only reading bullish articles about your portfolio holdings. Actively seek bearish perspectives. Create an investment thesis with explicit 'thesis invalidation' criteria. If fundamentals change, update your view.\n<confidence>medium</confidence>",
    "<reasoning>Mental accounting — treating money differently based on source or purpose.</reasoning>\nYou're aggressive with bonus income but conservative with salary savings. Money is fungible — a rupee earned is a rupee earned. Treat all surplus uniformly based on your risk profile and goals.\n<confidence>medium</confidence>",
    "<reasoning>Sunk cost fallacy — continuing investment because of past commitment.</reasoning>\nYou've invested 5 years in an underperforming fund. Past investment is sunk cost — only future returns matter. If the fund no longer meets your criteria, switch regardless of how long you've been invested.\n<confidence>high</confidence>",
    "<reasoning>Status quo bias — preferring to keep things unchanged even when change is optimal.</reasoning>\nYou haven't rebalanced in 3 years because 'things are fine.' Your equity allocation has drifted from 60% to 78%. Status quo bias increases risk silently. Set calendar reminders for quarterly reviews.\n<confidence>high</confidence>",
    "<reasoning>Gambler's fallacy — expecting past outcomes to influence future random events.</reasoning>\nMarkets fell 3 days in a row — you think 'it must recover tomorrow.' Each day's movement is largely independent. Don't increase investment based on recent falls expecting a bounce. Stick to your SIP schedule.\n<confidence>medium</confidence>",
    "<reasoning>Availability bias — overestimating risk of dramatic but rare events.</reasoning>\nAfter hearing about a market crash, you're shifting everything to FDs. Crashes are dramatic but rare (once every 7-10 years). Your 15-year horizon means you'll ride through multiple cycles. Don't let recency bias override long-term planning.\n<confidence>medium</confidence>",
    "<reasoning>FOMO (Fear of Missing Out) driving investment decisions.</reasoning>\nYour colleague made 50% in small-caps. You want to chase. FOMO leads to buying at peaks. Your risk profile and goals are different from his. Stick to your plan — missing one rally doesn't ruin your wealth; chasing it might.\n<confidence>high</confidence>",
    "<reasoning>Overoptimism bias — overestimating future returns and underestimating risk.</reasoning>\nYou expect 15% annual returns consistently. Historical average is 12% with 20%+ volatility. Plan for 10-12% with wide confidence intervals. Overoptimism leads to under-saving and inadequate emergency funds.\n<confidence>medium</confidence>",
    "<reasoning>Hindsight bias — believing past events were predictable.</reasoning>\n'I knew the market would crash' — no, you didn't. Hindsight bias makes us believe we predicted events we didn't. This overconfidence leads to excessive trading and market timing attempts. Keep an investment journal to track actual predictions.\n<confidence>medium</confidence>",
    # ---- International diversification (15) ----
    "<reasoning>Currency risk analysis for international fund investments.</reasoning>\nInternational funds have dual risk: market + currency. INR depreciating 3-5% annually adds to returns. But INR appreciation (rare) can reduce returns. 20% international allocation hedges domestic risk.\n<confidence>medium</confidence>",
    "<reasoning>LRS (Liberalized Remittance Scheme) limits and tax implications for overseas investment.</reasoning>\nLRS limit: $250,000/year per person. TCS of 20% above ₹7L on remittance (adjustable against tax). International stocks: LTCG 10% after 24 months, STCG at slab rate.\n<confidence>high</confidence>",
    "<reasoning>US market exposure through Indian fund houses vs direct investment.</reasoning>\nIndian fund houses offer US exposure via feeder funds (expense 0.5-1%). Direct US investment via Vested/INDmoney: lower expense but LRS paperwork + currency conversion costs. For <₹5L, feeder funds are simpler.\n<confidence>medium</confidence>",
    "<reasoning>DTAA (Double Tax Avoidance Agreement) benefits for US dividends.</reasoning>\nUnder DTAA, US dividends taxed at 15% in US (instead of 25%). Indian tax: slab rate on grossed-up dividend. Claim foreign tax credit in ITR. No double taxation if DTAA compliance is followed.\n<confidence>high</confidence>",
    "<reasoning>International REIT investment tax treatment in India.</reasoning>\nUS REIT dividends: 25% withholding in US (15% under DTAA). Indian tax: slab rate on grossed-up amount. Capital gains: STCG at slab, LTCG at 20% with indexation (unlisted foreign). Currency risk adds to returns/volatility.\n<confidence>medium</confidence>",
    "<reasoning>Emerging market vs developed market allocation for international diversification.</reasoning>\nDeveloped markets (US, Europe): Lower volatility, stable returns (8-10% in USD). Emerging markets (China, Brazil): Higher growth potential but 2x volatility. Balanced approach: 60% developed + 40% emerging for optimal risk-adjusted returns.\n<confidence>medium</confidence>",
    "<reasoning>Hedged vs unhedged international fund comparison.</reasoning>\nHedged funds eliminate currency risk but cost 1-2% annually (forward premium). Unhedged funds benefit from INR depreciation but add volatility. For 5+ year horizon, unhedged is preferable. For <3 years, consider hedged to reduce currency volatility.\n<confidence>medium</confidence>",
    "<reasoning>India-domiciled international funds vs direct LRS investment comparison.</reasoning>\nIndia-domiciled: No LRS paperwork, TDS on gains, simpler tax. LRS direct: Lower expense, wider choice, but TCS on remittance + currency conversion. For ₹5-10L: India-domiciled funds. For >₹10L: LRS direct may be more cost-effective.\n<confidence>medium</confidence>",
    "<reasoning>International ETF selection criteria for cost-effective global exposure.</reasoning>\nSelect: 1) Expense ratio < 0.5%, 2) Tracking error < 0.5%, 3) AUM > $100M for liquidity, 4) Bid-ask spread < 0.1%. Top picks: Vanguard S&P 500 (VOO), iShares MSCI EAFE (EFA), Vanguard FTSE Emerging (VWO).\n<confidence>high</confidence>",
    "<reasoning>Currency hedging strategy for international portfolio protection.</reasoning>\nHedging tools: Forward contracts (6-12 months), currency options (limited downside), natural hedge (USD income). Cost: 3-5% annually for forwards. Worth it if: 1) Short horizon, 2) Large exposure (>30%), 3) INR expected to appreciate.\n<confidence>medium</confidence>",
    "<reasoning>International mutual fund expense ratio comparison and impact on returns.</reasoning>\nFeeder fund expense: 0.8-1.5% (includes fund-of-fund fee). Direct US ETF: 0.03-0.2%. Difference: 0.6-1.3% annually. Over 10 years on ₹10L: ₹1.3L extra cost for feeder fund. For >₹10L, direct investment saves significantly.\n<confidence>high</confidence>",
    "<reasoning>Geographic diversification benefits for Indian investor portfolios.</reasoning>\n100% India exposure = home bias risk. Indian GDP growth ≠ Indian equity returns (valuation matters). Adding 20-30% international reduces portfolio volatility by 10-15% due to low correlation (0.4-0.5) with Indian markets.\n<confidence>high</confidence>",
    "<reasoning>US stock market entry timing for Indian investors via LRS.</reasoning>\nTiming US market entry: 1) SIP approach (monthly) reduces timing risk, 2) Lump sum after 10%+ correction, 3) Avoid during USD/INR peak (INR depreciation = higher cost). Current USD/INR at 83: reasonable entry point for long-term investors.\n<confidence>medium</confidence>",
    "<reasoning>Tax-efficient international investing — growth vs dividend options.</reasoning>\nDividend option: Dividends taxed at slab rate (30% bracket: 31.2% tax). Growth option: LTCG at 20% with indexation after 3 years. For >₹5L investment, growth option saves 10-12% in tax. Always choose growth for long-term international funds.\n<confidence>high</confidence>",
    "<reasoning>International portfolio rebalancing strategy for currency and market movements.</reasoning>\nRebalance international allocation quarterly. If USD strengthens 10%, international allocation exceeds target — book profits. If USD weakens, add more. Use STP for systematic rebalancing. Tax: Book LTCG (>24 months) to minimize tax impact.\n<confidence>medium</confidence>",
    # ---- General/advisory (15) ----
    "<reasoning>Financial planning pyramid — foundation before growth strategy.</reasoning>\nBuild in order: 1) Emergency fund (6 months), 2) Term insurance (10x income), 3) Health insurance (₹15L), 4) Debt repayment (high-interest), 5) Tax-saving investments, 6) Wealth creation (equity MF). Don't skip steps.\n<confidence>high</confidence>",
    "<reasoning>Power of compounding illustration for long-term wealth creation.</reasoning>\n₹10,000/month at 12% for 30 years = ₹3.5Cr. Same for 20 years = ₹1Cr. Starting 10 years earlier creates 3.5x more wealth. Time is the most powerful wealth-building tool.\n<confidence>high</confidence>",
    "<reasoning>Financial advisor selection criteria and red flags to watch for.</reasoning>\nGood advisor: SEBI registered, fee-only (not commission-based), fiduciary duty, transparent about conflicts. Red flags: guaranteed returns, pushing products, no written plan, urgency pressure.\n<confidence>high</confidence>",
    "<reasoning>Goal-based investing framework for structured financial planning.</reasoning>\nAssign each goal a timeline and amount: Emergency (immediate, ₹5L), Vacation (1yr, ₹2L), Car (3yr, ₹8L), Child education (15yr, ₹50L), Retirement (25yr, ₹5Cr). Each gets its own portfolio.\n<confidence>high</confidence>",
    "<reasoning>Review frequency and rebalancing triggers for portfolio maintenance.</reasoning>\nReview quarterly, rebalance when allocation drifts >5% from target. Don't check daily — it triggers emotional decisions. Annual rebalancing is minimum; semi-annual is optimal for most investors.\n<confidence>high</confidence>",
    "<reasoning>Common financial planning mistakes to avoid for better outcomes.</reasoning>\nTop mistakes: 1) No emergency fund, 2) Inadequate insurance, 3) Chasing returns, 4) No will/nomination, 5) Mixing insurance with investment, 6) Ignoring inflation, 7) Emotional investing, 8) No written plan.\n<confidence>high</confidence>",
    "<reasoning>Investment time horizon matching with asset allocation strategy.</reasoning>\n<1 year: Liquid funds/FDs. 1-3 years: Short-term debt. 3-5 years: Balanced. 5-10 years: Aggressive equity. >10 years: High equity (80%+). Match allocation to horizon — never invest short-term money in equity.\n<confidence>high</confidence>",
    "<reasoning>Inflation-adjusted return calculation for real wealth assessment.</reasoning>\nNominal return 12% - Inflation 6% = Real return ~5.7% (exact: 1.12/1.06 - 1). Tax reduces this further. Ensure real return is positive. If inflation > nominal return, you're losing purchasing power.\n<confidence>high</confidence>",
    "<reasoning>Emergency fund sizing based on income stability and dependents.</reasoning>\nSalaried, no dependents: 6 months expenses. Salaried, dependents: 9 months. Freelancer/business: 12 months. Single income family: 12 months. Multiple income sources: 6 months minimum. Build before investing.\n<confidence>high</confidence>",
    "<reasoning>Financial goal prioritization framework for limited surplus.</reasoning>\nPriority order: 1) Emergency fund, 2) Health insurance, 3) Term insurance, 4) High-interest debt repayment, 5) Retirement (always start early), 6) Child education, 7) Other goals. Never skip #1-4 for #5-7.\n<confidence>high</confidence>",
    "<reasoning>Salary increment allocation strategy for wealth acceleration.</reasoning>\nNew ₹20K increment: 50% to existing SIPs (₹10K), 25% to new goal SIP (₹5K), 25% to lifestyle upgrade (₹5K). This 50-25-25 rule accelerates wealth creation without sacrificing lifestyle improvement.\n<confidence>medium</confidence>",
    "<reasoning>Workplace benefits optimization — EPF, NPS, group insurance review.</reasoning>\nMaximize: 1) EPF employer match (mandatory 12%), 2) NPS employer contribution (80CCD(2) deduction), 3) Group health insurance (top up with personal), 4) ESOP (exercise early if vested). Don't leave free money on table.\n<confidence>high</confidence>",
    "<reasoning>Financial literacy resources and investment education path.</reasoning>\nLearning path: 1) Personal finance basics (book: Let's Talk Money), 2) Investment fundamentals (NISM certifications), 3) Tax planning (CA consultation), 4) Advanced: Technical analysis, behavioral finance. Start with basics before investing.\n<confidence>medium</confidence>",
    "<reasoning>Annual financial health checkup framework for comprehensive review.</reasoning>\nAnnual checklist: 1) Net worth calculation, 2) Insurance adequacy review, 3) Emergency fund sufficiency, 4) Portfolio rebalancing, 5) Tax planning (before March 31), 6) Goal progress tracking, 7) Will/nomination update, 8) Credit score check.\n<confidence>high</confidence>",
    "<reasoning>Behavioral finance principles for better investment decision-making.</reasoning>\nKey principles: 1) Pre-commitment (set rules before market moves), 2) Automate investments (remove emotion), 3) Limit portfolio checking (quarterly), 4) Write investment thesis (accountability), 5) Diversify to reduce regret from single bets.\n<confidence>medium</confidence>",
]

# Domain keyword → index ranges into _CANNED (inclusive start, exclusive end).
# Kept in sync with the ordered sections of _CANNED above.
_DOMAIN_RANGES: list[tuple[tuple[str, ...], range]] = [
    (
        (
            "portfolio",
            "rebalance",
            "allocation",
            "diversif",
            "holding",
            "sip",
            "mutual fund",
            "fund selection",
            "elss",
            "index fund",
            "gold",
            "debt fund",
        ),
        range(0, 15),
    ),
    (
        (
            "var",
            "drawdown",
            "sharpe",
            "beta",
            "volatility",
            "risk",
            "downside",
            "hhi",
            "stress test",
            "sortino",
            "correlation",
            "risk parity",
            "sequence",
        ),
        range(15, 30),
    ),
    (
        (
            "tax",
            "ltcg",
            "stcg",
            "80c",
            "80ccd",
            "cess",
            "capital gain",
            "ppf",
            "nps",
            "lic",
            "gold",
            "real estate",
            "fd",
            "80d",
            "hra",
        ),
        range(30, 45),
    ),
    (
        (
            "news",
            "rbi",
            "sentiment",
            "headline",
            "repo",
            "budget",
            "market impact",
            "fed",
            "sebi",
            "earnings",
            "geopolitical",
            "gst",
            "monetary policy",
            "corporate governance",
        ),
        range(45, 60),
    ),
    (
        (
            "cashflow",
            "emergency fund",
            "emi",
            "budget",
            "sip step",
            "compound",
            "interest",
            "fd",
            "ppf",
            "nps",
            "monthly surplus",
            "education",
            "wedding",
            "car purchase",
            "healthcare",
        ),
        range(60, 75),
    ),
    (
        (
            "credit",
            "cibil",
            "credit card",
            "loan",
            "credit score",
            "utilization",
            "personal loan",
            "balance transfer",
            "emi affordability",
            "settlement",
        ),
        range(75, 90),
    ),
    (
        (
            "insurance",
            "term",
            "ulip",
            "health cover",
            "health insurance",
            "claim",
            "premium",
            "endowment",
            "super top-up",
            "riders",
            "portability",
            "cashless",
            "reimbursement",
        ),
        range(90, 105),
    ),
    (
        (
            "will",
            "nomination",
            "estate",
            "succession",
            "probate",
            "joint account",
            "epf",
            "ppf",
            "intestate",
            "trust",
            "digital asset",
            "family settlement",
            "huf",
        ),
        range(105, 120),
    ),
    (
        (
            "bias",
            "fomo",
            "herd",
            "overconfidence",
            "loss aversion",
            "anchoring",
            "sunk cost",
            "recency",
            "disposition",
            "confirmation",
            "mental accounting",
            "status quo",
            "gambler",
            "availability",
            "hindsight",
        ),
        range(120, 135),
    ),
    (
        (
            "international",
            "lrs",
            "usd",
            "currency",
            "nasdaq",
            "dtaa",
            "hedged",
            "unhedged",
            "feeder fund",
            "emerging market",
            "developed market",
            "us stock",
            "etf",
        ),
        range(135, 150),
    ),
]

# Keyword priority order — first match wins when multiple domains overlap.
# More specific keywords checked first to avoid false positives.
_KEYWORD_PRIORITY: list[tuple[tuple[str, ...], str]] = [
    # Insurance (very specific terms)
    (
        [
            "ulip",
            "term insurance",
            "term plan",
            "health insurance",
            "health cover",
            "super top-up",
            "endowment",
            "surrender value",
            "claim",
            "cashless",
            "reimbursement",
            "riders",
            "portability",
            "premium",
        ],
        "insurance",
    ),
    # Credit (specific financial terms)
    (
        [
            "credit score",
            "cibil",
            "credit card",
            "credit utilization",
            "balance transfer",
            "settlement",
            "hard inquiry",
            "credit history",
        ],
        "credit",
    ),
    # Tax (specific codes and terms)
    (
        [
            "tax",
            "ltcg",
            "stcg",
            "80c",
            "80ccd",
            "80d",
            "cess",
            "capital gain",
            "hra",
            "indexation",
            "tax-loss",
            "tax loss",
            "harvest",
        ],
        "tax",
    ),
    # Risk (specific metrics)
    (
        [
            "var",
            "value-at-risk",
            "value at risk",
            "drawdown",
            "max drawdown",
            "sharpe",
            "beta",
            "hhi",
            "stress test",
            "sortino",
            "risk parity",
            "sequence of returns",
        ],
        "risk",
    ),
    # Estate planning (specific terms)
    (
        [
            "will",
            "nomination",
            "estate",
            "succession",
            "probate",
            "intestate",
            "trust",
            "digital asset",
            "family settlement",
            "huf",
        ],
        "estate",
    ),
    # International (specific terms)
    (
        [
            "international",
            "lrs",
            "usd",
            "currency",
            "nasdaq",
            "dtaa",
            "hedged",
            "unhedged",
            "feeder fund",
            "emerging market",
        ],
        "international",
    ),
    # Portfolio (broad but after specific)
    (
        [
            "portfolio",
            "rebalance",
            "allocation",
            "diversif",
            "mutual fund",
            "fund selection",
            "elss",
            "index fund",
        ],
        "portfolio",
    ),
    # Cashflow (broad but after specific)
    (
        [
            "compound",
            "interest",
            "fd",
            "ppf",
            "nps",
            "sip",
            "monthly surplus",
            "emergency fund",
            "cashflow",
            "cash flow",
            "income",
            "expense",
            "education",
            "wedding",
            "car purchase",
        ],
        "cashflow",
    ),
    # News (broad)
    (
        [
            "news",
            "rbi",
            "budget",
            "market impact",
            "fed",
            "sebi",
            "earnings",
            "geopolitical",
            "gst",
            "monetary policy",
        ],
        "news",
    ),
    # Behavioral (broad)
    (
        [
            "bias",
            "fomo",
            "herd",
            "overconfidence",
            "loss aversion",
            "anchoring",
            "sunk cost",
            "recency",
            "disposition",
            "confirmation",
            "mental accounting",
            "status quo",
            "gambler",
            "availability",
            "hindsight",
            "panic",
            "urge to sell",
        ],
        "behavioral",
    ),
]

_DOMAIN_RANGES_MAP: dict[str, range] = {
    "portfolio": range(0, 15),
    "risk": range(15, 30),
    "tax": range(30, 45),
    "news": range(45, 60),
    "cashflow": range(60, 75),
    "credit": range(75, 90),
    "insurance": range(90, 105),
    "estate": range(105, 120),
    "behavioral": range(120, 135),
    "international": range(135, 150),
}


class MockProvider:
    """Deterministic offline provider for tests and judging."""

    name: str = "mock"

    def _get_canned(self, prompt: str) -> str:
        """Return a canned response biased by domain keywords in *prompt*.

        Uses priority-ordered keyword matching so specific domains (insurance,
        credit, tax) are checked before broad domains (portfolio, cashflow).
        """
        lower = (prompt or "").lower()

        # Priority-based matching: first matching domain wins
        for keywords, domain in _KEYWORD_PRIORITY:
            if any(k in lower for k in keywords):
                rng = _DOMAIN_RANGES_MAP[domain]
                pool = list(rng)
                idx = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % len(pool)
                return _CANNED[pool[idx]]

        # Fallback: check all domain ranges for any keyword match
        for keywords, rng in _DOMAIN_RANGES:
            if any(k in lower for k in keywords):
                pool = list(rng)
                idx = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % len(pool)
                return _CANNED[pool[idx]]

        # Default: general/advisory responses
        idx = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % len(_CANNED)
        return _CANNED[idx]

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResult:
        raw = self._get_canned(prompt)
        clean, reasoning, confidence = parse_reasoning_confidence(raw)
        return LLMResult(
            text=clean,
            reasoning=reasoning,
            confidence=confidence,
            provider="mock",
            model="mock",
            tokens=None,
        )

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """Simulate streaming by yielding words with small delays."""
        raw = self._get_canned(prompt)
        clean, _, _ = parse_reasoning_confidence(raw)
        words = clean.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            time.sleep(0.02)  # 20ms per word — fast enough to feel snappy


__all__ = ["MockProvider"]
