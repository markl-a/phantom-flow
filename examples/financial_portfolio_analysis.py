"""
金融投資組合分析範例

這個範例展示如何分析投資組合表現，包含：
- 投資組合風險評估
- 資產配置優化
- 績效歸因分析
- 風險價值 (VaR) 計算

真實應用場景:
- 資產管理公司投資組合監控
- 個人投資者資產配置
- 銀行風險管理部門
- 保險公司資產負債管理
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import KMeansClusterer
except ImportError:
    import sys
    sys.path.insert(0, '..')


class PortfolioAnalyzer:
    """
    投資組合分析器

    提供完整的投資組合分析功能:
    - 績效指標計算 (收益率、夏普比率、最大回撤)
    - 風險評估 (波動率、VaR、Beta)
    - 資產相關性分析
    - 投資組合優化建議
    """

    def __init__(self, prices_df: pd.DataFrame, portfolio: Dict[str, float]):
        """
        初始化分析器

        Args:
            prices_df: 資產價格DataFrame，索引為日期，列為資產代碼
            portfolio: 投資組合權重字典 {資產代碼: 權重}
        """
        self.prices = prices_df.copy()
        self.portfolio = portfolio
        self.returns = self.prices.pct_change().dropna()
        self._validate_portfolio()

    def _validate_portfolio(self):
        """驗證投資組合權重"""
        total_weight = sum(self.portfolio.values())
        if abs(total_weight - 1.0) > 0.01:
            print(f"⚠️ 投資組合權重總和為 {total_weight:.2%}，已自動標準化")
            for asset in self.portfolio:
                self.portfolio[asset] /= total_weight

    def calculate_portfolio_returns(self) -> pd.Series:
        """計算投資組合加權收益率"""
        portfolio_returns = pd.Series(0, index=self.returns.index)
        for asset, weight in self.portfolio.items():
            if asset in self.returns.columns:
                portfolio_returns += self.returns[asset] * weight
        return portfolio_returns

    def calculate_performance_metrics(self, risk_free_rate: float = 0.02) -> Dict[str, float]:
        """
        計算績效指標

        Args:
            risk_free_rate: 無風險利率 (年化)

        Returns:
            績效指標字典
        """
        portfolio_returns = self.calculate_portfolio_returns()

        # 年化收益率
        total_days = (self.prices.index[-1] - self.prices.index[0]).days
        total_return = (1 + portfolio_returns).prod() - 1
        annual_return = (1 + total_return) ** (365 / total_days) - 1

        # 年化波動率
        annual_volatility = portfolio_returns.std() * np.sqrt(252)

        # 夏普比率
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0

        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 卡瑪比率 (收益/最大回撤)
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 索提諾比率 (只考慮下行風險)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (annual_return - risk_free_rate) / downside_std if downside_std > 0 else 0

        # 勝率
        win_rate = (portfolio_returns > 0).sum() / len(portfolio_returns)

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trading_days': len(portfolio_returns)
        }

    def calculate_var(self, confidence_level: float = 0.95,
                      method: str = 'historical') -> Dict[str, float]:
        """
        計算風險價值 (Value at Risk)

        Args:
            confidence_level: 信心水準
            method: 計算方法 ('historical', 'parametric')

        Returns:
            VaR 相關指標
        """
        portfolio_returns = self.calculate_portfolio_returns()

        if method == 'historical':
            var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        else:  # parametric
            mu = portfolio_returns.mean()
            sigma = portfolio_returns.std()
            from scipy import stats
            z_score = stats.norm.ppf(1 - confidence_level)
            var = mu + z_score * sigma

        # CVaR (Expected Shortfall)
        cvar = portfolio_returns[portfolio_returns <= var].mean()

        return {
            'var_1d': var,
            'var_1d_amount': var * 1000000,  # 假設100萬投資
            'cvar': cvar,
            'confidence_level': confidence_level,
            'method': method
        }

    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """計算資產相關性矩陣"""
        assets = [a for a in self.portfolio.keys() if a in self.returns.columns]
        return self.returns[assets].corr()

    def calculate_asset_metrics(self) -> pd.DataFrame:
        """計算各資產的績效指標"""
        metrics = []
        for asset in self.portfolio.keys():
            if asset not in self.returns.columns:
                continue

            returns = self.returns[asset]
            annual_return = returns.mean() * 252
            annual_vol = returns.std() * np.sqrt(252)
            sharpe = annual_return / annual_vol if annual_vol > 0 else 0

            # 計算 Beta (相對於投資組合)
            portfolio_returns = self.calculate_portfolio_returns()
            cov = returns.cov(portfolio_returns)
            var = portfolio_returns.var()
            beta = cov / var if var > 0 else 1

            metrics.append({
                'asset': asset,
                'weight': self.portfolio[asset],
                'annual_return': annual_return,
                'annual_volatility': annual_vol,
                'sharpe_ratio': sharpe,
                'beta': beta,
                'contribution': self.portfolio[asset] * annual_return
            })

        return pd.DataFrame(metrics).set_index('asset')

    def suggest_rebalancing(self) -> Dict[str, any]:
        """建議投資組合再平衡"""
        asset_metrics = self.calculate_asset_metrics()
        correlation = self.calculate_correlation_matrix()

        suggestions = []

        # 分析過度集中
        max_weight_asset = max(self.portfolio.items(), key=lambda x: x[1])
        if max_weight_asset[1] > 0.4:
            suggestions.append({
                'type': 'concentration_risk',
                'severity': 'HIGH',
                'message': f"資產 {max_weight_asset[0]} 佔比過高 ({max_weight_asset[1]:.1%})，建議降低至 40% 以下"
            })

        # 分析低績效資產
        for asset, row in asset_metrics.iterrows():
            if row['sharpe_ratio'] < 0 and row['weight'] > 0.1:
                suggestions.append({
                    'type': 'poor_performance',
                    'severity': 'MEDIUM',
                    'message': f"資產 {asset} 夏普比率為負 ({row['sharpe_ratio']:.2f})，建議減少配置"
                })

        # 分析高相關性
        for i, asset1 in enumerate(correlation.index):
            for j, asset2 in enumerate(correlation.columns):
                if i < j and correlation.loc[asset1, asset2] > 0.8:
                    suggestions.append({
                        'type': 'high_correlation',
                        'severity': 'LOW',
                        'message': f"{asset1} 與 {asset2} 相關性高 ({correlation.loc[asset1, asset2]:.2f})，分散效果有限"
                    })

        return {
            'current_allocation': self.portfolio,
            'suggestions': suggestions,
            'recommendation': self._generate_optimal_weights(asset_metrics)
        }

    def _generate_optimal_weights(self, metrics: pd.DataFrame) -> Dict[str, float]:
        """基於夏普比率生成建議權重"""
        # 簡化版本：按夏普比率調整權重
        sharpe_ratios = metrics['sharpe_ratio'].clip(lower=0)
        if sharpe_ratios.sum() > 0:
            optimal = sharpe_ratios / sharpe_ratios.sum()
            return optimal.to_dict()
        return self.portfolio

    def generate_report(self) -> str:
        """生成完整的投資組合分析報告"""
        metrics = self.calculate_performance_metrics()
        var_data = self.calculate_var()
        asset_metrics = self.calculate_asset_metrics()
        rebalance = self.suggest_rebalancing()

        report = f"""
{'='*80}
                    投資組合分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、投資組合概覽
{'='*40}
  分析期間: {self.prices.index[0].strftime('%Y-%m-%d')} ~ {self.prices.index[-1].strftime('%Y-%m-%d')}
  交易天數: {metrics['trading_days']}
  資產數量: {len(self.portfolio)}

  資產配置:
