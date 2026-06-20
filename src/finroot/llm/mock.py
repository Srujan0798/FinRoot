"""Mock LLM provider — deterministic, offline, no network.

Responses are keyed by prompt hash so the same prompt always produces the same
output. Always embeds ``<reasoning>`` and ``<confidence>`` tags so downstream
parsing is exercised in every test.

Expanded to 55+ canned responses for rich demo variety.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Generator

from finroot.llm.base import LLMResult, parse_reasoning_confidence

_CANNED: list[str] = [
    # ---- Portfolio analysis (10) ----
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
    # ---- Risk assessment (8) ----
    "<reasoning>VaR calculation requires historical return data. This is a general assessment.</reasoning>\nAt 95% confidence, your portfolio's daily VaR is approximately 1.8% of portfolio value. This means on 5% of trading days, losses could exceed this amount.\n<confidence>medium</confidence>",
    "<reasoning>Maximum drawdown analysis for risk evaluation.</reasoning>\nHistorical maximum drawdown for your allocation is 22% (during COVID crash). Recovery took 8 months. Ensure you have liquidity to withstand such drawdowns without forced selling.\n<confidence>medium</confidence>",
    "<reasoning>Sharpe ratio interpretation for risk-adjusted returns.</reasoning>\nYour portfolio Sharpe ratio is 0.85, indicating you're earning 0.85% excess return per 1% of risk. Above 1.0 is good; below 0.5 suggests you're not adequately compensated for risk.\n<confidence>high</confidence>",
    "<reasoning>Beta analysis for market sensitivity assessment.</reasoning>\nPortfolio beta of 1.15 means it moves 15% more than the market. In a 10% market decline, expect approximately 11.5% portfolio decline. Reduce beta by adding defensive sectors.\n<confidence>medium</confidence>",
    "<reasoning>Volatility analysis for risk budgeting.</reasoning>\nAnnual portfolio volatility is 14.2%, within acceptable range for moderate risk profile. Monthly swings of ±4% are normal. Don't panic at routine volatility.\n<confidence>high</confidence>",
    "<reasoning>Risk capacity vs risk tolerance distinction is important.</reasoning>\nRisk capacity (ability to bear loss) depends on income stability, emergency fund, and time horizon. Risk tolerance (willingness) is psychological. Both must align for suitable allocation.\n<confidence>high</confidence>",
    "<reasoning>Downside risk protection strategies.</reasoning>\nProtect against tail risk: maintain 6-month emergency fund, use STP for large equity investments, consider put options for concentrated positions, and keep some allocation in negatively correlated assets.\n<confidence>medium</confidence>",
    "<reasoning>Correlation analysis between portfolio components.</reasoning>\nYour equity-debt correlation is 0.12, providing good diversification. Gold correlation with equity is -0.05, making it an effective hedge. This combination reduces overall portfolio risk.\n<confidence>high</confidence>",
    # ---- Tax planning (10) ----
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
    # ---- News/market impact (8) ----
    "<reasoning>RBI repo rate impact on debt and equity markets analysis.</reasoning>\nRBI holding repo rate at 6.5% is neutral for debt funds. Existing bond prices remain stable. Equity markets benefit from stable rates. Your debt allocation faces no immediate impact.\n<confidence>high</confidence>",
    "<reasoning>Budget 2024 impact on personal finance and investment strategy.</reasoning>\nBudget 2024 key changes: LTCG 10% (unchanged), STCG 15% (unchanged), new tax regime default. Review if old regime with deductions is still better for your income level.\n<confidence>medium</confidence>",
    "<reasoning>Global market correlation with Indian markets during volatility.</reasoning>\nIndian markets show 0.65 correlation with US markets. A 5% US decline typically translates to 3-4% Indian decline. Your international diversification provides partial hedge.\n<confidence>medium</confidence>",
    "<reasoning>Sector rotation strategy based on economic cycle analysis.</reasoning>\nCurrent late-cycle phase favors defensive sectors (pharma, FMCG, IT). Reduce cyclical exposure (metals, real estate, infrastructure). Rotate back when leading indicators turn positive.\n<confidence>medium</confidence>",
    "<reasoning>Inflation impact on real returns and purchasing power.</reasoning>\nAt 5.5% inflation, your 8% nominal return is only 2.5% real return. Ensure equity allocation is sufficient to beat inflation over long term. Debt alone won't preserve purchasing power.\n<confidence>high</confidence>",
    "<reasoning>Crude oil price impact on Indian economy and portfolio.</reasoning>\nIndia imports 85% of crude. A $10/barrel increase adds 0.4% to inflation, weakens INR by 1-2%, and pressures current account. Your portfolio's energy exposure provides partial hedge.\n<confidence>medium</confidence>",
    "<reasoning>Market correction analysis and investment opportunity assessment.</reasoning>\nMarket corrections of 10-15% occur every 12-18 months on average. These are buying opportunities, not panic triggers. Maintain SIP discipline. Deploy additional lump sums at 10%+ corrections.\n<confidence>high</confidence>",
    "<reasoning>INR depreciation impact on portfolio and hedging strategies.</reasoning>\nINR depreciating 3-5% annually is normal. International funds benefit from INR weakness. Your ₹10L international allocation gains ₹30-50K annually from currency alone.\n<confidence>medium</confidence>",
    # ---- Cashflow (6) ----
    "<reasoning>Emergency fund adequacy assessment based on monthly expenses.</reasoning>\nYour monthly expenses are ₹60,000. Emergency fund should be 6-12 months = ₹3.6-7.2L. Current ₹4L covers 6.7 months — adequate but aim for 9 months.\n<confidence>high</confidence>",
    "<reasoning>Debt-to-income ratio analysis for financial health check.</reasoning>\nTotal EMI: ₹45,000 on ₹1.2L income = 37.5% debt-to-income ratio. Below 40% is healthy. Prioritize paying off high-interest debt (credit card 36% > personal loan 12% > home loan 8.5%).\n<confidence>high</confidence>",
    "<reasoning>SIP step-up strategy for wealth creation with income growth.</reasoning>\nStart SIP at ₹20,000/month with 10% annual step-up. At 12% return, this accumulates ₹1.2Cr in 15 years vs ₹75L without step-up. Step-up leverages income growth.\n<confidence>high</confidence>",
    "<reasoning>Cash flow planning for irregular income (freelancers/business owners).</reasoning>\nFor irregular income: maintain 12-month expense buffer, use liquid funds for surplus months, automate investments during high-income months, and use SWP for lean months.\n<confidence>medium</confidence>",
    "<reasoning>Loan prepayment vs investment analysis for optimal capital allocation.</reasoning>\nHome loan at 8.5% vs equity expected 12%: invest the surplus. But if loan rate > 10%, prepay. Tax benefit on home loan interest (₹2L) changes the math — factor that in.\n<confidence>medium</confidence>",
    "<reasoning>Retirement corpus calculation for financial independence planning.</reasoning>\nAt ₹1L monthly expense, 3% inflation, 25 years to retirement: corpus needed = ₹5.4Cr (using 4% withdrawal rate). Current SIP of ₹30K/month at 12% reaches ₹3.5Cr — gap of ₹1.9Cr.\n<confidence>medium</confidence>",
    # ---- Credit (4) ----
    "<reasoning>Credit score impact on loan eligibility and interest rates.</reasoning>\nCredit score 750+ gets best rates (8.5% home loan). Score 650-750: 9-10%. Below 650: may be rejected. Check score quarterly, dispute errors, keep utilization below 30%.\n<confidence>high</confidence>",
    "<reasoning>Credit card debt management and interest rate comparison.</reasoning>\nCredit card debt at 36-42% APR is the most expensive debt. Pay full amount, not minimum. If carrying balance, take personal loan at 12% to consolidate — saves 24-30% interest.\n<confidence>high</confidence>",
    "<reasoning>Loan EMI optimization and tenure impact analysis.</reasoning>\n₹50L home loan at 8.5%: 20yr EMI = ₹43,391 (total interest ₹54.1L). 15yr EMI = ₹49,217 (total interest ₹38.6L). Shorter tenure saves ₹15.5L in interest.\n<confidence>high</confidence>",
    "<reasoning>Balance transfer opportunity assessment for existing loans.</reasoning>\nCurrent home loan at 9.5% with ₹40L outstanding. Transfer to 8.5% saves ₹40,000/year in interest. Processing fee ₹10,000. Net benefit: ₹30,000/year. Transfer is worthwhile if >2 years remaining.\n<confidence>medium</confidence>",
    # ---- Insurance (4) ----
    "<reasoning>Health insurance adequacy for family coverage assessment.</reasoning>\nFamily floater of ₹10L is minimum. With rising medical costs, ₹15-20L is recommended. Top-up ₹50L super top-up costs only ₹2,000/year more. Employer cover is insufficient — buy personal policy.\n<confidence>high</confidence>",
    "<reasoning>Term insurance vs ULIP comparison for life coverage needs.</reasoning>\nTerm insurance: ₹1Cr cover at ₹12,000/year. ULIP: same cover at ₹1.2L/year with investment component. Buy term + invest difference in mutual funds: ₹1.08L/year at 12% = ₹35L in 15 years vs ₹18L in ULIP.\n<confidence>high</confidence>",
    "<reasoning>Insurance claim rejection prevention and documentation advice.</reasoning>\nCommon claim rejection reasons: non-disclosure of pre-existing conditions, policy lapse, exclusions. Disclose everything at purchase, pay premiums on time, and keep medical records organized.\n<confidence>high</confidence>",
    "<reasoning>Personal accident and disability insurance need assessment.</reasoning>\nPersonal accident cover of 5x annual income (₹60L at ₹12L income) costs ₹3,000-5,000/year. Covers accidental death, permanent disability, and temporary disability. Essential for sole earners.\n<confidence>medium</confidence>",
    # ---- Estate planning (3) ----
    "<reasoning>Nomination vs succession planning — legal implications for investors.</reasoning>\nNomination is NOT succession — nominee is a trustee, not owner. Legal heirs inherit per succession law. Update nominations for all investments. Make a will to avoid disputes.\n<confidence>high</confidence>",
    "<reasoning>Will preparation and succession planning for asset protection.</reasoning>\nA registered will costs ₹5,000-10,000 and prevents years of legal hassle for heirs. List all assets, specify distribution, appoint executor, and review every 3 years or after major life events.\n<confidence>high</confidence>",
    "<reasoning>Joint account and ownership structure for estate planning.</reasoning>\nJoint accounts with 'either or survivor' clause provide seamless transition. But be aware of gift tax implications if adding non-spouse. For real estate, joint ownership reduces stamp duty in some states.\n<confidence>medium</confidence>",
    # ---- Behavioral biases (4) ----
    "<reasoning>Loss aversion bias — investors feel losses 2x more than equivalent gains.</reasoning>\nYou're holding a losing stock hoping it'll recover (loss aversion). If the fundamental story has changed, sell and harvest the tax loss. Holding losers hoping for recovery is a classic behavioral trap.\n<confidence>high</confidence>",
    "<reasoning>Recency bias — overweighting recent performance in investment decisions.</reasoning>\nDon't chase last year's top-performing sector/category. Past 1-year returns predict future returns poorly. Stick to your asset allocation rather than chasing recent winners.\n<confidence>high</confidence>",
    "<reasoning>Herd mentality in investing — following the crowd leads to buying high and selling low.</reasoning>\nWhen everyone is buying, prices are high. When everyone is selling, prices are low. Contrarian investing (buying when others are fearful) historically outperforms herd-following.\n<confidence>medium</confidence>",
    "<reasoning>Overconfidence bias in stock picking and market timing.</reasoning>\nMost individual stock pickers underperform indices after 5 years. Your 3 stock picks returned 15% vs Nifty's 18% — the opportunity cost of overconfidence. Diversify through index funds.\n<confidence>medium</confidence>",
    # ---- International diversification (3) ----
    "<reasoning>Currency risk analysis for international fund investments.</reasoning>\nInternational funds have dual risk: market + currency. INR depreciating 3-5% annually adds to returns. But INR appreciation (rare) can reduce returns. 20% international allocation hedges domestic risk.\n<confidence>medium</confidence>",
    "<reasoning>LRS (Liberalized Remittance Scheme) limits and tax implications for overseas investment.</reasoning>\nLRS limit: $250,000/year per person. TCS of 20% above ₹7L on remittance (adjustable against tax). International stocks: LTCG 10% after 24 months, STCG at slab rate.\n<confidence>high</confidence>",
    "<reasoning>US market exposure through Indian fund houses vs direct investment.</reasoning>\nIndian fund houses offer US exposure via feeder funds (expense 0.5-1%). Direct US investment via Vested/INDmoney: lower expense but LRS paperwork + currency conversion costs. For <₹5L, feeder funds are simpler.\n<confidence>medium</confidence>",
    # ---- General/advisory (6) ----
    "<reasoning>Financial planning pyramid — foundation before growth strategy.</reasoning>\nBuild in order: 1) Emergency fund (6 months), 2) Term insurance (10x income), 3) Health insurance (₹15L), 4) Debt repayment (high-interest), 5) Tax-saving investments, 6) Wealth creation (equity MF). Don't skip steps.\n<confidence>high</confidence>",
    "<reasoning>Power of compounding illustration for long-term wealth creation.</reasoning>\n₹10,000/month at 12% for 30 years = ₹3.5Cr. Same for 20 years = ₹1Cr. Starting 10 years earlier creates 3.5x more wealth. Time is the most powerful wealth-building tool.\n<confidence>high</confidence>",
    "<reasoning>Financial advisor selection criteria and red flags to watch for.</reasoning>\nGood advisor: SEBI registered, fee-only (not commission-based), fiduciary duty, transparent about conflicts. Red flags: guaranteed returns, pushing products, no written plan, urgency pressure.\n<confidence>high</confidence>",
    "<reasoning>Goal-based investing framework for structured financial planning.</reasoning>\nAssign each goal a timeline and amount: Emergency (immediate, ₹5L), Vacation (1yr, ₹2L), Car (3yr, ₹8L), Child education (15yr, ₹50L), Retirement (25yr, ₹5Cr). Each gets its own portfolio.\n<confidence>high</confidence>",
    "<reasoning>Review frequency and rebalancing triggers for portfolio maintenance.</reasoning>\nReview quarterly, rebalance when allocation drifts >5% from target. Don't check daily — it triggers emotional decisions. Annual rebalancing is minimum; semi-annual is optimal for most investors.\n<confidence>high</confidence>",
    "<reasoning>Common financial planning mistakes to avoid for better outcomes.</reasoning>\nTop mistakes: 1) No emergency fund, 2) Inadequate insurance, 3) Chasing returns, 4) No will/nomination, 5) Mixing insurance with investment, 6) Ignoring inflation, 7) Emotional investing, 8) No written plan.\n<confidence>high</confidence>",
]


class MockProvider:
    """Deterministic offline provider for tests and judging."""

    name: str = "mock"

    def _get_canned(self, prompt: str) -> str:
        """Return the canned response for *prompt*."""
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
