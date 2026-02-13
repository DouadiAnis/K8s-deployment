cat << 'EOF' > README.md
# ☁️ Projet Technique : Déploiement CloudShop sur Kubernetes (AKS)

## 📝 Contexte et Objectifs
Ce projet a pour but de concevoir, conteneuriser et déployer une application e-commerce "CloudShop" basée sur une architecture microservices. L'environnement cible est **Microsoft Azure** (AKS pour le calcul, ACR pour le registre d'images et Azure Disks pour le stockage).

L'objectif principal est de démontrer une maîtrise avancée de Kubernetes à travers le respect d'un cahier des charges strict :
1. **Haute Disponibilité** (Réplicas, Pod Anti-Affinity, Rolling Updates).
2. **Sécurité & Isolation** (RBAC, Network Policies, TLS, Secrets, Service Accounts).
3. **Persistance & Placement** (Persistent Volumes, Taints & Tolerations, Node Affinity).

---

## 🏗️ Architecture et Choix Techniques

L'application est découpée en 3 tiers : **Frontend (Nginx)**, **Backend (Python/Flask)** et **Base de données (MySQL)**.

* **Infrastructure Azure (AKS & ACR)** : Au lieu d'utiliser des ConfigMaps pour stocker le code (anti-pattern), de véritables images Docker (Frontend et Backend) ont été packagées pour l'architecture cible (`linux/amd64`) et hébergées sur un registre privé Azure (ACR) lié au cluster AKS.
* **Stratégies de Placement (Scheduling)** : 
    * *Base de données* : Isolée sur un nœud dédié (`db-node`) via un système de Taints/Tolerations et NodeSelector.
    * *Backend* : Sécurisé contre les pannes matérielles via une règle de Pod Anti-Affinity forçant les réplicas sur des nœuds physiques différents.
* **Exposition et Routage (Ingress & TLS)** : Utilisation de NGINX Ingress Controller avec un routage basé sur l'hôte (`cloudshop.local`) et le chemin (`/api` pour le backend, `/` pour le frontend). Le trafic est chiffré via un certificat TLS auto-signé.

---

## 📁 Explication détaillée des manifests Kubernetes (YAML)

L'ensemble des ressources est déployé dans le namespace dédié `cloudshop`.

### 🔐 A. Sécurité et Droits (Dossier `/rbac`)
* **`backend-role.yaml`** : Implémente le principe du moindre privilège.
    * Crée les `ServiceAccount` `sa-frontend` et `sa-backend`.
    * Définit un `Role` limitant les droits à la lecture (`get`, `list`, `watch`) des ConfigMaps et Secrets du namespace.
    * Associe ce rôle uniquement au `sa-backend` via un `RoleBinding`.

### 💾 B. Stockage et Configuration (Dossier `/storage`)
* **`mysql-secret.yaml`** : Stocke les identifiants de la base de données de manière sécurisée (Secret Opaque) pour éviter de coder les mots de passe en dur dans les déploiements.
* **`mysql-pvc.yaml`** : Demande dynamiquement un disque dur virtuel (Azure Disk) de `1Gi` (`PersistentVolumeClaim`) pour garantir la persistance des données MySQL en cas de redémarrage du pod.

### 🚀 C. Déploiements Applicatifs (Dossier `/deployments`)
* **`mysql-deployment.yaml`** : 
    * *Stratégie Recreate* : Évite les conflits d'écriture simultanés sur le disque.
    * *Volume subPath* : Contourne le dossier système `lost+found` (présent par défaut sur les disques Azure) qui empêchait l'initialisation de MySQL.
    * *Placement ciblé* : Utilise des `tolerations` pour traverser le Taint du nœud DB, et un `nodeSelector` pour forcer l'exécution sur ce nœud spécifique.
* **`backend-deployment.yaml`** : 
    * *Haute Disponibilité* : 2 réplicas avec stratégie `RollingUpdate` (`maxUnavailable: 1`, `maxSurge: 1`).
    * *Pod Anti-Affinity* : Règle stricte (`requiredDuringSchedulingIgnoredDuringExecution`) forçant Kubernetes à placer les pods sur des hôtes distincts (`topologyKey: "kubernetes.io/hostname"`).
* **`frontend-deployment.yaml`** : 2 réplicas (RollingUpdate) utilisant notre image Nginx (ACR) et le ServiceAccount restreint `sa-frontend`.

### 🛡️ D. Réseau Interne et Zero Trust (Dossiers `/services` & `/network-policies`)
* **`*-service.yaml` (Frontend, Backend, MySQL)** : Créent des points d'entrée DNS internes stables (`ClusterIP`) pour la communication inter-pods.
* **`mysql-policy.yaml`** : Implémente une architecture "Zero Trust" (NetworkPolicy). Bloque tout le trafic entrant vers le port 3306 de la DB, à l'exception exclusive du trafic provenant des pods possédant le label `app: backend`.

### 🌍 E. Exposition Publique (Dossier `/ingress`)
* **`cloudshop-ingress.yaml`** : Configure le NGINX Ingress Controller.
    * *Routage* : Accepte le trafic pour `cloudshop.local`. Route `/api` vers le service backend (port 8080) et `/` vers le frontend (port 80).
    * *Sécurité TLS* : Référence le secret `cloudshop-tls` (certificat auto-signé) et force la bascule de HTTP vers HTTPS via l'annotation `ssl-redirect: "true"`.

---

## 🛠️ Guide de Déploiement Rapide (Reproduction)

### Prérequis
* Cluster Azure AKS opérationnel (avec un pool de nœuds standard et un nœud dédié isolé).
* Azure Container Registry (ACR) attaché au cluster contenant les images applicatives.
* CLI `kubectl` et `helm` installés localement.

### Commandes de déploiement

**1. Namespace & RBAC**
```bash
kubectl create namespace cloudshop
kubectl apply -f rbac/backend-role.yaml
```
### Base de Données (Stockage, Identifiants, Déploiement, Policy)

```bash
kubectl apply -f storage/mysql-secret.yaml
kubectl apply -f storage/mysql-pvc.yaml
kubectl apply -f deployments/mysql-deployment.yaml
kubectl apply -f services/mysql-service.yaml
kubectl apply -f network-policies/mysql-policy.yaml
```

### Microservices (Backend & Frontend)

```Bash
kubectl apply -f deployments/backend-deployment.yaml
kubectl apply -f services/backend-service.yaml
kubectl apply -f deployments/frontend-deployment.yaml
kubectl apply -f services/frontend-service.yaml
```
4. Ingress Controller (via Helm)

```Bash
helm repo add ingress-nginx [https://kubernetes.github.io/ingress-nginx](https://kubernetes.github.io/ingress-nginx)
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-basic --create-namespace
```
5. TLS et Routage

```Bash
# Génération du certificat auto-signé
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=cloudshop.local"
kubectl create secret tls cloudshop-tls --key tls.key --cert tls.crt -n cloudshop

# Application de l'Ingress
kubectl apply -f ingress/cloudshop-ingress.yaml
```