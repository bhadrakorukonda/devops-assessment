pipeline {
  agent any

  options { 
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '25'))
  }

  environment {
    // Per-build tag: e.g. 0.1.12
    IMAGE_TAG = "0.1.${env.BUILD_NUMBER}"
    // Docker Hub creds -> $DOCKERHUB_USR / $DOCKERHUB_PSW
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

          # --- 1) Find running Minikube container (Docker driver) ---
          MINIKUBE_C=$(docker ps --filter "name=minikube" --format "{{.Names}}" | head -n1 || true)
          if [ -z "$MINIKUBE_C" ]; then
            echo "[deploy] ERROR: Could not find a running Minikube container."
            echo "         Start it with:  minikube start --driver=docker"
            exit 1
          fi
          echo "[deploy] Using Minikube container: $MINIKUBE_C"

          # --- 2) Copy kubeconfig out of Minikube container ---
          TMPKC="/tmp/kubeconfig.minikube"
          docker cp "${MINIKUBE_C}:/var/lib/minikube/kubeconfig" "$TMPKC"
          chmod 600 "$TMPKC"
          echo "[deploy] Copied kubeconfig -> $TMPKC"

          # --- 3) Helper to run kubectl inside Minikube's netns with our kubeconfig ---
          K='docker run --rm --user 0 --network container:'"$MINIKUBE_C"' \
               -e KUBECONFIG=/tmp/config \
               -v '"$TMPKC"':'/tmp/config:ro \
               -v '"$PWD"':'/workspace -w /workspace \
               bitnami/kubectl:latest'

          echo "[deploy] Context:"
          $K config current-context || true

          echo "[deploy] Ensure namespace 'devops' exists..."
          $K get ns devops >/dev/null 2>&1 || $K create ns devops

          echo "[deploy] Apply manifests (namespace devops)..."
          $K -n devops apply -f k8s/

          echo "[deploy] Set images to this build tag..."
          $K -n devops set image deploy/frontend frontend=${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG} || true
          $K -n devops set image deploy/backend  backend=${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG}  || true

          echo "[deploy] Wait for rollouts..."
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
