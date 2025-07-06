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
            --primary-color: #2c3e50; /* Dark blue-gray for headings */
            --secondary-color: #34495e; /* Slightly lighter dark blue-gray */
            --accent-color: #3498db; /* Blue for highlights */
            --text-color: #333;
            --bg-color: #f8f9fa; /* Light gray background */
            --card-bg: #ffffff;
            --border-color: #e0e0e0;
            --shadow-light: rgba(0, 0, 0, 0.05);
            --shadow-medium: rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .container {
            max-width: 1000px;
            margin: 20px auto;
            background: var(--card-bg);
            padding: 30px 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px var(--shadow-medium);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color);
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            font-weight: 600;
        }

        h1 { font-size: 2.5em; border-bottom: 2px solid var(--border-color); padding-bottom: 10px; }
        h2 { font-size: 2em; color: var(--secondary-color); }
        h3 { font-size: 1.5em; color: var(--accent-color); }

        p {
            margin-bottom: 1em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px var(--shadow-light);
            border-radius: 8px;
            overflow: hidden; /* Ensures rounded corners apply to inner elements */
        }

        th, td {
            border: 1px solid var(--border-color);
            padding: 12px 15px;
            text-align: left;
            vertical-align: top;
        }

        th {
            background-color: var(--primary-color);
            color: #fff;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.9em;
        }

        tr:nth-child(even) {
            background-color: #f2f2f2; /* Lighter shade for even rows */
        }

        tr:hover {
            background-color: #e9ecef; /* Hover effect for rows */
        }

        .chart-container {
            position: relative;
            height: 450px; /* Slightly taller charts */
            width: 100%;
            margin-bottom: 30px;
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px var(--shadow-light);
        }

        .references {
            margin-top: 40px;
            border-top: 2px solid var(--border-color);
            padding-top: 25px;
            background-color: #f0f3f6;
            padding: 20px;
            border-radius: 8px;
        }

        .references h3 {
            color: var(--secondary-color);
            margin-top: 0;
        }

        .references ul {
            list-style: disc;
            padding-left: 20px;
            margin: 0;
        }

        .references li {
            margin-bottom: 8px;
            font-size: 0.95em;
            color: #555;
        }

        /* Markdown specific styles */
        div pre {
            background-color: #e9ecef;
            border: 1px solid var(--border-color);
            border-left: 5px solid var(--accent-color);
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            line-height: 1.4;
            margin-bottom: 1.5em;
        }

        div code {
            background-color: #ffe0b2; /* Light orange for inline code */
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }

        div blockquote {
            border-left: 4px solid var(--accent-color);
            margin: 1.5em 0;
            padding: 0.5em 15px;
            background-color: #eaf4fa;
            color: #555;
            font-style: italic;
        }

        div ul, div ol {
            margin-bottom: 1em;
            padding-left: 25px;
        }

        div ul li, div ol li {
            margin-bottom: 0.5em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Portfolio Analysis Report</h1>
        <p>This document provides a detailed analysis of the portfolio, generated by the LangGraph agent.</p>
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
    </div>
</body>
</html>
        """)

        # Render the template
        html_content = template.render(report_data=report_data)

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

