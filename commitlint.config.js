/**
 * Commitlint Configuration
 * Enforces conventional commit message format
 * 
 * Format: <type>(<scope>): <subject>
 * 
 * Examples:
 *   feat(api): add new endpoint for user management
 *   fix(auth): resolve token validation issue
 *   docs: update API documentation
 *   test(integration): add tests for webhook handler
 */

export default {
  extends: ['@commitlint/config-conventional'],
  
  rules: {
    // Enforce type-enum
    'type-enum': [
      2,
      'always',
      [
        'feat',      // New feature
        'fix',       // Bug fix
        'docs',      // Documentation only
        'style',     // Formatting, missing semicolons, etc
        'refactor',  // Code change that neither fixes a bug nor adds a feature
        'perf',      // Performance improvement
        'test',      // Adding or updating tests
        'build',     // Changes to build system or dependencies
        'ci',        // CI configuration changes
        'chore',     // Other changes that don't modify src or test files
        'revert',    // Revert a previous commit
        'wip',       // Work in progress
        'hotfix'     // Critical production fix
      ]
    ],
    
    // Enforce max subject length
    'subject-max-length': [2, 'always', 100],
    
    // Subject should not be empty
    'subject-empty': [2, 'never'],
    
    // Type should not be empty
    'type-empty': [2, 'never'],
    
    // Subject should be lowercase
    'subject-case': [2, 'always', 'lower-case'],
    
    // Body should have a blank line before it
    'body-leading-blank': [2, 'always'],
    
    // Footer should have a blank line before it
    'footer-leading-blank': [2, 'always'],
    
    // Scope should be lowercase
    'scope-case': [2, 'always', 'lower-case']
  },
  
  // Ignore patterns
  ignores: [
    (message) => message.startsWith('Merge'),
    (message) => message.startsWith('Revert'),
    (message) => message.includes('WIP')
  ]
};
