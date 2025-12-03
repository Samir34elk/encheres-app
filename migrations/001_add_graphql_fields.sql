-- Migration: Add GraphQL API fields to Sale and Lot models
-- Date: 2025-12-03
-- Description: Ajout des nouveaux champs pour supporter l'API GraphQL
--              au lieu du scraping HTML

-- ============================================================
-- 1. MODIFICATIONS SUR LA TABLE `sales`
-- ============================================================

-- Ajout du champ organiser (organisateur de la vente)
ALTER TABLE sales
ADD COLUMN IF NOT EXISTS organiser VARCHAR(255);

-- Mettre une valeur par défaut pour les ventes existantes
UPDATE sales
SET organiser = 'Domaine Public'
WHERE organiser IS NULL;

-- Rendre le champ NOT NULL après avoir mis les valeurs par défaut
ALTER TABLE sales
ALTER COLUMN organiser SET NOT NULL;

-- Ajout du champ type_vente (type de vente)
ALTER TABLE sales
ADD COLUMN IF NOT EXISTS type_vente VARCHAR(50);

-- Ajout du champ categories (catégories JSON)
ALTER TABLE sales
ADD COLUMN IF NOT EXISTS categories JSONB;

-- Ajout du champ image_url (URL de l'image de la vente)
ALTER TABLE sales
ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);

-- Création d'index pour les recherches sur categories
CREATE INDEX IF NOT EXISTS idx_sales_categories
ON sales USING GIN (categories);

-- Commentaires pour documentation
COMMENT ON COLUMN sales.organiser IS 'Organisateur de la vente (ex: CAV Paris)';
COMMENT ON COLUMN sales.type_vente IS 'Type de vente (ex: Enchères, Vente amiable)';
COMMENT ON COLUMN sales.categories IS 'Catégories de la vente (array JSON)';
COMMENT ON COLUMN sales.image_url IS 'URL de l''image de présentation';


-- ============================================================
-- 2. MODIFICATIONS SUR LA TABLE `lots`
-- ============================================================

-- Ajout du champ categories (catégories du lot JSON)
ALTER TABLE lots
ADD COLUMN IF NOT EXISTS categories JSONB;

-- Ajout du champ caracteristiques (caractéristiques détaillées JSON)
ALTER TABLE lots
ADD COLUMN IF NOT EXISTS caracteristiques JSONB;

-- Ajout du champ professionnel (réservé aux professionnels)
ALTER TABLE lots
ADD COLUMN IF NOT EXISTS professionnel BOOLEAN DEFAULT FALSE NOT NULL;

-- Ajout du champ price_reserve (prix de réserve)
ALTER TABLE lots
ADD COLUMN IF NOT EXISTS price_reserve INTEGER;

-- Modification du champ image_url: String → JSONB (pour multiple images)
-- On doit d'abord créer une colonne temporaire, migrer les données, puis remplacer

-- Étape 1: Créer une nouvelle colonne temporaire
ALTER TABLE lots
ADD COLUMN IF NOT EXISTS image_url_new JSONB;

-- Étape 2: Migrer les anciennes URLs String vers JSONB array
-- Si image_url existe et n'est pas vide, on le transforme en array JSON
UPDATE lots
SET image_url_new = jsonb_build_array(image_url)
WHERE image_url IS NOT NULL
  AND image_url != ''
  AND image_url_new IS NULL;

-- Étape 3: Supprimer l'ancienne colonne (ATTENTION: perte de données si pas migrées)
-- Décommenter cette ligne SEULEMENT après avoir vérifié que la migration est OK
-- ALTER TABLE lots DROP COLUMN IF EXISTS image_url;

-- Étape 4: Renommer la nouvelle colonne
-- Décommenter cette ligne SEULEMENT après avoir supprimé l'ancienne
-- ALTER TABLE lots RENAME COLUMN image_url_new TO image_url;

-- Pour l'instant, on garde les deux colonnes pour sécurité
-- Vous pourrez finaliser la migration après vérification

-- Création d'index GIN pour les recherches JSON
CREATE INDEX IF NOT EXISTS idx_lots_categories
ON lots USING GIN (categories);

CREATE INDEX IF NOT EXISTS idx_lots_caracteristiques
ON lots USING GIN (caracteristiques);

CREATE INDEX IF NOT EXISTS idx_lots_image_url_new
ON lots USING GIN (image_url_new);

-- Index pour professionnel (filtrage rapide)
CREATE INDEX IF NOT EXISTS idx_lots_professionnel
ON lots (professionnel);

-- Commentaires pour documentation
COMMENT ON COLUMN lots.categories IS 'Catégories du lot (array JSON)';
COMMENT ON COLUMN lots.caracteristiques IS 'Caractéristiques techniques (object JSON clé-valeur)';
COMMENT ON COLUMN lots.professionnel IS 'Réservé aux professionnels uniquement';
COMMENT ON COLUMN lots.price_reserve IS 'Prix de réserve en euros';
COMMENT ON COLUMN lots.image_url_new IS 'URLs des images (array JSON) - remplacera image_url';


-- ============================================================
-- 3. VÉRIFICATIONS POST-MIGRATION
-- ============================================================

-- Vérifier le nombre de ventes avec le nouveau champ organiser
SELECT COUNT(*) as total_sales,
       COUNT(organiser) as with_organiser,
       COUNT(categories) as with_categories
FROM sales;

-- Vérifier le nombre de lots avec les nouveaux champs
SELECT COUNT(*) as total_lots,
       COUNT(categories) as with_categories,
       COUNT(caracteristiques) as with_caracteristiques,
       COUNT(CASE WHEN professionnel THEN 1 END) as professionnel_only,
       COUNT(image_url_new) as with_new_images
FROM lots;

-- Exemple de requête pour voir la migration des images
SELECT id, lot_number, title,
       image_url as old_image_url,
       image_url_new as new_image_url_json
FROM lots
WHERE image_url IS NOT NULL
LIMIT 5;


-- ============================================================
-- 4. ROLLBACK (si nécessaire)
-- ============================================================

-- Pour annuler cette migration, décommentez et exécutez:

/*
-- Rollback sur sales
ALTER TABLE sales DROP COLUMN IF EXISTS organiser;
ALTER TABLE sales DROP COLUMN IF EXISTS type_vente;
ALTER TABLE sales DROP COLUMN IF EXISTS categories;
ALTER TABLE sales DROP COLUMN IF EXISTS image_url;
DROP INDEX IF EXISTS idx_sales_categories;

-- Rollback sur lots
ALTER TABLE lots DROP COLUMN IF EXISTS categories;
ALTER TABLE lots DROP COLUMN IF EXISTS caracteristiques;
ALTER TABLE lots DROP COLUMN IF EXISTS professionnel;
ALTER TABLE lots DROP COLUMN IF EXISTS price_reserve;
ALTER TABLE lots DROP COLUMN IF EXISTS image_url_new;
DROP INDEX IF EXISTS idx_lots_categories;
DROP INDEX IF EXISTS idx_lots_caracteristiques;
DROP INDEX IF EXISTS idx_lots_image_url_new;
DROP INDEX IF EXISTS idx_lots_professionnel;
*/
