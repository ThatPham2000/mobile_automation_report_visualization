import json
import base64
from datetime import timedelta
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns


def parse_test_data(data):
    """Parses the JSON test data into a structured format."""
    tests = {}
    groups = {}
    suites = {}

    start_time = 0
    end_time = 0

    for item in data:
        evt_type = item.get("type")

        if evt_type == "start":
            start_time = item.get("time")

        elif evt_type == "suite":
            suite_info = item.get("suite", {})
            suites[suite_info["id"]] = {
                "name": suite_info.get("path", "Unknown Suite"),
                "platform": suite_info.get("platform"),
                "tests": []
            }

        elif evt_type == "group":
            group_info = item.get("group", {})
            groups[group_info["id"]] = group_info

        elif evt_type == "testStart":
            test_info = item.get("test", {})
            test_id = test_info["id"]
            tests[test_id] = {
                "id": test_id,
                "name": test_info.get("name"),
                "suite_id": test_info.get("suiteID"),
                "start_time": item.get("time"),
                "logs": [],
                "errors": [],
                "hidden": test_info.get("metadata", {}).get("skip", False)
            }

        elif evt_type == "print":
            test_id = item.get("testID")
            if test_id in tests:
                tests[test_id]["logs"].append(item.get("message"))

        elif evt_type == "error":
            test_id = item.get("testID")
            if test_id in tests:
                tests[test_id]["errors"].append(item.get("error"))

        elif evt_type == "testDone":
            test_id = item.get("testID")
            if test_id in tests:
                tests[test_id].update({
                    "result": item.get("result"),
                    "skipped": item.get("skipped"),
                    "hidden": tests[test_id].get('hidden') or item.get("hidden", False),
                    "end_time": item.get("time")
                })
        elif evt_type == "done":
            end_time = item.get("time")

    # Process results
    for test_id, test in tests.items():
        if test.get("start_time") is not None and test.get("end_time") is not None:
            test["duration_ms"] = test["end_time"] - test["start_time"]
        else:
            test["duration_ms"] = 0

        if test.get("suite_id") in suites:
            # We only care about visible tests for the report details
            if not test.get("hidden"):
                suites[test["suite_id"]]["tests"].append(test)

    total_duration_ms = end_time - start_time

    # Filter out hidden tests for summary counts
    visible_tests = [t for t in tests.values() if not t.get("hidden")]

    return suites, visible_tests, total_duration_ms


