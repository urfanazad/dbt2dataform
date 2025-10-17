from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import zipfile
import subprocess
from converter import Converter
import shutil
import yaml

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'app/uploads'
app.config['EXTRACT_FOLDER'] = 'app/extracted'
app.config['DATAFORM_PROJECT_DIR'] = 'app/dataform'
app.config['CONVERTED_ZIP'] = 'dataform_project.zip'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Unzip the file
        if os.path.exists(app.config['EXTRACT_FOLDER']):
            shutil.rmtree(app.config['EXTRACT_FOLDER'])
        os.makedirs(app.config['EXTRACT_FOLDER'])
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(app.config['EXTRACT_FOLDER'])

        return redirect(url_for('validate_dbt'))

@app.route('/validate')
def validate_dbt():
    project_dir = app.config['EXTRACT_FOLDER']
    dbt_project_dir = None
    for root, dirs, files in os.walk(project_dir):
        if 'dbt_project.yml' in files:
            dbt_project_dir = root
            break
    else:
        return "dbt_project.yml not found in the uploaded zip file."

    # Create a dummy profiles.yml
    profiles_dir = os.path.expanduser('~/.dbt/')
    os.makedirs(profiles_dir, exist_ok=True)
    with open(os.path.join(profiles_dir, 'profiles.yml'), 'w') as f:
        yaml.dump({
            'config': {'send_anonymous_usage_stats': False},
            'my_dbt_project': {
                'target': 'dev',
                'outputs': {
                    'dev': {
                        'type': 'bigquery',
                        'method': 'oauth',
                        'project': 'dummy-project',
                        'schema': 'dummy-schema'
                    }
                }
            }
        }, f)

    result = subprocess.run(['dbt', 'debug', '--project-dir', dbt_project_dir], capture_output=True, text=True)

    if "dbt was unable to connect to the specified database" in result.stdout or ("ERROR" not in result.stdout and "ERROR" not in result.stderr):
        return f"<pre>{result.stdout}</pre><br><a href='/convert'>Convert to Dataform</a>"
    else:
        return f"<pre>{result.stdout}{result.stderr}</pre>"

@app.route('/convert')
def convert_dbt_to_dataform():
    dbt_project_dir = None
    for root, dirs, files in os.walk(app.config['EXTRACT_FOLDER']):
        if 'dbt_project.yml' in files:
            dbt_project_dir = root
            break

    if dbt_project_dir:
        # Clean the dataform directory before conversion
        if os.path.exists(app.config['DATAFORM_PROJECT_DIR']):
            shutil.rmtree(app.config['DATAFORM_PROJECT_DIR'])
        os.makedirs(app.config['DATAFORM_PROJECT_DIR'])

        converter = Converter(dbt_project_dir, app.config['DATAFORM_PROJECT_DIR'])
        converter.convert()

        # Zip the converted project
        shutil.make_archive(app.config['CONVERTED_ZIP'].replace('.zip', ''), 'zip', app.config['DATAFORM_PROJECT_DIR'])

        return redirect(url_for('view_dataform_project'))
    else:
        return "dbt_project.yml not found."

@app.route('/download')
def download_dataform_project():
    return send_from_directory('.', app.config['CONVERTED_ZIP'], as_attachment=True)

@app.route('/view')
def view_dataform_project():
    dataform_project_dir = app.config['DATAFORM_PROJECT_DIR']
    file_structure = []
    for root, dirs, files in os.walk(dataform_project_dir):
        for name in files:
            file_structure.append(os.path.join(root, name))
        for name in dirs:
            file_structure.append(os.path.join(root, name) + '/')

    return render_template('view.html', file_structure=file_structure)

if __name__ == '__main__':
    app.run(debug=True)