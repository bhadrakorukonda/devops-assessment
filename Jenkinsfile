pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    // Tag images per-build: e.g. 0.1.123
    IMAGE_TAG = "0.1.${env.BUILD_NUMBER}"

    // Bind Docker Hub username/password to DOCKERHUB_USR / DOCKERHUB_PSW
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

          # Build a minimal kubeconfig and repoint it to the node-local API (always 8443 inside minikube netns)
          TMPKC=/tmp/kubeconfig.minikube
          kubectl config view --raw --minify --flatten > "$TMPKC"
          CLUSTER_NAME=$(kubectl --kubeconfig "$TMPKC" config view -o jsonpath='{.clusters[0].name}')
          kubectl --kubeconfig "$TMPKC" config set-cluster "$CLUSTER_NAME" --server="https://127.0.0.1:8443" >/dev/null

          echo ">>> Current context on host:"
          kubectl --kubeconfig "$TMPKC" config current-context

          # Use kubectl inside a container that shares the minikube container network namespace
          # so https://127.0.0.1:8443 is reachable.
          K="docker run --rm --user 0 \
               --network container:minikube \
               -e KUBECONFIG=/tmp/config \
               -v $TMPKC:/tmp/config:ro \
               -v $PWD:/workspace -w /workspace \
               bitnami/kubectl:latest kubectl"
          # (Optional) Apply manifests if you have them in k8s/
          if [ -d k8s ]; then
            echo ">>> Applying manifests in k8s/ ..."
            $K -n devops apply -f k8s/ || true
          fi

          echo ">>> Set images to the freshly pushed tags ..."
          $K -n devops set image deploy/frontend frontend=${DOCKERHUB_USR}/devops-frontend:${IMAGE_TAG} --record
          $K -n devops set image deploy/backend  backend=${DOCKERHUB_USR}/devops-backend:${IMAGE_TAG}  --record

          echo ">>> Wait for rollouts ..."
          $K -n devops rollout status deploy/frontend
          $K -n devops rollout status deploy/backend

          echo ">>> Done. Current services:"
          $K -n devops get deploy,svc,ingress -o wide
        '''
      }
    }
  }

  post {
    always {
      // Best-effort docker logout so your token isn’t left around
      sh 'docker logout || true'
    }
  }
}
