import unittest
import os
import shutil
from app.converter import Converter
import yaml

class TestConverter(unittest.TestCase):
    def setUp(self):
        self.dbt_project_dir = 'tests/dbt_project'
        self.dataform_project_dir = 'tests/dataform_project'
        os.makedirs(os.path.join(self.dbt_project_dir, 'models'), exist_ok=True)
        os.makedirs(self.dataform_project_dir, exist_ok=True)
        with open(os.path.join(self.dbt_project_dir, 'dbt_project.yml'), 'w') as f:
            yaml.dump({'profile': 'test_profile'}, f)

    def tearDown(self):
        if os.path.exists(self.dbt_project_dir):
            shutil.rmtree(self.dbt_project_dir)
        if os.path.exists(self.dataform_project_dir):
            shutil.rmtree(self.dataform_project_dir)

    def test_replace_ref(self):
        converter = Converter(self.dbt_project_dir, self.dataform_project_dir)
        content = "select * from {{ ref('my_model') }}"
        expected_content = "select * from ref('my_model')"
        self.assertEqual(converter.replace_ref(content), expected_content)

    def test_convert_models(self):
        with open(os.path.join(self.dbt_project_dir, 'models', 'my_model.sql'), 'w') as f:
            f.write("select * from {{ ref('another_model') }}")

        converter = Converter(self.dbt_project_dir, self.dataform_project_dir)
        converter.convert_models()

        with open(os.path.join(self.dataform_project_dir, 'definitions', 'my_model.sql'), 'r') as f:
            content = f.read()

        self.assertEqual(content, "select * from ref('another_model')")

    def test_create_dataform_json(self):
        converter = Converter(self.dbt_project_dir, self.dataform_project_dir)
        converter.create_dataform_json()

        with open(os.path.join(self.dataform_project_dir, 'dataform.json'), 'r') as f:
            content = f.read()

        self.assertIn("'defaultSchema': 'test_profile'", content)

    def test_convert_sources(self):
        with open(os.path.join(self.dbt_project_dir, 'sources.yml'), 'w') as f:
            yaml.dump({
                'sources': [{
                    'name': 'my_source',
                    'database': 'my_db',
                    'tables': [{'name': 'my_table'}]
                }]
            }, f)

        converter = Converter(self.dbt_project_dir, self.dataform_project_dir)
        converter.convert_sources()

        with open(os.path.join(self.dataform_project_dir, 'definitions', 'declarations.js'), 'r') as f:
            content = f.read()

        self.assertEqual(content, "declare({ name: 'my_table', database: 'my_db', schema: 'my_source' });\n")

    def test_replace_source(self):
        converter = Converter(self.dbt_project_dir, self.dataform_project_dir)
        content = "select * from {{ source('my_source', 'my_table') }}"
        expected_content = "select * from ref('my_table')"
        self.assertEqual(converter.replace_source(content), expected_content)


if __name__ == '__main__':
    unittest.main()