#!/bin/bash

# Détection du système d'exploitation
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    IS_WINDOWS=true
    echo "Système Windows détecté, adaptation du script..."
else
    IS_WINDOWS=false
fi

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Obtenir le chemin absolu du répertoire courant
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== Démarrage de l'environnement de développement Immosphere ===${NC}"

# Vérifier que tous les répertoires nécessaires existent
if [ ! -d "$SCRIPT_DIR/frontend" ]; then
    echo -e "${RED}Erreur: Le répertoire frontend n'existe pas${NC}"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/backend/gateway" ]; then
    echo -e "${RED}Erreur: Le répertoire backend/gateway n'existe pas${NC}"
    exit 1
fi

# Vérifier admin-service
if [ ! -d "$SCRIPT_DIR/backend/admin-service" ]; then
    echo -e "${RED}Erreur: Le répertoire backend/admin-service n'existe pas${NC}"
    exit 1
fi

# Vérifier user-service
if [ ! -d "$SCRIPT_DIR/backend/user-service" ]; then
    echo -e "${RED}Erreur: Le répertoire backend/user-service n'existe pas${NC}"
    exit 1
fi

# Vérifier scan-service
if [ ! -d "$SCRIPT_DIR/backend/scan-service" ]; then
    echo -e "${RED}Erreur: Le répertoire backend/scan-service n'existe pas${NC}"
    exit 1
fi

# Vérifier pdf-service
if [ ! -d "$SCRIPT_DIR/backend/pdf-service" ]; then
    echo -e "${RED}Erreur: Le répertoire backend/pdf-service n'existe pas${NC}"
    exit 1
fi

# Créer un répertoire pour les logs
mkdir -p "$SCRIPT_DIR/logs"

# Charger le fichier .env tôt pour que Postgres et les services utilisent les mêmes valeurs
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${BLUE}Chargement des variables depuis .env...${NC}"
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Sortie Python non bufferisée pour voir les logs en temps réel
export PYTHONUNBUFFERED=1

# Lancer PostgreSQL avec Docker
echo -e "${GREEN}Lancement de PostgreSQL...${NC}"
POSTGRES_RUNNING=$(docker ps -q -f name=^/postgres$ 2>/dev/null)
POSTGRES_EXISTS=$(docker ps -aq -f name=^/postgres$ 2>/dev/null)
if [ -n "$POSTGRES_RUNNING" ]; then
    echo -e "${BLUE}PostgreSQL est déjà en cours d'exécution${NC}"
elif [ -n "$POSTGRES_EXISTS" ]; then
    # Conteneur existant mais arrêté : le redémarrer
    echo -e "${YELLOW}Redémarrage du conteneur PostgreSQL existant...${NC}"
    docker start postgres
    echo -e "${BLUE}PostgreSQL démarré${NC}"
else
        # Pas de conteneur : créer le volume, le réseau et lancer une nouvelle instance
        # Créer le volume s'il n'existe pas
    if ! docker volume inspect pgdata &>/dev/null; then
        echo -e "${YELLOW}Création du volume Docker 'pgdata'...${NC}"
        docker volume create pgdata
    fi

    # Créer un réseau si nécessaire
    if ! docker network inspect app-network &>/dev/null; then
        echo -e "${YELLOW}Création du réseau Docker 'app-network'...${NC}"
        docker network create app-network
    fi

    echo -e "${YELLOW}Démarrage du conteneur PostgreSQL...${NC}"
    docker run -d --name postgres \
        --network app-network \
        -p 5433:5432 \
        -e POSTGRES_DB="${POSTGRES_DB}" \
        -e POSTGRES_USER="${POSTGRES_USER}" \
        -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        -v pgdata:/var/lib/postgresql/data \
        postgis/postgis:17-3.4


    echo -e "${BLUE}PostgreSQL démarré${NC}"
fi

# Secours : si le conteneur postgres existe mais est arrêté, le démarrer (au cas où le bloc ci-dessus ne l'aurait pas fait)
if [ -n "$(docker ps -aq -f name=postgres 2>/dev/null)" ] && [ -z "$(docker ps -q -f name=postgres 2>/dev/null)" ]; then
    echo -e "${YELLOW}Conteneur PostgreSQL arrêté détecté, démarrage...${NC}"
    docker start postgres
    sleep 2
fi

