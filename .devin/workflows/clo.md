---
description: Cloudflare Dev Mode and Cache Purge
---

# Cloudflare Dev Mode and Cache Purge

This workflow enables Cloudflare Development Mode and performs a full cache purge.

## Steps

1. **Log into Cloudflare Dashboard**
   - Go to https://dash.cloudflare.com
   - Select your domain/site

2. **Enable Development Mode**
   - Navigate to Caching → Configuration
   - Find "Development Mode"
   - Click "Enable"
   - Development Mode bypasses cache for 3 hours (extendable)

3. **Purge Entire Cache**
   - Navigate to Caching → Configuration
   - Scroll to "Purge Everything"
   - Click "Purge Everything"
   - Confirm the purge

4. **Alternative: Purge by URL**
   - Navigate to Caching → Configuration
   - Scroll to "Custom Purge"
   - Enter specific URLs to purge
   - Click "Purge"

5. **Disable Development Mode (when done)**
   - Navigate to Caching → Configuration
   - Find "Development Mode"
   - Click "Disable" when development is complete

## API Method (for automation)

Using Cloudflare API:

```bash
# Set your API token and zone ID
export CF_API_TOKEN="your_api_token"
export CF_ZONE_ID="your_zone_id"

# Enable Development Mode
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/settings/development_mode" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"value":"on"}'

# Purge entire cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'

# Disable Development Mode
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/settings/development_mode" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"value":"off"}'
```

## Notes

- Development Mode automatically expires after 3 hours
- Cache purge may take up to 30 seconds to propagate globally
- Use Development Mode during development/testing to avoid cache issues
- Remember to disable Development Mode when done for production performance

