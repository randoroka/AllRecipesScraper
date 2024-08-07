import requests
import sys
import validators
from bs4 import BeautifulSoup


def main():
    print("This program takes a recipe link from AllRecipes.com and downloads it onto a file in the current directory. Link must begin in the format of https://www.allrecipes.com/ or www.allrecipes.com\n")
    recipe_url = input("Enter the Allrecipes recipe URL: ").strip()
    
    if not validate_url(recipe_url):
        sys.exit("Invalid recipe URL. Please provide a valid link from allrecipes.com.")
    
    try:
        create_recipe_file(recipe_url)
    except Exception as e:
        print(f"Error creating recipe file: {e}")


def validate_url(recipe_url):
    if not recipe_url.startswith("https://"):
        recipe_url = f"https://{recipe_url}"
    return validators.url(recipe_url) and recipe_url.startswith("https://www.allrecipes.com/")


def fetch_html(recipe_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(recipe_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        sys.exit(f"Error retrieving recipe: {e}")
    return BeautifulSoup(response.content, 'html.parser')


def get_title(soup):
    title = soup.find('h1', class_='article-heading type--lion')
    return title.text.strip() if title else 'Unknown Title'


def get_ingredients(soup):
    main_ingredients = parse_ingredients(soup.find('ul', class_='mntl-structured-ingredients__list'))
    additional_ingredients_heading = soup.find('p', class_='mntl-structured-ingredients__list-heading type--goat-bold')
    
    additional_ingredients = []
    if additional_ingredients_heading:
        additional_ingredients_section = additional_ingredients_heading.find_next('ul', class_='mntl-structured-ingredients__list')
        additional_ingredients = parse_ingredients(additional_ingredients_section)

    return main_ingredients, additional_ingredients, additional_ingredients_heading.text.strip() if additional_ingredients_heading else None


def parse_ingredients(ingredient_list_element):
    ingredients = []
    if ingredient_list_element:
        for item in ingredient_list_element.find_all('li', class_='mntl-structured-ingredients__list-item'):
            ingredient = {
                'name': item.find('span', {'data-ingredient-name': True}).text.strip() if item.find('span', {'data-ingredient-name': True}) else '',
                'quantity': item.find('span', {'data-ingredient-quantity': True}).text.strip() if item.find('span', {'data-ingredient-quantity': True}) else '',
                'unit': item.find('span', {'data-ingredient-unit': True}).text.strip() if item.find('span', {'data-ingredient-unit': True}) else ''
            }
            ingredients.append(ingredient)
    return ingredients


def get_details(soup):
    details = {}
    details_section = soup.find('div', class_='mntl-recipe-details__content')
    if details_section:
        for item in details_section.find_all('div', class_='mntl-recipe-details__item'):
            label = item.find('div', class_='mntl-recipe-details__label').text.strip()
            value = item.find('div', class_='mntl-recipe-details__value').text.strip()
            details[label] = value
    return details


def get_instructions(soup):
    instructions = []
    instructions_section = soup.find('div', class_='comp recipe__steps-content mntl-sc-page mntl-block')
    if instructions_section:
        for i, step in enumerate(instructions_section.find_all('p', class_='comp mntl-sc-block mntl-sc-block-html'), 1):
            instructions.append(f"Step {i}: {step.text.strip()}")
    return instructions


def create_recipe_file(recipe_url):
    soup = fetch_html(recipe_url)
    
    title = get_title(soup)
    ingredients, additional_ingredients, heading = get_ingredients(soup)
    details = get_details(soup)
    instructions = get_instructions(soup)

    filename = f"{title}.txt"
    with open(filename, 'w') as file:
        file.write(f"{title}\n\n")
        write_section(file, "Ingredients", format_ingredients(ingredients))
        if additional_ingredients:
            write_section(file, heading, format_ingredients(additional_ingredients))
        write_section(file, "Recipe Details", format_details(details))
        write_section(file, "Directions", instructions)
    


def write_section(file, heading, content):
    file.write(f"{heading}:\n")
    if isinstance(content, list):
        for line in content:
            file.write(f"{line}\n")
    elif isinstance(content, dict):
        for key, value in content.items():
            file.write(f"{key}: {value}\n")
    file.write("\n")


def format_ingredients(ingredients):
    formatted = []
    for ingredient in ingredients:
        quantity = ingredient.get('quantity', '')
        unit = ingredient.get('unit', '')
        name = ingredient.get('name', '')
        formatted.append(f"{quantity} {unit} {name}".strip())
    return formatted


def format_details(details):
    keys = ['Prep Time:', 'Cook Time:', 'Additional Time:', 'Total Time:', 'Servings:', 'Yield:']
    return {key: details.get(key, 'N/A') for key in keys}


if __name__ == "__main__":
    main()
