#!/bin/bash
# Linting script for Puntini Backend
# This script runs all linting tools and provides a comprehensive report

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the backend directory"
    exit 1
fi

# Create reports directory
mkdir -p reports

print_status "Starting comprehensive linting process..."

# 1. Ruff - Fast Python linter
print_status "Running Ruff linter..."
if ruff check . --output-format=json > reports/ruff-report.json 2>&1; then
    print_success "Ruff check passed"
else
    print_warning "Ruff found issues (see reports/ruff-report.json)"
fi

# 2. Black - Code formatter
print_status "Checking code formatting with Black..."
if black --check --diff . > reports/black-report.txt 2>&1; then
    print_success "Black formatting check passed"
else
    print_warning "Black found formatting issues (see reports/black-report.txt)"
fi

# 3. isort - Import sorting
print_status "Checking import sorting with isort..."
if isort --check-only --diff . > reports/isort-report.txt 2>&1; then
    print_success "isort check passed"
else
    print_warning "isort found import sorting issues (see reports/isort-report.txt)"
fi

# 4. Flake8 - Style guide enforcement
print_status "Running Flake8 linter..."
if flake8 . --output-file=reports/flake8-report.txt --count --statistics; then
    print_success "Flake8 check passed"
else
    print_warning "Flake8 found issues (see reports/flake8-report.txt)"
fi

# 5. MyPy - Type checking
print_status "Running MyPy type checker..."
if mypy . --ignore-missing-imports --junit-xml=reports/mypy-report.xml > reports/mypy-report.txt 2>&1; then
    print_success "MyPy type checking passed"
else
    print_warning "MyPy found type issues (see reports/mypy-report.txt)"
fi

# 6. Pylint - Comprehensive linting
print_status "Running Pylint..."
if pylint api/ config/ models/ graphstore/ agent/ --rcfile=pyproject.toml --output-format=json > reports/pylint-report.json 2>&1; then
    print_success "Pylint check passed"
else
    print_warning "Pylint found issues (see reports/pylint-report.json)"
fi

# 7. Bandit - Security linting
print_status "Running Bandit security linter..."
if bandit -r . -f json -o reports/bandit-report.json -ll; then
    print_success "Bandit security check passed"
else
    print_warning "Bandit found security issues (see reports/bandit-report.json)"
fi

# 8. Safety - Dependency vulnerability check
print_status "Running Safety dependency check..."
if safety check --output json > reports/safety-report.json; then
    print_success "Safety check passed"
else
    print_warning "Safety found dependency vulnerabilities (see reports/safety-report.json)"
fi

# Generate summary report
print_status "Generating summary report..."

cat > reports/lint-summary.md << EOF
# Linting Report Summary

Generated on: $(date)

## Tools Run

1. **Ruff** - Fast Python linter
2. **Black** - Code formatter
3. **isort** - Import sorting
4. **Flake8** - Style guide enforcement
5. **MyPy** - Type checking
6. **Pylint** - Comprehensive linting
7. **Bandit** - Security linting
8. **Safety** - Dependency vulnerability check

## Reports Generated

- \`ruff-report.json\` - Ruff linting results
- \`black-report.txt\` - Black formatting issues
- \`isort-report.txt\` - Import sorting issues
- \`flake8-report.txt\` - Flake8 style issues
- \`mypy-report.txt\` - MyPy type checking results
- \`mypy-report.xml\` - MyPy results in JUnit format
- \`pylint-report.json\` - Pylint comprehensive results
- \`bandit-report.json\` - Security issues
- \`safety-report.json\` - Dependency vulnerabilities

## Quick Fix Commands

To fix auto-fixable issues:

\`\`\`bash
# Fix Ruff issues
ruff check . --fix

# Format code with Black
black .

# Sort imports with isort
isort .

# Run all fixes
make lint-fix
\`\`\`

## Next Steps

1. Review the generated reports
2. Fix critical issues first (security, type errors)
3. Address style and formatting issues
4. Run tests to ensure nothing is broken
5. Commit changes with descriptive messages

EOF

print_success "Linting process completed!"
print_status "Reports generated in the 'reports/' directory"
print_status "Run 'make lint-fix' to auto-fix many issues"

# Show quick summary
echo ""
echo "=== QUICK SUMMARY ==="
echo "Reports directory: $(pwd)/reports/"
echo "Summary report: $(pwd)/reports/lint-summary.md"
echo ""
echo "To fix auto-fixable issues: make lint-fix"
echo "To run specific linter: make lint"
echo ""
