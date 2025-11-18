"""
Comprehensive Report Generator for AI Trading Models
Includes modular analyzers for Performance, Risk, Trend, Market Context, Behavior, and Change Detection
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database_enhanced import EnhancedDatabase
from market_context import MarketContextFetcher
import statistics


class PerformanceAnalyzer:
    """Analyze model performance metrics"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db

    def analyze(self, model_id: int, period_start: str, period_end: str) -> Dict:
        """Analyze performance for a model in given period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get trades in period
            cursor.execute('''
                SELECT * FROM trades
                WHERE model_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            ''', (model_id, period_start, period_end))

            trades = [dict(row) for row in cursor.fetchall()]

            if not trades:
                conn.close()
                return self._empty_performance()

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t['pnl'] > 0)
            losing_trades = sum(1 for t in trades if t['pnl'] <= 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            total_pnl = sum(t['pnl'] for t in trades)
            avg_profit_per_trade = total_pnl / total_trades if total_trades > 0 else 0

            # Get portfolio value at start and end
            cursor.execute('''
                SELECT portfolio_value FROM portfolio_history
                WHERE model_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC LIMIT 1
            ''', (model_id, period_start))

            start_row = cursor.fetchone()
            start_value = start_row['portfolio_value'] if start_row else 10000

            cursor.execute('''
                SELECT portfolio_value FROM portfolio_history
                WHERE model_id = ? AND timestamp <= ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (model_id, period_end))

            end_row = cursor.fetchone()
            end_value = end_row['portfolio_value'] if end_row else start_value

            net_roi = ((end_value - start_value) / start_value * 100) if start_value > 0 else 0

            # Calculate Sharpe ratio
            sharpe_ratio = self._calculate_sharpe_ratio(trades, start_value)

            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown(model_id, period_start, period_end, cursor)

            # Get cost breakdown
            total_fees = sum(t.get('fee', 0) for t in trades)
            total_slippage = sum(t.get('slippage', 0) for t in trades)

            # Estimate AI costs (simplified: $0.01 per decision)
            ai_costs = total_trades * 0.01

            total_costs = total_fees + total_slippage + ai_costs
            cost_impact_pct = (total_costs / start_value * 100) if start_value > 0 else 0

            conn.close()

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_profit_per_trade': round(avg_profit_per_trade, 2),
                'start_value': round(start_value, 2),
                'end_value': round(end_value, 2),
                'net_roi': round(net_roi, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'costs': {
                    'fees': round(total_fees, 2),
                    'slippage': round(total_slippage, 2),
                    'ai_costs': round(ai_costs, 2),
                    'total': round(total_costs, 2),
                    'impact_pct': round(cost_impact_pct, 2)
                }
            }

        except Exception as e:
            print(f"[ERROR] Performance analysis failed: {e}")
            return self._empty_performance()

    def _calculate_sharpe_ratio(self, trades: List[Dict], start_value: float) -> float:
        """Calculate Sharpe ratio"""
        if not trades or start_value == 0:
            return 0

        returns = [t['pnl'] / start_value for t in trades]
        if not returns:
            return 0

        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0

        if std_return == 0:
            return 0

        # Annualized Sharpe (assuming 365 trading days)
        sharpe = (avg_return / std_return) * (365 ** 0.5) if std_return > 0 else 0
        return sharpe

    def _calculate_max_drawdown(self, model_id: int, period_start: str, period_end: str, cursor) -> float:
        """Calculate maximum drawdown"""
        cursor.execute('''
            SELECT portfolio_value FROM portfolio_history
            WHERE model_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        ''', (model_id, period_start, period_end))

        values = [row['portfolio_value'] for row in cursor.fetchall()]

        if len(values) < 2:
            return 0

        peak = values[0]
        max_dd = 0

        for value in values:
            if value > peak:
                peak = value
            dd = (value - peak) / peak * 100
            if dd < max_dd:
                max_dd = dd

        return abs(max_dd)

    def _empty_performance(self) -> Dict:
        """Return empty performance metrics"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_profit_per_trade': 0,
            'start_value': 0,
            'end_value': 0,
            'net_roi': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'costs': {
                'fees': 0,
                'slippage': 0,
                'ai_costs': 0,
                'total': 0,
                'impact_pct': 0
            }
        }


