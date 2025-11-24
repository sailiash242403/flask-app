pipeline {
    agent none

    environment {
        DOCKERHUB_USER = 'thatavarthi403'
        IMAGE_NAME = 'flask-app'
        DOCKERHUB_PASS = credentials('dockerhub-creds')
    }

    options {
        timestamps()
    }

    stages {

        /* ---------------------------------------------------------
            CHECKOUT – ALWAYS ON JENKINS MASTER
        ----------------------------------------------------------*/
        stage('Checkout Code') {
            agent { label 'built-in' }
            steps {
                echo "Checking out source code from GitHub..."
                git branch: 'main',
                    url: 'https://github.com/sailiash242403/flask-app.git'

                stash name: 'source_code', includes: '**'
                echo "Source code stashed successfully."
            }
        }


        /* ---------------------------------------------------------
            PYTEST – ALWAYS ON BUILD AGENT
        --------------------------------------------------------- */
        stage('Run PyTests') {
            agent { label 'jenkins-build-node' }
            steps {
                unstash 'source_code'

                sh '''
                    echo "Creating a virtual environment..."
                    python3 -m venv venv
                    . venv/bin/activate

                    echo "Installing dependencies..."
                    pip install --upgrade pip
                    pip install flask pytest

                    echo "Running tests..."
                    pytest -v --junitxml=test-results.xml
                '''

                junit 'test-results.xml'
                echo "PyTests completed successfully."
            }
        }


        /* ---------------------------------------------------------
            BUILD & PUSH DOCKER IMAGE – BUILD AGENT
        --------------------------------------------------------- */
        stage('Build & Push Docker Image') {
            agent { label 'jenkins-build-node' }
            environment {
                BUILD_VERSION = "${env.BUILD_NUMBER}"
            }
            steps {
                unstash 'source_code'

                sh '''
                    echo "Logging in to DockerHub..."
                    echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin

                    echo "Building image: $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION"
                    docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION .

                    echo "Pushing versioned image..."
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION

                    echo "Updating 'latest' tag..."
                    docker tag $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION $DOCKERHUB_USER/$IMAGE_NAME:latest
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Cleaning up local Docker artifacts..."
                    docker image prune -f
                '''

                echo "Docker Image Build & Push completed successfully."
            }
        }


        /* ---------------------------------------------------------
             DEPLOY – ALWAYS ON DEPLOYMENT AGENT
        --------------------------------------------------------- */
        stage('Deploy to Server') {
            agent { label 'jenkins-deployment-node' }
            steps {
                sh '''
                    echo "Logging in to DockerHub..."
                    echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin

                    echo "Pulling the latest image..."
                    docker pull $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Stopping existing container if running..."
                    docker stop flask-app || true
                    docker rm flask-app || true

                    echo "Starting new container..."
                    docker run -d \
                        --name flask-app \
                        -p 5000:5000 \
                        $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Deployment successful!"
                '''
            }
        }
    }
}
