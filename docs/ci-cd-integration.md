# CI/CD Integration

Install the package and run `spira-report`. All config comes from environment variables — store secrets in your platform's secrets manager.

## GitLab CI/CD

```yaml
stages:
  - test
  - report

run_tests:
  stage: test
  script:
    - npm run test
  artifacts:
    paths:
      - test-results/
    when: always

send_to_spira:
  stage: report
  when: always
  variables:
    SPIRA_URL: "https://your-company.spiraservice.net"
    SPIRA_PROJECT_ID: "1"
    SPIRA_TEST_SET_ID: "10"
    SPIRA_RELEASE_ID: "5"
    SPIRA_AUTOMATION_ID_FIELD: "Custom_04"
    SPIRA_RESULTS_DIR: "test-results/"
  script:
    - pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git
    - spira-report
  # SPIRA_USERNAME and SPIRA_API_KEY: Settings > CI/CD > Variables (masked)
```

## GitHub Actions

```yaml
- name: Send results to Spira
  env:
    SPIRA_URL: ${{ secrets.SPIRA_URL }}
    SPIRA_USERNAME: ${{ secrets.SPIRA_USERNAME }}
    SPIRA_API_KEY: ${{ secrets.SPIRA_API_KEY }}
    SPIRA_PROJECT_ID: "1"
    SPIRA_TEST_SET_ID: "10"
    SPIRA_RELEASE_ID: "5"
    SPIRA_RESULTS_DIR: "test-results/"
    SPIRA_AUTOMATION_ID_FIELD: "Custom_04"
  run: |
    pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git
    spira-report
```

Store secrets under Settings > Secrets and variables > Actions.

## Jenkins

```groovy
stage('Report to Spira') {
    environment {
        SPIRA_URL = 'https://your-company.spiraservice.net'
        SPIRA_USERNAME = credentials('spira-username')
        SPIRA_API_KEY = credentials('spira-api-key')
        SPIRA_PROJECT_ID = '1'
        SPIRA_RESULTS_DIR = 'test-results/'
        SPIRA_AUTOMATION_ID_FIELD = 'Custom_04'
    }
    steps {
        sh 'pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git'
        sh 'spira-report'
    }
}
```

## Azure DevOps

```yaml
- script: |
    pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git
    spira-report
  displayName: 'Send results to Spira'
  env:
    SPIRA_URL: $(SPIRA_URL)
    SPIRA_USERNAME: $(SPIRA_USERNAME)
    SPIRA_API_KEY: $(SPIRA_API_KEY)
    SPIRA_RESULTS_DIR: 'test-results/'
    SPIRA_AUTOMATION_ID_FIELD: 'Custom_04'
```

Store secrets under Pipelines > Library > Variable groups.

## Notes for All Platforms

- Store `SPIRA_USERNAME` and `SPIRA_API_KEY` as masked/secret variables
- Run the reporting step with `when: always` / `continue-on-error` so results are sent even when tests fail
- Exit code 0 = success, non-zero = failure
- Use `spira-report --preflight` as an early pipeline stage to catch config issues before tests run
