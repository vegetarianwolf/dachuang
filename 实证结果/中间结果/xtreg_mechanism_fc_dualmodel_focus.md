# 机制检验：融资约束

## 本次操作
- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`
- 核心解释变量：`fund_est_scale_cum`
- 债务调节变量：`debt_pressure`、`debt_pressure_l1`
- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`
- 回归方法：地级市固定效应 + 年份固定效应，标准误按城市聚类
- 报告说明：以下表格完整记录该类别下所有已尝试规格的系数、标准误、p 值和显著性星号

## 显著结果摘要
| model | mvar | M_eq_sig | Y_term1_sig | Y_term2_sig | Y_term3_sig | total_rows |
| --- | --- | --- | --- | --- | --- | --- |
| mediated | fcity_fc_mean | 4 | 10 | 0 | 0 | 16 |
| mediated | fcity_ww_mean | 2 | 9 | 0 | 0 | 16 |
| mediated | fcity_sa_mean | 0 | 10 | 5 | 0 | 16 |
| mediated | fcity_kz_mean | 0 | 10 | 0 | 0 | 16 |
| moderator | fcity_kz_mean | 4 | 6 | 2 | 2 | 16 |
| moderator | fcity_fc_mean | 1 | 12 | 9 | 12 | 16 |
| moderator | fcity_sa_mean | 0 | 12 | 7 | 12 | 16 |
| moderator | fcity_ww_mean | 0 | 10 | 0 | 0 | 16 |

## 完整结果
### 模型 A：机制变量作为中介传导变量
#### A1. M_eq
| spec | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | 6.187605212e-11 | 2.7160623e-11 | 0.023992555 | ** | 844 | 0.039786365 |
| noctrl | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | 4.50009093e-11 | 1.790473e-11 | 0.012668956 | ** | 1557 | 0.018141661 |
| ctrl | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | 5.827785644e-11 | 2.6561149e-11 | 0.029600842 | ** | 841 | 0.046869073 |
| noctrl | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | 4.891915622e-11 | 1.9280477e-11 | 0.011856334 | ** | 1554 | 0.025501242 |
| ctrl | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -2.632163249e-10 | 2.6205169e-10 | 0.3166264 |  | 844 | 0.092205442 |
| noctrl | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.279713571e-10 | 1.9223982e-10 | 0.50630289 |  | 1557 | 0.058950081 |
| ctrl | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.500235198e-10 | 2.4145025e-10 | 0.53521585 |  | 841 | 0.074955039 |
| noctrl | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.126221492e-10 | 2.0206618e-10 | 0.57784539 |  | 1554 | 0.05059313 |
| ctrl | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -4.621550035e-12 | 1.3993084e-11 | 0.74160951 |  | 854 | 0.61857134 |
| noctrl | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | 2.063623782e-12 | 1.5736015e-11 | 0.89578265 |  | 1570 | 0.6271469 |
| ctrl | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | 9.136775267e-13 | 1.40196e-11 | 0.94811499 |  | 851 | 0.61101276 |
| noctrl | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -7.832029718e-13 | 1.6020555e-11 | 0.9610526 |  | 1567 | 0.61363792 |
| ctrl | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -4.314944329e-11 | 2.3883171e-11 | 0.072622016 | * | 853 | 0.017048687 |
| noctrl | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.16588918e-11 | 2.1153931e-11 | 0.13591234 |  | 1569 | 0.013505055 |
| ctrl | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.711180502e-11 | 2.1769106e-11 | 0.090081669 | * | 850 | 0.021193115 |
| noctrl | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -2.984040929e-11 | 2.3123614e-11 | 0.19821678 |  | 1566 | 0.016858771 |