# Attendre que PostgreSQL accepte les connexions (démarrage frais ou conteneur déjà en route)
echo -e "${YELLOW}Vérification que PostgreSQL est prêt...${NC}"
POSTGRES_USER="${POSTGRES_USER:-user}"
POSTGRES_DB="${POSTGRES_DB:-template_db}"
for i in $(seq 1 30); do
    if docker exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>/dev/null; then
        echo -e "${GREEN}PostgreSQL est prêt.${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}PostgreSQL ne répond pas après 30 s. Vérifiez le conteneur : docker logs postgres${NC}"
        exit 1
    fi
    sleep 1
done

# La base template_db est créée automatiquement par PostgreSQL

# Variables d'environnement communes (valeurs par défaut pour le dev local)
export IS_DOCKER=false
export POSTGRES_USER="${POSTGRES_USER:-user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
export POSTGRES_DB="${POSTGRES_DB:-template_db}"
export DATABASE_URL="${DATABASE_URL:-postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5433/${POSTGRES_DB}}"
export ADMIN_DATABASE_URL="${ADMIN_DATABASE_URL:-postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5433/${POSTGRES_DB}}"
export ADMIN_METRICS_API_KEY="${ADMIN_METRICS_API_KEY:-dev-admin-metrics-key}"
# Variables d'environnement frontend
export IS_BETA_TEST="${IS_BETA_TEST:-true}"
export IS_PROD="${IS_PROD:-false}"

# Fonction pour démarrer manuellement les services pour Windows/PowerShell
start_manual_services() {
    echo -e "${YELLOW}Sur Windows, vous devez démarrer manuellement les services:${NC}"
    echo -e "${GREEN}1. Démarrer le service gateway:${NC}"
    echo -e "   Ouvrez un nouveau terminal et exécutez:"
    echo -e "   cd $SCRIPT_DIR/backend/gateway && venv\\Scripts\\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

    echo -e "${GREEN}2. Démarrer le service admin-service:${NC}"
    echo -e "   Ouvrez un nouveau terminal et exécutez:"
    echo -e "   cd $SCRIPT_DIR/backend/admin-service && venv\\Scripts\\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload"

    echo -e "${GREEN}3. Démarrer le service user-service:${NC}"
    echo -e "   Ouvrez un nouveau terminal et exécutez:"
    echo -e "   cd $SCRIPT_DIR/backend/user-service && venv\\Scripts\\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload"

    echo -e "${GREEN}4. Démarrer le service scan-service:${NC}"
    echo -e "   Ouvrez un nouveau terminal et exécutez:"
    echo -e "   cd $SCRIPT_DIR/backend/scan-service && venv\\Scripts\\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload"

    echo -e "${GREEN}5. Démarrer le service pdf-service:${NC}"
    echo -e "   Ouvrez un nouveau terminal et exécutez:"
    echo -e "   cd $SCRIPT_DIR/backend/pdf-service && venv\\Scripts\\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8013 --reload"

    echo -e "${GREEN}6. Démarrer le frontend (Next.js):${NC}"
    echo -e "   Ouvrez un nouveau terminal et exécutez:"
    echo -e "   cd $SCRIPT_DIR/frontend && npm run dev"

    echo -e "${YELLOW}Pour arrêter les services, fermez les terminaux ou appuyez sur Ctrl+C dans chacun d'eux${NC}"

    # Obtenir l'adresse IP locale pour Windows
    if $IS_WINDOWS; then
        LOCAL_IP=$(ipconfig | grep -i "IPv4" | head -1 | awk '{print $NF}' | tr -d '\r' || echo "non disponible")
    else
        LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "non disponible")
        if [ "$LOCAL_IP" = "non disponible" ]; then
            LOCAL_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' || echo "non disponible")
        fi
    fi

    # Ouvrir le navigateur automatiquement
    echo -e "${GREEN}Frontend disponible à l'adresse locale: ${BLUE}http://localhost:3000${NC}"
    if [ "$LOCAL_IP" != "non disponible" ]; then
        echo -e "${GREEN}Frontend accessible depuis le réseau WiFi: ${BLUE}http://${LOCAL_IP}:3000${NC}"
    else
        echo -e "${YELLOW}Impossible de détecter l'adresse IP locale. Utilisez 'ipconfig' (Windows) ou 'ip addr' (Linux) pour la trouver manuellement.${NC}"
    fi

    if $IS_WINDOWS; then
        start http://localhost:3000
    else
        xdg-open http://localhost:3000 &> /dev/null || open http://localhost:3000 &> /dev/null || echo "Impossible d'ouvrir automatiquement le navigateur"
    fi
}

