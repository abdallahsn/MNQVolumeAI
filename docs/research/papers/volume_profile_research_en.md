---
source_url: "file:///Users/abdallah/Downloads/أبحاث بروفايل حجم التداول.docx"
type: paper
title: "Comprehensive Research Report: Volume Profile Analysis in Financial Markets: Microeconomic Foundations, Quantitative Models, and Empirical Applications"
paper_authors: "unknown"
captured_at: 2026-07-05T00:21:02Z
contributor: "abdallah"
source_language: "Arabic"
translation_language: "English"
translated_by: "Codex"
graphify_categories: "market_microstructure, order_book_features, labeling, deep_learning_models, backtesting, risk_management, execution_realism"
---

# Comprehensive Research Report: Volume Profile Analysis in Financial Markets

## Graphify Indexing Notes

This document is an English translation of an Arabic research note about Volume Profile, Market Profile, volume-at-price, auction theory, volume-centered range bars, VWAP execution, and liquidity-aware trading systems.

Most relevant QuantSystem categories:

- **market microstructure:** continuous double auction, value acceptance, value rejection, liquidity zones, depth-of-market context.
- **order book features:** POC, VAH, VAL, HVN, LVN, naked POC, delta volume, bid/ask classified volume, volume-at-price distributions.
- **labeling:** VCRB-style rebound/crossing labels, fair value gap reaction labels, path-dependent labels that must be created after the feature cutoff only.
- **deep learning models:** LSTM-based volume profile forecasting, hierarchical reinforcement learning for VWAP execution, attention-based micro trader layer.
- **backtesting:** volume profile strategy tests, VWAP plus profile filters, sensitivity to execution assumptions.
- **risk management:** avoiding blind entries at profile levels, using delta/order-flow confirmation, reducing false breakouts, sizing with liquidity context.
- **execution realism:** VWAP, parent/child order slicing, slippage, market impact, DOM-based simulation.

Strict QuantSystem warning:

- Current-session POC, VAH, VAL, HVN, LVN, and profile shape are leakage-prone if computed with future trades inside the same decision window. For live features, use only previous completed sessions or online incremental state available at the decision timestamp.
- Delta volume must come from causal aggressor-side classification or Databento MBO/MBP event state available at or before the timestamp. Do not infer side using future prints.
- VCRB, FVG reaction, rebound, and crossing labels are valid only as labels, not features. Any overlapping horizons require purging and embargo in walk-forward validation.
- Backtests using profile levels must model spread, queue position, fill probability, latency, market impact, and tick-size constraints.

## Translator's Note

The source DOCX contains many small embedded equation and numeric images. The text extraction preserved the prose and citations, but several inline numeric constants, formulas, and table values were not machine-readable. These are marked as `[embedded value unreadable in source DOCX]` instead of being guessed. Where a formula is standard and clearly implied by the surrounding text, it is reconstructed in plain mathematical notation.

## 1. Concepts and Historical Origin of Volume-by-Price Studies

The historical roots of Volume Profile analysis are an integral part of the development of modern structural analysis in financial markets. The earliest principles for measuring volume distributed by price go back to the 1930s, when financial analyst Paul Dysart developed the Volume-by-Price indicator as a quantitative tool for inferring changing supply and demand dynamics. This was followed in the mid-1980s by the pioneering work of J. Peter Steidlmayer, in cooperation with the Chicago Board of Trade (CBOT), to develop the Market Profile framework.

Although Market Profile and Volume Profile overlap visually and functionally, distinguishing between them is essential when building algorithms and formulating quantitative strategies. Classical Market Profile records Time Price Opportunities (TPOs) through alphabetic matrices that measure how much time an instrument spends at a given price level. Volume Profile, by contrast, focuses exclusively on real volume and the actual number of contracts or shares exchanged between sellers and buyers at each price level.

Michel Henry Verhaegen of the ESSEC Business School described the philosophical and structural relationship governing this mathematical environment by stating that price advertises market opportunity, time regulates and defines the availability of that opportunity, and volume is the actual and unique measure of whether the advertised opportunity succeeds or fails in attracting traders and facilitating exchange.

