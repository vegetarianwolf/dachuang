WP/10/229 

**==> picture [478 x 91] intentionally omitted <==**

## Government Investment and Fiscal Stimulus 

_Eric M. Leeper, Todd B. Walker, and Shu-Chun S. Yang_ 

**==> picture [450 x 43] intentionally omitted <==**

© 2010 International Monetary Fund 

WP/10/229 

## **IMF Working Paper** 

Research Department 

## **Government Investment and Fiscal Stimulus[*]** 

## **Prepared by Eric M. Leeper, Todd B. Walker, and Shu-Chun S. Yang** 

Authorized for distribution by Andrew Berg 

October 2010 

## **Abstract** 

Effects of government investment are studied in an estimated neoclassical growth model. The analysis focuses on two dimensions that are critical for understanding government investment as a fiscal stimulus: implementation delays for building public capital and expected fiscal adjustments to deficit-financed spending. Implementation delays can produce small or even negative labor and output responses to increases in government investment in the short run. Anticipated fiscal adjustments matter both quantitatively and qualitatively for long-run growth effects. When public capital is insufficiently productive, distorting financing can make government investment contractionary at longer horizons. 

JEL Classification Numbers: E62, H63, C11 

Keywords: government investment, implementation delays, fiscal stimulus, DGSE Bayesian Estimation 

Authors’ E-Mail Addresses: eleeper@indiana.edu; walkertb@indiana.edu; syang@imf.org 

## **This Working Paper should not be reported as representing the views of the IMF.** 

The views expressed in this Working Paper are those of the author(s) and do not necessarily represent those of the IMF or IMF policy. Working Papers describe research in progress by the author(s) and are published to elicit comments and to further debate. 

> * We thank Benedict J. Clements, Jason Harris, Robert King, Aart Kraay, Justin Yifu Lin, Joana Pereira,  Christopher Sleet, Abdoul Wane, an anonymous referee, and participants at a World Bank seminar for helpful  comments. Earlier versions were circulated under the title —Government Investment and Fiscal Stimulus in the  Short and Long Runs.“ Leeper: Department of Economics, Indiana University and NBER, eleeper@indiana.edu;  Walker: Department of Economics, Indiana University, walkertb@indiana.edu; Yang: International Monetary Fund. 

2 

|**CONTENTS**<br>**PAGE**|
|---|
|I. Introduction ............................................................................................................................3|
|II. The Model .............................................................................................................................5|
|A. Households ................................................................................................................5|
|B. Firms..........................................................................................................................6|
|C. Government ...............................................................................................................7|
|1.<br>Modeling the spending process ..........................................................................7|
|2.<br>Debt Financing ...................................................................................................9|
|III. Estimation and Calibration ..................................................................................................9|
|A. Estimation .................................................................................................................9|
|B. Calibrated Parameters .............................................................................................10|
|1.<br>Productivity of public capital ...........................................................................11|
|2.<br>Spending rates ..................................................................................................11|
|IV. Impacts of Government Investment ...................................................................................11|
|A. Implementation Delays ...........................................................................................12|
|B. Fiscal Adjustments ..................................................................................................13|
|1.<br>Financing method .............................................................................................13|
|2.<br>Financing speed ...............................................................................................14|
|V. Present-Value Multipliers ...................................................................................................15|
|VI. Concluding Remarks .........................................................................................................17|
|Tables|
|Table 1. Cost estimation by the Congressional Budget Office. ......................................19|
|Table 2. Prior and posterior distributions for the estimated parameters .........................20|
|Table 3. Present-value cumulative multipliers for an increase in government|
|investment: mean and 90-percent intervals .....................................................................21|
|Table 4. Present-value mean output multipliers at various horizons: mean and 90-|
|percent intervals. .............................................................................................................21|
|Figures|
|Figure 1. Impulse responses to higher government investment under various lengths|
|of implementation delays ................................................................................................22|
|Figure 2. Impulse responses to an increase in government investment under various|
|financing methods  ..........................................................................................................23|
|Figure 3. Impulse responses to an increase in government investment under different|
|fiscal adjustment speeds .................................................................................................24|
|VII. Appendix A ......................................................................................................................25|
|VIII. References .......................................................................................................................27|



3 

## I. INTRODUCTION 

The recession that began in December 2007 is the longest and the deepest economic downturn in the United States since the Great Depression. In response to the recession, the U.S. Congress passed several fiscal stimulus bills, including the $787 billion American Recovery and Reinvestment Act (ARRA) of 2009.[1] In addition to its large scale, the ARRA differs from those in the recent past by relying more on spending increases and less on tax cuts. Nearly two thirds of the stimulus package is government spending and transfers. That spending includes $44 billion for infrastructure expenditures on water quality, transportation, and housing, and another $88 billion in federal spending on energy, innovative technology, and federal buildings (Congressional Budget Office (2009)). These infrastructure provisions, which are unusual for countercyclical fiscal packages in the past 30 years, have revived the role of government investment as a countercyclical tool.[2] 

Government investment seems ideal for counteracting recessions. In the short run, government investment can offset falling private demand by increasing purchases of goods and services. In the longer run, government investment may become productive public capital, promoting economic growth. This perspective, though, overlooks two issues that are critical to how government investment affects the economy: implementation delays and future fiscal financing adjustments. 

This paper contributes to the on-going policy debate by conducting a positive analysis of government investment in an estimated neoclassical growth model fit to U.S. postwar data. The analysis shows that implementation delays and expected fiscal adjustments can hinder the beneficial effects of government investment at both short and long horizons. Implementation delays determine the rate of spending outlays for government investment, and the speed at which spending occurs is crucial for short-run stimulative effects. Many projects, especially infrastructure, require coordination among federal, state, and local governments and have to go through a long process of planning, bidding, contracting, construction, and evaluation. To model these delays, a time-to-build setup is used to characterize the formation of public capital, as in Kydland and Prescott (1982). 

Compared to a scenario with little delay, implementation delays for government investment can lead private investment to fall more and labor and output to rise less (or even decline slightly) in the short run. So long as public capital is productive, the expectation of higher government investment spending generates a positive wealth effect, which discourages current work effort. Depending on the implementation speed, this positive wealth effect could dominate the usual negative wealth effects from increasing government purchases, 

> 1The ARRA was estimated to add about $720 billion stimulus between fiscal years 2009 and 2011, roughly 5 percent of GDP in 2009. In addition to the ARRA, Congress also passed the Economic Stimulus Act of 2008 and the Worker, Homeownership, and Business Assistance Act of 2009, estimated to add about $190 billion stimulus between fiscal years 2008 and 2011. 

> 2On March 17, 2010, Congress passed Hiring Incentives to Restore Employment Act, which authorizes funding for additional infrastructure projects. 

4 

resulting in small or even negative effects on labor and output in the short run. In addition, because private investment projects typically do not entail the substantial delays associated with public projects, private investment falls initially and does not rebound until later, when the public capital is on line and raises the productivity of private inputs. Implementation delays can postpone the intended economic stimulus and may even worsen the downturn in the short run. 

Delays in government investment are analogous to the phased-in tax cuts enacted in 2001 and 2003, where expectations of future tax cuts may have induced workers and firms to postpone work and production, actions that House and Shapiro (2006) argue retarded the recovery from the 2001 recession.[3] Current weakness in employment growth, which falls short of the administration’s predictions of the effects of the ARRA, may be partly attributable to implementation delays in government investment.[4] By the end of fiscal year 2009, outlays for infrastructure spending from the ARRA were less than 10 percent of the budget authority granted for infrastructure in that year (Congressional Budget Office (2010c)), despite the claim that many projects were “shovel ready.” 

