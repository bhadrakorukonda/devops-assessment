pipeline {
  agent any

  environment {
    REGISTRY   = 'docker.io'
    FE_IMAGE   = 'bhadrakorukonda/devops-frontend'
    BE_IMAGE   = 'bhadrakorukonda/devops-backend'
    KUBECONFIG = '/var/jenkins_home/.kube/config'
  }

  stages {
    stage('Checkout') {
      steps {
        retry(3) {
          timeout(time: 2, unit: 'MINUTES') {
            checkout scm
          }
        }
        sh 'set -eu; pwd; ls -la'
      }
    }

    stage('Docker Login') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKERHUB', passwordVariable: 'DOCKERHUB_PSW')]) {
          sh 'echo "$DOCKERHUB_PSW" | docker login -u "$DOCKERHUB" --password-stdin'
        }
      }
    }

    stage('Build Images') {
      parallel {
        stage('Build Frontend Image') {
          steps {
            sh 'docker build -t $REGISTRY/$FE_IMAGE:${BUILD_NUMBER} -f frontend/Dockerfile frontend'
          }
        }
        stage('Build Backend Image') {
          steps {
            sh 'docker build -t $REGISTRY/$BE_IMAGE:${BUILD_NUMBER} -f backend/Dockerfile backend'
          }
        }
      }
    }

    stage('Push Images') {
      steps {
        sh '''
          set -eu
          docker push $REGISTRY/$FE_IMAGE:${BUILD_NUMBER}
          docker push $REGISTRY/$BE_IMAGE:${BUILD_NUMBER}
        '''
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh '''#!/bin/bash -eu
          kubectl config current-context
          echo "[deploy] kube server: $(awk '/server: /{print $2}' "$KUBECONFIG")"

          # bump image tags in manifests
          sed -i "s|image: .*devops-frontend:.*|image: $REGISTRY/$FE_IMAGE:${BUILD_NUMBER}|" k8s/frontend-deployment.yaml || true
          sed -i "s|image: .*devops-backend:.*|image: $REGISTRY/$BE_IMAGE:${BUILD_NUMBER}|"  k8s/backend-deployment.yaml  || true

          # apply resources
          kubectl apply -f k8s/namespace.yaml
          kubectl -n devops apply -f k8s/pg-secret.yaml -f k8s/pg-pvc.yaml -f k8s/pg-deployment.yaml -f k8s/pg-service.yaml || true
          kubectl -n devops apply -f k8s/backend-deployment.yaml -f k8s/backend-service.yaml || true
          kubectl -n devops apply -f k8s/frontend-deployment.yaml -f k8s/frontend-service.yaml
          kubectl -n devops apply -f k8s/ingress.yaml

          # wait & show status
          kubectl -n devops rollout status deploy/frontend-deployment --timeout=120s || true
          kubectl -n devops get ingress,svc,pod -o wide
        '''
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
    }
  }
}
