import os
import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

class MangaBot:
    def __init__(self):
        self.username = "iruledev"  # Replace with your actual username
        self.password = "1234567890"  # Replace with your actual password
        self.brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"  # Adjust the path if needed
        self.driver_path = "C:/Users/ekved/Downloads/chromedriver-win64/chromedriver.exe"
        
        # Set up the Chrome options to use Brave
        options = webdriver.ChromeOptions()
        options.binary_location = self.brave_path

        # Create a new instance of the Chrome driver with options
        self.driver = webdriver.Chrome(service=Service(self.driver_path), options=options)
        
    def login(self):
        self.driver.get("https://user.manganelo.com/login?l=manganato&re_l=login")
        
        # Wait for the username and password fields
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        
        self.driver.find_element(By.NAME, "username").send_keys(self.username)
        self.driver.find_element(By.NAME, "password").send_keys(self.password)
        
        # Wait for the CAPTCHA image to be fully visible
        captcha_image = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".captchar img"))
        )
        
        # At this point, the CAPTCHA image should be loaded and visible
        print("Please enter the CAPTCHA code visible in the browser.")
        
        # Wait for manual input for the CAPTCHA code
        captcha_code = input("Enter the CAPTCHA code: ")
        
        # Enter the CAPTCHA code in the field
        self.driver.find_element(By.NAME, "captchar").send_keys(captcha_code)
        
        # Click on the login button
        self.driver.find_element(By.ID, "submit_login").click()



    def save_cookies(self):
        cookies = self.driver.get_cookies()
        with open("cookies.pkl", "wb") as file:
            pickle.dump(cookies, file)
        print("Cookies saved successfully!")

    def load_cookies(self):
        self.driver.get("https://manganato.com")  # Open the same domain where cookies were saved
        try:
            with open("cookies.pkl", "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    # Modify the domain to match the current domain if necessary
                    if 'domain' in cookie and cookie['domain'] != "manganato.com":
                        cookie['domain'] = "manganato.com"
                    self.driver.add_cookie(cookie)
            print("Cookies loaded successfully!")
        except FileNotFoundError:
            print("No cookies file found. Proceeding without loading cookies.")

    def save_bookmarks(self, bookmarks):
        with open("bookmarks.pkl", "wb") as file:
            pickle.dump(bookmarks, file)
        print("Bookmarks saved successfully!")

    def load_bookmarks(self):
        with open("bookmarks.pkl", "rb") as file:
            return pickle.load(file)

    def get_current_bookmarks(self):
        """Extracts the current bookmark items and their metadata"""
        bookmarks_elements = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".user-bookmark-item"))
        )
        
        bookmarks = []
        for bookmark in bookmarks_elements:
            bookmark_id = bookmark.get_attribute("class").split()[-1]  # Extract ID from class
            manga_title = bookmark.find_element(By.CSS_SELECTOR, ".bm-title a").text  # Extract the title
            last_updated = bookmark.find_element(By.CLASS_NAME, "chapter-datecreate").text  # Extract the last updated time
            bookmarks.append({
                "id": bookmark_id,
                "title": manga_title,
                "last_updated": last_updated
            })
        return bookmarks

    def run(self):
        # Check if cookies file exists to decide whether to log in
        cookies_loaded = False
        try:
            self.load_cookies()
            cookies_loaded = True
            print("Loaded cookies")
        except FileNotFoundError:
            # If cookies don't exist, proceed to login with CAPTCHA
            pass

        # If cookies are not loaded or don't work, login manually
        if not cookies_loaded:
            print("Cookies not found, proceeding to login.")
            self.login()  # Captcha will be requested here
            self.save_cookies()  # Save cookies after logging in

        # Navigate to the bookmarks page
        self.driver.get("https://manganato.com/bookmark")
        
        if "login" in self.driver.current_url or "captcha" in self.driver.current_url:
            print("Access denied. Logging in again...")
            self.login()  # Captcha will be requested here
            self.save_cookies()  # Save cookies after logging in
            self.driver.get("https://manganato.com/bookmark")  # Retry accessing bookmarks page

        # Initial bookmarks to compare
        previous_bookmarks = []
        # Check if bookmarks file exists
        try:
            previous_bookmarks = self.load_bookmarks()
            print("Loaded existing bookmarks.")
        except FileNotFoundError:
            print("Bookmarks file not found. Collecting current bookmarks.")
            try:
                # Wait for the bookmarks to load
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "user-bookmark-item"))
                )

                # Get the current bookmarks
                current_bookmarks = [bookmark.text for bookmark in self.driver.find_elements(By.CLASS_NAME, "user-bookmark-item")]
                self.save_bookmarks(current_bookmarks)  # Save initial bookmarks
                print("Current bookmarks saved successfully.")
                return  # Exit after saving bookmarks if this is the first run
            except selenium.common.exceptions.TimeoutException:
                print("Failed to load bookmarks within the given time.")
                return

        # Compare new bookmarks with the previous ones
        try:
            # Wait for the bookmarks to load again
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "user-bookmark-item"))
            )

            # Get the current bookmarks
            current_bookmarks = [bookmark.text for bookmark in self.driver.find_elements(By.CLASS_NAME, "user-bookmark-item")]

            # Find new bookmarks by comparing current with previous
            new_bookmarks = [bm for bm in current_bookmarks if bm not in previous_bookmarks]
            
            if new_bookmarks:
                print("New bookmarks detected:")
                for new_bookmark in new_bookmarks:
                    print(new_bookmark)
            else:
                print("No new bookmarks found.")
        except selenium.common.exceptions.TimeoutException:
            print("Failed to load bookmarks within the given time.")



# Usage
manga_bot = MangaBot()
manga_bot.run()