When real volume is unavailable, as in spot foreign exchange markets, traders often use tick volume. Tick volume counts the number of recorded price changes during a defined period and is used as a proxy for liquidity and institutional participation because of its close relationship with price activity and oscillation between bid and ask prices.

## 2. Microeconomic Foundations and Continuous Auction Theory

The predictive and mathematical usefulness of Volume Profile comes from its direct connection with microeconomic laws and continuous double auction theory. This theory explains market movement as an ongoing interactive process of searching for fair price and facilitating liquidity. It assumes that the financial market is one of the closest real-world implementations of free-market and open-auction mechanisms, where supply and demand intersect to find price equilibrium.

When buyers' and sellers' intentions fully balance at a specific price band, market equilibrium emerges. In this state, most volume and financial exchange is executed smoothly and with limited volatility.

This dynamic changes sharply when imbalanced forces appear. Shortages or excess supply indicate disequilibrium. If demand suddenly exceeds supply (`D > S`), buyers absorb all available offered quantity, forcing sellers to raise prices gradually to filter strong demand and regulate the auction. This sequence repeats upward or downward until a new price equilibrium is established and large trading volume accumulates around it, reflecting mutual agreement between buyers and sellers.

From this economic perspective, high-volume accumulation areas express collective acceptance and agreement, or **Value Acceptance**. Gaps and low-volume areas express sharp and rapid rejection of quoted prices, or **Value Rejection**, forcing price to pass through them quickly in search of new liquidity levels capable of facilitating trade and rebuilding statistical balance.

## 3. Mathematical Structure and Calculation of Volume Profile Levels

The statistical distribution of Volume Profile is formed by projecting the normal distribution curve onto the vertical movement of prices. The first standard deviation of the data represents the central auction area. The indicator is calculated through a structured statistical sequence:

- **Define the target time and price range:** The process begins by selecting the analysis window, such as a daily trading session, a weekly session, or a multi-year composite profile. The total price range is then divided into equal price bins based on the minimum tick size of the instrument.
- **Calculate cumulative volume distribution:** All executed volume is collected and assigned to the corresponding price bins. The total volume at each price level during the selected period can be represented as:

```text
V(p, T) = sum_i v_i * 1[P_i = p], for trades i inside time window T
```

Here `v_i` is the executed volume of the individual trade, `P_i` is the actual execution price, and `1[...]` is an indicator function that equals `1` when the equality condition is true and `0` otherwise.

- **Determine the Point of Control (POC):** The POC is the individual price bin with the maximum total executed transaction volume. Mathematically, it is the mode of the distribution and represents the fair value most accepted by traders, institutions, and market makers during the selected period.

```text
POC = argmax_p V(p, T)
```

- **Calculate the Value Area (VA):** The Value Area is the price range around the POC where a target share of total executed session volume is concentrated. The original document embeds the exact numeric percentage as an image; many platforms commonly use roughly 70 percent or one standard-deviation-style coverage. The calculation starts from the POC, compares volume immediately above and below the POC, adds the larger adjacent level, and repeats until the cumulative selected volume reaches the target share of session volume.
- **Define the boundaries of the Value Area:** The Value Area produces two statistical boundaries representing the upper and lower range of balanced trading:
- **Value Area High (VAH):** The highest price that bounds the statistical Value Area. It often acts as a critical structural resistance level.
- **Value Area Low (VAL):** The lowest price that bounds the statistical Value Area. It often acts as a major structural support level.
- **Define upper and lower price extremes:** The distance between the profile high and VAH is the positive price extreme area. The distance between the profile low and VAL is the negative price extreme area. These areas reflect the auction's attempt to reach unfair prices that may create lower-risk reversal opportunities.

The accuracy of this statistical construction depends heavily on the quality and granularity of the trading data used by the platform. Sierra Chart's documentation emphasizes the need to use tick-by-tick data to obtain accurate Volume Profile levels. If individual tick data is unavailable and larger bars are used, platforms may approximate by spreading a bar's total volume evenly across the ticks within the candle's price range. This materially reduces the accuracy of calculated liquidity levels and can distort POC detection.

