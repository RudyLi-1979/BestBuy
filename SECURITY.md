# Security Guide

## API Key Management

### ✅ Best Practices

This project uses a `.env` file to manage sensitive information (like API Keys):

1. **Use a .env file**
   ```bash
   # .env
   BESTBUY_API_KEY=YOUR_ACTUAL_API_KEY
   ```

2. **.env is added to .gitignore**
   - The `.env` file will not be committed to version control
   - Only `.env.example` will be committed as a template

3. **Gradle reads .env**
   - `app/build.gradle.kts` automatically reads the `.env` file
   - The API Key is injected into `BuildConfig.BESTBUY_API_KEY`

### ❌ What Not to Do

1. **Do not hardcode it in your code**
   ```kotlin
   // ❌ Wrong example
   val apiKey = "YourActualApiKey123456"
   ```

2. **Do not commit .env to version control**
   - Ensure `.gitignore` includes `.env`
   - Check before committing: `git status`

3. **Do not share it in public**
   - Do not paste your API Key in Issues, PRs, or forums
   - Be sure to hide the API Key in screenshots

## Setup Steps

### 1. Create the .env file

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file
# Replace YOUR_API_KEY_HERE with your actual API Key
```

### 2. Verify Settings

When you build the project, Gradle reads `.env` and injects the key into BuildConfig:

```kotlin
// Use in code
val apiKey = BuildConfig.BESTBUY_API_KEY
```

### 3. Team Collaboration

When other developers clone the project:

1. They need to create their own `.env` file
2. Refer to the format in `.env.example`
3. Fill in their own API Key

## .env File Format

### Android App (project root `.env`)
```bash
# BestBuy API Key — injected into BuildConfig.BESTBUY_API_KEY at Gradle build time
BESTBUY_API_KEY=YOUR_BESTBUY_API_KEY
```

### UCP Server (`ucp_server/.env`)
```bash
# Best Buy
BESTBUY_API_KEY=YOUR_BESTBUY_API_KEY

# Gemini AI
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta

# Server
UCP_BASE_URL=https://ucp.rudy.xx.kg   # or http://localhost:58000 for local

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./ucp_bestbuy.db

# Redis (required by rate limiter)
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Development
DEBUG=true
LOG_LEVEL=DEBUG
```

> Copy `ucp_server/.env.example` → `ucp_server/.env` then fill in the real values.

## Frequently Asked Questions

### Q: Where is the .env file?
A: In the project root directory (same level as `build.gradle.kts`)

### Q: How to confirm .env won't be committed?
A: Run `git status`, confirm `.env` is not in the list of files to be committed

### Q: Do team members need my API Key?
A: No. Each developer should use their own API Key

### Q: What if the API Key is leaked?
A: 
1. Immediately go to [BestBuy Developer Portal](https://developer.bestbuy.com/) to revoke the API Key
2. Generate a new API Key
3. Update the `.env` file

## CI/CD Environment

If using CI/CD (such as GitHub Actions), you need to set environment variables in the CI environment:

### GitHub Actions Example

```yaml
# .github/workflows/build.yml
env:
  BESTBUY_API_KEY: ${{ secrets.BESTBUY_API_KEY }}
```

Set `BESTBUY_API_KEY` in GitHub Repository Settings → Secrets.

## Advanced Security Measures

### 1. ProGuard/R8 Obfuscation

During Release build, the API Key will be obfuscated:

```kotlin
// proguard-rules.pro
-keep class com.bestbuy.scanner.BuildConfig { *; }
```

### 2. Proxy Server

A more secure approach is to proxy API requests through your own backend server:

```
Mobile App → Your Backend → BestBuy API
```

This way, the API Key only exists on the backend and won't be exposed in the APK.

### 3. API Key Restrictions

Set API Key restrictions in the BestBuy Developer Portal:
- IP whitelist
- Request rate limiting
- Usage monitoring

## Checklist

Pre-launch checks:

- [ ] ✅ `.env` is in `.gitignore`
- [ ] ✅ No hardcoded API Key
- [ ] ✅ `.env.example` does not contain actual API Key
- [ ] ✅ README explains how to configure `.env`
- [ ] ✅ API Key has usage restrictions set
- [ ] ✅ Regularly rotate API Keys

## Related Links

- [BestBuy API Security Best Practices](https://bestbuyapis.github.io/api-documentation/)
- [Android Security Guide](https://developer.android.com/topic/security/best-practices)
- [OWASP Mobile Security](https://owasp.org/www-project-mobile-security/)

---

**Remember**: Security is an ongoing process, not a one-time task. Regularly review and update security measures.
