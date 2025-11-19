"""
Market Condition Analyzer and Profile Recommender
Analyzes existing trade data to recommend optimal risk profiles
No external APIs required - uses only internal trade history
"""

from typing import Dict, List, Tuple
from database_enhanced import EnhancedDatabase
import math

class MarketAnalyzer:
    """Analyzes market conditions and recommends risk profiles"""

    def __init__(self, db: EnhancedDatabase):
        self.db = db

    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate from trades"""
        if not trades:
            return 0.0

        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return (winning_trades / len(trades)) * 100

    def calculate_volatility(self, trades: List[Dict]) -> float:
        """
        Calculate volatility from trade PnL
        Returns: Standard deviation of PnL as percentage
        """
        if len(trades) < 5:
            return 0.0

        pnls = [t.get('pnl', 0) for t in trades]

        # Calculate mean
        mean_pnl = sum(pnls) / len(pnls)

        # Calculate variance
        variance = sum((pnl - mean_pnl) ** 2 for pnl in pnls) / len(pnls)

        # Standard deviation
        std_dev = math.sqrt(variance)

        # Return as absolute value (volatility is always positive)
        return abs(std_dev)

    def calculate_drawdown(self, model_id: int) -> Tuple[float, float]:
        """
        Calculate current drawdown from peak
        Returns: (current_drawdown_pct, peak_value)
        """
        try:
            # Get portfolio history
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT portfolio_value FROM portfolio_history
                WHERE model_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (model_id,))

            history = cursor.fetchall()
            conn.close()

            if not history:
                return 0.0, 0.0

            values = [row['portfolio_value'] for row in history]
            current_value = values[0]
            peak_value = max(values)

            if peak_value == 0:
                return 0.0, 0.0

            drawdown_pct = ((current_value - peak_value) / peak_value) * 100

            return drawdown_pct, peak_value

        except Exception as e:
            print(f"Error calculating drawdown: {e}")
            return 0.0, 0.0

    def calculate_consecutive_losses(self, trades: List[Dict]) -> int:
        """Calculate current consecutive losses"""
        if not trades:
            return 0

        consecutive_losses = 0

        for trade in reversed(trades):  # Start from most recent
            if trade.get('pnl', 0) <= 0:
                consecutive_losses += 1
            else:
                break  # Stop at first winning trade

        return consecutive_losses

    def calculate_daily_performance(self, model_id: int) -> Dict:
        """Calculate today's performance metrics"""
        try:
            from datetime import datetime

            # Get model info for initial capital
            model = self.db.get_model(model_id)
            initial_capital = model['initial_capital']

            # Get current portfolio value
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT portfolio_value FROM portfolio_history
                WHERE model_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (model_id,))

            current_row = cursor.fetchone()
            current_value = current_row['portfolio_value'] if current_row else initial_capital

            # Calculate daily P&L
            daily_pnl = current_value - initial_capital
            daily_pnl_pct = (daily_pnl / initial_capital * 100) if initial_capital > 0 else 0

            # Count today's trades
            today = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT COUNT(*) as count FROM trades
                WHERE model_id = ? AND timestamp LIKE ? AND signal != 'hold'
            ''', (model_id, f'{today}%'))

            trades_today = cursor.fetchone()['count']

            conn.close()

            return {
                'daily_pnl': daily_pnl,
                'daily_pnl_pct': daily_pnl_pct,
                'trades_today': trades_today,
                'current_value': current_value
            }

        except Exception as e:
            print(f"Error calculating daily performance: {e}")
            return {
                'daily_pnl': 0,
                'daily_pnl_pct': 0,
                'trades_today': 0,
                'current_value': 0
            }

    def get_market_metrics(self, model_id: int) -> Dict:
        """
        Calculate all market condition metrics
        Returns comprehensive analysis of current conditions
        """
        # Get recent trades (last 30)
        all_trades = self.db.get_trades(model_id, limit=50)
        recent_trades = all_trades[:30] if len(all_trades) > 30 else all_trades
        very_recent_trades = all_trades[:10] if len(all_trades) > 10 else all_trades

        # Calculate metrics
        win_rate = self.calculate_win_rate(recent_trades)
        recent_win_rate = self.calculate_win_rate(very_recent_trades)
        volatility = self.calculate_volatility(recent_trades)
        drawdown_pct, peak_value = self.calculate_drawdown(model_id)
        consecutive_losses = self.calculate_consecutive_losses(all_trades)
        daily_perf = self.calculate_daily_performance(model_id)

        return {
            'win_rate': win_rate,
            'recent_win_rate': recent_win_rate,  # Last 10 trades
            'volatility': volatility,
            'drawdown_pct': drawdown_pct,
            'peak_value': peak_value,
            'consecutive_losses': consecutive_losses,
            'daily_pnl_pct': daily_perf['daily_pnl_pct'],
            'trades_today': daily_perf['trades_today'],
            'total_trades': len(all_trades)
        }

    def recommend_profile(self, model_id: int) -> Dict:
        """
        Recommend the best risk profile based on current conditions
        Returns: {
            'recommended_profile': str,
            'reason': str,
            'confidence': float (0-100),
            'metrics': dict,
            'alternatives': list
        }
        """
        metrics = self.get_market_metrics(model_id)

        # Initialize scoring
        scores = {
            'Ultra-Safe': 0,
            'Conservative': 0,
            'Balanced': 0,
            'Aggressive': 0,
            'Scalper': 0
        }

        reasons = []

        # === RULE 1: Emergency Situations (Ultra-Safe) ===

        if metrics['drawdown_pct'] < -15:
            scores['Ultra-Safe'] += 50
            reasons.append(f"Large drawdown detected ({metrics['drawdown_pct']:.1f}%)")

        if metrics['consecutive_losses'] >= 5:
            scores['Ultra-Safe'] += 40
            reasons.append(f"{metrics['consecutive_losses']} consecutive losses")

        if metrics['recent_win_rate'] < 30 and metrics['total_trades'] >= 10:
            scores['Ultra-Safe'] += 35
            reasons.append(f"Poor recent performance ({metrics['recent_win_rate']:.0f}% win rate)")

        if metrics['daily_pnl_pct'] < -3:
            scores['Ultra-Safe'] += 30
            reasons.append(f"Significant daily loss ({metrics['daily_pnl_pct']:.1f}%)")

        # === RULE 2: Cautious Situations (Conservative) ===

        if -15 < metrics['drawdown_pct'] < -8:
            scores['Conservative'] += 40
            reasons.append(f"Moderate drawdown ({metrics['drawdown_pct']:.1f}%)")

        if 30 <= metrics['recent_win_rate'] < 45 and metrics['total_trades'] >= 10:
            scores['Conservative'] += 35
            reasons.append(f"Below-average win rate ({metrics['recent_win_rate']:.0f}%)")

        if metrics['volatility'] > 100 and metrics['win_rate'] < 50:
            scores['Conservative'] += 30
            reasons.append(f"High volatility with inconsistent results")

        if metrics['consecutive_losses'] >= 3:
            scores['Conservative'] += 25
            reasons.append(f"{metrics['consecutive_losses']} recent losses")

        # === RULE 3: Normal Situations (Balanced) ===

        if 45 <= metrics['win_rate'] <= 60 and metrics['total_trades'] >= 10:
            scores['Balanced'] += 40
            reasons.append(f"Moderate win rate ({metrics['win_rate']:.0f}%)")

        if -8 <= metrics['drawdown_pct'] <= 0:
            scores['Balanced'] += 30
            reasons.append(f"Stable performance")

        if 50 <= metrics['volatility'] <= 150:
            scores['Balanced'] += 25
            reasons.append(f"Normal volatility")

        if metrics['total_trades'] < 10:
            scores['Balanced'] += 50
            reasons.append(f"Limited trade history - recommending balanced approach")

        # === RULE 4: Good Situations (Aggressive) ===

        if metrics['win_rate'] > 60 and metrics['total_trades'] >= 15:
            scores['Aggressive'] += 45
            reasons.append(f"Strong win rate ({metrics['win_rate']:.0f}%)")

        if metrics['drawdown_pct'] > -3 and metrics['daily_pnl_pct'] > 1:
            scores['Aggressive'] += 40
            reasons.append(f"Positive momentum ({metrics['daily_pnl_pct']:.1f}% today)")

        if metrics['consecutive_losses'] == 0 and metrics['total_trades'] >= 10:
            scores['Aggressive'] += 35
            reasons.append(f"No recent losses - on winning streak")

        if metrics['volatility'] < 50 and metrics['win_rate'] > 55:
            scores['Aggressive'] += 30
            reasons.append(f"Low volatility with strong performance")

        # === RULE 5: High-Frequency Situations (Scalper) ===

        if metrics['trades_today'] > 15:
            scores['Scalper'] += 40
            reasons.append(f"High trading frequency ({metrics['trades_today']} trades today)")

        if metrics['volatility'] < 30 and metrics['total_trades'] >= 20:
            scores['Scalper'] += 35
            reasons.append(f"Low volatility - good for scalping")

        if metrics['win_rate'] > 55 and metrics['volatility'] < 75:
            scores['Scalper'] += 30
            reasons.append(f"Consistent small gains pattern")

        # === DETERMINE RECOMMENDATION ===

        # Sort by score
        sorted_profiles = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        recommended_profile = sorted_profiles[0][0]
        confidence = min(100, sorted_profiles[0][1])  # Cap at 100%

        # Get top reason
        main_reason = reasons[0] if reasons else "Based on overall performance analysis"

        # Get alternatives (top 3)
        alternatives = [
            {'profile': name, 'score': score}
            for name, score in sorted_profiles[1:4]
            if score > 0
        ]

        # Get current active profile
        settings = self.db.get_model_settings(model_id)
        active_profile_id = settings.get('active_profile_id')
        current_profile = None

        if active_profile_id:
            profile_data = self.db.get_risk_profile(active_profile_id)
            current_profile = profile_data['name'] if profile_data else None

        return {
            'recommended_profile': recommended_profile,
            'current_profile': current_profile,
            'reason': main_reason,
            'all_reasons': reasons[:3],  # Top 3 reasons
            'confidence': confidence,
            'metrics': metrics,
            'alternatives': alternatives,
            'should_switch': current_profile != recommended_profile if current_profile else True
        }

    def get_profile_suitability(self, model_id: int) -> Dict:
        """
        Analyze how suitable each profile is for current conditions
        Returns suitability scores (0-100) for all profiles
        """
        recommendation = self.recommend_profile(model_id)
        metrics = recommendation['metrics']

        suitability = {}

        for profile_name in ['Ultra-Safe', 'Conservative', 'Balanced', 'Aggressive', 'Scalper']:
            score = 0

            # Adjust based on metrics
            if profile_name == 'Ultra-Safe':
                score = 100 - metrics['win_rate']
                if metrics['drawdown_pct'] < -10:
                    score += 50

            elif profile_name == 'Conservative':
                score = 50
                if 35 <= metrics['win_rate'] <= 50:
                    score += 30
                if -10 < metrics['drawdown_pct'] < -5:
                    score += 20

            elif profile_name == 'Balanced':
                score = 70  # Default good choice
                if 45 <= metrics['win_rate'] <= 60:
                    score += 20

            elif profile_name == 'Aggressive':
                score = metrics['win_rate']
                if metrics['drawdown_pct'] > -3:
                    score += 20

            elif profile_name == 'Scalper':
                score = 40
                if metrics['trades_today'] > 10:
                    score += 30
                if metrics['volatility'] < 50:
                    score += 20

            suitability[profile_name] = min(100, max(0, score))

        return suitability
