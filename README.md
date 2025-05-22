
# Hybrid Python-Legacy Website Architecture

## System Overview

This project is a hybrid website system powered by a Python backend that serves both new and legacy content. All requests are routed through **HAProxy**, which determines whether to forward to the new Python backend or preserve access to legacy functionality.

### Request Handling Flow

- **HAProxy**
  - Routes `/v2/*` requests → Python backend
  - Routes any `.php`, `/`, or no-extension (non-static) → `/v1/*` → Python backend
  - Routes static assets (`.jpg`, `.js`, `.css`, etc.) directly to the legacy site

- **Python Backend**
  - Handles `/v2/*` as new functionality
  - Handles `/v1/*` by stripping `v1/`, fetching the old page, wrapping it in the new template, and serving it
  - Content from the legacy site uses a "BARE" template when fetched from the new server. This allows templating in a single location.
  - Manages sessions and logins:
    - Creates a 30-day Python session and cookie
    - Logs into the legacy site and stores PHP session ID
    - Re-authenticates if needed using encrypted credentials in the cookie

## Architecture Diagram


```mermaid
flowchart TD
    %% Main request flow
    A1[Incoming Request] --> HAProxy
    
    subgraph HAProxy["HAProxy Load Balancer"]
        direction LR
        H1{Path Check} 
        H1 -->|"/v2/*"| H2[To Python]
        H1 -->|"php or no-ext"| H3[Rewrite to /v1/* and to Python]
        H1 -->|"Static (img, js, css)"| H4[Direct to Legacy]
    end
    
    HAProxy --> Python_Backend
    HAProxy --> Legacy_System
    
    subgraph Python_Backend["Python Backend (New System)"]
        direction TB
        %% New content path
        P1[Process v2 requests] --> P2[Serve new content]
        
        %% Legacy content path
        P3[Process v1 requests] --> P4[Strip v1 prefix]
        P4 --> P5[Fetch from Legacy]
        P5 --> P6[Wrap in template]
        P6 --> P7[Serve final content]
        
        %% Session management
        P8[Session Manager] --> P9[Create 30d session]
        P9 --> P10[Auth with Legacy]
        P10 --> P11[Store PHPSESSID]
    end
    
    subgraph Legacy_System["Legacy PHP Server"]
        direction TB
        L1[Static Content Handler] --> L2[Serve images/JS/CSS]
        L3[Content Provider] --> L4[Generate bare page content]
        L5[Auth System] --> L6[Process login & return PHPSESSID]
    end
    
    %% Connection lines between systems
    Python_Backend -- "Request bare content" --> Legacy_System
    Legacy_System -- "Return bare content" --> Python_Backend
    Python_Backend -- "Auth request" --> Legacy_System
    Legacy_System -- "PHPSESSID" --> Python_Backend
    
    %% Flow mapping
    H2 -.-> P1
    H3 -.-> P3
    H4 -.-> L1
    P5 -.-> L3
    P10 -.-> L5
```


## Setting up the DB
```
sudo dnf install postgres-server 
sudo dnf install -y postgresql16-contrib

postgresql-setup --initdb
systemctl enable postgresql.service
systemctl start postgresql.service
chmod +x ./init/.db.sh
./init/db.sh

sudo -iu postgres psql -d virtual_reports -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

  ```

## open the firewall up
```
# 1. Add the postgresql service (or explicit port) permanently
sudo firewall-cmd --zone=public --add-service=postgresql --permanent
# (fallback if service isn’t defined)
sudo firewall-cmd --zone=public --add-port=5432/tcp --permanent

# 2. Reload firewalld to apply
sudo firewall-cmd --reload

# 3. Verify the rule is in place
sudo firewall-cmd --zone=public --list-services
sudo firewall-cmd --zone=public --list-ports
```


vi /var/lib/pgsql/data/postgresql.conf 
listen_addresses = '*'


vi /var/lib/pgsql/data/pg_hba.conf
host    virtual_reports    vr_web_user    0.0.0.0/0    md5

sudo dnf install postgresql-contrib