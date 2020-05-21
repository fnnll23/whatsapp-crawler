from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException



class WhatsappCrawler:
    def __init__(self, language, chrome_version, **args):
        self.language = language
        self.chrome_version = chrome_version
        self.contact = args.get('contact')
        self.message = args.get('message')
        
        caps = DesiredCapabilities().CHROME
        options = webdriver.ChromeOptions()
        prefs = {'profile.default_content_setting_values':{'images': 2}}
        options.add_experimental_option('prefs', prefs)

        # Specify brwoser dirver for selenium
        if self.chrome_version in ['83', '81', '80']:
            self.driver = webdriver.Chrome(desired_capabilities=caps, options=options, executable_path = './utils/drivers/chromedriver' + self.chrome_version)

        # Defining placeholders by language
        if self.language == 'Spanish':
            placeholder_str1 = '"Buscar o empezar un chat nuevo"'
            placeholder_str2 = '"Escribe un mensaje aquí"'
        elif self.language == 'English':
            placeholder_str1 = '"Search or start new chat"'
            placeholder_str2 = '"Type a message"'
        elif self.language == 'Portuguese':
            placeholder_str1 = '"Procurar ou começar uma nova conversa"' 
            placeholder_str2 = '"Digite uma mensagem"'
    
    # Opens whatsapp web site
    def open_whatsapp(self):
        self.driver.get('https://web.whatsapp.com/')

    # Terminates browser
    def close(self):
        self.driver.quit()

    # Search for specified contact in whatsapp web left pane
    def search_contact(self, placeholder_str1, testing=False):
        driver = self.driver
        contact = self.contact

        # Checks if still in landing page
        try:
            driver.find_elements_by_css_selector(".landing-wrapper")
            raise TimeoutError("QR scan timeout")
        except:
            pass

        # Checks if placeholder is found
        try:
            placeholder = driver.find_elements_by_xpath("//*[contains(text(), " + placeholder_str1 + ")]")[0]
            parent = placeholder.find_elements_by_xpath("./..")[0]
            parent.click()
        except IndexError:
            raise ValueError('Placeholder ' + str(placeholder_str1) + ' not found')

        if testing == False:
            #Step 2: Search for number and press Return
            label = parent.find_elements_by_css_selector("label")[0]
            divPadre = label.find_elements_by_css_selector("div")[0]
            divHijo2 = divPadre.find_elements_by_css_selector("div")[1]
            divHijo2.send_keys(str(contact))
            divHijo2.send_keys(Keys.RETURN)
    
    # Sends specified message
    def send_message(self, placeholder_str2):
        driver = self.driver
        message = self.message
    
        #Activate input field
        placeholder = driver.find_elements_by_xpath("//*[contains(text()," + placeholder_str2 + ")]")[0]
        parent = placeholder.find_elements_by_xpath("./..")[0]
        parent.click()

        #Insert message
        parent2 = parent.find_elements_by_xpath("./..")[0]
        parent2.send_keys(message)

        #Click send button
        parent2sibling = parent2.find_elements_by_xpath("following-sibling::*")[0]
        boton = parent2sibling.find_elements_by_css_selector('button')[0]
        boton.click()