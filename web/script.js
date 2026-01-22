// On page (DOM) load
document.addEventListener("DOMContentLoaded", () => {
  const isLoggedIn = sessionStorage.getItem("isLoggedIn");
  if (isLoggedIn === "true") {
    addLog("🔑 Already logged in");
    showPage("book-list");
    renderBooks();
  } else {
    showPage("auth-login");
  }
});

// Function that logs to the log box
eel.expose(addLog);
function addLog(message) {
  const logBox = document.getElementById("log-box");
  const time = new Date().toLocaleTimeString();
  logBox.innerHTML += `[${time}] ${message}\n`;
  logBox.scrollTop = logBox.scrollHeight;
}

// Function that switches to a page
function showPage(pageId) {
  document.querySelectorAll(".page").forEach((page) => {
    page.classList.add("d-none");
  });

  const page = document.getElementById(pageId);
  if (page) page.classList.remove("d-none");
}

// Checks if the backend (py) is logged in to bSmart and attempts to log in if not
async function login() {
  var email = document.getElementById("email").value;
  var password = document.getElementById("password").value;
  if (!email || !password) {
    addLog("❌ Error: Provide both email and password");
    return;
  }
  addLog("🔑 Attempting login...");

  isLoggedIn = await eel.bsmartLogin(email, password)();
  sessionStorage.setItem("isLoggedIn", isLoggedIn);

  if (isLoggedIn) {
    showPage("book-list")
    renderBooks();
  }
}

// Render books
async function renderBooks() {
    // Get book list
  const books = await eel.getBooks()();
  console.log(books);

  // Clear
  const container = document.getElementById("books-container");
  container.innerHTML = "";

  // Handle errors
  if (!books) {
    addLog("❌ No books found or not logged in.");
    return;
  }

  // Render each book's card
  books.forEach((book) => {
    const card = document.createElement("div");
    card.className = "col-12 col-sm-6 col-md-4 col-lg-3"; // responsive grid

    // Process authors array into a string
    const authorsText = (book.authors || [])
      .map((author) => `${author.name} ${author.surname}`)
      .join(", ");

    card.innerHTML = `
    <div class="card h-100 shadow-sm">
        <img src="${ book.cover }" class="card-img-top" alt="Cover">
        <div class="card-body d-flex flex-column">
        <h5 class="card-title">${book.title}</h5>
        <p class="card-text text-muted">${authorsText}</p>
        <div class="mt-auto">
            <button class="btn btn-primary w-100" onclick="downloadOptions('${book.id}', '${book.page_count}')">Download</button>
        </div>
        </div>
    </div>`;

    container.appendChild(card);
  });
}

// Show download options modal
function downloadOptions(bookId, maxPages) {
  // Get or create modal instance
  const downloadModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('downloadModal'));
  // Set max pages in the modal for end page
  document.getElementById('end-page').setAttribute('placeholder', maxPages);
  document.getElementById('end-page').setAttribute('value', maxPages);
  document.getElementById('end-page').setAttribute('max', maxPages);
  // Set max pages in the modal for start page
  document.getElementById('start-page').setAttribute('max', maxPages);
  // Set onclick attribute on the confirm button with the python function call
  document.getElementById('confirm-dl-button').setAttribute('onclick', `eel.downloadBook('${bookId}', document.getElementById('start-page').value, document.getElementById('end-page').value, document.getElementById('download-method').value, document.getElementById('image-store').value)`);
  // Show the modal
  downloadModal.show();
}
