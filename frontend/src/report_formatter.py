# At the top of your file, add:
from src.report_formatter import ReportFormatter

# Then use it like this:

# ============= EXAMPLE =============
# After you get your diagnostic JSON
formatter = ReportFormatter(width=120)

diagnostic_report = formatter.format_diagnostic_report(diagnostic_data)
print(diagnostic_report)

# Save to file
formatter.save_to_file(diagnostic_report, "diagnostic_report.txt")



import art

class ReportFormatter:
    def __init__(self, title, confidence_score, explanation):
        self.title = title
        self.confidence_score = confidence_score
        self.explanation = explanation

    def format_report(self):
        separator = "#" * 50
        ascii_art = art.text2art(self.title, font='block')

        formatted_output = f"{separator}\n{ascii_art}\n{separator}\n"
        formatted_output += f"Confidence Score: {self.confidence_score:.2f}\n"
        formatted_output += f"Explanation: {self.explanation}\n"
        formatted_output += f"{separator}\n"

        return formatted_output

# Example usage:
if __name__ == '__main__':
    report = ReportFormatter('Analysis Report', 0.95, 'The results are highly reliable.')
    print(report.format_report())