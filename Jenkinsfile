pipeline {
    agent none

    environment {
        DOCKERHUB_USER = 'thatavarthi403'
        IMAGE_NAME     = 'flask-app'
        DOCKERHUB_PASS = credentials('dockerhub-creds')
    }

    options {
        timestamps()
    }

    stages {

        /* ---------------------------------------------------------
            SHOW BRANCH INFO (for multibranch)
        ----------------------------------------------------------*/
        stage('Branch Info') {
            agent { label 'built-in' }
            steps {
                echo "Building job: ${env.JOB_NAME}"
                echo "Building branch: ${env.BRANCH_NAME}"
                script {
                    // Derive a sonar project key that is unique per repo/branch
                    env.SONAR_PROJECT_KEY = "${env.JOB_NAME}-${env.BRANCH_NAME}".replaceAll('[^A-Za-z0-9_.-]', '_')
                }
            }
        }

        /* ---------------------------------------------------------
            CHECKOUT – ALWAYS ON JENKINS MASTER (multibranch-friendly)
        ----------------------------------------------------------*/
        stage('Checkout Code') {
            agent { label 'built-in' }
            steps {
                echo "Checking out source code (scm)..."
                checkout scm
                stash name: 'source_code', includes: '**'
                echo "Source code stashed."
            }
        }

        /* ---------------------------------------------------------
            PYLINT ANALYSIS – RUNS ON ALL BRANCHES
        ----------------------------------------------------------*/
        stage('Pylint Analysis') {
            agent { label 'jenkins-build-node' }
            steps {
                unstash 'source_code'

                sh '''
                    set -e
                    # prepare lightweight venv for linting
                    if ! command -v python3 &> /dev/null; then
                        echo "python3 not found on node"
                        exit 1
                    fi
                    python3 -m venv .venv_pylint
                    . .venv_pylint/bin/activate
                    pip install --upgrade pip
                    pip install pylint

                    # run pylint and save output for Jenkins warnings plugin
                    echo "Running pylint..."
                    pylint --output-format=text $(find . -name "*.py" | grep -v 
".venv_pylint" || true) > pylint.log || true
                '''

                // record Pylint results with Warnings NG (pylint parser)
                recordIssues tools: [pylint(pattern: 'pylint.log')], stable: true
                archiveArtifacts artifacts: 'pylint.log', allowEmptyArchive: true
            }
        }

        /* ---------------------------------------------------------
            SONARQUBE ANALYSIS – RUNS ON ALL BRANCHES
        ----------------------------------------------------------*/
        stage('SonarQube Analysis') {
            agent { label 'jenkins-build-node' }
            environment {
                SCANNER_HOME = tool 'SonarScanner'
            }
            steps {
                unstash 'source_code'

                withSonarQubeEnv('SonarQube') {
                    sh "${SCANNER_HOME}/bin/sonar-scanner -Dsonar.projectKey=${env.SONAR_PROJECT_KEY} -Dsonar.sources=. -Dsonar.host.url=${env.SONAR_HOST_URL} || true"
                }

                // Wait for SonarQube Quality Gate (requires SonarQube plugin)
                script {
                    timeout(time: 5, unit: 'MINUTES') {
                        def qg = waitForQualityGate(abortPipeline: true)
                        echo "SonarQube Quality Gate status: ${qg.status}"
                    }
                }
            }
        }

        /* ---------------------------------------------------------
            RUN PYTESTS + COVERAGE – RUNS ON ALL BRANCHES
        ----------------------------------------------------------*/
        stage('Run PyTests & Coverage') {
            agent { label 'jenkins-build-node' }
            steps {
                unstash 'source_code'

                sh '''
                    set -e
                    if ! command -v python3 &> /dev/null; then
                        echo "python3 not found on node"
                        exit 1
                    fi

                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt || pip install flask pytest pytest-cov

                    echo "Running pytest with coverage..."
                    pytest -v --junitxml=test-results.xml --cov=./ --cov-report=xml:coverage.xml --cov-report=html:coverage_html || true
                '''

                // publish test results and coverage
                junit 'test-results.xml'
                archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
                archiveArtifacts artifacts: 'coverage_html/**', allowEmptyArchive: true

                publishHTML(target: [
                    reportName: 'Coverage Report',
                    reportDir: 'coverage_html',
                    reportFiles: 'index.html',
                    keepAll: true,
                    allowMissing: true
                ])
            }
            post {
                always {
                    echo 'Tests & Coverage stage finished.'
                }
            }
        }

        /* ---------------------------------------------------------
            BUILD & PUSH DOCKER IMAGE – ONLY ON MAIN
        ----------------------------------------------------------*/
        stage('Build & Push Docker Image') {
            when {
                branch 'main'
            }
            agent { label 'jenkins-build-node' }
            environment {
                BUILD_VERSION = "${env.BUILD_NUMBER}"
            }
            steps {
                unstash 'source_code'

                sh '''
                    set -e
                    echo "Logging into DockerHub..."
                    echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin

                    echo "Building Docker image..."
                    docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION .

                    echo "Pushing versioned image..."
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION

                    echo "Tagging and pushing latest image..."
                    docker tag $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION $DOCKERHUB_USER/$IMAGE_NAME:latest
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:latest || true

                    echo "Cleaning up..."
                    docker system prune -af || true
                '''

                echo "Docker image build & push complete."
            }
        }

        /* -----------------------------------------------------------
            DEPLOY – ONLY ON MAIN BRANCH
        -----------------------------------------------------------*/
        stage('Deploy to Server') {
            when {
                branch 'main'
            }
            agent { label 'jenkins-deployment-node' }
            steps {
                sh '''
                    set -e
                    echo "Logging into DockerHub..."
                    echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin

                    echo "Pulling latest image..."
                    docker pull $DOCKERHUB_USER/$IMAGE_NAME:latest || true

                    echo "Stopping existing container..."
                    docker stop flask-app || true
                    docker rm flask-app || true

                    echo "Starting new container..."
                    docker run -d --name flask-app -p 5000:5000 $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Deployment completed!"
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed.'
            // keep basic artifacts for debugging
            archiveArtifacts artifacts: 'pylint.log, test-results.xml, coverage.xml, coverage_html/**', allowEmptyArchive: true
        }
        failure {
            echo 'Pipeline failed. Inspect reports and logs.'
        }
    }
}