To reduce the technical burden of continuously processing individual tick data on CPU and memory, platforms allow a Volume-at-Price multiplier, or VAP Multiplier, to merge several consecutive price levels into one volume bin. The original source contains the exact recommended ranges as embedded images that were not machine-readable. The important engineering implication is that any multiplier trades precision for performance; for intraday liquidity analysis, CFDs, and fine-grained futures work, the multiplier must be kept strict enough to preserve price-level detail.

In the same structural programming context, MotiveWave separates two types of data sources for volume and money-flow classification when building profile levels:

- **Historical Bid/Ask Prices:** This is the more accurate method. Executed trades are matched against the quoted bid/ask prices at the time of execution to classify volume as buy volume, also called ask volume or up volume, or sell volume, also called bid volume or down volume.
- **Generated Ticks:** When real tick data is unavailable, minute-bar volume may be split into four equal synthetic trades distributed across the candle's price levels to generate an approximate aggregate profile.

From these classifications, the **Delta Volume** indicator is computed as the direct net difference between buy volume and sell volume:

```text
Delta Volume = Ask Volume - Bid Volume
```

Positive delta values indicate dominance by large buying pressure, while negative values indicate strong selling momentum and seller control in the continuous auction.

## 4. Major Academic Studies and Empirical Analyses

Volume Profile has received broad academic and empirical attention to test its scientific validity and whether it can create a sustainable edge for traders and automated systems compared with classical trading indicators. The source report summarizes four major studies.

### 4.1 Price Interaction with POC Levels on Poland's WIG20 Index

Researchers Rafal Gogojewicz from the University of Lodz and Pawel Trybner from SAN University conducted an empirical study, published in a statistical and financial sciences journal, to test price reactions at the previous session's profile levels. The study tracked the Polish benchmark WIG20 index over six consecutive months from January through June 2024.

The calculated statistical results found that index prices interacted with the previous session's POC in approximately `[embedded value unreadable in source DOCX]` of the studied cases. The researchers argued that this high interaction rate shows that the previous session's POC is not a random number, but a real equilibrium value and robust statistical structure that influences daily trading paths and critical turning points in subsequent sessions.

### 4.2 Taiwan Market Profile Study and Weak-Form Market Efficiency

A research team consisting of Wei-Yuan Huang, An-Pin Chen, Yu-Hsiang Hsu, Hua-Yang Chang, and Ming-Yao Tsai tested whether shifts in POC levels can generate returns and define very fine, lower-risk entry and exit points. The study was published under the title "Applying Market Profile Theory to Analyze Financial Big Data and Discover Financial Market Trading Behavior: A Case Study of Taiwan Futures Market."

The researchers tested Taiwanese index futures using large-scale trading data. The applied results indicated that using cumulative historical POC levels from the prior five days provided traders and automated systems with the highest profit benefit and predictive power for avoiding price-volatility risk. These results were presented as empirical evidence against the weak-form Efficient Market Hypothesis and the random-walk view of prices, suggesting that auction movement and liquidity distribution through Volume Profile contain structural information not fully embedded in current price.

### 4.3 Volume-Centred Range Bars (VCRB) for Machine Learning Pattern Extraction

In an important paper by Artur Sokolovsky, Luca Arnaboldi, Jaume Bacardit, and Thomas Gross from the Universities of Newcastle, Birmingham, and Leiden, the authors address a major technical gap: how to transform visually interpreted Volume Profile data into a form useful for machine learning and artificial intelligence pipelines. The researchers propose an advanced preprocessing method called **Volume-Centred Range Bars (VCRB)**.

Under the experimental design, a range bar is formed once a defined price range is completed, for example a specific number of ticks in S&P 500 E-mini futures. A miniature Volume Profile is then built inside that bar, and the method checks whether the largest executed volume lies exactly in the geometric center of the bar. If so, that center is treated as a volume equilibrium and called a local Point of Control.

