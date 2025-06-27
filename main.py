import json
import sys
import html

# --- HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flutter Integration Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            background-color: #f7f9fc;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #fff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        .summary {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .stats-card {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            flex-grow: 1;
            margin: 10px;
            min-width: 150px;
        }}
        .stats-card .count {{
            display: block;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .stats-card .label {{
            font-size: 1em;
            color: #555;
        }}
        #total-card .count {{ color: #3498db; }}
        #pass-card .count {{ color: #2ecc71; }}
        #fail-card .count {{ color: #e74c3c; }}
        #skip-card .count {{ color: #95a5a6; }}
        .chart-container {{
            width: 50%;
            max-width: 400px;
            margin: 0 auto;
            min-height: 300px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background-color: #34495e;
            color: #ffffff;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .status {{
            padding: 5px 10px;
            color: white;
            border-radius: 5px;
            font-weight: bold;
            text-align: center;
        }}
        .status-pass {{ background-color: #2ecc71; }}
        .status-fail {{ background-color: #e74c3c; }}
        .status-skip {{ background-color: #95a5a6; }}
        .details {{
            cursor: pointer;
        }}
        .error-log {{
            margin-top: 10px;
            padding: 15px;
            background-color: #fbecec;
            border: 1px solid #e74c3c;
            border-radius: 5px;
            font-family: "Courier New", Courier, monospace;
            color: #c0392b;
        }}
        .error-log pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
        }}
        .error-summary {{
             font-weight: bold;
             color: #c0392b;
        }}
        summary {{
            display: block;
            user-select: none;
        }}
        summary::-webkit-details-marker {{
            display: none;
        }}
        .toggle-icon {{
            float: right;
            transition: transform 0.2s;
            font-style: normal;
        }}
        .details[open] summary .toggle-icon {{
            transform: rotate(90deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Flutter Test Report</h1>

        <h2>Summary</h2>
        <div class="summary">
            <div class="stats-card" id="total-card">
                <span class="count">{total_tests}</span>
                <span class="label">Total Tests</span>
            </div>
            <div class="stats-card" id="pass-card">
                <span class="count">{passed_tests}</span>
                <span class="label">Passed</span>
            </div>
            <div class="stats-card" id="fail-card">
                <span class="count">{failed_tests}</span>
                <span class="label">Failed</span>
            </div>
            <div class="stats-card" id="skip-card">
                <span class="count">{skipped_tests}</span>
                <span class="label">Skipped</span>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="testStatusChart"></canvas>
        </div>

        <h2>Test Cases</h2>
        <table>
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Test Name</th>
                    <th>Duration (ms)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>

    <script>
        // Chart.js data and options
        const ctx = document.getElementById('testStatusChart').getContext('2d');
        new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{passed_tests}, {failed_tests}, {skipped_tests}],
                    backgroundColor: ['#2ecc71', '#e74c3c', '#95a5a6'],
                    borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    title: {{
                        display: true,
                        text: 'Test Case Distribution'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""


def parse_test_data(json_file_path):
    """Parses the JSON stream from the test runner."""
    tests = {}
    with open(json_file_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                event_type = event.get('type')

                if event_type == 'testStart':
                    test_info = event['test']
                    test_id = test_info['id']
                    tests[test_id] = {
                        'id': test_id,
                        'name': test_info.get('name', 'Unnamed Test'),
                        'start_time': event.get('time'),
                        'logs': [],
                        'status': 'running',
                        'hidden': False
                    }

                elif event_type == 'print':
                    test_id = event['testID']
                    if test_id in tests:
                        tests[test_id]['logs'].append(event['message'])

                elif event_type == 'error':
                    test_id = event['testID']
                    if test_id in tests:
                        tests[test_id]['status'] = 'fail'
                        error_message = f"ERROR: {event['error']}\nSTACK TRACE:\n{event['stackTrace']}"
                        tests[test_id]['logs'].insert(0, error_message)

                elif event_type == 'testDone':
                    test_id = event['testID']
                    if test_id in tests:
                        # Capture the 'hidden' flag to filter out setup/teardown hooks
                        tests[test_id]['hidden'] = event.get('hidden', False)

                        tests[test_id]['end_time'] = event.get('time')
                        tests[test_id]['duration'] = tests[test_id]['end_time'] - tests[test_id]['start_time']

                        if event.get('skipped'):
                            tests[test_id]['status'] = 'skip'
                        elif tests[test_id]['status'] != 'fail':
                            if event.get('result') == 'success':
                                tests[test_id]['status'] = 'pass'
                            else:  # Any result other than 'success' (e.g., 'error') is a failure
                                tests[test_id]['status'] = 'fail'

            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from line: {line.strip()}")
            except KeyError as e:
                print(f"Warning: Missing expected key {e} in event: {line.strip()}")

    # Filter out hidden tests from the final list
    return [test for test in tests.values() if 'end_time' in test and not test.get('hidden')]


def generate_html_report(all_tests, output_path):
    """Generates the final HTML report from the parsed test data."""
    passed_count, failed_count, skipped_count = 0, 0, 0
    table_rows_html = []

    for test in sorted(all_tests, key=lambda x: x.get('start_time', 0)):
        status = test.get('status', 'skip')
        status_class = f"status-{status}"
        status_text = status.upper()

        row_content = ""
        if status == 'pass':
            passed_count += 1
            row_content = f"""
                <td><span class="status {status_class}">{status_text}</span></td>
                <td>{html.escape(test['name'])}</td>
                <td>{test.get('duration', 'N/A')}</td>
            """
        elif status == 'skip':
            skipped_count += 1
            row_content = f"""
                <td><span class="status {status_class}">{status_text}</span></td>
                <td>{html.escape(test['name'])}</td>
                <td>N/A</td>
            """
        else:  # Fail
            failed_count += 1
            # Join with actual newline for <pre> tag
            log_messages = "\n".join(test.get('logs', ['No logs available.']))
            first_error_line = next((log for log in test.get('logs', []) if 'EXCEPTION' in log or 'ERROR:' in log),
                                    'View Logs')

            row_content = f"""
                <td><span class="status {status_class}">{status_text}</span></td>
                <td>
                     <details class="details">
                        <summary>
                            {html.escape(test['name'])}
                            <i class="toggle-icon">&#9654;</i>
                            <br><span class="error-summary">{html.escape(first_error_line)}</span>
                        </summary>
                        <div class="error-log">
                            <pre>{html.escape(log_messages)}</pre>
                        </div>
                    </details>
                </td>
                <td>{test.get('duration', 'N/A')}</td>
            """

        table_rows_html.append(f"<tr>{row_content}</tr>")

    total_count = passed_count + failed_count + skipped_count

    final_html = HTML_TEMPLATE.format(
        total_tests=total_count,
        passed_tests=passed_count,
        failed_tests=failed_count,
        skipped_tests=skipped_count,
        table_rows="".join(table_rows_html)
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Report successfully generated at: {output_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python report_generator.py <input_json_file> <output_html_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        all_tests = parse_test_data(input_file)
        generate_html_report(all_tests, output_file)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()