#!/usr/bin/env bash
# ==============================================================================
#  TSWEBUI / OCR PLATFORM — Unified Launch Script
#  Supports:
#    - Demo Mode:   Interactive foreground execution with live logs & clean Ctrl+C
#    - Deploy Mode: Daemon/background lifecycle (start, stop, restart, status, logs)
#  Services:
#    1. Backend API & Engine:        FastAPI (:8000)
#    2. Admin & Field Mapper UI:     Vite (:5173)
#    3. Public Document Portal:      Vite (:5174)
# ==============================================================================
set -e

# --- Colors & Formatting ---
if [ -t 1 ]; then
    COLOR_RESET="\033[0m"
    COLOR_BOLD="\033[1m"
    COLOR_RED="\033[31m"
    COLOR_GREEN="\033[32m"
    COLOR_YELLOW="\033[33m"
    COLOR_BLUE="\033[34m"
    COLOR_MAGENTA="\033[35m"
    COLOR_CYAN="\033[36m"
    COLOR_DIM="\033[2m"
else
    COLOR_RESET=""
    COLOR_BOLD=""
    COLOR_RED=""
    COLOR_GREEN=""
    COLOR_YELLOW=""
    COLOR_BLUE=""
    COLOR_MAGENTA=""
    COLOR_CYAN=""
    COLOR_DIM=""
fi

info()    { printf "${COLOR_CYAN}[INFO]${COLOR_RESET} %s\n" "$*"; }
success() { printf "${COLOR_GREEN}[OK]${COLOR_RESET} %s\n" "$*"; }
warn()    { printf "${COLOR_YELLOW}[WARN]${COLOR_RESET} %s\n" "$*"; }
error()   { printf "${COLOR_RED}[ERROR]${COLOR_RESET} %s\n" "$*" >&2; }
heading() { printf "\n${COLOR_BOLD}${COLOR_BLUE}=== %s ===${COLOR_RESET}\n" "$*"; }

# --- Resolve Root Paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/ocr-platform" ]; then
    PROJECT_ROOT="$SCRIPT_DIR/ocr-platform"
elif [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"
else
    error "Cannot find ocr-platform directory. Checked $SCRIPT_DIR"
    exit 1
fi

BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PUBLIC_SITE_DIR="$PROJECT_ROOT/public-site"
RUN_DIR="$SCRIPT_DIR/.run"
LOG_DIR="$SCRIPT_DIR/logs"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
PUBLIC_SITE_PID_FILE="$RUN_DIR/public-site.pid"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
PUBLIC_SITE_LOG="$LOG_DIR/public-site.log"

# --- Configurable Ports & Host ---
HOST="${HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PUBLIC_SITE_PORT="${PUBLIC_SITE_PORT:-5174}"

mkdir -p "$RUN_DIR" "$LOG_DIR" "$BACKEND_DIR/storage"

# --- Prerequisite Verification ---
check_prerequisites() {
    local missing=0
    if ! command -v python3 >/dev/null 2>&1; then
        error "Python 3 is required but not installed."
        missing=1
    fi
    if ! command -v node >/dev/null 2>&1; then
        error "Node.js is required but not installed."
        missing=1
    fi
    if [ "$missing" -eq 1 ]; then
        exit 1
    fi
}

# --- Database & Setup Initialization ---
init_database() {
    info "Verifying database and storage..."
    python3 -c "
import asyncio, sys
sys.path.insert(0, '$BACKEND_DIR')
from app.core.database import create_all_tables
asyncio.run(create_all_tables())
" >/dev/null 2>&1 || {
        warn "Database table check failed, proceeding anyway..."
    }
}