#### A2. Y_eq
| spec | yvar | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | term2 | coef2 | se2 | p2 | sig2 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | pat_apply_total | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.551788342e-05 | 1.5228683e-05 | 0.020885129 | ** | fcity_fc_mean | 1051.353926 | 1461.8116 | 0.47302094 |  | 844 | 0.65717024 |
| ctrl | pat_invent_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.251646469e-05 | 3.5108965e-06 | 0.00047538758 | *** | fcity_fc_mean | 345.444212 | 579.13361 | 0.55166417 |  | 844 | 0.69543141 |
| ctrl | pat_utility_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.448523021e-05 | 8.4355643e-06 | 0.087814622 | * | fcity_fc_mean | 551.0882109 | 1060.3229 | 0.60393977 |  | 844 | 0.5529061 |
| noctrl | pat_apply_total | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.206969425e-05 | 1.469271e-05 | 0.030111825 | ** | fcity_fc_mean | -306.6755297 | 983.92511 | 0.75557309 |  | 1556 | 0.64709085 |
| noctrl | pat_invent_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.279179877e-05 | 2.9473547e-06 | 2.1676742e-05 | *** | fcity_fc_mean | 449.5384228 | 342.79895 | 0.19109148 |  | 1556 | 0.71537298 |
| noctrl | pat_utility_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.240602034e-05 | 9.0026542e-06 | 0.16958445 |  | fcity_fc_mean | -437.1473634 | 773.6441 | 0.57261312 |  | 1556 | 0.49782243 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.976012708e-05 | 1.6798134e-05 | 0.019074511 | ** | fcity_fc_mean | 887.5408167 | 1586.4635 | 0.57660234 |  | 841 | 0.64329696 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.467158496e-05 | 4.0483701e-06 | 0.00038400831 | *** | fcity_fc_mean | 258.7599196 | 577.49457 | 0.65467757 |  | 841 | 0.68696678 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.536543912e-05 | 9.2673554e-06 | 0.099179924 | * | fcity_fc_mean | 166.6644712 | 1110.9203 | 0.88092583 |  | 841 | 0.55094111 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.464690717e-05 | 1.6143762e-05 | 0.032945983 | ** | fcity_fc_mean | -724.3712525 | 1070.3632 | 0.49926737 |  | 1553 | 0.64536732 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.335959005e-05 | 3.2957421e-06 | 6.9791982e-05 | *** | fcity_fc_mean | 403.8216561 | 342.8689 | 0.24014823 |  | 1553 | 0.71294791 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.353034026e-05 | 9.7831653e-06 | 0.16804729 |  | fcity_fc_mean | -896.8855272 | 886.66968 | 0.31286803 |  | 1553 | 0.49670914 |
| ctrl | pat_apply_total | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -3.54194475e-05 | 1.5222576e-05 | 0.021185419 | ** | fcity_kz_mean | 126.8245543 | 176.07185 | 0.47235334 |  | 844 | 0.65718836 |
| ctrl | pat_invent_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.247513522e-05 | 3.508376e-06 | 0.00049114064 | *** | fcity_kz_mean | 75.81120241 | 67.39138 | 0.26223877 |  | 844 | 0.69558209 |
| ctrl | pat_utility_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.443329033e-05 | 8.4363919e-06 | 0.088979237 | * | fcity_kz_mean | 67.77967087 | 98.976044 | 0.4944196 |  | 844 | 0.55292702 |
| noctrl | pat_apply_total | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -3.208046571e-05 | 1.4697563e-05 | 0.030110916 | ** | fcity_kz_mean | 23.671074 | 92.522148 | 0.79831064 |  | 1556 | 0.64708817 |
| noctrl | pat_invent_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.277070395e-05 | 2.94847e-06 | 2.2490314e-05 | *** | fcity_kz_mean | 6.760749759 | 33.45491 | 0.84003586 |  | 1556 | 0.71528304 |
| noctrl | pat_utility_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.242771081e-05 | 9.0071708e-06 | 0.16905569 |  | fcity_kz_mean | -15.77266475 | 64.134483 | 0.80596381 |  | 1556 | 0.4977814 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -3.970773537e-05 | 1.6805468e-05 | 0.019282311 | ** | fcity_kz_mean | 4.450864401 | 191.30376 | 0.98146576 |  | 841 | 0.64324725 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.464956005e-05 | 4.0447444e-06 | 0.00038704439 | *** | fcity_kz_mean | 46.29233379 | 65.13752 | 0.47826418 |  | 841 | 0.68701166 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.535527943e-05 | 9.2742821e-06 | 0.099652596 | * | fcity_kz_mean | 2.978473608 | 109.08877 | 0.97825032 |  | 841 | 0.55093527 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -3.467874669e-05 | 1.6145421e-05 | 0.032804839 | ** | fcity_kz_mean | 31.9307318 | 95.25486 | 0.73778045 |  | 1553 | 0.64533836 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.333961352e-05 | 3.296826e-06 | 7.1874565e-05 | *** | fcity_kz_mean | 1.970405037 | 34.064522 | 0.95392549 |  | 1553 | 0.71287698 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.357333965e-05 | 9.7858556e-06 | 0.16682163 |  | fcity_kz_mean | 7.773697961 | 67.591324 | 0.9085409 |  | 1553 | 0.49652797 |
| ctrl | pat_apply_total | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -3.548869519e-05 | 1.5215747e-05 | 0.020881651 | ** | fcity_sa_mean | -5662.942073 | 4020.793 | 0.16087861 |  | 854 | 0.65768778 |
| ctrl | pat_invent_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.249172266e-05 | 3.5086443e-06 | 0.00048346657 | *** | fcity_sa_mean | 3.769257958 | 1196.9688 | 0.99749124 |  | 854 | 0.69531476 |
| ctrl | pat_utility_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.450066033e-05 | 8.4113926e-06 | 0.086582012 | * | fcity_sa_mean | -6526.846353 | 3059.8176 | 0.034387492 | ** | 854 | 0.55536819 |
| noctrl | pat_apply_total | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -3.20963389e-05 | 1.465357e-05 | 0.029540487 | ** | fcity_sa_mean | -5600.930659 | 3428.6873 | 0.10377084 |  | 1569 | 0.64769214 |
| noctrl | pat_invent_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.277237656e-05 | 2.9479338e-06 | 2.232326e-05 | *** | fcity_sa_mean | 234.1618709 | 801.06128 | 0.77031916 |  | 1569 | 0.71525437 |
| noctrl | pat_utility_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.243748814e-05 | 8.9497689e-06 | 0.16601224 |  | fcity_sa_mean | -6425.083519 | 2737.9551 | 0.019822421 | ** | 1569 | 0.50042319 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -3.971396294e-05 | 1.6783812e-05 | 0.01911094 | ** | fcity_sa_mean | -4692.413713 | 4277.2842 | 0.27418756 |  | 851 | 0.64359653 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.465051942e-05 | 4.0412024e-06 | 0.00038233804 | *** | fcity_sa_mean | 600.8462337 | 1210.8165 | 0.62037915 |  | 851 | 0.68691123 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.537825483e-05 | 9.2438731e-06 | 0.09805347 | * | fcity_sa_mean | -6152.259654 | 3345.2036 | 0.067661479 | * | 851 | 0.55290163 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -3.471441642e-05 | 1.6092888e-05 | 0.032064948 | ** | fcity_sa_mean | -5947.67246 | 3546.8391 | 0.094964422 | * | 1566 | 0.64600056 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.333937453e-05 | 3.2968796e-06 | 7.1814771e-05 | *** | fcity_sa_mean | 290.2338589 | 781.18848 | 0.71059662 |  | 1566 | 0.71284938 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.360945084e-05 | 9.7209404e-06 | 0.16289887 |  | fcity_sa_mean | -6731.693862 | 2938.9451 | 0.022926092 | ** | 1566 | 0.49931532 |
| ctrl | pat_apply_total | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.531673229e-05 | 1.5190232e-05 | 0.021284387 | ** | fcity_ww_mean | 3348.697977 | 2157.656 | 0.1225649 |  | 853 | 0.65744972 |
| ctrl | pat_invent_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.243661803e-05 | 3.4894829e-06 | 0.0004770814 | *** | fcity_ww_mean | 1259.988781 | 816.15405 | 0.12453801 |  | 853 | 0.69563818 |
| ctrl | pat_utility_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.441124039e-05 | 8.4435605e-06 | 0.08973413 | * | fcity_ww_mean | 1351.612458 | 1563.4701 | 0.38856342 |  | 853 | 0.55270934 |
| noctrl | pat_apply_total | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.202840269e-05 | 1.4690374e-05 | 0.030291563 | ** | fcity_ww_mean | 2080.36655 | 1366.5658 | 0.12934908 |  | 1568 | 0.64721292 |
| noctrl | pat_invent_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.275598506e-05 | 2.9441992e-06 | 2.2329948e-05 | *** | fcity_ww_mean | 462.7107793 | 344.2439 | 0.18027624 |  | 1568 | 0.71530098 |
| noctrl | pat_utility_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.241618801e-05 | 9.0157309e-06 | 0.16984691 |  | fcity_ww_mean | 756.1591721 | 904.94574 | 0.40428674 |  | 1568 | 0.49758071 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.961873573e-05 | 1.6776499e-05 | 0.019344021 | ** | fcity_ww_mean | 2655.539737 | 1835.3973 | 0.14980295 |  | 850 | 0.64343786 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.461091258e-05 | 4.0318914e-06 | 0.00038433354 | *** | fcity_ww_mean | 1035.219836 | 788.802 | 0.19117706 |  | 850 | 0.6870957 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.53423321e-05 | 9.2769296e-06 | 0.10003224 |  | fcity_ww_mean | 1099.917951 | 1462.5049 | 0.45305645 |  | 850 | 0.55067694 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.463755734e-05 | 1.613621e-05 | 0.032906797 | ** | fcity_ww_mean | 2031.809019 | 1378.1656 | 0.14181516 |  | 1565 | 0.64543307 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.332372998e-05 | 3.2922933e-06 | 7.1562696e-05 | *** | fcity_ww_mean | 503.6936873 | 350.2345 | 0.15179017 |  | 1565 | 0.71290183 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.357337674e-05 | 9.7924558e-06 | 0.16709909 |  | fcity_ww_mean | 732.8899929 | 884.4679 | 0.40820405 |  | 1565 | 0.49631158 |

