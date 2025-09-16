pipeline {
  agent any

  environment {
    DOCKERHUB_USER = 'bhadrakorukonda'        // your Docker Hub user
    VERSION       = "0.1.${env.BUILD_NUMBER}" // auto-bump tag per build
    KUBECONFIG_IN_JENKINS = '/var/jenkins_home/.kube/config' // mounted kubeconfig
  }

  stages {
    stage('Checkout') {
      steps {
        checkout([$class: 'GitSCM',
          userRemoteConfigs: [[
            url: 'https://github.com/bhadrakorukonda/devops-assessment.git',
            credentialsId: 'dockerhub-creds' // ok for private; ignored for public
          ]],
          branches: [[name: '*/master']]
        ])
        sh 'pwd && ls -la'
      }
    }

    stage('Docker Login') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
          '''
        }
      }
    }

    stage('Build Frontend Image') {
      steps {
        sh """
          test -d frontend
          docker build -t ${DOCKERHUB_USER}/devops-frontend:${VERSION} ./frontend
        """
      }
    }

    stage('Build Backend Image') {
      steps {
        sh """
          test -d backend
          docker build -t ${DOCKERHUB_USER}/devops-backend:${VERSION} ./backend
        """
      }
    }

    stage('Push Images') {
      steps {
        sh """
          docker push ${DOCKERHUB_USER}/devops-frontend:${VERSION}
          docker push ${DOCKERHUB_USER}/devops-backend:${VERSION}
        """
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh """
          K='docker run --rm \
              -v ${KUBECONFIG_IN_JENKINS}:/root/.kube/config:ro \
              bitnami/kubectl:latest kubectl'

          # Sanity checks
          \$K config current-context
          \$K -n devops get deploy

          # Update images
          \$K -n devops set image deploy/frontend frontend=${DOCKERHUB_USER}/devops-frontend:${VERSION}
          \$K -n devops set image deploy/backend  backend=${DOCKERHUB_USER}/devops-backend:${VERSION}

          # Wait for rollouts
          \$K -n devops rollout status deploy/frontend --timeout=180s
          \$K -n devops rollout status deploy/backend  --timeout=180s
        """
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
    }
  }
}
