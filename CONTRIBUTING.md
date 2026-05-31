# Contributing to PyThrust

We welcome contributions to PyThrust! To maintain code quality and ensure a smooth review process, please follow these guidelines:

## 1. How to Report Issues
- Use the GitHub Issue Tracker to report bugs, suggest enhancements, or ask questions.
- Please provide a minimal reproducible example (MRE) when reporting bugs.

## 2. Development Workflow
1. Fork the repository and create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Set up the development environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run tests using `pytest` to make sure your changes don't break existing functionality:
   ```bash
   pytest
   ```
4. Write unit tests for any new features or bug fixes.
5. Submit a Pull Request (PR) describing your changes and matching issue.

## 3. Support and Community Governance
- For support, please open a GitHub Issue or reach out to Hüseyin Karakaya.
- Project governance follows a transparent BDFL (Benevolent Dictator for Life) model led by the main author.
