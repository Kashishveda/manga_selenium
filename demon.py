from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os
import requests

class MangaTracker:
    def __init__(self, mangasite_URL, sitename, debug=False):
        self.webpage_url = mangasite_URL  # Replace with actual homepage URL
        self.sitename = sitename # name of the site
        self.brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
        self.driver_path = "C:/Users/ekved/Downloads/chromedriver-win64/chromedriver.exe"
        options = webdriver.ChromeOptions()
        
        # Use Brave binary path only when running locally
        if os.getenv("GITHUB_ACTIONS") is None:  # This checks if you're running locally
            options.binary_location = self.brave_path  # Local binary path for Brave
            
        # Headless options for GitHub Actions or local headless run
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')  # Bypass OS security model
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

        # Driver setup: Local vs GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):  # Use the GitHub path for chromedriver
            self.driver = webdriver.Chrome(service=Service("./chromedriver"), options=options)
        else:  # Local system chromedriver path
            self.driver = webdriver.Chrome(service=Service(self.driver_path), options=options)
            
        self.chapter_data_file = "chapter_data.pkl"
        self.chapter_data = self.load_chapter_data()
        self.debug = debug  # Store debug state
        
        # Telegram bot configuration
        # Using environment variables for sensitive information
        # uncomment if using GitHub
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")  # This fetches the secret value
        self.chat_id = os.getenv("CHAT_ID")                # This fetches the chat ID

    def load_chapter_data(self):
        if os.path.exists(self.chapter_data_file):
            with open(self.chapter_data_file, "rb") as file:
                return pickle.load(file)
        else:
            return {}

    def save_chapter_data(self):
        with open(self.chapter_data_file, "wb") as file:
            pickle.dump(self.chapter_data, file)
            
    def log(self, message):  # Custom logging method
        if self.debug:
            print(message)
            
    def send_telegram_message(self, message):
        """Send a message to the Telegram bot."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        requests.post(url, json=payload) # Optional: To check the response
            
    def get_latest_chapter(self, manga_name):
        # not required because we dont want to load this everytime
        # self.driver.get(self.webpage_url)
        
        # Debug: Check if page loads correctly
        self.log("Page Loaded. URL: " + self.webpage_url)
        
        try:
            # Wait for page to fully load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            self.log(f"Searching for manga: {manga_name}")
            
            # Search for manga name in the page
            try:
                manga_element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[@title=\"{manga_name}\"]"))
                )
            except Exception as e:
                self.log(f"Manga '{manga_name}' not found.")
                return  # Skip to the next manga
            
            self.log(f"Manga found: {manga_name}")

            # Get the latest chapter info
            if self.sitename == "manganato":
                # Logic for manganato.com
                latest_chapter_element = manga_element.find_element(By.XPATH, ".//following::p[@class='a-h item-chapter'][1]/a")
                latest_chapter_text = latest_chapter_element.get_attribute('title')
            elif self.sitename == "demonmanga":
                # Logic for ciorti.online (demonmanga)
                latest_chapter_element = manga_element.find_element(By.XPATH, ".//following::div[@class='flex flex-row chap-date justify-space-between']/div[1]/a")
                latest_chapter_text = latest_chapter_element.text
                #latest_chapter_element = manga_element.find_element(By.XPATH, ".//following-sibling::div[contains(@class, 'chap-date')]/div[1]/a")
                #latest_chapter_text = latest_chapter_element.text
            else:
                self.log(f"Sitename '{self.sitename}' is not recognized.")
                return  # Skip to the next manga

            self.log(f"Latest Chapter for {manga_name}: {latest_chapter_text}")
            
            # Extract chapter number (assuming format like "Chapter 6: ...")
            latest_chapter_number = latest_chapter_text.split("Chapter ")[1].split(":")[0].strip()
            self.compare_chapter(manga_name, latest_chapter_number)
            
        except Exception as e:
            # Skip to the next manga if not found
            self.log(f"Skipping '{manga_name}': {e}")

    def compare_chapter(self, manga_name, latest_chapter_number):
        if manga_name not in self.chapter_data:
            self.log(f"New manga '{manga_name}' added. Initializing chapter to 0.")
            self.chapter_data[manga_name] = "0"  # Initialize to 0 for new manga

        # Convert both stored and latest chapter numbers to integers for comparison
        stored_chapter_number = int(self.chapter_data[manga_name])
        latest_chapter_number = int(latest_chapter_number)
    
        if latest_chapter_number > stored_chapter_number:
            message = f"New chapter from {self.sitename} detected for {manga_name}! Previous: {stored_chapter_number}, Now: {latest_chapter_number}"
            self.log(message)
            self.send_telegram_message(message)  # Send notification to Telegram
    
            # Update the chapter number with the latest one after comparison
            self.chapter_data[manga_name] = latest_chapter_number
            self.save_chapter_data()  # Save the updated data immediately after the update
        else:
            self.log(f"No new chapter for {manga_name}. Latest stored chapter is still {stored_chapter_number}.")

    def run(self, manga_list):
        # Load the page once before searching for each manga name
        self.driver.get(self.webpage_url)
        self.log("Page Loaded. URL: " + self.webpage_url)
        for manga_name in manga_list:
            self.get_latest_chapter(manga_name)
            # self.save_chapter_data()
        self.driver.quit()

# Example usage:
manga_list = [
    "A Modern Man Who Got Transmigrated Into the Murim World",
    "Absolute Sword Sense",
    "Academy’s Genius Swordsman",
    "Against the Gods",
    "Apotheosis",
    "Arcane Sniper",
    "Becoming the Sacheon Dang's Swordsmaster-Rank Young Lord",
    "Black Corporation: Joseon",
    "Bloodhound’s Regression Instinct",
    "Chronicles of the Demon Faction",
    "Cultivating the supreme dantian",
    "Death God",
    "Doctor’s Rebirth",
    "Doupo Cangqiong",
    "Dragon-Devouring Mage",
    "Genius of the Unique Lineage",
    "Global Martial Arts",
    "God of Martial Arts",
    "Healing Life Through Camping In Another World",
    "Heavenly Grand Archive’s Young Master",
    "Heavenly Inquisition Sword (Nine Heavens Swordmaster)",
    "Holy Emperor's Grandson Is a Necromancer",
    "How the Pro in His Past Life Sucks the Sweet Honey",
    "I'm Being Raised By Villains",
    "I Work Nine To Five In The Immortal Cultivation World",
    "Infinite Mage",
    "Insanely Talented Player",
    "Keep A Low Profile, Sect Leader!",
    "King of Manifestations",
    "Legend of Star General",
    "Lightning Degree",
    "Lord of Destiny Wheel",
    "Magic Academy’s Genius Blinker",    
    "Magic Emperor",
    "Margrave’s Bastard Son was The Emperor", 
    "Martial God Regressed to Level 2",
    "Martial inverse",
    "Martial Peak",  
    "Murim Login",
    "My Lucky Encounter From The Game Turned Into Reality",
    "My Ruined Academy",
    "My School Life Pretending To Be a Worthless Person",
    "Nano Machine",
    "Necromancer's Evolutionary Traits",
    "Overgeared",
    "Paranoid Mage",
    "Path of the Shaman",
    "Player Who Returned 10,000 Years Later",
    "Ranker Who Lives A Second Time",
    "Reborn As A Monster",
    "Records of the Swordsman Scholar",
    "Regressor Instruction Manual",
    "Regressor of the Fallen family",
    "Release That Witch",
    "Return of the Frozen Player",
    "Return of the Mount Hua Sect",
    "Return of the Legendary Spear Knight",
    "Revenge of the Sword Clan's Hound",
    "Snake Ancestor",
    "Solo Farming in the Tower",
    "Solo Max-Level Newbie",
    "Song Baek",
    "Soul Land V",
    "Starting From Today I'll Work As A City Lord",
    "Swallowed Star",
    "Sword Fanatic Wanders Through The Night",
    "Swordmaster’s Youngest Son", 
    "Surviving the Game as a Barbarian", 
    "Surviving as a Mage in a Magic Academy",
    "Tale of a Scribe Who Retires to the Countryside", 
    "Talent Copycat",
    "Tales of Demons and Gods",
    "Talent-Swallowing Magician",
    "Terminally-Ill Genius Dark Knight",
    "The Archmage's Restaurant",
    "The Count’s Youngest Son is A Player",
    "The Crown Prince That Sells Medicine",
    "The Dark Magician Transmigrates After 66666 Years",
    "The Devil Butler",
    "The Extra’s Academy Survival Guide",
    "The Greatest Estate Designer",
    "The Hero Returns",
    "The Heavenly Demon Can't Live a Normal Life",
    "The Indomitable Martial King",
    "The Knight King Who Returned With a God",
    "The Max Level Hero has Returned!",
    "The Nebula's Civilization",
    "The Primal Hunter",
    "The Lone Necromancer",
    "The Lord's Coins Aren't Decreasing?!",
    "The Reborn Young Lord Is An Assassin",
    "The Return of The Disaster-Class Hero",
    "The Twin Swords Of The Sima Clan",
    "The Tutorial Is Too Hard",
    "The Ultimate of All Ages",
    "To Hell With Being A Saint, I’m A Doctor",
    "Transcension Academy",
    "Warrior Grandpa and Grandmaster daughter",
    "Warrior Grandpa and Supreme Granddaughter",
    "World’s Greatest Senior Disciple",
    "Yuan Zun"
    # Add more manga names here
]

# Set debug=True for local testing
manga_URL = "https://manganato.com/"
sitename = "manganato"
manga_tracker = MangaTracker(manga_URL, sitename, debug=False)  # Set to False when running in GitHub Actions
manga_tracker.run(manga_list)
manga_URL = "https://ciorti.online/lastupdates.php"
sitename = "demonmanga"
manga_tracker2 = MangaTracker(manga_URL, sitename, debug=False) # Set to False
manga_tracker2.run(manga_list)

#17, 20,21,22 changes with change in brower and github action