# Fonction pour lancer un service en arrière-plan
launch_service() {
    local service_name=$1
    local command=$2
    local service_dir=$3
    local log_file="$SCRIPT_DIR/logs/${service_name}.log"

    echo -e "${GREEN}Lancement de ${service_name}...${NC}"

    if [ ! -d "$service_dir" ]; then
        echo -e "${RED}Erreur: Le répertoire $service_dir n'existe pas${NC}"
        return 1
    fi

    # Créer l'environnement virtuel s'il n'existe pas (pour les services Python)
    if [[ "$service_name" == *"-service" ]] || [[ "$service_name" == "gateway" ]]; then
        # Vérifier si l'environnement virtuel existe et est valide
        if [ ! -d "${service_dir}/venv" ]; then
            # L'environnement virtuel n'existe pas, le créer
            echo -e "${YELLOW}Création de l'environnement virtuel pour ${service_name}...${NC}"
            (cd "$service_dir" && python3.11 -m venv venv)

            # Vérifier que la création s'est bien passée
            if [ ! -f "${service_dir}/venv/bin/activate" ]; then
                echo -e "${RED}Erreur: L'environnement virtuel n'a pas été créé correctement pour ${service_name}${NC}"
                return 1
            fi
        elif [ ! -f "${service_dir}/venv/bin/activate" ]; then
            # L'environnement virtuel existe mais est corrompu, le supprimer et le recréer
            echo -e "${YELLOW}Suppression de l'environnement virtuel corrompu pour ${service_name}...${NC}"
            rm -rf "${service_dir}/venv"

            echo -e "${YELLOW}Création de l'environnement virtuel pour ${service_name}...${NC}"
            (cd "$service_dir" && python3.11 -m venv venv)

            # Vérifier que la création s'est bien passée
            if [ ! -f "${service_dir}/venv/bin/activate" ]; then
                echo -e "${RED}Erreur: L'environnement virtuel n'a pas été créé correctement pour ${service_name}${NC}"
                return 1
            fi
        else
            echo -e "${BLUE}Environnement virtuel existant trouvé pour ${service_name}${NC}"
        fi

        # Installer/mettre à jour les dépendances (+ package commun partagé)
        echo -e "${YELLOW}Installation/mise à jour des dépendances pour ${service_name}...${NC}"
        if [ -f "${service_dir}/venv/bin/activate" ]; then
            (cd "$service_dir" && . venv/bin/activate && pip install -e ../common && pip install -r requirements.txt && deactivate)
        else
            echo -e "${RED}Erreur: Impossible d'activer l'environnement virtuel pour ${service_name}${NC}"
            return 1
        fi
    fi

    # S'assurer que le fichier de log peut être créé
    touch "$log_file" || {
        echo -e "${RED}Erreur: Impossible de créer le fichier de log $log_file${NC}"
        return 1
    }

    # Changer de répertoire et exécuter la commande
    (cd "$service_dir" && eval "$command" > "$log_file" 2>&1) &
    local pid=$!
    echo -e "${BLUE}${service_name} démarré avec PID ${pid}${NC}"
    sleep 2
}

if $IS_WINDOWS; then
    # Sur Windows, utiliser l'approche manuelle
    start_manual_services
    echo -e "${GREEN}Fin du script pour Windows${NC}"
    exit 0
