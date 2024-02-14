import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from tqdm import tqdm

class WebScraper:
    def fetch_levi_data(self):
        urls = [
            'https://www.levi.com/US/en_US/clothing/men/jeans/c/levi_clothing_men_jeans',
            'https://www.levi.com/US/en_US/clothing/women/jeans/c/levi_clothing_women_jeans'
        ]
        
        levi_data = []

        for url in tqdm(urls, desc="Fetching Levi data"):
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            all_href_values = [str(a.get('href')) for a in soup.find_all('a') if a is not None]

            href_values_with_p = [href for href in all_href_values if '/p/' in href]

            # Lists to store extracted data
            product_url = []
            product_names = []
            product_overviews = []
            how_it_fits_list = []
            composition_care_list = []
            image_urls = []
            price_list = [] 

            # Extract data for each product
            for href in href_values_with_p:
                # full_url = "https://www.levi.com" + href
                if href.startswith('/'):
                    full_url = "https://www.levi.com" + href
                else:
                    full_url = href

                response = requests.get(full_url)
                html_content = response.text

                soup = BeautifulSoup(html_content, 'html.parser')

                product_name = soup.find('h1', class_='product-title').text.strip()
                product_names.append(product_name)

                product_overview = soup.find('div', class_='product-overview').text.strip()
                product_overviews.append(product_overview)

                spec_overview = soup.find('div', class_='product-spec-overview')
                how_it_fits = spec_overview.find('span', text='How it Fits').find_next('ul').text.strip()
                how_it_fits_list.append(how_it_fits)

                composition_care = spec_overview.find('span', text='Composition & Care').find_next('ul').text.strip()
                composition_care_list.append(composition_care)
                
                # Extracting image URL
                picture_tag = soup.find('picture', class_='responsive-picture')
                if picture_tag:
                    img_tag = picture_tag.find('img', class_='responsive-img')
                    if img_tag:
                        image_url = img_tag['src']
                        image_urls.append(image_url)
                    else:
                        image_urls.append('Image not found')
                else:
                    image_urls.append('Image not found')

                price_element = soup.find('span', class_='price')

                price = price_element.get_text(strip=True)
                price_list.append(price)

                product_url.append(full_url)

            # Create DataFrame
            data = {
                'Product Url': product_url,
                'Product Name': product_names,
                'Product Overview': product_overviews,
                'How it Fits': how_it_fits_list,
                'Composition & Care': composition_care_list,
                'Image URL': image_urls,
                'Price' : price_list
            }

            levi_df = pd.DataFrame(data)
            levi_data.append(levi_df)
        
        return pd.concat(levi_data)

    def fetch_shopduder_data(self):
        urls = [
            'https://shopduer.com/collections/mens-stretch-pants',
            'https://shopduer.com/collections/mens-stretch-jeans',
            'https://shopduer.com/collections/mens-joggers'
        ]

        shopduder_data = []

        for url in tqdm(urls, desc="Fetching shopduer data"):
            filtered_href_values = self.fetch_filtered_href(url)
            for href in filtered_href_values:
                full_url = "https://shopduer.com" + href
                product_details = self.fetch_product_details(full_url)
                shopduder_data.append(product_details)

        return pd.DataFrame(shopduder_data, columns=['Product Url', 'Product Name', 'Product Overview', 'How it Fits', 'Composition & Care', 'Image URL', 'Price'])

    def fetch_filtered_href(self, url):
        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        href_values = [a.get('href') for a in soup.find_all('a', class_='card__link')]
        return [href for href in href_values if '/products/' in href]

    def fetch_product_details(self, url):
        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        product_name = soup.find('h1', class_='product__title').text.strip()

        product_overview = soup.find('div', id='accordion-pdp-tabs-1').find('div', class_='product__description--pdp').text.strip()

        fit = soup.find('div', id='accordion-pdp-tabs-2').find('div', class_='accordion__content').text.strip()

        fabric_and_care = soup.find('div', id='accordion--pdp-tabs-3--content').text.strip()

        img_url = soup.find('img', class_='responsive-image__image')['src']

        price_element = soup.find('span', class_='price__original')

        price = price_element.get_text(strip=True)

        return [url, product_name, product_overview, fit, fabric_and_care, img_url, price]

    def create_excel(self):
        levi_df = self.fetch_levi_data()
        shopduder_df = self.fetch_shopduder_data()
        levi_df = levi_df.drop_duplicates(subset=['Product Url'])
        shopduder_df = shopduder_df.drop_duplicates(subset=['Product Url'])

        with pd.ExcelWriter('/Users/thilip/Downloads/product_details_v1.xlsx') as writer:
            levi_df.to_excel(writer, sheet_name='Levi', index=False)
            shopduder_df.to_excel(writer, sheet_name='Shopduder', index=False)
            
            women_url_pattern = "https://www.g-star.com/en_us/shop/women/jeans?page={}"
            men_url_pattern = "https://www.g-star.com/en_us/shop/men/jeans?page={}"

            women_all_product_hrefs = extract_product_hrefs(women_url_pattern)
            men_all_product_hrefs = extract_product_hrefs(men_url_pattern)

            all_product_hrefs = women_all_product_hrefs + men_all_product_hrefs

            all_product_hrefs = [url for url in all_product_hrefs if url != '/en_us/shop/women/jeans/g-star-shape']

            product_data_list = []
            for product_url in all_product_hrefs:
                product_data = scrape_product_data("https://www.g-star.com" + product_url)
                if product_data:
                    product_data_list.extend(product_data)

            gstar_df = pd.DataFrame(product_data_list)
            gstar_df.to_excel(writer, sheet_name='G-star-raw', index=False)

