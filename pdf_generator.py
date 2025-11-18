"""
PDF Report Generator
Generates PDF reports using WeasyPrint with HTML fallback
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class PDFGenerator:
    """Generate PDF reports from report data"""

    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = output_dir
        self.use_weasyprint = self._check_weasyprint()

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for subdir in ['weekly', 'daily', 'custom']:
            Path(f"{output_dir}/{subdir}").mkdir(parents=True, exist_ok=True)

    def _check_weasyprint(self) -> bool:
        """Check if WeasyPrint is available"""
        try:
            import weasyprint
            return True
        except ImportError:
            print("[WARN] WeasyPrint not available, using HTML fallback")
            return False

    def generate_report(self, report_data: Dict, ai_analysis: Dict) -> str:
        """
        Generate PDF report

        Args:
            report_data: Report metrics and data
            ai_analysis: AI-generated narrative analysis

        Returns:
            File path to generated report
        """
        # Generate HTML
        html_content = self._generate_html(report_data, ai_analysis)

        # Determine filename
        report_type = report_data.get('report_type', 'custom')
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        if report_type == 'weekly_comparative':
            subdir = 'weekly'
            filename = f"weekly_comparative_{timestamp}.pdf"
        elif report_type == 'daily_individual':
            subdir = 'daily'
            model_id = report_data['models'][0]['model_id'] if report_data.get('models') else 'unknown'
            filename = f"daily_model_{model_id}_{timestamp}.pdf"
        else:
            subdir = 'custom'
            filename = f"custom_report_{timestamp}.pdf"

        filepath = os.path.join(self.output_dir, subdir, filename)

        # Generate PDF or fallback to HTML
        if self.use_weasyprint:
            try:
                import weasyprint
                weasyprint.HTML(string=html_content).write_pdf(filepath)
                print(f"[INFO] PDF generated: {filepath}")
            except Exception as e:
                print(f"[WARN] WeasyPrint failed: {e}, falling back to HTML")
                filepath = filepath.replace('.pdf', '.html')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
        else:
            # HTML fallback
            filepath = filepath.replace('.pdf', '.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"[INFO] HTML report generated: {filepath}")

        return filepath

    def _generate_html(self, report_data: Dict, ai_analysis: Dict) -> str:
        """Generate HTML content for report"""

        if report_data.get('report_type') == 'weekly_comparative':
            return self._generate_comparative_html(report_data, ai_analysis)
        else:
            return self._generate_individual_html(report_data, ai_analysis)

    def _generate_comparative_html(self, report_data: Dict, ai_analysis: Dict) -> str:
        """Generate HTML for weekly comparative report"""

        models = report_data.get('models', [])
        top_model = models[0] if models else None
        market_context = report_data.get('market_context', {})

        # Recommendation badge
        recommendation = report_data.get('recommendation', 'not_ready')
        rec_badges = {
            'go_live': ('✅ READY FOR LIVE TRADING', '#10b981'),
            'continue_testing': ('⚠️ CONTINUE TESTING', '#f59e0b'),
            'not_ready': ('❌ NOT READY', '#ef4444')
        }
        rec_text, rec_color = rec_badges.get(recommendation, rec_badges['not_ready'])

        # Build models table
        models_table = ""
        for i, model in enumerate(models[:3], 1):
            rank_emoji = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else ''
            models_table += f"""
            <tr style="background-color: {'#f9fafb' if i % 2 == 0 else 'white'};">
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{rank_emoji} #{i}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{model['model_name']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;"><strong>{model['score']}/100</strong></td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{model['performance']['net_roi']}%</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{model['performance']['win_rate']}%</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{model['risk']['total_violations']}</td>
            </tr>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Weekly Comparative Report</title>
    <style>
        @page {{ size: A4; margin: 1cm; }}
        body {{ font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1f2937; }}
        h1 {{ color: #111827; font-size: 24pt; margin-bottom: 10px; }}
        h2 {{ color: #374151; font-size: 16pt; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }}
        h3 {{ color: #4b5563; font-size: 14pt; margin-top: 15px; margin-bottom: 8px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .period {{ color: #6b7280; font-size: 12pt; }}
        .recommendation {{ background-color: {rec_color}; color: white; padding: 15px; border-radius: 8px; text-align: center; font-size: 16pt; font-weight: bold; margin: 20px 0; }}
        .analysis-box {{ background-color: #f3f4f6; padding: 15px; border-left: 4px solid #3b82f6; margin: 15px 0; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background-color: #374151; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; }}
        .metric-row {{ display: flex; justify-content: space-between; margin: 10px 0; }}
        .metric-label {{ font-weight: bold; color: #6b7280; }}
        .metric-value {{ color: #111827; }}
        .page-break {{ page-break-before: always; }}
        .footer {{ text-align: center; color: #9ca3af; font-size: 9pt; margin-top: 30px; padding-top: 15px; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>

<div class="header">
    <h1>📊 Go-Live Readiness Report</h1>
    <div class="period">Period: {report_data['period_start']} to {report_data['period_end']}</div>
    <div class="period">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</div>

<div class="recommendation">{rec_text}</div>

<h2>🎯 Executive Summary</h2>
<div class="analysis-box">
    {ai_analysis.get('executive_summary', 'Analysis unavailable')}
</div>

<h2>🏆 Model Ranking</h2>
<table>
    <thead>
        <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Score</th>
            <th>Net ROI</th>
            <th>Win Rate</th>
            <th>Violations</th>
        </tr>
    </thead>
    <tbody>
        {models_table}
    </tbody>
</table>

<h2>📈 Key Metrics - Top Model</h2>
{self._generate_metrics_section(top_model) if top_model else '<p>No model data available</p>'}

<div class="page-break"></div>

<h2>🔬 Comparative Analysis</h2>
<div class="analysis-box">
    {ai_analysis.get('comparative_analysis', 'Analysis unavailable')}
</div>

<h2>🌍 Market Context</h2>
<div class="analysis-box">
    <h3>Market Performance</h3>
    <div class="metric-row">
        <span class="metric-label">BTC Performance:</span>
        <span class="metric-value">{market_context.get('btc_performance', {}).get('change_pct', 0)}%</span>
    </div>
    <div class="metric-row">
        <span class="metric-label">ETH Performance:</span>
        <span class="metric-value">{market_context.get('eth_performance', {}).get('change_pct', 0)}%</span>
    </div>
    <div class="metric-row">
        <span class="metric-label">Market Regime:</span>
        <span class="metric-value">{market_context.get('market_regime', 'Unknown')}</span>
    </div>
    <div class="metric-row">
        <span class="metric-label">Fear & Greed (Est.):</span>
        <span class="metric-value">{market_context.get('fear_greed_estimate', 50)}/100</span>
    </div>

    <h3>Context Interpretation</h3>
    <p>{ai_analysis.get('metrics_interpretation', 'Interpretation unavailable')}</p>
</div>

<div class="page-break"></div>

<h2>⚠️ Risk Assessment</h2>
<div class="analysis-box">
    {ai_analysis.get('risk_assessment', 'Risk assessment unavailable')}
</div>

<h2>💡 Recommendation & Next Steps</h2>
<div class="analysis-box">
    <h3>Confidence Level: {report_data.get('confidence_score', 0)}%</h3>

    {self._generate_next_steps(recommendation, top_model) if top_model else '<p>No recommendations available</p>'}
</div>

<div class="footer">
    Report generated by AI Trade Game | Sprint 3 Reporting System
</div>

</body>
</html>
        """
        return html

    def _generate_individual_html(self, report_data: Dict, ai_analysis: Dict) -> str:
        """Generate HTML for individual daily report (simplified)"""
        model = report_data['models'][0] if report_data.get('models') else None

        if not model:
            return "<html><body><h1>No model data available</h1></body></html>"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Daily Performance Report - {model['model_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        h1 {{ color: #111827; }}
        h2 {{ color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }}
        .metric-box {{ background-color: #f3f4f6; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background-color: #374151; color: white; padding: 10px; }}
        td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
    </style>
</head>
<body>

<h1>📊 Daily Performance Report</h1>
<p><strong>Model:</strong> {model['model_name']}</p>
<p><strong>Date:</strong> {report_data['period_start']}</p>

<h2>Performance Summary</h2>
{self._generate_metrics_section(model)}

<h2>Analysis</h2>
<div class="metric-box">
    {ai_analysis.get('executive_summary', 'Analysis unavailable')}
</div>

<p style="text-align: center; color: #6b7280; margin-top: 30px;">
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</p>

</body>
</html>
        """
        return html

    def _generate_metrics_section(self, model: Dict) -> str:
        """Generate HTML for metrics display"""
        perf = model.get('performance', {})
        risk = model.get('risk', {})

        return f"""
<table>
    <tr>
        <th>Metric</th>
        <th>Value</th>
        <th>Status</th>
    </tr>
    <tr>
        <td>Net ROI</td>
        <td>{perf.get('net_roi', 0)}%</td>
        <td>{'✅' if perf.get('net_roi', 0) > 5 else '⚠️'}</td>
    </tr>
    <tr>
        <td>Win Rate</td>
        <td>{perf.get('win_rate', 0)}%</td>
        <td>{'✅' if perf.get('win_rate', 0) > 50 else '⚠️'}</td>
    </tr>
    <tr>
        <td>Sharpe Ratio</td>
        <td>{perf.get('sharpe_ratio', 0)}</td>
        <td>{'✅' if perf.get('sharpe_ratio', 0) > 1.5 else '⚠️'}</td>
    </tr>
    <tr>
        <td>Max Drawdown</td>
        <td>{perf.get('max_drawdown', 0)}%</td>
        <td>{'✅' if perf.get('max_drawdown', 0) < 15 else '⚠️'}</td>
    </tr>
    <tr>
        <td>Total Trades</td>
        <td>{perf.get('total_trades', 0)}</td>
        <td>{'✅' if perf.get('total_trades', 0) > 10 else '⚠️'}</td>
    </tr>
    <tr>
        <td>Risk Violations</td>
        <td>{risk.get('total_violations', 0)}</td>
        <td>{'✅' if risk.get('total_violations', 0) == 0 else '❌'}</td>
    </tr>
</table>

<h3>Cost Breakdown</h3>
<ul>
    <li>Trading Fees: ${perf.get('costs', {}).get('fees', 0)}</li>
    <li>Slippage: ${perf.get('costs', {}).get('slippage', 0)}</li>
    <li>AI Costs: ${perf.get('costs', {}).get('ai_costs', 0)}</li>
    <li><strong>Total Impact: {perf.get('costs', {}).get('impact_pct', 0)}%</strong></li>
</ul>
        """

    def _generate_next_steps(self, recommendation: str, model: Dict) -> str:
        """Generate next steps based on recommendation"""
        if recommendation == 'go_live':
            return """
<h3>✅ Approved for Live Trading</h3>
<h4>Recommended Approach:</h4>
<ol>
    <li>Start with $500-1000 capital</li>
    <li>Use semi-automated mode for first 2 weeks</li>
    <li>Review daily reports closely</li>
    <li>Scale up gradually if performance continues</li>
</ol>

<h4>Stop-Loss Triggers:</h4>
<ul>
    <li>3-day losing streak</li>
    <li>Total drawdown exceeds -20%</li>
    <li>5+ risk violations in one week</li>
</ul>
            """
        elif recommendation == 'continue_testing':
            return """
<h3>⚠️ Continue Testing</h3>
<h4>Before Going Live:</h4>
<ul>
    <li>Maintain consistent performance for 2+ more weeks</li>
    <li>Achieve 50%+ win rate</li>
    <li>Zero risk violations for 2 consecutive weeks</li>
</ul>

<h4>Suggested Actions:</h4>
<ol>
    <li>Keep running in simulation mode</li>
    <li>Review and optimize risk parameters</li>
    <li>Monitor in different market conditions</li>
</ol>
            """
        else:
            return """
<h3>❌ Not Ready for Live Trading</h3>
<h4>Issues to Address:</h4>
<ul>
    <li>Improve profitability (target: 8%+ net ROI)</li>
    <li>Reduce risk violations to zero</li>
    <li>Increase win rate above 50%</li>
</ul>

<h4>Recommended Actions:</h4>
<ol>
    <li>Review and adjust AI prompts/strategy</li>
    <li>Tighten risk parameters</li>
    <li>Continue simulation testing</li>
    <li>Re-evaluate after 2-4 weeks of improvements</li>
</ol>
            """


# For testing
if __name__ == '__main__':
    generator = PDFGenerator()

    # Sample report data
    sample_data = {
        'report_type': 'weekly_comparative',
        'period_start': '2024-11-11',
        'period_end': '2024-11-17',
        'recommendation': 'go_live',
        'confidence_score': 87,
        'models': [{
            'model_id': 1,
            'model_name': 'GPT-4 Trader',
            'score': 87,
            'rank': 1,
            'performance': {
                'net_roi': 12.3,
                'win_rate': 58,
                'sharpe_ratio': 1.8,
                'max_drawdown': 15.2,
                'total_trades': 42,
                'costs': {'fees': 42, 'slippage': 18, 'ai_costs': 3.2, 'total': 63.2, 'impact_pct': 2.1}
            },
            'risk': {'total_violations': 0, 'compliance_rate': 100}
        }],
        'market_context': {
            'btc_performance': {'change_pct': 12.5},
            'eth_performance': {'change_pct': 10.2},
            'market_regime': 'Bullish with moderate volatility',
            'fear_greed_estimate': 68
        }
    }

    sample_analysis = {
        'executive_summary': 'This model demonstrates strong performance...',
        'comparative_analysis': 'Model comparison shows...',
        'risk_assessment': 'Key risks to monitor...',
        'metrics_interpretation': 'The metrics indicate...'
    }

    filepath = generator.generate_report(sample_data, sample_analysis)
    print(f"Report generated: {filepath}")