else
    # Sur Linux/Mac, lancer normalement les services
    # Lancer le service gateway
    launch_service "gateway" ". venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" "$SCRIPT_DIR/backend/gateway"

    # Lancer le service admin-service
    launch_service "admin-service" ". venv/bin/activate && export DATABASE_URL=\"$ADMIN_DATABASE_URL\" ADMIN_METRICS_API_KEY=\"$ADMIN_METRICS_API_KEY\" && uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload" "$SCRIPT_DIR/backend/admin-service"

    # Lancer le service user-service
    launch_service "user-service" ". venv/bin/activate && export DATABASE_URL=\"$DATABASE_URL\" && uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload" "$SCRIPT_DIR/backend/user-service"

    # Lancer le service scan-service (IS_PROD=false pour autoriser localhost/ports libres en dev)
    launch_service "scan-service" ". venv/bin/activate && export DATABASE_URL=\"$DATABASE_URL\" IS_PROD=false PDF_SERVICE_URL=http://localhost:8013 && uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload" "$SCRIPT_DIR/backend/scan-service"

    # Lancer le service pdf-service
    launch_service "pdf-service" ". venv/bin/activate && export DATABASE_URL=\"$DATABASE_URL\" && uvicorn app.main:app --host 0.0.0.0 --port 8013 --reload" "$SCRIPT_DIR/backend/pdf-service"

    # Lancer le frontend (Next.js)
    echo -e "${YELLOW}Démarrage du frontend Next.js (cela peut prendre jusqu'à 2-3 minutes si les packages sont déjà installés, sinon 5-15 minutes). Si ça ne marche pas, faire le clean install de npm et relancer le script.${NC}"
    launch_service "frontend" "npm run dev" "$SCRIPT_DIR/frontend"

    # Attendre que le frontend soit disponible (avec timeout plus long et moins de requêtes)
    echo -e "${YELLOW}Attente que le frontend Next.js soit disponible (peut prendre 1-2 minutes pour la première compilation)...${NC}"
    FRONTEND_READY=false
    # Attendre 10 secondes avant de commencer à vérifier (donner le temps à Next.js de démarrer)
    sleep 10
    for i in {1..20}; do
        # Utiliser timeout pour éviter que curl bloque trop longtemps
        if timeout 2 curl -s http://localhost:3000 > /dev/null 2>&1; then
            FRONTEND_READY=true
            echo -e "${GREEN}Frontend Next.js est disponible !${NC}"
            break
        fi
        # Afficher seulement toutes les 3 tentatives pour réduire le spam
        if [ $((i % 3)) -eq 0 ]; then
            echo -e "${YELLOW}Attente du démarrage du frontend Next.js (tentative $i/20, ~$((i * 10)) secondes écoulées)...${NC}"
            echo -e "${BLUE}Vérifiez les logs si cela prend trop de temps: tail -f logs/frontend.log${NC}"
        fi
        # Augmenter l'intervalle à 10 secondes pour réduire la charge CPU
        sleep 10
    done

    echo -e "${GREEN}=== Tous les services sont démarrés ===${NC}"
    echo -e "${YELLOW}Les logs sont disponibles dans le répertoire 'logs/'${NC}"
    echo -e "${YELLOW}Pour afficher les logs en temps réel: tail -f logs/[service].log${NC}"
    echo -e "${YELLOW}Pour arrêter tous les services, utilisez Ctrl+C ou 'pkill -f uvicorn; pkill -f npm'${NC}"

    # Obtenir l'adresse IP locale
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "non disponible")
    if [ "$LOCAL_IP" = "non disponible" ]; then
        # Essayer une autre méthode
        LOCAL_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' || echo "non disponible")
    fi

    # Afficher l'URL du frontend
    if [ "$FRONTEND_READY" = true ]; then
        echo -e "${GREEN}Frontend Next.js disponible à l'adresse locale: ${BLUE}http://localhost:3000${NC}"
        if [ "$LOCAL_IP" != "non disponible" ]; then
            echo -e "${GREEN}Frontend accessible depuis le réseau WiFi: ${BLUE}http://${LOCAL_IP}:3000${NC}"
        else
            echo -e "${YELLOW}Impossible de détecter l'adresse IP locale. Utilisez 'ip addr' ou 'ifconfig' pour la trouver manuellement.${NC}"
        fi
    else
        echo -e "${RED}Le frontend Next.js n'a pas démarré correctement. Vérifiez les logs: ${NC}logs/frontend.log"
        echo -e "${YELLOW}Vous pouvez essayer de le démarrer manuellement:${NC}"
        echo -e "${YELLOW}cd frontend && npm install && npm run dev${NC}"
    fi

    # Attendre que l'utilisateur appuie sur Ctrl+C
    echo -e "${GREEN}Appuyez sur Ctrl+C pour arrêter tous les services${NC}"

    # Amélioration de la fonction d'arrêt pour vérifier si les conteneurs existent
    function stop_services() {
        echo -e "${YELLOW}Arrêt des services...${NC}"

        # Arrêter les processus backend et frontend
        pkill -f uvicorn 2>/dev/null || true
        pkill -f npm 2>/dev/null || true

        # Arrêter les conteneurs Docker s'ils existent
        if docker ps -q -f name=postgres &>/dev/null; then
            docker stop postgres
        fi

        echo -e "${GREEN}Services arrêtés${NC}"
        exit 0
    }

    # Intercepter Ctrl+C pour arrêter proprement les services
    trap stop_services INT

    while true; do sleep 1; done
fi
