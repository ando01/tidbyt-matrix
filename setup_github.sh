#!/bin/bash
# Tidbyt Matrix - GitHub Setup and Push Script
# Run this script to automatically set up your GitHub repository

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Tidbyt Matrix - GitHub Setup Script                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git is not installed${NC}"
    echo "Install git first:"
    echo "  macOS: brew install git"
    echo "  Ubuntu: sudo apt install git"
    echo "  Windows: https://git-scm.com"
    exit 1
fi

echo -e "${GREEN}✓ Git is installed${NC}"
echo ""

# Get user input
read -p "GitHub username: " GITHUB_USERNAME
read -p "Repository name (default: tidbyt-matrix): " REPO_NAME
REPO_NAME=${REPO_NAME:-tidbyt-matrix}

read -p "Local project directory (default: ~/tidbyt-matrix): " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-~/tidbyt-matrix}
PROJECT_DIR=$(eval echo "$PROJECT_DIR")  # Expand ~

read -p "Source files directory (outputs folder path): " SOURCE_DIR

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}✗ Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Creating project structure...${NC}"

# Create project directory
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo -e "${GREEN}✓ Created directory: $PROJECT_DIR${NC}"

# Initialize git repository
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✓ Initialized git repository${NC}"
else
    echo -e "${YELLOW}⚠ Git repository already exists${NC}"
fi

# Configure git (optional if not set globally)
read -p "Configure git user (y/n, default: n): " CONFIGURE_GIT
if [ "$CONFIGURE_GIT" = "y" ]; then
    read -p "Your name: " GIT_NAME
    read -p "Your email: " GIT_EMAIL
    git config user.name "$GIT_NAME"
    git config user.email "$GIT_EMAIL"
    echo -e "${GREEN}✓ Git configured${NC}"
fi

echo ""
echo -e "${BLUE}Copying files...${NC}"

# Copy Python files
echo "Copying Python files..."
cp "$SOURCE_DIR"/tidbyt_matrix.py . 2>/dev/null && echo -e "${GREEN}✓ tidbyt_matrix.py${NC}" || echo -e "${YELLOW}⚠ tidbyt_matrix.py not found${NC}"
cp "$SOURCE_DIR"/tidbyt_apps.py . 2>/dev/null && echo -e "${GREEN}✓ tidbyt_apps.py${NC}" || echo -e "${YELLOW}⚠ tidbyt_apps.py not found${NC}"
cp "$SOURCE_DIR"/tidbyt_main.py . 2>/dev/null && echo -e "${GREEN}✓ tidbyt_main.py${NC}" || echo -e "${YELLOW}⚠ tidbyt_main.py not found${NC}"
cp "$SOURCE_DIR"/tidbyt_web.py . 2>/dev/null && echo -e "${GREEN}✓ tidbyt_web.py${NC}" || echo -e "${YELLOW}⚠ tidbyt_web.py not found${NC}"
cp "$SOURCE_DIR"/real_api_examples.py . 2>/dev/null && echo -e "${GREEN}✓ real_api_examples.py${NC}" || echo -e "${YELLOW}⚠ real_api_examples.py not found${NC}"

# Copy documentation files
echo ""
echo "Copying documentation files..."
mkdir -p docs

cp "$SOURCE_DIR"/README.md . 2>/dev/null && echo -e "${GREEN}✓ README.md${NC}" || echo -e "${YELLOW}⚠ README.md not found${NC}"
cp "$SOURCE_DIR"/QUICKSTART.md . 2>/dev/null && echo -e "${GREEN}✓ QUICKSTART.md${NC}" || echo -e "${YELLOW}⚠ QUICKSTART.md not found${NC}"