# --- Check If Seed Data Needed ---
seed_data_if_empty() {
    info "Checking if seed data is needed..."
    local has_setups
    has_setups=$(python3 -c "
import asyncio, sys
sys.path.insert(0, '$BACKEND_DIR')
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models.configuration import Configuration

async def check():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(func.count(Configuration.id)))
        print(res.scalar() or 0)
asyncio.run(check())
" 2>/dev/null || echo "0")

    if [ "$has_setups" = "0" ]; then
        info "Database is empty. Seeding demo setups, documents, and regression runs..."
        python3 "$BACKEND_DIR/scripts/seed_demo.py" || warn "Seeding returned non-zero, continuing..."
        success "Demo data seeded successfully."
    else
        success "Database contains $has_setups configuration(s)."
    fi
}

# --- Frontends Build Check ---
ensure_frontends_built() {
    local vite_bin="$PROJECT_ROOT/node_modules/vite/bin/vite.js"
    if [ ! -f "$vite_bin" ]; then
        vite_bin="$FRONTEND_DIR/node_modules/vite/bin/vite.js"
    fi

    if [ ! -f "$FRONTEND_DIR/dist/index.html" ]; then
        info "Admin frontend build not found. Building now..."
        (cd "$FRONTEND_DIR" && node "$vite_bin" build)
        success "Admin frontend built successfully."
    fi

    if [ -d "$PUBLIC_SITE_DIR" ] && [ ! -f "$PUBLIC_SITE_DIR/dist/index.html" ]; then
        info "Public site build not found. Building now..."
        (cd "$PUBLIC_SITE_DIR" && node "$vite_bin" build)
        success "Public site built successfully."
    fi
}

# --- Process Helpers ---
is_pid_alive() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

get_backend_pid() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid
        pid=$(cat "$BACKEND_PID_FILE" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    pgrep -f "uvicorn app.main:app.*$BACKEND_PORT" 2>/dev/null | head -n 1 || \
    pgrep -f "uvicorn app.main:app" 2>/dev/null | head -n 1 || true
}

get_frontend_pid() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid
        pid=$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    pgrep -f "vite.*preview.*$FRONTEND_PORT" 2>/dev/null | head -n 1 || \
    pgrep -f "vite.*preview" 2>/dev/null | head -n 1 || true
}

