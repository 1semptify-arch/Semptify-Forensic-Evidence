---
description: Quick Cloudflare Dev Mode enable and full cache purge
---

# Cloudflare Dev Mode + Full Cache Purge

Quick workflow to enable Development Mode and purge entire cache.

## Prerequisites

- Cloudflare API Token with Zone:Edit and Zone:Cache-Purge permissions
- Zone ID for your domain

## Quick API Commands

```bash
# Set your credentials
export CF_API_TOKEN="your_api_token"
export CF_ZONE_ID="your_zone_id"

# Enable Dev Mode and Purge Cache (one-liner)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/settings/development_mode" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"value":"on"}' && \
curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

## PowerShell Version

```powershell
# Set your credentials
$env:CF_API_TOKEN = "your_api_token"
$env:CF_ZONE_ID = "your_zone_id"

# Enable Dev Mode
Invoke-RestMethod -Method PATCH -Uri "https://api.cloudflare.com/client/v4/zones/$env:CF_ZONE_ID/settings/development_mode" `
  -Headers @{Authorization = "Bearer $env:CF_API_TOKEN"} `
  -Body '{"value":"on"}' -ContentType "application/json"

# Purge Cache
Invoke-RestMethod -Method POST -Uri "https://api.cloudflare.com/client/v4/zones/$env:CF_ZONE_ID/purge_cache" `
  -Headers @{Authorization = "Bearer $env:CF_API_TOKEN"} `
  -Body '{"purge_everything":true}' -ContentType "application/json"
```

## Manual Dashboard Method

1. Go to https://dash.cloudflare.com
2. Select your zone
3. Caching → Configuration
4. Click "Enable" under Development Mode
5. Click "Purge Everything"