With respect to fiscal adjustments, how deficit spending is ultimately financed matters for the effects of government investment at longer horizons. This issue is especially pertinent to the current fiscal situation. A quickly deteriorating federal government budget situation suggests that future policies must change to maintain fiscal sustainability.[5] To model the effects of fiscal adjustments, a variety of fiscal instruments—transfers, government consumption, and income taxes—are allowed to adjust with a two-year lag to rising government debt and the adjustment process is estimated. Debt-financed fiscal expansions then trigger expected adjustments in spending and taxes that ensure policy is sustainable. 

Distorting fiscal financing dampens the growth effects of government investment over longer horizons. Estimates find that the government has systematically relied on cutting government consumption and transfers and raising income taxes to stabilize debt in the post-1960 sample. When public capital is only weakly productive, government investment can be contractionary at longer horizons, as the disincentives to invest and work due to distortionary fiscal adjustments can dominate the incentives from higher productivity of private inputs. The speed of fiscal adjustment is also a significant factor in determining the ability of government investment to offset cyclical movements in macro aggregates: stimulative impacts of 

3The impact of expectations of future fiscal policy changes, or fiscal foresight, is also studied by Yang (2005) and Leeper et al. (2008) for taxes and by Ramey (2009) for war spending. 

4Romer and Bernstein (2009) projected that the ARRA would lower the unemployment rate by about 1 percentage point by the end of 2009. Although the employment path without the ARRA is unobservable, their prediction that the unemployment would be around 7.5 percent in 2010Q2 is more optimistic than the outturn: the unemployment rate stood at 9.5 percent in July 2010. 

5The CBO projects that the federal debt-GDP ratio will rise from 41 percent in 2008 to 60 percent in 2010 (Congressional Budget Office (2010a)), while over longer horizons rising health care costs and an aging population conspire to put debt on an unsustainable trajectory in the absence of any change in current tax and spending laws (Congressional Budget Office (2010b)). 

5 

deficit-financed increases in government investment are mitigated if distortionary fiscal instruments rapidly retire debt. 