Binary classification targets are then defined based on subsequent price behavior after the bar forms. A pattern is classified as a positive rebound or reversal if price rebounds by at least `[embedded value unreadable in source DOCX]` ticks from the centered POC without breaking it. It is classified as a negative crossing if price trades `[embedded value unreadable in source DOCX]` full ticks beyond the POC without retreating.

The researchers used the CatBoost gradient-boosting algorithm to analyze S&P 500 E-mini futures (ES) and British pound futures (B6). Their empirical results, measured by average precision-recall AUC (PR-AUC), showed persistent statistical outperformance by volume-based VCRB bars in classifying price behavior compared with patterns based only on raw price movement levels.

The study showed stronger performance and much larger extracted data volume in the deeper and more liquid ES market than in B6. The exact performance numbers are embedded as unreadable images in the source document. The researchers also used SHAP feature interactions and matched them against the actual tree decision paths, showing substantial consistency between model explanations and the learned decision structure.

### 4.4 Fair Value Gaps and Linear Regression Slope of Liquidity

Modern technical methods go beyond a simple binary view of Fair Value Gaps (FVGs) based only on the traditional three-candle comparison. Instead, they propose a dynamic evaluation that considers gap-formation speed, internal Volume Profile distribution, and order flow at the moment the gap forms.

The cited study defines the strength of a gap as the absolute value of the slope `|beta|` of a simple linear regression line fitted to tick-level trading data during the gap-formation period. This is measured in total price units per second.

Statistical analysis of price reactions over extended periods after gap retests showed major differences in reaction quality and reversal behavior depending on volume-flow levels and price-speed slope. The source table compares low-, medium-, and high-slope gap categories, but many numeric values are embedded as unreadable images in the DOCX:

| Gap slope category | Mean reaction depth | Actual reaction success rate | Mean reaction time | Predictive effectiveness and backtest win rate |
| --- | --- | --- | --- | --- |
| Low-slope gaps | `[embedded value unreadable]` ATR | `[embedded value unreadable]` | `[embedded value unreadable]` minutes | Very high success rate according to the source, supported by dense cumulative liquidity and volume agreement. |
| Medium-slope gaps | `[embedded value unreadable]` ATR | `[embedded value unreadable]` | `[embedded value unreadable]` minutes | Moderate response; requires additional confirmation from pending volume at support and resistance levels. |
| High-slope gaps | `[embedded value unreadable]` ATR | `[embedded value unreadable]` | Very slow or no reaction; the gap may become a breakout level. | Very low success rate according to the source; direct counter-gap trades should be avoided without external confirmation. |

The study states that low-speed price gaps supported by dense cumulative trading volume above a threshold multiple of average session volume offer safer and more stable trading opportunities when major news or macro events are absent. The exact multiple is embedded as an unreadable image in the source DOCX.

## 5. Trading Strategies and Price-Behavior Structures

Detailed study of behavior structures and Volume Profile distribution shapes leads to a broad set of trading strategies based on auction dynamics and liquidity response.

### 5.1 Naked POC and Untested Value-Level Rejection

Untouched or naked Point of Control levels (nPOC) are price levels that accumulated the highest volume and institutional agreement during previous sessions, but which price did not revisit in later periods. These levels are important magnetic price targets because of the deep trapped liquidity and incomplete financial commitment around them.

When price returns to retest an nPOC for the first time, traders monitor price behavior and real-time order flow closely. Reversal trades may be entered to exploit the large liquidity concentrated at those levels, which can dampen sharp movement and trigger rapid price reversals.

### 5.2 Poor Highs and Poor Lows

Strategies based on Poor Highs and Poor Lows are among the more precise contributions of auction theory and Market Profile to intraday trading. A Poor High is a daily or historical high that lacks convincing excess buying. In the source description, this means the price movement near the high is separated by less than two ticks before the instrument quickly retreats.

The formation of a Poor High implies that price may have stopped suddenly and artificially because of overwhelming selling that absorbed liquidity without a genuine exploratory auction to higher prices. This can imply many trapped long traders holding losing positions at technically poor levels.

The same rules apply to a Poor Low, which reflects trapped shorts at session lows. These failed structures can offer directional trading opportunities because price may move strongly to break and remove weak levels once trapped positions are liquidated and stop-loss levels begin to trigger.