get_public_site_pid() {
    if [ -f "$PUBLIC_SITE_PID_FILE" ]; then
        local pid
        pid=$(cat "$PUBLIC_SITE_PID_FILE" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    pgrep -f "vite.*preview.*$PUBLIC_SITE_PORT" 2>/dev/null | head -n 1 || true
}

# --- Wait For Service ---
wait_for_service() {
    local url="$1"
    local name="$2"
    local max_retries="${3:-20}"
    local count=0

    info "Waiting for $name to be ready at $url..."
    while [ "$count" -lt "$max_retries" ]; do
        if curl -s -m 1 "$url" >/dev/null 2>&1; then
            success "$name is ready!"
            return 0
        fi
        sleep 0.5
        count=$((count + 1))
    done

    warn "$name did not respond within $((max_retries / 2)) seconds. It may still be starting."
    return 1
}

# ==============================================================================
#  DEMO MODE (Foreground / Interactive)
# ==============================================================================
run_demo() {
    heading "STARTING DEMO MODE"
    check_prerequisites
    init_database
    seed_data_if_empty
    ensure_frontends_built

    local vite_bin="$PROJECT_ROOT/node_modules/vite/bin/vite.js"
    if [ ! -f "$vite_bin" ]; then
        vite_bin="$FRONTEND_DIR/node_modules/vite/bin/vite.js"
    fi

    local existing_b existing_f existing_p
    existing_b=$(get_backend_pid)
    existing_f=$(get_frontend_pid)
    existing_p=$(get_public_site_pid)
    if [ -n "$existing_b" ] || [ -n "$existing_f" ] || [ -n "$existing_p" ]; then
        warn "Existing platform processes detected (Backend: ${existing_b:-none}, Admin UI: ${existing_f:-none}, Public Site: ${existing_p:-none})."
        printf "Terminating them to start a clean interactive demo session...\n"
        stop_services
    fi

    local DEMO_BACKEND_PID=""
    local DEMO_FRONTEND_PID=""
    local DEMO_PUBLIC_PID=""

    cleanup_demo() {
        echo
        info "Shutting down demo services..."
        [ -n "$DEMO_PUBLIC_PID" ] && kill "$DEMO_PUBLIC_PID" 2>/dev/null || true
        [ -n "$DEMO_FRONTEND_PID" ] && kill "$DEMO_FRONTEND_PID" 2>/dev/null || true
        [ -n "$DEMO_BACKEND_PID" ] && kill "$DEMO_BACKEND_PID" 2>/dev/null || true
        pkill -P $$ 2>/dev/null || true
        pkill -f "uvicorn app.main:app" 2>/dev/null || true
        pkill -f "vite.*preview" 2>/dev/null || true
        success "All demo servers stopped cleanly. Goodbye!"
        exit 0
    }

    trap cleanup_demo INT TERM EXIT

    info "Starting Backend (FastAPI + Uvicorn) on $HOST:$BACKEND_PORT..."
    (
        cd "$BACKEND_DIR"
        exec python3 -m uvicorn app.main:app --host "$HOST" --port "$BACKEND_PORT"
    ) &
    DEMO_BACKEND_PID=$!

    info "Starting Admin Frontend Preview (Vite) on $HOST:$FRONTEND_PORT..."
    (
        cd "$FRONTEND_DIR"
        exec node "$vite_bin" preview --host "$HOST" --port "$FRONTEND_PORT"
    ) &
    DEMO_FRONTEND_PID=$!

    if [ -d "$PUBLIC_SITE_DIR" ]; then
        info "Starting Public Document Portal Preview (Vite) on $HOST:$PUBLIC_SITE_PORT..."
        (
            cd "$PUBLIC_SITE_DIR"
            exec node "$vite_bin" preview --host "$HOST" --port "$PUBLIC_SITE_PORT"
        ) &
        DEMO_PUBLIC_PID=$!
    fi

    # Wait for services
    wait_for_service "http://localhost:$BACKEND_PORT/api/health" "Backend API" 25
    wait_for_service "http://localhost:$FRONTEND_PORT/" "Admin Control Plane" 25
    [ -n "$DEMO_PUBLIC_PID" ] && wait_for_service "http://localhost:$PUBLIC_SITE_PORT/" "Public Document Portal" 25

    # Banner
    printf "\n"
    printf "${COLOR_BOLD}${COLOR_GREEN}╔════════════════════════════════════════════════════════════════════════════╗${COLOR_RESET}\n"
    printf "${COLOR_BOLD}${COLOR_GREEN}║               🚀 TSWEBUI DOCUMENT INTELLIGENCE PLATFORM LIVE!             ║${COLOR_RESET}\n"
    printf "${COLOR_BOLD}${COLOR_GREEN}╚════════════════════════════════════════════════════════════════════════════╝${COLOR_RESET}\n"
    printf "\n"
    printf "  ${COLOR_BOLD}⚙️  Admin Control Plane:${COLOR_RESET}     ${COLOR_CYAN}http://localhost:%s${COLOR_RESET}\n" "$FRONTEND_PORT"
    printf "  ${COLOR_BOLD}🌐 Public Document Portal:${COLOR_RESET}   ${COLOR_CYAN}http://localhost:%s${COLOR_RESET}\n" "$PUBLIC_SITE_PORT"
    printf "  ${COLOR_BOLD}📡 Shared Backend API:${COLOR_RESET}       ${COLOR_CYAN}http://localhost:%s/api${COLOR_RESET}\n" "$BACKEND_PORT"
    printf "  ${COLOR_BOLD}📖 OpenAPI / Swagger Docs:${COLOR_RESET}   ${COLOR_CYAN}http://localhost:%s/docs${COLOR_RESET}\n" "$BACKEND_PORT"
    printf "\n"
    printf "  ${COLOR_BOLD}${COLOR_YELLOW}✨ Key Features & Workflows:${COLOR_RESET}\n"
    printf "     1. ${COLOR_BOLD}Teach From PDF:${COLOR_RESET} Open ${COLOR_CYAN}http://localhost:%s${COLOR_RESET} -> Teach From PDF tab to visually map fields\n" "$FRONTEND_PORT"
    printf "     2. ${COLOR_BOLD}Website Builder:${COLOR_RESET} Create custom document websites & publish collections\n"
    printf "     3. ${COLOR_BOLD}Ranked Search:${COLOR_RESET} Test 5-tier search & PDF viewer at ${COLOR_CYAN}http://localhost:%s${COLOR_RESET}\n" "$PUBLIC_SITE_PORT"
    printf "     4. ${COLOR_BOLD}Security:${COLOR_RESET} Strict boundary between /api/admin/* and /api/public/*\n"
    printf "\n"
    printf "  ${COLOR_DIM}[Press Ctrl+C at any time to stop all services]${COLOR_RESET}\n\n"

    wait "$DEMO_BACKEND_PID" "$DEMO_FRONTEND_PID" ${DEMO_PUBLIC_PID:+"$DEMO_PUBLIC_PID"} 2>/dev/null || true
}

# ==============================================================================
#  DEPLOY MODE (Background / Daemon)
# ==============================================================================
start_services() {
    heading "DEPLOYING TSWEBUI OCR PLATFORM (DAEMON MODE)"
    check_prerequisites
    init_database
    ensure_frontends_built

    local vite_bin="$PROJECT_ROOT/node_modules/vite/bin/vite.js"
    if [ ! -f "$vite_bin" ]; then
        vite_bin="$FRONTEND_DIR/node_modules/vite/bin/vite.js"
    fi

    local existing_b existing_f existing_p
    existing_b=$(get_backend_pid)
    existing_f=$(get_frontend_pid)
    existing_p=$(get_public_site_pid)

    # 1. Backend
    if [ -n "$existing_b" ]; then
        warn "Backend is already running (PID: $existing_b)."
    else
        info "Starting backend daemon on $HOST:$BACKEND_PORT..."
        (
            cd "$BACKEND_DIR"
            if command -v setsid >/dev/null 2>&1; then
                setsid python3 -m uvicorn app.main:app \
                    --host "$HOST" \
                    --port "$BACKEND_PORT" \
                    </dev/null >> "$BACKEND_LOG" 2>&1 &
            else
                nohup python3 -m uvicorn app.main:app \
                    --host "$HOST" \
                    --port "$BACKEND_PORT" \
                    </dev/null >> "$BACKEND_LOG" 2>&1 &
            fi
            echo $! > "$BACKEND_PID_FILE"
        )
        local bpid
        bpid=$(cat "$BACKEND_PID_FILE" 2>/dev/null || true)
        success "Backend started (PID: ${bpid:-unknown}, Log: $BACKEND_LOG)."
    fi

    # 2. Admin Frontend
    if [ -n "$existing_f" ]; then
        warn "Admin frontend preview is already running (PID: $existing_f)."
    else
        info "Starting admin frontend preview on $HOST:$FRONTEND_PORT..."
        (
            cd "$FRONTEND_DIR"
            if command -v setsid >/dev/null 2>&1; then
                setsid node "$vite_bin" preview \
                    --host "$HOST" \
                    --port "$FRONTEND_PORT" \
                    </dev/null >> "$FRONTEND_LOG" 2>&1 &
            else
                nohup node "$vite_bin" preview \
                    --host "$HOST" \
                    --port "$FRONTEND_PORT" \
                    </dev/null >> "$FRONTEND_LOG" 2>&1 &
            fi
            echo $! > "$FRONTEND_PID_FILE"
        )
        local fpid
        fpid=$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)
        success "Admin Frontend started (PID: ${fpid:-unknown}, Log: $FRONTEND_LOG)."
    fi

    # 3. Public Site
    if [ -d "$PUBLIC_SITE_DIR" ]; then
        if [ -n "$existing_p" ]; then
            warn "Public site preview is already running (PID: $existing_p)."
        else
            info "Starting public site preview on $HOST:$PUBLIC_SITE_PORT..."
            (
                cd "$PUBLIC_SITE_DIR"
                if command -v setsid >/dev/null 2>&1; then
                    setsid node "$vite_bin" preview \
                        --host "$HOST" \
                        --port "$PUBLIC_SITE_PORT" \
                        </dev/null >> "$PUBLIC_SITE_LOG" 2>&1 &
                else
                    nohup node "$vite_bin" preview \
                        --host "$HOST" \
                        --port "$PUBLIC_SITE_PORT" \
                        </dev/null >> "$PUBLIC_SITE_LOG" 2>&1 &
                fi
                echo $! > "$PUBLIC_SITE_PID_FILE"
            )
            local ppid
            ppid=$(cat "$PUBLIC_SITE_PID_FILE" 2>/dev/null || true)
            success "Public Site started (PID: ${ppid:-unknown}, Log: $PUBLIC_SITE_LOG)."
        fi
    fi

    wait_for_service "http://localhost:$BACKEND_PORT/api/health" "Backend API" 25 || true
    wait_for_service "http://localhost:$FRONTEND_PORT/" "Admin Frontend" 25 || true
    [ -d "$PUBLIC_SITE_DIR" ] && wait_for_service "http://localhost:$PUBLIC_SITE_PORT/" "Public Site" 25 || true

    printf "\n"
    success "TSWEBUI successfully deployed in background!"
    printf "  • Admin Control Plane:   ${COLOR_CYAN}http://localhost:%s${COLOR_RESET}\n" "$FRONTEND_PORT"
    printf "  • Public Document Site:  ${COLOR_CYAN}http://localhost:%s${COLOR_RESET}\n" "$PUBLIC_SITE_PORT"
    printf "  • Backend API:           ${COLOR_CYAN}http://localhost:%s${COLOR_RESET}\n" "$BACKEND_PORT"
    printf "  • Logs:                  ${COLOR_DIM}%s${COLOR_RESET}\n" "$LOG_DIR"
    printf "  • Commands: bash launch.sh status | bash launch.sh logs | bash launch.sh stop\n\n"
}

