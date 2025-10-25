# Port Configuration for RefactAI

## Current Port Assignments

### Backend (Spring Boot)
- **Port:** 9090
- **Base URL:** http://localhost:9090
- **API Context Path:** /api
- **Full API URL:** http://localhost:9090/api

**Configuration File:** `backend/server/src/main/resources/application.yml`
```yaml
server:
  port: 9090
  servlet:
    context-path: /api
```

### Frontend (Next.js)
- **Port:** 4000
- **Base URL:** http://localhost:4000
- **API Proxy:** None (direct API calls to backend)

**Configuration Files:**
- `web/app/package.json` - Dev and start scripts use `-p 4000`
- `web/app/.env.local` - Environment variables for API URL

```json
"scripts": {
  "dev": "next dev -p 4000",
  "start": "next start -p 4000"
}
```

## How to Change Ports

### Change Backend Port

1. Edit `backend/server/src/main/resources/application.yml`:
   ```yaml
   server:
     port: YOUR_NEW_PORT
   ```

2. Update frontend API calls (if hardcoded) or use environment variable

### Change Frontend Port

1. Edit `web/app/package.json`:
   ```json
   "dev": "next dev -p YOUR_NEW_PORT"
   ```

2. Or use environment variable:
   ```bash
   PORT=YOUR_NEW_PORT npm run dev
   ```

### Update API URL in Frontend

1. Edit `web/app/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:YOUR_BACKEND_PORT/api
   ```

2. Or update hardcoded URLs in components:
   - `web/app/app/components/SecurityAnalysisDashboard.tsx`
   - `web/app/app/components/RippleImpactAnalysis.tsx`

## Starting the Application

### Start Backend
```bash
cd /Users/svm648/refactai/backend/server
java -jar target/refactai-server-0.1.0-SNAPSHOT.jar
```
Backend will start on port **9090**

### Start Frontend
```bash
cd /Users/svm648/refactai/web/app
npm run dev
```
Frontend will start on port **4000**

## Access URLs

- **Frontend:** http://localhost:4000
- **Backend API:** http://localhost:9090/api
- **Backend Health:** http://localhost:9090/api/actuator/health (if enabled)

## Security Analysis Endpoints

All security endpoints are now on port **9090**:

- `POST http://localhost:9090/api/security/analyze/{workspaceId}` - Run security analysis
- `POST http://localhost:9090/api/security/assessment/{workspaceId}` - Get full assessment
- `GET http://localhost:9090/api/security/summary/{workspaceId}` - Get security summary
- `GET http://localhost:9090/api/security/compliance/{workspaceId}` - Get compliance report
- `GET http://localhost:9090/api/security/remediation/{workspaceId}` - Get remediation plan

## Port Conflict Resolution

If ports are already in use:

### Find what's using a port
```bash
# macOS/Linux
lsof -i :9090
lsof -i :4000

# Kill the process
kill -9 <PID>
```

### Use different ports temporarily
```bash
# Backend
java -jar target/refactai-server-0.1.0-SNAPSHOT.jar --server.port=9091

# Frontend
PORT=4001 npm run dev
```

## Notes

- All hardcoded `localhost:8080` references have been updated to `localhost:9090`
- Frontend now uses port 4000 instead of 3000 to avoid conflicts
- SimpleSecurityController was removed to avoid duplicate endpoint mappings
- SecurityAnalysisController is the primary security API controller