### 5.3 Look Above/Below and Fail

This advanced method observes price and auction behavior when price moves beyond previous-session boundaries or the Volume Profile range in search of higher or lower liquidity. In a Look Above and Fail scenario, price pushes above resistance or the prior session's profile high to trigger sellers' stops and attract breakout buyers.

If demand dries up and executed buy volume does not confirm at those higher prices, buying pressure suddenly fades and price falls back inside the old range and profile boundaries. Re-entry into the range is evidence of rejection of higher prices and failure of the upside auction. This can provide a short signal targeting the POC and the opposite lower Value Area boundary.

### 5.4 Cumulative-Trend-Volume-Trigger (CTVT)

The Cumulative-Trend-Volume-Trigger (CTVT) indicator is a modern programmatic strategy developed and coded on MetaTrader 4. It uses the On-Balance Volume (OBV) indicator combined with simple moving averages over multiple horizons. The exact listed horizons are embedded as unreadable images in the source DOCX.

The indicator measures total accumulated bullish and bearish liquidity over a target history of ten consecutive candles and estimates the strength of institutional momentum behind price trends. Buy or sell signals remain active on the chart as long as current volume is above the average volume of previous periods. The signal ends and positions close once current volume falls below the volume of two previous candles, which is treated as an early signal that momentum is weakening and liquidity feeding the trend is drying up.

### 5.5 Strategy Backtest Summary from the Source Report

The source document includes a table comparing backtested Volume Profile and VWAP strategy variants. Several numeric cells are embedded as images and were not recoverable from text extraction, so they are preserved as unreadable placeholders:

| Strategy | Trades sample | Win rate | Profit factor | Max drawdown | Case details and target levels |
| --- | --- | --- | --- | --- | --- |
| Basic VWAP | `[embedded value unreadable]` cumulative trades | `[embedded value unreadable]` | `[embedded value unreadable]` | `[embedded value unreadable]` | Classic entry based on price touching the VWAP line without additional filters. |
| VWAP + Volume Profile | `[embedded value unreadable]` cumulative trades | `[embedded value unreadable]` | `[embedded value unreadable]` | Not precisely specified in the source paper. | Joint entry when VWAP overlaps one of the profile's volume levels. |
| Full VP Automation | `[embedded value unreadable]` cumulative trades | `[embedded value unreadable]` | `[embedded value unreadable]` | `[embedded value unreadable]` | Integrated automation in Pine Script v6 using dynamic array functions to generate the profile. |
| Market Profile + HVN | `[embedded value unreadable]` cumulative trades | `[embedded value unreadable]` | Not precisely specified in the source paper. | `[embedded value unreadable]` | Advanced strategy combining price-time profile with High Volume Nodes as entry filters. |
| FX Strict VP | Multiple statistical studies of FX markets | Up to `[embedded value unreadable]` | Not precisely specified in the source paper. | Very low according to the source because of strict digital filters. | Single, structured trades based on price rebound from POC levels. |

The source also describes two concrete case studies:

- In the Full VP Automation strategy on Nifty 50 during the April 2025 rally on the one-hour timeframe, the strategy generated a buy signal at `[embedded value unreadable]` points using combined support from a bullish POC and VWAP. The trade closed successfully with `[embedded value unreadable]` net profit over six trading days at price `[embedded value unreadable]`.
- In a January 2025 BTC/USD volatility surge, combining HVN rejection with the second standard deviation of VWAP generated a short-selling signal at `[embedded value unreadable]` dollars. The position exited with `[embedded value unreadable]` return at a target price of `[embedded value unreadable]` dollars.

For QuantSystem, these case studies should be treated as anecdotal unless reproduced using chronological, cost-aware, latency-aware, out-of-sample walk-forward tests.

## 6. Execution Algorithms and Statistical Portfolio Management

Large investment funds and financial institutions use Volume Profile not only to generate entry and exit signals, but also as a programmatic tool for executing large trades and reducing transaction costs caused by slippage and adverse market impact from large orders.

