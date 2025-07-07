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
        /* Universal box-sizing for consistent layout */
        * {
            box-sizing: border-box;
        }

        :root {
            --primary-color: #3498db; /* A professional, vibrant blue */
            --secondary-color: #2ecc71; /* A complementary green */
            --accent-color: #e67e22; /* A warm orange for highlights */
            --text-color: #333333; /* Dark gray for main text */
            --light-text-color: #666666; /* Medium gray for secondary text */
            --bg-color: #f8f9fa; /* Very light gray background */
            --card-bg: #ffffff; /* White for card backgrounds */
            --border-color: #e9ecef; /* Light gray for borders */
            --shadow-light: rgba(0, 0, 0, 0.08);
            --shadow-medium: rgba(0, 0, 0, 0.15);
            --hover-bg: #eaf2f8; /* Light blue for hover effects */
            --code-bg: #f4f4f4; /* Light gray for code blocks */
            --code-inline-bg: #eeeeee; /* Slightly darker gray for inline code */
            --blockquote-bg: #eef4f7; /* Light blue-gray for blockquotes */
        }

        body {
            font-family: 'Roboto', 'Inter', 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            font-size: 16px;
        }

        .container {
            max-width: 1000px;
            margin: 40px auto;
            background: var(--card-bg);
            padding: 40px 60px;
            border-radius: 10px;
            box-shadow: 0 10px 30px var(--shadow-medium);
            border: 1px solid var(--border-color);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color);
            margin-top: 2em;
            margin-bottom: 0.8em;
            font-weight: 700;
            line-height: 1.2;
        }

        h1 {
            font-size: 3em;
            border-bottom: 4px solid var(--primary-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
            text-align: center;
            color: var(--primary-color);
        }
        h2 { font-size: 2.4em; color: var(--secondary-color); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        h3 { font-size: 1.8em; color: var(--primary-color); }
        h4 { font-size: 1.5em; color: var(--text-color); }

        p {
            margin-bottom: 1.5em;
            color: var(--light-text-color);
        }

        table {
            width: 100%;
            border-collapse: collapse; /* Use collapse for cleaner borders */
            margin-bottom: 30px;
            box-shadow: 0 4px 15px var(--shadow-light);
            border-radius: 8px;
            overflow: hidden; /* Ensures rounded corners apply to inner elements */
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
        }

        th, td {
            border: 1px solid var(--border-color); /* Add subtle borders */
            padding: 12px 18px;
            text-align: left;
            vertical-align: middle;
        }

        th {
            background-color: var(--primary-color);
            color: #fff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.08em;
            position: sticky;
            top: 0;
        }

        tr:nth-child(even) {
            background-color: #f2f2f2; /* Lighter shade for even rows */
        }

        tr:hover {
            background-color: var(--hover-bg); /* Hover effect for rows */
            transition: background-color 0.2s ease-in-out;
        }

        td {
            font-size: 0.95em;
        }

        .chart-container {
            position: relative;
            height: 450px; /* Adjusted height for better balance */
            width: 100%;
            margin-bottom: 40px;
            background: var(--card-bg);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 6px 20px var(--shadow-light);
            border: 1px solid var(--border-color);
        }

        .references {
            margin-top: 60px;
            border-top: 2px solid var(--border-color);
            padding-top: 40px;
            background-color: var(--bg-color);
            padding: 30px;
            border-radius: 10px;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
        }

        .references h3 {
            color: var(--primary-color);
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 2em;
            text-align: center;
        }

        .references ul {
            list-style: none;
            padding-left: 0;
            margin: 0;
        }

        .references li {
            margin-bottom: 12px;
            font-size: 1em;
            color: var(--light-text-color);
            padding-left: 30px;
            position: relative;
        }

        .references li:before {
            content: "•";
            color: var(--accent-color);
            position: absolute;
            left: 0;
            font-size: 1.3em;
            line-height: 1;
            top: 2px;
        }

        /* Markdown specific styles */
        div pre {
            background-color: var(--code-bg);
            border: 1px solid var(--border-color);
            border-left: 8px solid var(--secondary-color);
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            line-height: 1.6;
            margin-bottom: 2em;
            box-shadow: inset 0 1px 8px rgba(0,0,0,0.05);
        }

        div code {
            background-color: var(--code-inline-bg);
            padding: 4px 8px;
            border-radius: 4px;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.85em;
            color: var(--primary-color);
        }

        div blockquote {
            border-left: 6px solid var(--accent-color);
            margin: 2em 0;
            padding: 1em 25px;
            background-color: var(--blockquote-bg);
            color: var(--light-text-color);
            font-style: italic;
            border-radius: 8px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.05);
        }

        div ul, div ol {
            margin-bottom: 1.8em;
            padding-left: 35px;
        }

        div ul li, div ol li {
            margin-bottom: 0.8em;
            color: var(--light-text-color);
        }

        /* Header and Footer */
        .report-header {
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 25px;
            border-bottom: 1px solid var(--border-color);
        }

        .report-header h1 {
            font-size: 3.8em;
            color: var(--primary-color);
            margin-bottom: 15px;
            border-bottom: none;
            padding-bottom: 0;
        }

        .report-header p {
            font-size: 1.3em;
            color: var(--light-text-color);
            margin-top: 0;
        }

        .report-footer {
            text-align: center;
            margin-top: 60px;
            padding-top: 25px;
            border-top: 1px solid var(--border-color);
            font-size: 0.95em;
            color: var(--light-text-color);
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .container {
                margin: 20px auto;
                padding: 30px 25px;
            }
            h1 { font-size: 2.5em; }
            h2 { font-size: 2em; }
            h3 { font-size: 1.6em; }
            .chart-container {
                height: 300px;
                padding: 20px;
            }
            th, td {
                padding: 10px 12px;
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
                    <div>{{ sub_section.content }}</div>
                {% endfor %}
            {% else %}
                <div>{{ section.content }}</div>
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

