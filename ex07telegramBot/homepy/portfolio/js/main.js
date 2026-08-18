const pages = [...document.querySelectorAll("[data-page]")];
const navLinks = [...document.querySelectorAll("[data-nav]")];
const nav = document.querySelector("#site-nav");
const toggle = document.querySelector(".nav-toggle");
const dialog = document.querySelector("#note-dialog");
const queryInput = document.querySelector("#note-query");
const filterButtons = [...document.querySelectorAll(".board-filters button")];
const rows = [...document.querySelectorAll(".board-row[data-cat]")];
const empty = document.querySelector(".board-empty");
const form = document.querySelector("#contact-form");

let noteFilter = "all";

function pageFromHash() {
  const name = location.hash.replace("#", "") || "home";
  return pages.some((page) => page.dataset.page === name) ? name : "home";
}

function showPage(name) {
  pages.forEach((page) => {
    const active = page.dataset.page === name;
    page.hidden = !active;
    page.classList.toggle("is-active", active);
  });

  navLinks.forEach((link) => {
    if (!link.closest(".site-nav")) return;
    if (link.dataset.nav === name) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });

  nav?.classList.remove("is-open");
  toggle?.setAttribute("aria-expanded", "false");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function applyNotes() {
  const q = (queryInput?.value ?? "").trim().toLowerCase();
  let visible = 0;

  rows.forEach((row) => {
    const cat = row.dataset.cat ?? "";
    const title = (row.dataset.title ?? "").toLowerCase();
    const matchCat = noteFilter === "all" || cat === noteFilter;
    const matchQuery = !q || title.includes(q) || cat.toLowerCase().includes(q);
    const show = matchCat && matchQuery;
    row.hidden = !show;
    if (show) visible += 1;
  });

  if (empty) empty.hidden = visible !== 0;
}

toggle?.addEventListener("click", () => {
  const open = nav?.classList.toggle("is-open");
  toggle.setAttribute("aria-expanded", String(Boolean(open)));
});

navLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const name = link.dataset.nav;
    if (!name) return;
    event.preventDefault();
    if (location.hash !== `#${name}`) {
      location.hash = name;
    } else {
      showPage(name);
    }
  });
});

window.addEventListener("hashchange", () => showPage(pageFromHash()));
showPage(pageFromHash());

document.querySelectorAll(".project-head").forEach((button) => {
  button.addEventListener("click", () => {
    const item = button.closest(".project");
    const open = !item?.classList.contains("is-open");
    document.querySelectorAll(".project").forEach((project) => {
      project.classList.remove("is-open");
      project.querySelector(".project-head")?.setAttribute("aria-expanded", "false");
    });
    if (open && item) {
      item.classList.add("is-open");
      button.setAttribute("aria-expanded", "true");
    }
  });
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    noteFilter = button.dataset.filter ?? "all";
    filterButtons.forEach((item) => item.classList.toggle("is-active", item === button));
    applyNotes();
  });
});

queryInput?.addEventListener("input", applyNotes);

rows.forEach((row) => {
  row.addEventListener("click", () => {
    if (!dialog) return;
    document.querySelector("#dialog-cat").textContent = row.dataset.cat ?? "";
    document.querySelector("#dialog-title").textContent = row.dataset.title ?? "";
    document.querySelector("#dialog-date").textContent = row.dataset.date ?? "";
    document.querySelector("#dialog-body").textContent = row.dataset.body ?? "";
    const wrap = document.querySelector("#dialog-link-wrap");
    const link = document.querySelector("#dialog-link");
    const href = row.dataset.link;
    if (href) {
      wrap.hidden = false;
      link.href = href;
    } else {
      wrap.hidden = true;
      link.removeAttribute("href");
    }
    dialog.showModal();
  });
});

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  const status = form.querySelector(".form-status");
  if (!form.checkValidity()) {
    form.reportValidity();
    if (status) status.textContent = "필수 항목을 확인해 주세요.";
    return;
  }
  if (status) status.textContent = "데모 폼입니다. 이메일은 위 주소로 직접 보내 주세요.";
  form.reset();
});
