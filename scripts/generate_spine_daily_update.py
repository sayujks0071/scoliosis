import datetime
import os
import re


def parse_roadmap(filepath):
    """
    Parses the roadmap markdown file to extract tasks and calculate progress.
    """
    if not os.path.exists(filepath):
        return None, "Roadmap file not found."

    with open(filepath, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    total_tasks = 0
    completed_tasks = 0
    phases = {}
    current_phase = None

    start_date_match = re.search(r'\*\*Start Date:\*\* (\d{4}-\d{2}-\d{2})', content)
    target_date_match = re.search(r'\*\*Target Submission Date:\*\* (\d{4}-\d{2}-\d{2})', content)

    start_date = datetime.datetime.strptime(start_date_match.group(1), '%Y-%m-%d').date() if start_date_match else None
    target_date = datetime.datetime.strptime(target_date_match.group(1), '%Y-%m-%d').date() if target_date_match else None

    for line in lines:
        if line.startswith('## Phase'):
            current_phase = line.strip().replace('## ', '')
            phases[current_phase] = {'total': 0, 'completed': 0}

        if line.strip().startswith('- ['):
            total_tasks += 1
            if current_phase:
                phases[current_phase]['total'] += 1

            if line.strip().startswith('- [x]'):
                completed_tasks += 1
                if current_phase:
                    phases[current_phase]['completed'] += 1

    percent_complete = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'percent_complete': percent_complete,
        'phases': phases,
        'start_date': start_date,
        'target_date': target_date
    }, None

def generate_report(data):
    """
    Generates a formatted daily update report.
    """
    today = datetime.date.today()

    if data['target_date']:
        days_remaining = (data['target_date'] - today).days
        expected_completion_str = f"{data['target_date']} ({days_remaining} days remaining)"
    else:
        expected_completion_str = "TBD"

    report = f"""# Daily Update: Spine Submission

**Date:** {today}
**Target Journal:** Spine (IF: 3.30, Q1)
**Strategy:** Computational Framework + Clinical Validation

## Status Overview
- **Percent Complete:** {data['percent_complete']:.1f}%
- **Tasks Completed:** {data['completed_tasks']} / {data['total_tasks']}
- **Expected Completion:** {expected_completion_str}

## Phase Breakdown
"""

    active_phase = "None"
    for phase, stats in data['phases'].items():
        phase_percent = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status_icon = "✅" if phase_percent == 100 else "🔄" if phase_percent > 0 else "⚪"
        report += f"- {status_icon} **{phase}:** {phase_percent:.1f}% ({stats['completed']}/{stats['total']})\n"

        if phase_percent < 100 and active_phase == "None":
            active_phase = phase

    report += f"\n**Current Focus:** {active_phase}\n"

    return report

if __name__ == "__main__":
    roadmap_path = "docs/spine_submission_roadmap.md"
    data, error = parse_roadmap(roadmap_path)

    if error:
        print(error)
    else:
        print(generate_report(data))
