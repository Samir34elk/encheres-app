# 🔒 Guide de Sécurité

## Mesures de Sécurité Implémentées

### ✅ Authentification & Autorisation

1. **Tokens JWT Sécurisés**
   - Tokens stockés dans httpOnly cookies (protection XSS)
   - Expiration automatique (30 min pour access token, 7 jours pour refresh token)
   - Algorithme HS256 avec SECRET_KEY forte

2. **Hashage des Mots de Passe**
   - Bcrypt avec salt automatique
   - Vérification sécurisée avec timing attack protection

3. **Rate Limiting**
   - 5 requêtes/minute pour endpoints d'authentification
   - 60 requêtes/minute pour autres endpoints
   - Protection contre brute-force

### ✅ Protection des Données

1. **CORS Restreint**
   - Origines whitelistées uniquement
   - Méthodes HTTP limitées
   - Headers spécifiques autorisés

2. **Validation des Données**
   - Pydantic pour validation backend
   - TypeScript pour type safety frontend
   - Sanitization des inputs utilisateur

3. **SQL Injection Protection**
   - SQLAlchemy ORM (paramètres bindés)
   - Pas de requêtes SQL raw

### ✅ Sécurité Réseau

1. **HTTPS Recommandé**
   - Cookies avec flag `secure` en production
   - `samesite=lax` pour protection CSRF

2. **Headers de Sécurité**
   - Implémentés via middleware CORS
   - Cache control sur endpoints sensibles

## Configuration de Production

### Variables d'Environnement Requises

```bash
# CRITIQUE: Générer une clé unique
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Base de données
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# Activer HTTPS en production
SECURE_COOKIES=True
```

### Checklist Avant Déploiement

- [ ] SECRET_KEY unique générée et stockée de manière sécurisée
- [ ] .env JAMAIS commité dans Git
- [ ] HTTPS activé (certificat SSL/TLS)
- [ ] Cookies `secure=True` en production
- [ ] Firewall configuré (ports 80/443 uniquement)
- [ ] Backups automatisés de la base de données
- [ ] Logs de sécurité activés
- [ ] Rate limiting configuré
- [ ] Dépendances à jour (npm audit, pip check)

## Signalement de Vulnérabilités

Si vous découvrez une vulnérabilité de sécurité :

1. **NE PAS** créer une issue publique
2. Envoyer un email à : security@encheres-domaine.fr
3. Inclure :
   - Description de la vulnérabilité
   - Steps to reproduce
   - Impact potentiel
   - Suggestions de correction (optionnel)

Nous nous engageons à répondre sous 48h.

## Audit de Sécurité

### Tests de Sécurité Automatisés

```bash
# Backend
cd backend
pytest tests/test_security.py -v

# Audit dépendances
pip install safety
safety check

# Frontend
cd frontend
npm audit
npm run test -- tests/security
```

### Scan de Vulnérabilités

```bash
# Docker images
docker scan encheres_backend
docker scan encheres_frontend

# Trivy
trivy fs .
```

## Meilleures Pratiques

1. **Gestion des Secrets**
   - Utiliser des gestionnaires de secrets (Vault, AWS Secrets Manager)
   - Rotation régulière des secrets
   - Principe du moindre privilège

2. **Mises à Jour**
   - Dépendances mises à jour mensuellement
   - Patches de sécurité appliqués immédiatement
   - Monitoring des CVEs

3. **Logging**
   - Logs de tentatives de connexion
   - Logs d'erreurs 401/403
   - Rotation des logs

4. **Monitoring**
   - Alertes sur activités suspectes
   - Dashboard de sécurité
   - Analyse des patterns d'attaque

## Références

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [React Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/React_Security_Cheat_Sheet.html)
