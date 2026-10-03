pipeline {
  agent any
  options { timestamps(); timeout(time: 45, unit: 'MINUTES') }

  parameters {
    choice(name: 'SUITE', choices: ['smoke', 'regression', 'negative', 'all'], description: 'Pytest suite to run')
    booleanParam(name: 'PARALLEL', defaultValue: false, description: 'Run with pytest -n 2')
  }

  environment {
    COMPOSE = "docker compose -f docker-compose.ci.yml -p qa-ci-${env.BUILD_NUMBER}"
  }

  stages {
    stage('Build images') {
      steps { sh '$COMPOSE build' }
    }

    stage('API tests (Newman)') {
      steps {
        sh '''
          mkdir -p reports
          rc=0
          $COMPOSE run --name newman-$BUILD_NUMBER newman || rc=$?
          docker cp newman-$BUILD_NUMBER:/etc/newman/newman.xml reports/newman.xml || true
          docker rm -f newman-$BUILD_NUMBER || true
          exit $rc
        '''
      }
    }

    stage('Pytest') {
      steps {
        sh '''
          mkdir -p reports
          ARGS="-m $SUITE"
          [ "$SUITE" = "all" ] && ARGS=""
          [ "$PARALLEL" = "true" ] && ARGS="$ARGS -n 2"
          rc=0
          $COMPOSE run --name tests-$BUILD_NUMBER tests pytest $ARGS || rc=$?
          docker cp tests-$BUILD_NUMBER:/app/reports/. reports/ || true
          docker rm -f tests-$BUILD_NUMBER || true
          exit $rc
        '''
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/*.xml'
      archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
      sh '$COMPOSE down -v --remove-orphans || true'
    }
    failure { echo 'Build failed: open the archived report.html / screenshots, then log a defect (docs/defect_report_template.md).' }
  }
}
