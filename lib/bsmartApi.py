import requests
from bs4 import BeautifulSoup
from jose import jwt
import base64
import hashlib
import re
import datetime

# Constants and headers
LOGIN_URL = "https://www.bsmart.it/users/sign_in?back_url=https://books.bsmart.it&from=books"
USER_URL = "https://www.bsmart.it/api/v6/user"
BOOK_LIST_URL = "https://www.bsmart.it/api/v6/books?page_thumb_size=medium&per_page=25000"
BOOK_INFO_URL = "https://www.bsmart.it/api/v6/books/by_book_id/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.bsmart.it',
    'Referer': LOGIN_URL,
}

# Authentication functions

# Prepare session for login and get authenticity token
def get_auth_values(session):
    response = session.get(LOGIN_URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    token_input = soup.find('form', {'id': 'new_user'}).find('input', {'name': 'authenticity_token'})
    authenticity_token = token_input['value']
    return session, authenticity_token

# Perform login and return session (with cookies)
def login(session, authenticity_token, email, password):
    data = {
        'authenticity_token': authenticity_token,
        'user[email]': email,
        'user[password]': password,
        'commit': 'Log in',
    }
    session.post(LOGIN_URL, data=data, headers=HEADERS)
    return session

# Get user's auth token from API
def get_auth_token(session):
    response = session.get(USER_URL, headers=HEADERS).json()
    return response.get("auth_token")


# Book list / info functions

# Get all books for the user
def get_books(session, auth_token):
    auth_headers = HEADERS.copy()
    auth_headers["auth_token"] = auth_token
    response = session.get(BOOK_LIST_URL, headers=auth_headers)
    return response.json()

# Get information for a specific book
def get_book_info(session, auth_token, book_id):
    auth_headers = HEADERS.copy()
    auth_headers["auth_token"] = auth_token
    response = session.get(f"{BOOK_INFO_URL}{book_id}", headers=auth_headers)
    return response.json()


# Jwt / password functions

# Generate the book password used for JWT creation, reverse engeneered from obfuscated and minified js
def calculate_password(book_info):
    publisher_id = str(book_info["brand"]["publisher"]["id"])
    book_code = str(book_info["book_code"])
    book_id = str(book_info["id"])
    publisher_name = str(book_info["brand"]["publisher"]["name"])

    encoded_book_code = base64.b64encode(book_code.encode()).decode()
    first_part = encoded_book_code[:8]
    second_part = encoded_book_code[8:]

    first_part_hash = hashlib.md5(first_part.encode()).hexdigest()
    publisher_name_hash = hashlib.md5(publisher_name.encode()).hexdigest()

    password_str = f"{publisher_id}b{first_part_hash}s{book_id}{publisher_name_hash}m{second_part}="
    return base64.b64encode(password_str.encode()).decode()

# Decrypt a private key extracted from obfuscated JS
def decrypt_private_key(encrypted_key):
    result = []
    for char in encrypted_key:
        if char.isalpha():
            upper_limit = 90 if char.isupper() else 122
            shifted = ord(char) + 14
            result.append(chr(shifted if shifted <= upper_limit else shifted - 26))
        else:
            result.append(char)
    return ''.join(result)

# Get the URL of the dynamic JS file (changes frequently).
def get_dynamic_js(session):
    html_content = session.get("https://books.bsmart.it").content
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'src': re.compile(r'/assets/index-')})
    return f"https://books.bsmart.it{script_tag['src']}"

# Extract and decrypt private key from dynamic JS
def dump_private_key(session, js_url):
    js_content = session.get(js_url).content.decode('utf-8')
    match = re.search(r"-----NQSUZ BDUHMFQ WQK-----([\s\S]*?)-----QZP BDUHMFQ WQK-----", js_content)
    encrypted_key = match.group(0)
    return decrypt_private_key(encrypted_key)

# Create a JWT for accessing a book
def create_jwt(session, private_key, book_id, password):
    permissions = ["read-document", "write"]
    document_id = f"bsmart-P-S-{book_id}"
    exp_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    payload = {
        "permissions": permissions,
        "document_id": document_id,
        "password": password,
        "exp": int(exp_time.timestamp())
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

# Retrieve authentication credentials for downloading the book
def get_book_auth(session, book_id, jwt_token):
    payload = {"jwt": jwt_token}
    auth_headers = HEADERS.copy()
    auth_headers.update({
        "PSPDFKit-Platform": "web",
        "PSPDFKit-Version": "protocol=5, client=1.1.0, client-git=e4dd477934",
        "Origin": "https://books.bsmart.it",
        "Referer": "https://books.bsmart.it/"
    })
    response = session.post(f"https://pspdfkit.bsmart.it/i/d/bsmart-P-S-{book_id}/auth",
                            headers=auth_headers, json=payload)
    return response.json()
