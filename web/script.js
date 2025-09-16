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

// Function that checks if (and makes) the backend (python) is logged in into bsmart
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

    // Process the authors array into a string
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
            <button class="btn btn-primary w-100" onclick="startDownload('${book.id}')">Download</button>
        </div>
        </div>
    </div>`;


    container.appendChild(card);
  });
}

// Show download modal
function showDownloadModal() {
  const downloadModal = new bootstrap.Modal(document.getElementById('downloadModal'));
  downloadModal.show();
}

// Start book download in py and show popup
async function startDownload(bookId) {
  showDownloadModal();
  eel.downloadBook(bookId)();
}
