from datetime import datetime
import unittest

from selectolax.parser import HTMLParser

from app.services.sale_discovery import SaleDiscoveryService


def build_tree(html: str):
    return HTMLParser(f"<div>{html}</div>")


class SaleDiscoveryParsingTests(unittest.TestCase):
    def setUp(self):
        self.service = SaleDiscoveryService(base_url="https://encheres-domaine.gouv.fr")

    def test_parse_sale_item_active_sale(self):
        html = """
        <div class="fr-list-product__item">
          <div class="fr-card-product fr-enlarge-link">
            <div class="fr-card-product__body">
              <div class="fr-card-product__content custom-product-content-gallery-item">
                <div class="fr-card-product__content-first">
                  <h3 class="fr-card-product__title fr-h6 fr-mb-1w">
                    <a href="/vente/42">Vente du 20 octobre 2025 par les Enchères du Domaine de Marseille</a>
                  </h3>
                  <p class="fr-card-product__desc fr-text--sm fr-text-500 fr-mb-1w"><span>349 Lots</span></p>
                  <div class="fr-flex fr-flex-wrap fr-flex-align-center fr-gap-2w fr-gap-0@md">
                    <p class="fr-text-active-blue-france fr-text-uppercase fr-text-700 fr-text--sm fr-mb-1w@md">
                      <span aria-hidden="true" class="fr-icon-cursor-line fr-icon--sm"></span>&nbsp;Vente en ligne
                    </p>
                  </div>
                  <ul class="fr-tags-group fr-mt-1w">
                    <li><p class="fr-tag">Véhicules</p></li>
                    <li><p class="fr-tag">High tech</p></li>
                  </ul>
                </div>
                <div class="fr-card-product__content-last">
                  <p class="fr-badge fr-badge--green-emeraude">Vente en cours</p>
                  <ul class="fr-list fr-my-0">
                    <li class="fr-text--sm fr-mb-1v">
                      <span class="fr-text-mention-grey">Clôture le </span>
                      <strong>20/10/2025 à 10h00</strong>
                    </li>
                    <li class="fr-text--sm fr-mb-1v">
                      <span class="fr-text-mention-grey">Organisateur : </span>
                      <strong>MARSEILLE</strong>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        """

        item = build_tree(html).css_first("div.fr-list-product__item")
        summary = self.service._parse_sale_item(item)

        self.assertIsNotNone(summary)
        self.assertEqual(summary.sale_number, 42)
        self.assertEqual(summary.lots_count, 349)
        self.assertEqual(summary.organizer, "MARSEILLE")
        self.assertEqual(summary.sale_type, "Vente en ligne")
        self.assertEqual(summary.tags, ["Véhicules", "High tech"])
        self.assertIsNone(summary.start_date)
        self.assertEqual(summary.end_date, datetime(2025, 10, 20, 10, 0))
        self.assertEqual(summary.status_label, "Vente en cours")

    def test_parse_sale_item_upcoming_sale(self):
        html = """
        <div class="fr-list-product__item">
          <div class="fr-card-product fr-enlarge-link">
            <div class="fr-card-product__body">
              <div class="fr-card-product__content custom-product-content-gallery-item">
                <div class="fr-card-product__content-first">
                  <h3 class="fr-card-product__title fr-h6 fr-mb-1w">
                    <a href="/vente/82">Vente du 24 Octobre 2025 par les Enchères du Domaine de Dijon</a>
                  </h3>
                  <p class="fr-card-product__desc fr-text--sm fr-text-500 fr-mb-1w"><span>1 Lot</span></p>
                  <div class="fr-flex fr-flex-wrap fr-flex-align-center fr-gap-2w fr-gap-0@md">
                    <p class="fr-text-active-blue-france fr-text-uppercase fr-text-700 fr-text--sm fr-mb-1w@md">
                      <span aria-hidden="true" class="fr-icon-cursor-line fr-icon--sm"></span>&nbsp;Vente en ligne
                    </p>
                  </div>
                </div>
                <div class="fr-card-product__content-last">
                  <p class="fr-badge fr-badge--info">Vente à venir</p>
                  <ul class="fr-list fr-my-0">
                    <li class="fr-text--sm fr-mb-1v">
                      <span class="fr-text-mention-grey">Débute le : </span>
                      <strong>20/10/2025 à 10h00</strong>
                    </li>
                    <li class="fr-text--sm fr-mb-1v">
                      <span class="fr-text-mention-grey">Clôture le </span>
                      <strong>24/10/2025 à 10h00</strong>
                    </li>
                    <li class="fr-text--sm fr-mb-1v">
                      <span class="fr-text-mention-grey">Organisateur : </span>
                      <strong>DIJON</strong>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        """

        item = build_tree(html).css_first("div.fr-list-product__item")
        summary = self.service._parse_sale_item(item)

        self.assertIsNotNone(summary)
        self.assertEqual(summary.sale_number, 82)
        self.assertEqual(summary.lots_count, 1)
        self.assertEqual(summary.organizer, "DIJON")
        self.assertEqual(summary.sale_type, "Vente en ligne")
        self.assertEqual(summary.start_date, datetime(2025, 10, 20, 10, 0))
        self.assertEqual(summary.end_date, datetime(2025, 10, 24, 10, 0))
        self.assertEqual(summary.status_label, "Vente à venir")


if __name__ == "__main__":
    unittest.main()