class RiskAnalyzer:
    """Analyze risk compliance and violations"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db

    def analyze(self, model_id: int, period_start: str, period_end: str) -> Dict:
        """Analyze risk metrics and violations"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get risk violations
            cursor.execute('''
                SELECT * FROM incidents
                WHERE model_id = ? AND timestamp >= ? AND timestamp <= ?
                AND incident_type LIKE '%RISK%' OR incident_type LIKE '%VIOLATION%'
            ''', (model_id, period_start, period_end))

            violations = [dict(row) for row in cursor.fetchall()]

            # Get model settings (risk profile)
            settings = self.db.get_model_settings(model_id)

            conn.close()

            return {
                'total_violations': len(violations),
                'violation_types': self._categorize_violations(violations),
                'risk_profile': {
                    'max_position_size_pct': settings.get('max_position_size_pct', 10),
                    'max_daily_loss_pct': settings.get('max_daily_loss_pct', 3),
                    'max_drawdown_pct': settings.get('max_drawdown_pct', 15)
                },
                'compliance_rate': 100 if len(violations) == 0 else 0  # Simplified
            }

        except Exception as e:
            print(f"[ERROR] Risk analysis failed: {e}")
            return {
                'total_violations': 0,
                'violation_types': {},
                'risk_profile': {},
                'compliance_rate': 100
            }

    def _categorize_violations(self, violations: List[Dict]) -> Dict:
        """Categorize violations by type"""
        categories = {}
        for v in violations:
            vtype = v['incident_type']
            categories[vtype] = categories.get(vtype, 0) + 1
        return categories


class TrendAnalyzer:
    """Analyze week-over-week trends"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db

    def analyze(self, model_id: int, period_end: str, lookback_weeks: int = 4) -> Dict:
        """Analyze trends for the last N weeks"""
        try:
            end_date = datetime.strptime(period_end, '%Y-%m-%d')
            weeks_data = []

            for week in range(lookback_weeks, 0, -1):
                week_end = end_date - timedelta(weeks=week-1)
                week_start = week_end - timedelta(days=7)

                perf_analyzer = PerformanceAnalyzer(self.db)
                week_perf = perf_analyzer.analyze(
                    model_id,
                    week_start.strftime('%Y-%m-%d'),
                    week_end.strftime('%Y-%m-%d')
                )

                # Get reasoning quality for this week
                reasoning_score = self._get_avg_reasoning_quality(
                    model_id,
                    week_start.strftime('%Y-%m-%d'),
                    week_end.strftime('%Y-%m-%d')
                )

                weeks_data.append({
                    'week_label': f'W-{week}',
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'week_end': week_end.strftime('%Y-%m-%d'),
                    'net_roi': week_perf['net_roi'],
                    'win_rate': week_perf['win_rate'],
                    'reasoning_quality': reasoning_score,
                    'total_trades': week_perf['total_trades']
                })

            # Determine trend direction
            if len(weeks_data) >= 2:
                recent_roi = weeks_data[-1]['net_roi']
                prev_roi = weeks_data[-2]['net_roi']
                trend = self._classify_trend(recent_roi - prev_roi)
            else:
                trend = 'insufficient_data'

            return {
                'weeks': weeks_data,
                'trend_direction': trend,
                'lookback_weeks': lookback_weeks
            }

        except Exception as e:
            print(f"[ERROR] Trend analysis failed: {e}")
            return {
                'weeks': [],
                'trend_direction': 'error',
                'lookback_weeks': lookback_weeks
            }

    def _get_avg_reasoning_quality(self, model_id: int, period_start: str, period_end: str) -> float:
        """Get average reasoning quality score"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT AVG(reasoning_quality) as avg_quality FROM reasoning_log
                WHERE model_id = ? AND timestamp >= ? AND timestamp <= ?
            ''', (model_id, period_start, period_end))

            row = cursor.fetchone()
            conn.close()

            return round(row['avg_quality'], 1) if row and row['avg_quality'] else 0

        except Exception:
            return 0

    def _classify_trend(self, change: float) -> str:
        """Classify trend based on change"""
        if change > 2:
            return 'improving'
        elif change < -2:
            return 'declining'
        else:
            return 'stable'


class BehaviorAnalyzer:
    """Analyze trading behavior patterns"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db

    def analyze(self, model_id: int, period_start: str, period_end: str) -> Dict:
        """Analyze trading behavior"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM trades
                WHERE model_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            ''', (model_id, period_start, period_end))

            trades = [dict(row) for row in cursor.fetchall()]
            conn.close()

            if not trades:
                return self._empty_behavior()

            # Calculate trade frequency
            start = datetime.strptime(period_start, '%Y-%m-%d')
            end = datetime.strptime(period_end, '%Y-%m-%d')
            days = max((end - start).days, 1)
            trades_per_day = len(trades) / days

            # Calculate average holding time (using entry and exit timestamps)
            avg_holding_hours = self._calculate_avg_holding_time(trades)

            # Entry/exit timing quality (simplified based on win rate)
            winning_trades = sum(1 for t in trades if t['pnl'] > 0)
            timing_quality = (winning_trades / len(trades) * 10) if trades else 0

            return {
                'trades_per_day': round(trades_per_day, 1),
                'avg_holding_hours': round(avg_holding_hours, 1),
                'entry_exit_timing_quality': round(timing_quality, 1),
                'total_trades': len(trades)
            }

        except Exception as e:
            print(f"[ERROR] Behavior analysis failed: {e}")
            return self._empty_behavior()

    def _calculate_avg_holding_time(self, trades: List[Dict]) -> float:
        """Calculate average holding time in hours"""
        # Simplified: assume average hold time based on trade frequency
        # In real implementation, would track entry/exit timestamps
        return 18.0  # Default assumption

    def _empty_behavior(self) -> Dict:
        return {
            'trades_per_day': 0,
            'avg_holding_hours': 0,
            'entry_exit_timing_quality': 0,
            'total_trades': 0
        }


