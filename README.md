# dbt to Dataform Converter

This project is an AI agent that converts dbt projects into Dataform projects. It provides a web interface to upload a dbt project as a zip file, validates the dbt project, and then converts it to the Dataform format.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.8+
*   pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/dbt2dataform.git
    cd dbt2dataform
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file should be created for a more robust setup. For now, you can install the dependencies manually as listed in the development process: `Flask`, `dbt-core`, `dbt-bigquery`, `PyYAML`)*

## Usage

1.  **Run the Flask application:**
    ```bash
    python -m flask --app app/main.py run
    ```

2.  **Open your browser and navigate to:**
    ```
    http://127.0.0.1:5000/
    ```

3.  **Upload your dbt project:**
    *   Zip your dbt project directory.
    *   Click the "Choose File" button and select your zip file.
    *   Click the "Upload" button.

4.  **Validate and Convert:**
    *   The application will first validate your dbt project by running `dbt debug`.
    *   If the validation is successful (or fails with an expected connection error), a "Convert to Dataform" link will appear.
    *   Click the link to start the conversion.

5.  **View and Download:**
    *   After conversion, you will be redirected to a page showing the file structure of the new Dataform project.
    *   You can then download the converted project as a zip file.

## How it Works

The conversion process involves the following steps:

1.  **File Upload:** The Flask application receives the dbt project as a zip file.
2.  **dbt Validation:** It runs `dbt debug` to ensure the project structure is valid. It creates a temporary `profiles.yml` to allow validation to proceed without a fully configured local dbt environment.
3.  **Source Conversion:** It looks for `.yml` files containing `sources` and creates a `definitions/declarations.js` file in the Dataform project with the corresponding `declare` statements.
4.  **Model Conversion:** It iterates through the SQL files in the `models` directory and replaces dbt's `{{ ref(...) }}` and `{{ source(...) }}` macros with their Dataform equivalents (`ref(...)`).
5.  **Configuration:** It generates a basic `dataform.json` file.
6.  **Download:** The converted Dataform project is zipped and made available for download.