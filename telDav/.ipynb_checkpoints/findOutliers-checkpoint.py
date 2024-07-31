# findOutliers.py
# Function collections of outlier finders
# Satoshi Miyazaki / Subaru Telescope, NAOJ
# June 14, 2024

import numpy as np

def byPercentile(ts, cut):
    l = np.percentile(ts, cut)
    h = np.percentile(ts, 100-cut)
    print(l, h)
    outliers = ts[(ts > h) | (ts < l)]
    return outliers

def byMovingMean(ts, window, cut):
    moving_average = ts.rolling(window=window).mean()

    # 差分を計算
    diff = ts - moving_average

    # 外れ値を検出（ここでは差分が標準偏差の3倍を超えるものを外れ値とする）
    threshold = cut * diff.std()
    outliers = ts[np.abs(diff) > threshold]
    return outliers

from statsmodels.tsa.holtwinters import ExponentialSmoothing

def byExponentialSmoothing(ts):
    # エクスポネンシャルスムージングを適用
    model = ExponentialSmoothing(ts, trend='add', seasonal=None)
    fit = model.fit(smoothing_level=0.8, optimized=False)
    smoothed = fit.fittedvalues

    # 差分を計算
    diff = ts - smoothed

    # 外れ値を検出（ここでは差分が標準偏差の3倍を超えるものを外れ値とする）
    threshold = 3 * diff.std()
    outliers = ts[np.abs(diff) > threshold]
    return outliers

def byPctChange(ts, cut):
    returns = ts.pct_change()

    # 外れ値を検出（ここでは変動率が標準偏差の3倍を超えるものを外れ値とする）
    threshold = cut * returns.std()
    outliers = ts[np.abs(returns) > threshold]
    return outliers