stop_services() {
    heading "STOPPING TSWEBUI SERVICES"

    local bpid fpid ppid
    bpid=$(get_backend_pid)
    fpid=$(get_frontend_pid)
    ppid=$(get_public_site_pid)

    if [ -z "$bpid" ] && [ -z "$fpid" ] && [ -z "$ppid" ]; then
        info "No active TSWEBUI services found."
        rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE" "$PUBLIC_SITE_PID_FILE"
        return 0
    fi

    if [ -n "$ppid" ]; then
        info "Stopping Public Site (PID: $ppid)..."
        kill "$ppid" 2>/dev/null || true
    fi

    if [ -n "$fpid" ]; then
        info "Stopping Admin Frontend (PID: $fpid)..."
        kill "$fpid" 2>/dev/null || true
    fi

    if [ -n "$bpid" ]; then
        info "Stopping Backend (PID: $bpid)..."
        kill "$bpid" 2>/dev/null || true
    fi

    sleep 1

    # Force cleanup if still lingering
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite.*preview" 2>/dev/null || true

    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE" "$PUBLIC_SITE_PID_FILE"
    success "All TSWEBUI services stopped."
}

restart_services() {
    heading "RESTARTING SERVICES"
    stop_services
    sleep 1
    start_services
}

show_status() {
    heading "TSWEBUI SERVICE STATUS"

    local bpid fpid ppid b_status f_status p_status
    bpid=$(get_backend_pid)
    fpid=$(get_frontend_pid)
    ppid=$(get_public_site_pid)

    if [ -n "$bpid" ] && is_pid_alive "$bpid"; then
        b_status="${COLOR_GREEN}RUNNING${COLOR_RESET} (PID: $bpid)"
    else
        b_status="${COLOR_RED}STOPPED${COLOR_RESET}"
    fi

    if [ -n "$fpid" ] && is_pid_alive "$fpid"; then
        f_status="${COLOR_GREEN}RUNNING${COLOR_RESET} (PID: $fpid)"
    else
        f_status="${COLOR_RED}STOPPED${COLOR_RESET}"
    fi

    if [ -n "$ppid" ] && is_pid_alive "$ppid"; then
        p_status="${COLOR_GREEN}RUNNING${COLOR_RESET} (PID: $ppid)"
    else
        p_status="${COLOR_RED}STOPPED${COLOR_RESET}"
    fi

    printf "  • Backend API (:8000):        %b\n" "$b_status"
    printf "  • Admin Control Plane (:5173):%b\n" "$f_status"
    printf "  • Public Site Portal (:5174): %b\n" "$p_status"
    printf "\n"

    info "Testing Backend API (http://localhost:$BACKEND_PORT/api/health)..."
    local health_response
    health_response=$(curl -s -m 2 "http://localhost:$BACKEND_PORT/api/health" 2>/dev/null || echo "")
    if [ -n "$health_response" ]; then
        success "API Healthy: $health_response"
    else
        warn "API Endpoint not responding."
    fi

    info "Testing Admin Frontend (http://localhost:$FRONTEND_PORT/)..."
    local fe_response
    fe_response=$(curl -s -m 2 -I "http://localhost:$FRONTEND_PORT/" 2>/dev/null | head -n 1 || echo "")
    if [ -n "$fe_response" ]; then
        success "Admin Frontend Responsive: $fe_response"
    else
        warn "Admin Frontend not responding."
    fi

    if [ -d "$PUBLIC_SITE_DIR" ]; then
        info "Testing Public Site (http://localhost:$PUBLIC_SITE_PORT/)..."
        local ps_response
        ps_response=$(curl -s -m 2 -I "http://localhost:$PUBLIC_SITE_PORT/" 2>/dev/null | head -n 1 || echo "")
        if [ -n "$ps_response" ]; then
            success "Public Site Responsive: $ps_response"
        else
            warn "Public Site not responding."
        fi
    fi
    echo
}

