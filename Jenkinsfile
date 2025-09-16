pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    // Tag images per-build: e.g. 0.1.42
    IMAGE_TAG = "0.1.${env.BUILD_NUMBER}"

    // Docker Hub username/password -> $DOCKERHUB_USR / $DOCKERHUB_PSW
    DOCKERHUB = credentials('dockerhub-creds')
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
        sh '''
          echo "$DOCKERHUB_PSW" | docker login -u "$DOCKERHUB_USR" --password-stdin
        '''
      }
    }

    stage('Build Frontend Image') {
      steps {
        sh '''
          test -d frontend
          docker build -t ${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG} ./frontend
        '''
      }
    }

    stage('Build Backend Image') {
      steps {
        sh '''
          test -d backend
          docker build -t ${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG} ./backend
        '''
      }
    }

    stage('Push Images') {
      steps {
        sh '''
          docker push ${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG}
          docker push ${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG}
        '''
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh '''
          set -eu

          # 1) Build an embedded kubeconfig from Jenkins' ~/.kube using dockerized kubectl
          TMPKC="/tmp/kubeconfig.minikube"

          echo "[deploy] Flattening kubeconfig from /var/jenkins_home/.kube ..."
          docker run --rm --user 0 \
            --network container:minikube \
            -v /var/jenkins_home/.kube:/root/.kube:ro \
            bitnami/kubectl:latest \
            kubectl config view --raw --minify --flatten > "$TMPKC"

          # 2) Force the apiserver host that works inside the minikube netns
          sed -i -E 's#server: https://[^[:space:]]+#server: https://127.0.0.1:8443#' "$TMPKC"

          # 3) Handy runner that uses the kubeconfig + joins the minikube network namespace
          K='docker run --rm --user 0 --network container:minikube \
               -e KUBECONFIG=/tmp/config \
               -v '"$TMPKC"':'/tmp/config:ro \
               -v '"$PWD"':'/workspace -w /workspace \
               bitnami/kubectl:latest kubectl'

          echo "[deploy] Sanity check..."
          $K config current-context || true
          $K get ns

          echo "[deploy] Applying manifests (namespace devops)..."
          $K -n devops apply -f k8s/

          echo "[deploy] Updating images with this build tag..."
          $K -n devops set image deploy/frontend frontend=${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG} || true
          $K -n devops set image deploy/backend  backend=${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG}  || true

          echo "[deploy] Waiting for rollouts..."
          $K -n devops rollout status deploy/frontend || true
          $K -n devops rollout status deploy/backend  || true

          echo "[deploy] Done."
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
