# 机制检验：早期投资

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
| mediated | early_inv_amt_share | 3 | 7 | 0 | 0 | 16 |
| mediated | early_inv_amt | 2 | 8 | 11 | 0 | 16 |
| mediated | early_inv_count | 0 | 10 | 12 | 0 | 16 |
| mediated | early_inv_count_share | 0 | 9 | 0 | 0 | 16 |
| moderator | early_inv_count | 4 | 12 | 8 | 10 | 16 |
| moderator | early_inv_count_share | 2 | 8 | 0 | 1 | 16 |
| moderator | early_inv_amt_share | 2 | 7 | 0 | 1 | 16 |
| moderator | early_inv_amt | 1 | 12 | 9 | 8 | 16 |

## 完整结果
### 模型 A：机制变量作为中介传导变量
#### A1. M_eq
| spec | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | 2.182864027e-06 | 1.0634914e-06 | 0.042220831 | ** | 575 | 0.10120591 |
| noctrl | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | 3.632235401e-07 | 3.2501922e-07 | 0.26535705 |  | 1048 | 0.02439048 |
| ctrl | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | 1.985884418e-06 | 1.0376025e-06 | 0.057954218 | * | 577 | 0.096057869 |
| noctrl | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | 4.225417998e-07 | 4.4151176e-07 | 0.33993343 |  | 1044 | 0.020379841 |
| ctrl | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | 5.125153477e-10 | 1.4440703e-10 | 0.00069026713 | *** | 233 | 0.094916791 |
| noctrl | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | 3.493273743e-10 | 1.2876351e-10 | 0.0077323401 | *** | 390 | 0.058395091 |
| ctrl | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | 2.825816453e-10 | 1.4469767e-10 | 0.054772478 | * | 241 | 0.086044066 |
| noctrl | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | 2.574536278e-10 | 1.5534976e-10 | 0.10029248 |  | 400 | 0.036707539 |
| ctrl | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | 1.748417405e-09 | 2.4362446e-08 | 0.94290209 |  | 683 | 0.37766641 |
| noctrl | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -7.024993061e-09 | 2.0871731e-08 | 0.73685414 |  | 1251 | 0.29095358 |
| ctrl | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.534454927e-08 | 2.9714217e-08 | 0.60648441 |  | 687 | 0.32794628 |
| noctrl | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.48922349e-08 | 2.1794026e-08 | 0.49535331 |  | 1252 | 0.27422827 |
| ctrl | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | 1.306488873e-10 | 1.4042612e-10 | 0.35456038 |  | 377 | 0.088288374 |
| noctrl | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | 9.073019422e-11 | 1.0455257e-10 | 0.38687459 |  | 677 | 0.059119809 |
| ctrl | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | 2.615054634e-11 | 1.4011096e-10 | 0.8523438 |  | 383 | 0.073308215 |
| noctrl | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | 6.753479526e-11 | 1.4620817e-10 | 0.64481616 |  | 685 | 0.058018718 |

