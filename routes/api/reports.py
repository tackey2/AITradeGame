"""
Report API Blueprint
Handles report generation, management and download endpoints.
"""
from flask import Blueprint, request, jsonify, send_file
import threading
import json
import os
from routes import app_context
from report_generator import ReportGenerator
from ai_report_analyst import AIReportAnalyst
from pdf_generator import PDFGenerator

reports_bp = Blueprint('reports', __name__)

# Initialize report components (lazy loading)
report_generator = None
pdf_generator = None


def get_report_generator():
    """Lazy initialization of report generator"""
    global report_generator
    if report_generator is None:
        enhanced_db = app_context['enhanced_db']
        report_generator = ReportGenerator(enhanced_db)
    return report_generator


def get_pdf_generator():
    """Lazy initialization of PDF generator"""
    global pdf_generator
    if pdf_generator is None:
        pdf_generator = PDFGenerator(output_dir='reports')
    return pdf_generator


@reports_bp.route('/api/reports/settings', methods=['GET'])
def get_report_settings():
    """Get report settings"""
    enhanced_db = app_context['enhanced_db']
    try:
        settings = enhanced_db.get_report_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports/settings', methods=['PUT'])
def update_report_settings():
    """Update report settings"""
    enhanced_db = app_context['enhanced_db']
    try:
        settings = request.json
        enhanced_db.update_report_settings(settings)
        return jsonify({'message': 'Settings updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports', methods=['GET'])
def get_reports():
    """Get all reports"""
    enhanced_db = app_context['enhanced_db']
    try:
        report_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        reports = enhanced_db.get_all_reports(report_type, limit)
        return jsonify(reports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Get a specific report"""
    enhanced_db = app_context['enhanced_db']
    try:
        report = enhanced_db.get_report(report_id)
        if report:
            return jsonify(report)
        else:
            return jsonify({'error': 'Report not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete a report"""
    enhanced_db = app_context['enhanced_db']
    try:
        report = enhanced_db.get_report(report_id)
        if report and report['file_path']:
            # Delete file if exists
            if os.path.exists(report['file_path']):
                os.remove(report['file_path'])

        enhanced_db.delete_report(report_id)
        return jsonify({'message': 'Report deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate a new report (async)"""
    enhanced_db = app_context['enhanced_db']
    try:
        data = request.json
        report_type = data.get('report_type', 'weekly_comparative')
        model_ids = data.get('model_ids', [])
        period_start = data.get('period_start')
        period_end = data.get('period_end')

        if not model_ids:
            return jsonify({'error': 'No models specified'}), 400

        if not period_start or not period_end:
            return jsonify({'error': 'Period dates required'}), 400

        # Get report settings
        settings = enhanced_db.get_report_settings()

        # Create report entry with 'generating' status
        report_id = enhanced_db.create_report(
            report_type=report_type,
            model_ids=model_ids,
            period_start=period_start,
            period_end=period_end,
            generated_by_model=settings.get('analysis_ai_model')
        )

        # Start background generation
        thread = threading.Thread(
            target=_generate_report_background,
            args=(report_id, report_type, model_ids, period_start, period_end, settings)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'report_id': report_id,
            'status': 'generating',
            'message': 'Report generation started'
        })

    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        return jsonify({'error': str(e)}), 500


def _generate_report_background(report_id, report_type, model_ids, period_start, period_end, settings):
    """Background task for report generation"""
    enhanced_db = app_context['enhanced_db']
    try:
        print(f"[INFO] Generating report {report_id}...")

        # Generate report data
        generator = get_report_generator()
        report_data = generator.generate_weekly_comparative_report(
            model_ids=model_ids,
            period_start=period_start,
            period_end=period_end
        )

        # Generate AI analysis
        analyst = AIReportAnalyst(
            provider=settings.get('analysis_ai_provider', 'anthropic'),
            model=settings.get('analysis_ai_model', 'claude-sonnet-3.5'),
            api_key=settings.get('analysis_api_key'),
            api_url=settings.get('analysis_api_url')
        )

        ai_analysis = {
            'executive_summary': analyst.generate_executive_summary(report_data),
            'comparative_analysis': analyst.generate_comparative_analysis(report_data['models']),
            'risk_assessment': analyst.generate_risk_assessment(
                report_data['models'][0] if report_data['models'] else {},
                report_data['market_context']
            ),
            'metrics_interpretation': analyst.generate_metrics_interpretation(report_data['models'])
        }

        # Generate PDF
        pdf_gen = get_pdf_generator()
        file_path = pdf_gen.generate_report(report_data, ai_analysis)

        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Update report with results
        enhanced_db.update_report(report_id, {
            'status': 'completed',
            'file_path': file_path,
            'file_size': file_size,
            'recommendation': report_data.get('recommendation'),
            'confidence_score': report_data.get('confidence_score'),
            'top_model_id': report_data.get('top_model_id'),
            'metadata': json.dumps({
                'models_count': len(report_data['models']),
                'market_regime': report_data['market_context'].get('market_regime')
            })
        })

        print(f"[INFO] Report {report_id} generated successfully: {file_path}")

    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        enhanced_db.update_report(report_id, {
            'status': 'failed',
            'error_message': str(e)
        })


@reports_bp.route('/api/reports/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    """Download report file"""
    enhanced_db = app_context['enhanced_db']
    try:
        report = enhanced_db.get_report(report_id)

        if not report:
            return jsonify({'error': 'Report not found'}), 404

        if not report['file_path'] or not os.path.exists(report['file_path']):
            return jsonify({'error': 'Report file not found'}), 404

        return send_file(
            report['file_path'],
            as_attachment=True,
            download_name=os.path.basename(report['file_path'])
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports/cleanup', methods=['POST'])
def cleanup_old_reports():
    """Clean up old reports based on retention settings"""
    enhanced_db = app_context['enhanced_db']
    try:
        result = enhanced_db.cleanup_old_reports()
        return jsonify({
            'message': 'Cleanup completed',
            'daily_deleted': result['daily_deleted'],
            'weekly_deleted': result['weekly_deleted']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
