import os

from flask import Blueprint, render_template, current_app, send_file, request

from utils.decorators import has_permission

reports_bp = Blueprint('reports', __name__, url_prefix='/models/reports')


@reports_bp.route('/')
@has_permission(['analysis.reports'])
def index(payload):
    folder = os.path.join(current_app.root_path, 'reports')
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    # files = os.listdir(os.path.join(current_app.root_path, 'reports'))
    return render_template('/analysis/model/reports/index.html', files=files)


@reports_bp.route('/download')
@has_permission(['analysis.reports.download'])
def download(payload):
    file = request.args.get('title')
    uploads = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
    return send_file(os.path.join(current_app.root_path, 'reports', file), as_attachment=True, download_name=file)
