import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MySeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")

        if "CI" not in os.environ and os.path.exists("/opt/google/chrome/chrome"):
            opts.binary_location = "/opt/google/chrome/chrome"

        cls.selenium = WebDriver(options=opts)
        cls.wait = WebDriverWait(cls.selenium, 15)

        # Superusuario para acceder al admin panel
        user = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        user.is_superuser = True
        user.is_staff = True
        user.save()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_crear_grup_i_verificar_en_creacio_usuari(self):
        # 1. Login en el admin panel
        self.selenium.get(f"{self.live_server_url}/admin/login/")

        user_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_field.send_keys("isard")
        self.selenium.find_element(By.NAME, "password").send_keys("pirineus")
        self.selenium.find_element(By.XPATH, "//input[@type='submit']").click()

        self.wait.until(EC.presence_of_element_located((By.ID, "user-tools")))

        # 2. Asegurar existencia del grupo
        group_name = "Auditors"
        Group.objects.get_or_create(name=group_name)

        # 3. Comprobar que el grupo aparece en el listado de grupos
        self.selenium.get(f"{self.live_server_url}/admin/auth/group/")
        group_elem = self.wait.until(
            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{group_name}')]"))
        )
        self.assertIsNotNone(group_elem)

        # 4. Crear usuario y navegar directamente a su pantalla de edición en admin
        test_user = User.objects.create_user("testuser", "test@isardvdi.com", "ContrasenyaSegura123!")
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/{test_user.id}/change/")

        # 5. Comprobar que en la pantalla de edición del usuario aparece el grupo en el select
        opcio_grup = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//select[@id='id_groups_from']//option[contains(text(), '{group_name}')]")
            )
        )
        self.assertIsNotNone(opcio_grup)
