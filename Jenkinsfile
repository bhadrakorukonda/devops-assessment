pipeline {
  agent any

  options { timestamps() }

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
          set -eu
          pwd
          ls -la
        '''
      }
    }

    stage('Docker Login') {
      steps {
        sh '''
          set -eu
          echo "$DOCKERHUB_PSW" | docker login -u "$DOCKERHUB_USR" --password-stdin
        '''
      }
    }

    stage('Build Frontend Image') {
      steps {
        sh '''
          set -eu
          test -d frontend
          docker build -t ${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG} ./frontend
        '''
      }
    }

    stage('Build Backend Image') {
      steps {
        sh '''
          set -eu
          test -d backend
          docker build -t ${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG} ./backend
        '''
      }
    }

    stage('Push Images') {
      steps {
        sh '''
          set -eu
          docker push ${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG}
          docker push ${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG}
        '''
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh '''
          set -eu

          # 1) Flatten kubeconfig from Jenkins' ~/.kube using dockerized kubectl
          TMPKC="/tmp/kubeconfig.minikube"
          echo "[deploy] Flattening kubeconfig from /var/jenkins_home/.kube ..."
          docker run --rm --user 0 \
            --network container:minikube \
            -v /var/jenkins_home/.kube:/root/.kube:ro \
            bitnami/kubectl:latest \
            config view --raw --minify --flatten > "$TMPKC"

          # 2) Helper to run kubectl inside the minikube netns with the flattened kubeconfig
          K='docker run --rm --user 0 --network container:minikube \
               -e KUBECONFIG=/tmp/config \
               -v '"$TMPKC"':'/tmp/config:ro \
               -v '"$PWD"':'/workspace -w /workspace \
               bitnami/kubectl:latest'

          echo "[deploy] Sanity check..."
          $K config current-context || true
          $K get ns

          echo "[deploy] Ensure namespace 'devops' exists..."
          $K get ns devops >/dev/null 2>&1 || $K create ns devops

          echo "[deploy] Applying manifests (namespace devops)..."
          $K -n devops apply -f k8s/

          echo "[deploy] Updating images to this build tag..."
          $K -n devops set image deploy/frontend frontend=${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG} || true
          $K -n devops set image deploy/backend  backend=${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG}  || true

          echo "[deploy] Waiting for rollouts..."
          $K -n devops rollout status deploy/frontend --timeout=120s || true
          $K -n devops rollout status deploy/backend  --timeout=120s || true

          echo "[deploy] Services:"
          $K -n devops get svc -o wide || true

          echo "[deploy] Done."
        '''
      }
    }
  }

  post {
    always {
      sh '''
        set +e
        docker logout || true
      '''
    }
  }
}

    
