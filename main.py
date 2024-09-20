from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from termcolor import colored
from datetime import datetime, timedelta

def display_banner():
    banner = """
<-.(`-')   _     <-. (`-')_ (`-')  _    (`-')  _   (`-')    
 __( OO)  (_)       \( OO) )(OO ).-/    (OO ).-/   ( OO).-> 
'-'---.\  ,-(`-'),--./ ,--/ / ,---.     / ,---.  ,(_/----.  
| .-. (/  | ( OO)|   \ |  | | \ /`.\    | \ /`.\ |__,    |  
| '-' `.) |  |  )|  . '|  |)'-'|_.' |   '-'|_.' | (_/   /   
| /`'.  |(|  |_/ |  |\    |(|  .-.  |  (|  .-.  | .'  .'_   
| '--'  / |  |'->|  | \   | |  | |  |,-.|  | |  ||       |  
`------'  `--'   `--'  `--' `--' `--''-'`--' `--'`-------'           
    """
    print(colored(banner, 'cyan'))

def filter_by_date(whentagtext, date_filter):
    today = datetime.now().date()
    post_date = None

    if 'bugün' in whentagtext:
        post_date = today
    elif 'dünən' in whentagtext:
        post_date = today - timedelta(days=1)
    else:
        try:
            days_ago = int(whentagtext.split()[0])
            post_date = today - timedelta(days=days_ago)
        except ValueError:
            pass

    if post_date:
        if date_filter == '1' and post_date >= today - timedelta(days=1):  # Today and Yesterday
            return True
        elif date_filter == '2' and post_date >= today - timedelta(days=5):  # Last 5 days
            return True
        elif date_filter == '3' and post_date >= today - timedelta(days=10):  # Last 10 days
            return True
    return False

def get_top_ten_prices(room_count, page_count, region, kupcha, metro, repair, date_filter, rent_or_buy,browser):
    fregion = 'baki'
    fmetro = '/'
    fkupcha = '&has_bill_of_sale=true'
    frepair = '&'
    driver = None

    if browser == 1:
        driver = webdriver.Safari()
    else:
        driver = webdriver.Chrome()

    
    if region == 1:
        fregion = 'baki'
    elif region == 2:
        fregion = 'sumqayit'
    elif region == 3:
        fregion = 'xirdalan'

    if kupcha == 'yes' and rent_or_buy == 2:
        fkupcha = 'has_bill_of_sale=true&'
    else:
        fkupcha = ''

    if repair == '1':
        frepair = 'has_repair=true&'
    elif repair == '2':
        frepair = 'has_repair=false&'
    elif repair == '3' and fkupcha == '':
        frepair = ''
    else:
        frepair = '&'

    if metro == 1:
        fmetro = '/genclik/'
    elif metro == 2:
        fmetro = '/insaatcilar/'
    elif metro == 3:
        fmetro = '/elmler-akademiyasi/'
    elif metro == 4:
        fmetro = '/'

    # Set base URL depending on rent or buy
    if rent_or_buy == 1:
        base_url = f"https://bina.az/kiraye/menziller/{room_count}-otaqli/?{fkupcha}{frepair}page={{}}"
    else:
        base_url = f"https://bina.az/{fregion}{fmetro}alqi-satqi/menziller/yeni-tikili/?{fkupcha}{frepair}page={{}}"
    
    # Initialize a list to store the top ten prices per m² and corresponding links
    top_ten = []

    try:

        # Loop through the specified number of pages
        for page in range(1, page_count + 1):
            # Open the page
            driver.get(base_url.format(page))

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Find all listings
            listings = soup.find_all('div', class_='items-i')

            for listing in listings:
                price_tag = listing.find('span', class_='price-val')
                details_tag = listing.find('ul', class_='name')
                location = listing.find('div', class_='location')
                link_tag = listing.find('a', href=True)
                when_tag = listing.find('div', class_="city_when")

                location_text = location.get_text(strip=True) if location else ''
                if location_text in ['Masazır q.', 'Hövsan q.', 'Sahil q.', 'Binəqədi q.', 'Sulutəpə q.', 'Zabrat q.', 'Mehdiabad q.']:
                    continue

                whentagtext = when_tag.get_text(strip=True) if when_tag else ''
                if filter_by_date(whentagtext, date_filter):
                    if price_tag and details_tag and link_tag:
                        try:
                            price = int(price_tag.get_text(strip=True).replace(' ', '').replace('AZN', ''))

                            # Adjust for rent (per month or per day)
                            if rent_or_buy == 1:
                                price_unit = listing.find('span', class_='price-per').get_text(strip=True)
                                if 'gün' in price_unit:
                                    price *= 30  # convert daily to monthly
                                # Add m² parsing logic
                                area = None
                                for li in details_tag.find_all('li'):
                                    if 'm²' in li.get_text():
                                        area = float(li.get_text().split('m²')[0].strip())
                                        break

                                if area:
                                    price_per_m2 = price / area
                                    top_ten.append((price_per_m2, link_tag['href']))
                            else:
                                # Normal sale logic
                                area = None
                                for li in details_tag.find_all('li'):
                                    if 'm²' in li.get_text():
                                        area = float(li.get_text().split('m²')[0].strip())
                                        break

                                if area:
                                    price_per_m2 = price / area
                                    top_ten.append((price_per_m2, link_tag['href']))

                        except (ValueError, IndexError):
                            print(colored("Could not calculate price per m² for a listing.", 'red'))

    except WebDriverException as e:
        print(colored(f"Error with WebDriver: {str(e)}", 'red'))

    finally:
        # Ensure WebDriver is properly closed
        if 'driver' in locals():
            driver.quit()

    # Sort the top_ten list by price per m²
    top_ten = sorted(top_ten, key=lambda x: x[0])

    # Remove duplicate links
    unique_top_ten = []
    seen_links = set()

    for price_per_m2, link in top_ten:
        if link not in seen_links:
            unique_top_ten.append((price_per_m2, link))
            seen_links.add(link)
        if len(unique_top_ten) == 10:
            break

    # Display the results with appropriate colors
    medals = ['yellow', 'light_grey', 'grey', 'blue', 'magenta', 'cyan', 'green', 'red', 'white', 'blue']
    for i, (price_per_m2, link) in enumerate(unique_top_ten):
        color = medals[i]
        print('\n\n')
        print(colored(f"{i+1}. Price per m²: {price_per_m2:.2f} AZN", color))
        print(colored(f"Link to the listing: https://bina.az{link}", 'blue'))
        print('\n\n')

