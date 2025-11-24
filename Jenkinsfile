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
            CHECKOUT – ALWAYS ON JENKINS MASTER
        ----------------------------------------------------------*/
        stage('Checkout Code') {
            agent { label 'built-in' }
            steps {
                echo "Checking out source code..."
                git branch: 'main',
                    url: 'https://github.com/sailiash242403/flask-app.git'

                stash name: 'source_code', includes: '**'
                echo "Source code stashed."
            }
        }


        /* ---------------------------------------------------------
            RUN PYTESTS – ALWAYS ON BUILD AGENT
        ----------------------------------------------------------*/
        stage('Run PyTests') {
            agent { label 'jenkins-build-node' }
            steps {
                unstash 'source_code'

                sh '''
                    echo "Checking Python3..."
                    if ! command -v python3 &> /dev/null
                    then
                        echo "Python3 NOT found. Installing..."

                        # Alpine Linux (DIND)
                        if command -v apk &> /dev/null; then
                            apk update
                            apk add --no-cache python3 py3-pip python3-dev
                        fi

                        # Ubuntu / Debian
                        if command -v apt-get &> /dev/null; then
                            apt-get update -y
                            apt-get install -y python3 python3-pip python3-venv
                        fi
                    fi

                    echo "Python version:"
                    python3 --version

                    echo "Creating virtual environment..."
                    python3 -m venv venv
                    . venv/bin/activate

                    echo "Installing dependencies..."
                    pip install --upgrade pip
                    pip install -r requirements.txt || pip install flask pytest

                    echo "Running tests..."
                    pytest -v --junitxml=test-results.xml
                '''

                junit 'test-results.xml'
                echo "Tests completed successfully."
            }
        }


        /* ---------------------------------------------------------
            BUILD & PUSH DOCKER IMAGE
        ----------------------------------------------------------*/
        stage('Build & Push Docker Image') {
            agent { label 'jenkins-build-node' }
            environment {
                BUILD_VERSION = "${env.BUILD_NUMBER}"
            }
            steps {
                unstash 'source_code'

                sh '''
                    echo "Logging into DockerHub..."
                    echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin

                    echo "Building Docker image..."
                    docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION .

                    echo "Pushing versioned image..."
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION

                    echo "Pushing latest tag..."
                    docker tag $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION \
                               $DOCKERHUB_USER/$IMAGE_NAME:latest
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Cleaning up..."
                    docker system prune -af || true
                '''

                echo "Docker image build & push complete."
            }
        }


        /* ---------------------------------------------------------
            DEPLOY – ALWAYS ON DEPLOYMENT AGENT
        ----------------------------------------------------------*/
        stage('Deploy to Server') {
            agent { label 'jenkins-deployment-node' }
            steps {
                sh '''
                    echo "Logging into DockerHub..."
                    echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin

                    echo "Pulling latest image..."
                    docker pull $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Stopping existing container..."
                    docker stop flask-app || true
                    docker rm flask-app || true

                    echo "Starting new container..."
                    docker run -d \
                        --name flask-app \
                        -p 5000:5000 \
                        $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Deployment completed!"
                '''
            }
        }
    }
}