### 模型 B：机制变量作为调节变量
#### B1. M_eq
| spec | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | term2 | coef2 | se2 | p2 | sig2 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | debt_pressure | fcity_fc_mean | debt_pressure | -2.425887794e-05 | 1.6507061e-05 | 0.14356115 |  | fund_est_scale_cum | 3.102174416e-08 | 2.3243004e-08 | 0.18381207 |  | 844 | 0.037887506 |
| noctrl | debt_pressure | fcity_fc_mean | debt_pressure | -9.260929301e-06 | 1.0776909e-05 | 0.391085 |  | fund_est_scale_cum | 2.945754608e-08 | 1.7624709e-08 | 0.096056059 | * | 1557 | 0.017335432 |
| ctrl | debt_pressure_l1 | fcity_fc_mean | debt_pressure_l1 | -7.887616259e-06 | 1.3149872e-05 | 0.54943132 |  | fund_est_scale_cum | 2.590285802e-08 | 2.162972e-08 | 0.23277582 |  | 841 | 0.045350228 |
| noctrl | debt_pressure_l1 | fcity_fc_mean | debt_pressure_l1 | -4.97001535e-06 | 1.0470862e-05 | 0.63549954 |  | fund_est_scale_cum | 2.164090915e-08 | 1.7322712e-08 | 0.21287258 |  | 1554 | 0.024674494 |
| ctrl | debt_pressure | fcity_kz_mean | debt_pressure | 0.0003440289913 | 0.00013245168 | 0.010237256 | ** | fund_est_scale_cum | 2.419413817e-07 | 2.1743776e-07 | 0.2674492 |  | 844 | 0.091824263 |
| noctrl | debt_pressure | fcity_kz_mean | debt_pressure | 0.000325291356 | 0.00010108877 | 0.0014844427 | *** | fund_est_scale_cum | 5.23629367e-08 | 1.6561846e-07 | 0.75217354 |  | 1557 | 0.058890592 |
| ctrl | debt_pressure_l1 | fcity_kz_mean | debt_pressure_l1 | 0.0002505145815 | 0.00011263609 | 0.027474115 | ** | fund_est_scale_cum | 5.212304723e-08 | 1.8272888e-07 | 0.77580553 |  | 841 | 0.074841432 |
| noctrl | debt_pressure_l1 | fcity_kz_mean | debt_pressure_l1 | 0.0002579948653 | 9.7879849e-05 | 0.0089825252 | *** | fund_est_scale_cum | 3.694398708e-08 | 1.6389993e-07 | 0.82187009 |  | 1554 | 0.050554752 |
| ctrl | debt_pressure | fcity_sa_mean | debt_pressure | 5.176663685e-06 | 9.1294442e-06 | 0.57146013 |  | fund_est_scale_cum | -1.239494357e-08 | 1.4790374e-08 | 0.40321255 |  | 854 | 0.61855644 |
| noctrl | debt_pressure | fcity_sa_mean | debt_pressure | -3.537617462e-06 | 6.2348395e-06 | 0.57101655 |  | fund_est_scale_cum | -2.39205019e-08 | 1.9099314e-08 | 0.21172605 |  | 1570 | 0.62714469 |
| ctrl | debt_pressure_l1 | fcity_sa_mean | debt_pressure_l1 | 4.721353016e-06 | 7.1201216e-06 | 0.50817531 |  | fund_est_scale_cum | -1.002493551e-08 | 1.4727387e-08 | 0.49699831 |  | 851 | 0.61101222 |
| noctrl | debt_pressure_l1 | fcity_sa_mean | debt_pressure_l1 | -2.086737742e-06 | 5.6779181e-06 | 0.7135796 |  | fund_est_scale_cum | -2.370693384e-08 | 1.9483974e-08 | 0.22498353 |  | 1567 | 0.61363769 |
| ctrl | debt_pressure | fcity_ww_mean | debt_pressure | -1.851089334e-06 | 7.2555399e-06 | 0.7989403 |  | fund_est_scale_cum | 2.471168031e-08 | 2.637586e-08 | 0.35016841 |  | 853 | 0.01515469 |
| noctrl | debt_pressure | fcity_ww_mean | debt_pressure | 8.35498346e-06 | 6.7141686e-06 | 0.2146657 |  | fund_est_scale_cum | 2.475461703e-08 | 1.7874475e-08 | 0.16746259 |  | 1569 | 0.012758894 |
| ctrl | debt_pressure_l1 | fcity_ww_mean | debt_pressure_l1 | -2.160909488e-06 | 5.979949e-06 | 0.71828502 |  | fund_est_scale_cum | 1.511333029e-08 | 2.309268e-08 | 0.51370782 |  | 850 | 0.020031635 |
| noctrl | debt_pressure_l1 | fcity_ww_mean | debt_pressure_l1 | 7.223135959e-06 | 6.067557e-06 | 0.23512882 |  | fund_est_scale_cum | 2.350977772e-08 | 1.7950017e-08 | 0.19162694 |  | 1566 | 0.01631438 |