def create_summary_pie_chart(test_results):
    """Creates a pie chart of test results and returns it as a base64 string."""
    results = [r['result'] for r in test_results]
    passed = results.count('success')
    failed = results.count('error')
    skipped = len([r for r in test_results if r.get('skipped')])

    labels = []
    sizes = []
    colors = []

    if passed > 0:
        labels.append(f'Passed ({passed})')
        sizes.append(passed)
        colors.append('#4CAF50')
    if failed > 0:
        labels.append(f'Failed ({failed})')
        sizes.append(failed)
        colors.append('#F44336')
    if skipped > 0:
        labels.append(f'Skipped ({skipped})')
        sizes.append(skipped)
        colors.append('#FFC107')

    if not sizes:
        return None

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90,
           wedgeprops={"edgecolor": "white", 'linewidth': 1})
    ax.axis('equal')
    plt.title('Test Result Distribution', pad=20)

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def create_duration_bar_chart(test_results):
    """Creates a bar chart of test durations and returns it as a base64 string."""
    if not test_results:
        return None

    # Sort tests by duration
    sorted_tests = sorted(test_results, key=lambda x: x['duration_ms'], reverse=True)

    # Truncate long test names
    names = [
        (name[:75] + '...') if len(name) > 78 else name
        for name in [r['name'].split(']:')[-1].strip() for r in sorted_tests]
    ]
    durations_s = [r['duration_ms'] / 1000.0 for r in sorted_tests]
    results = [r['result'] for r in sorted_tests]

    # Assign colors based on result
    palette = {'success': '#4CAF50', 'error': '#F44336', 'skipped': '#FFC107'}
    bar_colors = [palette.get(res, '#9E9E9E') for res in results]

    fig, ax = plt.subplots(figsize=(10, len(names) * 0.5 + 1))
    sns.barplot(x=durations_s, y=names, ax=ax, palette=bar_colors, orient='h')

    ax.set_title('Test Execution Duration', pad=20)
    ax.set_xlabel('Duration (seconds)')
    ax.set_ylabel('Test Case')
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    # Add duration labels on bars
    for i, (p, d) in enumerate(zip(ax.patches, durations_s)):
        ax.text(p.get_width(), i, f' {d:.2f}s', va='center')

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def generate_html_report(suites, test_results, total_duration_ms, pie_chart_b64, duration_chart_b64):
    """Generates a self-contained HTML report."""

    passed_count = sum(1 for t in test_results if t.get('result') == 'success' and not t.get('skipped'))
    failed_count = sum(1 for t in test_results if t.get('result') != 'success' and not t.get('skipped'))
    skipped_count = sum(1 for t in test_results if t.get('skipped'))
    total_tests = len(test_results)

    overall_status = "Failed" if failed_count > 0 else "Passed"
    overall_status_color = "#F44336" if failed_count > 0 else "#4CAF50"

    total_duration_str = str(timedelta(milliseconds=total_duration_ms)).split('.')[0]

    test_details_html = ""
    for suite_id, suite in suites.items():
        test_details_html += f"<h2>Test Suite: {suite['name']}</h2>"
        for test in sorted(suite['tests'], key=lambda x: x['id']):
            result = test['result']
            status_class = "success" if result == 'success' else 'error' if result == 'error' else 'skipped'
            duration_s = test['duration_ms'] / 1000.0

            logs_html = ""
            if test['logs'] or test['errors']:
                logs_html = "<details class='logs'><summary>Logs & Errors</summary><pre><code>"
                if test['logs']:
                    logs_html += "\n".join(test['logs'])
                if test['errors']:
                    logs_html += "\n\n--- ERRORS ---\n" + "\n".join(test['errors'])
                logs_html += "</code></pre></details>"

            test_details_html += f"""
            <div class="test-case {status_class}">
                <div class="test-header">
                    <span class="test-name">{test['name']}</span>
                    <span class="test-status">{result.upper()}</span>
                    <span class="test-duration">{duration_s:.2f}s</span>
                </div>
                {logs_html}
            </div>
            """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flutter Test Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background-color: #f7f9fc; color: #333; }}
            .container {{ max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #01579B; }}
            .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; text-align: center; margin-bottom: 30px; }}
            .summary-box {{ padding: 20px; border-radius: 8px; color: #fff; }}
            .summary-box .value {{ font-size: 2em; font-weight: bold; }}
            .total-tests {{ background-color: #0277BD; }}
            .passed-tests {{ background-color: #4CAF50; }}
            .failed-tests {{ background-color: #F44336; }}
            .skipped-tests {{ background-color: #FFC107; }}
            .duration {{ background-color: #607D8B; }}
            .overall-status {{ grid-column: 1 / -1; padding: 15px; font-size: 1.5em; border-radius: 8px; color: white; background-color: {overall_status_color}; }}
            .charts {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-bottom: 30px; }}
            .charts img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            h2 {{ color: #0277BD; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
            .test-case {{ border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px; overflow: hidden; }}
            .test-header {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background-color: #f9f9f9; }}
            .test-name {{ font-weight: 500; flex-grow: 1; }}
            .test-status {{ padding: 4px 10px; border-radius: 12px; color: white; font-size: 0.8em; font-weight: bold; }}
            .test-duration {{ font-family: monospace; font-size: 0.9em; color: #555; margin-left: 20px; }}
            .test-case.success .test-header {{ border-left: 5px solid #4CAF50; }}
            .test-case.success .test-status {{ background-color: #4CAF50; }}
            .test-case.error .test-header {{ border-left: 5px solid #F44336; }}
            .test-case.error .test-status {{ background-color: #F44336; }}
            .test-case.skipped .test-header {{ border-left: 5px solid #FFC107; }}
            .test-case.skipped .test-status {{ background-color: #FFC107; }}
            .logs {{ margin: 0 15px 10px 15px; }}
            .logs summary {{ cursor: pointer; color: #0277BD; font-size: 0.9em; padding: 5px 0; }}
            .logs pre {{ background-color: #2d2d2d; color: #f1f1f1; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Flutter Integration Test Report</h1>
            <div class="summary">
                <div class="overall-status">Overall Status: {overall_status}</div>
                <div class="summary-box total-tests"><div class="value">{total_tests}</div><div>Total Tests</div></div>
                <div class="summary-box passed-tests"><div class="value">{passed_count}</div><div>Passed</div></div>
                <div class="summary-box failed-tests"><div class="value">{failed_count}</div><div>Failed</div></div>
                <div class="summary-box duration"><div class="value">{total_duration_str}</div><div>Total Duration</div></div>
            </div>

            <div class="charts">
                <img src="data:image/png;base64,{pie_chart_b64}" alt="Test Results Pie Chart">
                <img src="data:image/png;base64,{duration_chart_b64}" alt="Test Durations Bar Chart">
            </div>

            <div class="test-details">
                {test_details_html}
            </div>
        </div>
    </body>
    </html>
    """

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    """Main function to generate the report."""
    try:
        data = []
        with open('report.jsonl', 'r') as jsonl_file:
            for line in jsonl_file:
                data.append(json.loads(line))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    suites, test_results, total_duration_ms = parse_test_data(data)

    if not test_results:
        print("No visible test results found in the data.")
        return

    pie_chart_b64 = create_summary_pie_chart(test_results)
    duration_chart_b64 = create_duration_bar_chart(test_results)

    generate_html_report(suites, test_results, total_duration_ms, pie_chart_b64, duration_chart_b64)

    print("Report 'report.html' generated successfully.")


if __name__ == "__main__":
    main()