class ChangeDetectionAnalyzer:
    """Detect week-over-week changes"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db

    def analyze(self, model_id: int, current_week_start: str, current_week_end: str) -> Dict:
        """Detect changes from previous week"""
        try:
            # Get current week performance
            perf_analyzer = PerformanceAnalyzer(self.db)
            current_perf = perf_analyzer.analyze(model_id, current_week_start, current_week_end)

            # Get previous week
            current_start = datetime.strptime(current_week_start, '%Y-%m-%d')
            prev_week_end = current_start - timedelta(days=1)
            prev_week_start = prev_week_end - timedelta(days=6)

            prev_perf = perf_analyzer.analyze(
                model_id,
                prev_week_start.strftime('%Y-%m-%d'),
                prev_week_end.strftime('%Y-%m-%d')
            )

            # Calculate deltas
            changes = {
                'net_roi': {
                    'current': current_perf['net_roi'],
                    'previous': prev_perf['net_roi'],
                    'change': current_perf['net_roi'] - prev_perf['net_roi'],
                    'direction': self._get_direction(current_perf['net_roi'] - prev_perf['net_roi'])
                },
                'win_rate': {
                    'current': current_perf['win_rate'],
                    'previous': prev_perf['win_rate'],
                    'change': current_perf['win_rate'] - prev_perf['win_rate'],
                    'direction': self._get_direction(current_perf['win_rate'] - prev_perf['win_rate'])
                },
                'max_drawdown': {
                    'current': current_perf['max_drawdown'],
                    'previous': prev_perf['max_drawdown'],
                    'change': current_perf['max_drawdown'] - prev_perf['max_drawdown'],
                    'direction': self._get_direction(-(current_perf['max_drawdown'] - prev_perf['max_drawdown']))  # Lower is better
                }
            }

            return changes

        except Exception as e:
            print(f"[ERROR] Change detection failed: {e}")
            return {}

    def _get_direction(self, change: float) -> str:
        """Get direction symbol"""
        if change > 0.5:
            return '↗'
        elif change < -0.5:
            return '↘'
        else:
            return '→'


class ConfidenceScoreCalculator:
    """Calculate confidence score for recommendations"""

    def calculate(self, model_data: Dict, market_context: Dict) -> Tuple[float, Dict]:
        """
        Calculate confidence score (0-100) and breakdown

        Returns:
            (confidence_score, breakdown_dict)
        """
        components = {}

        # Sample size (0-20 points)
        total_trades = model_data['performance']['total_trades']
        if total_trades >= 50:
            components['sample_size'] = 20
        elif total_trades >= 30:
            components['sample_size'] = 15
        elif total_trades >= 15:
            components['sample_size'] = 10
        else:
            components['sample_size'] = 5

        # Consistency (0-20 points) - based on Sharpe ratio
        sharpe = model_data['performance']['sharpe_ratio']
        if sharpe >= 2.0:
            components['consistency'] = 20
        elif sharpe >= 1.5:
            components['consistency'] = 15
        elif sharpe >= 1.0:
            components['consistency'] = 10
        else:
            components['consistency'] = 5

        # Trend direction (0-15 points)
        trend = model_data.get('trend', {}).get('trend_direction', 'stable')
        if trend == 'improving':
            components['trend'] = 15
        elif trend == 'stable':
            components['trend'] = 10
        else:
            components['trend'] = 5

        # Risk compliance (0-15 points)
        violations = model_data['risk']['total_violations']
        if violations == 0:
            components['risk_compliance'] = 15
        elif violations <= 2:
            components['risk_compliance'] = 10
        else:
            components['risk_compliance'] = 5

        # Market regime penalty (0 to -10)
        # Only tested in one market condition
        components['market_regime'] = -10

        # Time period penalty (0 to -8)
        # Only one week of data
        components['time_period'] = -8

        # Calculate total
        total_confidence = sum(components.values())
        total_confidence = max(0, min(100, total_confidence))  # Clamp to 0-100

        return round(total_confidence, 0), components


class ScoringAlgorithm:
    """Calculate overall score for model ranking"""

    def calculate_score(self, model_data: Dict) -> float:
        """
        Calculate weighted score (0-100) for model ranking

        Weights:
        - Net ROI: 25%
        - Sharpe Ratio: 15%
        - vs Benchmark: 15%
        - Reasoning Quality: 15%
        - Risk Compliance: 15%
        - Consistency: 10%
        - Cost Efficiency: 5%
        """
        perf = model_data['performance']
        risk = model_data['risk']

        # Net ROI (0-25 points)
        roi_score = self._normalize_roi(perf['net_roi']) * 25

        # Sharpe Ratio (0-15 points)
        sharpe_score = self._normalize_sharpe(perf['sharpe_ratio']) * 15

        # vs Benchmark (0-15 points) - placeholder, will calculate later
        benchmark_score = 10  # Neutral

        # Reasoning Quality (0-15 points) - placeholder
        reasoning_score = 12  # Default decent score

        # Risk Compliance (0-15 points)
        compliance_score = 15 if risk['total_violations'] == 0 else max(0, 15 - risk['total_violations'] * 3)

        # Consistency (0-10 points) - based on win rate
        consistency_score = (perf['win_rate'] / 100) * 10

        # Cost Efficiency (0-5 points)
        cost_impact = perf['costs']['impact_pct']
        cost_score = max(0, 5 - cost_impact * 2)

        total_score = (
            roi_score +
            sharpe_score +
            benchmark_score +
            reasoning_score +
            compliance_score +
            consistency_score +
            cost_score
        )

        return round(min(100, max(0, total_score)), 1)

    def _normalize_roi(self, roi: float) -> float:
        """Normalize ROI to 0-1 scale"""
        # 20% ROI = 1.0, 0% = 0.5, -10% = 0
        normalized = (roi + 10) / 30
        return max(0, min(1, normalized))

    def _normalize_sharpe(self, sharpe: float) -> float:
        """Normalize Sharpe ratio to 0-1 scale"""
        # 2.0 or higher = 1.0, 1.0 = 0.5, 0 = 0
        normalized = sharpe / 2.0
        return max(0, min(1, normalized))


class ReportGenerator:
    """Main report generator orchestrating all analyzers"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db
        self.market_fetcher = MarketContextFetcher()

        # Initialize analyzers
        self.performance_analyzer = PerformanceAnalyzer(db)
        self.risk_analyzer = RiskAnalyzer(db)
        self.trend_analyzer = TrendAnalyzer(db)
        self.behavior_analyzer = BehaviorAnalyzer(db)
        self.change_detector = ChangeDetectionAnalyzer(db)
        self.confidence_calculator = ConfidenceScoreCalculator()
        self.scoring_algorithm = ScoringAlgorithm()

    def generate_weekly_comparative_report(self, model_ids: List[int], period_start: str, period_end: str) -> Dict:
        """Generate weekly comparative report for multiple models"""
        try:
            models_data = []

            for model_id in model_ids:
                model_data = self._analyze_model(model_id, period_start, period_end)
                models_data.append(model_data)

            # Get market context
            market_context = self.market_fetcher.get_market_context(period_start, period_end)

            # Rank models
            ranked_models = self._rank_models(models_data)

            # Generate recommendation
            recommendation = self._generate_recommendation(ranked_models[0]) if ranked_models else 'no_models'

            # Calculate confidence
            confidence, confidence_breakdown = self.confidence_calculator.calculate(
                ranked_models[0],
                market_context
            ) if ranked_models else (0, {})

            return {
                'report_type': 'weekly_comparative',
                'period_start': period_start,
                'period_end': period_end,
                'models': ranked_models,
                'market_context': market_context,
                'recommendation': recommendation,
                'confidence_score': confidence,
                'confidence_breakdown': confidence_breakdown,
                'top_model_id': ranked_models[0]['model_id'] if ranked_models else None
            }

        except Exception as e:
            print(f"[ERROR] Report generation failed: {e}")
            raise

    def _analyze_model(self, model_id: int, period_start: str, period_end: str) -> Dict:
        """Analyze a single model comprehensively"""
        # Get model info
        model = self.db.get_model(model_id)

        # Run all analyzers
        performance = self.performance_analyzer.analyze(model_id, period_start, period_end)
        risk = self.risk_analyzer.analyze(model_id, period_start, period_end)

        # Get settings for trend lookback
        settings = self.db.get_report_settings()
        lookback_weeks = settings.get('trend_lookback_weeks', 2)

        trend = self.trend_analyzer.analyze(model_id, period_end, lookback_weeks) if settings.get('enable_trend_analysis') else None
        behavior = self.behavior_analyzer.analyze(model_id, period_start, period_end) if settings.get('enable_behavior_analysis') else None
        changes = self.change_detector.analyze(model_id, period_start, period_end) if settings.get('enable_change_detection') else None

        model_data = {
            'model_id': model_id,
            'model_name': model['name'],
            'performance': performance,
            'risk': risk,
            'trend': trend,
            'behavior': behavior,
            'changes': changes
        }

        # Calculate score
        model_data['score'] = self.scoring_algorithm.calculate_score(model_data)

        return model_data

    def _rank_models(self, models_data: List[Dict]) -> List[Dict]:
        """Rank models by score"""
        ranked = sorted(models_data, key=lambda m: m['score'], reverse=True)

        # Add rank
        for i, model in enumerate(ranked):
            model['rank'] = i + 1

        return ranked

    def _generate_recommendation(self, top_model: Dict) -> str:
        """Generate go-live recommendation"""
        score = top_model['score']
        roi = top_model['performance']['net_roi']
        violations = top_model['risk']['total_violations']

        if score >= 80 and roi > 8 and violations == 0:
            return 'go_live'
        elif score >= 60 and roi > 5:
            return 'continue_testing'
        else:
            return 'not_ready'


# For testing
if __name__ == '__main__':
    from database_enhanced import EnhancedDatabase

    db = EnhancedDatabase('AITradeGame.db')
    generator = ReportGenerator(db)

    # Test report generation
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    report = generator.generate_weekly_comparative_report(
        model_ids=[1],
        period_start=start_date.strftime('%Y-%m-%d'),
        period_end=end_date.strftime('%Y-%m-%d')
    )

    print(json.dumps(report, indent=2))