#### B2. Y_eq
| spec | yvar | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | term2 | coef2 | se2 | p2 | sig2 | term3 | coef3 | se3 | p3 | sig3 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | pat_apply_total | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.543153232e-05 | 1.404679e-05 | 0.012596969 | ** | fcity_fc_mean | -2725.943968 | 1459.6603 | 0.063592009 | * | fund_est_scale_cum#fcity_fc_me | 0.5728452178 | 0.1514727 | 0.00021693076 | *** | 844 | 0.72871464 |
| ctrl | pat_invent_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.248905935e-05 | 4.1143758e-06 | 0.0027890294 | *** | fcity_fc_mean | -853.3611144 | 617.76019 | 0.16901892 |  | fund_est_scale_cum#fcity_fc_me | 0.1818045379 | 0.045120984 | 8.5026011e-05 | *** | 844 | 0.73833269 |
| ctrl | pat_utility_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.44353099e-05 | 5.9879944e-06 | 0.017013583 | ** | fcity_fc_mean | -1632.599744 | 896.19818 | 0.070301324 | * | fund_est_scale_cum#fcity_fc_me | 0.3311666797 | 0.077346966 | 3.1308879e-05 | *** | 844 | 0.63634372 |
| noctrl | pat_apply_total | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.20265308e-05 | 1.2495395e-05 | 0.011039345 | ** | fcity_fc_mean | -2827.494849 | 1015.2834 | 0.0058184825 | *** | fund_est_scale_cum#fcity_fc_me | 0.468267873 | 0.10312783 | 9.2154351e-06 | *** | 1556 | 0.69243187 |
| noctrl | pat_invent_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.278253455e-05 | 3.0990166e-06 | 5.2564188e-05 | *** | fcity_fc_mean | -91.50808703 | 404.57156 | 0.82126647 |  | fund_est_scale_cum#fcity_fc_me | 0.1005049019 | 0.045921322 | 0.029671092 | ** | 1556 | 0.72804677 |
| noctrl | pat_utility_apply | debt_pressure | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.23768051e-05 | 6.7930246e-06 | 0.069808573 | * | fcity_fc_mean | -2143.367118 | 866.91486 | 0.014175192 | ** | fund_est_scale_cum#fcity_fc_me | 0.316947704 | 0.069446944 | 8.3306377e-06 | *** | 1556 | 0.56661117 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -4.584821098e-05 | 1.663379e-05 | 0.0064913635 | *** | fcity_fc_mean | -3175.935874 | 1670.0906 | 0.058927853 | * | fund_est_scale_cum#fcity_fc_me | 0.7200631895 | 0.1827126 | 0.00011885079 | *** | 841 | 0.74538785 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.661240507e-05 | 5.1624397e-06 | 0.0015494968 | *** | fcity_fc_mean | -1036.635709 | 592.04773 | 0.081782714 | * | fund_est_scale_cum#fcity_fc_me | 0.2295489254 | 0.037934579 | 9.0815568e-09 | *** | 841 | 0.74973357 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.868302025e-05 | 7.2783259e-06 | 0.01113217 | ** | fcity_fc_mean | -2047.646926 | 1050.0496 | 0.05283485 | * | fund_est_scale_cum#fcity_fc_me | 0.3923842188 | 0.10463051 | 0.00024288677 | *** | 841 | 0.65499067 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -3.96144018e-05 | 1.3883383e-05 | 0.0047348388 | *** | fcity_fc_mean | -3179.284207 | 1082.9111 | 0.003676137 | *** | fund_est_scale_cum#fcity_fc_me | 0.5928411544 | 0.12746876 | 5.6756935e-06 | *** | 1553 | 0.70667017 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.443898214e-05 | 3.3178285e-06 | 2.0588495e-05 | *** | fcity_fc_mean | -129.6089404 | 403.32745 | 0.74824816 |  | fund_est_scale_cum#fcity_fc_me | 0.1288190728 | 0.045075573 | 0.0046708998 | *** | 1553 | 0.73089814 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_fc_mean | fund_est_scale_cum#debt_pressu | -1.680110096e-05 | 7.6818606e-06 | 0.029778553 | ** | fcity_fc_mean | -2513.280388 | 981.02148 | 0.011072321 | ** | fund_est_scale_cum#fcity_fc_me | 0.3903459768 | 0.099612348 | 0.00011860068 | *** | 1553 | 0.58252579 |
| ctrl | pat_apply_total | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -3.273882397e-05 | 2.0215119e-05 | 0.1072333 |  | fcity_kz_mean | 193.2404581 | 231.16222 | 0.40438372 |  | fund_est_scale_cum#fcity_kz_me | -0.007232918342 | 0.026491076 | 0.78516781 |  | 844 | 0.65788323 |
| ctrl | pat_invent_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.021550348e-05 | 4.1639723e-06 | 0.01518872 | ** | fcity_kz_mean | 131.796492 | 82.332535 | 0.11132645 |  | fund_est_scale_cum#fcity_kz_me | -0.006096988899 | 0.0063208337 | 0.33615521 |  | 844 | 0.69852149 |
| ctrl | pat_utility_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.236746641e-05 | 1.0716715e-05 | 0.25014451 |  | fcity_kz_mean | 118.9631217 | 139.40643 | 0.39469233 |  | fund_est_scale_cum#fcity_kz_me | -0.005574052293 | 0.015177664 | 0.71389759 |  | 844 | 0.55436707 |
| noctrl | pat_apply_total | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -2.778062061e-05 | 1.4034412e-05 | 0.049004886 | ** | fcity_kz_mean | 152.5543548 | 139.92744 | 0.27679521 |  | fund_est_scale_cum#fcity_kz_me | -0.01797161172 | 0.014618373 | 0.22023471 |  | 1556 | 0.65495187 |
| noctrl | pat_invent_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.382859348e-05 | 3.405283e-06 | 6.7878784e-05 | *** | fcity_kz_mean | -24.94836291 | 59.831177 | 0.67709827 |  | fund_est_scale_cum#fcity_kz_me | 0.004421549928 | 0.0072406824 | 0.54205632 |  | 1556 | 0.71817124 |
| noctrl | pat_utility_apply | debt_pressure | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -7.873639437e-06 | 8.4238445e-06 | 0.35097092 |  | fcity_kz_mean | 120.730778 | 79.889809 | 0.1321619 |  | fund_est_scale_cum#fcity_kz_me | -0.01903417462 | 0.0064522005 | 0.0035194836 | *** | 1556 | 0.52699333 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -3.292213088e-05 | 2.2364515e-05 | 0.14287284 |  | fcity_kz_mean | 194.2671398 | 271.22345 | 0.47482383 |  | fund_est_scale_cum#fcity_kz_me | -0.02001304751 | 0.02960691 | 0.49999636 |  | 841 | 0.64784455 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.147866563e-05 | 4.7294766e-06 | 0.01627898 | ** | fcity_kz_mean | 134.9929601 | 80.574219 | 0.095718667 | * | fund_est_scale_cum#fcity_kz_me | -0.009352042362 | 0.0067599015 | 0.16835994 |  | 841 | 0.6930849 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.076956352e-05 | 1.190076e-05 | 0.36678913 |  | fcity_kz_mean | 131.2564356 | 161.37331 | 0.41715637 |  | fund_est_scale_cum#fcity_kz_me | -0.01352483048 | 0.017186776 | 0.43243015 |  | 841 | 0.55814153 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -2.946562047e-05 | 1.5549937e-05 | 0.059404738 | * | fcity_kz_mean | 170.6112136 | 143.29076 | 0.23505689 |  | fund_est_scale_cum#fcity_kz_me | -0.02176817371 | 0.015723091 | 0.16760404 |  | 1553 | 0.65612602 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -1.4406874e-05 | 3.5443725e-06 | 6.6765126e-05 | *** | fcity_kz_mean | -26.42104219 | 62.031574 | 0.67057228 |  | fund_est_scale_cum#fcity_kz_me | 0.004456502798 | 0.007744553 | 0.56557858 |  | 1553 | 0.71568096 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_kz_mean | fund_est_scale_cum#debt_pressu | -8.296633656e-06 | 9.4650095e-06 | 0.38167408 |  | fcity_kz_mean | 148.1455399 | 84.007721 | 0.079195999 | * | fund_est_scale_cum#fcity_kz_me | -0.0220336604 | 0.0073837694 | 0.0031627389 | *** | 1553 | 0.53221613 |
| ctrl | pat_apply_total | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -6.121638018e-05 | 1.603457e-05 | 0.00018985198 | *** | fcity_sa_mean | -7304.681606 | 3572.8132 | 0.042481843 | ** | fund_est_scale_cum#fcity_sa_me | 0.3755416276 | 0.11175484 | 0.00096573157 | *** | 854 | 0.74509686 |
| ctrl | pat_invent_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.731057486e-05 | 4.2261354e-06 | 6.554123e-05 | *** | fcity_sa_mean | -303.7321805 | 1207.3671 | 0.8016879 |  | fund_est_scale_cum#fcity_sa_me | 0.07033977584 | 0.034170225 | 0.041103885 | ** | 854 | 0.71357143 |
| ctrl | pat_utility_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -3.026347023e-05 | 6.4194332e-06 | 5.1090224e-06 | *** | fcity_sa_mean | -7532.705533 | 2705.9875 | 0.0059977989 | *** | fund_est_scale_cum#fcity_sa_me | 0.2300864335 | 0.049157415 | 5.9105723e-06 | *** | 854 | 0.66986108 |
| noctrl | pat_apply_total | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -4.728205509e-05 | 1.2755785e-05 | 0.0002651969 | *** | fcity_sa_mean | -6822.320975 | 3174.5596 | 0.032711584 | ** | fund_est_scale_cum#fcity_sa_me | 0.2674897094 | 0.067840271 | 0.00010791675 | *** | 1569 | 0.6926772 |
| noctrl | pat_invent_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.693772092e-05 | 3.5415981e-06 | 3.1536922e-06 | *** | fcity_sa_mean | -100.8576436 | 837.34039 | 0.9042356 |  | fund_est_scale_cum#fcity_sa_me | 0.0733707083 | 0.027320102 | 0.0077870381 | *** | 1569 | 0.73579168 |
| noctrl | pat_utility_apply | debt_pressure | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.973493675e-05 | 7.3747028e-06 | 0.0080054458 | *** | fcity_sa_mean | -7012.01883 | 2575.6465 | 0.0069950619 | *** | fund_est_scale_cum#fcity_sa_me | 0.1285413465 | 0.028143799 | 8.1896833e-06 | *** | 1569 | 0.53482443 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -6.787864165e-05 | 1.7087243e-05 | 0.0001053518 | *** | fcity_sa_mean | -6189.870142 | 3769.885 | 0.10247605 |  | fund_est_scale_cum#fcity_sa_me | 0.4133561496 | 0.12023784 | 0.00073933101 | *** | 851 | 0.74765831 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -2.060474425e-05 | 5.2548089e-06 | 0.00012817641 | *** | fcity_sa_mean | 284.2726861 | 1234.9005 | 0.81821734 |  | fund_est_scale_cum#fcity_sa_me | 0.08738659779 | 0.038326148 | 0.023860248 | ** | 851 | 0.71504873 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -3.177123834e-05 | 6.97839e-06 | 1.0122871e-05 | *** | fcity_sa_mean | -7023.839934 | 2973.5542 | 0.01931675 | ** | fund_est_scale_cum#fcity_sa_me | 0.2405900175 | 0.052566946 | 9.1426155e-06 | *** | 851 | 0.67389262 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -5.32473847e-05 | 1.3857407e-05 | 0.00015880009 | *** | fcity_sa_mean | -6989.3835 | 3268.2351 | 0.033556957 | ** | fund_est_scale_cum#fcity_sa_me | 0.2841507959 | 0.069725022 | 6.3910709e-05 | *** | 1566 | 0.6942178 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -1.844537405e-05 | 3.7459765e-06 | 1.6494226e-06 | *** | fcity_sa_mean | 3.233093839 | 825.60284 | 0.99687898 |  | fund_est_scale_cum#fcity_sa_me | 0.07828610106 | 0.027228735 | 0.0044296784 | *** | 1566 | 0.73554772 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_sa_mean | fund_est_scale_cum#debt_pressu | -2.244893143e-05 | 7.8919411e-06 | 0.0048613357 | *** | fcity_sa_mean | -7228.548137 | 2771.9111 | 0.0097285155 | *** | fund_est_scale_cum#fcity_sa_me | 0.1355285029 | 0.02900151 | 5.1308557e-06 | *** | 1566 | 0.53473377 |
| ctrl | pat_apply_total | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.671290172e-05 | 1.392657e-05 | 0.0091798669 | *** | fcity_ww_mean | -7.211829873 | 2389.7834 | 0.99759579 |  | fund_est_scale_cum#fcity_ww_me | 0.4315784272 | 0.35299963 | 0.22321266 |  | 853 | 0.6785562 |
| ctrl | pat_invent_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.263920968e-05 | 3.4443262e-06 | 0.00032704623 | *** | fcity_ww_mean | 773.02831 | 724.40295 | 0.28746501 |  | fund_est_scale_cum#fcity_ww_me | 0.06262433926 | 0.072666414 | 0.39003757 |  | 853 | 0.69828397 |
| ctrl | pat_utility_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.515088645e-05 | 7.1380778e-06 | 0.035275195 | ** | fcity_ww_mean | -426.2415758 | 1568.0066 | 0.78608543 |  | fund_est_scale_cum#fcity_ww_me | 0.2286364926 | 0.18180332 | 0.21030147 |  | 853 | 0.57337952 |
| noctrl | pat_apply_total | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.273291144e-05 | 1.4188876e-05 | 0.021979814 | ** | fcity_ww_mean | -843.4640746 | 4116.3594 | 0.83783382 |  | fund_est_scale_cum#fcity_ww_me | 0.1883946735 | 0.30824348 | 0.54170054 |  | 1568 | 0.65032047 |
| noctrl | pat_invent_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.296473414e-05 | 2.9365374e-06 | 1.5774551e-05 | *** | fcity_ww_mean | -403.6332649 | 991.82123 | 0.68442822 |  | fund_est_scale_cum#fcity_ww_me | 0.05582218135 | 0.072898701 | 0.44463843 |  | 1568 | 0.71695656 |
| noctrl | pat_utility_apply | debt_pressure | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.279073965e-05 | 8.5467545e-06 | 0.13592786 |  | fcity_ww_mean | -798.2935878 | 2352.3403 | 0.7346583 |  | fund_est_scale_cum#fcity_ww_me | 0.1001599127 | 0.16491091 | 0.54423428 |  | 1568 | 0.50048941 |
| ctrl | pat_apply_total | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -4.231122086e-05 | 1.6440445e-05 | 0.010928106 | ** | fcity_ww_mean | -485.3641168 | 2736.968 | 0.85945779 |  | fund_est_scale_cum#fcity_ww_me | 0.3646397142 | 0.37936983 | 0.33784696 |  | 850 | 0.66007036 |
| ctrl | pat_invent_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.490086769e-05 | 4.1008393e-06 | 0.00037107797 | *** | fcity_ww_mean | 696.9742832 | 798.93872 | 0.38424882 |  | fund_est_scale_cum#fcity_ww_me | 0.03926823856 | 0.083860405 | 0.64020759 |  | 850 | 0.6882627 |
| ctrl | pat_utility_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.691584006e-05 | 8.084774e-06 | 0.037914071 | ** | fcity_ww_mean | -735.6491866 | 1676.4277 | 0.66135615 |  | fund_est_scale_cum#fcity_ww_me | 0.2130981104 | 0.19272651 | 0.27043635 |  | 850 | 0.57017291 |
| noctrl | pat_apply_total | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -3.585775752e-05 | 1.5575377e-05 | 0.022245919 | ** | fcity_ww_mean | -1105.909596 | 4051.2913 | 0.78512347 |  | fund_est_scale_cum#fcity_ww_me | 0.1992299023 | 0.29879522 | 0.50560361 |  | 1565 | 0.64907682 |
| noctrl | pat_invent_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.360728087e-05 | 3.2321127e-06 | 3.7042202e-05 | *** | fcity_ww_mean | -225.4513514 | 966.66943 | 0.81580073 |  | fund_est_scale_cum#fcity_ww_me | 0.04629717086 | 0.071142539 | 0.51586729 |  | 1565 | 0.71412212 |
| noctrl | pat_utility_apply | debt_pressure_l1 | fcity_ww_mean | fund_est_scale_cum#debt_pressu | -1.438763284e-05 | 9.1158299e-06 | 0.11591116 |  | fcity_ww_mean | -1360.952129 | 2421.3218 | 0.57463288 |  | fund_est_scale_cum#fcity_ww_me | 0.1329488117 | 0.16439536 | 0.41954169 |  | 1565 | 0.50155085 |

## 输出文件
- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`
- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`
- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`