def extract_product_hrefs(url_pattern, page_limit=5):
    all_product_hrefs = []

    def extract_hrefs(url):
        product_hrefs = []

        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            links = soup.find_all('a', href=True)

            product_hrefs.extend([link['href'] for link in links if re.match(r'^/en_us/shop/(men|women)/jeans/\w+-\w+-\w+$', link['href'])])

            next_page_link = soup.find('a', class_='link--next')
            if next_page_link:
                next_page_url = "https://www.g-star.com" + next_page_link['href']

                product_hrefs.extend(extract_hrefs(next_page_url))

        return product_hrefs

    for page_number in range(1, page_limit + 1):
        page_url = url_pattern.format(page_number)

        current_page_hrefs = extract_hrefs(page_url)
        if not current_page_hrefs:
            break
        all_product_hrefs.extend(current_page_hrefs)

        if len(current_page_hrefs) < 1:
            break

    return all_product_hrefs


def scrape_product_data(url):
    product_data_list = []

    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        product_name_element = soup.find('div', {'data-testid': 'summary-product-name'})
        product_description_element = soup.find('div', {'data-testid': 'exploding-view-description'})
        features_element = soup.find('ul', {'data-testid': 'features-bullets'})
        materials_element = soup.find('ul', {'data-testid': 'fabrics-bullets'})
        sizing_element = soup.find('ul', {'data-testid': 'features-dimensions-bullets'})

        if product_name_element:
            product_name = product_name_element.find('h1').text.strip()
        else:
            product_name = ""

        if product_description_element:
            product_description = product_description_element.text.strip()
        else:
            product_description = ""

        feature_list = [feature.text.strip() for feature in features_element.find_all('p', {'class': 'sc-f49cbd52-0 eRaPyi'})] if features_element else []
        material_list = [material.text.strip() for material in materials_element.find_all('li', {'class': 'sc-7f4ee78b-7 dIZsTi'})] if materials_element else []
        sizing_list = [sizing_item.text.strip() for sizing_item in sizing_element.find_all('p', {'data-testid': 'features-dimensions-bullets-item'})] if sizing_element else []

        source_tag = soup.find('source')
        srcset_value = source_tag.get('srcset') if source_tag else ''
        image_urls_split = srcset_value.split(".jpg")
        image_urls = [url.strip() + ".jpg" for url in image_urls_split[:-1]]


        price_element = soup.find('strong', {'data-testid': 'summary-product-price'})

        price = price_element.get_text(strip=True)

        product_data = {
            'Product URL': [url],
            'Product Name': product_name,
            'Product Description': product_description,
            'Product Features': [feature_list],
            'Product Materials': [material_list],
            'Sizing': [sizing_list],
            'Image URL': [image_urls],
            'Price':[price]
        }

        product_data_list.append(product_data)

    return product_data_list


if __name__ == "__main__":
    scraper = WebScraper()
    scraper.create_excel()
