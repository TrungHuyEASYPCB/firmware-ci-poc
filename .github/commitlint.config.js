module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Type must be one of the allowed values
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'chore',
        'docs',
        'refactor',
        'test',
        'perf',
        'ci',
        'revert',
        'hotfix',
      ],
    ],
    // Subject line max length
    'header-max-length': [2, 'always', 72],
    // Subject may not be title/sentence/upper case — but lowercase with
    // acronyms (AT, RGB, LCD, LTE, SPI) is allowed
    'subject-case': [
      2,
      'never',
      ['sentence-case', 'start-case', 'pascal-case', 'upper-case'],
    ],
    // Subject must not end with a period
    'subject-full-stop': [2, 'never', '.'],
    // Type must be lowercase
    'type-case': [2, 'always', 'lower-case'],
    // Type must not be empty
    'type-empty': [2, 'never'],
    // Scope must be lowercase if provided
    'scope-case': [2, 'always', 'lower-case'],
  },
};