#### A2. Y_eq
| spec | yvar | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | term2 | coef2 | se2 | p2 | sig2 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | pat_apply_total | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -4.120407199e-05 | 2.0830274e-05 | 0.050136242 | * | early_inv_amt | 2.27740925 | 1.3542181 | 0.095140941 | * | 575 | 0.69525242 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.14246648e-05 | 5.903953e-06 | 0.055256508 | * | early_inv_amt | 0.3635046313 | 0.19859245 | 0.069590807 | * | 575 | 0.74118525 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.646817932e-05 | 1.053157e-05 | 0.12043744 |  | early_inv_amt | 1.387315535 | 0.77637142 | 0.076393217 | * | 575 | 0.59681129 |
| noctrl | pat_apply_total | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -3.3215183e-05 | 1.7596969e-05 | 0.060831413 | * | early_inv_amt | 0.8969172522 | 0.54366899 | 0.10088528 |  | 1039 | 0.66445172 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.136530293e-05 | 4.4043518e-06 | 0.010731936 | ** | early_inv_amt | 0.1746386777 | 0.073981963 | 0.019408692 | ** | 1039 | 0.74487585 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.219274307e-05 | 1.0252311e-05 | 0.23603265 |  | early_inv_amt | 0.5307284117 | 0.2624006 | 0.044720706 | ** | 1039 | 0.49641761 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -4.480974571e-05 | 2.1972737e-05 | 0.043559082 | ** | early_inv_amt | 2.344518164 | 1.3886354 | 0.093875751 | * | 577 | 0.67970163 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.452282102e-05 | 6.2205486e-06 | 0.021182299 | ** | early_inv_amt | 0.4235263381 | 0.22428817 | 0.061339386 | * | 577 | 0.73383433 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.616230312e-05 | 1.1234707e-05 | 0.15280224 |  | early_inv_amt | 1.403644611 | 0.79190266 | 0.078787826 | * | 577 | 0.59238678 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -3.578378005e-05 | 1.8841332e-05 | 0.059280958 | * | early_inv_amt | 0.8743807371 | 0.5251894 | 0.097833134 | * | 1035 | 0.66014117 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.190252486e-05 | 4.8604074e-06 | 0.015376551 | ** | early_inv_amt | 0.1808050259 | 0.080998316 | 0.026947394 | ** | 1035 | 0.74345207 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.308515811e-05 | 1.0770886e-05 | 0.22615372 |  | early_inv_amt | 0.5179594194 | 0.25471327 | 0.043604165 | ** | 1035 | 0.49433321 |
| ctrl | pat_apply_total | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -3.884304677e-05 | 2.0046933e-05 | 0.056649398 | * | early_inv_amt_share | 1374.907137 | 2553.7449 | 0.59199274 |  | 233 | 0.74350351 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -9.329784311e-06 | 5.9817226e-06 | 0.1232738 |  | early_inv_amt_share | -508.8243469 | 912.4884 | 0.57885593 |  | 233 | 0.78215086 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.376060324e-05 | 1.037227e-05 | 0.18886842 |  | early_inv_amt_share | 48.15592285 | 1551.1211 | 0.97532004 |  | 233 | 0.67942429 |
| noctrl | pat_apply_total | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -3.813251814e-05 | 1.9863002e-05 | 0.057476338 | * | early_inv_amt_share | 2986.242386 | 2304.2627 | 0.19770041 |  | 389 | 0.71582234 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.296690497e-05 | 5.6062995e-06 | 0.022587188 | ** | early_inv_amt_share | 417.740401 | 658.85663 | 0.52737206 |  | 389 | 0.7732811 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.269272406e-05 | 1.0604927e-05 | 0.23393017 |  | early_inv_amt_share | 333.9047606 | 1494.3073 | 0.8235988 |  | 389 | 0.59068197 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -4.613691748e-05 | 2.332883e-05 | 0.05184745 | * | early_inv_amt_share | 3019.187211 | 2582.03 | 0.24619043 |  | 241 | 0.71157849 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.508067297e-05 | 7.2100456e-06 | 0.040050637 | ** | early_inv_amt_share | 188.4082466 | 764.99762 | 0.80617142 |  | 241 | 0.75996464 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.414852614e-05 | 1.1776211e-05 | 0.2335692 |  | early_inv_amt_share | 1191.051765 | 1671.3434 | 0.47840938 |  | 241 | 0.65944582 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -3.844199188e-05 | 2.0849136e-05 | 0.067901321 | * | early_inv_amt_share | 2309.806428 | 2145.6028 | 0.28404555 |  | 398 | 0.70688981 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.294951757e-05 | 5.9975036e-06 | 0.033010863 | ** | early_inv_amt_share | 460.1615822 | 591.63843 | 0.4383713 |  | 398 | 0.76849729 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.231532999e-05 | 1.1076499e-05 | 0.2686297 |  | early_inv_amt_share | 167.9794479 | 1543.8104 | 0.91355276 |  | 398 | 0.58547592 |
| ctrl | pat_apply_total | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -3.639280166e-05 | 1.0600303e-05 | 0.0008096153 | *** | early_inv_count | 269.1424779 | 59.70599 | 1.4870775e-05 | *** | 683 | 0.73118252 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -1.271897026e-05 | 2.2092677e-06 | 6.2505976e-08 | *** | early_inv_count | 72.21072838 | 11.06759 | 1.5323149e-09 | *** | 683 | 0.72819281 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -1.489364725e-05 | 7.0042879e-06 | 0.035439324 | ** | early_inv_count | 112.3734567 | 37.185387 | 0.003046873 | *** | 683 | 0.6061762 |
| noctrl | pat_apply_total | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -2.988135008e-05 | 1.0570029e-05 | 0.0052767554 | *** | early_inv_count | 262.5883103 | 59.405975 | 1.7751217e-05 | *** | 1242 | 0.69772339 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -1.239024209e-05 | 2.4240355e-06 | 8.7215074e-07 | *** | early_inv_count | 57.20684651 | 15.506495 | 0.00030457746 | *** | 1242 | 0.73021549 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -1.116239563e-05 | 7.4082036e-06 | 0.13377245 |  | early_inv_count | 127.7338699 | 32.568401 | 0.00012828602 | *** | 1242 | 0.54512382 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -3.561619868e-05 | 1.0836492e-05 | 0.0013161326 | *** | early_inv_count | 290.1339012 | 48.619026 | 2.3139211e-08 | *** | 687 | 0.73483115 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.34933317e-05 | 2.4799288e-06 | 2.682865e-07 | *** | early_inv_count | 80.46491477 | 9.5628805 | 7.6946777e-14 | *** | 687 | 0.73067814 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.358805079e-05 | 7.5916619e-06 | 0.075896636 | * | early_inv_count | 125.4819557 | 27.530138 | 1.2126352e-05 | *** | 687 | 0.61675841 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -3.006994368e-05 | 1.1394351e-05 | 0.0091111995 | *** | early_inv_count | 284.2124711 | 47.167931 | 1.06511e-08 | *** | 1243 | 0.70540655 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.247654913e-05 | 2.5904089e-06 | 3.2879439e-06 | *** | early_inv_count | 59.27828154 | 16.126516 | 0.00032028093 | *** | 1243 | 0.72939098 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.093433479e-05 | 7.8543562e-06 | 0.16575462 |  | early_inv_count | 149.9909632 | 29.617664 | 1.0871855e-06 | *** | 1243 | 0.55776167 |
| ctrl | pat_apply_total | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -3.669133233e-05 | 1.5794179e-05 | 0.02233094 | ** | early_inv_count_share | 1173.154769 | 1670.3695 | 0.48420739 |  | 377 | 0.6922707 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.27915338e-05 | 3.7988086e-06 | 0.001101457 | *** | early_inv_count_share | -580.4028353 | 557.22906 | 0.30027452 |  | 377 | 0.72495735 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.409485206e-05 | 8.4392832e-06 | 0.098216854 | * | early_inv_count_share | 589.9276871 | 1122.0061 | 0.60027969 |  | 377 | 0.61907709 |
| noctrl | pat_apply_total | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -3.29642852e-05 | 1.5776892e-05 | 0.03834857 | ** | early_inv_count_share | 949.8643177 | 1279.5393 | 0.45902932 |  | 675 | 0.6813013 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.404534307e-05 | 3.4060911e-06 | 6.1361876e-05 | *** | early_inv_count_share | -267.3833848 | 319.96494 | 0.40466392 |  | 675 | 0.73881078 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.154456582e-05 | 9.1098418e-06 | 0.20701219 |  | early_inv_count_share | 211.8735175 | 815.19275 | 0.79529029 |  | 675 | 0.56646568 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -4.204732293e-05 | 1.8083074e-05 | 0.022211166 | ** | early_inv_count_share | 1424.838131 | 1706.4156 | 0.40584117 |  | 383 | 0.67313921 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.564849208e-05 | 4.601864e-06 | 0.00098896737 | *** | early_inv_count_share | -384.6244921 | 573.0752 | 0.50376529 |  | 383 | 0.71363592 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.496158569e-05 | 9.5876858e-06 | 0.12200229 |  | early_inv_count_share | 763.9893673 | 1129.1372 | 0.50031286 |  | 383 | 0.60981405 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -3.486957578e-05 | 1.716117e-05 | 0.043941874 | ** | early_inv_count_share | 852.5873233 | 1278.4478 | 0.50587213 |  | 683 | 0.67643481 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.449280279e-05 | 3.7972859e-06 | 0.00019782614 | *** | early_inv_count_share | -225.7082384 | 339.51257 | 0.50720555 |  | 683 | 0.73415607 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.207866066e-05 | 9.7960437e-06 | 0.21951227 |  | early_inv_count_share | 151.3735819 | 839.44415 | 0.85714167 |  | 683 | 0.56139529 |

