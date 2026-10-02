pipeline {
  agent any
  options { timestamps(); timeout(time: 30, unit: 'MINUTES') }
  environment {
    BASE_URL     = 'http://localhost:5000'
    DATABASE_URL = 'postgresql://qa:qa@localhost:5432/shop'
    HEADLESS     = 'true'
  }
  parameters {
    choice(name: 'SUITE', choices: ['smoke', 'regression', 'negative', 'all'], description: 'Test suite to run')
  }
  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Setup') {
      steps {
        sh '''
          python3 -m venv venv
          . venv/bin/activate
          pip install -r requirements.txt
          docker compose up -d db
          until docker compose exec -T db pg_isready -U qa -d shop; do sleep 2; done
          python -m shop_app.seed
          nohup python -m shop_app.app > app.log 2>&1 &
          for i in $(seq 1 20); do curl -sf $BASE_URL/api/health && break || sleep 1; done
        '''
      }
    }

    stage('API tests (Newman)') {
      steps {
        sh '''
          npx --yes newman run postman/ecommerce_api.postman_collection.json \
              --reporters cli,junit --reporter-junit-export reports/newman.xml || true
        '''
      }
    }

    stage('Pytest') {
      steps {
        sh '''
          . venv/bin/activate
          if [ "$SUITE" = "all" ]; then pytest -n 2; else pytest -m "$SUITE" -n 2; fi
        '''
      }
    }
  }
  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/*.xml'
      archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
      publishHTML(target: [reportDir: 'reports', reportFiles: 'report.html', reportName: 'Pytest HTML Report', allowMissing: true, keepAll: true])
      sh 'docker compose down -v || true; pkill -f shop_app.app || true'
    }
    failure { echo 'Build failed: log defects using docs/defect_report_template.md' }
  }
}
