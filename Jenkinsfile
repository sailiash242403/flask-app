pipeline {
    agent none

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKERHUB_USER = 'thatavarthi403'
        IMAGE_NAME     = 'flask-app'
        DOCKERHUB_PASS = credentials('dockerhub-creds')
        SONARQUBE_ENV  = 'sonarqube-server'
    }

    stages {

        /**************************************************************
         * Stage: Checkout Code
         * Purpose: Pull the latest source code from SCM and stash it.
         **************************************************************/
        stage('Checkout Code') {
            agent { label 'jenkins-build-node' }
            steps {
                checkout scm
                stash name: 'source_code', includes: '**/*'
            }
        }

        /**************************************************************
         * Stage: Pylint Analysis
         * Purpose: Run linting to check Python code quality. 
         *          Uses a virtual environment to avoid system pollution.
         **************************************************************/
        stage('Pylint Analysis') {
            agent { label 'jenkins-build-node' }
            steps {
                unstash 'source_code'

                sh '''
                    set -e

                    python3 -m venv .venv_pylint
                    . .venv_pylint/bin/activate
                    pip install --upgrade pip
                    pip install pylint

                    echo "Running pylint..."

                    pylint --output-format=text $( \
                        find . -name "*.py" | grep -v ".venv_pylint" || true \
                    ) > pylint.log || true
                '''

                recordIssues tools: [pylint(pattern: 'pylint.log')], stable: true
                archiveArtifacts artifacts: 'pylint.log', allowEmptyArchive: true
            }
        }

        /**************************************************************
         * Stage: Unit Tests + Coverage
         * Purpose: Execute pytest, generate coverage reports, publish 
         *          results to Jenkins test reporting plugins.
         **************************************************************/
        stage('Unit Tests + Coverage') {
            agent { label 'jenkins-build-node' }
            steps {
                unstash 'source_code'

                sh '''
                    python3 -m venv .venv_test
                    . .venv_test/bin/activate

                    pip install -r requirements.txt || true
                    pip install pytest pytest-cov

                    pytest --cov=. --cov-report=xml --cov-report=term
                '''

                junit '**/test-results/**/*.xml'
                cobertura coberturaReportFile: 'coverage.xml'
            }
        }

        /**************************************************************
         * Stage: SonarQube Analysis
         * Purpose: Perform static code analysis and code quality checks 
         *          using SonarQube. Requires Jenkins Sonar plugin setup.
         **************************************************************/
        stage('SonarQube Analysis') {
            agent { label 'jenkins-build-node' }
            environment {
                SONAR_HOST_URL = credentials('sonar-host-url')
                SONAR_TOKEN    = credentials('sonar-token')
            }
            steps {
                unstash 'source_code'

                withSonarQubeEnv('sonarqube-server') {
                    sh """
                        . .venv_test/bin/activate
                        sonar-scanner \
                            -Dsonar.projectKey=flask-app \
                            -Dsonar.sources=. \
                            -Dsonar.python.coverage.reportPaths=coverage.xml
                    """
                }
            }
        }

        /**************************************************************
         * Stage: Docker Build & Push
         * Purpose: Build Docker image for the Flask app and push it 
         *          to DockerHub with latest tag.
         **************************************************************/
        stage('Docker Build & Push') {
            agent { label 'jenkins-docker-node' }
            steps {
                unstash 'source_code'

                sh '''
                    echo "$DOCKERHUB_PASS" | docker login -u "$DOCKERHUB_USER" --password-stdin

                    docker build -t ${IMAGE_NAME}:latest .
                    docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
                    docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
                '''
            }
        }

        /**************************************************************
         * Stage: Deploy
         * Purpose: Pull the latest Docker image on the deployment server 
         *          and restart the running container.
         **************************************************************/
        stage('Deploy') {
            agent { label 'jenkins-deploy-node' }
            steps {
                sh '''
                    docker pull ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
                    docker stop ${IMAGE_NAME} || true
                    docker rm ${IMAGE_NAME} || true

                    docker run -d -p 5000:5000 --name ${IMAGE_NAME} ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
                '''
            }
        }
    }

    post {
        /**************************************************************
         * Post: Always
         * Purpose: Archive logs, cleanup workspace after every run.
         **************************************************************/
        always {
            echo "Archiving logs and cleaning workspace..."
            archiveArtifacts artifacts: '**/*.log', allowEmptyArchive: true
            cleanWs()
        }

        /**************************************************************
         * Post: Success
         **************************************************************/
        success {
            echo "Pipeline SUCCESS."
        }

        /**************************************************************
         * Post: Failure
         **************************************************************/
        failure {
            echo "Pipeline FAILED — check logs."
        }
    }
}