### 模型 B：机制变量作为调节变量
#### B1. M_eq
| spec | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | term2 | coef2 | se2 | p2 | sig2 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | debt_pressure | early_inv_amt | debt_pressure | 0.3364797328 | 0.20958216 | 0.11093225 |  | fund_est_scale_cum | -0.001892660222 | 0.0016010199 | 0.23940454 |  | 575 | 0.072611205 |
| noctrl | debt_pressure | early_inv_amt | debt_pressure | -0.04152707798 | 0.046135373 | 0.36934823 |  | fund_est_scale_cum | 0.0006230233393 | 0.00036821968 | 0.092502147 | * | 1048 | 0.023331093 |
| ctrl | debt_pressure_l1 | early_inv_amt | debt_pressure_l1 | 0.3103690032 | 0.21341829 | 0.14841697 |  | fund_est_scale_cum | -0.00186652543 | 0.0015421984 | 0.2284838 |  | 577 | 0.072741993 |
| noctrl | debt_pressure_l1 | early_inv_amt | debt_pressure_l1 | -0.01932804104 | 0.045027286 | 0.6682933 |  | fund_est_scale_cum | 0.0006083988819 | 0.00039281935 | 0.12332262 |  | 1044 | 0.019067563 |
| ctrl | debt_pressure | early_inv_amt_share | debt_pressure | 0.0002204238461 | 8.5202701e-05 | 0.0117291 | ** | fund_est_scale_cum | 3.406621026e-09 | 1.4720244e-07 | 0.9816016 |  | 233 | 0.066261157 |
| noctrl | debt_pressure | early_inv_amt_share | debt_pressure | 2.145836855e-05 | 0.00010051594 | 0.83134246 |  | fund_est_scale_cum | 6.638237699e-08 | 8.9399592e-08 | 0.45933139 |  | 390 | 0.042077255 |
| ctrl | debt_pressure_l1 | early_inv_amt_share | debt_pressure_l1 | 0.0002117872688 | 7.6275101e-05 | 0.0070187217 | *** | fund_est_scale_cum | -4.625888778e-08 | 1.2061737e-07 | 0.70248204 |  | 241 | 0.078356855 |
| noctrl | debt_pressure_l1 | early_inv_amt_share | debt_pressure_l1 | 6.126999616e-05 | 9.7972967e-05 | 0.53300756 |  | fund_est_scale_cum | 3.769755466e-08 | 8.2123449e-08 | 0.64710653 |  | 400 | 0.028899036 |
| ctrl | debt_pressure | early_inv_count | debt_pressure | -0.0009167321511 | 0.0039490149 | 0.81680739 |  | fund_est_scale_cum | 6.429111164e-05 | 2.397903e-05 | 0.008327594 | *** | 683 | 0.37759823 |
| noctrl | debt_pressure | early_inv_count | debt_pressure | -0.002296150937 | 0.0028621517 | 0.42354378 |  | fund_est_scale_cum | 5.688251613e-05 | 2.1413611e-05 | 0.008659808 | *** | 1251 | 0.28934035 |
| ctrl | debt_pressure_l1 | early_inv_count | debt_pressure_l1 | -0.003832249211 | 0.0045832135 | 0.40466663 |  | fund_est_scale_cum | 7.472770249e-05 | 2.9459403e-05 | 0.012423347 | ** | 687 | 0.32350636 |
| noctrl | debt_pressure_l1 | early_inv_count | debt_pressure_l1 | -0.002693575006 | 0.0027965512 | 0.33685109 |  | fund_est_scale_cum | 5.799956087e-05 | 2.2362303e-05 | 0.010340245 | ** | 1252 | 0.26840413 |
| ctrl | debt_pressure | early_inv_count_share | debt_pressure | 0.0001613476529 | 6.8308116e-05 | 0.020236304 | ** | fund_est_scale_cum | 4.720500211e-08 | 9.9146597e-08 | 0.63509852 |  | 377 | 0.086350307 |
| noctrl | debt_pressure | early_inv_count_share | debt_pressure | 8.152634922e-05 | 6.0504339e-05 | 0.17984164 |  | fund_est_scale_cum | 5.214634266e-08 | 8.0799339e-08 | 0.51965344 |  | 677 | 0.058313932 |
| ctrl | debt_pressure_l1 | early_inv_count_share | debt_pressure_l1 | 0.0001209155557 | 4.9316259e-05 | 0.016059376 | ** | fund_est_scale_cum | -3.561565325e-09 | 8.0375194e-08 | 0.96474993 |  | 383 | 0.073239215 |
| noctrl | debt_pressure_l1 | early_inv_count_share | debt_pressure_l1 | 5.61169847e-05 | 5.9833215e-05 | 0.34980851 |  | fund_est_scale_cum | 3.721947115e-08 | 7.7930693e-08 | 0.63363224 |  | 685 | 0.057638668 |

