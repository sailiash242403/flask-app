pipeline {
    agent none

    environment {
        DOCKERHUB_USER = 'thatavarthi403'
        IMAGE_NAME = 'flask-app'
        DOCKERHUB_PASS = credentials('dockerhub-creds')
    }

    stages {

        /* ---------------------------------------------------------
              CHECKOUT – ALWAYS ON JENKINS MASTER
           --------------------------------------------------------- */
        stage('Checkout Code') {
            agent { label 'master' }
            steps {
                git branch: 'main',
                    url: 'https://github.com/sailiash242403/flask-app.git'

                /* Stash the code so other agents can use it */
                stash name: 'source_code', includes: '**'
            }
        }


        /* ---------------------------------------------------------
              BUILD & PUSH DOCKER IMAGE – BUILD AGENT
           --------------------------------------------------------- */
        stage('Build & Push Docker Image') {
            agent { label 'build-node' }
            environment {
                BUILD_VERSION = "${env.BUILD_NUMBER}"
            }
            steps {
                unstash 'source_code'

                sh '''
                    echo "Logging in to DockerHub..."
                    docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASS

                    echo "Building image with version: $BUILD_VERSION"
                    docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION .

                    echo "Pushing versioned image..."
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION

                    echo "Tagging and pushing 'latest'..."
                    docker tag $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_VERSION $DOCKERHUB_USER/$IMAGE_NAME:latest
                    docker push $DOCKERHUB_USER/$IMAGE_NAME:latest
                '''

                echo "Docker Image Build & Push completed successfully."
            }
        }


        /* ---------------------------------------------------------
                 DEPLOY – ALWAYS ON DEPLOYMENT AGENT
           --------------------------------------------------------- */
        stage('Deploy to Server') {
            agent { label 'deploy-node' }
            steps {
                sh '''
                    echo "Logging in to DockerHub..."
                    docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASS

                    echo "Pulling the latest image..."
                    docker pull $DOCKERHUB_USER/$IMAGE_NAME:latest

                    echo "Stopping old container (if running)..."
                    docker stop flask-app || true
                    docker rm flask-app || true

                    echo "Starting new container..."
                    docker run -d \
                        --name flask-app \
                        -p 5000:5000 \
                        $DOCKERHUB_USER/$IMAGE_NAME:latest
                '''

                echo "Deployment completed successfully."
            }
        }
    }
}