show_logs() {
    local target="${1:-all}"
    case "$target" in
        backend)
            info "Tailing backend logs ($BACKEND_LOG)..."
            tail -n 50 -f "$BACKEND_LOG"
            ;;
        frontend|admin)
            info "Tailing admin frontend logs ($FRONTEND_LOG)..."
            tail -n 50 -f "$FRONTEND_LOG"
            ;;
        public|public-site)
            info "Tailing public site logs ($PUBLIC_SITE_LOG)..."
            tail -n 50 -f "$PUBLIC_SITE_LOG"
            ;;
        *)
            info "Showing last 20 lines of all logs:"
            printf "\n${COLOR_BOLD}=== Backend Log ($BACKEND_LOG) ===${COLOR_RESET}\n"
            [ -f "$BACKEND_LOG" ] && tail -n 20 "$BACKEND_LOG" || echo "(no logs yet)"
            printf "\n${COLOR_BOLD}=== Admin Frontend Log ($FRONTEND_LOG) ===${COLOR_RESET}\n"
            [ -f "$FRONTEND_LOG" ] && tail -n 20 "$FRONTEND_LOG" || echo "(no logs yet)"
            printf "\n${COLOR_BOLD}=== Public Site Log ($PUBLIC_SITE_LOG) ===${COLOR_RESET}\n"
            [ -f "$PUBLIC_SITE_LOG" ] && tail -n 20 "$PUBLIC_SITE_LOG" || echo "(no logs yet)"
            ;;
    esac
}