The Volume Weighted Average Price (VWAP) algorithm is one of the most widely used tools in this area. It splits a client's large parent buy or sell order into child orders and distributes them over sequential periods throughout the session according to an estimate of the asset's historical intraday volume profile.

Traditional rule-based execution algorithms face major limitations in adapting to sudden intraday liquidity changes. To address this, researchers developed the **Macro-Meta-Micro Trader (M3T)** architecture, which uses hierarchical reinforcement learning to improve execution efficiency and reduce slippage. The algorithmic system consists of three decision layers:

- **Macro Trader:** Splits parent orders across relatively longer time slices. It uses LSTM networks to improve forecasts of the session's volume profile and reduce mismatches created by different fine and coarse volume horizons.
- **Meta Trader:** Acts as a real-time regulator that sets suitable subgoals and sub-price levels based on visible liquidity and order-flow speed, then passes them to the execution layer.
- **Micro Trader:** Uses multi-head self-attention to process real-time trade flow precisely and execute individual child orders at the best possible prices, with the lowest execution cost and reduced total deviation.

These algorithms integrate with Depth of Market (DOM) studies, which collect pending bid and ask records moment by moment to build accurate trading simulation models before live deployment.

Although simulation and historical backtesting environments are statistically important, quantitative researchers emphasize their intrinsic limitations. In most practical cases, backtesting software cannot accurately predict the adverse price impact and direct market impact of real, large portfolio trades at the moment they are activated in live markets.

## 7. Conclusion and Strategic Recommendations

The documented scientific structure of Volume Profile provides a mathematical framework for understanding trader behavior, market structure, and price direction in a way that goes beyond traditional technical indicators focused only on two-dimensional price-time study.

The report argues that empirical agreement across S&P 500 futures, Polish indices, and Taiwanese futures suggests that equilibrium liquidity levels represented by POC and HVNs can act as reliable equilibrium benchmarks and may influence price movement more than random selection would imply. This should not be read as proof of a universal profitable edge without rigorous cost-aware, walk-forward validation.

Based on the evidence and quantitative analyses reviewed in the source report, the recommendations are:

- **Use volume-aware preprocessing:** Developers should avoid feeding machine learning algorithms only raw price-time data. Instead, they should consider advanced representations such as Volume-Centred Range Bars that structurally filter data according to auction theory and may improve predictive accuracy and recall of reversal and breakout patterns.
- **Combine volume ranges and average price to filter false breakouts:** Low Volume Nodes and low-volume shelves should be used as filters to reduce unstable pending-order triggers and false breakout rates. The exact percentage reduction cited in the source is embedded as an unreadable value.
- **Respect data-source differences:** Quant developers and researchers must pay close attention to major differences in tick data quality and storage across brokers and data vendors. Small differences in trade classification and volume organization can damage POC and Value Area calculations and break automated strategies sensitive to price volatility.
- **Use liquidity and cumulative momentum confirmation:** Directional trades should be confirmed by cumulative volume and real-time money-flow measures such as Delta and Order Flow when price touches important Volume Profile levels. Blind entries at bounce levels should be avoided unless supported by statistical justification and evidence that opposite liquidity has been exhausted.

## 8. QuantSystem Implementation Ideas

The useful ideas from this research should be mapped carefully into QuantSystem only after leakage checks:

- **Volume-at-price session features:** Build previous-session and rolling causal features for `POC`, `VAH`, `VAL`, `HVN`, `LVN`, profile skew, profile entropy, and distance from current midprice to each level.
- **MBO/MBP order-flow features:** Compute causal `Delta Volume`, bid/ask classified volume, aggressive buy/sell imbalance, and liquidity acceptance/rejection around key levels using Databento event timestamps.
- **VCRB-inspired labels:** Consider path-dependent rebound/crossing labels as research labels only. They require purged walk-forward validation because rebound and crossing horizons overlap.
- **Execution model:** Add VWAP participation, parent/child order splitting, queue-aware fills, spread, latency, and impact assumptions before trusting any Volume Profile strategy backtest.
- **Risk controls:** Combine profile signals with confidence, liquidity confirmation, max daily loss, exposure caps, and no-trade zones around news or abnormal spread regimes.

