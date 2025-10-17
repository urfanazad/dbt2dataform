import os
import re
import yaml

class Converter:
    def __init__(self, dbt_project_dir, dataform_project_dir):
        self.dbt_project_dir = dbt_project_dir
        self.dataform_project_dir = dataform_project_dir

    def convert(self):
        self.convert_sources()
        self.convert_models()
        self.create_dataform_json()

    def convert_models(self):
        dbt_models_dir = os.path.join(self.dbt_project_dir, 'models')
        dataform_models_dir = os.path.join(self.dataform_project_dir, 'definitions')
        os.makedirs(dataform_models_dir, exist_ok=True)

        for root, _, files in os.walk(dbt_models_dir):
            for file in files:
                if file.endswith('.sql'):
                    dbt_model_path = os.path.join(root, file)
                    dataform_model_path = os.path.join(dataform_models_dir, file)

                    with open(dbt_model_path, 'r') as f:
                        content = f.read()

                    content = self.replace_ref(content)
                    content = self.replace_source(content)

                    with open(dataform_model_path, 'w') as f:
                        f.write(content)

    def replace_ref(self, content):
        return re.sub(r'\{\{\s*ref\(\s*\'(\w+)\'\s*\)\s*\}\}', r"ref('\g<1>')", content)

    def replace_source(self, content):
        return re.sub(r'\{\{\s*source\(\s*\'(\w+)\'\s*,\s*\'(\w+)\'\s*\)\s*\}\}', r"ref('\g<2>')", content)

    def convert_sources(self):
        dataform_models_dir = os.path.join(self.dataform_project_dir, 'definitions')
        os.makedirs(dataform_models_dir, exist_ok=True)

        for root, _, files in os.walk(self.dbt_project_dir):
            for file in files:
                if file.endswith('.yml'):
                    dbt_source_path = os.path.join(root, file)
                    with open(dbt_source_path, 'r') as f:
                        dbt_source = yaml.safe_load(f)

                    if dbt_source and 'sources' in dbt_source:
                        for source in dbt_source['sources']:
                            source_name = source['name']
                            for table in source['tables']:
                                table_name = table['name']
                                declaration = f"declare({{ name: '{table_name}', database: '{source.get('database', '')}', schema: '{source_name}' }});\n"
                                with open(os.path.join(dataform_models_dir, 'declarations.js'), 'a') as f:
                                    f.write(declaration)

    def create_dataform_json(self):
        with open(os.path.join(self.dbt_project_dir, 'dbt_project.yml'), 'r') as f:
            dbt_project = yaml.safe_load(f)

        dataform_json = {
            "defaultSchema": dbt_project.get('profile'),
            "assertionSchema": "dataform_assertions",
            "warehouse": "bigquery",
            "defaultDatabase": "your-gcp-project-id",
            "defaultLocation": "US"
        }

        with open(os.path.join(self.dataform_project_dir, 'dataform.json'), 'w') as f:
            f.write(str(dataform_json))