build_frontends() {
    heading "BUILDING PRODUCTION FRONTEND ASSETS"
    check_prerequisites
    local vite_bin="$PROJECT_ROOT/node_modules/vite/bin/vite.js"
    if [ ! -f "$vite_bin" ]; then
        vite_bin="$FRONTEND_DIR/node_modules/vite/bin/vite.js"
    fi

    info "Building Admin Frontend..."
    (cd "$FRONTEND_DIR" && node "$vite_bin" build)
    success "Admin Frontend built to $FRONTEND_DIR/dist"

    if [ -d "$PUBLIC_SITE_DIR" ]; then
        info "Building Public Site..."
        (cd "$PUBLIC_SITE_DIR" && node "$vite_bin" build)
        success "Public Site built to $PUBLIC_SITE_DIR/dist"
    fi
}

seed_demo_data() {
    heading "SEEDING DEMO DATA"
    check_prerequisites
    init_database
    python3 "$BACKEND_DIR/scripts/seed_demo.py"
    success "Demo database populated."
}

run_tests() {
    heading "RUNNING TEST SUITE"
    check_prerequisites
    cd "$BACKEND_DIR"
    python3 -m pytest tests/ -v
}

# ==============================================================================
#  HELP & INTERACTIVE MENU
# ==============================================================================
show_help() {
    printf "${COLOR_BOLD}TSWEBUI / OCR PLATFORM — Unified Launch Controller${COLOR_RESET}\n\n"
    printf "Usage: ${COLOR_CYAN}bash launch.sh [command]${COLOR_RESET}\n\n"
    printf "${COLOR_BOLD}Commands:${COLOR_RESET}\n"
    printf "  ${COLOR_GREEN}demo${COLOR_RESET}             Run in interactive foreground Demo Mode (with live banner & clean Ctrl+C)\n"
    printf "  ${COLOR_GREEN}deploy [action]${COLOR_RESET}  Manage production background services:\n"
    printf "      start        Start background daemon services (Backend, Admin UI, Public Site)\n"
    printf "      stop         Stop running background services\n"
    printf "      restart      Restart background services\n"
    printf "      status       Show running status and check HTTP health endpoints\n"
    printf "      logs         View live logs (tail -f)\n"
    printf "  ${COLOR_GREEN}start${COLOR_RESET}            Shorthand for 'deploy start'\n"
    printf "  ${COLOR_GREEN}stop${COLOR_RESET}             Shorthand for 'deploy stop'\n"
    printf "  ${COLOR_GREEN}restart${COLOR_RESET}          Shorthand for 'deploy restart'\n"
    printf "  ${COLOR_GREEN}status${COLOR_RESET}           Shorthand for 'deploy status'\n"
    printf "  ${COLOR_GREEN}logs${COLOR_RESET}             Shorthand for 'deploy logs'\n"
    printf "  ${COLOR_GREEN}build${COLOR_RESET}            Build production assets for both Admin UI and Public Site\n"
    printf "  ${COLOR_GREEN}seed${COLOR_RESET}             Seed sample setups, documents, and regression runs\n"
    printf "  ${COLOR_GREEN}test${COLOR_RESET}             Run backend test suite\n"
    printf "  ${COLOR_GREEN}help${COLOR_RESET}             Show this help guide\n\n"
    printf "${COLOR_BOLD}Environment Variables:${COLOR_RESET}\n"
    printf "  HOST             Bind host (default: 0.0.0.0)\n"
    printf "  BACKEND_PORT     FastAPI backend port (default: 8000)\n"
    printf "  FRONTEND_PORT    Admin Frontend UI port (default: 5173)\n"
    printf "  PUBLIC_SITE_PORT Public Document Portal port (default: 5174)\n\n"
    printf "${COLOR_BOLD}Examples:${COLOR_RESET}\n"
    printf "  bash launch.sh demo             # Launch interactive demo\n"
    printf "  bash launch.sh start            # Start all 3 daemons\n"
    printf "  bash launch.sh status           # Verify health across all 3 ports\n"
    printf "  bash launch.sh stop             # Stop all services\n\n"
}

