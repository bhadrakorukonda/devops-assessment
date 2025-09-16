pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    skipDefaultCheckout(true)
  }

  environment {
    DOCKERHUB_USER = 'bhadrakorukonda'       // <-- your Docker Hub username
    TAG            = "0.1.${env.BUILD_NUMBER}" // image tag per-build (0.1.X)
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          pwd
          ls -la
        '''
      }
    }

    stage('Docker Login') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'dockerhub-creds',   // <-- make sure this Jenkins credential ID exists
          usernameVariable: 'DH_USER',
          passwordVariable: 'DH_PASS'
        )]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
          '''
        }
      }
    }

    stage('Build Frontend Image') {
      steps {
        sh '''
          test -d frontend
          docker build -t $DOCKERHUB_USER/devops-frontend:$TAG ./frontend
        '''
      }
    }

    stage('Build Backend Image') {
      steps {
        sh '''
          test -d backend
          docker build -t $DOCKERHUB_USER/devops-backend:$TAG ./backend
        '''
      }
    }

    stage('Push Images') {
      steps {
        sh '''
          docker push $DOCKERHUB_USER/devops-frontend:$TAG
          docker push $DOCKERHUB_USER/devops-backend:$TAG
        '''
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh '''
          set -e

          # Use kubectl via container. We mount Jenkins' kubeconfig + workspace.
          K="docker run --rm \
            -v /var/jenkins_home/.kube/config:/root/.kube/config:ro \
            -v $PWD:/workspace -w /workspace \
            --add-host=host.docker.internal:host-gateway \
            bitnami/kubectl:latest"

          # Rewrite API server from 127.0.0.1 to host.docker.internal,
          # so the container can reach your host's minikube.
          docker run --rm \
            -v /var/jenkins_home/.kube/config:/root/.kube/config \
            bash:5 bash -lc "sed -i 's#https://127.0.0.1:#https://host.docker.internal:#' /root/.kube/config && grep server /root/.kube/config"

          # Sanity
          $K version --client
          $K config current-context

          # Apply (idempotent)
          $K apply -f k8s/namespace.yaml
          $K apply -f k8s/postgres.yaml
          $K apply -f k8s/backend.yaml
          $K apply -f k8s/frontend.yaml
          $K apply -f k8s/ingress.yaml

          # Point deployments to the new images we just pushed
          $K -n devops set image deployment/backend  backend=$DOCKERHUB_USER/devops-backend:$TAG
          $K -n devops set image deployment/frontend frontend=$DOCKERHUB_USER/devops-frontend:$TAG

          # Wait for rollouts
          $K rollout status -n devops deployment/backend
          $K rollout status -n devops deployment/frontend
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
