pipeline {
    agent { label 'docker' }

    stages {
        stage('Checkout Code') {
            steps {
                git 'https://github.com/sailiash242403/flask-app.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("thatavarthi403/flask-app:${BUILD_NUMBER}")
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub') {
                        dockerImage.push()
                    }
                }
            }
        }
    }
}