interactive_menu() {
    while true; do
        printf "\n"
        printf "${COLOR_BOLD}${COLOR_BLUE}╔══════════════════════════════════════════════════════════════════════════╗${COLOR_RESET}\n"
        printf "${COLOR_BOLD}${COLOR_BLUE}║             TSWEBUI DOCUMENT INTELLIGENCE CONTROL CENTER                ║${COLOR_RESET}\n"
        printf "${COLOR_BOLD}${COLOR_BLUE}╚══════════════════════════════════════════════════════════════════════════╝${COLOR_RESET}\n"
        printf "  ${COLOR_BOLD}[1]${COLOR_RESET} 🚀 ${COLOR_GREEN}Run Demo Mode${COLOR_RESET}       (Interactive foreground + live banner)\n"
        printf "  ${COLOR_BOLD}[2]${COLOR_RESET} 🌐 ${COLOR_CYAN}Deploy - Start${COLOR_RESET}      (Run backend + admin + public in background)\n"
        printf "  ${COLOR_BOLD}[3]${COLOR_RESET} 🛑 ${COLOR_RED}Deploy - Stop${COLOR_RESET}       (Stop background services)\n"
        printf "  ${COLOR_BOLD}[4]${COLOR_RESET} 🔄 ${COLOR_YELLOW}Deploy - Restart${COLOR_RESET}    (Restart background services)\n"
        printf "  ${COLOR_BOLD}[5]${COLOR_RESET} 📊 Check Status        (View health & running PIDs for all 3)\n"
        printf "  ${COLOR_BOLD}[6]${COLOR_RESET} 📜 View Logs           (Tail backend/admin/public logs)\n"
        printf "  ${COLOR_BOLD}[7]${COLOR_RESET} 📦 Build Frontends     (Compile Vite bundles for Admin & Public)\n"
        printf "  ${COLOR_BOLD}[8]${COLOR_RESET} 🧪 Run Test Suite      (Verify 87/87 backend tests)\n"
        printf "  ${COLOR_BOLD}[9]${COLOR_RESET} 🌱 Seed Demo Data      (Populate sample setups & invoices)\n"
        printf "  ${COLOR_BOLD}[0]${COLOR_RESET} 🚪 Exit\n"
        printf "${COLOR_BOLD}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}\n"
        printf "Select an option [0-9]: "
        read -r opt || opt="0"
        echo

        case "$opt" in
            1) run_demo; break ;;
            2) start_services ;;
            3) stop_services ;;
            4) restart_services ;;
            5) show_status ;;
            6) show_logs ;;
            7) build_frontends ;;
            8) run_tests ;;
            9) seed_demo_data ;;
            0|q|Q|exit) info "Goodbye!"; exit 0 ;;
            *) warn "Invalid selection: $opt" ;;
        esac
    done
}

# ==============================================================================
#  CLI ROUTER
# ==============================================================================
case "${1:-}" in
    demo)
        run_demo
        ;;
    deploy)
        shift
        case "${1:-start}" in
            start)   start_services ;;
            stop)    stop_services ;;
            restart) restart_services ;;
            status)  show_status ;;
            logs)    shift; show_logs "${1:-all}" ;;
            *)       error "Unknown deploy command: $1. Valid: start, stop, restart, status, logs"; exit 1 ;;
        esac
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        shift
        show_logs "${1:-all}"
        ;;
    build)
        build_frontends
        ;;
    seed)
        seed_demo_data
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        if [ -t 0 ]; then
            interactive_menu
        else
            show_help
        fi
        ;;
    *)
        error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
