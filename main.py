import json
import html
import sys

# --- HTML and CSS Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flutter Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #343a40;
        }}
        .container {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }}
        header h1 {{
            color: #1a2b4d;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .summary {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 20px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .summary-metrics {{
            display: flex;
            gap: 30px;
        }}
        .metric {{
            text-align: center;
        }}
        .metric .value {{
            display: block;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .metric .label {{
            font-size: 1em;
            color: #6c757d;
        }}
        .metric .value.total {{ color: #0096FF; }}
        .metric .value.passed {{ color: #28a745; }}
        .metric .value.failed {{ color: #dc3545; }}
        .metric .value.skipped {{ color: #ffc107; }}

        .chart-container {{
            text-align: center;
            margin-top: 20px;
        }}
        #pie-chart {{
            width: 250px;
            height: 250px;
            border-radius: 50%;
            position: relative; /* For positioning the labels */
            margin: 0 auto 15px auto; /* Center it */
            background: #e9ecef; /* Fallback color for no tests */
            {pie_chart_style}
        }}
        .pie-label {{
            position: absolute;
            transform: translate(-50%, -50%);
            color: white;
            font-weight: bold;
            font-size: 1.2em;
            text-shadow: 0 0 4px rgba(0,0,0,0.8);
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9em;
        }}
        .legend-color {{
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .table-container {{
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            border: 1px solid #dee2e6;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background-color: #e9ecef;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .status {{
            padding: 5px 10px;
            border-radius: 15px;
            color: #fff;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.8em;
            display: inline-block;
        }}
        .status-pass {{ background-color: #28a745; }}
        .status-fail {{ background-color: #dc3545; }}
        .status-skip {{ background-color: #ffc107; color: #212529; }}

        .details {{
            width: 100%;
        }}
        .details summary {{
            cursor: pointer;
            outline: none;
            display: block;
        }}
         .details summary::marker, .details summary::-webkit-details-marker {{
            display: none;
        }}
        .toggle-icon {{
            display: inline-block;
            transition: transform 0.2s;
            margin-right: 5px;
        }}
        .details[open] > summary .toggle-icon {{
            transform: rotate(90deg);
        }}
        .error-summary {{
            color: #dc3545;
            font-size: 0.9em;
            font-style: italic;
            font-weight: 500;
            margin-top: 5px;
            display: inline-block;
        }}
        .error-log {{
            margin-top: 10px;
            padding: 15px;
            background-color: #1E1E1E;
            color: #D4D4D4;
            border-radius: 5px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #333;
        }}
        .error-log pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Flutter Test Automation Report</h1>
        </header>
        <div class="summary">
            <div class="summary-metrics">
                <div class="metric">
                    <span id="total-tests" class="value total">{total_tests}</span>
                    <span class="label">Total Tests</span>
                </div>
                <div class="metric">
                    <span id="passed-tests" class="value passed">{passed_tests}</span>
                    <span class="label">Passed</span>
                </div>
                <div class="metric">
                    <span id="failed-tests" class="value failed">{failed_tests}</span>
                    <span class="label">Failed</span>
                </div>
                <div class="metric">
                    <span id="skipped-tests" class="value skipped">{skipped_tests}</span>
                    <span class="label">Skipped</span>
                </div>
            </div>
            <div class="chart-container">
                <div id="pie-chart"></div>
                 <ul class="legend">
                    <li class="legend-item"><span class="legend-color" style="background-color: #28a745;"></span>Passed</li>
                    <li class="legend-item"><span class="legend-color" style="background-color: #dc3545;"></span>Failed</li>
                    <li class="legend-item"><span class="legend-color" style="background-color: #ffc107;"></span>Skipped</li>
                </ul>
            </div>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 10%;">Status</th>
                        <th style="width: 75%;">Test Case</th>
                        <th style="width: 15%;">Duration (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>
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

    pie_chart_style = ""
    if total_count > 0:
        passed_percent = (passed_count / total_count) * 100
        failed_percent = (failed_count / total_count) * 100
        skipped_percent = (skipped_count / total_count) * 100

        slices = []
        cumulative_percent = 0

        # Define order for consistent chart layout
        if failed_count > 0:
            slices.append({'start': cumulative_percent, 'percent': failed_percent, 'color': '#dc3545'})
            cumulative_percent += failed_percent
        if skipped_count > 0:
            slices.append({'start': cumulative_percent, 'percent': skipped_percent, 'color': '#ffc107'})
            cumulative_percent += skipped_percent
        if passed_count > 0:
            slices.append({'start': cumulative_percent, 'percent': passed_percent, 'color': '#28a745'})

        gradient_parts = [f"{s['color']} {s['start']:.2f}% {s['start'] + s['percent']:.2f}%" for s in slices]
        pie_chart_style = f"background: conic-gradient({', '.join(gradient_parts)});"

    final_html = HTML_TEMPLATE.format(
        total_tests=total_count,
        passed_tests=passed_count,
        failed_tests=failed_count,
        skipped_tests=skipped_count,
        table_rows="".join(table_rows_html),
        pie_chart_style=pie_chart_style,
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