"""
        for asset, weight in sorted(self.portfolio.items(), key=lambda x: -x[1]):
            bar = '█' * int(weight * 40)
            report += f"    {asset:10}: {weight:6.1%} {bar}\n"

        report += f"""
二、績效指標
{'='*40}
  總收益率: {metrics['total_return']:+.2%}
  年化收益率: {metrics['annual_return']:+.2%}
  年化波動率: {metrics['annual_volatility']:.2%}

  風險調整收益:
    夏普比率: {metrics['sharpe_ratio']:.3f}
    索提諾比率: {metrics['sortino_ratio']:.3f}
    卡瑪比率: {metrics['calmar_ratio']:.3f}

  其他指標:
    最大回撤: {metrics['max_drawdown']:.2%}
    勝率: {metrics['win_rate']:.1%}

三、風險評估 (VaR)
{'='*40}
  信心水準: {var_data['confidence_level']:.0%}
  計算方法: {var_data['method']}

  每日VaR: {var_data['var_1d']:.2%}
  CVaR (Expected Shortfall): {var_data['cvar']:.2%}

  以 $1,000,000 投資為例:
    每日最大損失 (95%信心): ${abs(var_data['var_1d_amount']):,.0f}

四、資產分析
{'='*40}
"""
        for asset, row in asset_metrics.iterrows():
            report += f"""
  {asset}:
    權重: {row['weight']:.1%}
    年化收益: {row['annual_return']:+.2%}
    年化波動: {row['annual_volatility']:.2%}
    夏普比率: {row['sharpe_ratio']:.3f}
    Beta: {row['beta']:.2f}
    收益貢獻: {row['contribution']:+.2%}