def fancy_input(prompt):
    print("\n" + "="*50)
    value = input(colored(prompt, 'yellow')).strip()
    print("="*50 + "\n")
    return value

def fancy_input(prompt):
    print("\n" + "="*50)
    value = input(colored(prompt, 'yellow')).strip()
    print("="*50 + "\n")
    return value

def main():
    display_banner()

    browser = int(fancy_input('Skan üçün istifadə edəcəyiniz brauzeri seçin.\n\n(1) Safari\n(2) Chrome\n\n'))
    rent_or_buy= int(fancy_input('\n Kiraye(1) yoxsa Almaq(2)\n\nSechin:')); 
    region = int(fancy_input("\nBakı (1)\nSumqayit (2)\nXirdalan (3)\n\nŞəhəri seçin: "))
    room_count = fancy_input("Mənzildəki otaq sayını yazın (məsələn, 2-otaqlı mənzillər üçün 2 yazın): ")
    kupcha = fancy_input("Çıxarışın olmağı mütləqdir? (yes/no):").lower()
    repair = fancy_input("Təmirli ya təmirsiz mənzillər axtaraq?\n\n(1) Təmirli\n(2) Təmirsiz\n(3) Hər hansı\n\nSeçin:")
    metro = int(fancy_input("Metro-nın adına görə skan edək:\n\n(1) Gənclik\n(2) İnşaatçılar\n(3) Elmlər Akademiyası\n(4) Hər hansı\n\nSeçin: "))
    date_filter = fancy_input("Post edilmiş tarixlərə görə axtarış edin:\n\n(1) Bugün və dünən\n(2) Son 5 gün\n(3) Son 10 gün\n\nSeçin: ")
    page_count = int(fancy_input("Neçə səhifə skan edək?(10 tövsiyyə olunur): "))

    get_top_ten_prices(room_count, page_count, region, kupcha, metro, repair, date_filter,rent_or_buy,browser)

if __name__ == "__main__":
    main()
