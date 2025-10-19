#!/usr/bin/env python3
"""
Script de test pour l'API Enchères du Domaine
Teste l'inscription, la connexion et le scraping
"""

import requests
import json
import time
from typing import Optional, Dict

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_section(title: str):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")


class APITester:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_email = f"test_user_{int(time.time())}@example.com"
        self.user_password = "TestPassword123!"
        self.user_username = f"testuser_{int(time.time())}"
        self.admin_token: Optional[str] = None

    def headers(self, auth: bool = False) -> Dict[str, str]:
        """Get headers for requests"""
        headers = {"Content-Type": "application/json"}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def test_health_check(self) -> bool:
        """Test if the API is running"""
        print_section("TEST 1: Health Check")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print_success("L'API est en ligne et fonctionne")
                return True
            else:
                print_error(f"L'API a retourné le code {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print_error("Impossible de se connecter à l'API")
            print_info("Vérifiez que le backend est démarré avec: docker-compose up -d")
            return False
        except Exception as e:
            print_error(f"Erreur lors du test de santé: {str(e)}")
            return False

    def test_register(self) -> bool:
        """Test user registration"""
        print_section("TEST 2: Inscription d'un nouvel utilisateur")

        user_data = {
            "email": self.user_email,
            "username": self.user_username,
            "full_name": "Test User",
            "password": self.user_password
        }

        print_info(f"Tentative d'inscription avec l'email: {self.user_email}")

        try:
            response = requests.post(
                f"{API_V1}/auth/register",
                json=user_data,
                headers=self.headers(),
                timeout=10
            )

            if response.status_code == 201:
                user = response.json()
                print_success("Inscription réussie!")
                print_info(f"Utilisateur créé: {user.get('username')} (ID: {user.get('id')})")
                return True
            elif response.status_code == 400:
                error = response.json()
                print_error(f"Erreur d'inscription: {error.get('detail', 'Erreur inconnue')}")
                return False
            else:
                print_error(f"Erreur lors de l'inscription (Code: {response.status_code})")
                print_error(f"Réponse: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception lors de l'inscription: {str(e)}")
            return False

    def test_login(self) -> bool:
        """Test user login"""
        print_section("TEST 3: Connexion")

        login_data = {
            "username": self.user_email,  # OAuth2 uses 'username' field
            "password": self.user_password
        }

        print_info(f"Tentative de connexion avec l'email: {self.user_email}")

        try:
            response = requests.post(
                f"{API_V1}/auth/login",
                data=login_data,  # Use form data for OAuth2
                timeout=10
            )

            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get("access_token")
                self.refresh_token = tokens.get("refresh_token")
                print_success("Connexion réussie!")
                print_info(f"Token d'accès reçu (longueur: {len(self.access_token)})")
                return True
            else:
                print_error(f"Erreur lors de la connexion (Code: {response.status_code})")
                print_error(f"Réponse: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception lors de la connexion: {str(e)}")
            return False

    def test_get_user_info(self) -> bool:
        """Test getting current user info"""
        print_section("TEST 4: Récupération des informations utilisateur")

        if not self.access_token:
            print_error("Pas de token d'accès disponible")
            return False

        try:
            response = requests.get(
                f"{API_V1}/auth/me",
                headers=self.headers(auth=True),
                timeout=10
            )

            if response.status_code == 200:
                user = response.json()
                print_success("Informations utilisateur récupérées!")
                print_info(f"Email: {user.get('email')}")
                print_info(f"Username: {user.get('username')}")
                print_info(f"Admin: {user.get('is_admin')}")
                return True
            else:
                print_error(f"Erreur (Code: {response.status_code})")
                print_error(f"Réponse: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception: {str(e)}")
            return False

    def test_get_lots(self) -> bool:
        """Test getting auction lots"""
        print_section("TEST 5: Récupération des lots")

        try:
            response = requests.get(
                f"{API_V1}/lots?page=1&size=10",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print_success(f"Lots récupérés: {data.get('total')} lots au total")
                print_info(f"Page: {data.get('page')}/{data.get('pages')}")
                print_info(f"Lots sur cette page: {len(data.get('items', []))}")

                if data.get('total') == 0:
                    print_warning("Aucun lot trouvé. Lancez le scraping pour importer des lots.")
                else:
                    # Afficher quelques lots
                    for i, lot in enumerate(data.get('items', [])[:3], 1):
                        print_info(f"  Lot {i}: {lot.get('title')} - {lot.get('price')}€")

                return True
            else:
                print_error(f"Erreur (Code: {response.status_code})")
                return False

        except Exception as e:
            print_error(f"Exception: {str(e)}")
            return False

    def test_get_sales(self) -> bool:
        """Test getting sales"""
        print_section("TEST 6: Récupération des ventes")

        try:
            response = requests.get(
                f"{API_V1}/sales?page=1&size=10",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print_success(f"Ventes récupérées: {data.get('total')} ventes au total")

                if data.get('total') == 0:
                    print_warning("Aucune vente trouvée. Lancez le scraping pour importer des ventes.")
                else:
                    for i, sale in enumerate(data.get('items', [])[:5], 1):
                        print_info(f"  Vente {i}: #{sale.get('sale_number')} - {sale.get('title')}")
                        print_info(f"    Total lots: {sale.get('total_lots')}, Scrapé: {sale.get('is_scraped')}")

                return True
            else:
                print_error(f"Erreur (Code: {response.status_code})")
                return False

        except Exception as e:
            print_error(f"Exception: {str(e)}")
            return False

    def test_trigger_scraping(self, sale_number: int = 42) -> bool:
        """Test triggering scraping (requires admin)"""
        print_section(f"TEST 7: Déclenchement du scraping (Vente #{sale_number})")

        if not self.access_token:
            print_warning("Pas de token d'accès. Ce test nécessite un compte admin.")
            return False

        print_warning("Ce test nécessite des privilèges admin")
        print_info(f"Tentative de scraping de la vente #{sale_number}...")

        try:
            response = requests.post(
                f"{API_V1}/admin/scrape?sale_number={sale_number}",
                headers=self.headers(auth=True),
                timeout=120  # Le scraping peut prendre du temps
            )

            if response.status_code == 200:
                result = response.json()
                print_success("Scraping déclenché avec succès!")
                print_info(f"Message: {result.get('message')}")
                print_info(f"Stats: {result.get('stats')}")
                return True
            elif response.status_code == 403:
                print_warning("Accès refusé: privilèges admin requis")
                return False
            else:
                print_error(f"Erreur (Code: {response.status_code})")
                print_error(f"Réponse: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║       TEST DE L'API ENCHÈRES DU DOMAINE                   ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")

        results = []

        # Test 1: Health check
        results.append(("Health Check", self.test_health_check()))

        if not results[-1][1]:
            print_error("\nL'API n'est pas accessible. Arrêt des tests.")
            return

        # Test 2: Register
        results.append(("Inscription", self.test_register()))

        # Test 3: Login
        results.append(("Connexion", self.test_login()))

        # Test 4: Get user info
        if self.access_token:
            results.append(("Info utilisateur", self.test_get_user_info()))

        # Test 5: Get lots
        results.append(("Récupération des lots", self.test_get_lots()))

        # Test 6: Get sales
        results.append(("Récupération des ventes", self.test_get_sales()))

        # Test 7: Trigger scraping (optional, needs admin)
        # results.append(("Scraping", self.test_trigger_scraping()))

        # Summary
        print_section("RÉSUMÉ DES TESTS")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = f"{Colors.GREEN}✓ PASSÉ{Colors.END}" if result else f"{Colors.RED}✗ ÉCHOUÉ{Colors.END}"
            print(f"{test_name:.<40} {status}")

        print(f"\n{Colors.BOLD}Résultat final: {passed}/{total} tests réussis{Colors.END}")

        if passed == total:
            print_success("\n🎉 Tous les tests sont passés avec succès!")
        else:
            print_warning(f"\n⚠️  {total - passed} test(s) ont échoué")


def main():
    """Main function"""
    tester = APITester()
    tester.run_all_tests()

    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Pour déclencher le scraping manuellement:{Colors.END}")
    print(f"{Colors.YELLOW}curl -X POST 'http://localhost:8000/api/v1/admin/scrape?sale_number=42' \\{Colors.END}")
    print(f"{Colors.YELLOW}  -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    main()
