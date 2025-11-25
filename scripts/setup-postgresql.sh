#!/bin/bash
# PostgreSQL Local Development Setup Script
#
# Purpose: Automate PostgreSQL user and database creation
# Usage: ./scripts/setup-postgresql.sh [username] [password] [db_prefix]
# Example: ./scripts/setup-postgresql.sh slea_user change_me_dev_password sleassem

set -e

# Default values
DB_USER="${1:-slea_user}"
DB_PASSWORD="${2:-change_me_dev_password}"
DB_PREFIX="${3:-sleassem}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}PostgreSQL Local Development Setup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Database User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo "  Databases: ${DB_PREFIX}_dev, ${DB_PREFIX}_test, ${DB_PREFIX}_prod"
echo ""

# Check if PostgreSQL is running
echo -e "${YELLOW}[1/4] Checking PostgreSQL service...${NC}"
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${RED}PostgreSQL is not running!${NC}"
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
    sleep 2
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Create database user
echo -e "${YELLOW}[2/4] Creating/updating database user...${NC}"
sudo -u postgres psql << EOF
-- Drop user if exists (optional, comment out to preserve existing user)
-- DROP USER IF EXISTS $DB_USER;

-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;
EOF
echo -e "${GREEN}✓ User '$DB_USER' created/updated${NC}"

# Create databases and set ownership
echo -e "${YELLOW}[3/4] Creating/updating databases...${NC}"
sudo -u postgres psql << EOF
-- Create databases if not exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_PREFIX}_dev') THEN
        CREATE DATABASE ${DB_PREFIX}_dev;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_PREFIX}_test') THEN
        CREATE DATABASE ${DB_PREFIX}_test;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_PREFIX}_prod') THEN
        CREATE DATABASE ${DB_PREFIX}_prod;
    END IF;
END
\$\$;

-- Change ownership to $DB_USER
ALTER DATABASE ${DB_PREFIX}_dev OWNER TO $DB_USER;
ALTER DATABASE ${DB_PREFIX}_test OWNER TO $DB_USER;
ALTER DATABASE ${DB_PREFIX}_prod OWNER TO $DB_USER;
EOF
echo -e "${GREEN}✓ Databases created/updated${NC}"

# Grant privileges
echo -e "${YELLOW}[4/4] Granting privileges...${NC}"
sudo -u postgres psql << EOF
GRANT ALL PRIVILEGES ON DATABASE ${DB_PREFIX}_dev TO $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE ${DB_PREFIX}_test TO $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE ${DB_PREFIX}_prod TO $DB_USER;
EOF
echo -e "${GREEN}✓ Privileges granted${NC}"

# Verification
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Verification${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Databases:"
sudo -u postgres psql -c "\l" | grep "$DB_PREFIX"
echo ""
echo "Testing connection:"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "${DB_PREFIX}_dev" -h localhost -c "SELECT version();" 2>/dev/null && \
    echo -e "${GREEN}✓ Connection test successful!${NC}" || \
    echo -e "${RED}✗ Connection test failed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  Local development (WSL):"
echo "    export PGPASSWORD='$DB_PASSWORD'"
echo "    psql -U $DB_USER -d ${DB_PREFIX}_dev -h localhost"
echo ""
echo "  Or use environment variable (.env):"
echo "    DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost:5432/${DB_PREFIX}_dev"
echo ""
