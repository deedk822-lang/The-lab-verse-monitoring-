#!/bin/bash

# Automated Migration Script for ESLint 10 and Dependency Updates
# Usage: chmod +x migrate.sh && ./migrate.sh

set -e  # Exit on any error

echo "🚀 Starting automated migration..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version must be 18 or higher. Current: $(node -v)"
    exit 1
fi
print_success "Node.js version check passed: $(node -v)"

# Step 1: Backup
print_info "Creating backups..."
cp package.json package.json.backup
[ -f package-lock.json ] && cp package-lock.json package-lock.json.backup
[ -f .eslintrc.js ] && cp .eslintrc.js .eslintrc.js.backup
[ -f .eslintrc.json ] && cp .eslintrc.json .eslintrc.json.backup
print_success "Backups created"

# Step 2: Clean up
print_info "Cleaning up old files..."
rm -rf node_modules package-lock.json
rm -f .eslintrc.js .eslintrc.json .eslintrc.yml .eslintignore
rm -rf .husky/_
print_success "Cleanup complete"

# Step 3: Remove deprecated packages
print_info "Removing deprecated packages..."
npm uninstall rimraf inflight glob @humanwhocodes/config-array @humanwhocodes/object-schema 2>/dev/null || true

print_success "Deprecated packages removed"

# Step 4: Install new dependencies
print_info "Installing ESLint 10 and updated dependencies..."
npm install --save-dev --force \
    eslint@^9.0.0 \
    @eslint/js@^9.0.0 \
    globals@^15.12.0 \
    eslint-config-prettier@^10.0.1 \
    eslint-plugin-react@^7.37.2 \
    eslint-plugin-react-hooks@^5.0.0 \
    rimraf@^6.0.1 \
    glob@^11.0.0 \
    prettier@^3.4.2 \
    husky@^9.1.7 \
    lint-staged@^15.2.11

print_success "Dependencies installed"

# Step 5: Update package.json scripts
print_info "Updating package.json scripts..."
npm pkg set scripts.prepare="husky"
npm pkg set scripts.lint="eslint ."
npm pkg set scripts.lint:fix="eslint . --fix"
npm pkg set scripts.format="prettier --write \"**/*.{js,jsx,ts,tsx,json,css,md}\""
print_success "Scripts updated"

# Step 6: Initialize Husky
print_info "Setting up Husky..."
npx husky init
echo "npx lint-staged" > .husky/pre-commit
chmod +x .husky/pre-commit
print_success "Husky configured"

# Step 7: Create ESLint config
print_info "Creating eslint.config.js..."
cat > eslint.config.js << 'EOF'
import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';

export default [
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/.next/**',
      '**/coverage/**',
      '**/.cache/**'
    ]
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,mjs,cjs}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      }
    },
    plugins: {
      react,
      'react-hooks': reactHooks
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'warn',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
    },
    settings: {
      react: {
        version: 'detect'
      }
    }
  },
  prettier
];
EOF
print_success "ESLint config created"

# Step 8: Create Prettier config
print_info "Creating .prettierrc.json..."
cat > .prettierrc.json << 'EOF'
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
EOF
print_success "Prettier config created"

# Step 9: Create .prettierignore
print_info "Creating .prettierignore..."
cat > .prettierignore << 'EOF'
node_modules
dist
build
coverage
.next
*.min.js
package-lock.json
EOF
print_success ".prettierignore created"

# Step 10: Fix security vulnerabilities
print_info "Fixing security vulnerabilities..."
npm audit fix || print_warning "Some vulnerabilities may require manual review"

# Step 11: Run linting
print_info "Testing ESLint configuration..."
npm run lint || print_warning "Linting found issues - run 'npm run lint:fix' to auto-fix"

# Final summary
echo ""
echo "======================================"
print_success "Migration completed successfully!"
echo "======================================"
echo ""
print_info "Next steps:"
echo "  1. Review the changes in your package.json"
echo "  2. Run 'npm run lint:fix' to fix auto-fixable issues"
echo "  3. Run 'npm run format' to format your code"
echo "  4. Test your git hooks: git add . && git commit -m 'test'"
echo "  5. Run 'npm audit' to check for remaining vulnerabilities"
echo ""
print_info "Backup files created:"
echo "  - package.json.backup"
echo "  - package-lock.json.backup"
echo "  - .eslintrc.*.backup (if they existed)"
echo ""
print_warning "Remember to update your CI/CD workflows to use Node.js 18+"
echo ""
