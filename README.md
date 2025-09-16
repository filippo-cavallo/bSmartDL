# bSmartDL 📚

_A reverse-engineered backup tool for your legally purchased bSmart books_

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)

---

> [!CAUTION]
> This project is for **educational and personal use only**. It does **not encourage piracy**.
> The sole purpose is to help you **back up books you have legally purchased**, allowing you to read them on platforms that don't natively support bSmart Books client (e-readers, offline PDF readers and many more)
>
> **The author takes no responsibility for any misuse.** If you own the book, you have the right to read it. If you don't, please don't use this tool.

---

## What is bSmartDL? ✨

bSmartDL is a desktop tool that lets you **export your legally purchased books from bSmart Books as high-quality DRM free PDFs**. Built with Python and Eel for a clean UI.

This project was born from a deep-dive into the bSmart Books platform, involving:
* Reverse engineering of minified and obfuscated JavaScript.
* Decryption of a private key embedded in dynamic javascript.
* Reconstruction of a custom, per book password generation algorithm.
* JWT token creation to authenticate with the bSmart backend.

---

## Features 🚀

* **Simple, intuitive UI** to log in with your bSmart account.
* **Automatically lists** all your purchased books with covers and metadata.
* **One-click PDF downloads** for a seamless backup process.
* **Real-time logging** to monitor your downloads.

---

## Getting Started 💻

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/filippo-cavallo/bSmartDL.git
    cd bSmartDL
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  Ensure you have a **Chromium-based browser** (like Chrome, Edge, or Brave) installed, as it's required by the Eel framework.

---

### Building an Executable

You can easily package the project into a standalone executable using **PyInstaller**.

Already built Windows executables are provided in releases.

**Example for Windows**:
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "web;web" --clean --strip --icon=web/assets/favicon.ico app.py
```

---

### Technical Deep-Dive 🧠

Here’s a simplified breakdown of the core logic:

1.  **Authentication**: The tool simulates the standard login flow to obtain a session cookie and an authentication token.

2.  **JWT Generation**:
    * The tool analyzes the dynamic JavaScript on the bSmart platform to find and decrypt an embedded private key.

    * It then uses a **reverse engineered algorithm** to generate a unique, per-book password based on book specific metadata.

    * Finally, a unique **JSON Web Token (JWT)** is crafted and signed with the decrypted private key. This token includes permissions and the book specific password.

3.  **Content Access**: Using the newly created JWT, the tool authenticates with the `pspdfkit.bsmart.it` backend. It then downloads each book page as a high quality image.

4.  **PDF Assembly**: All downloaded images are compiled into a PDF file using the `fpdf2` library