"""

        report += f"""
五、相關性矩陣
{'='*40}
{self.calculate_correlation_matrix().round(2).to_string()}

六、再平衡建議
{'='*40}
"""
        if rebalance['suggestions']:
            for i, suggestion in enumerate(rebalance['suggestions'], 1):
                severity_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
                icon = severity_icon.get(suggestion['severity'], '⚪')
                report += f"  {i}. {icon} [{suggestion['type']}] {suggestion['message']}\n"
        else:
            report += "  ✅ 當前配置合理，無需調整\n"

        report += f"""
七、建議配置
{'='*40}
"""
        for asset, weight in sorted(rebalance['recommendation'].items(), key=lambda x: -x[1]):
            current = self.portfolio.get(asset, 0)
            diff = weight - current
            arrow = '↑' if diff > 0.01 else ('↓' if diff < -0.01 else '→')
            report += f"    {asset:10}: {weight:6.1%} ({arrow} {diff:+.1%})\n"

        report += f"""
{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_stock_data(symbols: List[str],
                        days: int = 365,
                        seed: int = 42) -> pd.DataFrame:
    """
    生成模擬股票價格數據

    模擬真實股票特性:
    - 幾何布朗運動
    - 不同的預期收益率和波動率
    - 市場相關性
    """
    np.random.seed(seed)

    # 資產特性設定
    asset_params = {
        'AAPL': {'mu': 0.15, 'sigma': 0.25, 'price': 150},
        'GOOGL': {'mu': 0.12, 'sigma': 0.22, 'price': 120},
        'MSFT': {'mu': 0.14, 'sigma': 0.20, 'price': 300},
        'AMZN': {'mu': 0.18, 'sigma': 0.30, 'price': 130},
        'TSLA': {'mu': 0.20, 'sigma': 0.50, 'price': 200},
        'META': {'mu': 0.10, 'sigma': 0.35, 'price': 280},
        'NVDA': {'mu': 0.25, 'sigma': 0.45, 'price': 400},
        'BRK': {'mu': 0.08, 'sigma': 0.15, 'price': 350},
        'JNJ': {'mu': 0.06, 'sigma': 0.12, 'price': 160},
        'XOM': {'mu': 0.07, 'sigma': 0.18, 'price': 100},
        'BOND': {'mu': 0.03, 'sigma': 0.05, 'price': 100},
        'GOLD': {'mu': 0.05, 'sigma': 0.15, 'price': 1800},
    }

    # 生成日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 營業日

    # 生成價格
    prices = {}

    # 市場因子 (共同影響)
    market_returns = np.random.normal(0.0003, 0.01, len(dates))

    for symbol in symbols:
        if symbol in asset_params:
            params = asset_params[symbol]
        else:
            params = {'mu': 0.10, 'sigma': 0.20, 'price': 100}

        # 日收益率參數
        daily_mu = params['mu'] / 252
        daily_sigma = params['sigma'] / np.sqrt(252)

        # 特異性收益 + 市場影響
        idio_returns = np.random.normal(daily_mu, daily_sigma, len(dates))
        beta = np.random.uniform(0.5, 1.5)  # 市場敏感度
        total_returns = 0.3 * market_returns * beta + 0.7 * idio_returns

        # 價格路徑
        price_path = [params['price']]
        for ret in total_returns[1:]:
            price_path.append(price_path[-1] * (1 + ret))

        prices[symbol] = price_path

    return pd.DataFrame(prices, index=dates)


def main():
    """執行投資組合分析範例"""
    print("="*80)
    print(" "*20 + "投資組合分析範例")
    print("="*80)

    # ========================================
    # 1. 準備數據
    # ========================================
    print("\n[1/4] 準備投資組合數據...")

    # 定義投資組合
    portfolio = {
        'AAPL': 0.20,   # 蘋果
        'GOOGL': 0.15,  # 谷歌
        'MSFT': 0.15,   # 微軟
        'NVDA': 0.10,   # 輝達
        'JNJ': 0.10,    # 嬌生 (防守型)
        'BOND': 0.20,   # 債券
        'GOLD': 0.10,   # 黃金
    }

    # 生成價格數據
    prices = generate_stock_data(list(portfolio.keys()), days=500)

    print(f"  ✓ 投資組合包含 {len(portfolio)} 項資產")
    print(f"  ✓ 分析期間: {prices.index[0].strftime('%Y-%m-%d')} ~ {prices.index[-1].strftime('%Y-%m-%d')}")
    print(f"  ✓ 交易天數: {len(prices)}")

    # ========================================
    # 2. 初始化分析器
    # ========================================
    print("\n[2/4] 初始化投資組合分析器...")
    analyzer = PortfolioAnalyzer(prices, portfolio)
    print("  ✓ 分析器初始化完成")

    # ========================================
    # 3. 計算績效指標
    # ========================================
    print("\n[3/4] 計算績效指標...")

    metrics = analyzer.calculate_performance_metrics()
    print(f"\n  📊 績效摘要:")
    print(f"     年化收益率: {metrics['annual_return']:+.2%}")
    print(f"     年化波動率: {metrics['annual_volatility']:.2%}")
    print(f"     夏普比率: {metrics['sharpe_ratio']:.3f}")
    print(f"     最大回撤: {metrics['max_drawdown']:.2%}")

    var_data = analyzer.calculate_var()
    print(f"\n  ⚠️ 風險評估:")
    print(f"     每日VaR (95%): {var_data['var_1d']:.2%}")
    print(f"     CVaR: {var_data['cvar']:.2%}")

    # ========================================
    # 4. 資產分析
    # ========================================
    print("\n[4/4] 分析各資產表現...")

    asset_metrics = analyzer.calculate_asset_metrics()
    print("\n  📈 資產績效排名 (按夏普比率):")
    ranked = asset_metrics.sort_values('sharpe_ratio', ascending=False)
    for i, (asset, row) in enumerate(ranked.iterrows(), 1):
        print(f"     {i}. {asset}: 夏普 {row['sharpe_ratio']:.2f}, 收益 {row['annual_return']:+.1%}")

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存報告
    try:
        with open('data/outputs/portfolio_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/portfolio_analysis_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
