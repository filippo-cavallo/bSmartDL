import eel
import os
import requests
import subprocess
import lib.bsmartApi
from io import BytesIO
from fpdf import FPDF
import sys

def on_close(page, sockets):
    sys.exit(0)

# Get absolute path for PyInstaller
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class AppState:
    auth_token = None
    session_token = None
    session = None

# bSmart login
@eel.expose
def bsmartLogin(email, password):
    if email and password:
        # Create requests session
        eel.addLog("🔄 Creating session...")
        session = requests.Session()
        eel.addLog("🔑 Logging in...")

        # Get bsmart authenticity token
        session, authenticity_token = lib.bsmartApi.get_auth_values(session)
        session = lib.bsmartApi.login(session, authenticity_token, email, password)

        # Get session token
        session_token = None
        for cookie in session.cookies:
            if cookie.name == '_bsw_session_v1_production':
                session_token = cookie.value
                break
        
        if session_token:
            eel.addLog("🔖 Session token: " + session_token)
        else:
            eel.addLog("❌ Error: Login failed, invalid session token")
            return False
        
        # From session token get account auth token
        eel.addLog("🔄 Getting auth token...")
        auth_token=lib.bsmartApi.get_auth_token(session)

        # Save to app state (global variables)
        AppState.auth_token = auth_token
        AppState.session = session
        AppState.session_token = session_token

        if auth_token:
            eel.addLog("✅ Logged in!")
            eel.addLog("🔖 Auth token: "+ auth_token)
        else:
            eel.addLog("❌ Error: Login failed, invalid auth token, check credentials")
            return False
    return True

# Get book list
@eel.expose
def getBooks():
    if AppState.auth_token:
        eel.addLog("🔄 Getting books...")
        books = lib.bsmartApi.get_books(AppState.session, AppState.auth_token)
        return books
    else:
        return None

# Download a book, given book_id
@eel.expose
def downloadBook(book_id):
    try: # Error handling
        eel.addLog(f"🔄 Starting download for book {book_id}...")

        # Get book info from bSmart
        eel.addLog("ℹ️ Getting book info...")
        book_info = lib.bsmartApi.get_book_info(AppState.session, AppState.auth_token, book_id)
        if not book_info or "page_count" not in book_info:
            eel.addLog("❌ Error: Failed to retrieve book information.")
            return
        page_count = book_info["page_count"]
        title = book_info["title"]
        eel.addLog(f"✅ Book has {page_count} pages.")

        # Calculate password, reverse engeneered from minified and obfuscated js
        eel.addLog("🔑 Calculating password...")
        password = lib.bsmartApi.calculate_password(book_info)
        if not password:
            eel.addLog("❌ Error: Failed to calculate book password.")
            return
        eel.addLog("✅ Password calculated.")

        # Get dynamic js file to extract private key
        eel.addLog("ℹ️ Getting dynamic js...")
        dynamic_js = lib.bsmartApi.get_dynamic_js(AppState.session)
        if not dynamic_js:
            eel.addLog("❌ Error: Failed to retrieve dynamic JS.")
            return

        # Get private key needed for jwt creation
        eel.addLog("ℹ️ Dumping private key...")
        private_key = lib.bsmartApi.dump_private_key(AppState.session, dynamic_js)
        if not private_key:
            eel.addLog("❌ Error: Failed to extract private key.")
            return

        # Create book authentication json web token
        eel.addLog("🔑 Creating JWT...")
        jwt = lib.bsmartApi.create_jwt(AppState.session, private_key, book_id, password)
        if not jwt:
            eel.addLog("❌ Error: Failed to create JWT for book authentication.")
            return
        eel.addLog("✅ JWT created.")

        # Get book authentication, needed for accessing book images
        eel.addLog("ℹ️ Getting book auth...")
        auth_credentials = lib.bsmartApi.get_book_auth(AppState.session, book_id, jwt)
        if not auth_credentials:
            eel.addLog("❌ Error: Failed to get book authentication credentials.")
            return

        eel.addLog("✅ Authenticated for book download!")

        # Define headers used for authentication (image requests)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'X-PSPDFKit-Image-Token': auth_credentials["imageToken"],
        }

        # Create folder if doesnt exist and create pdf
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/{title}.pdf" # Change title if you want
        eel.addLog(f"💾 Downloading to {title}.pdf...")

        pdf = FPDF(unit="pt", format=[1600, 2262]) # Page dimensions
        pdf.set_auto_page_break(auto=False)

        # Download each page
        for i in range(page_count):
            page_content = requests.get(f'https://pspdfkit.bsmart.it/i/d/bsmart-P-S-{book_id}/h/{auth_credentials["layerHandle"]}/page-{i}-dimensions-1600-2262-tile-0-0-1600-2262',headers=headers).content
            if not page_content:
                eel.addLog(f"❌ Failed to download page {i}")
                continue

            img = BytesIO(page_content)
            pdf.add_page()
            pdf.image(img, x=0, y=0, w=1600, h=2262)

            # Update status in logs
            eel.addLog(f"📄 Downloaded page {i+1}/{page_count}")

        pdf.output(filename)
        eel.addLog(f"✅ Download completed! File saved as {title}.pdf in downloads folder")

        # Open folder after download
        if os.name == "nt":  # Windows
            os.startfile(os.path.abspath("downloads"))
        elif os.name == "posix":  # macOS/Linux
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", os.path.abspath("downloads")])

    except Exception as e:
        eel.addLog(f"❌ An unexpected error occurred during download: {e}")


# Main.py
if __name__ == "__main__":
    # Check if downloads folder exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")  # If not, create it

    # Init eel
    eel.init(resource_path("web"))
    eel.start('index.html', size=(1000, 800), block=True, close_callback=on_close)