#### B2. Y_eq
| spec | yvar | dvar | mvar | term1 | coef1 | se1 | p1 | sig1 | term2 | coef2 | se2 | p2 | sig2 | term3 | coef3 | se3 | p3 | sig3 | N | r2w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctrl | pat_apply_total | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -4.486999659e-05 | 1.9651648e-05 | 0.024116654 | ** | early_inv_amt | 6.578584854 | 1.7476367 | 0.00025657058 | *** | fund_est_scale_cum#early_inv_a | -9.415523097e-06 | 3.7964028e-06 | 0.014475351 | ** | 575 | 0.7028842 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.231373444e-05 | 5.7475536e-06 | 0.034113344 | ** | early_inv_amt | 1.40663701 | 0.79894668 | 0.080769077 | * | fund_est_scale_cum#early_inv_a | -2.283477334e-06 | 1.831701e-06 | 0.21487817 |  | 575 | 0.74385732 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.924774755e-05 | 9.7403763e-06 | 0.050366014 | * | early_inv_amt | 4.648542203 | 1.5230174 | 0.0027798594 | *** | fund_est_scale_cum#early_inv_a | -7.139014502e-06 | 2.4286689e-06 | 0.0039225016 | *** | 575 | 0.61291653 |
| noctrl | pat_apply_total | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -4.356602511e-05 | 1.7546847e-05 | 0.014027765 | ** | early_inv_amt | 4.678983358 | 1.9065011 | 0.015151376 | ** | fund_est_scale_cum#early_inv_a | -3.496185645e-06 | 1.423214e-06 | 0.015057508 | ** | 1039 | 0.69820827 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.163012481e-05 | 4.2988104e-06 | 0.0075336574 | *** | early_inv_amt | 0.2714012278 | 0.22583862 | 0.23117261 |  | fund_est_scale_cum#early_inv_a | -8.944842032e-08 | 1.7808635e-07 | 0.61613935 |  | 1039 | 0.74500489 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.970896512e-05 | 9.8066575e-06 | 0.046077073 | ** | early_inv_amt | 3.277060387 | 1.2203999 | 0.0079837004 | *** | fund_est_scale_cum#early_inv_a | -2.538741038e-06 | 1.011367e-06 | 0.013023232 | ** | 1039 | 0.55613315 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -4.876573256e-05 | 2.1161419e-05 | 0.022873417 | ** | early_inv_amt | 6.657837038 | 1.9487534 | 0.00086039706 | *** | fund_est_scale_cum#early_inv_a | -9.457113739e-06 | 4.5053021e-06 | 0.037852135 | ** | 577 | 0.68754411 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.558480169e-05 | 6.3134048e-06 | 0.014940655 | ** | early_inv_amt | 1.58143243 | 0.97794735 | 0.10841991 |  | fund_est_scale_cum#early_inv_a | -2.538752624e-06 | 2.256161e-06 | 0.26267263 |  | 577 | 0.73724896 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.904317561e-05 | 1.0853793e-05 | 0.081832044 | * | early_inv_amt | 4.544737375 | 1.5096928 | 0.0031668171 | *** | fund_est_scale_cum#early_inv_a | -6.886963935e-06 | 2.4376045e-06 | 0.0055135735 | *** | 577 | 0.60742646 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -4.542752277e-05 | 1.901229e-05 | 0.018005252 | ** | early_inv_amt | 4.631659003 | 1.8709657 | 0.01431314 | ** | fund_est_scale_cum#early_inv_a | -3.467074571e-06 | 1.4256295e-06 | 0.016086757 | ** | 1035 | 0.69360209 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -1.210385123e-05 | 4.7400963e-06 | 0.011570291 | ** | early_inv_amt | 0.2592433712 | 0.23794258 | 0.277513 |  | fund_est_scale_cum#early_inv_a | -7.237994448e-08 | 1.8362429e-07 | 0.69396144 |  | 1035 | 0.74353904 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt | fund_est_scale_cum#debt_pressu | -2.015453258e-05 | 1.0497369e-05 | 0.056588043 | * | early_inv_amt | 3.272243498 | 1.1875377 | 0.0065194387 | *** | fund_est_scale_cum#early_inv_a | -2.541549391e-06 | 1.0049683e-06 | 0.01237738 | ** | 1035 | 0.55323207 |
| ctrl | pat_apply_total | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -4.41500049e-05 | 2.3211289e-05 | 0.061215974 | * | early_inv_amt_share | -435.9706162 | 2870.6038 | 0.87971687 |  | fund_est_scale_cum#early_inv_a | 0.01934517023 | 0.034575749 | 0.57758057 |  | 233 | 0.74513704 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -6.993948106e-06 | 5.9486861e-06 | 0.24363697 |  | early_inv_amt_share | 288.2261892 | 1082.8611 | 0.79087895 |  | fund_est_scale_cum#early_inv_a | -0.008514698619 | 0.0057176193 | 0.14086258 |  | 233 | 0.78403264 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.942352122e-05 | 1.1902222e-05 | 0.10712341 |  | early_inv_amt_share | -1884.184966 | 1817.3318 | 0.30335364 |  | fund_est_scale_cum#early_inv_a | 0.02064273161 | 0.019758822 | 0.2996895 |  | 233 | 0.68641061 |
| noctrl | pat_apply_total | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -3.834431137e-05 | 1.9777735e-05 | 0.055092406 | * | early_inv_amt_share | 2734.586819 | 2043.9281 | 0.18368594 |  | fund_est_scale_cum#early_inv_a | 0.002422163873 | 0.013800722 | 0.86100161 |  | 389 | 0.71586168 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.331188243e-05 | 5.5094843e-06 | 0.017330639 | ** | early_inv_amt_share | 7.833530155 | 702.5603 | 0.99112397 |  | fund_est_scale_cum#early_inv_a | 0.003945319491 | 0.0070067984 | 0.57453299 |  | 389 | 0.77388263 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.256505574e-05 | 1.0459031e-05 | 0.23219205 |  | early_inv_amt_share | 485.6019794 | 1742.4928 | 0.78101182 |  | fund_est_scale_cum#early_inv_a | -0.001460073096 | 0.0059487796 | 0.8065725 |  | 389 | 0.59073097 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -4.7820624e-05 | 2.4232135e-05 | 0.0523385 | * | early_inv_amt_share | 2321.203869 | 2584.7808 | 0.37220624 |  | fund_est_scale_cum#early_inv_a | 0.007612895304 | 0.029730216 | 0.79864037 |  | 241 | 0.71186364 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.313818558e-05 | 7.4934892e-06 | 0.083870031 | * | early_inv_amt_share | 993.6696233 | 861.45813 | 0.25258416 |  | fund_est_scale_cum#early_inv_a | -0.00878297545 | 0.0041957959 | 0.039897524 | ** | 241 | 0.76225215 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.709021994e-05 | 1.1972837e-05 | 0.15784355 |  | early_inv_amt_share | -28.43229627 | 1788.948 | 0.98736411 |  | fund_est_scale_cum#early_inv_a | 0.01330089692 | 0.018403465 | 0.47221449 |  | 241 | 0.66266346 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -3.836470982e-05 | 2.0698541e-05 | 0.066490635 | * | early_inv_amt_share | 2423.645612 | 2095.9153 | 0.25003663 |  | fund_est_scale_cum#early_inv_a | -0.001112476033 | 0.013132831 | 0.93264627 |  | 398 | 0.70689821 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.323488126e-05 | 5.7898146e-06 | 0.024176575 | ** | early_inv_amt_share | 39.81085783 | 656.78845 | 0.95177627 |  | fund_est_scale_cum#early_inv_a | 0.004107813234 | 0.0060299598 | 0.49715513 |  | 398 | 0.76916867 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_amt_share | fund_est_scale_cum#debt_pressu | -1.203447339e-05 | 1.0984641e-05 | 0.27565873 |  | early_inv_amt_share | 581.6910513 | 1788.2874 | 0.74558836 |  | fund_est_scale_cum#early_inv_a | -0.004042933438 | 0.0063669654 | 0.52675623 |  | 398 | 0.58584529 |
| ctrl | pat_apply_total | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -4.106733655e-05 | 1.1777001e-05 | 0.00067455386 | *** | early_inv_count | 375.8074889 | 129.34015 | 0.0043369615 | *** | fund_est_scale_cum#early_inv_c | -0.0001136090182 | 0.00010174324 | 0.26629663 |  | 683 | 0.7367056 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -1.00320741e-05 | 3.3496081e-06 | 0.0033096073 | *** | early_inv_count | 10.90028473 | 34.292263 | 0.7511183 |  | fund_est_scale_cum#early_inv_c | 6.53018196e-05 | 3.8095488e-05 | 0.088977568 | * | 683 | 0.73903984 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -2.152014411e-05 | 6.3358152e-06 | 0.00091539219 | *** | early_inv_count | 263.5789515 | 75.600883 | 0.00067599356 | *** | fund_est_scale_cum#early_inv_c | -0.0001610491355 | 5.2514428e-05 | 0.0026529108 | *** | 683 | 0.6449874 |
| noctrl | pat_apply_total | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -3.642476657e-05 | 9.4218512e-06 | 0.00015852481 | *** | early_inv_count | 408.7786013 | 120.927 | 0.00090243475 | *** | fund_est_scale_cum#early_inv_c | -0.0001551755134 | 7.6579512e-05 | 0.044331569 | ** | 1242 | 0.70488614 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -8.526646973e-06 | 2.752221e-06 | 0.0022877413 | *** | early_inv_count | -29.11198937 | 36.223198 | 0.4227291 |  | fund_est_scale_cum#early_inv_c | 9.162420829e-05 | 3.1511165e-05 | 0.0041394359 | *** | 1242 | 0.74535084 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_count | fund_est_scale_cum#debt_pressu | -2.022670398e-05 | 5.9166659e-06 | 0.00079195487 | *** | early_inv_count | 330.2448789 | 73.908325 | 1.4537783e-05 | *** | fund_est_scale_cum#early_inv_c | -0.0002149578442 | 4.0822197e-05 | 4.2768391e-07 | *** | 1242 | 0.59069538 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -4.042521227e-05 | 1.2161135e-05 | 0.0011640931 | *** | early_inv_count | 390.1524669 | 120.16469 | 0.0014983291 | *** | fund_est_scale_cum#early_inv_c | -0.0001041791648 | 9.0463909e-05 | 0.25167915 |  | 687 | 0.73978341 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -1.054733919e-05 | 3.5910211e-06 | 0.0039448552 | *** | early_inv_count | 19.19373292 | 31.051109 | 0.5376119 |  | fund_est_scale_cum#early_inv_c | 6.381995689e-05 | 3.3332195e-05 | 0.05782054 | * | 687 | 0.74190575 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -2.088781479e-05 | 6.6426414e-06 | 0.002078881 | *** | early_inv_count | 277.3035117 | 68.17775 | 8.3593834e-05 | *** | fund_est_scale_cum#early_inv_c | -0.0001581370697 | 4.6127181e-05 | 0.00082308333 | *** | 687 | 0.65601736 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -3.70094771e-05 | 1.013619e-05 | 0.00035003186 | *** | early_inv_count | 428.1031216 | 107.59378 | 0.00010348958 | *** | fund_est_scale_cum#early_inv_c | -0.000157270132 | 7.0668415e-05 | 0.027405318 | ** | 1243 | 0.71318281 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -8.457763035e-06 | 3.1370214e-06 | 0.0077428222 | *** | early_inv_count | -24.05091519 | 37.104286 | 0.51775807 |  | fund_est_scale_cum#early_inv_c | 9.10774517e-05 | 3.0812727e-05 | 0.0035752181 | *** | 1243 | 0.7455467 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count | fund_est_scale_cum#debt_pressu | -2.079223077e-05 | 6.3271741e-06 | 0.0012406488 | *** | early_inv_count | 354.3936197 | 66.618614 | 3.3427003e-07 | *** | fund_est_scale_cum#early_inv_c | -0.0002234087667 | 3.8915216e-05 | 4.4137852e-08 | *** | 1243 | 0.60849112 |
| ctrl | pat_apply_total | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -3.460333464e-05 | 1.653676e-05 | 0.039087482 | ** | early_inv_count_share | 2806.746001 | 1830.1417 | 0.12848157 |  | fund_est_scale_cum#early_inv_c | -0.06047406611 | 0.044589888 | 0.17827536 |  | 377 | 0.7002728 |
| ctrl | pat_invent_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.152681931e-05 | 4.2743732e-06 | 0.0082988851 | *** | early_inv_count_share | 409.0745524 | 708.77509 | 0.56521314 |  | fund_est_scale_cum#early_inv_c | -0.03662955565 | 0.020313941 | 0.074564993 | * | 377 | 0.74240887 |
| ctrl | pat_utility_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.299833558e-05 | 8.1712242e-06 | 0.1150246 |  | early_inv_count_share | 1447.811641 | 1185.5201 | 0.22504713 |  | fund_est_scale_cum#early_inv_c | -0.03175808605 | 0.021129768 | 0.13619076 |  | 377 | 0.6269151 |
| noctrl | pat_apply_total | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -3.283122904e-05 | 1.6492681e-05 | 0.048323546 | ** | early_inv_count_share | 1124.040585 | 1249.778 | 0.36987582 |  | fund_est_scale_cum#early_inv_c | -0.005515906491 | 0.036159538 | 0.87896186 |  | 675 | 0.68136674 |
| noctrl | pat_invent_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.362910914e-05 | 3.7115408e-06 | 0.00033328892 | *** | early_inv_count_share | 277.4848552 | 451.60449 | 0.53984785 |  | fund_est_scale_cum#early_inv_c | -0.01725517662 | 0.013495294 | 0.20299721 |  | 675 | 0.74266678 |
| noctrl | pat_utility_apply | debt_pressure | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.144625324e-05 | 9.2384425e-06 | 0.21727499 |  | early_inv_count_share | 340.5689321 | 853.11554 | 0.69030541 |  | fund_est_scale_cum#early_inv_c | -0.004075594697 | 0.015243473 | 0.78955179 |  | 675 | 0.5665859 |
| ctrl | pat_apply_total | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -4.22256474e-05 | 1.8286068e-05 | 0.023124512 | ** | early_inv_count_share | 2959.475697 | 2021.9265 | 0.14661448 |  | fund_est_scale_cum#early_inv_c | -0.05515112086 | 0.050858375 | 0.28095835 |  | 383 | 0.68057936 |
| ctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.575032579e-05 | 5.0733561e-06 | 0.0025186106 | *** | early_inv_count_share | 491.7434027 | 812.69879 | 0.54658741 |  | fund_est_scale_cum#early_inv_c | -0.03149451879 | 0.024791578 | 0.20708762 |  | 383 | 0.72830987 |
| ctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.505798218e-05 | 9.426165e-06 | 0.11351812 |  | early_inv_count_share | 1593.565196 | 1228.8329 | 0.19787014 |  | fund_est_scale_cum#early_inv_c | -0.02981292637 | 0.020901863 | 0.15708634 |  | 383 | 0.61740899 |
| noctrl | pat_apply_total | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -3.488237154e-05 | 1.7242886e-05 | 0.04486141 | ** | early_inv_count_share | 1139.744289 | 1263.1116 | 0.36833763 |  | fund_est_scale_cum#early_inv_c | -0.008875862839 | 0.03572211 | 0.80411315 |  | 683 | 0.67660522 |
| noctrl | pat_invent_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.451618568e-05 | 3.9624956e-06 | 0.00034526293 | *** | early_inv_count_share | 299.0404037 | 465.89233 | 0.52194649 |  | fund_est_scale_cum#early_inv_c | -0.01621969002 | 0.014071122 | 0.25088215 |  | 683 | 0.73765397 |
| noctrl | pat_utility_apply | debt_pressure_l1 | early_inv_count_share | fund_est_scale_cum#debt_pressu | -1.208939906e-05 | 9.8654946e-06 | 0.22234957 |  | early_inv_count_share | 392.3602427 | 868.55023 | 0.65211207 |  | fund_est_scale_cum#early_inv_c | -0.007448764274 | 0.014619901 | 0.61115915 |  | 683 | 0.56178784 |

## 输出文件
- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`
- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`
- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`