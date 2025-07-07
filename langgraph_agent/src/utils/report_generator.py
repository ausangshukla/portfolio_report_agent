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
        *, *::before, *::after {
            box-sizing: border-box;
        }

        :root {
            --primary-color: #2c3e50; /* Dark Slate Blue - professional */
            --secondary-color: #3498db; /* Bright Blue - vibrant accent */
            --accent-color: #e74c3c; /* Muted Red - for highlights/warnings */
            --text-color: #34495e; /* Darker text for readability */
            --light-text-color: #7f8c8d; /* Gray for secondary text */
            --bg-color: #ecf0f1; /* Light Gray - soft background */
            --card-bg: #ffffff; /* White for card backgrounds */
            --border-color: #bdc3c7; /* Light border for structure */
            --shadow-light: rgba(0, 0, 0, 0.05);
            --shadow-medium: rgba(0, 0, 0, 0.12);
            --hover-bg: #f5f7f8; /* Very light gray for hover effects */
            --code-bg: #f8f8f8; /* Light gray for code blocks */
            --code-inline-bg: #e8e8e8; /* Slightly darker gray for inline code */
            --blockquote-bg: #f0f6f9; /* Light blue-gray for blockquotes */
            --header-bg: linear-gradient(135deg, var(--primary-color), #34495e);
        }

        body {
            font-family: 'Inter', 'Roboto', 'Segoe UI', Arial, sans-serif;
            line-height: 1.7;
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            font-size: 17px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 40px 20px;
        }

        .container {
            width: 100%;
            max-width: 1000px;
            background: var(--card-bg);
            padding: 50px 70px;
            border-radius: 12px;
            box-shadow: 0 15px 40px var(--shadow-medium);
            border: 1px solid var(--border-color);
            margin: 0; /* Remove auto margin for flex centering */
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color);
            margin-top: 2.5em;
            margin-bottom: 1em;
            font-weight: 700;
            line-height: 1.3;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 3.5em;
            border-bottom: 5px solid var(--secondary-color);
            padding-bottom: 25px;
            margin-bottom: 40px;
            text-align: center;
            color: var(--primary-color);
            background: var(--header-bg);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        }
        h2 {
            font-size: 2.6em;
            color: var(--secondary-color);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 12px;
            margin-top: 3em;
            font-weight: 600;
        }
        h3 {
            font-size: 2em;
            color: var(--primary-color);
            margin-top: 2.5em;
            font-weight: 600;
        }
        h4 { font-size: 1.6em; color: var(--text-color); }

        p {
            margin-bottom: 1.8em;
            color: var(--text-color);
            font-size: 1.05em;
        }

        table {
            width: 100%;
            border-collapse: separate; /* Use separate for rounded corners on cells */
            border-spacing: 0;
            margin-bottom: 40px;
            box-shadow: 0 6px 20px var(--shadow-light);
            border-radius: 10px;
            overflow: hidden; /* Ensures rounded corners apply to inner elements */
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
        }

        th, td {
            border: none; /* Remove individual cell borders */
            padding: 15px 20px;
            text-align: left;
            vertical-align: middle;
            border-bottom: 1px solid var(--border-color); /* Only bottom border for rows */
        }

        th {
            background-color: var(--primary-color);
            color: #fff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.05em;
            position: sticky;
            top: 0;
            /* Removed white-space: nowrap; to allow header text to wrap */
        }
        th:first-child { border-top-left-radius: 10px; }
        th:last-child { border-top-right-radius: 10px; }

        table {
            table-layout: fixed; /* Ensure fixed table layout */
        }

        tr:nth-child(even) {
            background-color: var(--hover-bg); /* Use hover-bg for subtle zebra striping */
        }

        tr:hover {
            background-color: #e0e8ed; /* Slightly darker hover for better feedback */
            transition: background-color 0.3s ease-in-out;
        }

        td {
            font-size: 1em;
            color: var(--text-color);
        }
        tr:last-child td {
            border-bottom: none; /* Remove bottom border for the last row */
        }


        .chart-container {
            position: relative;
            height: 500px; /* Increased height for better chart visibility */
            width: 100%;
            margin-bottom: 50px;
            background: var(--card-bg);
            padding: 35px;
            border-radius: 12px;
            box-shadow: 0 8px 25px var(--shadow-light);
            border: 1px solid var(--border-color);
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chart-container canvas {
            max-height: 100%;
            max-width: 100%;
        }


        .references {
            margin-top: 70px;
            border-top: 2px solid var(--secondary-color);
            padding-top: 50px;
            background-color: var(--bg-color);
            padding: 35px;
            border-radius: 12px;
            box-shadow: inset 0 3px 15px rgba(0,0,0,0.03);
        }

        .references h3 {
            color: var(--secondary-color);
            margin-top: 0;
            margin-bottom: 25px;
            font-size: 2.2em;
            text-align: center;
            font-weight: 700;
        }

        .references ul {
            list-style: none;
            padding-left: 0;
            margin: 0;
        }

        .references li {
            margin-bottom: 15px;
            font-size: 1.05em;
            color: var(--light-text-color);
            padding-left: 35px;
            position: relative;
            line-height: 1.5;
        }

        .references li:before {
            content: "•";
            color: var(--accent-color);
            position: absolute;
            left: 0;
            font-size: 1.5em;
            line-height: 1;
            top: 0px;
            font-weight: bold;
        }

        /* Markdown specific styles */
        div pre {
            background-color: var(--code-bg);
            border: 1px solid var(--border-color);
            border-left: 10px solid var(--secondary-color);
            padding: 25px;
            border-radius: 10px;
            overflow-x: auto;
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.95em;
            line-height: 1.7;
            margin-bottom: 2.5em;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.03);
        }

        div code {
            background-color: var(--code-inline-bg);
            padding: 5px 9px;
            border-radius: 5px;
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            color: var(--primary-color);
            white-space: nowrap;
        }

        div blockquote {
            border-left: 8px solid var(--accent-color);
            margin: 2.5em 0;
            padding: 1.2em 30px;
            background-color: var(--blockquote-bg);
            color: var(--text-color);
            font-style: italic;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            line-height: 1.8;
        }

        div ul, div ol {
            margin-bottom: 2em;
            padding-left: 40px;
        }

        div ul li, div ol li {
            margin-bottom: 1em;
            color: var(--text-color);
            font-size: 1.05em;
        }

        /* Header and Footer */
        .report-header {
            text-align: center;
            margin-bottom: 60px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--border-color);
        }

        .report-header h1 {
            font-size: 4.2em;
            color: var(--primary-color);
            margin-bottom: 20px;
            border-bottom: none;
            padding-bottom: 0;
            background: none; /* Remove gradient for header in this context */
            -webkit-background-clip: unset;
            -webkit-text-fill-color: unset;
            text-shadow: none;
        }

        .report-header p {
            font-size: 1.4em;
            color: var(--light-text-color);
            margin-top: 0;
            line-height: 1.5;
        }

        .report-footer {
            text-align: center;
            margin-top: 70px;
            padding-top: 30px;
            border-top: 1px solid var(--border-color);
            font-size: 1em;
            color: var(--light-text-color);
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            body {
                padding: 15px;
            }
            .container {
                margin: 0;
                padding: 30px 25px;
                border-radius: 8px;
            }
            h1 { font-size: 3em; margin-bottom: 30px; padding-bottom: 20px; }
            h2 { font-size: 2.2em; margin-top: 2.5em; }
            h3 { font-size: 1.8em; margin-top: 2em; }
            p { font-size: 1em; margin-bottom: 1.5em; }
            .chart-container {
                height: 350px;
                padding: 25px;
                margin-bottom: 30px;
            }
            th, td {
                padding: 12px 15px;
                font-size: 0.9em;
            }
            .references {
                margin-top: 50px;
                padding-top: 30px;
            }
            .references h3 {
                font-size: 1.8em;
                margin-bottom: 20px;
            }
            .references li {
                font-size: 0.95em;
                padding-left: 25px;
            }
            div pre {
                padding: 20px;
                font-size: 0.85em;
            }
            div code {
                font-size: 0.8em;
            }
            div blockquote {
                padding: 1em 20px;
            }
            div ul, div ol {
                padding-left: 30px;
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
            {% if section.current_section_sub_sections %} {# Use current_section_sub_sections for structured content #}
                {% for sub_section in section.current_section_sub_sections %}
                    <h3>{{ sub_section.title }}</h3>
                    <div>{{ sub_section.content | markdown_to_html }}</div> {# Apply markdown filter here if content might have markdown #}
                {% endfor %}
            {% elif section.content %} {# Fallback to section.content if no structured sub_sections #}
                <div>{{ section.content | markdown_to_html }}</div> {# Apply markdown filter #}
            {% endif %}

            {% if section.tabular_data %}
                <h3>{{ section.tabular_data.title }}</h3>
                <div style="overflow-x: auto;"> {# Add responsive wrapper for tables #}
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
                </div>
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
                                                    text: "{{ graph_spec.title }}",
                                                    font: {
                                                        size: 18,
                                                        weight: 'bold'
                                                    },
                                                    color: 'var(--text-color)'
                                                },
                                                legend: {
                                                    labels: {
                                                        font: {
                                                            size: 14
                                                        },
                                                        color: 'var(--light-text-color)'
                                                    }
                                                }
                                            },
                                            scales: {
                                                x: {
                                                    ticks: {
                                                        color: 'var(--light-text-color)',
                                                        font: {
                                                            size: 12
                                                        }
                                                    },
                                                    grid: {
                                                        color: 'rgba(0, 0, 0, 0.05)'
                                                    }
                                                },
                                                y: {
                                                    ticks: {
                                                        color: 'var(--light-text-color)',
                                                        font: {
                                                            size: 12
                                                        }
                                                    },
                                                    grid: {
                                                        color: 'rgba(0, 0, 0, 0.05)'
                                                    }
                                                },
                                                'y-axis-1': { // For primary Y-axis
                                                    type: 'linear',
                                                    position: 'left',
                                                    ticks: {
                                                        color: 'var(--secondary-color)',
                                                        font: {
                                                            size: 12
                                                        }
                                                    },
                                                    grid: {
                                                        drawOnChartArea: false, // Only draw grid lines for the first Y-axis
                                                        color: 'rgba(0, 0, 0, 0.05)'
                                                    }
                                                },
                                                'y-axis-2': { // For secondary Y-axis (e.g., percentages)
                                                    type: 'linear',
                                                    position: 'right',
                                                    ticks: {
                                                        color: 'var(--accent-color)',
                                                        font: {
                                                            size: 12
                                                        }
                                                    },
                                                    grid: {
                                                        drawOnChartArea: false // Do not draw grid lines for the second Y-axis
                                                    }
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

