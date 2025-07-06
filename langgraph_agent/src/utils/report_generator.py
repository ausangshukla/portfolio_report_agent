import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import markdown
from bs4 import BeautifulSoup

def generate_html_report(json_report_path: str, output_html_path: str):
    """
    Generates a well-formatted HTML report from a JSON analysis report,
    including tabular data and charts.

    Args:
        json_report_path (str): The file path to the input JSON report.
        output_html_path (str): The full file path for the output HTML document.
    """
    try:
        with open(json_report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))

        # Add a filter to convert markdown to HTML
        def markdown_to_html(md_text):
            return markdown.markdown(md_text)
        env.filters['markdown_to_html'] = markdown_to_html

        template = env.from_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary-color: #0056b3; /* Deep Blue */
            --secondary-color: #007bff; /* Bright Blue */
            --accent-color: #28a745; /* Success Green */
            --text-color: #343a40; /* Dark Gray */
            --light-text-color: #6c757d; /* Medium Gray */
            --bg-color: #f4f7f6; /* Very Light Gray */
            --card-bg: #ffffff; /* White */
            --border-color: #dee2e6; /* Light Border Gray */
            --shadow-light: rgba(0, 0, 0, 0.08);
            --shadow-medium: rgba(0, 0, 0, 0.15);
            --hover-bg: #e2e6ea; /* Lighter Gray for hover */
            --code-bg: #e9ecef; /* Code background */
            --code-inline-bg: #fff3cd; /* Inline code background */
            --blockquote-bg: #eaf0f6; /* Blockquote background */
        }

        body {
            font-family: 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            font-size: 16px;
        }

        .container {
            max-width: 1100px;
            margin: 30px auto;
            background: var(--card-bg);
            padding: 40px 50px;
            border-radius: 12px;
            box-shadow: 0 8px 30px var(--shadow-medium);
            border: 1px solid var(--border-color);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color);
            margin-top: 1.8em;
            margin-bottom: 0.7em;
            font-weight: 700;
            line-height: 1.3;
        }

        h1 {
            font-size: 2.8em;
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 15px;
            margin-bottom: 25px;
            text-align: center;
            color: var(--primary-color);
        }
        h2 { font-size: 2.2em; color: var(--secondary-color); border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
        h3 { font-size: 1.7em; color: var(--primary-color); }
        h4 { font-size: 1.4em; color: var(--text-color); }

        p {
            margin-bottom: 1.2em;
            color: var(--light-text-color);
        }

        table {
            width: 100%;
            border-collapse: separate; /* Use separate for border-spacing */
            border-spacing: 0; /* Remove space between borders */
            margin-bottom: 30px;
            box-shadow: 0 4px 15px var(--shadow-light);
            border-radius: 10px;
            overflow: hidden; /* Ensures rounded corners apply to inner elements */
            background-color: var(--card-bg);
        }

        th, td {
            border: none; /* Remove individual cell borders */
            padding: 15px 20px;
            text-align: left;
            vertical-align: middle;
        }

        th {
            background-color: var(--primary-color);
            color: #fff;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.05em;
            position: sticky;
            top: 0;
        }

        th:first-child { border-top-left-radius: 10px; }
        th:last-child { border-top-right-radius: 10px; }

        tr:nth-child(even) {
            background-color: #f8f9fa; /* Lighter shade for even rows */
        }

        tr:hover {
            background-color: var(--hover-bg); /* Hover effect for rows */
            transition: background-color 0.3s ease;
        }

        td {
            border-bottom: 1px solid var(--border-color);
        }
        tr:last-child td {
            border-bottom: none;
        }

        .chart-container {
            position: relative;
            height: 500px; /* Taller charts for better visualization */
            width: 100%;
            margin-bottom: 40px;
            background: var(--card-bg);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px var(--shadow-light);
            border: 1px solid var(--border-color);
        }

        .references {
            margin-top: 50px;
            border-top: 1px solid var(--border-color);
            padding-top: 30px;
            background-color: var(--bg-color);
            padding: 25px;
            border-radius: 10px;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.03);
        }

        .references h3 {
            color: var(--primary-color);
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.8em;
            text-align: center;
        }

        .references ul {
            list-style: none; /* Remove default bullet */
            padding-left: 0;
            margin: 0;
        }

        .references li {
            margin-bottom: 10px;
            font-size: 0.95em;
            color: var(--light-text-color);
            padding-left: 25px;
            position: relative;
        }

        .references li:before {
            content: "•"; /* Custom bullet point */
            color: var(--accent-color);
            position: absolute;
            left: 0;
            font-size: 1.2em;
            line-height: 1;
        }

        /* Markdown specific styles */
        div pre {
            background-color: var(--code-bg);
            border: 1px solid var(--border-color);
            border-left: 6px solid var(--secondary-color);
            padding: 18px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.95em;
            line-height: 1.5;
            margin-bottom: 1.8em;
            box-shadow: inset 0 1px 5px rgba(0,0,0,0.05);
        }

        div code {
            background-color: var(--code-inline-bg);
            padding: 3px 7px;
            border-radius: 5px;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            color: var(--primary-color);
        }

        div blockquote {
            border-left: 5px solid var(--accent-color);
            margin: 1.8em 0;
            padding: 0.8em 20px;
            background-color: var(--blockquote-bg);
            color: var(--light-text-color);
            font-style: italic;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        div ul, div ol {
            margin-bottom: 1.5em;
            padding-left: 30px;
        }

        div ul li, div ol li {
            margin-bottom: 0.7em;
            color: var(--light-text-color);
        }

        /* Header and Footer */
        .report-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .report-header h1 {
            font-size: 3.5em;
            color: var(--primary-color);
            margin-bottom: 10px;
            border-bottom: none;
            padding-bottom: 0;
        }

        .report-header p {
            font-size: 1.2em;
            color: var(--light-text-color);
            margin-top: 0;
        }

        .report-footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            font-size: 0.9em;
            color: var(--light-text-color);
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            body {
                padding: 15px;
            }
            .container {
                margin: 15px auto;
                padding: 25px 30px;
            }
            h1 { font-size: 2.2em; }
            h2 { font-size: 1.8em; }
            h3 { font-size: 1.4em; }
            .chart-container {
                height: 350px;
            }
        }

        @media print {
            body {
                background-color: #fff;
                padding: 0;
                margin: 0;
            }
            .container {
                box-shadow: none;
                border: none;
                margin: 0;
                padding: 0;
                max-width: none;
            }
            table, pre, .chart-container, blockquote {
                page-break-inside: avoid;
            }
            h1, h2, h3, h4, h5, h6 {
                page-break-after: avoid;
            }
            .report-footer {
                page-break-before: always;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>Portfolio Analysis Report</h1>
            <p>Detailed analysis generated by the LangGraph agent.</p>
            <p>Date: {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
        </div>
{% for section in report_data %}
            <h2>{{ section.section }}</h2>
            {% if section.sub_sections %}
                {% for sub_section in section.sub_sections %}
                    <h3>{{ sub_section.title }}</h3>
                    <div>{{ sub_section.content | markdown_to_html }}</div>
                {% endfor %}
            {% else %}
                <div>{{ section.content | markdown_to_html }}</div>
            {% endif %}

            {% if section.tabular_data %}
                <h3>{{ section.tabular_data.title }}</h3>
                <table>
                    <thead>
                        <tr>
                            {% for header in section.tabular_data.rows[0].keys() %}
                                <th>{{ header }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in section.tabular_data.rows %}
                            <tr>
                                {% for key, value in row.items() %}
                                    <td>{{ value if value is not none else '' }}</td>
                                {% endfor %}
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% endif %}

            {% if section.graph_specs %}
                {% for graph_spec in section.graph_specs %}
                    {% if graph_spec.type != 'none' %}
                        <h3>{{ graph_spec.title }}</h3>
                        {% if graph_spec.type == 'textual_description' %}
                            <p>{{ graph_spec.data }}</p>
                        {% else %}
                            <div class="chart-container">
                                <canvas id="chart-{{ section.section | replace(' ', '-') }}-{{ loop.index }}"></canvas>
                            </div>
                            <script>
                                document.addEventListener('DOMContentLoaded', function() {
                                    var ctx = document.getElementById('chart-{{ section.section | replace(' ', '-') }}-{{ loop.index }}').getContext('2d');
                                    var chartData = {{ graph_spec.data | tojson }};
                                    var chartType = "{{ graph_spec.type }}";
                                    new Chart(ctx, {
                                        type: chartType,
                                        data: chartData,
                                        options: {
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            plugins: {
                                                title: {
                                                    display: true,
                                                    text: "{{ graph_spec.title }}"
                                                }
                                            }
                                        }
                                    });
                                });
                            </script>
                        {% endif %}
                    {% endif %}
                {% endfor %}
            {% endif %}

            {% if False and section.references %}
                <div class="references">
                    <h3>References</h3>
                    <ul>
                        {% for ref in section.references %}
                            <li>{{ ref.document }}: {{ ref.location }}</li>
                        {% endfor %}
                    </ul>
                </div>
            {% endif %}
        {% endfor %}
        <div class="report-footer">
            <p>&copy; {{ datetime.now().year }} LangGraph Agent. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """)

        # Render the template
        html_content = template.render(report_data=report_data, datetime=datetime)

        os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report successfully generated at '{output_html_path}'")

    except FileNotFoundError:
        print(f"Error: JSON report file not found at '{json_report_path}'")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_report_path}'. Ensure it's a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