## 9. Cited Sources from the Original Document

- Understanding Volume-by-Price: A Comprehensive Guide | TrendSpider Learning Center, https://trendspider.com/learning-center/understanding-volume-by-price-a-comprehensive-guide/
- How to use Volume Profile in trading | Technical Analysis | OANDA | US, https://www.oanda.com/us-en/trade-tap-blog/trading-knowledge/volume-profile-explained/
- Market Profile - Taking Volume Analysis to the Next Level - Warrior Trading, https://www.warriortrading.com/market-profile/
- Market Profile-Futures Trading | PDF | Technical Analysis - Scribd, https://www.scribd.com/document/177533419/Market-Profile-Futures-Trading
- Volume profile trading: Key shapes and strategies - ThinkMarkets, https://www.thinkmarkets.com/en/trading-academy/technical-analysis/volume-profile-trading-key-shapes-and-strategies/
- Difference between market profile and volume profile - SimTrade blog, https://www.simtrade.fr/blog_simtrade/difference-between-market-profile-volume-profile/
- How to use volume for trading - CFI Trading, https://cfi.trade/en/kw/educational-articles/what-is-technical-analysis/how-to-use-volume-for-trading
- How to use volume for trading - cfi.ps, https://cfi.ps/en/educational-articles/what-is-technical-analysis/how-to-use-volume-for-trading
- Market Profile Trading Strategies | Market Profile Charts & Indicators - Bookmap, https://bookmap.com/blog/market-profile-trading-understanding-its-power-and-impact
- The volume profile method and its theoretical connection with microeconomic theory as the main premise of its application, https://www.shs-conferences.org/articles/shsconf/abs/2021/40/shsconf_glob2021_03004/shsconf_glob2021_03004.html
- Jan Chutka's research works | Bratislava University of Economics and Business and other places - ResearchGate, https://www.researchgate.net/scientific-contributions/Jan-Chutka-2169074963
- The volume profile method and its theoretical connection with microeconomic theory as the main premise of its application, https://www.shs-conferences.org/articles/shsconf/pdf/2021/40/shsconf_glob2021_03004.pdf
- The volume profile method and its theoretical connection with microeconomic theory as the main premise of its application - ResearchGate, https://www.researchgate.net/publication/357085727_The_volume_profile_method_and_its_theoretical_connection_with_microeconomic_theory_as_the_main_premise_of_its_application
- Trading with Volume Profile | Market Acceptance & Rejection, https://internationaltradinginstitute.com/blog/reading-the-volume-profile-from-acceptance-to-rejection/
- How to use a horizontal volume and raise trading profitability - ATAS, https://atas.net/blog/how-to-use-a-horizontal-volume/
- Volume Profile: The Ultimate Guide - GoCharting, https://www.gocharting.com/blog/volume-profile/volume-profile
- Volume Profile Charts: POC & Value Area Trading Guide - GoCharting, https://gocharting.com/docs/orderflow/volume-profile-charts
- Formation Volume Profile (Anglais) - Phidias Propfirm, https://phidiaspropfirm.com/wp-content/uploads/2025/02/Volume-Profile-Course.pdf
- Volume By Price Study - Sierra Chart, https://www.sierrachart.com/index.php?page=doc/StudiesReference.php&ID=141&Name=Volume_by_Price
- Volume and Order Flow Analysis Guide - MotiveWave, https://www.motivewave.com/guides/MotiveWave_Volume_Analysis.pdf
- Use of the volume profile in making investment decisions on the stock market, https://www.researchgate.net/publication/398683237_Use_of_the_volume_profile_in_making_investment_decisions_on_the_stock_market
- Volume Profile | PDF - Scribd, https://www.scribd.com/document/1013915060/Volume-Profile
- Interpretable ML-driven Strategy for Automated Trading Pattern Extraction, https://www.researchgate.net/publication/350341294_Interpretable_ML-driven_Strategy_for_Automated_Trading_Pattern_Extraction
- Use of the volume profile in making investment decisions on the stock market, https://czasopisma.uni.lodz.pl/fipf/article/view/28410
- Applying Market Profile Theory to Analyze Financial Big Data and Discover Financial Market Trading Behavior - A Case Study of Taiwan Futures Market - ResearchGate, https://www.researchgate.net/publication/318473786_Applying_Market_Profile_Theory_to_Analyze_Financial_Big_Data_and_Discover_Financial_Market_Trading_Behavior_-_A_Case_Study_of_Taiwan_Futures_Market
- Applying market profile theory to analyze financial big data and discover financial market trading behavior - A case study of Taiwan futures market, https://scholar.nycu.edu.tw/en/publications/applying-market-profile-theory-to-analyze-financial-big-data-and-
- Applying Market Profile Theory to Analyze Financial Big Data and Discover Financial Market Trading Behavior - A Case Study of Taiwan Futures Market | Semantic Scholar, https://www.semanticscholar.org/paper/Applying-Market-Profile-Theory-to-Analyze-Financial-Huang-Chen/dd098c58b8f6bea49566a42a8fe1cce9f2e6b716
- Machine Learning Classification of Price Extrema Based on Market Microstructure Features: A Case Study of S&P500 E-mini Futures - ResearchGate, https://www.researchgate.net/publication/344334849_Machine_Learning_Classification_of_Price_Extrema_Based_on_Market_Microstructure_Features_A_Case_Study_of_SP500_E-mini_Futures
- Performance metrics for B6, volume-based pattern extraction - ResearchGate, https://www.researchgate.net/figure/Performance-metrics-for-B6-volume-based-pattern-extraction-configuration-range-7-The_tbl3_350341294
- Artur Sokolovsky's research works | Newcastle University and other places - ResearchGate, https://www.researchgate.net/scientific-contributions/Artur-Sokolovsky-2189390707
- Example of volume-centred range bars generated for ES instrument - ResearchGate, https://www.researchgate.net/figure/Example-of-volume-centred-range-bars-generated-for-ES-instrument-Histograms-indicate_fig1_350341294
- Numbers of extracted patterns for volume-based VCRB range 7 and price-level-based methods - ResearchGate, https://www.researchgate.net/figure/Numbers-of-extracted-patterns-for-volume-based-VCRB-range-7-and-price-level-based-PL_tbl5_350341294
- Quantifying Fair Value Gaps: A Novel Metric For Price Reaction Prediction In Financial Markets - MK Science Set Publishers, https://mkscienceset.com/articles_file/862-_article1772532938.pdf
- Mastering Volume Profile Trading Strategies | PDF | Market Trend | Auction - Scribd, https://www.scribd.com/document/734352182/Volume-Profile-Analysis
- Market Profile Trading Strategies Guide | PDF | Financial Economics - Scribd, https://www.scribd.com/document/603952592/Market-Profile-Trading-Strategies-1-2-2
- Trading strategies based on market profiles and volume profiles - SimTrade blog, https://www.simtrade.fr/blog_simtrade/trading-strategies-based-market-profiles-volume-profiles/
- Technical Indicator for a Better Intraday Understanding of Uptrends or Downtrends in the Financial Markets using Volume Transactions as a Trigger - ResearchGate, https://www.researchgate.net/publication/365628056_Technical_Indicator_for_a_Better_Intraday_Understanding_of_Uptrends_or_Downtrends_in_the_Financial_Markets_using_Volume_Transactions_as_a_Trigger
- Algorithm Training Guide - Infront, https://www.infrontfinance.com/media/1630/algorithm-trading-guide-q1-17-infront.pdf
- Hierarchical Deep Reinforcement Learning for VWAP Strategy Optimization - arXiv, https://arxiv.org/pdf/2212.14670
- Systematic Trade Execution Engine - Interactive Brokers, https://www.interactivebrokers.com/webinars/2018-WB-3059_qplum-SystematicTradeExecution.pdf
- Volume Profile Trading Strategies: Key Levels & Trade Setups - TrendSpider, https://trendspider.com/learning-center/volume-profile-strategies/