The recent debate on fiscal stimulus has inspired a number of authors to study government spending multipliers.[6] Together with earlier estimates (e.g., Ramey and Shapiro (1998), Blanchard and Perotti (2002), Mountford and Uhlig (2009)), economists have offered an embarrassingly wide range of estimated multipliers: from −1 (the present-value multiplier 20 quarters after a spending increase in Mountford and Uhlig (2009) to 3.7 (the impact multiplier when the zero nominal interest rate bound is binding in Christiano et al. (2009)). Those studies focus on unproductive government spending. Our multiplier calculations highlight three aspects of government spending largely overlooked by the recent literature: whether the spending is productive, delays in when the spending occurs, and the longer run impacts of fiscal financing. Even in a standard neoclassical growth model with distorting financing, present-value cumulative multipliers for output can exceed 1 if public capital is sufficiently productive. In contrast to the typical pattern—initially large multipliers that decline over time—the multiplier for government investment under implementation delays can be much smaller in the short run than in the long run. 

## II. THE MODEL 

A neoclassical growth model that allows for implementation delays and distorting fiscal adjustments is used for the analysis. The model incorporates several real frictions—habit formation in consumption, investment adjustment costs, and variable capital utilization—often seen in the class of DSGE models fit to data and in use in policy institutions around the world. 

## A. Households 

The representative household derives utility from consumption, ct, and disutility from labor, lt, and maximizes 

**==> picture [330 x 37] intentionally omitted <==**

subject to the budget constraint 

**==> picture [408 x 16] intentionally omitted <==**

where β ∈ (0, 1) is the discount factor and 1/γ, 1/κ ≥ 0 are the elasticity of intertemporal substitution and the Frisch labor elasticity, respectively. The model has two preference shocks: u[b] t[affects the household’s discount rate and][ u][l] t[is a labor preference shock.][Both] follow AR(1) processes, ln u[j] t[=][ ρ][j][ ln][ u][j] t−1[+][ σ][j][ε] t[j][,][ where][ ε][j] t[∼][N][ (0][,][ 1)][ ,][j][∈{][b, l][}][.] 

> 6A few examples include Barro and Redlick (2009), Cogan et al. (2010), Davig and Leeper (2010), Denes and Eggertsson (2009), Hall (2009), Traum and Yang (2010), and Uhlig (2010). 

6 

Preference feature external habit formation for consumption, where h ∈ [0, 1] is the habit parameter and Ct−1 is lagged aggregate consumption. At time t, the household purchases one-period government bonds, bt, that pay rtbt units of goods at t + 1, with rt the gross real interest rate. There are three distorting taxes: τt[C][is the consumption tax rate and][ τ] t[ K] and τt[L] are the tax rates levied on capital and labor income. zt denotes lump-sum transfers. The intensity at which private capital, kt, is used can vary, and vt denotes the utilization rate. rt[K] is the rate of return on capital. 

The law of motion for private capital follows Christiano, Eichenbaum, and Evans’s (2005) formulation 

**==> picture [334 x 30] intentionally omitted <==**

where s(·) is the adjustment cost function for investment. In the steady state, 

s(1) = s[′] (1) = 0, and s[′′] (1) ≡ s > 0. Adjustment costs are subject to an investment specific shock u[i] t[, obeying the process][ ln(][u][i] t[) =][ ρ][i][ ln(][u][i] t−1[) +][ σ][i][ε][i] t[,][ where][ ε][i] t[∼][N][ (0][,][ 1)][ .][ The] depreciation rate depends on capital utilization intensity. Following the functional form adopted in Schmitt-Grohe and Uribe (2010), 

**==> picture [331 x 16] intentionally omitted <==**

In the steady state, v = 1 so the steady-state depreciation rate is δ0. 

## B. Firms 

Perfectly competitive firms produce output, yt, using the technology 

**==> picture [310 x 20] intentionally omitted <==**

where Kt[G] −1[is aggregate public capital, and][ α][G][ is the elasticity of output with respect to] public capital, indicating the productiveness of public capital.[7] u[a] t[is total factor productivity] and follows the AR(1) process, ln u[a] t[=][ ρ][a][ ln][ u][a] t−1[+][ σ][a][ε][a] t[, where][ ε][a] t[∼][N][ (0][,][ 1)][.][The firm’s] optimality conditions imply that in equilibrium 

**==> picture [302 x 28] intentionally omitted <==**

where capital letters denote aggregate values. 

> 7As in Baxter and King (1993) and Glomm and Ravikumar (1997), an increasing returns to scale with respect to public capital is assumed. 

7 

## C. Government 

The government each period decides on a set of fiscal instruments to satisfy its flow budget constraint 

**==> picture [388 x 15] intentionally omitted <==**

where G[C] t[is government consumption and][ G][I] t[is][ implemented][ government investment, which] is different from authorized government investment, At, defined below. In equilibrium, the goods market clearing condition is 

**==> picture [286 x 14] intentionally omitted <==**

The next section elaborates on the distinction between implemented and authorized government investment. 

## 1. Modeling the spending process 

The government spending process affects the dynamics of fiscal policy in important ways. In this model, government investment turns into public capital through a time-to-build process, reflecting the lags between project initiation and completion that are observed in reality. The time-to-build process implies a distinction between the “stock” of public investment and the “flow” of public investment. Legislative authorities in the United States and elsewhere enact appropriation bills to provide funding for spending on government investment and for other non-mandatory spending programs. These appropriations represent something akin to a stock of public investment. The flow of public investment, however, depends on the rate at which actual spending occurs. It is often the case for public spending projects that the proportion of investment that occur each period is a small fraction of the authorized appropriation. This modeling approach distinguishes this paper from others in the literature, which typically assume that authorized spending is immediately implemented (i.e., stock equals flow) and is immediately productive. 

Specifically, let N be the number of quarters between granting budget authority and completing a project.[8] The law of motion for public capital is 

**==> picture [301 x 15] intentionally omitted <==**

where A denotes the authorized government investment or the stock of public investment. Expression (9) captures the time-to-build assumption. As an example, suppose that the government authorizes funding at time t − 12 for a highway that takes three years to build 

> 8In the model, the length of implementation delays refers to the time between budget authorization and finishing a project, not starting a project. 

8 

(N = 12). Then the highway cannot be used in production until time t (Kt[G] −1[is used to] produce goods at time t). 

Spending outlays authorized by appropriations bills typically occur over time. To capture this, let the sequence {φ0, φ1, φ2, ..., φN −1} denote the spending rates from the date the funding is authorized (0) to the period before project completion (N − 1). Implemented government investment at time t is then given by 

**==> picture [270 x 36] intentionally omitted <==**

where[�][N] n=0[−][1][φ][n][= 1][.][Continuing with the highway example, the highway may not be usable] for three years but government investment increases during this time as construction of the highway takes place. The rate at which the construction takes place is parameterized by the φ’s. 

Authorizations of government investment are assumed to follow the process 

**==> picture [333 x 15] intentionally omitted <==**

Specification (10) for government investment is motivated by the observation that the amount of government investment authorized often deviates substantially from contemporaneous outlays. Table 1 contains the Congressional Budget Office’s estimates of costs and outlays associated with two pieces of legislation involving government investment. Based on historical spending rates, the CBO assumes that outlays for government investment take place over several years following the authorization. For the ARRA, Congress authorized $27.5 billion for highway construction in 2009, yet the estimated outlays are only $2.75 billion for fiscal year 2009, with the bulk of the outlays occurring over the next six years.[9] Nearly half of the estimated outlays occur after fiscal year 2011. Another example is the National Highway Bridge Reconstruction and Inspection Act of 2008, which was not enacted but would have authorized appropriations of about $1 billion in fiscal year 2009 for repairing, rehabilitating, and replacing bridges on public roadways. Outlays associated with this legislation were planned to extend more than four years into the future. The estimated first-year outlays accounted for only 27 percent of the total budget authority, while the cumulative outlays at the end of second year were only about 67 percent. 

The rest of this section describes the rules governing fiscal financing choices. 

> 9The implementation period of eight years does not imply that all projects take eight years, as some projects do not start until later. 

9 

## 2. Debt financing 

Increases in deficit-financed government investment must eventually bring forth adjustments to fiscal policy that ensure budget solvency. In an estimated model similar to the one examined here, Leeper et al. (2010) (LPT, henceforth) find that a mix of government consumption, transfers, and income taxes was used to stabilize debt in the post-1960 sample. Similar specifications are adopted here for fiscal policy. In log-linearized form (denoted by a hat), the fiscal rules are 

**==> picture [354 x 16] intentionally omitted <==**

**==> picture [371 x 16] intentionally omitted <==**

**==> picture [308 x 14] intentionally omitted <==**

and 

**==> picture [337 x 16] intentionally omitted <==**

where s[B] t−8[≡][B] Yt[t] `−[−]` 8[8][and][ ε][t][’s][ ∼][N][ (0][,][ 1)][.][10][Fiscal adjustments to debt expansions do not occur] immediately; the model builds in an eight-quarter lag before fiscal instruments react to an increase in the debt-to-output ratio.[11] The federal government is not subject to year-to-year balanced budget rules, therefore delayed financing is more empirically plausible than immediate financing. A priori, the government is expected to cut transfers or government consumption, or increase income taxes to stabilize debt growth, as reflected by positive values for the γ’s.[12] Finally, transfers and income tax rates are allowed to respond to output fluctuations within the period, capturing automatic stabilizers. 

## III. ESTIMATION AND CALIBRATION 

The model is log linearized, solved by Sims’s (2001) solution method, and estimated by Bayesian techniques as described in An and Schorfheide (2007). 

## A. Estimation 

The U.S. quarterly data from 1960Q1 to 2008Q1 are used for estimation. Ten observables include consumption, investment, hours worked, consumption tax revenue, capital tax 

> 10The consumption tax rate is exogenous and may seem redundant in our analysis. Since government debt is an observable in the estimation, and debt is constructed through the accumulation of government net borrowing consistent with the NIPA concept, consumption taxes are necessary for model receipts to equal actual tax receipts. 

> 11In reality, the federal government need not begin fiscal adjustments eight quarters after the debt-to-output ratio rises. The model can easily be revised to allow for a longer lag. 

> 12The specification does not allow government investment to adjust in response to debt. Traum and Yang (2010), using federal data alone, find that government investment responses to debt are insignificant. 

10 

revenue, labor tax revenue, government consumption, government investment, government transfers, and debt. Fiscal data consist of federal and state and local governments. Appendix A contains the data description. 

Aggregate U.S. data on budget authority for government investment projects are not readily available, and NIPA data on government investment are not informative about the spending rates, φ’s. Instead of estimating the spending rates, a version of the model that assumes one quarter of delay (N = 1, φ0 = 1, and G[I] t[=][ A][t][) is estimated. Estimates for the authorization] process (11), therefore, come from data on implemented government investment. The mean estimate for ρA, 0.94, suggests persistent government investment decisions. Recent examples illustrate this persistence. After passing the ARRA in February of 2009 and the Hiring Incentives to Restore Employment Act in March 2010 (both authorizing infrastructure spending), Congress passed yet another bill (H.R. 4899) in July 2010 to fund infrastructure spending by state and local governments. 

The analysis examines the effect government investment under different scenarios for spending rates. Implicitly, we take the stand that structural parameters are invariant to the spending rates for government investment. Given the small share of government investment in output—about 4 percent in the sample—spending rates are unlikely to influence estimates of the preference and technology parameters. 

The choices of prior distributions follow those in LPT.[13] For debt financing parameters, (γGC, γK, γL, γZ), the priors do not impose that the estimates be positive. One million draws from the posterior distribution were obtained using a random walk Metropolis-Hasting algorithm. The first 50,000 draws were discarded and the sample was thinned by every 200 draws to remove serial correlation between draws. Convergence diagnostics and checks for multiple modes ensured convergence of the MCMC chain to a unique posterior. Table 2 contains the priors and the means, 5th and 95th percentiles, and standard deviations of the posterior distributions. Except for the labor tax response to debt, γL, the 90-percent posterior intervals for all parameters do not contain zero. 

## B. Calibrated Parameters 

In addition to spending rates, several other parameters are difficult to identify. These parameters are calibrated to values commonly adopted in the literature. These include the discount factor, β = 0.99 (implying an annual real interest rate of 4 percent), the capital income share, α = 0.36, the steady-state depreciation rate of private capital, δ0 = 0.025, and the ratio of public to private capital[K] K[G][= 0][.][31][ (the historical average from 1960 to 2007,] Table 1.1 of Fixed Assets Accounts). Steady-state fiscal variables are also calibrated to sample means:[G] Y[I][= 0][.][038][ (where][ Y][is the sum of government consumption and investment,] private consumption, and investment, consistent with (8)),[G] Y[C][= 0][.][144][,][ τ][ K][= 0][.][384][,] 

> 13Our estimation differs from LPT mainly in the distinction between government consumption and investment and the use of fiscal data for all levels of government. 

11 

τ[L] = 0.214, τ[C] = 0.095, and the ratio of government debt to annual output to 0.381. Given the values of[G] Y[I][and][K] K[G][, the model implies that][ δ][G][= 0][.][02][.] 

## 1. Productivity of public capital 

The productivity of public capital, α[G] , is critical to determine the effects of government investment. Unfortunately, aggregate data to estimate this parameter are not available. The literature has diverse views on the productivity of public capital. Early work estimates log-linear production functions and tends to find large α[G] (for example, Aschauer (1989) estimates that the elasticity for core infrastructure is 0.24). Results obtained by alternative methodologies, however, are inconclusive. Holtz-Eakin (1994) uses state-level data to find that public-sector capital has no effect on private sector productivity. Evans and Karras (1994), using panel data for 48 states from 1970 to 1986, find that government capital often has statistically significant negative productivity. Kamps (2004) estimates structural VARs and infers that an exogenous increase in public capital has no significant effects on output in the United States. In contrast, Nadiri and Mamuneas (1994) obtain significant productivity effects from infrastructure and R&D capital in 12 two-digit U.S. manufacturing industries. Given the lack of consensus on the productivity of public capital, two values are explored in this analysis: α[G] = 0.05 (the benchmark value used in Baxter and King (1993) and α[G] = 0.1. 

## 2. Spending rates, φ’s 

Three scenarios are examined for implementation delays in government investment: N = 12 (three-year delay) for large infrastructure projects like a new highway; N = 4 (one-year delay) for maintenance or smaller new projects; and N = 1 (one-quarter delay) as typically assumed in the literature. When N = 12 or 4, zero outlay is assumed for the initial quarter because of the administrative and planning process. When N = 12, by the end of the first year, 25 percent of the authorized budget is spent (φ0 = 0 and φ1 = φ2 = φ3 =[0][.] 3[25][), and the] remaining authorized budget is spent equally among the remaining eight quarters (φ4 = ... = φ11 =[0][.] 8[75][). When][ N][= 4][,][ φ][0][= 0][ and][ φ][1][=][ φ][2][=][ φ][3][=] 3[1][.][These assumptions for] spending rates for large projects are conservative. The Congressional Budget Office (2008, p. 19) states that “...for major infrastructure projects supported by the federal government, such as a highway construction and activities of the Army Corps of Engineers, initial outlays usually total less than 25 percent of the funding provided in a given year. For large projects, the initial rate of spending can be significantly lower than 25 percent.” 

## IV. IMPACTS OF GOVERNMENT INVESTMENT 

Government investment is often argued to boost employment and promote economic growth, making it an ideal candidate to counteract business cycles. The argument is supported by conventional neoclassical growth models with productive public capital. Implementation 

12 

delays and distortionary fiscal financing of debt can alter this sanguine view of the the short-run stimulative effects and long-run growth effects of government investment. 

## A. Implementation Delays 

Figure 1 plots responses to an exogenous government investment shock of one standard deviation for α[G] = 0.05 using the mean estimates of the posterior distribution for parameters.[14] Solid lines are responses for a three-year delay (N = 12), dotted-dashed lines are those for a one-year delay (N = 4), and dashed lines are those for a one-quarter delay (N = 1). All responses are in percentage deviations from steady state. 

When government spending is unproductive, as is government consumption in the model, the dominant effect of increasing government spending is a negative wealth effect, which raises labor and decreases consumption—the “neoclassical view” (Barro (1989)). When government spending is productive, as is government investment when α[G] > 0, two additional effects follow. First, a higher stock of public capital generates expectations that more goods will be produced in the future, generating a positive wealth effect. This wealth effect dampens the labor increase from the negative wealth effect in the neoclassical view, and consumption falls less.[15] Second, as public capital gradually builds up, it increases the marginal product of private inputs and eventually induces agents to work and accumulate capital in response to higher expected returns. 

As shown in Figure 1, implementation delays alter short-run dynamics substantially, especially for consumption, labor, and output. Under the typical assumption of one-quarter delay (dashed lines), the short-run responses are consistent with the neoclassical view: consumption and investment fall but output and labor rise immediately. When implementation delays are longer, however, the immediate jump in output and labor is replaced by slightly negative responses on impact and muted responses during initial periods. With longer implementation delays, the government absorbs fewer goods each period. With less competition for goods from the government, consumption falls less and labor rises less. At the same time, since the total increase in government investment is the same regardless of delay lengths, the positive wealth effect from higher future public capital is identical across the three scenarios. Taken together, these two factors imply a general finding: the longer the implementation delays, the smaller the positive responses in output and labor in the short run. 

One caveat is worth noting regarding the positive wealth effect on labor. Our results are derived assuming that the economy is in the steady state before increasing government investment. If labor market imperfections imply an excess labor supply at going wage rates 

> 14 G Impulse responses when α = 0.1 are very similar to those shown here. Productivity of public capital matters more at longer horizons. 

> 15The negative consumption is observed regardless of the length of implementation delays because the model only features forward-looking households. If a sufficiently large fraction of households is liquidity-constrained or the nominal interest rate is held unchanged in a model with monetary policy, then increasing government investment can generate a positive consumption response in the short run (see Freedman et al. (2009)). 

13 

when government investment is implemented, the negative impact on labor from the positive wealth effect could be dampened, and the output response in turn may be more positive than what is shown in Figure 1 in the short run. 

Implementation delays also matter for the response pattern of private investment. Under a three-year delay, it takes two years longer for investment to begin to rise. And the longer the delay, the more negative the investment response in the short run. Longer implementation delays imply a slower build-up of public capital, and therefore, a slower increase in the marginal product of private capital. Because it takes less time to build private capital, agents postpone investment until public capital significantly raises the productivity of private production inputs. 

## B. Fiscal Adjustments 

Sources of fiscal financing have important implications for how government investment affects the economy over longer horizons. Estimates reveal that historically debt has been stabilized by adjustments in distorting fiscal instruments, particularly, government consumption and capital taxes. Because lump-sum financing is frequently assumed in the literature, we contrast the results under the estimated financing mechanisms to those under lump-sum financing. The case when only income taxes adjust, as in Barro (1990), is also considered. Finally, how the speed at which policy reacts to stabilize debt affects outcomes is investigated. 

## 1. Financing method 

Figure 2 plots responses to a positive government investment shock of one standard deviation for α[G] = 0.05 (the left column) and α[G] = 0.1. Because implementation delays have little influence on responses at long horizons, the role of fiscal financing is illustrated for only a three-year delay. The path of government investment is identical to the solid line in Figure 1. Solid lines in Figure 2 reflect outcomes when all instruments adjust according to the mean estimates of fiscal parameters in Table 2. Dotted-dashed lines are the outcomes when only lump-sum transfers adjust (γZ = 0.155 and γGC = γK = γL = 0). Dashed lines are the patterns that arise when only income taxes adjust (γK = 0.143, γL = 0.077, and γGC = γZ = 0).[16] 

The choice of financing instrument matters a great deal for the effects of government investment at longer horizons, regardless of the productivity of public capital. Fiscal adjustments involving distortionary financing methods create another channel that influences the effects of government investment. Raising income tax rates or reducing government consumption offsets some of the growth effects from more productive public capital. Among 

> 16The mean estimates of γK and γL are insufficient to stabilize debt growth when other instruments are set to 0. Thus, the mean estimates of γK and γL are scaled by 1.5 to ensure an equilibrium exists. 

14 

the three methods of financing, government investment is most expansionary when non-distorting transfers are reduced and is least expansionary—in fact, can be contractionary— when government raises income tax rates. 

The dashed lines of the left column in Figure 2 show that when public capital is weakly productive (α[G] = 0.05), consumption, investment, and output are persistently negative at long horizons when income tax rates alone adjust to stabilize debt. On the other hand, if public capital is more productive, as in the right column (α[G] = 0.1), government investment can expand output throughout the horizon (except for an initial negative response due to implementation delays). 

The results show that studies that ignore distorting fiscal financing are likely to overstate the growth effects of deficit-financed government investment. Although cutting lump-sum transfers produces the most growth, it is worth noting that our analysis overlooks the distributional effects of government investment. Because a significant portion of transfers go to households with low-income, debt-financing through transfers reductions can substantially reduce the welfare of some segments of the population. 

## 2. Financing speed 

In the current policy debate, many political leaders have stressed the need to get “the fiscal house in order” by stabilizing government debt quickly. Within a week of the passage of the ARRA in February 2009, for example, President Obama pledged to cut the federal deficit in half by 2013 Calmes (2009). The rest of this section investigates how more rapid debt stabilization can affect the impacts of government investment. 

Figure 3 plots the responses to a government investment shock assuming a three-year implementation delay when α[G] = 0.05. The solid lines are responses using the mean estimates in Table 2, where the government does not begin to retire the debt until two years after the initial increase in debt (as assumed in the earlier analysis). The dotted-dashed lines assume that the responses to debt (the γ coefficients) are twice as large, and that the government begins to retire debt only one year after the increase in the debt-to-output ratio. 

Speeding up debt retirement brings forward the negative impact of distorting debt financing from raising tax rates or reducing government consumption. Retiring debt more quickly dampens the expansionary effects of government investment in the short run. The dotted-dashed lines in Figure 3 show that labor and output rise less and private investment falls more than when debt is stabilized more gradually. In particular, output turns negative (as a result of distorting debt financing) earlier and by a larger magnitude, compared to the estimated speed of debt retirement. 

Retiring debt early, of course, leads to smaller accumulation of debt and, therefore, smaller eventual fiscal adjustments. If the policy objective is to stimulate the economy by government investment in the short run, then retiring debt too soon could defeat that purpose. Generally speaking, the financing speed is important not only for the short-run effects of 

15 

government investment but for the effectiveness of all countercyclical fiscal measures, as Leeper et al. (2010) show for other fiscal instruments. 

## V. PRESENT-VALUE MULTIPLIERS 

Government spending multipliers are often used to summarize the effects of fiscal policy. Following Mountford and Uhlig (2009), the present-value multipliers for output, consumption, and private investment are computed. The present-value multiplier k quarters after an increase in government spending is defined as 

**==> picture [285 x 76] intentionally omitted <==**

where △Yt+i and △G[I] t+i[are level changes in output and government investment relative to] their steady state values. Discount factors, the r’s, are model-based, constructed from real interest rates along the transition path. Compared with other measures of multipliers, such as peak responses to an initial change in a fiscal policy variable (as reported in Blanchard and Perotti (2002) or period-by-period flow changes in government spending and output (as in Cogan et al. (2010)), present-value multipliers better account for the dynamic effects of deficit-financed spending increases, particularly at longer horizons. 

Table 3 reports the cumulative present-value multipliers for output, consumption, and investment based on the mean estimates, along with their 90-percent posterior intervals computed from the posterior distribution of estimated parameters. k in (16) is set to 1000 in order to account for all the dynamics following a government investment shock. Multipliers are computed for α[G] = 0.05 and 0.1 and under the three different implementation delays. The 90-percent posterior interval shows that conditional on productivity (α[G] ) and the implementation delay, the multipliers are tightly estimated. 

The productivity of public capital is the dominant factor determining cumulative multipliers for government investment, as seen in Table 3. When α[G] = 0.1, multipliers are uniformly larger than when α[G] = 0.05, for a given length of implementation delay. A high stock of productive public capital has long-lasting effects on output. When government spending transforms into productive public capital, the cumulative output multiplier can be as large as 1.3 when α[G] = 0.1. Present-value consumption multipliers can also be positive because the positive wealth effect eventually dominates the short-run negative consumption response. Present-value investment multipliers, on the other hand, remain negative for all cases examined. For a given length of implementation delay, however, a larger α[G] implies a less 

16 

negative investment multiplier. Longer delays lead to more negative multipliers because there is a larger short-run dip in investment.[17] 

Neoclassical studies of government spending multipliers typically assume all spending is unproductive. The resulting negative wealth effect crowds out private consumption and investment. Those studies tend to infer that the output multiplier is less than 1 (for example, Uhlig (2010)). The analysis here shows that in a standard neoclassical growth model, the cumulative multiplier for output can still be larger than 1, even under distortionary financing and with a modest degree of productivity of public capital. Since recent countercyclical fiscal actions in the United State include substantial government investment projects, our results indicate that different government spending categories are likely to have very different multipliers, depending on the productivity of the spending. 

Another common theme that emerges from existing work is that the stimulative effect of government spending is highest on impact and declines gradually afterwards. This typical pattern shows up in DSGE estimates in Forni et al. (2009), Cogan et al. (2010), and Zubairy (2009), as well as VAR estimates in Mountford and Uhlig (2009). The pattern provides some justification for relying on government spending to stimulate an economy in the short run. But with implementation delays and productive government spending, output multipliers can be relatively small on impact. Table 4 reports present-value mean output multipliers one year (k = 5) and three years (k = 13) after a government investment shock. When there is a one-quarter delay to build public capital, the typical pattern holds when government investment is weakly productive (α[G] = 0.05): the output multiplier declines over time, mainly due to subsequent expected fiscal adjustments. With longer delays, the output multipliers change very little over time. The reduction in output multipliers during the initial years results from implementation delays, which produce slightly negative or muted responses in output. 

However, when government investment is more productive (α[G] = 0.1), the patterns of output multipliers are generally reversed. Short-run output multipliers are much smaller than long-run multipliers. Even though government investment is more productive, the output multipliers after one year are smaller than those when α[G] = 0.05. More productive government investment generates stronger positive wealth effects, so labor rises less, investment falls more, and output rises less in the short run. This suggests that there is considerable uncertainty about the short-run expansionary effects of government investment, especially when a project involves substantial delay. 

To see the quantitative importance of distorting fiscal financing, output multipliers are also computed under lump-sum transfer adjustments only. All parameters are set to their mean estimates, except that the responses of government consumption, capital taxes, and labor taxes to the debt-to-output ratio are turned off (γGC = γK = γL = 0). Compared to the scenarios estimated from data, output multipliers can be much larger. When α[G] = 0.05, 

> 17Using the Japanese data in the 1990s, Bruckner and Tuladhar (2010) find that investment multipliers are larger for projects implemented by Japanese local governments than those by the central government, which could be driven by higher implementation speeds of the former projects. 

17 

present-value cumulative multipliers for output are 0.93 (one-quarter delay), 0.78 (one-year delay), and 0.72 (three-three delay), compared to 0.39, 0.40, and 0.31 in Table 3. When α[G] = 0.1, the multipliers are 1.39 (one-quarter delay), 1.30 (one-year delay), and 1.15 (three-year delay), compared to 1.14, 1.11, and 0.90 in Table 3. These comparisons suggest that models assuming lump-sum financing could significantly over-estimate the cumulative output multipliers for government spending. 

Multipliers in Table 3 indicate quite a bit of uncertainty in assessing government investment. The 90-percent posterior intervals reflect estimation uncertainty conditional on the model specification in Section II; they do not, however, account for model uncertainty. Leeper et al. (2009) consider three alternative specifications: agents can derive utility from government consumption, private capital is also subject to a process of time-to-build, and the economy includes a government production section where the government employs workers and purchases goods to produce output. The multipliers for those calibrated models show that the basic messages conveyed in this analysis holds. In general, the more productive is government investment, the more favorable the growth effects and the more likely the cumulative consumption multiplier will be positive. And the shorter the implementation delay, the less negative is the cumulative investment multiplier. 

## VI. CONCLUDING REMARKS 

Macroeconomic effects of government investment hinge critically on implementation delays and distorting fiscal adjustments. A substantial time-to-build lag in a standard neoclassical model can make expansionary government investment contractionary in the short run, at worst, and have a muted impact, at best. Over longer horizons, the choice of fiscal adjustment instruments is important for minimizing the negative effects from stabilizing government debt. The productivity of government investment is also critical. Macroeconomic analysis often does not distinguish among the various types of government spending. But present-value long-run output multipliers can be larger than 1 even if government investment is only moderately productive. 

An important parameter in this analysis, the productivity of public capital, (α[G] ), is difficult to pin down. Some readers may claim that even in the face of implementation delays, expansions in government investment can stimulate the economy in the short run because, in fact, public capital is far more productive than the α[G] = 0.05 or 0.10 values assumed here. Based on the model’s estimates of the other parameters, to generate positive consumption multipliers over horizons of 1 to 3 years, α[G] must be between 40 percent and 110 percent higher than the maximum value used here, depending on whether implementation delays are 3 years or 1 year. Of course, the more productive is public capital, the more likely it is that the wealth effect from higher government investment will serve to reduce employment and output in the short run. Compelling arguments about the efficacy of government investment for offsetting business cycle fluctuations need to quantify the productivity of public capital. 

Multiplier estimates in Table 3 suggest that conditional on degree of implementation delay and the productivity of government capital, data are fairly informative about the size of 

18 

government investment multipliers. But conventional macroeconomic time series tell us very little about those two critical pieces of the puzzle. Looking across the two settings for the productivity parameter, for example, there is substantial uncertainty: even the sign of the long-run present-value consumption multiplier changes from negative to positive as public capital becomes more productive. In addition, long-run multipliers can take on very different values, depending on the fiscal financing rules the government follows. 

Further progress on estimating government spending multipliers may require bringing fresh data to bear on the three dimensions of the issue that this paper has highlighted: implementation delays, productivity of public capital, and fiscal financing schemes. 

19 

Table 1. Cost estimation by the Congressional Budget Office. 

|||ARRA, Highway Construction in Title XII(billions)|ARRA, Highway Construction in Title XII(billions)|ARRA, Highway Construction in Title XII(billions)|ARRA, Highway Construction in Title XII(billions)|ARRA, Highway Construction in Title XII(billions)||||
|---|---|---|---|---|---|---|---|---|---|
||2009|2010|2011|2012|2013|2014|2015|2016|2009-16|
|Budget Authority|27.5|0|0|0|0|0|0|0|27.5|
|Estimated Outlay|2.75|6.875|5.5|4.125|3.025|2.75|1.925|.55|27.5|
||National|Highway|Bridge Reconstruction and Inspection Act||||(millions)|||
||2009|2010|2011|2012|2013||||2009-13|
|Budget Authority|1,029|5|5|5|5||||1,049|
|Estimated Outlay|280|425|169|56|46||||976|



Note: Top panel—highway construction in Title XII of the American Recovery and Reinvestment Act of 2009. Bottom panel—the National Highway Bridge Reconstruction and Inspection Act of 2008. 

20 

Table 2. Prior and posterior distributions for the estimated parameters. 

|Parameters||Prior|||Posterior|Posterior||
|---|---|---|---|---|---|---|---|
||func.|mean|std.|mean|5%|95%|std.|
|Structural||||||||
|γ, risk aversion|G|1.75|0.5|3.46|2.7|4.3|0.51|
|κ, inverse Frisch labor elast.|G|2|0.5|1.89|1.3|2.5|0.37|
|h, habit formation|B|0.5|0.2|0.31|0.22|0.41|0.06|
|δ2, capital utilization|B|0.7|0.5|0.067|0.041|0.1|0.021|
|s, investment adj. cost|N|5|0.25|5.21|4.8|5.6|0.25|
|Fiscal policy||||||||
|γGC, govt consumption resp to debt|N|0.15|0.1|0.072|0.022|0.12|0.031|
|γK, capital tax resp to debt|N|0.15|0.1|0.095|0.033|0.16|0.037|
|γL, labor tax resp to debt|N|0.15|0.1|0.051|−0.023|0.12|0.045|
|γZ, transfers resp to debt|N|0.15|0.1|0.15|0.047|0.27|0.066|
|ϕK, capital resp. to output|G|1|0.3|1.2|0.91|1.5|0.19|
|ϕL, labor resp. to output|G|0.5|0.25|0.53|0.24|0.84|0.18|
|ϕZ, transfers resp. to output|G|0.2|0.1|0.23|0.082|0.43|0.11|
|AR(1) coeffcients||||||||
|ρa, technology|B|0.5|0.2|0.95|0.94|0.97|0.01|
|ρb, preference|B|0.5|0.2|0.78|0.74|0.83|0.026|
|ρl, leisure preference|B|0.5|0.2|0.99|0.99|1|0.0046|
|ρi, investment|B|0.5|0.2|0.24|0.18|0.3|0.038|
|ρGC, govt consumption|B|0.5|0.2|0.95|0.93|0.98|0.015|
|ρA, govt investment|B|0.5|0.2|0.94|0.90|0.98|0.021|
|ρK, capital tax|B|0.5|0.2|0.89|0.84|0.93|0.027|
|ρL, labor tax|B|0.5|0.2|0.99|0.97|1|0.0093|
|ρC, consumption tax|B|0.5|0.2|0.88|0.83|0.94|0.033|
|ρZ, transfer|B|0.5|0.2|0.96|0.92|0.99|0.021|
|Std. of shocks||s|v|||||
|σa, technology|IG|1|4|0.63|0.57|0.69|0.037|
|σb, preference|IG|1|4|2.35|2|2.7|0.2|
|σl, leisure preference|IG|1|4|2.82|2.3|3.4|0.34|
|σi, investment|IG|1|4|4.59|4.2|5|0.27|
|σGC, government consumption|IG|1|4|2.04|1.9|2.2|0.12|
|σA, government investment|IG|1|4|3.17|2.9|3.4|0.16|
|σK, capital tax|IG|1|4|2.60|2.4|2.8|0.13|
|σL, labor tax|IG|1|4|2.91|2.7|3.2|0.15|
|σC, consumption tax|IG|1|4|1.25|1.1|1.4|0.065|
|σZ, transfers|IG|1|4|4.46|4.1|4.9|0.23|



Note: For function IG—the inverse gamma distribution, `−` v s and v are parameters in f(x|s, v) = v[s] Γ[−][1] (s)x[−][s][−][1] exp x . 

21 

Table 3. Present-value cumulative multipliers for an increase in government investment: mean and 90-percent intervals. 

|delay|Y|C|I|Y|C|I|
|---|---|---|---|---|---|---|
|||αG = 0.05|||αG = 0.1||
|1Q|0.39|−0.07|−0.35|1.14|0.43|−0.17|
||(0.01,0.65)|(−0.16,0.005)|(−0.59,−0.19)|(0.90,1.34)|(0.35,0.52)|(−0.32,−0.06)|
|1Y|0.40|−0.08|−0.36|1.11|0.40|−0.20|
||(0.09,0.63)|(−0.16,−0.02)|(−0.56,−0.21)|(0.92,1.30)|(0.33,0.49)|(−0.32,−0.10)|
|3Y|0.31|−0.11|−0.40|0.90|0.32|−0.31|
||(−0.03,0.57)|(−0.19,−0.05)|(−0.62,−0.24)|(0.68,1.11)|(0.26,0.41)|(−0.45,−0.20)|



Note: Parentheses contain the 5th and 95th percentiles of multipliers computed from the posterior distribution of estimated parameters. Variables include output (Y ), consumption (C), and private investment (I). 

Table 4. Present-value mean output multipliers at various horizons: mean and 90-percent intervals. 

|delay|1Y after|3Y after|cumulative|1Y after|3Y after|cumulative|
|---|---|---|---|---|---|---|
|||αG = 0.05|||αG = 0.1||
|1Q|0.51|0.42|0.39|0.52|0.46|1.14|
||(0.47,0.57)|(0.37,0.49)|(0.01,0.65)|(0.47,0.57)|(0.40,0.53)|(0.90,1.34)|
|1Y|0.43|0.37|0.40|0.38|0.35|1.11|
||(0.39,0.49)|(0.32,0.44)|(0.09,0.63)|(0.33,0.43)|(0.30,0.41)|(0.92,1.30)|
|3Y|0.33|0.31|0.31|0.10|0.16|0.90|
||(0.22,0.49)|(0.24,0.41)|(−0.03,0.57)|(0.03,0.21)|(0.11,0.23)|(0.68,1.11)|



Note: The parentheses contain the 5th and 95th percentiles of multipliers computed from the posterior distribution of estimated parameters. 

22 

**==> picture [399 x 299] intentionally omitted <==**

**----- Start of picture text -----**<br>
C I<br>0<br>0 −0.1<br>−0.2<br>−0.02<br>−0.3<br>−0.04<br>0 2 4 6 8 10 0 2 4 6 8 10<br>L Y<br>0.08<br>0.08<br>0.06<br>0.06<br>0.04 0.04<br>0.02 0.02<br>0<br>0<br>0 2 4 6 8 10 0 2 4 6 8 10<br>A, Budget Authority G [I] , Implemented<br>3 3<br>2 2<br>1<br>1<br>0<br>0 2 4 6 8 10 0 2 4 6 8 10<br>**----- End of picture text -----**<br>


## Figure 1. Impulse responses to higher government investment under various lengths of implementation delays. 

Note: Dashed lines are one-quarter delay; dotted-dashed lines are one-year delay; solid lines are three-year delay. Variables include consumption (C), private investment (I), hours worked (L), and output (Y ), along with budget authority (A) and implemented government investment (G[I] ). All variables are in percentage deviations from the steady state. X-axis is in years. 

23 

**==> picture [409 x 308] intentionally omitted <==**

**----- Start of picture text -----**<br>
C C<br>0.02 0.02<br>0 0<br>−0.02 −0.02<br>0 10 20 30 40 0 10 20 30 40<br>I I<br>0.1 0.1<br>0 0<br>−0.1 −0.1<br>−0.2 −0.2<br>−0.3 −0.3<br>0 10 20 30 40 0 10 20 30 40<br>Y Y<br>0.03 0.03<br>0.02 0.02<br>0.01 0.01<br>0 0<br>−0.01 −0.01<br>0 10 20 30 40 0 10 20 30 40<br>α [G] =0.05 α [G] =0.1<br>**----- End of picture text -----**<br>


Figure 2. Impulse responses to an increase in government investment under various financing methods. 

Note: Solid lines are all adjust under mean estimated debt financing parameters (as in Table 2); dotted-dashed lines are only transfers adjusting (γZ = 0.154, γGC = γK = γL = 0); dashed lines are only income taxes adjusting (γK = 0.142, γL = 0.077, γGC = γZ = 0). The total increase in government investment is one unit of good. Variables include consumption (C), private investment (I), and output (Y ). All variables are in percentage deviations from the steady state. X-axis is in years. 

24 

**==> picture [409 x 308] intentionally omitted <==**

**----- Start of picture text -----**<br>
I L<br>0.04<br>−0.05<br>−0.1 0.03<br>−0.15<br>0.02<br>−0.2<br>−0.25 0.01<br>−0.3<br>0 2 4 6 8 10 0 2 4 6 8 10<br>Y sb<br>0.8<br>0.02<br>0.6<br>0.01 0.4<br>0.2<br>0<br>0<br>0 2 4 6 8 10 0 2 4 6 8 10<br>**----- End of picture text -----**<br>


Figure 3. Impulse responses to an increase in government investment under different fiscal adjustment speeds. 

Note: Solid lines are mean estimates as in Table 2; dotted-dashed lines are faster adjustments. Variables include consumption (C), private investment (I), output (Y ), and the debt-output ratio (sb). All variables are in percentage deviations from the steady state. X-axis is in years. 

25 

## VII. Appendix A 

The data source, unless stated otherwise, is the National Income and Product Accounts (NIPA) compiled by the Bureau of Economic Analysis. Nominal values are converted to real values using the implicit price deflator for personal consumption expenditures (Table 1.1.9 line 2). Fiscal variables include federal and state and local governments. To construct a government debt series that is consistent with the NIPA’s definition of net lending and net borrowing (Table 3.1 line 39), government consumption and transfers are constructed differently from the definitions commonly used. Data construction is detailed below. 

Consumption. Ct is personal consumption expenditure on nondurable goods (Table 1.1.5 line 5) and services (Table 1.1.5 line 6) 

Investment. It is the sum of personal consumption expenditure on durable goods (Table 1.1.5 line 4) and gross private domestic investment (Table 1.1.5 line 7). 

Hours worked. Lt is an index of total weekly hours worked. Let Ht denote the seasonally adjusted index for the average weekly hours, nonfarm business, all persons, (U.S. Department of Labor, PRS85006023), and Nt denote the civilian employment for 16 years and over (U.S. Department of Labor, CE16OV). Then Lt =[H] 100[t][N][t][.] 

Consumption tax revenue. Tt[C][=][ C][t][ ×][ τ] t[ C][, where][ τ] t[ C][=] CtT−t[C] Tt[C][and][ T][ C] t[is taxes on] production and imports (Table 3.1 line 4) less property taxes (Table 3.3 line 8). 

Capital and tax revenue. Jones’s (2002) definitions are used to construct capital and labor tax revenues (Tt[K][and][ T][ L] t[).] 

Government consumption. G[C] t[is government consumption expenditure (Table 3.1 line 16)] and government net purchases of non-produced assets (Table 3.1 line 37), minus government consumption of fixed capital (Table 3.1 line 38). 

Government investment. G[I] t[is gross government investment (Table 3.1 line 35).] 

Transfers. Zt is the sum of net current transfers, net capital transfers, and subsidies (Table 3.1 line 25), minus the tax residual. Net current transfers are current transfer payments (Table 3.1 line 17) minus current transfer receipts (Table 3.1 line 11). Net capital transfers are defined as capital transfer payments (Table 3.1 line 36) minus capital transfer receipts (Table 3.1 line 32). The tax residual is the sum of current tax receipts (Table 3.1 line 2), contributions for government social insurance (Table 3.1 line 7), income receipts on assets (Table 3.1 line 8), and the current surplus of government enterprises (Table 3.1 line 14), minus total tax revenue (Tt[C][,][ T][ K] t[, and][ T][ L] t[).] 

Government debt. Following Leeper et al. (2010), Bt is constructed as the sum of net borrowing at t and government debt at t − 1 less seigniorage. Net borrowing is the sum of government consumption (G[C] t[), government investment (][G][I] t[), transfers (][Z][t][), and interest] payment (Table 3.1 line 22) less tax revenues (Tt[C][,][ T][ K] t[, and][ T][ L] t[). Seigniorage is the increase] 

26 

in adjusted monetary base (published by the Federal Reserve Bank of St. Louis) between quarters, where quarterly values are monthly averages. 

Finally, all the data described above are scaled by a population index and logarithmic transformation as follows. The observable X = ln x × 100, where p is a population index � p � (civilian noninstitutional population, ages 16 years and over, seasonally adjusted, U.S. Bureau of Labor Statistics, LNS10000000) and x is the quantity before scaling and transformation. 

27 

## **VIII. REFERENCES** 

An, S., and F. Schorfheide, 2007, “Bayesian Analysis of DSGE Models,” _Econometric Reviews_ , Vol. 26, Issues 2-4, pp. 113–172. 

- Aschauer, D. A., 1989, “Does Public Capital Crowd Out Private Capital?,” _Journal of Monetary Economics_ , Vol. 24 (September), pp. 171–188. 

- Barro, R. J., 1989, “The Neoclassical Approach to Fiscal Policy,” in _Modern Business Cycle Theory_ , ed. by R. J. Barro, pp. 178–235. (Cambridge, Mass.: Harvard University Press). 

- ———, 1990, “Government Spending in a Simple Model of Endogenous Growth,” _Journal of Political Economy_ , Vol. 98, Issue 5, Part 2, pp. S103–S125. 

- Barro, R. J., and C. J. Redlick, 2009, “Macroeconomic Effects from Government 

   - Purchases and Taxes,” NBER Working Paper No. 15369 (Cambridge, Massachusetts: National Bureau of Economic Research). 

- Baxter, M., and R. G. King, 1993, “Fiscal Policy in General Equilibrium,” _American_ 

_Economic Review_ , Vol. 83, Issue 3, pp. 315–334. 

- Blanchard, O. J., and R. Perotti, 2002, “An Empirical Characterization of the 

   - Dynamic Effects of Changes in Government Spending and Taxes on Output,” 

   - _Quarterly Journal of Economics_ , Vol. 117, Issue 4, pp. 1329–1368. 

- Bruckner, M. and A. Tuladhar, 2010, “Public Investment as a Fiscal Stimulus: Evidence from Japan’s Regional Spending During the 1990s,” IMF Working Paper No. 10/110 

   - (Washington: International Monetary Fund). 

- Calmes, J., 2009, “Obama Planning to Slash Deficit, Despite Stimulus Spending,” _The New York Times_ , February 21, p. A1. 

- Christiano, L. J., M. Eichenbaum, and C. L. Evans, 2005, “Nominal Rigidities 

   - and the Dynamic Effects of a Shock to Monetary Policy,” _Journal of Political Economy_ , Vol. 113, Issue 1, pp. 1–45. 

- Christiano, L. J., M. Eichenbaum, and S. Rebelo, 2009, “When is the Government 

   - Spending Multiplier Large?,” Manuscript, (Northwestern University). 

- Cogan, J. F., T. Cwik, J. B. Taylor, and V. Wieland 496, 2010, “New Keynesian 

   - versus Old Keynesian Government Spending Multipliers,” _Journal of Economic_ 

   - _Dynamics and Control_ , Vol. 34, Issue 3, pp. 281–295. 

28 

Congressional Budget Office, 2008, “Options for Responding to Short-Term Economic Weakness,” (January), (Washington, D.C.). 

- ———, 2009, “Estimated Macroeconomic Impacts of the American Recovery and 

Reinvestment Act of 2009,” (Washington, D.C.). 

———, 2010a, “The Budget and Economic Outlook: Fiscal Years 2010 to 2020,” (Washington, D.C.). 

———, 2010b, “The Long-Term Budget Outlook,” (Washington, D.C.). 

———, 2010c, “Policies for Increasing Economic Growth and Employment in 2010 and 2011,” (Washington, D.C.). 

Davig, T., and E. M. Leeper, 2010, “Monetary-Fiscal Policy Interactions and Fiscal Stimulus,” NBER Working Paper No. 15133. 

Denes, M., and G. B. Eggertsson, 2009, “A Bayesian Approach to Estimating Tax 

and Spending Multipliers,” Federal Reserve Bank of New York Staff Reports No. 403. 

Evans, P., and G. Karras, 1994, “Are Government Activities Productive? Evidence 

from a Panel of U.S. States,” _Review of Economic and Statistics_ , Vol. 76, Issue 1, pp. 1–11. 

Forni, L., L. Monteforte, and L. Sessa, 2009, “The General Equilibrium Effects 

of Fiscal Policy: Estimates for the Euro Area,” _Journal of Public Economics_ , Vol. 93, Issues 3-4, pp. 559–585. 

Freedman, C., M. Kumhof, D. Laxton, D. Muir, and S. Mursula, 2009, “Fiscal Stimulus to the Rescue? Short-Run Benefits and Potential Long-Run Costs of Fiscal Deficits,” IMF Working Paper No. 09/255 (Washington: International Monetary Fund). 

Glomm, G., and B. Ravikumar, 1997, “Productive Government Expenditures and 

   - Long-Run Growth,” _Journal of Economic Dynamics and Control_ , Vol 21, pp. 183– 204. 

- Hall, R. E., 2009, “By How Much Does GDP Rise If the Government Buys More Output?,” Manuscript, (Stanford University). 

Holtz-Eakin, D., 1994, “Public-Sector Capital and the Productivity Puzzle,” _Review of Economic and Statistics_ , Vol. 76, Issue 1, pp. 12–21. 

House, C. L., and M. D. Shapiro, 2006, “Phased-in Tax Cuts and Economic Activity,” 

29 

_American Economic Review_ , Vol. 96, Issue 5, pp. 1835–1849. 

- Jones , J.B., 2002, “Has Fiscal Policy Helped Stabilize the Postwar U.S. Economy?,” _Journal of Monetary Economics,_ Vol 49 (May), pp. 709-746. 

- Kamps, C., 2004, _The Dynamic Macroeconomic Effects of Public Capital_ . (Berlin, Germany: Springer). 

Kydland, F., and E. C. Prescott, 1982, “Time to Build and Aggregate Fluctuations,” _Econometrica_ , Vol. 50, Issue 6, pp. 1345–1370. 

Leeper, E. M., M. Plante, and N. Traum, 2010, “Dynamics of Fiscal Financing in 

the United States,” _Journal of Econometrics_ , Vol. 156, Issue 2, pp. 304–321. Leeper, E. M., T. B. Walker, and S.-C. S. Yang, 2008, “Fiscal Foresight: Analytics and Econometrics,” NBER Working Paper No. 14028. 

- ———, (2009): “Government Investment and Fiscal Stimulus in the Short and Long Runs,” NBER Working Paper No. 15153. 

Mountford, A., and H. Uhlig, 2009, “What Are the Effects of Fiscal Policy Shocks?,” _Journal of Applied Econometrics_ , Vol. 24, Issue 6, pp. 960–992. 

Nadiri, M. I., and T. P. Mamuneas, 1994, “The Effects of Public Infrastructure and R 

   - & D Capital on the Cost Structure and Performance of U.S. Manufacturing Industries,” _Review of Economic and Statistics_ , Vol. 76, Issue 1, 22–37. 

- Ramey, V. A., 2009, “Identifying Government Spending Shocks: It’s All in the Timing,” NBER Working Paper No. 15464. 

Ramey, V. A., and M. D. Shapiro, 1998, “Costly Capital Reallocation and the Effects of Government Spending,” in _Carneige-Rochester Conference Series on Public Policy_ , Vol. 48 of Carnegie-Rochester Conference Series on Public Policy, pp. 145–194. (North-Holland). 

- Romer, C., and J. Bernstein, 2009, “The Job Impact of the American Recovery and Reinvestment Plan,” Obama Transition Team, January 9 (Washington, D.C.). 

Schmitt-Groh´e, S., and M. Uribe, 2010, “What’s ‘News’ in Business Cycles?,” Manuscript (Columbia University). 

- Sims, C. A., 2001, “Solving Linear Rational Expectations Models,” _Journal of Computational Economics_ , Vol. 20, Issues 1-2, pp. 1–20. 

Traum, N., and S.-C. S. Yang, 2010, “When Does Government Debt Crowd Out 

30 

Investment?,” Congressional Budget Office Working Paper 2010-02. 

Uhlig, H., 2010, “Some Fiscal Calculus,” _American Economic Review: Papers & Proceedings_ , Vol. 100, Issue 2, pp. 30–34. 

Yang, S.-C. S., 2005, “Quantifying Tax Effects Under Policy Foresight,” _Journal of Monetary Economics_ , Vol. 52, Issue 8, pp. 1557–1568. 

Zubairy, S., 2009, “On Fiscal Multipliers: Estimates from a Medium Scale DSGE Model,” Manuscript (Duke University). 

