import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
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

        # Usar ruta local si no estamos en CI
        if "CI" not in os.environ and os.path.exists("/opt/google/chrome/chrome"):
            opts.binary_location = "/opt/google/chrome/chrome"

        cls.selenium = WebDriver(options=opts)
        cls.wait = WebDriverWait(cls.selenium, 20)

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
        submit_btn = self.selenium.find_element(By.XPATH, "//input[@type='submit']")
        self.selenium.execute_script("arguments[0].click();", submit_btn)

        # Esperar a que cargue el panel principal
        self.wait.until(EC.presence_of_element_located((By.ID, "user-tools")))

        # 2. Navegar a crear grupo
        self.selenium.get(f"{self.live_server_url}/admin/auth/group/add/")

        group_input = self.wait.until(EC.presence_of_element_located((By.NAME, "name")))
        group_name = "Auditors"
        group_input.send_keys(group_name)

        save_btn = self.wait.until(EC.element_to_be_clickable((By.NAME, "_save")))
        self.selenium.execute_script("arguments[0].click();", save_btn)

        # Esperar mensaje de confirmación de Django Admin
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.success, ul.messagelist")))

        # 3. Comprobar que el grupo aparece en la tabla
        group_link = self.wait.until(
            EC.presence_of_element_located((By.XPATH, f"//*[text()='{group_name}']"))
        )
        self.assertIsNotNone(group_link)

        # 4. Navegar a añadir usuario
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/add/")

        user_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_input.send_keys("testuser")
        self.selenium.find_element(By.NAME, "password1").send_keys("ContrasenyaSegura123!")
        self.selenium.find_element(By.NAME, "password2").send_keys("ContrasenyaSegura123!")

        save_user_btn = self.wait.until(EC.element_to_be_clickable((By.NAME, "_save")))
        self.selenium.execute_script("arguments[0].click();", save_user_btn)

        # 5. Comprobar que en la pantalla de edición del usuario aparece el grupo entre las opciones
        opcio_grup = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//select[@id='id_groups_from']/option[text()='{group_name}']")
            )
        )
        self.assertIsNotNone(opcio_grup)