cp "$SOURCE_DIR"/EMULATOR_README.md docs/ 2>/dev/null && echo -e "${GREEN}✓ EMULATOR_README.md${NC}" || echo -e "${YELLOW}⚠ EMULATOR_README.md not found${NC}"
cp "$SOURCE_DIR"/EMULATOR_GUIDE.md docs/ 2>/dev/null && echo -e "${GREEN}✓ EMULATOR_GUIDE.md${NC}" || echo -e "${YELLOW}⚠ EMULATOR_GUIDE.md not found${NC}"
cp "$SOURCE_DIR"/EMULATOR_QUICK_REFERENCE.md docs/ 2>/dev/null && echo -e "${GREEN}✓ EMULATOR_QUICK_REFERENCE.md${NC}" || echo -e "${YELLOW}⚠ EMULATOR_QUICK_REFERENCE.md not found${NC}"
cp "$SOURCE_DIR"/EMULATOR_INTEGRATION.md docs/ 2>/dev/null && echo -e "${GREEN}✓ EMULATOR_INTEGRATION.md${NC}" || echo -e "${YELLOW}⚠ EMULATOR_INTEGRATION.md not found${NC}"
cp "$SOURCE_DIR"/EMULATOR_INDEX.md docs/ 2>/dev/null && echo -e "${GREEN}✓ EMULATOR_INDEX.md${NC}" || echo -e "${YELLOW}⚠ EMULATOR_INDEX.md not found${NC}"
cp "$SOURCE_DIR"/EMULATOR_FEATURES.txt docs/ 2>/dev/null && echo -e "${GREEN}✓ EMULATOR_FEATURES.txt${NC}" || echo -e "${YELLOW}⚠ EMULATOR_FEATURES.txt not found${NC}"
cp "$SOURCE_DIR"/SYSTEMD_SETUP.md docs/ 2>/dev/null && echo -e "${GREEN}✓ SYSTEMD_SETUP.md${NC}" || echo -e "${YELLOW}⚠ SYSTEMD_SETUP.md not found${NC}"

# Copy service files
echo ""
echo "Copying service files..."
cp "$SOURCE_DIR"/tidbyt.service . 2>/dev/null && echo -e "${GREEN}✓ tidbyt.service${NC}" || echo -e "${YELLOW}⚠ tidbyt.service not found${NC}"
cp "$SOURCE_DIR"/tidbyt-web.service . 2>/dev/null && echo -e "${GREEN}✓ tidbyt-web.service${NC}" || echo -e "${YELLOW}⚠ tidbyt-web.service not found${NC}"

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo ""
    echo -e "${BLUE}Creating .gitignore...${NC}"
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Config files (with secrets)
tidbyt_config.json
*.env

# Temporary files
*.log
.cache/
tmp/

# OS
.DS_Store
Thumbs.db
EOF
    echo -e "${GREEN}✓ Created .gitignore${NC}"
fi

# Create LICENSE if it doesn't exist
if [ ! -f "LICENSE" ]; then
    echo ""
    echo -e "${BLUE}Creating MIT LICENSE...${NC}"
    cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Tidbyt Matrix Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    echo -e "${GREEN}✓ Created LICENSE${NC}"
fi

# Stage files
echo ""
echo -e "${BLUE}Staging files...${NC}"
git add .
echo -e "${GREEN}✓ Files staged${NC}"

# Show what will be committed
echo ""
echo -e "${BLUE}Files to be committed:${NC}"
git diff --cached --name-only | sed 's/^/  /'

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "1. Create repository on GitHub (if not already created):"
echo "   https://github.com/new"
echo "   - Name: $REPO_NAME"
echo "   - Visibility: Public (optional)"
echo "   - DO NOT initialize with README"
echo ""
echo "2. Once created, come back here and run these commands:"
echo ""
echo -e "${BLUE}cd $PROJECT_DIR${NC}"
echo -e "${BLUE}git commit -m \"Initial commit: Tidbyt matrix display system\"${NC}"
echo -e "${BLUE}git branch -M main${NC}"
echo -e "${BLUE}git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git${NC}"
echo -e "${BLUE}git push -u origin main${NC}"
echo ""
echo "Or run this script with --push flag after creating the repo:"
echo -e "${BLUE}bash $0 --push${NC}"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "For more details, see GITHUB_SETUP.md"
echo ""
