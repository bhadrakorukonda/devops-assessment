pipeline {
  agent any
  environment {
    DOCKERHUB_USER = 'bhadrakorukonda'         // <- your Docker Hub username
    FRONTEND_IMAGE = "${DOCKERHUB_USER}/devops-frontend"
    BACKEND_IMAGE  = "${DOCKERHUB_USER}/devops-backend"
    TAG            = "0.1.${env.BUILD_NUMBER}"
  }
  options { timestamps() }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'pwd && ls -la'
      }
    }

    stage('Docker Login') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                          usernameVariable: 'DH_USER',
                                          passwordVariable: 'DH_PASS')]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
          '''
        }
      }
    }

    stage('Build Frontend Image') {
      steps {
        sh '''
          test -d frontend || (echo "missing ./frontend" && exit 1)
          docker build -t ${FRONTEND_IMAGE}:${TAG} ./frontend
        '''
      }
    }

    stage('Build Backend Image') {
      steps {
        sh '''
          test -d backend || (echo "missing ./backend" && exit 1)
          docker build -t ${BACKEND_IMAGE}:${TAG} ./backend
        '''
      }
    }

    stage('Push Images') {
      steps {
        sh '''
          docker push ${FRONTEND_IMAGE}:${TAG}
          docker push ${BACKEND_IMAGE}:${TAG}
        '''
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        // Requires a Jenkins "Secret file" credential with your kubeconfig, id: jenkins-kubeconfig
        withKubeConfig([credentialsId: 'jenkins-kubeconfig']) {
          sh '''
            kubectl -n devops set image deployment/frontend frontend=${FRONTEND_IMAGE}:${TAG} --record=true
            kubectl -n devops set image deployment/backend  backend=${BACKEND_IMAGE}:${TAG}  --record=true
            kubectl -n devops rollout status deploy/frontend
            kubectl -n devops rollout status deploy/backend
          '''
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
    }
  }
}
